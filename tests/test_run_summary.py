import json

from fastapi.testclient import TestClient

from app import api
from app.run_summary import read_events, summarise


def ev(agent, ts, **kw):
    return {"timestamp": f"2026-10-23T02:53:{ts:02d}.000Z", "trace_id": "run_x", "agent_name": agent, "action": "a",
            "output_summary": "", "retry_count": 0, "status": "success", **kw}


CLEAN = [
    ev("Orchestrator", 0),
    ev("GateAgent", 1),
    ev("PlannerAgent", 5, target_agent="ResolverAgent", meterless_receipt_ids=["r1"], latency_ms=4000, zetaris_query_ids=["q1"]),
    ev("AnalystAgent", 7, target_agent="CriticAgent", zetaris_query_ids=["q2", "q3"]),
    ev("CriticAgent", 10, target_agent="RiskAgent", meterless_receipt_id="r2", latency_ms=2000, output_summary="0 issues; route=risk; revise=[] re-resolve=[]; "),
    ev("ReporterAgent", 20, meterless_receipt_ids=["r3"], latency_ms=9000, output_summary="memo with 5 findings (0 suppressed, 0 rejected)"),
    ev("Orchestrator", 21),
]


def test_clean_run():
    s = summarise(CLEAN)
    assert (s["critiques"], s["retries"], s["escalations"], s["replans"], s["loops"]) == (0, 0, 0, 0, [])
    assert s["llm_calls"] == 3 and s["zetaris_queries"] == 3 and s["duration_s"] == 21
    assert s["memory_hits"] == 0 and s["memory_tracked"] is False and s["cleared_by_memory"] == 0
    assert s["prompt_tokens"] is None
    pa = {a["agent"]: a for a in s["per_agent"]}
    assert "Orchestrator" not in pa and pa["ReporterAgent"]["time_s"] == 9 and pa["PlannerAgent"]["llm_calls"] == 1


def test_critique_retry_escalation():
    evs = CLEAN[:4] + [
        ev("CriticAgent", 10, target_agent="AnalystAgent", status="needs_revision", retry_count=1, meterless_receipt_id="r2",
           output_summary="3 issues; route=analyst; revise=['R1']; claim not supported by rows"),
        ev("AnalystAgent", 12, target_agent="CriticAgent", status="partial_success"),
        ev("CriticAgent", 14, target_agent="RiskAgent", retry_count=2, status="success"),
        ev("RiskAgent", 16, target_agent="PlannerAgent", status="escalated", output_summary="1 escalated, 0 wording violations, replan=True."),
    ]
    s = summarise(evs)
    assert s["critiques"] == 1 and s["retries"] == 2 and s["escalations"] == 1 and s["partial_success"] == 1 and s["replans"] == 1
    assert s["loops"][0] == {"from_agent": "CriticAgent", "to_agent": "AnalystAgent", "reason": "claim not supported by rows", "claims": 3}
    assert s["loops"][1]["to_agent"] == "PlannerAgent"


def test_memory_hits_and_tokens():
    evs = [ev("PlannerAgent", 1, memory_hits=2, usage={"prompt_tokens": 100, "completion_tokens": 10}),
           ev("CriticAgent", 3, memory_hits=1, prompt_tokens=50, completion_tokens=5),
           ev("ReporterAgent", 5, output_summary="memo with 4 findings (2 suppressed, 0 rejected)")]
    s = summarise(evs)
    assert s["memory_hits"] == 3 and s["memory_tracked"] and s["cleared_by_memory"] == 2
    assert (s["prompt_tokens"], s["completion_tokens"]) == (150, 15)


def test_empty_and_junk():
    s = summarise([])
    assert s["duration_s"] == 0 and s["loops"] == [] and s["llm_calls"] == 0
    assert summarise([{"agent_name": "X", "timestamp": "nope", "retry_count": None}])["retries"] == 0


def test_endpoint(tmp_path, monkeypatch):
    (tmp_path / "run_abc.jsonl").write_text("\n".join(json.dumps(e) for e in CLEAN) + "\nnot json\n")
    monkeypatch.setattr(api, "get_settings", lambda: type("S", (), {"logs_dir": tmp_path})())
    c = TestClient(api.app)
    r = c.get("/runs/run_abc/summary")
    assert r.status_code == 200 and r.json()["llm_calls"] == 3 and r.json()["run_id"] == "run_abc"
    assert c.get("/runs/run_abc/summary?view=public").status_code in (200, 503)
    assert c.get("/runs/run_nope/summary").status_code == 404
    assert len(read_events(tmp_path / "run_abc.jsonl")) == len(CLEAN)
