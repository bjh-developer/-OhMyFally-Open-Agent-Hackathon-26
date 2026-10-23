"""AGO citations: the curated flag -> excerpt map is valid, and the Reporter attaches refs only where a mapping exists."""
import json
from datetime import date

import pytest

from app.agents import ago, reporter
from app.checks.rules import red_flags
from app.orchestration.state import Deps
from app.schemas import Finding, Plan, RunRequest
from app.tracing import Tracer
from tests.fakes import FakeLLM, FakeSQL

ROOT = ago.ROOT
REQ = RunRequest(agency="People's Association", date_from=date(2021, 4, 1), date_to=date(2026, 3, 31))


def test_every_mapped_chunk_exists():
    ui_index = json.loads((ROOT / "web" / "lib" / "ago-index.json").read_text(encoding="utf-8"))
    for flag, entries in ago.ago_map().items():
        for e in entries:
            cid = e["chunk_id"]
            assert cid in ago.ago_index(), f"{flag}: {cid} not in data/ago/index.csv"
            assert (ROOT / "data" / "ago" / f"{cid}.txt").exists(), f"{flag}: {cid}.txt missing"
            assert cid in ui_index, f"{flag}: {cid} not in web/lib/ago-index.json"
            assert e["rationale"].strip(), f"{flag}: {cid} has no rationale"


def test_map_keys_are_known_flags():
    assert set(ago.ago_map()) <= set(red_flags())


def test_no_duplicate_chunks_within_a_flag():
    for flag, entries in ago.ago_map().items():
        ids = [e["chunk_id"] for e in entries]
        assert len(ids) == len(set(ids)), flag


def test_r1_is_not_cited_against_edb_evaluation():
    """22 Oct audit: an R1 finding cited an unrelated EDB evaluation excerpt."""
    assert ago.refs_for("R1") == []
    assert all("edb" not in c for f in ("R1", "R2", "R3", "R8") for c in ago.refs_for(f))


def test_refs_capped_and_unknown_flag_empty():
    assert len(ago.refs_for("R9")) <= ago.MAX_REFS
    assert ago.refs_for("R99") == []
    assert ago.why_line("R99") is None


def _finding(fid: str, flag: str) -> Finding:
    return Finding(finding_id=fid, flag_id=flag, tender_no=f"T-{fid}", agency=REQ.agency, supplier_name=f"Supplier {fid}",
                   summary="An anomaly for review.", confidence=0.9, status="accepted", award_date=date(2024, 1, 1), awarded_amt=1000)


def _run_reporter(tmp_path, flags: list[str]):
    findings = [_finding(f"F{i}", fl) for i, fl in enumerate(flags)]
    d = Deps(tracer=Tracer("run_t", tmp_path), sql=FakeSQL(), llm=FakeLLM())
    state = {"run_id": "run_t", "request": REQ, "plan": Plan(checks=sorted(set(flags))), "findings": findings,
             "scores": {f.finding_id: 50 for f in findings}}
    memo = reporter.make(d)(state)["memo"]
    return {f.flag_id: f for f in memo.findings}, memo


def test_reporter_fills_ago_refs_only_for_mapped_flags(tmp_path):
    mapped = [f for f, e in ago.ago_map().items() if e]
    unmapped = [f for f in ("R1", "R2", "R3", "R8") if not ago.ago_map().get(f)]
    assert mapped and unmapped
    by_flag, memo = _run_reporter(tmp_path, mapped + unmapped)
    for f in mapped:
        assert by_flag[f].ago_refs == ago.refs_for(f) and by_flag[f].ago_refs
    for f in unmapped:
        assert by_flag[f].ago_refs == []
    assert memo.markdown.count("- Why it matters:") == len(mapped)


def test_memo_has_no_why_line_without_mapping(tmp_path):
    _, memo = _run_reporter(tmp_path, ["R1"])
    assert "Why it matters" not in memo.markdown
    assert json.loads((tmp_path / "run_t.memo.json").read_text())["findings"][0]["ago_refs"] == []
