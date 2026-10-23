#!/usr/bin/env python
"""Record a replay set from ONE real run (live Zetaris + Nightshift).

  python scripts/record_replay.py                      # HDB 2024-04-01..2025-03-31 -> data/replay/hdb-fy2425/
  python scripts/record_replay.py --name x --agency "..." --from 2024-04-01 --to 2025-03-31
  python scripts/record_replay.py --name pa-2024 --input input_examples/example_2.json

Stores Zetaris results keyed by normalised SQL and Nightshift replies keyed by prompt (see app/replay.py).
Record with H-MEM stopped (HMEM_URL pointing nowhere): recalled memories change which findings reach the
Critic, and offline replay runs without memory, so the recorded SQL must match that path.
Takes about 3 minutes and uses the LLM call budget of a normal run. Refuses to record a run that itself
used replayed data.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import replay  # noqa: E402
from app.adapters.config import get_settings  # noqa: E402
from app.orchestration.factory import make_deps  # noqa: E402
from app.orchestration.graph import run_investigation  # noqa: E402
from app.schemas import RunRequest  # noqa: E402
from app.tracing import Tracer  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="hdb-fy2425")
    ap.add_argument("--agency", default="Housing and Development Board")
    ap.add_argument("--from", dest="d1", default="2024-04-01")
    ap.add_argument("--to", dest="d2", default="2025-03-31")
    ap.add_argument("--input", help="JSON request file (agency, date_from, date_to, flags); overrides --agency/--from/--to")
    a = ap.parse_args()
    out = ROOT / "data" / "replay" / a.name
    if a.input:
        req = RunRequest.model_validate(json.loads(Path(a.input).read_text()))
        a.agency, a.d1, a.d2 = req.agency, str(req.date_from), str(req.date_to)
    else:
        req = RunRequest(agency=a.agency, date_from=date.fromisoformat(a.d1), date_to=date.fromisoformat(a.d2))
    tracer = Tracer()
    mark = replay.mark()
    with replay.Recorder() as rec:
        deps = make_deps(tracer)
        final = run_investigation(req, deps)
    if replay.served_since(mark):
        print("run used replayed data; not recording", file=sys.stderr)
        return 2
    memo = final.get("memo")
    if not memo:
        print(f"no memo ({final.get('rejected_reason')}); not recording", file=sys.stderr)
        return 1
    try:
        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        sha = None
    man = rec.save(out, {"name": a.name, "request": {"agency": a.agency, "date_from": a.d1, "date_to": a.d2, "flags": list(req.flags)},
                         "source_run_id": tracer.run_id, "hmem_used": deps.hmem is not None, "git_sha": sha,
                         "note": "Recorded from one live run. Replayed output is NOT a live run; it is labelled as such."})
    print(f"recorded {man['zetaris_queries']} zetaris queries, {man['nightshift_calls']} nightshift calls -> {out}")
    print(f"source run: {tracer.run_id} ({len(memo.findings)} findings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
