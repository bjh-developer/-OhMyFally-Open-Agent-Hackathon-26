#!/usr/bin/env python
"""Register our sources in Zetaris from sql/register/*.sql (one statement per file, run in name order).

  python scripts/register_zetaris.py [--csv]

Idempotent: `*_drop_*.sql` files drop OUR objects only (errors ignored), then everything is recreated.
${VARS} in the SQL come from .env / defaults, so no secret is committed. --csv swaps the ACRA table to the
CSV fallback in sql/register/alt/ if Zetaris cannot read the Parquet file.
40-47 rebuild the USL `procurement_usl` (drop, namespace, COMPILE, ACTIVATE per table).
Finishes by running the milestone counts, including the USL.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from string import Template

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_common import ROOT  # noqa: E402
import _zrest as z  # noqa: E402

REG = ROOT / "sql" / "register"


def params() -> dict[str, str]:
    return {
        "POSTGRES_USER": os.environ["POSTGRES_USER"],
        "POSTGRES_PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "S3_BUCKET": os.getenv("S3_BUCKET", "pi-acra"),
        "S3_ZETARIS_ENDPOINT": os.getenv("S3_ENDPOINT", "http://pi-s3:8333"),
        "S3_ACCESS_KEY": os.getenv("S3_ACCESS_KEY", "pi"),
        "S3_SECRET_KEY": os.getenv("S3_SECRET_KEY", "pi-secret"),
    }


def statement(path: Path, p: dict[str, str]) -> str:
    lines = [l for l in path.read_text().splitlines() if not l.strip().startswith("--")]
    return Template("\n".join(lines)).substitute(p).strip().rstrip(";")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", action="store_true", help="register ACRA from the CSV fallback")
    a = ap.parse_args()
    p = params()
    files = sorted(REG.glob("*.sql"))
    if a.csv:
        files = sorted([f for f in files if f.name != "31_acra_entities.sql"] + [REG / "alt" / "31_acra_entities_csv.sql"],
                       key=lambda f: f.name)
    for f in files:
        is_drop = "_drop_" in f.name
        try:
            r = z.run(statement(f, p), timeout=170)
            print(f"ok    {f.name}  query_id={r['query_id']}")
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            for secret in (p["POSTGRES_PASSWORD"], p["S3_SECRET_KEY"]):
                msg = msg.replace(secret, "***")
            if is_drop:
                print(f"skip  {f.name}  (nothing to drop)")
                continue
            print(f"FAIL  {f.name}: {msg[:400]}")
            return 1
    usl = "lightning.metastore.procurement.procurement_usl.award_profile"
    for q in ("SELECT count(*) FROM gebiz_pg.awards", "SELECT count(*) FROM ACRA_FILES.entities",
              f"SELECT count(*) FROM {usl}", f"SELECT count(*) FROM {usl} WHERE registry_status IS NOT NULL"):
        r = z.run(q)
        print(f"{q} -> {r['data'][0][0]}  (query_id={r['query_id']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
