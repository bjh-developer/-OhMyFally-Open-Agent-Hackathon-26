"""Critic/Planner behaviour that must fire on real-looking data: R3 address density, plan review, visible memory."""
import json
import shutil
from datetime import date

import pytest

from app.checks import runner
from app.orchestration.graph import run_investigation
from app.orchestration.state import Deps
from app.schemas import RunRequest
from app.tracing import Tracer
from tests.fakes import FakeLLM, FakeSQL

REQ = RunRequest(agency="Housing and Development Board", date_from=date(2025, 1, 1), date_to=date(2025, 12, 31), flags=["R1", "R3"])
UENS = ["201111111A", "201122222B", "201133333C"]
DENS_HEAD = ["uen", "level_no", "unit_no", "postal_code", "n_entities"]


@pytest.fixture(autouse=True)
def _checks(monkeypatch):
    monkeypatch.setattr(runner, "CHECKS_DIR", runner.ROOT / "tests" / "fixtures" / "checks_r3")


def deps(tmp_path, sql=None, llm=None, **kw):
    return Deps(tracer=Tracer("run_t", tmp_path), sql=sql or FakeSQL(), llm=llm or FakeLLM(), **kw)


def trace(tmp_path):
    return [json.loads(x) for x in (tmp_path / "run_t.jsonl").read_text().splitlines()]


def density(n, level="06", unit="28"):
    return {"density": lambda _: {"headers": DENS_HEAD, "data": [[u, level, unit, "409051", str(n)] for u in UENS]}}


def r3(final):
    return [f for f in final["findings"] if f.flag_id == "R3"]


def test_busy_address_is_downgraded_with_a_plain_note(tmp_path):
    final = run_investigation(REQ, deps(tmp_path, FakeSQL(density(60))))
    fs = r3(final)
    assert len(fs) == 4 and all(f.confidence <= 0.72 and f.status in ("accepted",) for f in fs)
    assert all(any("Many businesses are registered at this address" in n for n in f.notes) for f in fs)
    ev = [e for e in trace(tmp_path) if e["action"] == "address_density"]
    assert len(ev) == 1 and ev[0]["status"] == "needs_revision" and ev[0]["output_summary"].startswith("downgrade") and ev[0]["zetaris_query_ids"]


def test_quiet_address_is_escalated_with_reason(tmp_path):
    final = run_investigation(REQ, deps(tmp_path, FakeSQL(density(3))))
    fs = r3(final)
    assert fs and all(f.status == "escalated" for f in fs)
    assert any("quiet address (3 entities)" in n for n in fs[0].notes)
    ev = [e for e in trace(tmp_path) if e["action"] == "address_density"]
    assert ev[0]["status"] == "escalated" and "escalate" in ev[0]["output_summary"]
    assert set(final["memo"].escalated) >= {f.finding_id for f in fs}


def test_missing_level_and_unit_is_escalated_even_when_busy(tmp_path):
    final = run_investigation(REQ, deps(tmp_path, FakeSQL(density(90, level="na", unit=""))))
    assert all(f.status == "escalated" for f in r3(final))
    assert "level and unit are missing" in " ".join(r3(final)[0].notes)


def test_density_is_checked_once_per_finding_not_per_critic_loop(tmp_path):
    sql = FakeSQL(density(60))
    run_investigation(REQ, deps(tmp_path, sql))
    assert sql.counts["density"] == 1


class ShortPlanLLM(FakeLLM):
    """Planner drops R3 although it is a must-have check that exists."""

    def __call__(self, lane, messages, json_schema=None, **kw):
        if "Planner" in messages[0]["content"]:
            res = super().__call__(lane, messages, json_schema=json_schema, **kw)
            data = {"checks": ["R1"], "rationale": "only the newest-supplier check"}
            return res.__class__(**{**res.__dict__, "content": json.dumps(data), "parsed": json_schema.model_validate(data)})
        return super().__call__(lane, messages, json_schema=json_schema, **kw)


