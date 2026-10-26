"""SAMPLE_MODE with an empty .env: all three input_examples complete from recorded data, with no network."""
import json
from pathlib import Path

import httpx
import pytest

from app import replay
from app.adapters import config
from app.orchestration.factory import make_deps
from app.orchestration.graph import run_investigation
from app.schemas import RunRequest
from app.tracing import Tracer

EXAMPLES = sorted((config.ROOT / "input_examples").glob("example_*.json"))


@pytest.fixture
def offline(monkeypatch):
    for k in ("ZETARIS_API_KEY", "METERLESS_RUNTIME_TOKEN", "REPLAY_SET"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("SAMPLE_MODE", "true")
    monkeypatch.setattr("app.adapters.config.load_dotenv", lambda *a, **k: None)  # an empty .env
    config.get_settings.cache_clear()
    replay.reset()

    def no_network(self, *a, **k):
        raise AssertionError("offline sample mode touched the network")

    monkeypatch.setattr(httpx.Client, "send", no_network)
    yield
    config.get_settings.cache_clear()
    replay.reset()


def test_placeholder_credentials_count_as_unset(monkeypatch):
    monkeypatch.setenv("ZETARIS_API_KEY", "your-zetaris-api-key")
    monkeypatch.setenv("METERLESS_RUNTIME_TOKEN", "your-nightshift-runtime-token")
    monkeypatch.setenv("SAMPLE_MODE", "true")
    config.get_settings.cache_clear()
    assert config.get_settings().offline is True
    monkeypatch.setenv("ZETARIS_API_KEY", "zk-real")
    config.get_settings.cache_clear()
    assert config.get_settings().offline is False
    monkeypatch.setenv("ZETARIS_API_KEY", "")
    monkeypatch.setenv("METERLESS_RUNTIME_TOKEN", "")
    monkeypatch.setenv("SAMPLE_MODE", "false")
    config.get_settings.cache_clear()
    assert config.get_settings().offline is False


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.stem for p in EXAMPLES])
def test_input_example_completes_offline_and_is_labelled(offline, path, tmp_path):
    req = RunRequest.model_validate(json.loads(path.read_text()))
    tr = Tracer("run_offline_t", tmp_path)
    final = run_investigation(req, make_deps(tr, write_files=False))
    memo = final["memo"]
    assert memo is not None and memo.agency == req.agency and memo.markdown
    assert memo.limitations[0].startswith(replay.MEMO_LINE) and replay.MEMO_LINE in memo.markdown
    assert memo.stats["replayed"]["zetaris"] > 0
    assert all(e.status != "failed" for e in tr.events)
    zq = [q for e in tr.events for q in e.zetaris_query_ids]
    assert zq and all(q.startswith("replay:") for q in zq)
    assert any(e.action == "memory_skipped" for e in tr.events)


def test_unrecorded_request_is_refused_not_faked(offline, tmp_path):
    req = RunRequest(agency="Ministry of Nothing", date_from="2020-01-01", date_to="2020-12-31")
    tr = Tracer("run_offline_u", tmp_path)
    final = run_investigation(req, make_deps(tr, write_files=False))
    assert final["memo"] is None and "recorded" in final["rejected_reason"].lower()


def test_missing_model_reply_falls_back_without_a_model(offline, tmp_path, monkeypatch):
    """Drop every recorded model reply: the memo still comes out, built by the rule-based fallbacks and labelled."""
    req = RunRequest.model_validate(json.loads(EXAMPLES[0].read_text()))
    replay.use_for(req)
    monkeypatch.setattr(replay.store(), "entries", [])
    tr = Tracer("run_offline_f", tmp_path)
    final = run_investigation(req, make_deps(tr, write_files=False))
    memo = final["memo"]
    assert memo is not None and memo.findings
    assert any("rule-based fallback" in x for x in memo.limitations)
    assert not any(e.meterless_receipt_ids for e in tr.events)
