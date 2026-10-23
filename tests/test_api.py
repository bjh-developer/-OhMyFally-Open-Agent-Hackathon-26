from fastapi.testclient import TestClient

from app import api
from app.checks import runner
from app.orchestration.state import Deps
from tests.fakes import FakeLLM, FakeSQL


def test_post_run_wait_and_events(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "CHECKS_DIR", runner.ROOT / "tests" / "fixtures" / "checks")
    monkeypatch.setattr(api, "make_deps", lambda tr: Deps(tracer=tr, sql=FakeSQL(), llm=FakeLLM(), write_files=False))
    monkeypatch.setattr(api, "Tracer", lambda rid: __import__("app.tracing", fromlist=["Tracer"]).Tracer(rid, tmp_path))
    c = TestClient(api.app)
    r = c.post("/run?wait=true", json={"agency": "Housing and Development Board", "date_from": "2025-01-01", "date_to": "2025-12-31"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "done" and len(body["memo"]["findings"]) == 1
    ev = c.get(f"/runs/{body['run_id']}/events")
    assert ev.text.count("data:") >= 8 and "event: end" in ev.text
    assert c.get("/runs/run_nope").status_code == 404 and c.get("/runs/..%2Fx").status_code == 404


REQ = {"agency": "Housing and Development Board", "date_from": "2025-01-01", "date_to": "2025-12-31"}


def _client(monkeypatch, tmp_path, deps_factory=None):
    monkeypatch.setattr(runner, "CHECKS_DIR", runner.ROOT / "tests" / "fixtures" / "checks")
    monkeypatch.setattr(api, "make_deps", deps_factory or (lambda tr: Deps(tracer=tr, sql=FakeSQL(), llm=FakeLLM(), write_files=False)))
    monkeypatch.setattr(api, "Tracer", lambda rid: __import__("app.tracing", fromlist=["Tracer"]).Tracer(rid, tmp_path))
    return TestClient(api.app)


def test_post_run_defaults_to_waiting_and_returns_the_memo(monkeypatch, tmp_path):
    r = _client(monkeypatch, tmp_path).post("/run", json=REQ)  # the plain curl from the self-check
    assert r.status_code == 200
    b = r.json()
    assert b["status"] == "done" and b["memo"]["findings"] and b["trace_id"] == b["run_id"]
    assert b["execution_time_seconds"] >= 0


def test_post_run_wait_false_is_async(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    r = c.post("/run?wait=false", json=REQ)
    assert r.status_code == 202 and r.json()["run_id"].startswith("run_")


def test_rejected_run_is_a_structured_error(monkeypatch, tmp_path):
    r = _client(monkeypatch, tmp_path).post("/run", json={**REQ, "date_to": "2024-01-01"})
    b = r.json()
    assert r.status_code == 422 and b["status"] == "error"
    assert set(b) == {"run_id", "status", "error", "trace_id", "execution_time_seconds"}
    assert b["error"]["type"] == "request_rejected" and b["error"]["recoverable"] is True and "date_to" in b["error"]["message"]


def test_crashing_run_returns_error_without_a_stack_trace(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise RuntimeError("secret internals /Users/x/app.py line 3")

    c = _client(monkeypatch, tmp_path)
    monkeypatch.setattr(api, "run_investigation", boom)
    r = c.post("/run", json=REQ)
    b = r.json()
    assert r.status_code == 500 and b["status"] == "error" and b["error"]["type"] == "run_failed" and b["error"]["recoverable"] is False
    assert "Traceback" not in r.text and "/Users/" not in r.text and b["trace_id"] == b["run_id"]


def test_bad_body_is_a_structured_error(monkeypatch, tmp_path):
    r = _client(monkeypatch, tmp_path).post("/run", json={"agency": "X"})
    b = r.json()
    assert r.status_code == 422 and b["status"] == "error" and b["error"]["type"] == "invalid_request" and b["run_id"] is None
