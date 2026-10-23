"""Critic (fast lane): verifies every finding before it can reach the memo.

1. Re-runs the check SQL (fresh Zetaris query_id) and confirms each cited row still exists.
2. Rejects Resolver matches under the threshold -> back to the Resolver with a different strategy.
3. Queries H-MEM: an exact dismiss memory suppresses the finding; the same pattern down-weights it.
4. R3 address density: how many ACRA entities share each flagged address? Busy commercial addresses are down-weighted,
   quiet or unit-less ones are escalated to a human.
5. One batched fast-lane call: is each summary supported by its evidence rows?
Also hosts the plan review (``make_plan_review``): the Planner's plan against what the data can actually support.
Loops are bounded by ``deps.max_retries``.
"""
from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from ..adapters.config import ROOT
from ..checks.rules import red_flags
from ..checks.runner import MATCH_DEPENDENT, available_checks, facts_only, load_sql, render
from ..orchestration.state import Deps, RunState
from ..schemas import Critique, Finding
from .common import compact_finding, dumps, parallel_map

NAME = "CriticAgent"


class ClaimCheck(BaseModel):
    finding_id: str
    supported: bool
    reason: str = ""


class ClaimChecks(BaseModel):
    checks: list[ClaimCheck]


CLAIM_BATCH = 5  # findings per fast-lane claim check
PARALLEL = 3  # concurrent Nightshift calls per agent

CRITIC_SQL = ROOT / "sql" / "critic"
_UEN = re.compile(r"^[A-Za-z0-9]{8,12}$")
_NO_VALUE = {"", "NA", "N/A", "NULL", "NONE", "-"}
DENSITY_MARK = "Address check:"


def _density_cfg() -> dict:
    return {"busy_min_entities": 25, "busy_confidence_cap": 0.72, **(red_flags().get("R3", {}).get("address_density") or {})}


def _blank(v: Any) -> bool:
    return v is None or str(v).strip().upper() in _NO_VALUE


