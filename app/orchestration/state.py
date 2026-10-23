"""Graph state and injected dependencies."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, TypedDict

from ..adapters import nightshift, zetaris
from ..adapters.config import get_settings
from ..schemas import Critique, Finding, Match, Memo, Plan, RunRequest
from ..tracing import Tracer

MATCH_THRESHOLD = 0.92  # Resolver matches below this are rejected by the Critic


class HMemLike(Protocol):  # implemented by app/adapters/hmem_client.py (D2)
    def recall(self, *, agency: str, uen: str | None, flag_id: str | None, query: str) -> list[dict]: ...
    def feedback(self, memory_id: str, signal: str, run_id: str) -> None: ...


def _default_sql(sql: str) -> zetaris.Result:
    # federated joins (Postgres + S3) can take 15 s+, so checks get a longer timeout than the 20 s default
    return zetaris.run_sql(sql, timeout=max(60.0, get_settings().source_timeout))


@dataclass
class Deps:
    tracer: Tracer
    sql: Callable[[str], zetaris.Result] = _default_sql
    llm: Callable[..., nightshift.ChatResult] = nightshift.chat
    resolve: Callable[..., list[Match]] | None = None
    hmem: HMemLike | None = None
    max_retries: int = field(default_factory=lambda: min(2, get_settings().max_retries))
    max_replans: int = 1
    match_threshold: float = MATCH_THRESHOLD
    write_files: bool = True


class RunState(TypedDict, total=False):
    run_id: str
    request: RunRequest
    rejected_reason: str | None
    plan: Plan
    matches: dict[str, Match]            # supplier_name -> Match
    resolver_strategy: str               # "default" | "fuzzy" | "llm_tiebreak"
    resolver_retry: int
    resolver_names: list[str]            # names the Critic wants re-resolved
    findings: list[Finding]
    critiques: list[Critique]
    retries: dict[str, int]              # flag_id -> analyst retries used
    revise_checks: list[str]             # flags to re-run
    coverage_gaps: list[str]             # planned checks that could not run
    check_errors: dict[str, str]
    replan_requested: bool
    replan_notes: str
    plan_reviewed: int                   # replan_count of the plan the Critic last reviewed
    replan_required: list[str]           # checks the plan review wants added on the replan
    plan_limitations: list[str]          # data-coverage limits found by the plan review (for the memo)
    wording_violations: list[str]        # finding_ids to rewrite
    scores: dict[str, float]
    memory_refs: list[str]
    memo: Memo | None
    route: str
    extras: dict[str, Any]
