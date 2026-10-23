"""Per-run behaviour summary, computed on the read side from the trace lines of ``logs/<run_id>.jsonl``.

Pure: ``summarise(events)`` takes trace dicts (CONTRACTS section 8) and returns a JSON-able dict. Agents log
nothing extra for it. Fields added later (``memory_hits``) are optional, so old traces still summarise.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

# Pipeline order. An edge to the same or an earlier stage is a loop (a back-edge).
_ORDER = ["gate", "planner", "resolver", "analyst", "critic", "risk", "reporter"]
_CLAIMS = re.compile(r"(\d+)\s+issues?")
_SUPPRESSED = re.compile(r"(\d+)\s+suppressed")
_REPLAN = re.compile(r"replan\s*=\s*true", re.I)


def _stage(name: str | None) -> str:
    n = (name or "").lower()
    return next((s for s in _ORDER if s in n), n)


def _rank(name: str | None) -> int:
    s = _stage(name)
    return _ORDER.index(s) if s in _ORDER else -1


def _agent(e: dict) -> str:
    return str(e.get("agent_name") or e.get("agent") or "unknown")


def _ts(v: Any) -> float | None:
    if not isinstance(v, str):
        return None
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _num(v: Any) -> int | None:
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _receipts(e: dict) -> list[str]:
    ids = e.get("meterless_receipt_ids") or []
    if not ids:
        one = e.get("meterless_receipt_id") or e.get("nightshift_receipt")
        ids = [one] if one else []
    return [str(i) for i in ids]


def _queries(e: dict) -> list[str]:
    ids = e.get("zetaris_query_ids")
    if ids is None and e.get("zetaris_query"):
        ids = [e["zetaris_query"]]
    return [str(i) for i in ids or []]


def _tokens(e: dict) -> tuple[int | None, int | None]:
    u = e.get("usage") if isinstance(e.get("usage"), dict) else {}
    p = _num(e.get("prompt_tokens", u.get("prompt_tokens")))
    c = _num(e.get("completion_tokens", u.get("completion_tokens")))
    return p, c


def _reason(e: dict, claims: int) -> str:
    """Plain reason for a loop, taken from the line's output summary (the Critic writes its issues after the route)."""
    out = str(e.get("output_summary") or "")
    parts = [p.strip() for p in out.split(";")]
    tail = [p for p in parts if p and not re.match(r"(\d+\s+issues?|route=|revise=|re-resolve=)", p)]
    reason = "; ".join(tail)[:160]
    if not reason and _REPLAN.search(out):
        reason = "the risk review asked for a wider plan"
    return reason


def summarise(events: Iterable[dict]) -> dict:
    evs = [e for e in events if isinstance(e, dict)]
    receipts: set[str] = set()
    queries: set[str] = set()
    per: dict[str, dict] = {}
    loops: list[dict] = []
    prompt = completion = None
    hits = None
    cleared = 0
    cleared_seen = False
    critiques = escalations = replans = partial = retries = 0
    stamps: list[float] = []

    for e in evs:
        agent = _agent(e)
        status = e.get("status")
        out = str(e.get("output_summary") or "")
        rc = _receipts(e)
        receipts.update(rc)
        queries.update(_queries(e))
        t = _ts(e.get("timestamp"))
        if t is not None:
            stamps.append(t)
        retries = max(retries, _num(e.get("retry_count")) or 0)
        if status == "escalated":
            escalations += 1
        if status == "partial_success":
            partial += 1
        if _stage(agent) == "critic" and status == "needs_revision":
            critiques += 1
        p, c = _tokens(e)
        if p is not None:
            prompt = (prompt or 0) + p
        if c is not None:
            completion = (completion or 0) + c
        mh = _num(e.get("memory_hits"))
        if mh is not None:
            hits = (hits or 0) + mh
        if isinstance(e.get("cleared_by_memory"), int):
            cleared, cleared_seen = cleared + e["cleared_by_memory"], True
        elif _stage(agent) == "reporter" and (m := _SUPPRESSED.search(out)):
            cleared, cleared_seen = cleared + int(m.group(1)), True

        if _stage(agent) != "orchestrator" and agent != "Orchestrator":
            a = per.setdefault(agent, {"agent": agent, "calls": 0, "time_s": 0.0, "llm_calls": 0})
            a["calls"] += 1
            a["time_s"] += (_num(e.get("latency_ms")) or 0) / 1000
            a["llm_calls"] += len(rc)

        tgt = e.get("target_agent")
        replan = bool(_REPLAN.search(out)) and _stage(agent) == "risk"
        if tgt and _rank(agent) >= 0 and _rank(tgt) >= 0 and _rank(tgt) <= _rank(agent):
            m = _CLAIMS.search(out)
            claims = int(m.group(1)) if m else 0
            loops.append({"from_agent": agent, "to_agent": str(tgt), "reason": _reason(e, claims), "claims": claims})
            if _stage(tgt) == "planner":
                replans += 1
        elif replan:
            replans += 1
            loops.append({"from_agent": agent, "to_agent": "PlannerAgent", "reason": _reason(e, 0), "claims": 0})

    for a in per.values():
        a["time_s"] = round(a["time_s"], 2)
    return {
        "critiques": critiques,
        "retries": retries,
        "escalations": escalations,
        "replans": replans,
        "partial_success": partial,
        "llm_calls": len(receipts),
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "duration_s": round(max(stamps) - min(stamps), 2) if len(stamps) > 1 else 0.0,
        "per_agent": sorted(per.values(), key=lambda a: -a["time_s"]),
        "memory_hits": hits or 0,
        "memory_tracked": hits is not None,
        "cleared_by_memory": cleared if cleared_seen else 0,
        "zetaris_queries": len(queries),
        "loops": loops,
    }


def read_events(path: Path) -> list[dict]:
    """Trace lines from a JSONL file; a torn or non-JSON line is skipped."""
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if isinstance(d, dict):
            out.append(d)
    return out
