from __future__ import annotations

import json
from typing import Any

from ..schemas import Finding


def compact_finding(f: Finding) -> dict[str, Any]:
    return {
        "finding_id": f.finding_id, "flag_id": f.flag_id, "tender_no": f.tender_no, "supplier": f.supplier_name,
        "agency": f.agency, "amount": f.awarded_amt, "award_date": str(f.award_date) if f.award_date else None,
        "metric": f"{f.metric_name}={f.metric_value} (threshold {f.threshold})", "summary": f.summary,
        "confidence": f.confidence, "status": f.status,
    }


def dumps(o: Any) -> str:
    return json.dumps(o, default=str, ensure_ascii=False)
