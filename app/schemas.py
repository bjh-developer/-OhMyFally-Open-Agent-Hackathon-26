"""Pydantic models shared by agents, API and tracing (CONTRACTS section 7.4 and 8)."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

FindingStatus = Literal["accepted", "escalated", "rejected", "suppressed"]
TraceStatus = Literal["success", "needs_revision", "retrying", "escalated", "partial_success", "failed"]
Method = Literal["exact", "former_name", "fuzzy", "llm_tiebreak", "unresolved", "out_of_scope"]


class Match(BaseModel):
    supplier_name: str
    uen: str | None = None
    confidence: float = 0.0
    method: str = "unresolved"
    candidates: list[dict] = Field(default_factory=list)


class Evidence(BaseModel):
    query_id: str
    sql: str
    row_count: int
    rows: list[dict[str, Any]] = Field(default_factory=list, max_length=20)
    source_objects: list[str] = Field(default_factory=list)


class Finding(BaseModel):
    finding_id: str
    flag_id: str
    tender_no: str
    agency: str
    supplier_name: str
    uen: str | None = None
    summary: str = ""
    confidence: float = 0.0
    status: FindingStatus = "accepted"
    evidence: list[Evidence] = Field(default_factory=list)
    ago_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    wording_checked: bool = False
    # extras beyond the contract (additive): numbers the check computed and why a status was set
    awarded_amt: float | None = None
    award_date: date | None = None
    metric_name: str | None = None
    metric_value: str | None = None
    threshold: str | None = None
    detail: str | None = None
    notes: list[str] = Field(default_factory=list)


class RunRequest(BaseModel):
    """What the auditor asks. ``flags`` empty means let the Planner decide."""
    agency: str
    date_from: date
    date_to: date
    flags: list[str] = Field(default_factory=list)
    question: str | None = None


class Plan(BaseModel):
    checks: list[str]
    params: dict[str, str] = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)
    rationale: str = ""
    replan_count: int = 0


class Critique(BaseModel):
    finding_id: str
    verdict: Literal["ok", "revise", "reject", "suppress"]
    reason: str = ""
    target: str | None = None  # agent to send back to


class FindingGroup(BaseModel):
    """Findings that describe one underlying pattern (e.g. R3: several awards at one shared address)."""
    group_id: str
    flag_id: str
    title: str
    detail: str = ""
    finding_ids: list[str]
    suppliers: list[str] = Field(default_factory=list)
    n_awards: int = 0
    total_amt: float = 0.0
    status: FindingStatus = "accepted"
    priority: float = 0.0


class Memo(BaseModel):
    run_id: str
    agency: str
    date_from: date
    date_to: date
    summary: str
    findings: list[Finding]
    groups: list[FindingGroup] = Field(default_factory=list)  # additive: R3 awards grouped by shared address
    limitations: list[str] = Field(default_factory=list)
    disclaimer: str = ""
    escalated: list[str] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)
    markdown: str = ""


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class TraceEvent(BaseModel):
    timestamp: str = Field(default_factory=utcnow_iso)
    trace_id: str
    agent_name: str
    action: str
    input_summary: str = ""
    output_summary: str = ""
    target_agent: str | None = None
    confidence: float | None = None
    retry_count: int = 0
    status: TraceStatus = "success"
    zetaris_query_ids: list[str] = Field(default_factory=list)
    meterless_receipt_id: str | None = None
    # additive detail for the UI; harmless to consumers of the contract
    meterless_receipt_ids: list[str] = Field(default_factory=list)
    routed_model: str | None = None
    latency_ms: int | None = None
    egress: Any = None
    replayed: bool | None = None  # true: served from a recorded run, not a live service (app/replay.py)
