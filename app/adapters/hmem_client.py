"""Typed client for the H-MEM HTTP service (CONTRACTS section 6)."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from .config import get_settings

log = logging.getLogger("pi.hmem")
AGENT_ID = "procurement-integrity"


class HMemClient:
    def __init__(self, url: str | None = None, timeout: float | None = None, client: httpx.Client | None = None):
        s = get_settings()
        self.url = (url or s.hmem_url).rstrip("/")
        self.http = client or httpx.Client(timeout=timeout or s.source_timeout)
        self.run_id = "run_unscoped"

    def _post(self, path: str, body: dict) -> dict:
        r = self.http.post(f"{self.url}{path}", json=body)
        r.raise_for_status()
        return r.json()

    def healthz(self) -> dict:
        r = self.http.get(f"{self.url}/healthz")
        r.raise_for_status()
        return r.json()

    def add(self, content: str, *, type: str = "factual", layer: str = "short_term", tags: list[str] | None = None,
            source: str = AGENT_ID, confidence: float = 0.7, entities: list[str] | None = None, meta: dict | None = None,
            run_id: str | None = None) -> str:
        return self._post("/add", {"content": content, "type": type, "layer": layer, "tags": tags or [], "source": source,
                                   "confidence": confidence, "agentId": AGENT_ID, "runId": run_id or self.run_id,
                                   "entities": entities or [], "meta": meta or {}})["id"]

    def query(self, query: str, *, top_n: int = 5, filters: dict | None = None, run_id: str | None = None) -> dict:
        return self._post("/query", {"query": query, "topN": top_n, "filters": filters or {}, "agentId": AGENT_ID,
                                     "runId": run_id or self.run_id})

    def recall(self, *, agency: str, uen: str | None, flag_id: str | None, query: str) -> list[dict[str, Any]]:
        """Memories relevant to this agency (and uen/flag when given). Service enforces agency scoping."""
        filters = {k: v for k, v in {"agency": agency, "uen": uen, "flag_id": flag_id}.items() if v}
        try:
            return self.query(query, filters=filters)["memories"]
        except httpx.HTTPError as e:
            log.warning("hmem recall failed: %s", type(e).__name__)
            return []

    def feedback(self, memory_id: str, signal: str, run_id: str) -> None:
        self._post("/feedback", {"memoryId": memory_id, "signal": signal, "agentId": AGENT_ID, "runId": run_id})

    def auditor_decision(self, *, run_id: str, finding_id: str, uen: str, flag_id: str, agency: str, decision: str,
                         reason: str, pattern_tag: str | None = None, scope: str = "agency") -> str:
        body = {"runId": run_id, "finding_id": finding_id, "uen": uen, "flag_id": flag_id, "agency": agency,
                "decision": decision, "reason": reason, "scope": scope}
        if pattern_tag:
            body["pattern_tag"] = pattern_tag
        return self._post("/auditor-decision", body)["memoryId"]

    def ledger(self, run_id: str | None = None) -> str:
        r = self.http.get(f"{self.url}/ledger", params={"runId": run_id} if run_id else None)
        r.raise_for_status()
        return r.text
