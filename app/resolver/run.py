"""Fill gebiz.supplier_xwalk.

  python -m app.resolver.run --pass 1        # exact + former_name only (before R1)
  python -m app.resolver.run --pass 2        # fuzzy + LLM tie-break + unresolved/out_of_scope for the rest
  python -m app.resolver.run --pass 2 --no-llm

Reads supplier names and ACRA entities through Zetaris; writes the crosswalk straight to Postgres
(Zetaris sources are read-only), with an upsert so re-runs are safe.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from app.resolver.entities import EntityIndex, zetaris_query  # noqa: E402
from app.resolver.match import pass1, resolve
from app.schemas import Match  # noqa: E402


def supplier_names() -> list[str]:
    _, rows, _ = zetaris_query("SELECT DISTINCT supplier_name FROM gebiz_pg.awards WHERE supplier_name IS NOT NULL")
    return sorted(r[0] for r in rows)


def write_xwalk(matches: list[Match]) -> None:
    from fetch_common import pg_conn

    conn = pg_conn("gebiz")
    with conn, conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO supplier_xwalk (supplier_name, uen, confidence, method, candidates, resolved_at)
               VALUES (%s, %s, %s, %s, %s::jsonb, now())
               ON CONFLICT (supplier_name) DO UPDATE SET uen = EXCLUDED.uen, confidence = EXCLUDED.confidence,
               method = EXCLUDED.method, candidates = EXCLUDED.candidates, resolved_at = now()""",
            [(m.supplier_name, m.uen, m.confidence, m.method, json.dumps(m.candidates)) for m in matches],
        )
    conn.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pass", dest="pass_", type=int, choices=[1, 2], required=True)
    ap.add_argument("--no-llm", action="store_true")
    a = ap.parse_args()
    names = supplier_names()
    index = EntityIndex.from_zetaris()
    print(f"suppliers={len(names)} entities={len(index.entities)}")
    if a.pass_ == 1:
        ms = [m for m in pass1(names, index) if m.uen]  # only resolved rows; the rest wait for pass 2
        write_xwalk(ms)
    else:
        tb = None
        if not a.no_llm:
            from app.resolver.llm import RECEIPTS, nightshift_tiebreak
            tb = nightshift_tiebreak
        ms = resolve(names, index, tiebreak=tb)
        write_xwalk(ms)
        if tb:
            print("nightshift receipts:", json.dumps(RECEIPTS))
    print("methods:", dict(Counter(m.method for m in ms)))


if __name__ == "__main__":
    main()
