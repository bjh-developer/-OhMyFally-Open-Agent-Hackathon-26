"""Analyst: runs sql/checks/R*.sql through Zetaris and builds Findings with evidence."""
from __future__ import annotations

from ..checks.runner import MATCH_DEPENDENT, available_checks, run_check, to_findings
from ..orchestration.state import Deps, RunState
from ..schemas import Finding

NAME = "AnalystAgent"


def make(deps: Deps):
    def analyst(state: RunState) -> dict:
        req, plan = state["request"], state["plan"]
        matches = state.get("matches") or {}
        revise = state.get("revise_checks") or []
        retries = dict(state.get("retries") or {})
        errors = dict(state.get("check_errors") or {})
        todo = revise or plan.checks
        have = set(available_checks())
        kept = [f for f in (state.get("findings") or []) if f.flag_id not in todo]
        new: list[Finding] = []
        gaps: list[str] = [g for g in (state.get("coverage_gaps") or []) if g not in todo]
        for flag in todo:
            if flag in revise:
                retries[flag] = retries.get(flag, 0) + 1
            if flag not in have:
                gaps.append(flag)
                deps.tracer.emit(NAME, f"run_check:{flag}", input=flag, output="no SQL for this check yet", status="partial_success")
                continue

            def conf(row, flag=flag) -> float:
                if flag not in MATCH_DEPENDENT:
                    return 0.8 if flag == "R8" else 1.0
                m = matches.get(row.get("supplier_name"))
                return m.confidence if m else 0.0

            try:
                run = run_check(flag, agency=req.agency, date_from=req.date_from, date_to=req.date_to, run_sql=deps.sql)
            except Exception as e:
                gaps.append(flag)
                errors[flag] = f"{type(e).__name__}: {str(e)[:200]}"
                deps.tracer.emit(NAME, f"run_check:{flag}", input=flag, output=errors[flag], status="failed",
                                 retry=retries.get(flag, 0), query_ids=[getattr(e, "query_id", None)] if getattr(e, "query_id", None) else [])
                continue
            fs = to_findings(run, conf)
            new += fs
            errors.pop(flag, None)
            deps.tracer.emit(NAME, f"run_check:{flag}", input=f"{flag} {req.agency} {req.date_from}..{req.date_to}",
                             output=f"{len(fs)} candidate findings from {len(run.rows)} rows", target="CriticAgent",
                             retry=retries.get(flag, 0), status="success", query_ids=[run.result.query_id],
                             confidence=(sum(f.confidence for f in fs) / len(fs)) if fs else None)
        return {"findings": kept + new, "retries": retries, "revise_checks": [], "coverage_gaps": list(dict.fromkeys(gaps)),
                "check_errors": errors}

    return analyst
