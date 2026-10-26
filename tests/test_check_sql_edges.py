"""Execute isolated fictional SQL inputs through live Zetaris. Opt in with RUN_LIVE_SQL_TESTS=1."""
import json
import os

import pytest

from app.adapters.config import get_settings
from app.adapters.zetaris import run_sql
from app.checks.runner import CHECK_COLUMNS, _lit, load_sql, render

pytestmark = pytest.mark.skipif(os.getenv("RUN_LIVE_SQL_TESTS") != "1", reason="Set RUN_LIVE_SQL_TESTS=1 for live SQL edge tests")


@pytest.fixture(autouse=True)
def real_zetaris(monkeypatch):
    for key in ("ZETARIS_REST_URL", "ZETARIS_ORG_ID", "ZETARIS_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("SAMPLE_MODE", "false")
    get_settings.cache_clear()


def table(name, columns, rows):
    statements = []
    for row in rows:
        fields = []
        for (key, kind), value in zip(columns, row):
            literal = "NULL" if value is None else f"'{_lit(str(value))}'"
            fields.append(f"CAST({literal} AS {kind}) AS {key}")
        statements.append("SELECT " + ", ".join(fields))
    return name + " AS (" + " UNION ALL ".join(statements) + ")"


AWARD_COLS = [("tender_no","STRING"),("agency","STRING"),("supplier_name","STRING"),
              ("award_date","DATE"),("awarded_amt","DOUBLE"),("tender_description","STRING")]
XWALK_COLS = [("supplier_name","STRING"),("uen","STRING"),("confidence","DOUBLE")]


def execute(flag, fixtures):
    sql = render(load_sql(flag), agency="Synthetic Edge Agency", date_from="2025-01-01", date_to="2025-12-31")
    for source, name, columns, rows in fixtures:
        sql = sql.replace(source, name)
    ctes = [table(name, columns, rows) for _,name,columns,rows in fixtures]
    offset = sql.index("WITH ")
    sql = sql[:offset] + "WITH " + ",\n".join(ctes) + ",\n" + sql[offset+5:]
    result = run_sql(sql, timeout=90, retries=0)
    assert not result.replayed
    assert result.headers == CHECK_COLUMNS
    return result.dicts()


@pytest.mark.parametrize("mode,expected", [("lower_score",1),("tie",0),("incomplete",0),
    ("inconsistent_weights",0),("duplicate_criterion",0),("bad_weight_total",0),("invalid_score",0)])
def test_r9_comparable_weighted_scores_only(mode, expected):
    scores = [["T1","WINNER TEST PTE LTD","price",.4,80], ["T1","WINNER TEST PTE LTD","quality",.6,84],
              ["T1","OTHER TEST PTE LTD","price",.4,92], ["T1","OTHER TEST PTE LTD","quality",.6,88]]
    if mode == "tie":
        scores[0][-1], scores[1][-1] = 92, 88
    elif mode == "incomplete":
        scores.pop()
    elif mode == "inconsistent_weights":
        scores[2][-2], scores[3][-2] = .5, .5
    elif mode == "duplicate_criterion":
        scores.append(list(scores[-1]))
    elif mode == "bad_weight_total":
        for row in scores:
            row[-2] = .4
    elif mode == "invalid_score":
        scores[-1][-1] = 120
    rows = execute("R9", [
        ("gebiz_pg.awards","test_awards",AWARD_COLS,[["T1","Synthetic Edge Agency","WINNER TEST PTE LTD","2025-04-01",10000,"Test technical services"]]),
        ("gebiz_pg.supplier_xwalk","test_xwalk",XWALK_COLS,[["WINNER TEST PTE LTD","TEST-W",1]]),
        ("internal_pg.evaluations","test_evaluations",[("tender_no","STRING"),("supplier_name","STRING"),("criterion","STRING"),("weight","DOUBLE"),("score","DOUBLE")],scores),
    ])
    assert len(rows) == expected
    if rows:
        assert float(rows[0]["metric_value"]) == pytest.approx(82.4)
        assert float(rows[0]["threshold"]) == pytest.approx(89.6)


@pytest.mark.parametrize("leaders,others,expected", [(5,1,5),(3,3,0),(4,0,0)])
def test_r6_share_boundary_and_minimum_category_size(leaders, others, expected):
    awards = [[f"T{i}","Synthetic Edge Agency","LEADER TEST PTE LTD" if i < leaders else "OTHER TEST PTE LTD",
               "2025-04-01",10000,"Provision of road freight transport and delivery services"] for i in range(leaders+others)]
    rows = execute("R6", [
        ("gebiz_pg.awards","test_awards",AWARD_COLS,awards),
        ("gebiz_pg.supplier_xwalk","test_xwalk",XWALK_COLS,[["LEADER TEST PTE LTD","TEST-L",1],["OTHER TEST PTE LTD","TEST-O",1]]),
    ])
    assert len(rows) == expected
    assert all(row["supplier_name"] == "LEADER TEST PTE LTD" for row in rows)


@pytest.mark.parametrize("similarity,confidence,expected", [(.1,1,1),(.2,1,0),(.8,1,0),(.1,.8,0)])
def test_r5_similarity_boundary_and_identity_guard(similarity, confidence, expected):
    description = "Computer software and network support services"
    activity = "Manufacture of bread and confectionery"
    params = json.dumps({"max_similarity":.2,"model":"fixture-only","similarities":[
        {"tender_description":description,"ssic_description":activity,"similarity":similarity}]})
    rows = execute("R5", [
        ("gebiz_pg.awards","test_awards",AWARD_COLS,[["T1","Synthetic Edge Agency","BAKERY TEST PTE LTD","2025-04-01",10000,description]]),
        ("gebiz_pg.supplier_xwalk","test_xwalk",XWALK_COLS,[["BAKERY TEST PTE LTD","TEST-B",confidence]]),
        ("ACRA_FILES.entities","test_entities",[("uen","STRING"),("primary_ssic_description","STRING")],[["TEST-B",activity]]),
        ("gebiz_pg.rules","test_rules",[("flag_id","STRING"),("params","STRING")],[["R5",params]]),
    ])
    assert len(rows) == expected
