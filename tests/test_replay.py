"""Replay mode: services down + SAMPLE_MODE=true -> recorded data, labelled; otherwise unchanged."""
import httpx
import pytest
from pydantic import BaseModel

from app import replay
from app.adapters import config
from app.adapters.nightshift import ChatResult, NightshiftError, chat
from app.adapters.zetaris import Result, ZetarisError, run_sql
from app.schemas import Memo
from app.tracing import Tracer

DEAD = "http://127.0.0.1:9"  # nothing listens on the discard port: connection refused


class Out(BaseModel):
    ok: bool


MSGS = [{"role": "system", "content": "You check claims."}, {"role": "user", "content": "claim A"}]


@pytest.fixture
def fixture_set(tmp_path):
    with replay.Recorder() as rec:
        replay.record_sql(Result(headers=["n"], rows=[["42"]], query_id="live-1", ms=7, sql="SELECT  count(*)\nFROM t;", total=1))
        replay.record_chat("fast", MSGS, ChatResult(content='{"ok": true}', receipt_id="rcpt_9", routed_model="nemotron",
                                                     latency_ms=500, usage={"prompt_tokens": 10}, prompt_chars=40))
    rec.save(tmp_path, {"name": "t"})
    return tmp_path


def _down(monkeypatch, path, sample="true"):
    monkeypatch.setenv("ZETARIS_REST_URL", DEAD)
    monkeypatch.setenv("METERLESS_BASE_URL", DEAD)
    monkeypatch.setenv("SAMPLE_MODE", sample)
    monkeypatch.setenv("REPLAY_SET", str(path))
    config.get_settings.cache_clear()
    replay.reset()


def test_zetaris_down_serves_recorded_result_labelled(fixture_set, monkeypatch):
    _down(monkeypatch, fixture_set)
    r = run_sql("SELECT count(*) FROM t")  # whitespace and trailing ; are normalised
    assert r.replayed and r.rows == [["42"]] and r.query_id.startswith("replay:")
    assert len(replay.served_since(0)) == 1


def test_zetaris_down_unrecorded_sql_still_raises(fixture_set, monkeypatch):
    _down(monkeypatch, fixture_set)
    with pytest.raises(ZetarisError):
        run_sql("SELECT something_else")


def test_sample_mode_off_never_replays(fixture_set, monkeypatch):
    _down(monkeypatch, fixture_set, sample="false")
    with pytest.raises(ZetarisError):
        run_sql("SELECT count(*) FROM t")
    with pytest.raises(NightshiftError):
        chat("fast", MSGS, Out)


def test_live_service_up_is_not_replayed(fixture_set, monkeypatch):
    _down(monkeypatch, fixture_set)
    ok = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"headers": ["n"], "data": [["7"]]})))
    r = run_sql("SELECT count(*) FROM t", client=ok)
    assert not r.replayed and r.rows == [["7"]] and replay.served_since(0) == []


def test_client_error_is_not_replayed(fixture_set, monkeypatch):
    _down(monkeypatch, fixture_set)
    bad = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(400, text="syntax")))
    with pytest.raises(ZetarisError):
        run_sql("SELECT count(*) FROM t", client=bad)


def test_nightshift_down_serves_recorded_reply_labelled(fixture_set, monkeypatch):
    _down(monkeypatch, fixture_set)
    res = chat("fast", MSGS, Out)
    assert res.replayed and res.parsed == Out(ok=True) and res.receipt_id == "replay:rcpt_9"
    assert res.latency_ms == 0 and "replayed" in res.routed_model and res.egress["destination"].startswith("replay")


def test_nightshift_template_match_when_user_prompt_differs(fixture_set, monkeypatch):
    _down(monkeypatch, fixture_set)
    other = [MSGS[0], {"role": "user", "content": "claim B"}]
    assert chat("fast", other, Out).replayed
    with pytest.raises(NightshiftError):  # different agent prompt: no recorded answer
        chat("fast", [{"role": "system", "content": "Something else"}], Out)


def test_nightshift_bad_schema_for_recorded_reply_raises(fixture_set, monkeypatch):
    class Other(BaseModel):
        needed: int

    _down(monkeypatch, fixture_set)
    with pytest.raises(NightshiftError):
        chat("fast", MSGS, Other)


def test_trace_and_memo_are_labelled(fixture_set, monkeypatch, tmp_path):
    _down(monkeypatch, fixture_set)
    run_sql("SELECT count(*) FROM t")
    res = chat("fast", MSGS, Out)
    tr = Tracer("run_t", tmp_path)
    ev = tr.llm("CriticAgent", "validate", res, output="fine")
    assert ev.replayed is True and ev.status == "success" and "[replayed" in ev.output_summary
    live = tr.emit("X", "y", output="live")
    assert live.replayed is None and '"replayed"' not in (tmp_path / "run_t.jsonl").read_text().splitlines()[-1]
    memo = Memo(run_id="run_t", agency="A", date_from="2024-04-01", date_to="2025-03-31", summary="s", findings=[],
                limitations=["R1: x"], markdown="# Memo\n\n## Limitations\n- R1: x\n")
    replay.annotate_memo(memo, replay.served_since(0))
    assert memo.limitations[0].startswith(replay.MEMO_LINE) and replay.MEMO_LINE in memo.markdown
    assert memo.stats["replayed"] == {"zetaris": 1, "nightshift": 1, "set": fixture_set.name}


def test_committed_hdb_set_replays_a_full_memo_with_services_down(monkeypatch, tmp_path):
    """Whole graph, both services on a dead port, committed fixture set: a labelled memo comes out."""
    from datetime import date

    from app.orchestration.factory import make_deps
    from app.orchestration.graph import run_investigation
    from app.schemas import RunRequest

    _down(monkeypatch, config.ROOT / "data" / "replay" / "hdb-fy2425")
    monkeypatch.setenv("HMEM_URL", DEAD)
    config.get_settings.cache_clear()
    tr = Tracer("run_replay_e2e", tmp_path)
    final = run_investigation(RunRequest(agency="Housing and Development Board", date_from=date(2024, 4, 1), date_to=date(2025, 3, 31)),
                              make_deps(tr, write_files=False))
    memo = final["memo"]
    assert memo is not None and memo.findings
    assert memo.limitations[0].startswith(replay.MEMO_LINE) and replay.MEMO_LINE in memo.markdown
    assert any(e.replayed for e in tr.events) and all(e.status != "failed" for e in tr.events)
