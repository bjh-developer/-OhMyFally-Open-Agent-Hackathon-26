"""JSONL tracer: one line per agent step in ``logs/<run_id>.jsonl`` (CONTRACTS section 8).

Also fans events out to in-process subscribers (the API's SSE stream).
"""
from __future__ import annotations

import json
import re
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Callable

from .adapters.config import get_settings
from .schemas import TraceEvent


def new_run_id() -> str:
    return f"run_{time.strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(3)}"


_RUN_ID = re.compile(r"^run_[A-Za-z0-9_\-]{1,64}$")
# Secret-shaped strings never reach the log, even if a caller passes one by mistake.
_SECRETS = re.compile(r"(Bearer\s+[A-Za-z0-9._\-]{8,}|\b(?:sk|nvapi|rk|pk)[-_][A-Za-z0-9_\-]{16,}|(?:api[_-]?key|token|password|secret)[\"']?\s*[:=]\s*[\"']?[^\s\"',}]{6,})", re.I)


def _short(v: Any, n: int = 300) -> str:
    s = v if isinstance(v, str) else json.dumps(v, default=str, ensure_ascii=False)
    s = _SECRETS.sub("[redacted]", s)
    return s if len(s) <= n else s[: n - 1] + "…"


def _egress(e: Any) -> Any:
    """Keep the Nightshift egress receipt small: destination, coverage and sizes only."""
    if not isinstance(e, dict):
        return e if e is None else _short(e, 80)
    sent = e.get("sent") if isinstance(e.get("sent"), dict) else {}
    return {"destination": e.get("destination"), "coverage": e.get("coverage"), "prompt_chars": sent.get("prompt_chars"),
            "redacted": len(sent.get("redacted") or []), "withheld": len(e.get("withheld") or [])}


class Tracer:
    def __init__(self, run_id: str | None = None, logs_dir: Path | None = None):
        self.run_id = run_id or new_run_id()
        if not _RUN_ID.match(self.run_id):
            raise ValueError("invalid run_id")
        self.dir = Path(logs_dir or get_settings().logs_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / f"{self.run_id}.jsonl"
        self.events: list[TraceEvent] = []
        self._subs: list[Callable[[TraceEvent], None]] = []
        self._lock = threading.Lock()

    def subscribe(self, fn: Callable[[TraceEvent], None]) -> None:
        self._subs.append(fn)

    def emit(
        self,
        agent: str,
        action: str,
        *,
        input: Any = "",
        output: Any = "",
        target: str | None = None,
        confidence: float | None = None,
        retry: int = 0,
        status: str = "success",
        query_ids: list[str] | None = None,
        receipt_ids: list[str] | None = None,
        routed_model: str | None = None,
        latency_ms: int | None = None,
        egress: Any = None,
        replayed: bool = False,
    ) -> TraceEvent:
        ids = [*(query_ids or []), *(receipt_ids or [])]
        replayed = replayed or any(str(i).startswith("replay:") for i in ids)
        ev = TraceEvent(
            trace_id=self.run_id, agent_name=agent, action=action,
            input_summary=_short(input), output_summary=_short(output) + (" [replayed from recorded run]" if replayed else ""), target_agent=target,
            confidence=confidence, retry_count=retry, status=status,  # type: ignore[arg-type]
            zetaris_query_ids=list(query_ids or []),
            meterless_receipt_id=(receipt_ids[-1] if receipt_ids else None),
            meterless_receipt_ids=list(receipt_ids or []),
            routed_model=routed_model, latency_ms=latency_ms, egress=_egress(egress), replayed=True if replayed else None,
        )
        with self._lock:
            self.events.append(ev)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(ev.model_dump_json(exclude_none=True) + "\n")
        for fn in self._subs:
            try:
                fn(ev)
            except Exception:  # a broken subscriber must never break a run
                pass
        return ev

    def llm(self, agent: str, action: str, res: Any, **kw: Any) -> TraceEvent:
        """Emit with the receipt fields of a nightshift ChatResult."""
        return self.emit(agent, action, receipt_ids=res.receipt_ids, routed_model=res.routed_model,
                         latency_ms=res.latency_ms, egress=res.egress, **kw)
