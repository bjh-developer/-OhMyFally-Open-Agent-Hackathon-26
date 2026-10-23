#!/usr/bin/env python
r"""Evaluate three sample requests, planted recall, Resolver labels and precision reviews.

    .venv\Scripts\python.exe -X utf8 scripts/eval.py

Runs production SQL checks (not full LLM investigations), with live Zetaris and replay disabled.
Supplemental scopes cover planted cases outside the three sample requests. Never guesses review labels.
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
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.agents import analyst, resolver
from app.checks.runner import available_checks
from app.orchestration.state import Deps
from app.schemas import Plan, RunRequest
from app.tracing import Tracer
from scripts.eval_resolver import evaluate_live

PRECISION_FIELDS = ["finding_id", "flag_id", "tender_no", "agency", "awarded_amt", "metric_name", "metric_value",
                    "threshold", "evidence_query_id", "label", "review_status", "reviewer", "reason"]


def covers(request: RunRequest, case: dict, flag: str, checks: list[str]) -> bool:
    dates = [date.fromisoformat(award["award_date"]) for award in case["awards"]]
    return (request.agency == case["agency"] and flag in checks
            and request.date_from <= min(dates) and request.date_to >= max(dates))


def supplemental_requests(requests: list[RunRequest], cases: list[dict], implemented: list[str]) -> list[RunRequest]:
    """Use case scope only, never expected tender IDs/supplier names as inputs to detection."""
    missing: dict[str, set[str]] = {}
    for case in cases:
        for flag in case["flags"]:
            if not any(covers(req, case, flag, req.flags or implemented) for req in requests):
                missing.setdefault(case["agency"], set()).add(flag)
    output = []
    for agency, flags in sorted(missing.items()):
        agency_dates = [date.fromisoformat(award["award_date"]) for case in cases if case["agency"] == agency for award in case["awards"]]
        output.append(RunRequest(agency=agency, date_from=min(date(2021,4,1), min(agency_dates)),
                                 date_to=max(date(2026,3,31), max(agency_dates)), flags=sorted(flags)))
    return output


def planted_recall(cases: list[dict], runs: list[dict]) -> dict:
    results = []
    for case in cases:
        for flag in case["flags"]:
            expected_tenders = set(case.get("expected_tenders", {}).get(flag, [award["tender_no"] for award in case["awards"]]))
            expected = {(award["tender_no"], award["supplier_name"]) for award in case["awards"] if award["tender_no"] in expected_tenders}
            if not expected:
                raise ValueError("A planted flag needs at least one expected award")
            eligible = [run for run in runs if covers(run["request"], case, flag, run["checks"])]
            completed = [run for run in eligible if flag not in run["coverage_gaps"]]
            observed = {(f.tender_no, f.supplier_name) for run in completed for f in run["findings"] if f.flag_id == flag}
            found = expected.intersection(observed)
            negatives = set(case.get("not_expected_tenders", {}).get(flag, []))
            unexpected = sorted(tender for tender, _ in observed if tender in negatives)
            results.append({"case_id": case["case_id"], "flag_id": flag, "evaluated": bool(completed),
                            "expected_awards": len(expected), "found_awards": len(found),
                            "missed_tenders": sorted(tender for tender, supplier in expected - found),
                            "recall": len(found) / len(expected), "case_caught": expected <= observed,
                            "negative_control_hits": unexpected})
    expected = sum(row["expected_awards"] for row in results)
    found = sum(row["found_awards"] for row in results)
    case_ids = {row["case_id"] for row in results}
    caught_cases = sum(all(row["case_caught"] for row in results if row["case_id"] == case_id) for case_id in case_ids)
    return {"stage": "SQL candidate findings; no Critic, Risk or memory suppression applied",
            "cases": len(case_ids), "cases_caught": caught_cases,
            "case_flag_pairs": len(results), "case_flags_evaluated": sum(row["evaluated"] for row in results),
            "case_flags_caught": sum(row["case_caught"] for row in results),
            "expected_awards": expected, "found_awards": found,
            "award_recall": found / expected if expected else None,
            "case_flag_recall": sum(row["case_caught"] for row in results) / len(results) if results else None,
            "case_recall": caught_cases / len(case_ids) if case_ids else None,
            "negative_controls_passed": not any(row["negative_control_hits"] for row in results),
            "results": results}


def load_precision_labels(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"finding_id", "label", "review_status", "reviewer", "reason"}.issubset(reader.fieldnames or []):
            raise ValueError("Precision labels need finding_id, label, review_status, reviewer and reason columns")
        rows = list(reader)
    seen = set()
    for row in rows:
        row["label"] = row["label"].strip().lower()
        if not row["finding_id"].strip() or row["finding_id"] in seen:
            raise ValueError("Precision labels need unique nonempty finding IDs")
        seen.add(row["finding_id"])
        if row["review_status"] not in {"pending", "human_reviewed", "agent_reviewed"}:
            raise ValueError("Unknown precision review status")
        if row["label"] not in {"", "plausible", "explained", "unclear"}:
            raise ValueError("Unknown precision label")
        if row["review_status"] == "pending" and row["label"]:
            raise ValueError("Pending precision rows must not contain guessed labels")
        if row["review_status"] != "pending" and (not row["label"] or not row["reviewer"].strip() or not row["reason"].strip()):
            raise ValueError("Reviewed precision rows require a label, reviewer and reason")
    return rows


def precision_metrics(labels: list[dict], candidates: dict) -> dict:
    relevant = [row for row in labels if row["finding_id"] in candidates]
    human = [row for row in relevant if row["review_status"] == "human_reviewed"]
    counts = Counter(row["label"] for row in human)
    decided = counts["plausible"] + counts["explained"]
    return {"status": "measured" if decided else "not_measured",
            "definition": "plausible / (plausible + explained); unclear and pending excluded. Plausibility is not proof of wrongdoing.",
            "precision": counts["plausible"] / decided if decided else None,
            "plausible": counts["plausible"], "explained": counts["explained"], "unclear": counts["unclear"],
            "decided": decided, "human_reviewed": len(human),
            "pending": sum(row["review_status"] == "pending" for row in relevant),
            "agent_reviewed_excluded": sum(row["review_status"] == "agent_reviewed" for row in relevant),
            "unmatched_labels": sum(row["finding_id"] not in candidates for row in labels),
            "nonplanted_candidates": len(candidates),
            "review_coverage": len(human) / len(candidates) if candidates else None}


def create_review_queue(path: Path, candidates: dict, limit: int = 30) -> bool:
    """Create pending rows only; an existing review file is never overwritten."""
    if path.exists():
        return False
    selected = sorted(candidates.values(), key=lambda f: (-(f.awarded_amt or 0), f.finding_id))[:limit]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=PRECISION_FIELDS)
        writer.writeheader()
        for f in selected:
            writer.writerow({"finding_id": f.finding_id, "flag_id": f.flag_id, "tender_no": f.tender_no,
                             "agency": f.agency, "awarded_amt": f.awarded_amt, "metric_name": f.metric_name,
                             "metric_value": f.metric_value, "threshold": f.threshold,
                             "evidence_query_id": f.evidence[0].query_id if f.evidence else "",
                             "label": "", "review_status": "pending", "reviewer": "", "reason": ""})
    return True


class LiveSQL:
    def __init__(self, deadline: float):
        self.deadline = deadline
        self.calls = []
        self.scope = "startup"

    def __call__(self, sql, **kwargs):
        from app.adapters.zetaris import run_sql
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Evaluation time budget exhausted")
        started = time.monotonic()
        result = run_sql(sql, limit=100000, timeout=min(90, remaining), retries=0)
        if result.replayed:
            raise ValueError("Live evaluation cannot use replayed results")
        if result.total is not None and int(result.total) > len(result.rows):
            raise ValueError("Truncated SQL result cannot be scored")
        self.calls.append({"scope": self.scope, "query_id": result.query_id, "rows": len(result.rows),
                           "runtime_seconds": round(time.monotonic() - started, 3)})
        return result


def run_request(request: RunRequest, sql: LiveSQL, trace_dir: Path, index: int, implemented: list[str], *, supplemental=False) -> dict:
    started = time.monotonic()
    sql.scope = ("supplemental_" if supplemental else "sample_") + str(index)
    checks = list(dict.fromkeys(request.flags or implemented))
    tracer = Tracer(f"run_eval_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}_{index}", logs_dir=trace_dir)
    deps = Deps(tracer=tracer, sql=sql, write_files=False)
    state = {"request": request, "plan": Plan(checks=checks), "matches": {}, "retries": {}}
    state.update(resolver.make(deps)(state))  # Read the crosswalk; do not resolve/write source data during scoring.
    state.update(analyst.make(deps)(state))
    return {"request": request, "checks": checks, "findings": state["findings"],
            "coverage_gaps": state.get("coverage_gaps", []), "check_errors": state.get("check_errors", {}),
            "runtime_seconds": round(time.monotonic() - started, 3), "trace_path": str(tracer.path),
            "supplemental": supplemental}


def summarize_run(run: dict) -> dict:
    return {"request": run["request"].model_dump(mode="json"), "checks": run["checks"],
            "status": "partial" if run["coverage_gaps"] else "success", "coverage_gaps": run["coverage_gaps"],
            "findings": len(run["findings"]), "findings_by_flag": dict(Counter(f.flag_id for f in run["findings"])),
            "runtime_seconds": run["runtime_seconds"], "trace_path": run["trace_path"],
            "supplemental": run["supplemental"]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, nargs=3, default=[ROOT / f"input_examples/example_{n}.json" for n in (1,2,3)])
    parser.add_argument("--output", type=Path, default=ROOT / "output_examples/metrics.json")
    parser.add_argument("--entity-labels", type=Path, default=ROOT / "data/eval/entity_labels.csv")
    parser.add_argument("--precision-labels", type=Path, default=ROOT / "data/eval/precision_review.csv")
    parser.add_argument("--timeout", type=float, default=600)
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 600:
        parser.error("--timeout must be between 1 and 600 seconds")
    started = time.monotonic()
    os.environ["SAMPLE_MODE"] = "false"
    from app.adapters.config import get_settings
    get_settings.cache_clear()
    requests = [RunRequest.model_validate(json.loads(path.read_text(encoding="utf-8"))) for path in args.inputs]
    if any(req.date_to < req.date_from for req in requests):
        raise ValueError("Sample request date range is reversed")
    cases = json.loads((ROOT / "data/eval/planted.json").read_text(encoding="utf-8"))["cases"]
    load_precision_labels(args.precision_labels)  # Validate existing labels before expensive live work.
    trace_dir = ROOT / "logs" / f"eval_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}"
    sql = LiveSQL(started + args.timeout)
    implemented = available_checks()
    runs = []
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "mode": "live_checks",
              "pipeline_agents": ["Resolver crosswalk read", "Analyst"], "complete": False,
              "precision": {"status": "not_measured", "precision": None}, "errors": []}
    try:
        for index, request in enumerate(requests, 1):
            print(f"Sample {index}/3: {request.agency}", flush=True)
            runs.append(run_request(request, sql, trace_dir, index, implemented))
        for index, request in enumerate(supplemental_requests(requests, cases, implemented), 4):
            print(f"Supplemental planted scope: {request.agency}, {request.flags}", flush=True)
            runs.append(run_request(request, sql, trace_dir, index, implemented, supplemental=True))
        report["planted"] = planted_recall(cases, runs)
        sql.scope = "resolver_accuracy"
        print("Evaluating Resolver labels against fresh registry data", flush=True)
        resolver_report = evaluate_live(args.entity_labels, sql_fn=sql)
        # No supplier names or personal data are copied into the combined public metrics.
        resolver_report.pop("predictions", None)
        report["resolver"] = resolver_report
        planted_awards = {(case["agency"], award["tender_no"]) for case in cases for award in case["awards"]}
        candidates = {f.finding_id: f for run in runs if not run["supplemental"] for f in run["findings"]
                      if (f.agency, f.tender_no) not in planted_awards}
        created = create_review_queue(args.precision_labels, candidates)
        precision_labels = load_precision_labels(args.precision_labels)
        report["precision"] = {**precision_metrics(precision_labels, candidates), "labels_path": str(args.precision_labels),
                               "queue_created": created, "queue_selection": "Top 30 nonplanted sample findings by award value; no supplier names or addresses"}
        calls = resolver_report["llm_calls"]
        report["tokens"] = {"llm_calls": calls, "total_tokens": 0 if calls == 0 else None,
                            "provider_reported_total_tokens": None,
                            "status": "no_llm_calls" if calls == 0 else "not_collected",
                            "note": "SQL checks use no LLM. Resolver tie-break usage is not estimated; unknown provider usage remains null."}
        report["complete"] = (not any(run["coverage_gaps"] for run in runs)
                              and not resolver_report["llm_failed_batches"]
                              and all(row["evaluated"] for row in report["planted"]["results"]))
        report["quality_checks_passed"] = (report["planted"]["case_recall"] == 1
                                           and report["planted"]["negative_controls_passed"])
    except Exception as exc:
        report["errors"].append({"type": type(exc).__name__, "scope": sql.scope})
        print(f"Evaluation incomplete ({type(exc).__name__}); preserving measured progress", flush=True)
    report["samples"] = [summarize_run(run) for run in runs if not run["supplemental"]]
    report["supplemental_scopes"] = [summarize_run(run) for run in runs if run["supplemental"]]
    report["sql_calls"] = sql.calls
    report["runtime_seconds"] = round(time.monotonic() - started, 3)
    report["limitations"] = ["Check-level evaluation does not measure Critic acceptance, memory suppression, ranking or memo quality.",
        "Planted recall uses fictional cases and does not establish precision on real awards.",
        "Precision is unmeasured until humans label findings; unclear, pending and agent reviews are excluded from the precision denominator.",
        "Resolver accuracy is an agent-reviewed, positive-heavy in-sample diagnostic; human-reviewed accuracy remains separate.",
        "R5 semantic scores and R6 keyword categories are uncalibrated screening heuristics."]
    report["provenance"] = {"inputs": [{"file": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in args.inputs],
        "evaluator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "check_sql_sha256": {flag: hashlib.sha256((ROOT / "sql/checks" / f"{flag}.sql").read_bytes()).hexdigest() for flag in implemented},
        "planted_sha256": hashlib.sha256((ROOT / "data/eval/planted.json").read_bytes()).hexdigest(),
        "precision_labels_sha256": hashlib.sha256(args.precision_labels.read_bytes()).hexdigest() if args.precision_labels.exists() else None}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {args.output}; complete={report['complete']}; runtime={report['runtime_seconds']}s", flush=True)
    return 0 if report["complete"] and report.get("quality_checks_passed") else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"Evaluation could not start ({type(exc).__name__}). Check input and label files; no new results claimed.", file=sys.stderr)
        sys.exit(1)
