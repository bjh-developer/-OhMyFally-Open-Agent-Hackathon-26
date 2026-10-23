"""Integration: every sql/checks/R*.sql catches its planted case through Zetaris.

Needs the stack up and seeded/registered/resolved:
  python scripts/seed.py && python scripts/register_zetaris.py
  python -m app.resolver.run --pass 1 && python -m app.resolver.run --pass 2
Skipped when Zetaris is unreachable.
"""
import json
from pathlib import Path

import pytest

from app.checks import runner
from app.resolver.entities import zetaris_query
from app.adapters.config import get_settings

PLANTED = json.loads((Path(__file__).resolve().parent.parent / "data" / "eval" / "planted.json").read_text())["cases"]


def _zetaris_up() -> bool:
    try:
        zetaris_query("SELECT count(*) FROM gebiz_pg.supplier_xwalk", timeout=20)
        return True
    except Exception:
        return False


@pytest.fixture(autouse=True)
def _real_env(monkeypatch):
    """conftest.py fakes Zetaris/Nightshift env for unit tests; integration tests want the real .env."""
    for k in ("ZETARIS_REST_URL", "ZETARIS_ORG_ID", "ZETARIS_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("SAMPLE_MODE", "false")
    get_settings.cache_clear()


pytestmark = pytest.mark.skipif(not _zetaris_up(), reason="Zetaris not reachable")

CASES = [(c, f) for c in PLANTED for f in c["flags"]]


@pytest.mark.parametrize("case,flag", CASES, ids=[f"{c['case_id']}-{f}" for c, f in CASES])
def test_check_catches_planted_case(case, flag):
    from app.adapters.zetaris import run_sql
    run = runner.run_check(flag, agency=case["agency"], date_from="2021-04-01", date_to="2026-03-31",
                           run_sql=lambda sql: run_sql(sql, limit=100000, timeout=90, retries=0))
    assert not run.result.replayed
    assert run.result.headers == runner.CHECK_COLUMNS
    found = {r["tender_no"] for r in run.rows}
    expected = set(case.get("expected_tenders", {}).get(flag, [a["tender_no"] for a in case["awards"]]))
    assert expected <= found, f"{flag} missed {expected - found}"
    assert not found.intersection(case.get("not_expected_tenders", {}).get(flag, []))
