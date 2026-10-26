"""Zetaris REST adapter: one Lightning SQL statement per call.

REST returns every value as a string, so callers cast with ``Result.typed`` or the
``to_*`` helpers. Retries cover timeouts, connection errors and 5xx only.
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

import httpx

from .config import get_settings

log = logging.getLogger("pi.zetaris")

_NULLS = {"", "null", "none", "nan"}


class ZetarisError(RuntimeError):
    def __init__(self, msg: str, query_id: str | None = None, status: int | None = None):
        super().__init__(msg)
        self.query_id = query_id
        self.status = status


# ---- casting helpers -------------------------------------------------------

def _is_null(v: Any) -> bool:
    return v is None or (isinstance(v, str) and v.strip().lower() in _NULLS)


def to_int(v: Any) -> int | None:
    if _is_null(v):
        return None
    try:
        return int(Decimal(str(v).replace(",", "")))
    except InvalidOperation as e:
        raise ValueError(f"not an int: {v!r}") from e


def to_float(v: Any) -> float | None:
    return None if _is_null(v) else float(str(v).replace(",", ""))


def to_decimal(v: Any) -> Decimal | None:
    return None if _is_null(v) else Decimal(str(v).replace(",", ""))


def to_date(v: Any) -> date | None:
    if _is_null(v):
        return None
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            pass
    raise ValueError(f"not a date: {v!r}")


def to_datetime(v: Any) -> datetime | None:
    if _is_null(v):
        return None
    return datetime.fromisoformat(str(v).strip().replace("Z", "+00:00"))


def to_bool(v: Any) -> bool | None:
    return None if _is_null(v) else str(v).strip().lower() in {"true", "t", "1", "yes", "y"}


def to_str(v: Any) -> str | None:
    return None if v is None else str(v)


_CASTERS: dict[Any, Callable[[Any], Any]] = {
    int: to_int, float: to_float, Decimal: to_decimal, date: to_date,
    datetime: to_datetime, bool: to_bool, str: to_str,
}


def cast_value(v: Any, typ: Any) -> Any:
    return _CASTERS[typ](v) if typ in _CASTERS else typ(v)


# ---- result ----------------------------------------------------------------

@dataclass
class Result:
    headers: list[str]
    rows: list[list[Any]]
    query_id: str
    ms: int
    sql: str = ""
    total: int | None = None
    attempts: int = 1
    meta: dict = field(default_factory=dict)
    replayed: bool = False  # True when served from a recorded run (app/replay.py), not a live query

    def __len__(self) -> int:
        return len(self.rows)

    def dicts(self) -> list[dict[str, Any]]:
        return [dict(zip(self.headers, r)) for r in self.rows]

    def typed(self, types: dict[str, Any]) -> list[dict[str, Any]]:
        """Dict rows with the named columns cast, e.g. ``{"awarded_amt": float, "award_date": date}``."""
        out = self.dicts()
        for d in out:
            for col, typ in types.items():
                if col in d:
                    d[col] = cast_value(d[col], typ)
        return out

    def scalar(self, typ: Any = str) -> Any:
        return cast_value(self.rows[0][0], typ) if self.rows else None


# ---- client ----------------------------------------------------------------

def _run_sql_live(
    sql: str,
    *,
    limit: int = 1000,
    timeout: float | None = None,
    retries: int | None = None,
    client: httpx.Client | None = None,
) -> Result:
    """Run one statement. Fresh UUID per attempt as both X-Request-ID and queryId."""
    s = get_settings()
    sql = sql.strip().rstrip(";")
    if not sql:
        raise ZetarisError("empty SQL")
    timeout = s.source_timeout if timeout is None else timeout
    retries = min(2, s.max_retries if retries is None else retries)
    own = client is None
    client = client or httpx.Client(timeout=timeout)
    last: Exception | None = None
    try:
        for attempt in range(retries + 1):
            qid = str(uuid.uuid4())
            t0 = time.monotonic()
            try:
                r = client.post(
                    f"{s.zetaris_url}/sql-editor/sqls/run",
                    json={"queryId": qid, "sql": sql, "source": "SqlEditor", "limit": limit},
                    headers={
                        "Authorization": f"Bearer {s.zetaris_api_key}",
                        "X-Org-ID": s.zetaris_org_id,
                        "X-Request-ID": qid,
                    },
                    timeout=timeout,
                )
                if r.status_code >= 500:
                    raise ZetarisError(f"HTTP {r.status_code}: {r.text[:300]}", qid, r.status_code)
                if r.status_code >= 400:  # not retryable
                    raise ZetarisError(f"HTTP {r.status_code}: {r.text[:300]}", qid, r.status_code)
                body = r.json()
                ms = int((time.monotonic() - t0) * 1000)
                log.info("zetaris ok query_id=%s rows=%s ms=%s attempt=%s", qid, len(body.get("data") or []), ms, attempt + 1)
                return Result(
                    headers=list(body.get("headers") or []),
                    rows=[list(x) for x in (body.get("data") or [])],
                    query_id=qid, ms=ms, sql=sql, total=body.get("total"), attempts=attempt + 1,
                    meta={"timeUsed": body.get("timeUsed")},
                )
            except (httpx.TimeoutException, httpx.TransportError) as e:
                last = ZetarisError(f"{type(e).__name__}: {e}", qid)
            except ZetarisError as e:
                if e.status and e.status < 500:
                    log.warning("zetaris fail query_id=%s %s", qid, e)
                    raise
                last = e
            log.warning("zetaris retry query_id=%s attempt=%s err=%s", qid, attempt + 1, last)
            time.sleep(min(2.0, 0.5 * (attempt + 1)))
        raise last  # type: ignore[misc]
    finally:
        if own:
            client.close()


def run_sql(
    sql: str,
    *,
    limit: int = 1000,
    timeout: float | None = None,
    retries: int | None = None,
    client: httpx.Client | None = None,
) -> Result:
    """Live query. If Zetaris is unreachable (transport error, timeout, 5xx) and replay mode is on
    (SAMPLE_MODE=true and a recorded set exists), serve the recorded result, labelled ``replayed``."""
    from .. import replay

    if replay.offline():  # SAMPLE_MODE without credentials: recordings only, no network
        rec = replay.serve_sql(sql) if replay.enabled() else None
        if rec is None:
            raise ZetarisError("offline sample mode: no recorded Zetaris result for this query")
        return rec
    if replay.enabled() and replay.breaker_open("zetaris"):
        rec = replay.serve_sql(sql)
        if rec is not None:
            return rec
    try:
        res = _run_sql_live(sql, limit=limit, timeout=timeout, retries=retries, client=client)
    except ZetarisError as e:
        if (e.status is None or e.status >= 500) and replay.enabled():
            replay.trip("zetaris")
            rec = replay.serve_sql(sql)
            if rec is not None:
                log.warning("zetaris unreachable (%s); served recorded result %s", e, rec.query_id)
                return rec
        raise
    replay.record_sql(res)
    return res
