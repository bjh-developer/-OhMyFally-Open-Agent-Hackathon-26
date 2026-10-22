from datetime import date

import httpx
import pytest

from app.adapters.zetaris import ZetarisError, run_sql, to_date, to_float, to_int


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_run_sql_ok_headers_and_ids():
    seen = {}

    def h(req: httpx.Request):
        import json
        body = json.loads(req.content)
        seen.update(h=dict(req.headers), b=body)
        return httpx.Response(200, json={"headers": ["a", "b"], "data": [["1", "2.5"]], "total": 1, "timeUsed": 12})

    r = run_sql("SELECT 1;", client=_client(h))
    assert r.headers == ["a", "b"] and r.rows == [["1", "2.5"]] and len(r) == 1
    assert seen["b"]["sql"] == "SELECT 1" and seen["b"]["queryId"] == r.query_id == seen["h"]["x-request-id"]
    assert seen["h"]["authorization"] == "Bearer zk-secret" and seen["h"]["x-org-id"] == "1"
    assert r.typed({"a": int, "b": float}) == [{"a": 1, "b": 2.5}]


def test_retries_5xx_then_succeeds_with_fresh_ids():
    ids = []

    def h(req):
        import json
        ids.append(json.loads(req.content)["queryId"])
        return httpx.Response(502, text="bad") if len(ids) < 3 else httpx.Response(200, json={"headers": ["x"], "data": [["1"]]})

    r = run_sql("SELECT 1", client=_client(h))
    assert r.attempts == 3 and len(set(ids)) == 3 and r.query_id == ids[-1]


def test_gives_up_after_two_retries():
    n = {"c": 0}

    def h(req):
        n["c"] += 1
        return httpx.Response(500, text="boom")

    with pytest.raises(ZetarisError):
        run_sql("SELECT 1", client=_client(h))
    assert n["c"] == 3


def test_4xx_not_retried():
    n = {"c": 0}

    def h(req):
        n["c"] += 1
        return httpx.Response(400, text="syntax")

    with pytest.raises(ZetarisError) as ei:
        run_sql("SELEC", client=_client(h))
    assert n["c"] == 1 and ei.value.status == 400 and ei.value.query_id


def test_timeout_retried():
    n = {"c": 0}

    def h(req):
        n["c"] += 1
        raise httpx.ReadTimeout("slow")

    with pytest.raises(ZetarisError):
        run_sql("SELECT 1", client=_client(h))
    assert n["c"] == 3


def test_casts():
    assert to_int("1,234") == 1234 and to_int(None) is None and to_int("") is None and to_int("12.0") == 12
    assert to_float("null") is None and to_float("89999.5") == 89999.5
    assert to_date("2025-06-20") == date(2025, 6, 20) == to_date("20/6/2025") and to_date("2025-06-20 00:00:00") == date(2025, 6, 20)
