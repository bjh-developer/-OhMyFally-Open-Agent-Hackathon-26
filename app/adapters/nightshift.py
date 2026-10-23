"""Meterless Nightshift adapter (OpenAI-compatible), deep and fast lanes.

Nightshift binds one mode per app, so the lane is chosen by the ``meterless-app``
header (METERLESS_APP_DEEP / METERLESS_APP_FAST). Every response carries a
``meterless`` receipt; we keep receipt_id, routed_model, latency_ms and egress.
All calls count against the global LLM_CALL_CAP.
"""
from __future__ import annotations

import contextvars
import json
import logging
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ValidationError

from .config import get_settings
from ..replay import prompt_chars

log = logging.getLogger("pi.nightshift")

Lane = Literal["deep", "fast"]
TIMEOUT_S = 90.0


class NightshiftError(RuntimeError):
    pass


class NightshiftUnavailable(NightshiftError):
    """Outage-type failure (connection, timeout, 429/499/5xx) after retries; the only kind replay mode answers."""


class CallCapExceeded(NightshiftError):
    pass


class NightshiftClientError(NightshiftError):
    """4xx other than 429: not retried."""


class CallBudget:
    """Thread-safe LLM call counter. One per run (see ``budget_scope``)."""

    def __init__(self, cap: int | None = None):
        self.cap = get_settings().llm_call_cap if cap is None else cap
        self.used = 0
        self._lock = threading.Lock()

    def take(self) -> None:
        with self._lock:
            if self.used >= self.cap:
                raise CallCapExceeded(f"LLM_CALL_CAP={self.cap} reached")
            self.used += 1

    @property
    def remaining(self) -> int:
        return max(0, self.cap - self.used)


_budget: contextvars.ContextVar[CallBudget | None] = contextvars.ContextVar("llm_budget", default=None)
_global_budget = CallBudget()


def current_budget() -> CallBudget:
    return _budget.get() or _global_budget


class budget_scope:
    """``with budget_scope(40) as b:`` gives a run its own counter."""

    def __init__(self, cap: int | None = None):
        self.b = CallBudget(cap)

    def __enter__(self) -> CallBudget:
        self._tok = _budget.set(self.b)
        return self.b

    def __exit__(self, *a: Any) -> None:
        _budget.reset(self._tok)


@dataclass
class ChatResult:
    content: str
    parsed: Any = None
    receipt_id: str | None = None
    routed_model: str | None = None
    latency_ms: int | None = None
    egress: Any = None
    usage: dict = field(default_factory=dict)
    receipt_ids: list[str] = field(default_factory=list)  # includes repair retries
    calls: int = 1
    lane: str = ""
    prompt_chars: int = 0     # characters of message content sent, summed over attempts
    replayed: bool = False    # True when served from a recorded run (app/replay.py)


def _receipt(body: dict) -> dict:
    m = body.get("meterless") or {}
    usage = m.get("usage") or {}
    privacy = m.get("privacy") or {}
    return {
        "receipt_id": m.get("receipt_id"),
        "routed_model": m.get("routed_model") or body.get("model"),
        "latency_ms": usage.get("latency_ms"),
        "egress": m.get("egress", privacy.get("path")),
    }


_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S | re.I)


def extract_json(text: str) -> Any:
    """Parse JSON from a model reply: plain, fenced, or the first balanced {...}/[...]."""
    text = (text or "").strip()
    if not text:
        raise ValueError("empty reply")
    cands = [text] + [m.strip() for m in _FENCE.findall(text)]
    for c in cands:
        try:
            return json.loads(c)
        except json.JSONDecodeError:
            pass
    for open_, close in (("{", "}"), ("[", "]")):
        start = text.find(open_)
        while start != -1:
            depth, in_str, esc = 0, False, False
            for i in range(start, len(text)):
                ch = text[i]
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == '"':
                        in_str = False
                elif ch == '"':
                    in_str = True
                elif ch == open_:
                    depth += 1
                elif ch == close:
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start : i + 1])
                        except json.JSONDecodeError:
                            break
            start = text.find(open_, start + 1)
    raise ValueError("no JSON found in reply")


def _validate(parsed: Any, schema: dict | type[BaseModel] | None) -> Any:
    if schema is None:
        return parsed
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        return schema.model_validate(parsed)
    if isinstance(schema, dict):
        if schema.get("type") == "object" and not isinstance(parsed, dict):
            raise ValueError("expected a JSON object")
        missing = [k for k in schema.get("required", []) if not isinstance(parsed, dict) or k not in parsed]
        if missing:
            raise ValueError(f"missing required keys: {missing}")
    return parsed


def _schema_dict(schema: dict | type[BaseModel]) -> dict:
    return schema.model_json_schema() if isinstance(schema, type) else schema


