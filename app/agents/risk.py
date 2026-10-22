"""Risk (deep lane): wording gate, escalation, ranking scores, and at most one replan request."""
from __future__ import annotations

import math

from pydantic import BaseModel

from ..checks.rules import banned_hits, red_flags
from ..checks.runner import available_checks
from ..orchestration.state import Deps, RunState
from .common import compact_finding, dumps

NAME = "RiskAgent"
ESCALATE_BELOW = 0.7


class Score(BaseModel):
    finding_id: str
    priority: float  # 0..100
    reason: str = ""


class Scores(BaseModel):
    scores: list[Score]


def _fallback_score(f) -> float:
    amt = f.awarded_amt or 0
    return round(min(100.0, 40 * f.confidence + 10 * math.log10(amt + 1) + (10 if red_flags().get(f.flag_id, {}).get("priority") == "must" else 0)), 1)


def make(deps: Deps):
    def risk(state: RunState) -> dict:
        findings = [f.model_copy(deep=True) for f in (state.get("findings") or [])]
        plan = state["plan"]
        live = [f for f in findings if f.status in ("accepted", "escalated")]
        violations = [f.finding_id for f in live if banned_hits(f.summary)]
        # escalation
        escalated = []
        for f in live:
            should_have = red_flags().get(f.flag_id, {}).get("priority") != "must"
            if f.status == "accepted" and (f.confidence < ESCALATE_BELOW or should_have):
                f.status = "escalated"
                f.notes.append("Escalated to human review: " + ("low confidence" if f.confidence < ESCALATE_BELOW else "should-have flag"))
                escalated.append(f.finding_id)
        # scoring
        scores = {f.finding_id: _fallback_score(f) for f in live}
        res = None
        if live:
            try:
                res = deps.llm("deep", [
                    {"role": "system", "content": "You triage procurement anomalies for an agency auditor. Score each finding's review priority 0-100 "
                     "from the evidence only (amount, strength of the metric versus its threshold, confidence). These are anomalies for review, not conclusions."},
                    {"role": "user", "content": dumps({"findings": [compact_finding(f) for f in live[:20]],
                                                       "answer_format": {"scores": [{"finding_id": "...", "priority": 50, "reason": "short"}]}})},
                ], json_schema=Scores, max_tokens=3000)
                for s in res.parsed.scores:
                    if s.finding_id in scores:
                        scores[s.finding_id] = max(0.0, min(100.0, s.priority))
            except Exception:
                pass
        # replan: planned must-have coverage missing, once
        gaps = state.get("coverage_gaps") or []
        have = set(available_checks())
        missed_must = [fid for fid, m in red_flags().items() if m.get("priority") == "must" and fid in have and fid not in plan.checks
                       and (not state["request"].flags or fid in state["request"].flags)]
        replan = bool(missed_must or [g for g in gaps if g in have]) and plan.replan_count < deps.max_replans
        route = "planner" if replan else ("reporter")
        notes = f"missing must-have checks {missed_must}; failed checks {gaps}" if replan else ""
        out = dict(input=f"{len(live)} live findings", output=f"{len(escalated)} escalated, {len(violations)} wording violations, replan={replan}. {notes}",
                   target="PlannerAgent" if replan else "ReporterAgent", status="needs_revision" if replan or violations else "success")
        if res:
            deps.tracer.llm(NAME, "assess_risk", res, **out)
        else:
            deps.tracer.emit(NAME, "assess_risk", **out)
        return {"findings": findings, "scores": scores, "wording_violations": violations, "replan_requested": replan,
                "replan_notes": notes, "route": route}

    return risk
