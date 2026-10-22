#!/usr/bin/env python3
"""CLI: run one investigation end to end and write logs/<run_id>.{jsonl,md,memo.json}.

    python run.py --input input_examples/example_1.json
    python run.py --agency "Housing and Development Board" --from 2025-01-01 --to 2025-12-31 --flags R1,R4
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path

from app.orchestration.factory import make_deps
from app.orchestration.graph import run_investigation
from app.schemas import RunRequest
from app.tracing import Tracer


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", help="JSON file with agency, date_from, date_to, flags")
    ap.add_argument("--agency")
    ap.add_argument("--from", dest="date_from", type=date.fromisoformat)
    ap.add_argument("--to", dest="date_to", type=date.fromisoformat)
    ap.add_argument("--flags", default="", help="comma separated, e.g. R1,R4 (default: planner decides)")
    ap.add_argument("--run-id")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO if a.verbose else logging.WARNING, format="%(name)s %(message)s")
    if a.input:
        req = RunRequest.model_validate(json.loads(Path(a.input).read_text()))
    elif a.agency and a.date_from and a.date_to:
        req = RunRequest(agency=a.agency, date_from=a.date_from, date_to=a.date_to, flags=[f for f in a.flags.split(",") if f])
    else:
        ap.error("give --input or --agency/--from/--to")
    tracer = Tracer(a.run_id)
    tracer.subscribe(lambda e: print(f"  [{e.agent_name}] {e.action} -> {e.status}: {e.output_summary[:110]}", file=sys.stderr))
    final = run_investigation(req, make_deps(tracer))
    memo = final.get("memo")
    if not memo:
        print(f"Request rejected: {final.get('rejected_reason')}", file=sys.stderr)
        return 2
    print(memo.markdown)
    print(f"\nTrace: {tracer.path}\nMemo:  {tracer.dir / (memo.run_id + '.md')}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
