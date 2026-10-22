import json

import httpx
import pytest
from pydantic import BaseModel

from app.adapters.nightshift import CallCapExceeded, NightshiftError, budget_scope, chat, extract_json


def _resp(content, rid="rcpt_1"):
    return httpx.Response(200, json={
        "model": "nvidia/x", "choices": [{"message": {"content": content}}], "usage": {"total_tokens": 5},
        "meterless": {"receipt_id": rid, "routed_model": "nvidia/nemotron", "usage": {"latency_ms": 321}, "privacy": {"path": "cloud-ok"}},
    })


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_lane_headers_and_receipt():
    seen = []

    def h(req):
        seen.append(dict(req.headers))
        return _resp("hello")

    d = chat("deep", [{"role": "user", "content": "hi"}], client=_client(h))
    f = chat("fast", [{"role": "user", "content": "hi"}], client=_client(h))
    assert seen[0]["meterless-app"] == "app-deep" and seen[1]["meterless-app"] == "app-fast"
    assert seen[0]["meterless-scope"] == "user" and seen[0]["authorization"] == "Bearer ns-secret"
    assert d.content == "hello" and d.receipt_id == "rcpt_1" and d.routed_model == "nvidia/nemotron" and d.latency_ms == 321 and d.egress == "cloud-ok"
    assert f.lane == "fast"


def test_json_parse_fenced():
    r = chat("fast", [], json_schema={"type": "object", "required": ["a"]}, client=_client(lambda q: _resp('Sure:\n```json\n{"a": 1}\n```')))
    assert r.parsed == {"a": 1} and r.calls == 1


def test_json_repair_retry_once():
    replies = iter(["not json at all", '{"a": 2}'])
    bodies = []

    def h(req):
        bodies.append(json.loads(req.content))
        return _resp(next(replies), rid=f"r{len(bodies)}")

    r = chat("fast", [{"role": "user", "content": "x"}], json_schema={"type": "object", "required": ["a"]}, client=_client(h))
    assert r.parsed == {"a": 2} and r.calls == 2 and r.receipt_ids == ["r1", "r2"]
    assert "not valid" in bodies[1]["messages"][-1]["content"]


def test_json_fails_after_repair():
    with pytest.raises(NightshiftError):
        chat("fast", [], json_schema={"type": "object", "required": ["a"]}, client=_client(lambda q: _resp("nope")))


def test_pydantic_schema():
    class M(BaseModel):
        n: int

    assert chat("fast", [], json_schema=M, client=_client(lambda q: _resp('{"n": 3}'))).parsed.n == 3


def test_call_cap_enforced():
    with budget_scope(2) as b:
        c = _client(lambda q: _resp("ok"))
        chat("fast", [], client=c)
        chat("fast", [], client=c)
        with pytest.raises(CallCapExceeded):
            chat("fast", [], client=c)
        assert b.used == 2


def test_retries_502_and_counts_attempts():
    n = {"c": 0}

    def h(req):
        n["c"] += 1
        return httpx.Response(502, text="x") if n["c"] == 1 else _resp("ok")

    with budget_scope(10) as b:
        assert chat("deep", [], client=_client(h)).content == "ok"
        assert b.used == 2


def test_retries_499_request_aborted():
    n = {"c": 0}

    def h(req):
        n["c"] += 1
        return httpx.Response(499, text="request_aborted") if n["c"] == 1 else _resp("ok")

    with budget_scope(10) as b:
        assert chat("fast", [], client=_client(h)).content == "ok"
        assert b.used == 2


def test_4xx_not_retried():
    n = {"c": 0}

    def h(req):
        n["c"] += 1
        return httpx.Response(401, text="no")

    with pytest.raises(NightshiftError):
        chat("deep", [], client=_client(h))
    assert n["c"] == 1


def test_extract_json_embedded():
    assert extract_json('blah {"a": "x}y", "b": [1,2]} trailing') == {"a": "x}y", "b": [1, 2]}
    assert extract_json("[1,2]") == [1, 2]


def test_499_retried_only_once():
    n = {"c": 0}

    def h(req):
        n["c"] += 1
        return httpx.Response(499, text="request_aborted")

    with budget_scope(10) as b:
        with pytest.raises(NightshiftError):
            chat("fast", [], client=_client(h))
        assert b.used == 2