def _post(client: httpx.Client, lane: Lane, payload: dict, retries: int) -> dict:
    s = get_settings()
    headers = {
        "Authorization": f"Bearer {s.meterless_token}",
        "meterless-app": s.app_deep if lane == "deep" else s.app_fast,
        "meterless-scope": "user",
    }
    last: Exception | None = None
    for attempt in range(retries + 1):
        current_budget().take()
        try:
            r = client.post(f"{s.meterless_url}/chat/completions", json=payload, headers=headers, timeout=TIMEOUT_S)
            # 499 = Nightshift/provider aborted the request mid-flight (seen on the fast lane); transient, so retry.
            if r.status_code in (408, 425, 429, 499, 500, 502, 503, 504):
                raise NightshiftUnavailable(f"HTTP {r.status_code}: {r.text[:200]}")
            if r.status_code >= 400:
                raise NightshiftClientError(f"HTTP {r.status_code}: {r.text[:300]}")
            return r.json()
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last = NightshiftUnavailable(f"{type(e).__name__}: {e}")
        except NightshiftClientError:
            raise
        except NightshiftError as e:
            last = e
            if str(e).startswith("HTTP 499") and attempt >= 1:
                break  # an identical request aborts the same way; stop wasting calls after one retry
        log.warning("nightshift retry lane=%s attempt=%s err=%s", lane, attempt + 1, last)
        time.sleep(min(3.0, 1.0 * (attempt + 1)))
    raise last  # type: ignore[misc]


def _chat_live(
    lane: Lane,
    messages: list[dict],
    json_schema: dict | type[BaseModel] | None = None,
    max_tokens: int = 2000,
    temperature: float = 0.2,
    *,
    client: httpx.Client | None = None,
    retries: int = 2,
) -> ChatResult:
    """One chat completion. With ``json_schema`` the reply is parsed and validated,
    with a single repair retry if it is not valid. Raises CallCapExceeded at the cap."""
    s = get_settings()
    msgs = list(messages)
    if json_schema is not None:
        sch = json.dumps(_schema_dict(json_schema))
        msgs.append({"role": "system", "content": f"Reply with ONLY one JSON value matching this JSON Schema, no prose, no code fences: {sch}"})
    payload: dict[str, Any] = {
        "model": s.model_deep if lane == "deep" else s.model_fast,
        "messages": msgs, "max_tokens": max_tokens, "temperature": temperature,
    }
    own = client is None
    client = client or httpx.Client(timeout=TIMEOUT_S)
    ids: list[str] = []
    calls = 0
    sent_chars = prompt_chars(msgs)
    try:
        body = _post(client, lane, payload, retries); calls += 1
        rc = _receipt(body)
        if rc["receipt_id"]:
            ids.append(rc["receipt_id"])
        content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        usage = body.get("usage") or {}
        parsed = None
        if json_schema is not None:
            try:
                parsed = _validate(extract_json(content), json_schema)
            except (ValueError, ValidationError) as err:
                log.warning("nightshift json invalid lane=%s: %s; repair retry", lane, str(err)[:200])
                prior = [{"role": "assistant", "content": content[:4000]}] if content.strip() else []  # empty assistant turns are rejected (400)
                payload["messages"] = msgs + prior + [
                    {"role": "user", "content": f"Your previous reply was not valid ({str(err)[:300]}). Return ONLY the corrected JSON."},
                ]
                sent_chars += prompt_chars(payload["messages"])
                payload["max_tokens"] = int(payload["max_tokens"] * 1.5)  # empty replies usually mean reasoning used the budget
                body = _post(client, lane, payload, retries); calls += 1
                rc = _receipt(body)
                if rc["receipt_id"]:
                    ids.append(rc["receipt_id"])
                content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
                usage = body.get("usage") or usage
                try:
                    parsed = _validate(extract_json(content), json_schema)
                except (ValueError, ValidationError) as err2:
                    raise NightshiftError(f"JSON invalid after repair retry: {str(err2)[:200]}") from err2
        log.info("nightshift ok lane=%s receipt=%s model=%s calls=%s", lane, rc["receipt_id"], rc["routed_model"], calls)
        return ChatResult(content=content, parsed=parsed, receipt_id=rc["receipt_id"], routed_model=rc["routed_model"],
                          latency_ms=rc["latency_ms"], egress=rc["egress"], usage=usage, receipt_ids=ids, calls=calls, lane=lane, prompt_chars=sent_chars)
    finally:
        if own:
            client.close()


def chat(
    lane: Lane,
    messages: list[dict],
    json_schema: dict | type[BaseModel] | None = None,
    max_tokens: int = 2000,
    temperature: float = 0.2,
    *,
    client: httpx.Client | None = None,
    retries: int = 2,
) -> ChatResult:
    """Live chat completion (see ``_chat_live``). If Nightshift is unreachable and replay mode is on
    (SAMPLE_MODE=true and a recorded set exists), serve the recorded reply, labelled ``replayed``.
    Cap, client (4xx) and bad-JSON errors are never replayed."""
    from .. import replay

    if replay.offline():  # SAMPLE_MODE without credentials: recordings only, no network
        rec = replay.serve_chat(lane, messages, json_schema) if replay.enabled() else None
        if rec is None:
            raise NightshiftUnavailable("offline sample mode: no recorded model reply for this call")
        return rec
    if replay.enabled() and replay.breaker_open("nightshift"):
        rec = replay.serve_chat(lane, messages, json_schema)
        if rec is not None:
            return rec
    try:
        res = _chat_live(lane, messages, json_schema, max_tokens, temperature, client=client, retries=retries)
    except NightshiftUnavailable as e:
        if replay.enabled():
            replay.trip("nightshift")
            rec = replay.serve_chat(lane, messages, json_schema)
            if rec is not None:
                log.warning("nightshift unreachable (%s); served recorded reply %s", str(e)[:80], rec.receipt_id)
                return rec
        raise
    replay.record_chat(lane, messages, res)
    return res
