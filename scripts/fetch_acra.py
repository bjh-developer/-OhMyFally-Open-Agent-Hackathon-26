#!/usr/bin/env python
"""ACRA entities: download the 27 collection CSVs, keep only candidate matches for our suppliers.

  python scripts/fetch_acra.py download   # raw CSVs -> data/raw/acra/ (rate limited, cached)
  python scripts/fetch_acra.py            # build the FULL candidate set -> data/local/ (gitignored)
  python scripts/fetch_acra.py minimise   # after the Resolver ran: write the committed data/sample/ subset

The committed sample is privacy-minimised: only entities the Resolver matched to a GeBIZ supplier, the top-3
candidates of ambiguous (unresolved / llm_tiebreak) suppliers, with level_no/unit_no blanked for sole
proprietorships/partnerships. The full set stays in data/local/ and is used by seed.py when present.

Candidate rule: an ACRA entity is kept when ANY of its names (current or former_entity_name1..15)
shares the first two significant tokens with a supplier in data/sample/awards.csv, or shares the first
token when that token is rare in ACRA (<= RARE_MAX entities). Source: data.gov.sg collection 2
(Singapore Open Data Licence).
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

import pandas as pd
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import LOCAL, RAW, ROOT, SAMPLE, download_dataset, pg_conn  # noqa: E402
from app.resolver.normalize import blocking_keys, normalize  # noqa: E402

COLLECTION_META = "https://api-production.data.gov.sg/v2/public/api/collections/2/metadata"
ACRA_RAW = RAW / "acra"
RARE_MAX = 50
FORMER_COLS = [f"former_entity_name{i}" for i in range(1, 16)]
KEEP_COLS = ["uen", "entity_name", "entity_type_description", "entity_status_description",
             "registration_incorporation_date", "block", "street_name", "level_no", "unit_no",
             "building_name", "postal_code", "primary_ssic_code", "primary_ssic_description",
             "no_of_officers"] + FORMER_COLS


def dataset_ids() -> list[str]:
    r = httpx.get(COLLECTION_META, timeout=60)
    r.raise_for_status()
    return r.json()["data"]["collectionMetadata"]["childDatasets"]


def download_all(pause: float = 14.0) -> list[Path]:
    ids = dataset_ids()
    paths = []
    for i, ds in enumerate(ids, 1):
        dest = ACRA_RAW / f"{ds}.csv"
        cached = dest.exists() and dest.stat().st_size > 0
        download_dataset(ds, dest)
        print(f"[{i}/{len(ids)}] {ds} {dest.stat().st_size // 1024} KiB", flush=True)
        paths.append(dest)
        if not cached:
            time.sleep(pause)  # unauthenticated limit: 5 requests/min
    return paths


def raw_files() -> list[Path]:
    files = sorted(ACRA_RAW.glob("*.csv"))
    if not files:
        raise SystemExit("no raw ACRA files; run: python scripts/fetch_acra.py download")
    return files


def read_file(f: Path) -> pd.DataFrame:
    df = pd.read_csv(f, dtype=str, keep_default_na=False)
    for c in KEEP_COLS:
        if c not in df.columns:
            df[c] = ""
    return df[KEEP_COLS]


def entity_keys(row) -> list[tuple[str, str]]:
    ks = []
    for n in row:
        if n:
            f, t = blocking_keys(n)
            if f:
                ks.append((f, t))
    return ks


def supplier_keys() -> tuple[set[str], set[str]]:
    aw = pd.read_csv(SAMPLE / "awards.csv", dtype=str, keep_default_na=False)
    first, two = set(), set()
    for n in aw["supplier_name"].unique():
        f, t = blocking_keys(n)
        if f:
            first.add(f)
            two.add(t)
    return first, two


def build() -> pd.DataFrame:
    """Two streaming passes over the raw files (a full concat is ~2M rows x 30 string columns: OOM)."""
    first_s, two_s = supplier_keys()
    files = raw_files()
    first_counts: Counter[str] = Counter()
    total = 0
    for f in files:  # pass 1: how common is each first token across ACRA?
        df = read_file(f)
        total += len(df)
        for row in df[["entity_name"] + FORMER_COLS].to_numpy():
            for tok in {k[0] for k in entity_keys(row)}:
                first_counts[tok] += 1
    kept = []
    for f in files:  # pass 2: keep candidates
        df = read_file(f)
        mask = [any(t in two_s or (ft in first_s and first_counts[ft] <= RARE_MAX) for ft, t in entity_keys(row))
                for row in df[["entity_name"] + FORMER_COLS].to_numpy()]
        kept.append(df[pd.Series(mask, index=df.index)])
    out = pd.concat(kept, ignore_index=True).drop_duplicates("uen").reset_index(drop=True)
    out["registration_incorporation_date"] = pd.to_datetime(
        out["registration_incorporation_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    LOCAL.mkdir(parents=True, exist_ok=True)
    out.to_parquet(LOCAL / "acra_entities_full.parquet", index=False)
    out.to_csv(LOCAL / "acra_entities_full.csv", index=False)
    print(f"ACRA total rows: {total}  candidates kept (local, gitignored): {len(out)}")
    return out


SOLE_PROP = "Sole Proprietorship/ Partnership"


def minimise() -> pd.DataFrame:
    """Committed sample = Resolver-matched entities + top-3 candidates of ambiguous suppliers; sole-prop unit blanked."""
    full_path = LOCAL / "acra_entities_full.parquet"
    if not full_path.exists():
        raise SystemExit("no data/local/acra_entities_full.parquet; run fetch_acra.py (build) and the Resolver first")
    full = pd.read_parquet(full_path)
    conn = pg_conn("gebiz")
    with conn.cursor() as cur:
        cur.execute("SELECT uen FROM supplier_xwalk WHERE uen IS NOT NULL")
        keep = {r[0] for r in cur.fetchall()}
        matched = len(keep)
        cur.execute("SELECT candidates FROM supplier_xwalk WHERE method IN ('unresolved', 'llm_tiebreak')")
        for (cands,) in cur.fetchall():
            for c in (cands or [])[:3]:
                keep.add(c["uen"])
    conn.close()
    out = full[full["uen"].isin(keep)].copy().reset_index(drop=True)
    sole = out["entity_type_description"] == SOLE_PROP
    out.loc[sole, ["level_no", "unit_no"]] = ""
    SAMPLE.mkdir(parents=True, exist_ok=True)
    out.to_parquet(SAMPLE / "acra_entities.parquet", index=False)
    out.to_csv(SAMPLE / "acra_entities.csv", index=False)
    print(f"matched uens={matched} + ambiguous candidates -> {len(out)} rows (of {len(full)} local)")
    print(out["entity_type_description"].value_counts().to_string())
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="build", choices=["build", "download", "minimise"])
    a = ap.parse_args()
    if a.cmd == "download":
        download_all()
    elif a.cmd == "minimise":
        minimise()
    else:
        build()


if __name__ == "__main__":
    main()