def _address_density(findings: list[Finding], deps: Deps) -> tuple[list[str], int]:
    """R3 critique. Mutates accepted R3 findings; emits one trace line per shared-address group.
    Returns (zetaris query ids, number of groups changed)."""
    cfg = _density_cfg()
    todo = [f for f in findings if f.flag_id == "R3" and f.status == "accepted" and f.uen and _UEN.match(f.uen)
            and not any(n.startswith(DENSITY_MARK) for n in f.notes)]
    if not todo:
        return [], 0
    groups: dict[str, list[Finding]] = {}
    for f in todo:
        groups.setdefault(f.detail or f.finding_id, []).append(f)
    uens = sorted({f.uen for f in todo})
    sql = (CRITIC_SQL / "R3_address_density.sql").read_text().replace("{{uens}}", ", ".join(f"'{u}'" for u in uens)).strip().rstrip(";")
    try:
        res = deps.sql(sql)
    except Exception as e:
        deps.tracer.emit(NAME, "address_density", input=f"{len(groups)} shared-address groups", output=f"skipped: {type(e).__name__}: {str(e)[:150]}",
                         status="partial_success")
        return [], 0
    info = {d["uen"]: d for d in res.dicts()}
    changed = 0
    for key, fs in groups.items():
        rows = [info[f.uen] for f in fs if f.uen in info]
        if not rows:
            continue
        n = max(int(float(r.get("n_entities") or 0)) for r in rows)
        no_unit = any(_blank(r.get("level_no")) or _blank(r.get("unit_no")) for r in rows)
        suppliers = sorted({f.supplier_name for f in fs})
        label = key.split("address ", 1)[-1].split(". ")[0] if "address " in key else f"{len(suppliers)} suppliers"
        if no_unit:
            decision, status = "escalate", "escalated"
            reason = "level and unit are missing, so a shared address cannot be told apart from a shared building"
            note = f"{DENSITY_MARK} level/unit missing ({n} entities at the block); escalated to human review."
        elif n >= cfg["busy_min_entities"]:
            decision, status = "downgrade", "needs_revision"
            reason = f"{n} entities are registered at this block, street and postal code"
            note = f"{DENSITY_MARK} Many businesses are registered at this address ({n} entities), so the match is probably benign; confidence lowered."
        else:
            decision, status = "escalate", "escalated"
            reason = f"only {n} entities at this address, so the shared unit is ambiguous"
            note = f"{DENSITY_MARK} quiet address ({n} entities) with the same unit shared; escalated to human review."
        for f in fs:
            f.notes.append(note)
            if decision == "downgrade":
                f.confidence = round(min(f.confidence, float(cfg["busy_confidence_cap"])), 3)
            else:
                f.status = "escalated"
                f.notes.append("Escalated to human review: " + reason + ".")
        changed += 1
        deps.tracer.emit(NAME, "address_density", input=f"{label} ({len(suppliers)} suppliers, {len(fs)} awards)",
                         output=f"{decision}: {reason}", target="RiskAgent", status=status,
                         query_ids=[res.query_id], confidence=fs[0].confidence)
    return [res.query_id], changed


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
        mem_seen: list[str] = []

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
            # R5's finding confidence expresses semantic uncertainty, not a weak identity match.
            match_confidence = f.confidence
            if f.flag_id == "R5":
                match = matches.get(f.supplier_name)
                match_confidence = match.confidence if match and match.uen == f.uen else 0.0
            if match_confidence < deps.match_threshold:
                if resolver_retry < deps.max_retries and f.supplier_name not in redo_names:
                    redo_names.append(f.supplier_name)
                    critiques.append(Critique(finding_id=f.finding_id, verdict="revise", target="ResolverAgent",
                                              reason=f"match confidence {match_confidence:.2f} below {deps.match_threshold}"))
                else:
                    f.status = "rejected"
                    f.notes.append(f"Rejected: supplier match confidence {match_confidence:.2f} stayed below {deps.match_threshold} after retries.")
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
                    if m.get("id") and m["id"] not in mem_seen:
                        mem_seen.append(m["id"])
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

        # 4. R3 address density
        dq, n_density = _address_density(findings, deps)
        qids += dq

        # 5. claim support check (fast lane, one batched call, only for still-accepted findings)
        live = [f for f in findings if f.status == "accepted" and not any(c.finding_id == f.finding_id for c in critiques)]
        receipt_res = None
        if live:
            # Small batches: one big call makes Nemotron generate long enough that Nightshift aborts it (HTTP 499).
            pending = live[:15]
            chunks = [pending[i:i + CLAIM_BATCH] for i in range(0, len(pending), CLAIM_BATCH)]

            def check(chunk: list) -> Any:
                batch = [{**compact_finding(f), "summary": facts_only(f.summary), "evidence_rows": f.evidence[0].rows[:1]} for f in chunk]
                return deps.llm("fast", [
                    {"role": "system", "content": "You are a strict verifier. For each finding decide whether the facts in its summary (names, tender number, agency, amount, date, "
                     "metric values) agree with its evidence_rows. A summary is supported unless it states a fact that contradicts or is absent from the rows. "
                     "Do not judge whether the finding is a real problem, and do not object to tone. Keep each reason under 15 words."},
                    {"role": "user", "content": dumps({"findings": batch, "answer_format": {"checks": [{"finding_id": "...", "supported": True, "reason": "short"}]}})},
                ], json_schema=ClaimChecks, max_tokens=2000)

            # Batches run in parallel: one big call ran long enough for Nightshift to abort it (HTTP 499), and serial batches were slow.
            for chunk, res in zip(chunks, parallel_map(check, chunks, max_workers=PARALLEL)):
                if isinstance(res, BaseException):
                    start = pending.index(chunk[0]) + 1
                    deps.tracer.emit(NAME, "claim_support_check", input=f"findings {start}-{start + len(chunk) - 1} of {len(pending)}",
                                     output=f"skipped: {type(res).__name__}: {str(res)[:150]}", status="partial_success")
                    continue
                receipt_res = res
                for c in res.parsed.checks:
                    if not c.supported:
                        critiques.append(Critique(finding_id=c.finding_id, verdict="revise", target="AnalystAgent", reason=f"claim not supported: {c.reason}"))
                        fl = next((x.flag_id for x in live if x.finding_id == c.finding_id), None)
                        if fl and fl not in revise_checks:
                            revise_checks.append(fl)

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

        applied = [m for m in dict.fromkeys(memory_refs) if m in mem_seen]
        if revise_checks:
            route, status = "analyst", "needs_revision"
        elif redo_names:
            route, status = "resolver", "needs_revision"
        else:
            route, status = "risk", "success"
        n_bad = len([c for c in critiques if c.verdict != "ok"]) + n_density
        out = dict(input=f"{len(findings)} findings", output=f"{n_bad} issues; route={route}; revise={revise_checks} re-resolve={redo_names}; "
                   f"{'; '.join(c.reason for c in critiques[:3])}", target={"analyst": "AnalystAgent", "resolver": "ResolverAgent", "risk": "RiskAgent"}[route],
                   status=status, retry=max(retries.values(), default=0), query_ids=qids)
        if deps.hmem:
            out["memory_hits"], out["memory_ids"] = len(mem_seen), mem_seen
            out["output"] += f"; used {len(applied)} past decision{'s' if len(applied) != 1 else ''} (recalled {len(mem_seen)})"
        if receipt_res:
            deps.tracer.llm(NAME, "validate_claims", receipt_res, **out)
        else:
            deps.tracer.emit(NAME, "validate_claims", **out)
        return {"findings": findings, "critiques": critiques, "revise_checks": revise_checks, "resolver_names": redo_names,
                "resolver_retry": resolver_retry + (1 if redo_names else 0), "route": route, "memory_refs": memory_refs}

    return critic


