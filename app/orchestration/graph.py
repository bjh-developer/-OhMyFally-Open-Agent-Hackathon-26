"""LangGraph wiring: gate -> planner -> resolver -> plan_review (-> planner once) -> analyst -> critic -(loops)-> risk -> reporter."""
from __future__ import annotations

import re
from datetime import date

from langgraph.graph import END, START, StateGraph

from .. import replay
from ..adapters.nightshift import budget_scope
from ..agents import analyst, critic, planner, reporter, resolver, risk
from ..schemas import Memo, RunRequest
from ..tracing import Tracer
from .state import Deps, RunState

_FLAG = re.compile(r"^R\d{1,2}$")


def gate(deps: Deps):
    def node(state: RunState) -> dict:
        req = state["request"]
        reason = None
        if not req.agency.strip():
            reason = "no agency given"
        elif req.date_to < req.date_from:
            reason = "date_to is before date_from"
        elif (req.date_to - req.date_from).days > 366 * 6:
            reason = "period longer than 6 years is out of scope"
        elif any(not _FLAG.match(f) for f in req.flags):
            reason = "unknown flag id in request"
        deps.tracer.emit("GateAgent", "scope_check", input=req.model_dump_json(), output=reason or "in scope",
                         status="failed" if reason else "success")
        return {"rejected_reason": reason}

    return node


def build_graph(deps: Deps):
    g = StateGraph(RunState)
    g.add_node("gate", gate(deps))
    g.add_node("planner", planner.make(deps))
    g.add_node("resolver", resolver.make(deps))
    g.add_node("plan_review", critic.make_plan_review(deps))
    g.add_node("analyst", analyst.make(deps))
    g.add_node("critic", critic.make(deps))
    g.add_node("risk", risk.make(deps))
    g.add_node("reporter", reporter.make(deps))
    g.add_edge(START, "gate")
    g.add_conditional_edges("gate", lambda s: "end" if s.get("rejected_reason") else "planner", {"end": END, "planner": "planner"})
    g.add_edge("planner", "resolver")
    g.add_edge("resolver", "plan_review")
    g.add_conditional_edges("plan_review", lambda s: "planner" if s.get("replan_requested") else "analyst", {"planner": "planner", "analyst": "analyst"})
    g.add_edge("analyst", "critic")
    g.add_conditional_edges("critic", lambda s: s["route"], {"analyst": "analyst", "resolver": "resolver", "risk": "risk"})
    g.add_conditional_edges("risk", lambda s: s["route"], {"planner": "planner", "reporter": "reporter"})
    g.add_edge("reporter", END)
    return g.compile()


def run_investigation(request: RunRequest, deps: Deps, *, llm_cap: int | None = None) -> RunState:
    """Run the whole graph. Returns final state (``memo`` is None when the gate rejected the request)."""
    deps.tracer.emit("Orchestrator", "start_run", input=request.model_dump_json(), output=f"run {deps.tracer.run_id}")
    graph = build_graph(deps)
    replay_mark = replay.mark()
    with budget_scope(llm_cap) as budget:
        final = graph.invoke({"run_id": deps.tracer.run_id, "request": request, "matches": {}, "retries": {}, "resolver_retry": 0},
                             config={"recursion_limit": 40})
    served = replay.served_since(replay_mark)
    if final.get("memo"):
        final["memo"].stats["llm_calls"] = budget.used
        if served:  # some answers came from a recorded run: say so in the memo
            replay.annotate_memo(final["memo"], served)
            if deps.write_files:
                (deps.tracer.dir / f"{final['memo'].run_id}.md").write_text(final["memo"].markdown, encoding="utf-8")
        if deps.write_files:
            (deps.tracer.dir / f"{final['memo'].run_id}.memo.json").write_text(final["memo"].model_dump_json(indent=2), encoding="utf-8")
    deps.tracer.emit("Orchestrator", "end_run", output=f"llm_calls={budget.used}; " + (f"{len(served)} replayed step(s); " if served else "") + ("memo ready" if final.get("memo") else f"rejected: {final.get('rejected_reason')}"),
                     status="success" if final.get("memo") else "failed", replayed=bool(served))
    return final
