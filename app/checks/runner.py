"""Loads sql/checks/R*.sql, substitutes parameters safely, runs through Zetaris, builds Findings."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

from ..adapters.config import ROOT
from ..adapters.zetaris import Result, to_date, to_float
from ..schemas import Evidence, Finding
from .rules import red_flags, wording

CHECKS_DIR = ROOT / "sql" / "checks"
CHECK_COLUMNS = ["flag_id", "tender_no", "agency", "supplier_name", "uen", "award_date", "awarded_amt",
                 "metric_name", "metric_value", "threshold", "detail"]
SOURCE_OBJECTS = {
    "R1": ["gebiz_pg.awards", "gebiz_pg.supplier_xwalk", "ACRA_FILES.entities"],
    "R2": ["gebiz_pg.awards", "gebiz_pg.supplier_xwalk", "ACRA_FILES.entities"],
    "R3": ["gebiz_pg.awards", "gebiz_pg.supplier_xwalk", "ACRA_FILES.entities"],
    "R4": ["gebiz_pg.awards"],
    "R8": ["gebiz_pg.awards", "gebiz_pg.supplier_xwalk", "ACRA_FILES.entities"],
}
_AGENCY_OK = re.compile(r"^[\w &.,'()/\-]{1,120}$")
_DATE_OK = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_FLAG_OK = re.compile(r"^R\d{1,2}$")


def available_checks() -> list[str]:
    return sorted((p.stem for p in CHECKS_DIR.glob("R*.sql")), key=lambda s: int(s[1:])) if CHECKS_DIR.exists() else []


def load_sql(flag_id: str) -> str:
    if not _FLAG_OK.match(flag_id):
        raise ValueError(f"bad flag id {flag_id!r}")
    return (CHECKS_DIR / f"{flag_id}.sql").read_text()


def _lit(v: str) -> str:
    return v.replace("'", "''")


def render(sql: str, *, agency: str, date_from: str | date, date_to: str | date) -> str:
    """Substitute {{agency}}, {{date_from}}, {{date_to}}. Values are validated and quote-escaped.

    Works whether the template writes ``'{{agency}}'`` (quotes already there) or bare ``{{agency}}``.
    """
    df, dt = str(date_from), str(date_to)
    if not _AGENCY_OK.match(agency):
        raise ValueError("agency contains characters that are not allowed")
    if not (_DATE_OK.match(df) and _DATE_OK.match(dt)):
        raise ValueError("dates must be YYYY-MM-DD")
    vals = {"agency": agency, "date_from": df, "date_to": dt}

    def sub(m: re.Match) -> str:
        key = m.group(2)
        if key not in vals:
            raise ValueError(f"unknown placeholder {{{{{key}}}}}")
        return f"'{_lit(vals[key])}'"  # always a quoted literal; swallows quotes the template already had

    return re.sub(r"('?)\{\{\s*(\w+)\s*\}\}('?)", sub, sql).strip().rstrip(";")


def finding_id(flag: str, tender_no: str, supplier: str, uen: str | None) -> str:
    h = hashlib.sha1(f"{flag}|{tender_no}|{uen or supplier}".encode()).hexdigest()[:8]
    return f"{flag}-{h}"


@dataclass
class CheckRun:
    flag_id: str
    sql: str
    result: Result
    rows: list[dict[str, Any]]


def run_check(flag_id: str, *, agency: str, date_from: str | date, date_to: str | date,
              run_sql: Callable[[str], Result]) -> CheckRun:
    sql = render(load_sql(flag_id), agency=agency, date_from=date_from, date_to=date_to)
    res = run_sql(sql)
    missing = [c for c in CHECK_COLUMNS if c not in res.headers]
    if missing:
        raise ValueError(f"{flag_id}.sql is missing contract columns: {missing}")
    rows = res.typed({"awarded_amt": float, "award_date": to_date})
    return CheckRun(flag_id, sql, res, rows)


def _fmt_amt(v: float | None) -> str:
    return "n/a" if v is None else f"{v:,.0f}"


def summarise(row: dict[str, Any]) -> str:
    """Deterministic wording-safe summary from the SQL row (no LLM, so it cannot invent facts)."""
    flag = red_flags().get(row["flag_id"], {})
    detail = (row.get("detail") or "").strip()
    if not detail and row.get("metric_name"):
        detail = f"{row['metric_name']} = {row.get('metric_value')} (threshold {row.get('threshold')})."
    return " ".join(wording()["summary_template"].format(
        flag_name=flag.get("name", row["flag_id"]), supplier=row.get("supplier_name"), tender_no=row.get("tender_no"),
        agency=row.get("agency"), amt=_fmt_amt(row.get("awarded_amt")), date=row.get("award_date"), detail=detail,
    ).split())


def to_findings(run: CheckRun, confidence: Callable[[dict], float] | None = None) -> list[Finding]:
    ev_base = dict(query_id=run.result.query_id, sql=run.sql, row_count=len(run.rows),
                   source_objects=SOURCE_OBJECTS.get(run.flag_id, []))
    out: list[Finding] = []
    for r in run.rows:
        ev = Evidence(**ev_base, rows=[{k: (str(v) if isinstance(v, date) else v) for k, v in r.items()}])
        out.append(Finding(
            finding_id=finding_id(run.flag_id, r["tender_no"], r["supplier_name"], r.get("uen")),
            flag_id=run.flag_id, tender_no=r["tender_no"], agency=r["agency"], supplier_name=r["supplier_name"],
            uen=r.get("uen") if r.get("uen") not in ("", "null", None) else None,
            summary=summarise(r), confidence=confidence(r) if confidence else 1.0, evidence=[ev],
            awarded_amt=r.get("awarded_amt"), award_date=r.get("award_date"), metric_name=r.get("metric_name"),
            metric_value=None if r.get("metric_value") is None else str(r["metric_value"]),
            threshold=None if r.get("threshold") is None else str(r["threshold"]), detail=r.get("detail"),
        ))
    return out


# Flags whose evidence depends on a GeBIZ -> ACRA supplier match (R4/R8 work on names and amounts alone).
MATCH_DEPENDENT = {"R1", "R2", "R3", "R5", "R7"}
