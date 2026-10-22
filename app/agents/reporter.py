"""Reporter (deep lane): ranked memo. Every claim is tied to evidence; wording rules enforced."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from pydantic import BaseModel

from ..checks.rules import banned_hits, red_flags, sanitise, wording
from ..orchestration.state import Deps, RunState
from ..schemas import Finding, Memo
from .common import compact_finding, dumps

NAME = "ReporterAgent"


class Narrative(BaseModel):
    headline: str
    overview: str


def _render_md(m: Memo, scores: dict[str, float]) -> str:
    L = [f"# Procurement review memo: {m.agency}", f"Period {m.date_from} to {m.date_to}. Run `{m.run_id}`.", "", f"**{m.summary}**", "", f"> {m.disclaimer}", ""]
    L.append(f"## Findings ({len(m.findings)})")
    if not m.findings:
        L.append("No anomalies for review were produced for this scope.")
    for i, f in enumerate(m.findings, 1):
        ev = f.evidence[-1] if f.evidence else None
        L += [f"### {i}. [{f.flag_id}] {f.supplier_name}: {f.tender_no} ({f.status}, priority {scores.get(f.finding_id, 0):.0f})",
              f.summary, f"- Confidence: {f.confidence:.2f}" + (f"; UEN {f.uen}" if f.uen else ""),
              f"- Metric: {f.metric_name} = {f.metric_value} (threshold {f.threshold})"]
        if ev:
            L.append(f"- Evidence: Zetaris query `{ev.query_id}` over {', '.join(ev.source_objects)}, {ev.row_count} row(s)")
        for n in f.notes:
            L.append(f"- Note: {n}")
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
        shown.sort(key=lambda f: (f.status != "accepted", -scores.get(f.finding_id, 0)))
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
                {"role": "user", "content": dumps({"agency": req.agency, "period": [str(req.date_from), str(req.date_to)], "top_findings": [compact_finding(f) for f in shown[:8]],
                                                   "counts": {"shown": len(shown), "suppressed": len(suppressed), "rejected": len(rejected)},
                                                   "answer_format": {"headline": "one sentence", "overview": "2-3 sentences"}})},
            ], json_schema=Narrative, max_tokens=2500)
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
            summary=f"{headline.rstrip('. ')}. {overview}".strip(), findings=shown, limitations=lim, disclaimer=wording()["disclaimer"].strip(),
            escalated=[f.finding_id for f in shown if f.status == "escalated"],
            stats={"candidates": len(findings), "shown": len(shown), "suppressed": len(suppressed), "rejected": len(rejected),
                   "llm_calls": None, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
        )
        memo.markdown = _render_md(memo, scores)
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
