import json
from datetime import date

import pytest

from app.adapters.nightshift import budget_scope
from app.checks import runner
from app.orchestration.graph import run_investigation
from app.orchestration.state import Deps
from app.schemas import Match, RunRequest
from app.tracing import Tracer
from tests.fakes import FakeLLM, FakeSQL

REQ = RunRequest(agency="Housing and Development Board", date_from=date(2025, 1, 1), date_to=date(2025, 12, 31))


@pytest.fixture(autouse=True)
def _checks(monkeypatch):
    monkeypatch.setattr(runner, "CHECKS_DIR", runner.ROOT / "tests" / "fixtures" / "checks")


def deps(tmp_path, sql=None, llm=None, **kw):
    return Deps(tracer=Tracer("run_t", tmp_path), sql=sql or FakeSQL(), llm=llm or FakeLLM(), **kw)


def trace(tmp_path):
    return [json.loads(x) for x in (tmp_path / "run_t.jsonl").read_text().splitlines()]


def test_happy_path_r1_memo(tmp_path):
    sql, llm = FakeSQL(), FakeLLM()
    final = run_investigation(REQ, deps(tmp_path, sql, llm))
    memo = final["memo"]
    assert len(memo.findings) == 1
    f = memo.findings[0]
    assert f.flag_id == "R1" and f.status == "accepted" and f.uen == "T99ZZ0001A" and f.wording_checked
    assert f.evidence[0].query_id and f.evidence[0].rows[0]["tender_no"] == "PLT000ETT25000001"
    assert len(f.evidence) == 2  # analyst run + critic's independent re-run
    assert f.evidence[0].query_id != f.evidence[1].query_id
    assert "anomaly for review" in f.summary
    assert (tmp_path / "run_t.md").exists() and (tmp_path / "run_t.memo.json").exists()
    agents = [e["agent_name"] for e in trace(tmp_path)]
    for a in ("GateAgent", "PlannerAgent", "ResolverAgent", "AnalystAgent", "CriticAgent", "RiskAgent", "ReporterAgent"):
        assert a in agents
    crit = [e for e in trace(tmp_path) if e["action"] == "validate_claims"][0]
    assert crit["zetaris_query_ids"] and crit["meterless_receipt_id"].startswith("rcpt_critic")
    assert [l for l, _ in llm.calls] == ["deep", "fast", "deep", "deep"]  # planner, critic, risk, reporter
    assert memo.stats["llm_calls"] == 4


def test_critic_retry_then_ok(tmp_path):
    """First analyst run returns a row that a fresh run no longer reproduces: Critic sends it back once."""
    from tests.fakes import load
    good = load("zetaris")["R1"]
    stale = {"headers": good["headers"], "data": [[*good["data"][0][:8], "99", *good["data"][0][9:]]]}
    # call 1 (analyst) stale, call 2 (critic) good -> mismatch; call 3 (analyst retry) good, call 4 (critic) good
    sql = FakeSQL({"R1": lambda n: stale if n == 1 else good})
    final = run_investigation(REQ, deps(tmp_path, sql))
    assert final["memo"].findings[0].status == "accepted"
    ev = trace(tmp_path)
    crit = [e for e in ev if e["action"] == "validate_claims"]
    assert crit[0]["status"] == "needs_revision" and crit[0]["target_agent"] == "AnalystAgent"
    assert crit[1]["status"] == "success"
    assert [e for e in ev if e["action"] == "run_check:R1"][-1]["retry_count"] == 1


def test_critic_gives_up_after_max_retries(tmp_path):
    from tests.fakes import load
    good = load("zetaris")["R1"]
    flip = lambda n: {"headers": good["headers"], "data": [[*good["data"][0][:8], str(100 + n), *good["data"][0][9:]]]}  # never reproducible
    sql = FakeSQL({"R1": flip})
    final = run_investigation(REQ, deps(tmp_path, sql))
    assert final["memo"].findings == [] and final["memo"].stats["rejected"] == 1
    assert sql.counts["R1"] == 2 * 3 - 0  # (analyst + critic) x (1 run + 2 retries)


def test_weak_match_goes_back_to_resolver_then_rejected(tmp_path):
    from tests.fakes import load
    xw = load("zetaris")["xwalk"]
    weak = {"headers": xw["headers"], "data": [["ZYLOQ TEST ENGINEERING PTE. LTD.", "T99ZZ0001A", "0.81", "fuzzy"], xw["data"][1]]}
    calls = []

    def resolve(names, strategy="default"):
        calls.append((tuple(names), strategy))
        return [Match(supplier_name=n, uen="T99ZZ0001A", confidence=0.81, method="fuzzy") for n in names]

    final = run_investigation(REQ, deps(tmp_path, FakeSQL({"xwalk": lambda n: weak}), resolve=resolve))
    assert final["memo"].findings == []
    assert [s for _, s in calls] == ["fuzzy", "llm_tiebreak"]  # two retries, different strategy each time
    notes = " ".join(" ".join(f.notes) for f in final["findings"])
    assert "Rejected" in notes


