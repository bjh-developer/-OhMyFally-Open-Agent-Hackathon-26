r"""Evaluate frozen entity labels against a fresh Resolver run using live Zetaris data.

    .venv\Scripts\python.exe -X utf8 scripts/eval_resolver.py
    .venv\Scripts\python.exe -X utf8 scripts/eval_resolver.py --deterministic

This measures entity matching only, not anomaly precision or planted-case recall.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.resolver.entities import EntityIndex
from app.resolver.match import LLM_ERRORS, resolve
from app.orchestration.state import MATCH_THRESHOLD

REVIEWED = {"agent_reviewed", "human_reviewed"}


def load_labels(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"supplier_name", "correct_uen", "category", "review_status", "reviewer"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Label CSV is missing required columns")
        labels = list(reader)
    seen = set()
    for row in labels:
        name = row["supplier_name"]
        if not name.strip() or name in seen:
            raise ValueError("Supplier names must be nonempty and unique")
        seen.add(name)
        status = row["review_status"]
        if status not in REVIEWED | {"pending"}:
            raise ValueError("Unknown review status")
        if status in REVIEWED and (not row["correct_uen"].strip() or not row["reviewer"].strip()):
            raise ValueError("Reviewed rows need an explicit UEN or NONE and a reviewer")
        if status == "pending" and row["correct_uen"].strip():
            raise ValueError("Pending rows must not have a guessed answer")
    return labels


def evaluate(labels: list[dict], matches: list, threshold: float = MATCH_THRESHOLD) -> dict:
    """Score reviewed rows only; NONE means abstention, not an unresolved guess."""
    scored = [row for row in labels if row["review_status"] in REVIEWED]
    predictions = {match.supplier_name: match for match in matches}
    if set(predictions) != {row["supplier_name"] for row in scored} or len(predictions) != len(matches):
        raise ValueError("Predictions must cover each reviewed supplier exactly once")
    details = []
    for row in scored:
        match = predictions[row["supplier_name"]]
        expected = None if row["correct_uen"] == "NONE" else row["correct_uen"]
        details.append({"supplier_name": row["supplier_name"], "expected_uen": expected,
                        "predicted_uen": match.uen, "correct": match.uen == expected,
                        "method": match.method, "confidence": match.confidence,
                        "category": row["category"], "review_status": row["review_status"],
                        "passes_critic_threshold": bool(match.uen and match.confidence >= threshold)})

    def summary(rows):
        total = len(rows)
        linked = sum(bool(row["predicted_uen"]) for row in rows)
        positives = sum(bool(row["expected_uen"]) for row in rows)
        correct_links = sum(bool(row["expected_uen"]) and row["correct"] for row in rows)
        accepted = [row for row in rows if row["passes_critic_threshold"]]
        return {"total": total, "correct": sum(row["correct"] for row in rows),
                "accuracy": sum(row["correct"] for row in rows) / total if total else None,
                "linked": linked, "positive_labels": positives,
                "link_precision": correct_links / linked if linked else None,
                "link_recall": correct_links / positives if positives else None,
                "wrong_links": sum(bool(row["predicted_uen"]) and not row["correct"] for row in rows),
                "missed_links": sum(bool(row["expected_uen"]) and not row["predicted_uen"] for row in rows),
                "correct_abstentions": sum(not row["expected_uen"] and not row["predicted_uen"] for row in rows),
                "critic_accepted_links": len(accepted),
                "critic_link_precision": sum(row["correct"] for row in accepted) / len(accepted) if accepted else None,
                "critic_link_recall": sum(row["correct"] for row in accepted) / positives if positives else None}

    return {"overall": summary(details), "human_reviewed": summary([r for r in details if r["review_status"] == "human_reviewed"]),
            "by_category": {category: summary([r for r in details if r["category"] == category]) for category in sorted({r["category"] for r in details})},
            "methods": dict(Counter(row["method"] for row in details)),
            "pending_excluded": sum(row["review_status"] == "pending" for row in labels),
            "critic_threshold": threshold, "predictions": details}


def evaluate_live(labels_path: Path, *, deterministic: bool = False, sql_fn=None) -> dict:
    """Run a fresh evaluation; shared by this CLI and the combined evaluation harness."""
    # This is a live evaluation. Never silently report recorded responses as new accuracy.
    os.environ["SAMPLE_MODE"] = "false"
    from app.adapters.config import get_settings
    from app.adapters.zetaris import run_sql
    from app.adapters.nightshift import budget_scope
    from app.resolver.llm import RECEIPTS, nightshift_tiebreak
    get_settings.cache_clear()
    labels = load_labels(labels_path)
    reviewed = [row for row in labels if row["review_status"] in REVIEWED]
    if not reviewed:
        raise ValueError("No reviewed labels to evaluate")
    start = time.monotonic()
    sources = {}
    def live_query(sql, **kwargs):
        result = (sql_fn or run_sql)(sql, limit=100000, timeout=90, retries=0)
        if result.replayed:
            raise ValueError("Live evaluation received replayed data")
        sources[result.query_id] = {"sql": sql, "rows": len(result.rows)}
        return result
    def registry_query(sql):
        result = live_query(sql)
        return result.headers, result.rows, result.query_id
    index = EntityIndex.from_zetaris(query=registry_query)
    supplier_result = live_query("SELECT DISTINCT supplier_name FROM gebiz_pg.awards")
    suppliers = {row[0] for row in supplier_result.rows}
    uens = {entity.uen for entity in index.entities}
    if any(row["supplier_name"] not in suppliers for row in reviewed):
        raise ValueError("A reviewed supplier is absent from the live awards")
    if any(row["correct_uen"] != "NONE" and row["correct_uen"] not in uens for row in reviewed):
        raise ValueError("A labelled UEN is absent from the live registry subset")
    LLM_ERRORS.clear()
    RECEIPTS.clear()
    with budget_scope(40) as budget:
        matches = resolve([row["supplier_name"] for row in reviewed], index,
                          tiebreak=None if deterministic else nightshift_tiebreak)
    report = evaluate(labels, matches)
    report.update({"generated_at": datetime.now(timezone.utc).isoformat(), "mode": "live",
                   "resolver_mode": "deterministic" if deterministic else "full",
                   "labels_sha256": hashlib.sha256(labels_path.read_bytes()).hexdigest(),
                   "registry_entities": len(index.entities), "sources": sources,
                   "runtime_seconds": round(time.monotonic() - start, 3),
                   "llm_calls": budget.used, "llm_failed_batches": len(LLM_ERRORS),
                   "meterless_receipt_ids": [r["receipt_id"] for r in RECEIPTS],
                   "limitations": ["Agent-reviewed labels are not human sign-off or independently verified legal identities.",
                       "The registry sample was previously minimised using Resolver candidates; this is an in-sample diagnostic, not a held-out benchmark.",
                       "Only source-supported corporate matches and a placeholder are scored; ambiguous cases remain pending.",
                       "No fuzzy or LLM tie-break accuracy claim is supported unless those methods appear in the results.",
                       "Former names have no change dates; historical ownership at award time is unverified."]})
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=ROOT / "data/eval/entity_labels.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "output_examples/resolver_metrics.json")
    parser.add_argument("--deterministic", action="store_true", help="Disable LLM tie-breaks")
    args = parser.parse_args(argv)
    report = evaluate_live(args.labels, deterministic=args.deterministic)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("overall", "methods", "pending_excluded", "llm_calls", "llm_failed_batches")}, indent=2))
    print(f"Saved {args.output}")
    return 1 if report["llm_failed_batches"] else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        # Keep credentials and raw remote error responses out of terminal output.
        print(f"Resolver evaluation failed ({type(exc).__name__}). No new successful result was claimed.", file=sys.stderr)
        sys.exit(1)
