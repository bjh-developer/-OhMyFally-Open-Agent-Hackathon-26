#!/usr/bin/env python
"""Token savings of Zetaris pushdown vs dumping the raw joined rows into the model.

  python scripts/token_baseline.py [--set hdb-fy2425]

(a) Pushdown: prompt characters the agents actually sent to Nightshift in the recorded live run
    (data/replay/<set>/nightshift.json, written by scripts/record_replay.py; summed over every call and repair retry).
(b) Naive: the awards x supplier_xwalk x ACRA entities rows for the same agency and period, fetched live through
    Zetaris (SELECT a.*, e.*) and serialised as one compact JSON table. Counted ONCE, with no instructions added,
    so it is a lower bound: a real naive agent would resend rows on every call and still need prompts.
Tokens are estimated as chars / 4 (not a tokenizer count). Provider-reported prompt_tokens, when the recorded
replies carry them, are listed as a cross-check.
Writes output_examples/token_savings.json and output_examples/token_savings.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.adapters.config import get_settings  # noqa: E402
from app.adapters.zetaris import _run_sql_live  # noqa: E402  (live only: a replayed naive query would prove nothing)
from app.checks.runner import render  # noqa: E402

NAIVE_SQL = ("SELECT a.*, e.* FROM gebiz_pg.awards a "
             "JOIN gebiz_pg.supplier_xwalk x ON x.supplier_name = a.supplier_name AND x.uen IS NOT NULL "
             "JOIN ACRA_FILES.entities e ON e.uen = x.uen "
             "WHERE a.agency = {{agency}} AND a.award_date BETWEEN {{date_from}} AND {{date_to}}")


def tok(chars: int) -> int:
    return round(chars / 4)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="hdb-fy2425")
    a = ap.parse_args()
    d = get_settings().replay_dir.parent / a.set
    man = json.loads((d / "manifest.json").read_text())
    ns = json.loads((d / "nightshift.json").read_text())["entries"]
    zq = json.loads((d / "zetaris.json").read_text())
    req = man["request"]

    sent_chars = sum(e["prompt_chars"] for e in ns)
    reported = [e["usage"].get("prompt_tokens") for e in ns if isinstance(e.get("usage"), dict)]
    reported_total = sum(x for x in reported if isinstance(x, int)) if reported and all(isinstance(x, int) for x in reported) else None
    app_side = sum(len(json.dumps(q["rows"], separators=(",", ":"))) for q in zq.values())

    res = _run_sql_live(render(NAIVE_SQL, agency=req["agency"], date_from=req["date_from"], date_to=req["date_to"]),
                        limit=1_000_000, timeout=170.0, retries=0)
    naive_chars = len(json.dumps({"columns": res.headers, "rows": res.rows}, separators=(",", ":"), ensure_ascii=False))
    p, n = tok(sent_chars), tok(naive_chars)
    out = {
        "request": req, "source_run_id": man.get("source_run_id"),
        "method": "tokens = chars / 4 (estimate, not a tokenizer count)",
        "pushdown": {"llm_calls": sum(e.get("calls", 1) for e in ns), "prompt_chars": sent_chars, "est_tokens": p,
                     "provider_reported_prompt_tokens": reported_total,
                     "note": "prompts the agents really sent, from the recorded live run"},
        "naive": {"joined_rows": len(res), "columns": len(res.headers), "chars": naive_chars, "est_tokens": n,
                  "note": "awards x supplier_xwalk x ACRA entities for the same agency and period, one compact JSON dump, "
                          "no instructions; lower bound (one dump, not one per LLM call)"},
        "app_side_zetaris_rows_chars": app_side,
        "app_side_note": "result rows the Python side pulled from Zetaris (checks, name lists, crosswalk, entity index); never sent to the LLM",
        "reduction": {"factor": round(n / p, 1) if p else None, "pct_fewer_tokens": round(100 * (1 - p / n), 1) if n else None},
        "caveats": ["chars/4 is a rough estimate; compact JSON of ASCII text is closer to 3-4 chars/token",
                    "naive row count may exceed the model's context window, in which case it could not be done at all",
                    "provider-reported prompt_tokens (when present) exceed chars/4 for the pushdown prompts; the naive side was not tokenised by the provider, so the ratio rests on chars/4 for both sides",
                    "this is the curated sample subset (a few hundred joined rows); naive cost grows with table size, pushdown cost with the number of flagged awards, so the gap widens on the full registry",
                    "pushdown prompts also carry instructions, so the comparison favours naive slightly"],
    }
    o = ROOT / "output_examples"
    o.mkdir(exist_ok=True)
    (o / "token_savings.json").write_text(json.dumps(out, indent=2) + "\n")
    f = out["reduction"]["factor"]
    md = (f"- **Pushdown:** the agents sent ~{p:,} tokens to Nemotron in {out['pushdown']['llm_calls']} calls "
          f"(HDB FY24/25; Zetaris joins and filters first).\n"
          f"- **Naive:** dumping the {len(res):,} raw joined award x ACRA rows would be ~{n:,} tokens in a single pass.\n"
          f"- **Saving:** ~{f}x fewer tokens ({out['reduction']['pct_fewer_tokens']}%); estimate = chars/4, naive counted once, so conservative.\n")
    (o / "token_savings.md").write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
