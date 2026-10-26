import math
from datetime import date

import pytest

from app.adapters.zetaris import Result
from app.agents import critic, risk
from app.checks.runner import CHECK_COLUMNS, CheckRun, to_findings
from app.checks.semantic import R5PreparationError, validate_scores
from app.orchestration.state import Deps
from app.schemas import Match, Plan, RunRequest
from app.tracing import Tracer
from scripts.prepare_r5 import cosine
from tests.fakes import FakeLLM


def test_cosine_is_normalized_and_rejects_invalid_vectors():
    assert cosine([2, 0], [4, 0]) == 1
    assert cosine([1, 0], [0, 1]) == 0
    assert cosine([1, 0], [-1, 0]) == -1
    for left, right in [([0, 0], [1, 0]), ([1], [1, 2]), ([math.nan], [1])]:
        with pytest.raises(ValueError):
            cosine(left, right)


def test_r5_rejects_missing_stale_or_invalid_preparation():
    pair = {"tender_description": "computer software", "ssic_description": "bakery"}
    params = {"prepared": True, "model": "test", "max_similarity": .2, "similarities": [{**pair, "similarity": .1}]}
    validate_scores(params, [pair])
    for invalid, pairs in [({}, [pair]), (params, [{**pair, "tender_description": "changed source"}]),
                           ({**params, "similarities": [{**pair, "similarity": math.nan}]}, [pair]),
                           ({**params, "similarities": params["similarities"] * 2}, [pair])]:
        with pytest.raises(R5PreparationError):
            validate_scores(invalid, pairs)


def r5_state(tmp_path, match_confidence=1):
    row = dict(zip(CHECK_COLUMNS, ["R5", "TEST-TENDER", "Synthetic Review Agency", "QUILLORA TEST BAKERY PTE LTD",
        "TEST-UEN", "2025-03-01", "120000", "business_description_cosine_similarity", "0.1", "0.2", "Anomaly for review: cosine similarity 0.1."]))
    result = Result(CHECK_COLUMNS, [list(row.values())], "query-test", 1)
    typed = {**row, "awarded_amt": 120000.0, "award_date": date(2025,3,1)}
    finding = to_findings(CheckRun("R5", "SELECT 'R5'", result, [typed]), lambda r: match_confidence)[0]
    request = RunRequest(agency=row["agency"], date_from=date(2025,1,1), date_to=date(2025,12,31), flags=["R5"])
    state = {"run_id": "run_test", "request": request, "plan": Plan(checks=["R5"]), "findings": [finding],
             "matches": {row["supplier_name"]: Match(supplier_name=row["supplier_name"], uen="TEST-UEN", confidence=match_confidence)},
             "retries": {}}
    deps = Deps(tracer=Tracer("run_test", logs_dir=tmp_path), sql=lambda _: result, llm=FakeLLM(), write_files=False)
    return state, deps


def test_r5_semantic_uncertainty_does_not_trigger_identity_retries(tmp_path):
    state, deps = r5_state(tmp_path)
    assert state["findings"][0].confidence == .6
    update = critic.make(deps)(state)
    assert update["route"] == "risk"
    state.update(update)
    update = risk.make(deps)(state)
    assert update["findings"][0].status == "escalated"
    assert update["findings"][0].confidence <= .6


def test_r5_still_retries_a_genuinely_weak_identity_match(tmp_path):
    state, deps = r5_state(tmp_path, match_confidence=.8)
    assert critic.make(deps)(state)["route"] == "resolver"
