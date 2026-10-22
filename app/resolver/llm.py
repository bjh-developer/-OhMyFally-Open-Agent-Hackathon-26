"""Fast-lane Nightshift tie-break for ambiguous supplier matches (about 8 suppliers per call).

Goes through app.adapters.nightshift.chat, so the global LLM_CALL_CAP, retries and JSON repair apply.
"""
from __future__ import annotations

import json

from app.adapters.nightshift import chat

SYSTEM = (
    "You match Singapore government supplier names to ACRA registry entities. For each item choose the "
    "candidate that is the SAME legal entity as the supplier name, or null if none is clearly the same. "
    "Beware of similar but different companies (different trade words, branches, LLP vs company). "
    "Do not explain. Output the JSON object only, with no other text: "
    '{"results":[{"id":"<id>","uen":"<candidate uen or null>","confidence":0.0-1.0}]}'
)
SCHEMA = {"type": "object", "required": ["results"]}
RECEIPTS: list[dict] = []  # meterless receipts kept for tracing/handover


def nightshift_tiebreak(items: list[dict]) -> dict[str, dict]:
    payload = [{"id": it["id"], "supplier_name": it["name"],
                "candidates": [{"uen": c["uen"], "name": c["entity_name"], "status": c["status"],
                                "former_name_match": c.get("matched_on", "").endswith("former")}
                               for c in it["candidates"]]} for it in items]
    res = chat("fast",
               [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps(payload) + "\n\nJSON only."}],
               json_schema=SCHEMA, max_tokens=3000, temperature=0)
    RECEIPTS.append({"receipt_id": res.receipt_id, "routed_model": res.routed_model,
                     "latency_ms": res.latency_ms, "egress": res.egress, "items": len(items)})
    return {str(x["id"]): x for x in res.parsed["results"]}
