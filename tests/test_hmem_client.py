"""Contract test against the running pi-hmem service (skipped when it is down)."""
import uuid

import httpx
import pytest

from app.adapters.hmem_client import HMemClient


@pytest.fixture
def hm():
    c = HMemClient(url="http://127.0.0.1:7070", timeout=5)
    try:
        c.healthz()
    except httpx.HTTPError:
        pytest.skip("pi-hmem not running")
    return c


def test_dismiss_is_recalled_by_exact_filter_and_scoped_by_agency(hm):
    uen = "T" + uuid.uuid4().hex[:8].upper()
    run = f"run_test_{uuid.uuid4().hex[:6]}"
    mid = hm.auditor_decision(run_id=run, finding_id="R1-x", uen=uen, flag_id="R1", agency="Agency A", decision="dismiss",
                              reason="Known new SME, checked evaluation file", pattern_tag="new_sme")
    got = hm.recall(agency="Agency A", uen=uen, flag_id="R1", query=f"R1 {uen}")
    assert any(m["id"] == mid and m["meta"]["decision"] == "dismiss" for m in got)
    other = hm.recall(agency="Agency B", uen=uen, flag_id="R1", query=f"R1 {uen}")
    assert all(m["id"] != mid for m in other)
