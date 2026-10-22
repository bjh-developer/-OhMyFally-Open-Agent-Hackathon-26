"""Critic (fast lane): verifies every finding before it can reach the memo.

1. Re-runs the check SQL (fresh Zetaris query_id) and confirms each cited row still exists.
2. Rejects Resolver matches under the threshold -> back to the Resolver with a different strategy.
3. Queries H-MEM: an exact dismiss memory suppresses the finding; the same pattern down-weights it.
4. One batched fast-lane call: is each summary supported by its evidence rows?
Loops are bounded by ``deps.max_retries``.
"""
from __future__ import annotations

from pydantic import BaseModel

from ..checks.runner import MATCH_DEPENDENT, facts_only, load_sql, render
from ..orchestration.state import Deps, RunState
from ..schemas import Critique, Finding
from .common import compact_finding, dumps

NAME = "CriticAgent"


class ClaimCheck(BaseModel):
    finding_id: str
    supported: bool
    reason: str = ""


class ClaimChecks(BaseModel):
    checks: list[ClaimCheck]


CLAIM_BATCH = 5  # findings per fast-lane claim check

def _row_key(r: dict) -> tuple:
    return (str(r.get("flag_id")), str(r.get("tender_no")), str(r.get("supplier_name")), str(r.get("metric_value")))


