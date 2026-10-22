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
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "done" and len(body["memo"]["findings"]) == 1
    ev = c.get(f"/runs/{body['run_id']}/events")
    assert ev.text.count("data:") >= 8 and "event: end" in ev.text
    assert c.get("/runs/run_nope").status_code == 404 and c.get("/runs/..%2Fx").status_code == 404
