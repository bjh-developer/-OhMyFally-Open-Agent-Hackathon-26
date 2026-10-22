"""Fast-lane Nightshift tie-break for ambiguous supplier matches (about 20 suppliers per call)."""
from __future__ import annotations

import json
import re
import time

import httpx

from app.resolver.entities import _env

SYSTEM = (
    "You match Singapore government supplier names to ACRA registry entities. For each item choose the "
    "candidate that is the SAME legal entity as the supplier name, or null if none is clearly the same. "
    "Beware of similar but different companies (different trade words, branches, LLP vs company). "
    'Do not explain. Output the JSON object only, with no other text: '
    '{"results":[{"id":"<id>","uen":"<candidate uen or null>","confidence":0.0-1.0}]}'
)
RECEIPTS: list[dict] = []  # meterless receipts kept for tracing/handover


def _parse(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)


def nightshift_tiebreak(items: list[dict], retries: int = 2) -> dict[str, dict]:
    env = _env()
    payload = [{"id": it["id"], "supplier_name": it["name"],
                "candidates": [{"uen": c["uen"], "name": c["entity_name"], "status": c["status"],
                                "former_name_match": c.get("matched_on", "").endswith("former")}
                               for c in it["candidates"]]} for it in items]
    body = {
        "model": env["METERLESS_MODEL_FAST"],
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": json.dumps(payload) + "\n\nJSON only."}],
        "max_tokens": 3000,
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {env['METERLESS_RUNTIME_TOKEN']}", "meterless-app": env["METERLESS_APP_FAST"],
               "meterless-scope": "user"}
    last = None
    for attempt in range(retries + 1):
        t0 = time.time()
        r = httpx.post(env["METERLESS_BASE_URL"].rstrip("/") + "/chat/completions", headers=headers, json=body, timeout=180)
        if r.status_code >= 500:  # provider hiccup (e.g. empty_response): retry, bounded
            last = RuntimeError(f"HTTP {r.status_code}")
            continue
        r.raise_for_status()
        j = r.json()
        rc = j.get("meterless") or {}
        RECEIPTS.append({"receipt_id": rc.get("receipt_id"), "routed_model": rc.get("routed_model"),
                         "latency_ms": (j.get("usage") or {}).get("latency_ms") or int((time.time() - t0) * 1000),
                         "egress": rc.get("egress"), "items": len(items)})
        try:
            data = _parse(j["choices"][0]["message"]["content"])
            return {str(x["id"]): x for x in data["results"]}
        except Exception as e:  # noqa: BLE001
            last = e
            body["messages"].append({"role": "user", "content": "Invalid JSON. Reply with the JSON object only."})
    raise RuntimeError(f"tie-break returned unparseable output: {last}")
