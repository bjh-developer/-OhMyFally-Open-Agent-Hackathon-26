"""Planner (deep lane): decides which checks to run. Constrained to checks that exist."""
from __future__ import annotations

from pydantic import BaseModel

from ..checks.rules import red_flags
from ..checks.runner import available_checks
from ..orchestration.state import Deps, RunState
from ..schemas import Plan
from .common import dumps

NAME = "PlannerAgent"


class PlanOut(BaseModel):
    checks: list[str]
    rationale: str = ""


def make(deps: Deps):
    def planner(state: RunState) -> dict:
        req = state["request"]
        have = available_checks()
        catalog = {}
        try:
            r = deps.sql("SHOW DATASOURCES")
            catalog = {"datasources": [x[0] for x in r.rows][:10]}
            qids = [r.query_id]
        except Exception as e:  # catalog is context only, never fatal
            qids = []
            catalog = {"error": str(e)[:100]}
        recall = []
        if deps.hmem:
            try:
                recall = deps.hmem.recall(agency=req.agency, uen=None, flag_id=None, query=f"{req.agency} procurement review")
            except Exception:
                recall = []
        wanted = [f for f in req.flags if f in have] if req.flags else []
        notes = state.get("replan_notes") or ""
        msgs = [
            {"role": "system", "content": "You are the Planner of a procurement-integrity screening system for a government agency auditor. "
             "Pick which red-flag checks to run. Findings are anomalies for review, never conclusions."},
            {"role": "user", "content": dumps({
                "request": req.model_dump(mode="json"),
                "implemented_checks": {f: red_flags().get(f, {}).get("name", f) for f in have},
                "catalog": catalog, "memory_recall": [m.get("content") for m in recall][:5],
                "replan_notes": notes,
                "instruction": "Return {\"checks\": [flag ids from implemented_checks], \"rationale\": \"one or two sentences\"}. "
                               "Include every check the auditor asked for. Default to all implemented checks.",
            })},
        ]
        status, rationale, checks, res = "success", "", [], None
        try:
            res = deps.llm("deep", msgs, json_schema=PlanOut, max_tokens=2500)
            out: PlanOut = res.parsed
            checks = [c for c in dict.fromkeys(out.checks) if c in have]
            rationale = out.rationale
        except Exception as e:
            status, rationale = "partial_success", f"planner LLM failed ({type(e).__name__}); using deterministic plan"
        for f in wanted:  # auditor's explicit asks always run
            if f not in checks:
                checks.append(f)
        if not checks:
            checks = wanted or have
        plan = Plan(checks=checks, params={"agency": req.agency, "date_from": str(req.date_from), "date_to": str(req.date_to)},
                    sources=["gebiz_pg.awards", "gebiz_pg.supplier_xwalk", "ACRA_FILES.entities"], rationale=rationale,
                    replan_count=(state.get("plan").replan_count + 1) if state.get("plan") and state.get("replan_requested") else 0)
        ev = dict(input=f"agency={req.agency} {req.date_from}..{req.date_to} flags={req.flags or 'auto'}",
                  output=f"checks={checks} {rationale}", target="ResolverAgent", status=status, query_ids=qids)
        if res:
            deps.tracer.llm(NAME, "plan", res, **ev)
        else:
            deps.tracer.emit(NAME, "plan", **ev)
        return {"plan": plan, "replan_requested": False, "coverage_gaps": [f for f in req.flags if f not in have], "check_errors": {}}

    return planner
