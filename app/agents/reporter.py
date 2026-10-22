"""Reporter (deep lane): ranked memo. Every claim is tied to evidence; wording rules enforced."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

from pydantic import BaseModel

from ..checks.rules import banned_hits, red_flags, sanitise, wording
from ..orchestration.state import Deps, RunState
from ..schemas import Finding, FindingGroup, Memo
from .common import compact_finding, dumps

NAME = "ReporterAgent"


class Narrative(BaseModel):
    headline: str
    overview: str


GROUPED_FLAGS = {"R3"}  # many awards, one underlying pattern: show one entry per shared address
_ADDR = re.compile(r"share the ACRA address (.+?)\.\s", re.S)


def _unit_key(f: Finding) -> str | None:
    """Key for findings that belong together. R3 rows carry the same detail text for the whole address group."""
    if f.flag_id in GROUPED_FLAGS and f.detail:
        return f"{f.flag_id}|{f.agency}|{f.detail}"
    return None


def _group_title(f: Finding, n_suppliers: int) -> str:
    m = _ADDR.search((f.detail or "") + " ")
    where = m.group(1) if m else "the same registered address"
    return f"{n_suppliers} winning suppliers share {where}"


def _n_suppliers(f: Finding, suppliers: list[str]) -> int:
    try:  # the check's own count (distinct UENs) beats counting names
        return int(float(f.metric_value or ""))
    except ValueError:
        return len(suppliers)


def build_units(shown: list[Finding], scores: dict[str, float]) -> tuple[list[Finding], list[FindingGroup], list[list[Finding]]]:
    """Order findings into ranked units (a single finding or a group). Returns (flat findings, groups, units)."""
    buckets: dict[str, list[Finding]] = {}
    units: list[list[Finding]] = []
    for f in shown:
        k = _unit_key(f)
        if k is None:
            units.append([f])
        elif k in buckets:
            buckets[k].append(f)
        else:
            buckets[k] = [f]
            units.append(buckets[k])

    def rank(u: list[Finding]) -> tuple:
        return (not any(x.status == "accepted" for x in u), -max(scores.get(x.finding_id, 0) for x in u))

    units.sort(key=rank)
    groups: list[FindingGroup] = []
    for u in units:
        u.sort(key=lambda x: (str(x.award_date or ""), x.tender_no))
        if _unit_key(u[0]) is None:
            continue
        sup = list(dict.fromkeys(x.supplier_name for x in u))
        groups.append(FindingGroup(
            group_id="G-" + hashlib.sha1(_unit_key(u[0]).encode()).hexdigest()[:8], flag_id=u[0].flag_id,
            title=_group_title(u[0], _n_suppliers(u[0], sup)), detail=u[0].detail or "",
            finding_ids=[x.finding_id for x in u], suppliers=sup, n_awards=len(u),
            total_amt=round(sum(x.awarded_amt or 0 for x in u), 2),
            status="accepted" if any(x.status == "accepted" for x in u) else "escalated",
            priority=max(scores.get(x.finding_id, 0) for x in u)))
    return [f for u in units for f in u], groups, units


def _ev_line(f: Finding) -> str | None:
    ev = f.evidence[-1] if f.evidence else None
    return f"- Evidence: Zetaris query `{ev.query_id}` over {', '.join(ev.source_objects)}, {ev.row_count} row(s)" if ev else None


def _render_md(m: Memo, scores: dict[str, float], units: list[list[Finding]], groups: list[FindingGroup]) -> str:
    gby = {g.finding_ids[0]: g for g in groups}
    L = [f"# Procurement review memo: {m.agency}", f"Period {m.date_from} to {m.date_to}. Run `{m.run_id}`.", "", f"**{m.summary}**", "", f"> {m.disclaimer}", ""]
    L.append(f"## Findings ({len(m.findings)} awards in {len(units)} entries)")
    if not m.findings:
        L.append("No anomalies for review were produced for this scope.")
    for i, u in enumerate(units, 1):
        f = u[0]
        g = gby.get(f.finding_id)
        if g:
            L += [f"### {i}. [{g.flag_id}] {g.title} ({g.status}, priority {g.priority:.0f})",
                  f"{g.detail} Together these {g.n_awards} awards total S${g.total_amt:,.0f}.", "",
                  "| Supplier | UEN | Tender | Award date | Amount (S$) |", "|---|---|---|---|---|"]
            L += [f"| {x.supplier_name} | {x.uen or ''} | {x.tender_no} | {x.award_date} | {(x.awarded_amt or 0):,.0f} |" for x in u]
            L.append(_ev_line(f) or "")
            L += [f"- Note: {n}" for n in dict.fromkeys(n for x in u for n in x.notes)]
            L.append("")
            continue
        L += [f"### {i}. [{f.flag_id}] {f.supplier_name}: {f.tender_no} ({f.status}, priority {scores.get(f.finding_id, 0):.0f})",
              f.summary, f"- Confidence: {f.confidence:.2f}" + (f"; UEN {f.uen}" if f.uen else ""),
              f"- Metric: {f.metric_name} = {f.metric_value} (threshold {f.threshold})"]
        if _ev_line(f):
            L.append(_ev_line(f))
        L += [f"- Note: {n}" for n in f.notes]
        if f.memory_refs:
            L.append(f"- Memory: {', '.join(f.memory_refs)}")
        L.append("")
    if m.limitations:
        L += ["## Limitations", *[f"- {x}" for x in m.limitations], ""]
    return "\n".join(L)


def make(deps: Deps):
    def reporter(state: RunState) -> dict:
        req = state["request"]
        scores = state.get("scores") or {}
        fixes = set(state.get("wording_violations") or [])
        findings = [f.model_copy(deep=True) for f in (state.get("findings") or [])]
        # wording gate: deterministic rewrite of any banned term, then mark checked
        for f in findings:
            if f.finding_id in fixes or banned_hits(f.summary):
                f.summary = sanitise(f.summary)
                f.notes.append("Reporter rewrote banned wording.")
            f.wording_checked = not banned_hits(f.summary)
        shown = [f for f in findings if f.status in ("accepted", "escalated")]
        shown, groups, units = build_units(shown, scores)
        suppressed = [f for f in findings if f.status == "suppressed"]
        rejected = [f for f in findings if f.status == "rejected"]
        # limitations come from the rule metadata of flags actually run
        lim = []
        for fid in state["plan"].checks:
            t = red_flags().get(fid, {}).get("limitation")
            if t:
                lim.append(f"{fid}: {t}")
        for g in state.get("coverage_gaps") or []:
            lim.append(f"{g}: not run (no SQL available or the check failed).")
        res, status, err = None, "success", ""
        headline = f"{len(shown)} award(s) at {req.agency} flagged as anomalies for review"
        overview = ""
        try:
            if not shown:
                raise LookupError("nothing to narrate")
            res = deps.llm("deep", [
                {"role": "system", "content": "You write the opening of an audit memo. Use only the facts given. Use the phrases 'anomaly for review' and 'may indicate'. "
                 "Never use the words fraud, corrupt, illegal, criminal, guilty or scam."},
                {"role": "user", "content": dumps({"agency": req.agency, "period": [str(req.date_from), str(req.date_to)], "top_findings": [{**compact_finding(u[0]), **({"note": f"one of {len(u)} awards at a shared address"} if len(u) > 1 else {})} for u in units[:8]],
                                                   "counts": {"shown": len(shown), "suppressed": len(suppressed), "rejected": len(rejected)},
                                                   "answer_format": {"headline": "one sentence", "overview": "2-3 sentences"}})},
            ], json_schema=Narrative, max_tokens=4000)
            n: Narrative = res.parsed
            if banned_hits(n.headline + " " + n.overview):
                n = Narrative(headline=sanitise(n.headline), overview=sanitise(n.overview))
            headline, overview = n.headline, n.overview
        except LookupError:
            headline = f"No awards at {req.agency} were flagged as anomalies for review in this scope"
            overview = "The checks that ran returned no rows; this does not rule out matters outside the checks or the data available."
        except Exception as e:
            status, err = "partial_success", f"{type(e).__name__}: {str(e)[:160]}"
            overview = f"(narrative unavailable: {type(e).__name__}; findings below are generated from the SQL evidence directly.)"
        memo = Memo(
            run_id=state["run_id"], agency=req.agency, date_from=req.date_from, date_to=req.date_to,
            summary=f"{headline.rstrip('. ')}. {overview}".strip(), findings=shown, groups=groups, limitations=lim, disclaimer=wording()["disclaimer"].strip(),
            escalated=[f.finding_id for f in shown if f.status == "escalated"],
            stats={"candidates": len(findings), "shown": len(shown), "suppressed": len(suppressed), "rejected": len(rejected),
                   "llm_calls": None, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
        )
        memo.markdown = _render_md(memo, scores, units, groups)
        if deps.write_files:
            d = deps.tracer.dir
            (d / f"{memo.run_id}.md").write_text(memo.markdown, encoding="utf-8")
            (d / f"{memo.run_id}.memo.json").write_text(memo.model_dump_json(indent=2), encoding="utf-8")
        out = dict(input=f"{len(findings)} candidates", output=f"memo with {len(shown)} findings ({len(suppressed)} suppressed, {len(rejected)} rejected)" + (f"; narrative failed: {err}" if status != "success" else ""),
                   status=status, query_ids=[])
        if res:
            deps.tracer.llm(NAME, "build_memo", res, **out)
        else:
            deps.tracer.emit(NAME, "build_memo", **out)
        return {"memo": memo, "route": "end"}

    return reporter
