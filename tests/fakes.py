"""Test doubles backed by recorded fixtures: FakeSQL (Zetaris) and FakeLLM (Nightshift)."""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Callable

from app.adapters.nightshift import ChatResult, current_budget
from app.adapters.zetaris import Result

FIX = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIX / f"{name}.json").read_text())


class FakeSQL:
    def __init__(self, overrides: dict[str, Callable[[int], dict]] | None = None):
        self.fx = load("zetaris")
        self.calls: list[tuple[str, str]] = []
        self.overrides = overrides or {}
        self.counts: dict[str, int] = {}

    def _key(self, sql: str) -> str:
        if "FIXTURE_R1" in sql:
            return "R1"
        if "FIXTURE_R3" in sql:
            return "R3"
        if sql.startswith("SHOW DATASOURCES"):
            return "show_datasources"
        if "supplier_xwalk" in sql:
            return "xwalk"
        if "DISTINCT supplier_name" in sql:
            return "names"
        raise AssertionError(f"unexpected SQL: {sql[:80]}")

    def __call__(self, sql: str) -> Result:
        key = self._key(sql)
        self.counts[key] = self.counts.get(key, 0) + 1
        body = self.overrides[key](self.counts[key]) if key in self.overrides else self.fx[key]
        qid = str(uuid.uuid4())
        self.calls.append((key, qid))
        return Result(headers=body["headers"], rows=[list(r) for r in body["data"]], query_id=qid, ms=3, sql=sql)


class FakeLLM:
    """Scripted replies keyed by the system prompt. ``fail`` makes a lane raise."""

    def __init__(self, unsupported: set[str] | None = None, fail: set[str] | None = None, narrative: dict | None = None):
        self.calls: list[tuple[str, str]] = []
        self.unsupported = unsupported or set()
        self.fail = fail or set()
        self.narrative = narrative

    def __call__(self, lane, messages, json_schema=None, max_tokens=2000, **kw) -> ChatResult:
        current_budget().take()
        sys = messages[0]["content"]
        user = json.loads(messages[-1]["content"])
        who = ("planner" if "Planner" in sys else "critic" if "verifier" in sys else "risk" if "triage" in sys else "reporter" if "audit memo" in sys else "other")
        self.calls.append((lane, who))
        if who in self.fail:
            raise RuntimeError(f"{who} down")
        if who == "planner":
            data = {"checks": user["instruction"] and list(user["implemented_checks"]), "rationale": "run everything implemented"}
        elif who == "critic":
            data = {"checks": [{"finding_id": f["finding_id"], "supported": f["finding_id"] not in self.unsupported, "reason": "ok"} for f in user["findings"]]}
        elif who == "risk":
            data = {"scores": [{"finding_id": f["finding_id"], "priority": 80, "reason": "large award, strong metric"} for f in user["findings"]]}
        else:
            data = self.narrative or {"headline": "1 award flagged as an anomaly for review", "overview": "The award may indicate a concern and requires auditor judgement."}
        return ChatResult(content=json.dumps(data), parsed=json_schema.model_validate(data) if hasattr(json_schema, "model_validate") else data,
                          receipt_id=f"rcpt_{who}_{len(self.calls)}", receipt_ids=[f"rcpt_{who}_{len(self.calls)}"],
                          routed_model="nvidia/fake", latency_ms=5, egress={"destination": "nvidia"}, lane=lane)
