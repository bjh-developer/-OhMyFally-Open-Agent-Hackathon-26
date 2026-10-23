import pytest
from fastapi.testclient import TestClient

from app import api, privacy


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("PSEUDONYM_KEY", "unit-test-key")


def test_pseudonym_is_deterministic_and_keyed(monkeypatch):
    a = privacy.pseudonym("ACME PTE. LTD.")
    assert a == privacy.pseudonym("  acme pte. ltd. ")
    assert a.startswith("Supplier-") and len(a) == len("Supplier-7F3A")
    monkeypatch.setenv("PSEUDONYM_KEY", "other-key")
    assert privacy.pseudonym("ACME PTE. LTD.") != a


def test_missing_key_fails_closed(monkeypatch):
    monkeypatch.delenv("PSEUDONYM_KEY")
    with pytest.raises(privacy.PseudonymKeyMissing):
        privacy.mask_payload({"supplier_name": "ACME PTE. LTD."})


def test_mask_payload_everywhere_and_test_suppliers_kept():
    real, fake = "ACME PTE. LTD.", "SHELLCO TEST PTE. LTD."
    memo = {
        "summary": f"{real} won 3 awards; {fake} won 1.",
        "markdown": f"## {real}\nsee {real.lower()}",
        "findings": [
            {"supplier_name": real, "uen": "201234567A", "detail": f"same address as {fake}",
             "evidence": [{"sql": f"... WHERE supplier_name = '{real}'", "rows": [{"supplier_name": real, "entity_name": real}]}]},
            {"supplier_name": fake, "evidence": []},
        ],
        "groups": [{"suppliers": [real, fake, "OTHER CO PTE. LTD."]}],
    }
    out = privacy.mask_payload(memo)
    blob = repr(out)
    alias = privacy.pseudonym(real)
    assert real not in blob and real.lower() not in blob and "OTHER CO" not in blob
    assert out["findings"][0]["supplier_name"] == alias
    assert out["findings"][0]["evidence"][0]["rows"][0]["entity_name"] == alias
    assert out["findings"][0]["uen"] == "201234567A"  # public registry identifier stays
    assert out["findings"][1]["supplier_name"] == fake and fake in out["summary"]
    assert out["groups"][0]["suppliers"][1] == fake
    assert memo["findings"][0]["supplier_name"] == real  # input untouched


def test_longer_name_containing_shorter_is_masked_whole():
    out = privacy.mask_payload({"suppliers": ["ABC PTE. LTD.", "ABC PTE. LTD. (SINGAPORE BRANCH)"],
                                "text": "ABC PTE. LTD. (SINGAPORE BRANCH) and ABC PTE. LTD."})
    assert "ABC" not in out["text"] and "SINGAPORE" not in out["text"]


def _seed_run(tmp_path):
    from datetime import date

    from app.schemas import Finding, Memo
    from app.tracing import Tracer
    real = "ACME PTE. LTD."
    memo = Memo(run_id="run_x", agency="HDB", date_from=date(2025, 1, 1), date_to=date(2025, 12, 31),
                summary=f"{real} flagged", disclaimer="", markdown=f"- {real}",
                findings=[Finding(finding_id="f1", flag_id="R1", tender_no="T1", agency="HDB", supplier_name=real,
                                  uen="201234567A"),
                          Finding(finding_id="f2", flag_id="R1", tender_no="T2", agency="HDB",
                                  supplier_name="ZYLOQ TEST ENGINEERING PTE. LTD.")])
    api._RUNS["run_x"] = {"status": "done", "tracer": Tracer("run_x", tmp_path), "memo": memo, "error": None}
    return real


def test_api_public_view(tmp_path):
    real = _seed_run(tmp_path)
    c = TestClient(api.app)
    full = c.get("/runs/run_x").json()
    assert full["memo"]["findings"][0]["supplier_name"] == real
    pub = c.get("/runs/run_x?view=public").json()["memo"]
    assert real not in repr(pub)
    assert pub["findings"][0]["supplier_name"] == privacy.pseudonym(real) == pub["summary"].split()[0]
    assert pub["findings"][0]["uen"] == "201234567A"
    assert pub["findings"][1]["supplier_name"] == "ZYLOQ TEST ENGINEERING PTE. LTD."
    assert c.get("/runs/run_x?view=bogus").status_code == 422


def test_api_public_view_without_key_is_503_and_full_still_works(tmp_path, monkeypatch):
    _seed_run(tmp_path)
    monkeypatch.delenv("PSEUDONYM_KEY")
    c = TestClient(api.app)
    assert c.get("/runs/run_x?view=public").status_code == 503
    assert c.get("/runs/run_x").status_code == 200
