#!/usr/bin/env python3
"""Entry point: serve the API, or run one investigation end to end and write logs/<run_id>.{jsonl,md,memo.json}.

    python run.py --serve                # FastAPI on 0.0.0.0:$PORT (default 8000): POST /run
    python run.py --input input_examples/example_1.json
    python run.py --agency "Housing and Development Board" --from 2025-01-01 --to 2025-12-31 --flags R1,R4
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import date
from pathlib import Path

from app.orchestration.factory import make_deps
from app.orchestration.graph import run_investigation
from app.schemas import RunRequest
from app.tracing import Tracer, format_event


def serve() -> int:
    import uvicorn

    uvicorn.run("app.api:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), log_level=os.getenv("LOG_LEVEL", "info").lower())
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serve", action="store_true", help="start the HTTP API on 0.0.0.0:$PORT (default 8000); also the default with no other arguments")
    ap.add_argument("--input", help="JSON file with agency, date_from, date_to, flags")
    ap.add_argument("--agency")
    ap.add_argument("--from", dest="date_from", type=date.fromisoformat)
    ap.add_argument("--to", dest="date_to", type=date.fromisoformat)
    ap.add_argument("--flags", default="", help="comma separated, e.g. R1,R4 (default: planner decides)")
    ap.add_argument("--run-id")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    if a.serve or not (a.input or a.agency or a.date_from or a.date_to):
        return serve()
    logging.basicConfig(level=logging.INFO if a.verbose else logging.WARNING, format="%(name)s %(message)s")
    if a.input:
        req = RunRequest.model_validate(json.loads(Path(a.input).read_text()))
    elif a.agency and a.date_from and a.date_to:
        req = RunRequest(agency=a.agency, date_from=a.date_from, date_to=a.date_to, flags=[f for f in a.flags.split(",") if f])
    else:
        ap.error("give --input or --agency/--from/--to")
    tracer = Tracer(a.run_id)
    tracer.subscribe(lambda e: print(format_event(e), flush=True))
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
