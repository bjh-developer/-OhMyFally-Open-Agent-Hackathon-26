import csv
import time
from datetime import date
from types import SimpleNamespace

import pytest

from app.schemas import RunRequest
from scripts.eval import (LiveSQL, covers, create_review_queue, load_precision_labels,
                          planted_recall, precision_metrics, supplemental_requests)


def request(agency="Test Agency", flags=None, end=date(2025,12,31)):
    return RunRequest(agency=agency, date_from=date(2025,1,1), date_to=end, flags=flags or [])


CASE = {"case_id":"P-TEST", "agency":"Test Agency", "flags":["R6"],
        "awards":[{"tender_no":"T1","supplier_name":"LEADER TEST LTD","award_date":"2025-02-01"},
                  {"tender_no":"T2","supplier_name":"LEADER TEST LTD","award_date":"2025-03-01"},
                  {"tender_no":"T3","supplier_name":"OTHER TEST LTD","award_date":"2025-06-01"}],
        "expected_tenders":{"R6":["T1","T2"]}, "not_expected_tenders":{"R6":["T3"]}}


def run(findings, gaps=None):
    return {"request":request(), "checks":["R6"], "coverage_gaps":gaps or [], "findings":findings}


def finding(tender="T1", name="LEADER TEST LTD"):
    return SimpleNamespace(flag_id="R6", tender_no=tender, supplier_name=name)


def test_recall_counts_expected_awards_and_does_not_accept_wrong_supplier():
    report = planted_recall([CASE], [run([finding(), finding("T2", "WRONG TEST LTD")])])
    assert report["expected_awards"] == 2
    assert report["found_awards"] == 1
    assert report["award_recall"] == .5
    assert report["case_recall"] == 0
    assert report["results"][0]["missed_tenders"] == ["T2"]


def test_failed_check_stays_in_recall_denominator_and_is_not_evaluated():
    report = planted_recall([CASE], [run([finding()], gaps=["R6"])])
    assert report["expected_awards"] == 2 and report["award_recall"] == 0
    assert report["case_flags_evaluated"] == 0


def test_negative_controls_are_checked_separately():
    report = planted_recall([CASE], [run([finding(), finding("T2"), finding("T3", "OTHER TEST LTD")])])
    assert report["case_recall"] == 1
    assert report["negative_controls_passed"] is False


def test_case_recall_requires_every_flag_for_a_multiflag_case():
    case={"case_id":"MULTI", "agency":"Test Agency", "flags":["R1","R6"], "awards":[CASE["awards"][0]]}
    report=planted_recall([case], [run([finding()])])
    assert report["case_flag_recall"] == .5
    assert report["case_recall"] == 0 and report["cases_caught"] == 0


def test_supplemental_scope_accounts_for_flags_dates_and_negative_context():
    implemented = ["R1", "R6"]
    assert supplemental_requests([request()], [CASE], implemented) == []
    assert not covers(request(end=date(2025,4,1)), CASE, "R6", implemented)
    extra = supplemental_requests([request(flags=["R1"])], [CASE], implemented)
    assert len(extra) == 1 and extra[0].flags == ["R6"]
    assert extra[0].agency == "Test Agency"
    assert covers(extra[0], CASE, "R6", extra[0].flags)


def review(fid, label="", status="pending"):
    return {"finding_id":fid, "label":label, "review_status":status,
            "reviewer":"human" if status != "pending" else "", "reason":"Evidence reviewed" if status != "pending" else ""}


def test_precision_excludes_unclear_pending_agent_and_unmatched_labels():
    rows = [review("1","plausible","human_reviewed"), review("2","explained","human_reviewed"),
            review("3","unclear","human_reviewed"), review("4"), review("5","plausible","agent_reviewed"),
            review("stale","plausible","human_reviewed")]
    report = precision_metrics(rows, {str(i):None for i in range(1,6)})
    assert report["precision"] == .5 and report["decided"] == 2
    assert report["human_reviewed"] == 3 and report["pending"] == 1
    assert report["agent_reviewed_excluded"] == 1 and report["unmatched_labels"] == 1
    assert precision_metrics([], {"1":None})["precision"] is None


@pytest.mark.parametrize("rows", [
    [review("1","plausible")],
    [review("1","bad-label","human_reviewed")],
    [review("1"),review("1")],
    [{**review("1","plausible","human_reviewed"),"reason":""}],
])
def test_invalid_precision_labels_are_rejected(tmp_path, rows):
    path = tmp_path / "labels.csv"
    with path.open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError):
        load_precision_labels(path)


def test_review_queue_is_pending_private_and_preserves_existing_file(tmp_path):
    candidate = SimpleNamespace(finding_id="F1",flag_id="R1",tender_no="T1",agency="Test Agency",awarded_amt=100,
        metric_name="age_days",metric_value="20",threshold="183",evidence=[],supplier_name="PERSONAL NAME NEVER EXPORTED")
    path=tmp_path / "precision.csv"
    assert create_review_queue(path, {"F1":candidate})
    rows=load_precision_labels(path)
    assert len(rows)==1 and rows[0]["review_status"]=="pending" and rows[0]["label"]==""
    original=path.read_bytes()
    assert b"PERSONAL NAME" not in original
    assert create_review_queue(path, {}) is False
    assert path.read_bytes()==original


def test_expired_budget_stops_before_external_query():
    with pytest.raises(TimeoutError):
        LiveSQL(time.monotonic()-1)("SELECT 1")
