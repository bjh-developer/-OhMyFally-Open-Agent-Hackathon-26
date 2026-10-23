"""Replay mode: serve recorded Zetaris and Nightshift responses when a live service is unreachable.

Active only when ``SAMPLE_MODE=true`` and a recorded set exists (``data/replay/<set>/``). Two modes:

* fallback (keys configured): the live call is tried first and replay answers only an outage-type failure
  (connection, timeout, 5xx; never a 4xx or a bad-JSON reply);
* offline (``Settings.offline``: SAMPLE_MODE with no Zetaris key and no Nightshift token): the network is never
  touched, every call is answered from the recorded set.

One set is recorded per request (``manifest.json`` ``request``); ``use_for(request)`` picks the set for the run
(a contextvar), falling back to REPLAY_SET. The agents run unchanged on the recorded Zetaris rows; a model call with
no recorded reply raises like an outage, so the agents' own rule-based fallbacks run. Every replayed response is labelled: ids start with ``replay:``, ``Result.replayed`` / ``ChatResult.replayed`` are set, trace
response is labelled: ids start with ``replay:``, ``Result.replayed`` / ``ChatResult.replayed`` are set, trace
events carry ``replayed: true`` and the memo gets a limitation line. A miss re-raises the original error.

Fixture layout (written by scripts/record_replay.py):
    manifest.json   what was recorded, when, for which request
    zetaris.json    {sha256(normalised SQL)[:16]: {sql, headers, rows, total, ms}}
    nightshift.json {"entries": [{lane, sys_key, exact_key, agent, prompt_chars, content, receipt_id, ...}]}
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import contextvars
import threading
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from .adapters.config import get_settings

log = logging.getLogger("pi.replay")

MEMO_LINE = "Replayed from a recorded run: services were offline"
BREAKER_S = 30.0

_lock = threading.Lock()
_served: list[dict] = []
_missed: list[dict] = []
_set_dir: contextvars.ContextVar[Path | None] = contextvars.ContextVar("replay_set_dir", default=None)
_down_until: dict[str, float] = {}


# ---- keys ------------------------------------------------------------------

def norm_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip().rstrip(";")).strip()


def sql_key(sql: str) -> str:
    return hashlib.sha256(norm_sql(sql).encode()).hexdigest()[:16]


def _h(o: Any) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()[:16]


def prompt_chars(messages: list[dict]) -> int:
    return sum(len(str(m.get("content") or "")) for m in messages)


def chat_keys(lane: str, messages: list[dict]) -> tuple[str, str]:
    """(sys_key, exact_key): lane + first message (the agent's prompt template), and lane + every message."""
    first = str((messages[0] if messages else {}).get("content") or "")
    return _h([lane, first]), _h([lane, [m.get("content") for m in messages]])


def agent_hint(messages: list[dict]) -> str:
    first = str((messages[0] if messages else {}).get("content") or "")
    return re.sub(r"\s+", " ", first)[:90]


# ---- enable / breaker --------------------------------------------------------

def current_dir() -> Path:
    return _set_dir.get() or get_settings().replay_dir


def enabled() -> bool:
    s = get_settings()
    return bool(s.sample_mode and (current_dir() / "manifest.json").is_file())


def offline() -> bool:
    """True when SAMPLE_MODE has no credentials to try: answer only from recordings, never open a socket."""
    return bool(get_settings().offline)


def available_sets() -> list[dict]:
    """Manifests of every recorded set under data/replay/ (name, request)."""
    out = []
    for m in sorted(get_settings().replay_dir.parent.glob("*/manifest.json")):
        try:
            man = json.loads(m.read_text(encoding="utf-8"))
        except ValueError:
            continue
        out.append({"name": m.parent.name, "dir": m.parent, "request": man.get("request") or {}})
    return out


def use_for(request: Any) -> bool:
    """Choose the recorded set that matches the request's agency and period for this run. Returns False when none
    does (the default REPLAY_SET then applies, or the run is refused in offline mode)."""
    for s in available_sets():
        r = s["request"]
        if (str(r.get("agency", "")).strip().lower() == request.agency.strip().lower()
                and r.get("date_from") == str(request.date_from) and r.get("date_to") == str(request.date_to)):
            _set_dir.set(s["dir"])
            with _lock:
                st = _load(str(s["dir"]))
                st.used.clear()
                st.cursor.clear()
            return True
    _set_dir.set(None)
    return False


def trip(kind: str) -> None:
    with _lock:
        _down_until[kind] = time.monotonic() + BREAKER_S


def breaker_open(kind: str) -> bool:
    with _lock:
        return time.monotonic() < _down_until.get(kind, 0.0)


def reset() -> None:
    """Forget the outage breaker, the served log and cached fixtures (tests)."""
    _set_dir.set(None)
    with _lock:
        _down_until.clear()
        _served.clear()
        _missed.clear()
    _load.cache_clear()


# ---- fixtures ----------------------------------------------------------------

@dataclass
class Store:
    dir: Path
    manifest: dict
    sql: dict[str, dict]
    entries: list[dict]
    used: set[int] = field(default_factory=set)
    cursor: dict[str, int] = field(default_factory=dict)


@lru_cache(maxsize=4)
def _load(path: str) -> Store:
    d = Path(path)
    manifest = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    sql = json.loads((d / "zetaris.json").read_text(encoding="utf-8")) if (d / "zetaris.json").is_file() else {}
    ns = json.loads((d / "nightshift.json").read_text(encoding="utf-8")) if (d / "nightshift.json").is_file() else {}
    return Store(d, manifest, sql, ns.get("entries", []))


def store() -> Store:
    return _load(str(current_dir()))


def _note(kind: str, key: str, how: str) -> dict:
    s = store()
    rec = {"kind": kind, "key": key, "how": how, "set": s.dir.name, "at": time.time()}
    with _lock:
        _served.append(rec)
    return rec


def _miss(kind: str, what: str) -> None:
    _missed.append({"kind": kind, "what": what, "at": time.time()})  # callers may hold _lock; list.append is atomic


def mark() -> int:
    with _lock:
        return len(_served)


def mark_missed() -> int:
    with _lock:
        return len(_missed)


def missed_since(m: int) -> list[dict]:
    with _lock:
        return list(_missed[m:])


def served_since(m: int) -> list[dict]:
    with _lock:
        return list(_served[m:])


# ---- serving -----------------------------------------------------------------

def serve_sql(sql: str):
    """Recorded Result for this statement (None on a miss)."""
    from .adapters.zetaris import Result

    s = store()
    key = sql_key(sql)
    e = s.sql.get(key)
    if e is None:
        log.warning("replay miss zetaris key=%s sql=%s", key, norm_sql(sql)[:100])
        _miss("zetaris", key)
        return None
    _note("zetaris", key, "exact")
    return Result(headers=list(e["headers"]), rows=[list(r) for r in e["rows"]], query_id=f"replay:{key}", ms=0,
                  sql=norm_sql(sql), total=e.get("total"), meta={"replayed_from": s.dir.name, "recorded_ms": e.get("ms")},
                  replayed=True)


def serve_chat(lane: str, messages: list[dict], json_schema: Any = None):
    """Recorded ChatResult for this call (None on a miss). Exact prompt match first, then the same prompt
    template in recorded order."""
    from .adapters.nightshift import ChatResult, NightshiftError, _validate, extract_json

    s = store()
    sys_key, exact_key = chat_keys(lane, messages)
    with _lock:
        pick, how = None, ""
        for i, e in enumerate(s.entries):
            if e["exact_key"] == exact_key and i not in s.used:
                pick, how = i, "exact"
                break
        if pick is None:
            same = [i for i, e in enumerate(s.entries) if e["sys_key"] == sys_key]
            if same:
                n = s.cursor.get(sys_key, 0)
                s.cursor[sys_key] = n + 1
                pick, how = same[n % len(same)], "template"
        if pick is None:
            log.warning("replay miss nightshift lane=%s agent=%s", lane, agent_hint(messages)[:60])
            _miss("nightshift", agent_hint(messages)[:60])
            return None
        s.used.add(pick)
        e = s.entries[pick]
    content = e["content"]
    parsed = None
    if json_schema is not None:
        try:
            parsed = _validate(extract_json(content), json_schema)
        except Exception as err:  # recorded reply does not fit this caller's schema: do not fake it
            raise NightshiftError(f"replayed reply does not match the requested schema: {str(err)[:150]}") from err
    _note("nightshift", e["exact_key"], how)
    rid = f"replay:{e.get('receipt_id') or e['exact_key']}"
    return ChatResult(content=content, parsed=parsed, receipt_id=rid, routed_model=f"{e.get('routed_model')} (replayed)",
                      latency_ms=0, egress={"destination": "replay (recorded run, no network)", "coverage": how, "sent": {}},
                      usage=e.get("usage") or {}, receipt_ids=[rid], calls=0, lane=lane, prompt_chars=0, replayed=True)


# ---- memo label ---------------------------------------------------------------

def limitation_line(served: list[dict]) -> str:
    z = sum(1 for x in served if x["kind"] == "zetaris")
    n = sum(1 for x in served if x["kind"] == "nightshift")
    name = served[0]["set"] if served else store().dir.name
    return f"{MEMO_LINE}. {z} Zetaris result(s) and {n} Nightshift reply(ies) came from the recorded set '{name}', not from live services."


def fallback_line(missed: list[dict]) -> str:
    n = sum(1 for x in missed if x["kind"] == "nightshift")
    return (f"{n} model call(s) had no recorded reply and no live model was reachable: those steps used the rule-based fallback "
            "(deterministic scores, template narrative, no model claim check).")


def annotate_memo(memo: Any, served: list[dict], missed: list[dict] | None = None) -> None:
    """Add the replay limitation (and the model-free fallback note) to the memo and its markdown, in place."""
    lines = []
    if served:
        lines.append(limitation_line(served))
        memo.stats["replayed"] = {"zetaris": sum(1 for x in served if x["kind"] == "zetaris"),
                                  "nightshift": sum(1 for x in served if x["kind"] == "nightshift"), "set": served[0]["set"]}
    if missed and any(x["kind"] == "nightshift" for x in missed):
        lines.append(fallback_line(missed))
        memo.stats["model_free_fallback"] = sum(1 for x in missed if x["kind"] == "nightshift")
    md = memo.markdown or ""
    for line in reversed(lines):
        if line in memo.limitations:
            continue
        memo.limitations.insert(0, line)
        if "## Limitations\n" in md:
            md = md.replace("## Limitations\n", f"## Limitations\n- {line}\n", 1)
        else:
            md = md.rstrip("\n") + f"\n\n## Limitations\n- {line}\n"
    memo.markdown = md


# ---- recording -----------------------------------------------------------------

class Recorder:
    """Collects live responses while active. ``with Recorder() as r: ...; r.save(dir, meta)``."""

    def __init__(self) -> None:
        self.sql: dict[str, dict] = {}
        self.entries: list[dict] = []
        self._lock = threading.Lock()

    def __enter__(self) -> "Recorder":
        global _recorder
        _recorder = self
        return self

    def __exit__(self, *a: Any) -> None:
        global _recorder
        _recorder = None

    def save(self, out: Path, meta: dict) -> dict:
        out.mkdir(parents=True, exist_ok=True)
        (out / "zetaris.json").write_text(json.dumps(self.sql, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        (out / "nightshift.json").write_text(json.dumps({"entries": self.entries}, ensure_ascii=False, indent=1), encoding="utf-8")
        man = {**meta, "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "zetaris_queries": len(self.sql),
               "nightshift_calls": len(self.entries)}
        (out / "manifest.json").write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding="utf-8")
        return man


_recorder: Recorder | None = None


def record_sql(res: Any) -> None:
    r = _recorder
    if r is None or getattr(res, "replayed", False):
        return
    with r._lock:
        r.sql[sql_key(res.sql)] = {"sql": norm_sql(res.sql), "headers": res.headers, "rows": res.rows, "total": res.total, "ms": res.ms}


def record_chat(lane: str, messages: list[dict], res: Any) -> None:
    r = _recorder
    if r is None or getattr(res, "replayed", False):
        return
    sys_key, exact_key = chat_keys(lane, messages)
    with r._lock:
        r.entries.append({
            "lane": lane, "agent": agent_hint(messages), "sys_key": sys_key, "exact_key": exact_key,
            "prompt_chars": res.prompt_chars, "content": res.content, "receipt_id": res.receipt_id,
            "routed_model": res.routed_model, "latency_ms": res.latency_ms, "usage": res.usage, "calls": res.calls,
        })
