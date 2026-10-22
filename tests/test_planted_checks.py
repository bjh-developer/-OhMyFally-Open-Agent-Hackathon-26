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

PLANTED = json.loads((Path(__file__).resolve().parent.parent / "data" / "eval" / "planted.json").read_text())["cases"]
runner._lit = lambda v: v.replace("\\", "\\\\").replace("'", "\\'")  # Spark quote escaping (see scripts/run_check.py)


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


pytestmark = pytest.mark.skipif(not _zetaris_up(), reason="Zetaris not reachable")

CASES = [(c, f) for c in PLANTED for f in c["flags"] if f != "R9"]  # R9 check is built on D2


@pytest.mark.parametrize("case,flag", CASES, ids=[f"{c['case_id']}-{f}" for c, f in CASES])
def test_check_catches_planted_case(case, flag):
    sql = runner.render(runner.load_sql(flag), agency=case["agency"], date_from="2021-04-01", date_to="2026-03-31")
    headers, rows, _ = zetaris_query(sql)
    assert headers == runner.CHECK_COLUMNS
    found = {r[headers.index("tender_no")] for r in rows}
    expected = {a["tender_no"] for a in case["awards"]}
    assert expected <= found, f"{flag} missed {expected - found}"