def test_plan_gap_triggers_exactly_one_replan(tmp_path):
    req = REQ.model_copy(update={"flags": []})
    final = run_investigation(req, deps(tmp_path, FakeSQL(density(60)), ShortPlanLLM()))
    ev = trace(tmp_path)
    reviews = [e for e in ev if e["action"] == "plan_review"]
    assert [e["status"] for e in reviews] == ["needs_revision", "success"] and reviews[0]["target_agent"] == "PlannerAgent"
    assert len([e for e in ev if e["agent_name"] == "PlannerAgent"]) == 2
    assert final["plan"].replan_count == 1 and "R3" in final["plan"].checks
    assert r3(final)  # the replanned check actually ran


def test_period_outside_data_is_a_limitation_not_a_replan(tmp_path):
    cov = {"coverage": lambda _: {"headers": ["n_all", "min_date", "max_date", "n_period", "n_etq"], "data": [["100", "2021-04-01", "2023-03-31", "0", "4"]]}}
    final = run_investigation(REQ, deps(tmp_path, FakeSQL(cov)))
    assert any("outside the data range" in x for x in final["plan_limitations"])
    rev = [e for e in trace(tmp_path) if e["action"] == "plan_review"]
    assert len(rev) == 1 and rev[0]["status"] == "partial_success"


def test_zero_quotations_makes_r4_partial(tmp_path, monkeypatch):
    d = tmp_path / "checks"
    d.mkdir()
    for n in ("R1", "R4"):
        shutil.copy(runner.ROOT / "tests" / "fixtures" / "checks" / "R1.sql", d / f"{n}.sql")
    monkeypatch.setattr(runner, "CHECKS_DIR", d)
    cov = {"coverage": lambda _: {"headers": ["n_all", "min_date", "max_date", "n_period", "n_etq"], "data": [["100", "2021-04-01", "2026-03-31", "40", "0"]]}}
    final = run_investigation(REQ.model_copy(update={"flags": []}), deps(tmp_path / "out", FakeSQL(cov)))
    assert any("R4 is partial" in x and "0 quotation (ETQ)" in x for x in final["plan_limitations"])


def test_unresolved_names_get_r8_added_on_replan(tmp_path, monkeypatch):
    d = tmp_path / "checks"
    d.mkdir()
    for n in ("R1", "R8"):
        shutil.copy(runner.ROOT / "tests" / "fixtures" / "checks" / "R1.sql", d / f"{n}.sql")
    monkeypatch.setattr(runner, "CHECKS_DIR", d)
    xw = {"headers": ["supplier_name", "uen", "confidence", "method"],
          "data": [[f"NAME {i} PTE. LTD.", "", "0", "unresolved"] for i in range(6)] + [["ZYLOQ TEST ENGINEERING PTE. LTD.", "T99ZZ0001A", "1.0", "exact"]]}
    final = run_investigation(REQ.model_copy(update={"flags": []}), deps(tmp_path / "out", FakeSQL({"xwalk": lambda _: xw}), ShortPlanLLM()))
    assert "R8" in final["plan"].checks and final["plan"].replan_count == 1


class Mem:
    def recall(self, **kw):
        return [{"id": "mem_1", "content": "Dismissed: sister companies", "meta": {"agency": REQ.agency}},
                {"id": "mem_2", "content": "Confirmed: new vendor", "meta": {"agency": REQ.agency}}]

    def feedback(self, *a):
        pass


def test_memory_hits_are_emitted_by_planner_and_critic(tmp_path):
    run_investigation(REQ, deps(tmp_path, hmem=Mem()))
    ev = trace(tmp_path)
    p = [e for e in ev if e["agent_name"] == "PlannerAgent"][0]
    assert p["memory_hits"] == 2 and p["memory_ids"] == ["mem_1", "mem_2"] and "used 2 past decisions" in p["output_summary"]
    c = [e for e in ev if e["action"] == "validate_claims"][0]
    assert c["memory_hits"] == 2 and c["memory_ids"] == ["mem_1", "mem_2"] and "past decision" in c["output_summary"]


def test_no_memory_fields_without_hmem(tmp_path):
    run_investigation(REQ, deps(tmp_path))
    assert all("memory_hits" not in e and "memory_ids" not in e for e in trace(tmp_path))
