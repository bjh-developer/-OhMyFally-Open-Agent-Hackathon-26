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


SCORE_BATCH = 7  # findings per deep-lane scoring call

def _fallback_score(f) -> float:
    """Deterministic 0-100 priority: match confidence, award size, flag priority, and how far past its threshold."""
    amt = f.awarded_amt or 0
    must = red_flags().get(f.flag_id, {}).get("priority") == "must"
    score = 30 * f.confidence + 6 * math.log10(amt + 1) + (10 if must else 0)
    try:
        m, t = float(f.metric_value), float(f.threshold)
        if f.flag_id == "R1" and t > 0:
            score += 12 * max(0.0, (t - m) / t)  # newer supplier = higher
        elif f.flag_id == "R4" and t > 0:
            score += 12 * min(1.0, max(0.0, (m - t) / t))
        elif f.flag_id == "R3":
            score += min(8.0, 2.0 * (m - t + 1))
    except (TypeError, ValueError):
        pass
    return round(min(100.0, score), 1)


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
        base = dict(scores)
        res = None
        ranked = sorted(live, key=lambda f: -base[f.finding_id])[:20]  # the model scores the top 20 by the deterministic score
        if live:
            # Score in small batches: one 20-finding call runs long enough for Nightshift to abort it (HTTP 499).
            for i in range(0, len(ranked), SCORE_BATCH):
                chunk = ranked[i:i + SCORE_BATCH]
                try:
                    r = deps.llm("deep", [
                        {"role": "system", "content": "You triage procurement anomalies for an agency auditor. Score each finding's review priority 0-100 "
                         "from the evidence only (amount, strength of the metric versus its threshold, confidence). These are anomalies for review, not conclusions. "
                         "Keep each reason under 15 words."},
                        {"role": "user", "content": dumps({"findings": [compact_finding(f) for f in chunk],
                                                           "answer_format": {"scores": [{"finding_id": "...", "priority": 50, "reason": "short"}]}})},
                    ], json_schema=Scores, max_tokens=2500)
                    res = r
                    for sc in r.parsed.scores:
                        if sc.finding_id in scores:  # blend so the model can reorder but not saturate the scale
                            scores[sc.finding_id] = round(0.6 * base[sc.finding_id] + 0.4 * max(0.0, min(100.0, sc.priority)), 1)
                except Exception:
                    pass  # this batch keeps its deterministic score
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
