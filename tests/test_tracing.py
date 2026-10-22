import json

from app.tracing import Tracer


def test_jsonl_lines_match_contract(tmp_path):
    t = Tracer("run_x", tmp_path)
    got = []
    t.subscribe(got.append)
    t.emit("CriticAgent", "validate_claims", input="in", output="out", target="AnalystAgent", confidence=0.82,
           retry=1, status="needs_revision", query_ids=["q1", "q2"], receipt_ids=["rcpt_1"])
    t.emit("PlannerAgent", "plan")
    lines = [json.loads(x) for x in (tmp_path / "run_x.jsonl").read_text().splitlines()]
    assert len(lines) == 2 == len(got)
    first = lines[0]
    for k in ("timestamp", "trace_id", "agent_name", "action", "input_summary", "output_summary", "target_agent",
              "confidence", "retry_count", "status", "zetaris_query_ids", "meterless_receipt_id"):
        assert k in first
    assert first["trace_id"] == "run_x" and first["zetaris_query_ids"] == ["q1", "q2"] and first["meterless_receipt_id"] == "rcpt_1"
    assert first["status"] == "needs_revision"


def test_run_id_validated_and_secrets_redacted(tmp_path):
    import pytest
    for bad in ("../x", "run_/../../etc", "x", "run_a/b"):
        with pytest.raises(ValueError):
            Tracer(bad, tmp_path)
    t = Tracer("run_ok", tmp_path)
    ev = t.emit("A", "b", input="auth Bearer abcdefghijklmnop1234", output="api_key=supersecretvalue99",
                egress={"destination": "nvidia", "coverage": "x", "sent": {"prompt_chars": 5, "redacted": [], "context_sources": ["messages"]}})
    assert "abcdefghijklmnop1234" not in ev.input_summary and "supersecretvalue99" not in ev.output_summary
    assert ev.egress == {"destination": "nvidia", "coverage": "x", "prompt_chars": 5, "redacted": 0, "withheld": 0}
