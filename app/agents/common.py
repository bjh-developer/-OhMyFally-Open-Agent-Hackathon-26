from __future__ import annotations

import contextvars
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, TypeVar

from ..schemas import Finding

T = TypeVar("T")
R = TypeVar("R")


def compact_finding(f: Finding) -> dict[str, Any]:
    return {
        "finding_id": f.finding_id, "flag_id": f.flag_id, "tender_no": f.tender_no, "supplier": f.supplier_name,
        "agency": f.agency, "amount": f.awarded_amt, "award_date": str(f.award_date) if f.award_date else None,
        "metric": f"{f.metric_name}={f.metric_value} (threshold {f.threshold})", "summary": f.summary,
        "confidence": f.confidence, "status": f.status,
    }


def dumps(o: Any) -> str:
    return json.dumps(o, default=str, ensure_ascii=False)


def parallel_map(fn: Callable[[T], R], items: list[T], max_workers: int = 3) -> list[R | BaseException]:
    """Run ``fn`` over ``items`` concurrently, results in input order; an exception is returned in place of its result.
    Each worker runs in a copy of the caller's context, so the per-run LLM call budget (a ContextVar) still applies."""
    if not items:
        return []

    def call(item: T) -> R | BaseException:
        try:
            return fn(item)
        except BaseException as e:  # noqa: BLE001 - surfaced to the caller per item
            return e

    with ThreadPoolExecutor(max_workers=min(max_workers, len(items))) as ex:
        futures = [ex.submit(contextvars.copy_context().run, call, it) for it in items]
        return [f.result() for f in futures]
