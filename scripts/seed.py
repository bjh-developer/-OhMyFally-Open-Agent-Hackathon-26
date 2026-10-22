#!/usr/bin/env python
"""Seed pi-postgres and pi-s3 from data/. Idempotent: running twice yields the same state.

  python scripts/seed.py [--no-planted]

Postgres `gebiz`:          awards, rules, ago_chunks, supplier_xwalk (emptied; re-run the Resolver)
Postgres `agency_internal`: bids, evaluations, coi_declarations (S5, synthetic; planted rows only)
S3 `pi-acra`:              acra/entities.parquet and acra_csv/entities.csv (sample + planted entities)

Planted cases (data/eval/planted.json) use FICTIONAL suppliers only and are injected here so the same
check SQL that scans real data must find them.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import ROOT, SAMPLE, pg_conn, s3_client  # noqa: E402

RULES_DIR = ROOT / "data" / "rules"
AGO_DIR = ROOT / "data" / "ago"
PLANTED = ROOT / "data" / "eval" / "planted.json"
BUCKET = os.getenv("S3_BUCKET", "pi-acra")

GEBIZ_DDL = [
    """CREATE TABLE IF NOT EXISTS awards (
        tender_no text, tender_description text, agency text, award_date date,
        tender_detail_status text, supplier_name text, awarded_amt numeric)""",
    "CREATE TABLE IF NOT EXISTS rules (flag_id text PRIMARY KEY, name text, params jsonb, source_url text)",
    """CREATE TABLE IF NOT EXISTS ago_chunks (
        chunk_id text PRIMARY KEY, report text, fy text, section text, text text, embedding jsonb)""",
    """CREATE TABLE IF NOT EXISTS supplier_xwalk (
        supplier_name text PRIMARY KEY, uen text NULL, confidence real, method text,
        candidates jsonb, resolved_at timestamptz DEFAULT now())""",
]
INTERNAL_DDL = [
    """CREATE TABLE IF NOT EXISTS bids (
        tender_no text, supplier_name text, bid_amt numeric, bid_rank int)""",
    """CREATE TABLE IF NOT EXISTS evaluations (
        tender_no text, supplier_name text, criterion text, weight numeric, score numeric)""",
    """CREATE TABLE IF NOT EXISTS coi_declarations (
        tender_no text, evaluator_id text, supplier_name text, declared_conflict boolean, note text)""",
]
ENTITY_COLS = ["uen", "entity_name", "entity_type_description", "entity_status_description",
               "registration_incorporation_date", "block", "street_name", "level_no", "unit_no",
               "building_name", "postal_code", "primary_ssic_code", "primary_ssic_description",
               "no_of_officers"] + [f"former_entity_name{i}" for i in range(1, 16)]


def ensure_db(name: str) -> None:
    c = pg_conn("postgres")
    c.autocommit = True
    with c.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (name,))
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE "{name}"')
    c.close()


def copy_rows(cur, table: str, cols: list[str], rows: list[list]) -> None:
    with cur.copy(f"COPY {table} ({','.join(cols)}) FROM STDIN") as cp:
        for r in rows:
            cp.write_row(r)


def load_planted(enabled: bool) -> list[dict]:
    if not enabled or not PLANTED.exists():
        return []
    return json.loads(PLANTED.read_text())["cases"]


def seed_gebiz(planted: list[dict]) -> dict:
    awards = pd.read_csv(SAMPLE / "awards.csv", dtype=str, keep_default_na=False)
    rows = awards[["tender_no", "tender_description", "agency", "award_date", "tender_detail_status",
                   "supplier_name", "awarded_amt"]].values.tolist()
    for case in planted:
        for a in case.get("awards", []):
            rows.append([a["tender_no"], a.get("tender_description", "PLANTED TEST TENDER"),
                         case["agency"], a["award_date"], a.get("tender_detail_status", "Awarded to Suppliers"),
                         a["supplier_name"], a["awarded_amt"]])
    rules = []
    for f in sorted(RULES_DIR.glob("red_flags.yaml")):
        for r in yaml.safe_load(f.read_text()):
            rules.append([r["flag_id"], r["name"], json.dumps(r.get("params", {})), r.get("source_url")])
    ago = []
    index_csv = AGO_DIR / "index.csv"
    if index_csv.exists():  # index.csv + <chunk_id>.txt; embeddings are added later (R5), NULL until then
        for c in pd.read_csv(index_csv, dtype=str, keep_default_na=False).to_dict("records"):
            txt = AGO_DIR / f"{c['chunk_id']}.txt"
            ago.append([c["chunk_id"], c["report"], c["fy"], c["section"], txt.read_text().strip(), None])
    conn = pg_conn("gebiz")
    with conn, conn.cursor() as cur:
        for ddl in GEBIZ_DDL:
            cur.execute(ddl)
        cur.execute("TRUNCATE awards, rules, ago_chunks, supplier_xwalk")
        copy_rows(cur, "awards", ["tender_no", "tender_description", "agency", "award_date",
                                  "tender_detail_status", "supplier_name", "awarded_amt"], rows)
        if rules:
            copy_rows(cur, "rules", ["flag_id", "name", "params", "source_url"], rules)
        if ago:
            copy_rows(cur, "ago_chunks", ["chunk_id", "report", "fy", "section", "text", "embedding"], ago)
        counts = {}
        for t in ("awards", "rules", "ago_chunks", "supplier_xwalk"):
            cur.execute(f"SELECT count(*) FROM {t}")
            counts[t] = cur.fetchone()[0]
    conn.close()
    return counts


def seed_internal(planted: list[dict]) -> dict:
    ensure_db("agency_internal")
    conn = pg_conn("agency_internal")
    with conn, conn.cursor() as cur:
        for ddl in INTERNAL_DDL:
            cur.execute(ddl)
        cur.execute("TRUNCATE bids, evaluations, coi_declarations")
        for case in planted:
            it = case.get("internal") or {}
            if it.get("bids"):
                copy_rows(cur, "bids", ["tender_no", "supplier_name", "bid_amt", "bid_rank"],
                          [[b["tender_no"], b["supplier_name"], b["bid_amt"], b["bid_rank"]] for b in it["bids"]])
            if it.get("evaluations"):
                copy_rows(cur, "evaluations", ["tender_no", "supplier_name", "criterion", "weight", "score"],
                          [[e["tender_no"], e["supplier_name"], e["criterion"], e["weight"], e["score"]]
                           for e in it["evaluations"]])
            if it.get("coi_declarations"):
                copy_rows(cur, "coi_declarations",
                          ["tender_no", "evaluator_id", "supplier_name", "declared_conflict", "note"],
                          [[c["tender_no"], c["evaluator_id"], c["supplier_name"], c["declared_conflict"],
                            c.get("note")] for c in it["coi_declarations"]])
        counts = {}
        for t in ("bids", "evaluations", "coi_declarations"):
            cur.execute(f"SELECT count(*) FROM {t}")
            counts[t] = cur.fetchone()[0]
    conn.close()
    return counts


def entity_table(planted: list[dict]) -> pa.Table:
    df = pd.read_parquet(SAMPLE / "acra_entities.parquet").astype(str).replace({"nan": "", "None": ""})
    extra = []
    for case in planted:
        for e in case.get("entities", []):
            row = {c: "" for c in ENTITY_COLS}
            row.update({k: str(v) for k, v in e.items() if k in ENTITY_COLS})
            extra.append(row)
    if extra:
        df = pd.concat([df[~df["uen"].isin([e["uen"] for e in extra])], pd.DataFrame(extra)], ignore_index=True)
    df = df[ENTITY_COLS].copy()
    df["registration_incorporation_date"] = pd.to_datetime(df["registration_incorporation_date"], errors="coerce").dt.date
    schema = pa.schema([(c, pa.date32() if c == "registration_incorporation_date" else pa.string())
                        for c in ENTITY_COLS])
    return pa.Table.from_pandas(df, schema=schema, preserve_index=False)


def seed_s3(planted: list[dict]) -> int:
    t = entity_table(planted)
    s3 = s3_client()
    if BUCKET not in [b["Name"] for b in s3.list_buckets()["Buckets"]]:
        s3.create_bucket(Bucket=BUCKET)
    pbuf = io.BytesIO()
    pq.write_table(t, pbuf)
    s3.put_object(Bucket=BUCKET, Key="acra/entities.parquet", Body=pbuf.getvalue())
    cbuf = io.StringIO()
    t.to_pandas().to_csv(cbuf, index=False)
    s3.put_object(Bucket=BUCKET, Key="acra_csv/entities.csv", Body=cbuf.getvalue().encode())
    return t.num_rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-planted", action="store_true", help="skip fictional planted cases")
    a = ap.parse_args()
    planted = load_planted(not a.no_planted)
    print(f"planted cases injected: {len(planted)}")
    print("gebiz:", seed_gebiz(planted))
    print("agency_internal:", seed_internal(planted))
    print("s3 entities rows:", seed_s3(planted))


if __name__ == "__main__":
    main()
