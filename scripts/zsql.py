#!/usr/bin/env python3
"""Run ONE Lightning SQL statement through Zetaris REST and print the result.

    python scripts/zsql.py "SELECT count(*) FROM gebiz_pg.awards"
    python scripts/zsql.py -f sql/register/01_datasource.sql
    echo "SHOW DATASOURCES" | python scripts/zsql.py
    python scripts/zsql.py --json "SELECT 1"

Stdlib only, so it works before the venv exists. The API key is read from .env
(or the environment) and is never printed. Every call gets a fresh UUID used as
both X-Request-ID and queryId.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_env(path: Path | None = None) -> dict[str, str]:
    """Minimal .env reader (KEY=VALUE, '#' comments). Real environment wins."""
    env: dict[str, str] = {}
    path = path or ROOT / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.split(" #")[0].strip() if " #" in line else line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip("\"'")
    env.update({k: v for k, v in os.environ.items() if k in env or k.startswith(("ZETARIS_", "METERLESS_"))})
    return env


def run_sql(sql: str, env: dict[str, str] | None = None, limit: int = 1000, timeout: float = 60) -> dict:
    env = env or load_env()
    for k in ("ZETARIS_REST_URL", "ZETARIS_ORG_ID", "ZETARIS_API_KEY"):
        if not env.get(k):
            raise SystemExit(f"missing {k} in .env")
    query_id = str(uuid.uuid4())
    req = urllib.request.Request(
        env["ZETARIS_REST_URL"].rstrip("/") + "/sql-editor/sqls/run",
        data=json.dumps({"queryId": query_id, "sql": sql, "source": "SqlEditor", "limit": limit}).encode(),
        headers={
            "Authorization": f"Bearer {env['ZETARIS_API_KEY']}",
            "X-Org-ID": env["ZETARIS_ORG_ID"],
            "X-Request-ID": query_id,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            out = json.load(resp)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} (query_id={query_id}): {e.read().decode(errors='replace')[:500]}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Zetaris unreachable (query_id={query_id}): {e.reason}")
    out["query_id"] = query_id
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sql", nargs="?", help="one SQL statement (omit to read stdin)")
    ap.add_argument("-f", "--file", help="read the statement from a file")
    ap.add_argument("--limit", type=int, default=1000)
    ap.add_argument("--json", action="store_true", help="print raw JSON")
    a = ap.parse_args()
    sql = Path(a.file).read_text() if a.file else (a.sql if a.sql is not None else sys.stdin.read())
    sql = sql.strip().rstrip(";")
    if not sql:
        ap.error("no SQL given")
    res = run_sql(sql, limit=a.limit)
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        headers, data = res.get("headers", []), res.get("data", [])
        print("\t".join(headers))
        for row in data:
            print("\t".join("" if c is None else str(c) for c in row))
        print(f"-- {len(data)} row(s) of {res.get('total')}, {res.get('timeUsed')} ms, query_id={res['query_id']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
