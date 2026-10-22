"""Minimal Zetaris REST client for the registration script (httpx; one statement per call)."""
from __future__ import annotations

import os
import uuid

import httpx
from dotenv import load_dotenv

from fetch_common import ROOT

load_dotenv(ROOT / ".env")


def run(sql: str, limit: int = 1000, timeout: int = 120) -> dict:
    url = os.environ["ZETARIS_REST_URL"].rstrip("/") + "/sql-editor/sqls/run"
    rid = str(uuid.uuid4())
    r = httpx.post(
        url,
        headers={
            "Authorization": f"Bearer {os.environ['ZETARIS_API_KEY']}",
            "X-Org-ID": os.environ["ZETARIS_ORG_ID"],
            "X-Request-ID": rid,
            "Content-Type": "application/json",
        },
        json={"queryId": rid, "sql": sql, "source": "SqlEditor", "limit": limit},
        timeout=timeout,
    )
    if not r.is_success:
        raise RuntimeError(f"zetaris HTTP {r.status_code}: {r.text[:500]}")
    out = r.json()
    out["query_id"] = rid
    return out