def make(deps: Deps):
    def critic(state: RunState) -> dict:
        req = state["request"]
        findings = [f.model_copy(deep=True) for f in (state.get("findings") or [])]
        retries = dict(state.get("retries") or {})
        matches = state.get("matches") or {}
        resolver_retry = state.get("resolver_retry", 0)
        critiques: list[Critique] = []
        revise_checks: list[str] = []
        redo_names: list[str] = []
        memory_refs: list[str] = list(state.get("memory_refs") or [])
        qids: list[str] = []

        # 1. re-run SQL per flag, confirm rows exist
        by_flag: dict[str, list[Finding]] = {}
        for f in findings:
            if f.status == "accepted":
                by_flag.setdefault(f.flag_id, []).append(f)
        for flag, fs in by_flag.items():
            try:
                sql = render(load_sql(flag), agency=req.agency, date_from=req.date_from, date_to=req.date_to)
                r = deps.sql(sql)
                qids.append(r.query_id)
                again = {_row_key(d) for d in r.dicts()}
            except Exception as e:
                for f in fs:
                    critiques.append(Critique(finding_id=f.finding_id, verdict="revise", target="AnalystAgent", reason=f"re-check failed: {e}"))
                revise_checks.append(flag)
                continue
            for f in fs:
                row = f.evidence[0].rows[0] if f.evidence and f.evidence[0].rows else {}
                if _row_key(row) in again:
                    f.evidence.append(f.evidence[0].model_copy(update={"query_id": r.query_id, "rows": [row], "row_count": len(again)}))
                    f.notes.append(f"Critic re-ran the SQL (query {r.query_id}) and confirmed the cited row.")
                else:
                    critiques.append(Critique(finding_id=f.finding_id, verdict="revise", target="AnalystAgent",
                                              reason="cited row not reproduced by a fresh run of the SQL"))
                    if flag not in revise_checks:
                        revise_checks.append(flag)

        # 2. weak resolver matches
        for f in findings:
            if f.status != "accepted" or f.flag_id not in MATCH_DEPENDENT:
                continue
            if f.confidence < deps.match_threshold:
                if resolver_retry < deps.max_retries and f.supplier_name not in redo_names:
                    redo_names.append(f.supplier_name)
                    critiques.append(Critique(finding_id=f.finding_id, verdict="revise", target="ResolverAgent",
                                              reason=f"match confidence {f.confidence:.2f} below {deps.match_threshold}"))
                else:
                    f.status = "rejected"
                    f.notes.append(f"Rejected: supplier match confidence {f.confidence:.2f} stayed below {deps.match_threshold} after retries.")
                    critiques.append(Critique(finding_id=f.finding_id, verdict="reject", reason="low-confidence supplier match"))

        # 3. H-MEM recall
        if deps.hmem:
            for f in findings:
                if f.status != "accepted":
                    continue
                try:
                    mems = deps.hmem.recall(agency=f.agency, uen=f.uen, flag_id=f.flag_id,
                                            query=f"{f.flag_id} {f.supplier_name} {f.agency}")
                except Exception:
                    continue
                for m in mems:
                    meta = m.get("meta") or {}
                    exact = meta.get("uen") == f.uen and meta.get("flag_id") == f.flag_id and meta.get("agency") == f.agency
                    if exact and meta.get("decision") == "dismiss" and f.uen:
                        f.status = "suppressed"
                        f.memory_refs.append(m["id"])
                        memory_refs.append(m["id"])
                        f.notes.append(f"Suppressed: auditor dismissed this exact case before ({m.get('content', '')[:120]}).")
                        critiques.append(Critique(finding_id=f.finding_id, verdict="suppress", reason=f"H-MEM {m['id']}"))
                        try:
                            deps.hmem.feedback(m["id"], "helpful", state["run_id"])
                        except Exception:
                            pass
                        break
                    if meta.get("pattern_tag") and meta.get("decision") == "dismiss" and (meta.get("agency") == f.agency or meta.get("scope") == "global"):
                        f.confidence = round(f.confidence * 0.7, 3)
                        f.memory_refs.append(m["id"])
                        memory_refs.append(m["id"])
                        f.notes.append(f"Confidence down-weighted: similar pattern dismissed at this agency (memory {m['id']}).")

        # 4. claim support check (fast lane, one batched call, only for still-accepted findings)
        live = [f for f in findings if f.status == "accepted" and not any(c.finding_id == f.finding_id for c in critiques)]
        receipt_res = None
        if live:
            # Small batches: one big call makes Nemotron generate long enough that Nightshift aborts it (HTTP 499).
            pending = live[:15]
            for i in range(0, len(pending), CLAIM_BATCH):
                chunk = pending[i:i + CLAIM_BATCH]
                try:
                    batch = [{**compact_finding(f), "summary": facts_only(f.summary), "evidence_rows": f.evidence[0].rows[:1]} for f in chunk]
                    res = deps.llm("fast", [
                        {"role": "system", "content": "You are a strict verifier. For each finding decide whether the facts in its summary (names, tender number, agency, amount, date, "
                         "metric values) agree with its evidence_rows. A summary is supported unless it states a fact that contradicts or is absent from the rows. "
                         "Do not judge whether the finding is a real problem, and do not object to tone. Keep each reason under 15 words."},
                        {"role": "user", "content": dumps({"findings": batch, "answer_format": {"checks": [{"finding_id": "...", "supported": True, "reason": "short"}]}})},
                    ], json_schema=ClaimChecks, max_tokens=2000)
                    receipt_res = res
                    for c in res.parsed.checks:
                        if not c.supported:
                            critiques.append(Critique(finding_id=c.finding_id, verdict="revise", target="AnalystAgent", reason=f"claim not supported: {c.reason}"))
                            fl = next((x.flag_id for x in live if x.finding_id == c.finding_id), None)
                            if fl and fl not in revise_checks:
                                revise_checks.append(fl)
                except Exception as e:
                    deps.tracer.emit(NAME, "claim_support_check", input=f"findings {i + 1}-{i + len(chunk)} of {len(pending)}",
                                     output=f"skipped: {type(e).__name__}: {str(e)[:150]}", status="partial_success")

        # bounded loops: flags over the retry limit are given up on, not looped
        give_up = [fl for fl in revise_checks if retries.get(fl, 0) >= deps.max_retries]
        for fl in give_up:
            revise_checks.remove(fl)
            for f in findings:
                for c in critiques:
                    if c.finding_id != f.finding_id or c.verdict != "revise" or c.target != "AnalystAgent" or f.flag_id != fl:
                        continue
                    if c.reason.startswith("claim not supported"):  # rows exist, wording disputed: a human decides
                        f.status = "escalated"
                        f.notes.append(f"Escalated to human review: Critic could not verify the summary against its rows ({c.reason[:140]}).")
                    else:
                        f.status = "rejected"
                        f.notes.append("Rejected by Critic: evidence could not be reproduced after retries.")

        if revise_checks:
            route, status = "analyst", "needs_revision"
        elif redo_names:
            route, status = "resolver", "needs_revision"
        else:
            route, status = "risk", "success"
        n_bad = len([c for c in critiques if c.verdict != "ok"])
        out = dict(input=f"{len(findings)} findings", output=f"{n_bad} issues; route={route}; revise={revise_checks} re-resolve={redo_names}; "
                   f"{'; '.join(c.reason for c in critiques[:3])}", target={"analyst": "AnalystAgent", "resolver": "ResolverAgent", "risk": "RiskAgent"}[route],
                   status=status, retry=max(retries.values(), default=0), query_ids=qids)
        if receipt_res:
            deps.tracer.llm(NAME, "validate_claims", receipt_res, **out)
        else:
            deps.tracer.emit(NAME, "validate_claims", **out)
        return {"findings": findings, "critiques": critiques, "revise_checks": revise_checks, "resolver_names": redo_names,
                "resolver_retry": resolver_retry + (1 if redo_names else 0), "route": route, "memory_refs": memory_refs}

    return critic