def make_plan_review(deps: Deps):
    """Plan critique: judge the Planner's plan against what the data can support.

    A fixable gap (a must-have check missing, R8 unplanned while names are unresolved) sends the run back to the Planner
    (bounded by ``deps.max_replans``). Anything else is recorded as a limitation for the memo.
    """

    def plan_review(state: RunState) -> dict:
        req, plan = state["request"], state["plan"]
        if state.get("plan_reviewed") == plan.replan_count:  # Critic -> Resolver retries pass through here again: review once per plan
            return {}
        matches = state.get("matches") or {}
        have = set(available_checks())
        limits: list[str] = []
        qids: list[str] = []
        try:
            res = deps.sql(render((CRITIC_SQL / "plan_coverage.sql").read_text(), agency=req.agency, date_from=req.date_from, date_to=req.date_to))
            qids.append(res.query_id)
            c = res.dicts()[0]
            n_all, n_period, n_etq = (int(float(c.get(k) or 0)) for k in ("n_all", "n_period", "n_etq"))
            lo, hi = c.get("min_date"), c.get("max_date")
            if n_all == 0:
                limits.append(f"No GeBIZ awards are held for {req.agency}, so no check can find anything.")
            elif n_period == 0:
                limits.append(f"The period {req.date_from}..{req.date_to} is outside the data range for this agency ({lo}..{hi}); nothing to check.")
            elif lo and hi and (str(req.date_from) < lo[:10] or str(req.date_to) > hi[:10]):
                limits.append(f"Part of the period lies outside the data range for this agency ({lo[:10]}..{hi[:10]}); results cover {n_period} awards.")
            if "R4" in plan.checks and n_etq == 0:
                limits.append("R4 is partial: GeBIZ holds 0 quotation (ETQ) records, so splitting below the tender threshold cannot be seen.")
        except Exception as e:
            limits.append(f"Plan coverage could not be checked ({type(e).__name__}).")

        required: list[str] = []
        asked = set(req.flags)
        for fid, meta in red_flags().items():
            if meta.get("priority") == "must" and fid in have and fid not in plan.checks and (not asked or fid in asked):
                required.append(fid)
        unresolved = [m for m in matches.values() if m.method == "unresolved"]
        need = int((red_flags().get("R8", {}).get("plan_critique") or {}).get("unresolved_min", 5))
        if "R8" in have and "R8" not in plan.checks and "R8" not in required and unresolved and len(unresolved) >= need and (not asked or "R8" in asked):
            required.append("R8")
        elif "R8" in plan.checks and unresolved:
            limits.append(f"{len(unresolved)} supplier names could not be matched to ACRA; R8 lists them for manual lookup.")

        replan = bool(required) and plan.replan_count < deps.max_replans
        if required and not replan:
            limits.append(f"Checks {required} were wanted but not planned (replan budget used).")
        notes = f"Add {required} to the plan: " + ("missing must-have checks" if any(r != "R8" for r in required) else f"{len(unresolved)} unresolved supplier names make R8 worth running") if replan else ""
        verdict = "replan" if replan else ("limitations" if limits else "plan ok")
        deps.tracer.emit(NAME, "plan_review", input=f"plan {plan.checks}; {len(matches)} matches, {len(unresolved)} unresolved",
                         output=f"{verdict}: " + (notes if replan else "; ".join(limits) or "plan matches data coverage"),
                         target="PlannerAgent" if replan else "AnalystAgent", retry=plan.replan_count,
                         status="needs_revision" if replan else ("partial_success" if limits else "success"), query_ids=qids)
        return {"plan_reviewed": plan.replan_count, "replan_requested": replan, "replan_required": required if replan else [], "replan_notes": notes, "plan_limitations": limits}

    return plan_review