def test_weak_match_improved_by_resolver(tmp_path):
    from tests.fakes import load
    xw = load("zetaris")["xwalk"]
    weak = {"headers": xw["headers"], "data": [["ZYLOQ TEST ENGINEERING PTE. LTD.", "T99ZZ0001A", "0.81", "fuzzy"], xw["data"][1]]}

    def resolve(names, strategy="default"):
        return [Match(supplier_name=n, uen="T99ZZ0001A", confidence=0.97, method="llm_tiebreak") for n in names]

    final = run_investigation(REQ, deps(tmp_path, FakeSQL({"xwalk": lambda n: weak}), resolve=resolve))
    assert final["memo"].findings[0].confidence == 0.97


def test_banned_wording_is_rewritten(tmp_path):
    from tests.fakes import load
    good = load("zetaris")["R1"]
    bad = {"headers": good["headers"], "data": [[*good["data"][0][:10], "This looks like fraud and a scam."]]}
    final = run_investigation(REQ, deps(tmp_path, FakeSQL({"R1": lambda n: bad})))
    f = final["memo"].findings[0]
    assert "fraud" not in f.summary.lower() and "scam" not in f.summary.lower() and f.wording_checked
    assert any(e["agent_name"] == "RiskAgent" and "1 wording violations" in e["output_summary"] for e in trace(tmp_path))


def test_gate_rejects_bad_request(tmp_path):
    bad = RunRequest(agency="HDB", date_from=date(2025, 12, 1), date_to=date(2025, 1, 1))
    final = run_investigation(bad, deps(tmp_path))
    assert final.get("memo") is None and "before" in final["rejected_reason"]


def test_llm_failures_degrade_gracefully(tmp_path):
    final = run_investigation(REQ, deps(tmp_path, llm=FakeLLM(fail={"planner", "critic", "risk", "reporter"})))
    assert len(final["memo"].findings) == 1
    assert [e for e in trace(tmp_path) if e["agent_name"] == "PlannerAgent"][0]["status"] == "partial_success"


def test_call_cap_bounds_run(tmp_path):
    final = run_investigation(REQ, deps(tmp_path), llm_cap=2)
    assert final["memo"].stats["llm_calls"] == 2  # planner + critic fit; risk/reporter hit the cap and degrade


def test_hmem_dismiss_suppresses_and_cites(tmp_path):
    class H:
        def recall(self, **kw):
            return [{"id": "mem_1", "content": "Dismissed: known new SME", "meta": {"uen": "T99ZZ0001A", "flag_id": "R1", "agency": REQ.agency, "decision": "dismiss"}}]

        def feedback(self, *a):
            self.fb = a

    h = H()
    final = run_investigation(REQ, deps(tmp_path, hmem=h))
    assert final["memo"].findings == [] and final["memo"].stats["suppressed"] == 1
    assert final["findings"][0].memory_refs == ["mem_1"] and h.fb[1] == "helpful"


def test_unverifiable_claim_escalates_after_retries(tmp_path):
    fid = runner.finding_id("R1", "PLT000ETT25000001", "ZYLOQ TEST ENGINEERING PTE. LTD.", "T99ZZ0001A")
    sql, llm = FakeSQL(), FakeLLM(unsupported={fid})
    final = run_investigation(REQ, deps(tmp_path, sql, llm))
    f = final["memo"].findings[0]
    assert f.status == "escalated" and final["memo"].escalated == [fid]
    assert sql.counts["R1"] == 6 and [e["status"] for e in trace(tmp_path) if e["action"] == "validate_claims"] == ["needs_revision", "needs_revision", "success"]


def test_requested_flag_without_sql_is_a_reported_gap(tmp_path):
    req = REQ.model_copy(update={"flags": ["R1", "R4"]})
    final = run_investigation(req, deps(tmp_path))
    assert "R4" in final["coverage_gaps"] and any("R4: not run" in x for x in final["memo"].limitations)


def test_r3_awards_are_grouped_by_shared_address(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "CHECKS_DIR", runner.ROOT / "tests" / "fixtures" / "checks_r3")
    req = REQ.model_copy(update={"flags": ["R1", "R3"]})
    final = run_investigation(req, deps(tmp_path))
    memo = final["memo"]
    assert len(memo.findings) == 5 and len(memo.groups) == 1  # 1 R1 + 4 R3 awards -> 1 group
    g = memo.groups[0]
    assert g.flag_id == "R3" and g.n_awards == 4 and g.total_amt == 260000 and len(g.suppliers) == 3
    assert "3 winning suppliers share 60 PAYA LEBAR ROAD #06-28 S409051" == g.title
    assert set(g.finding_ids) == {f.finding_id for f in memo.findings if f.flag_id == "R3"}
    ids = [f.finding_id for f in memo.findings]
    pos = sorted(ids.index(i) for i in g.finding_ids)
    assert pos == list(range(pos[0], pos[0] + 4))  # members are adjacent in the flat list
    md = memo.markdown
    assert md.count("### ") == 2 and "| BETA EVENTS PTE. LTD. | 201122222B | T2 |" in md and "5 awards in 2 entries" in md
