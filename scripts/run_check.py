#!/usr/bin/env python
"""Run one sql/checks/R*.sql through Zetaris with the same renderer the Analyst uses.

  python scripts/run_check.py R1 "Housing and Development Board" 2021-04-01 2026-03-31
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.checks.runner import run_check  # noqa: E402
from app.adapters.zetaris import run_sql  # noqa: E402


def main() -> int:
    flag, agency, d1, d2 = sys.argv[1:5]
    check = run_check(flag, agency=agency, date_from=d1, date_to=d2,
                      run_sql=lambda sql: run_sql(sql, limit=100000, timeout=90, retries=0))
    headers, rows, qid = check.result.headers, check.result.rows, check.result.query_id
    print("\t".join(headers))
    for r in rows:
        print("\t".join("" if c is None else str(c) for c in r))
    print(f"-- {len(rows)} row(s), query_id={qid}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
