"""Entity Resolver: GeBIZ supplier_name -> ACRA UEN (CONTRACTS §7.2 supplier_xwalk, §7.4 Match).

Pass 1 (deterministic, runs BEFORE R1):  exact  ->  former_name
Pass 2 (after the checks exist):         fuzzy (rapidfuzz)  ->  llm_tiebreak (fast Nightshift lane)  ->  unresolved | out_of_scope

resolve(names, strategies=...) lets the Resolver agent retry with a different strategy when the Critic
rejects a match. Every Match records `method`, `confidence` and the `candidates` considered.
"""
from __future__ import annotations

import json
import re
from typing import Callable, Iterable, Sequence

from rapidfuzz import fuzz

from app.resolver.entities import Entity, EntityIndex
from app.resolver.normalize import has_local_suffix, normalize

from app.schemas import Match  # pydantic model (CONTRACTS §7.4); build with keywords only


def M(name: str, uen: str | None, conf: float, method: str, cands: list[dict] | None = None) -> Match:
    return Match(supplier_name=name, uen=uen, confidence=conf, method=method, candidates=cands or [])

FUZZY_MATCH = 92.0
FUZZY_AMBIGUOUS = 80.0
LLM_BATCH = 8  # spec says ~20; 10 keeps each fast-lane call well under the 180 s timeout
LLM_MAX_CONF = 0.85
STRATEGIES = ("exact", "former_name", "fuzzy", "llm_tiebreak")
PLACEHOLDER_NAMES = {"UNKNOWN", "NIL", "NA", "N A", "NONE", "TBC", "TBA", ""}

LLM_ERRORS: list[str] = []
TieBreak = Callable[[list[dict]], dict[str, dict]]


def _compatible(supplier_name: str, e: Entity) -> bool:
    """Legal-form sanity: 'XYZ LLP' should not resolve to 'XYZ' the company, and vice versa."""
    s = supplier_name.upper()
    if re.search(r"\bLLP\b|LIMITED LIABILITY PARTNERSHIP", s):
        return "LIMITED LIABILITY" in e.etype.upper()
    if has_local_suffix(supplier_name):
        return "LIMITED LIABILITY" not in e.etype.upper() or bool(re.search(r"\bLP\b", s))
    return True


def _pick(idxs: list[int], index: EntityIndex, supplier_name: str) -> tuple[list[Entity], Entity | None]:
    """Candidates after the legal-form filter, and the single winner if one is clearly best."""
    cands = [index.entities[i] for i in idxs]
    ok = [e for e in cands if _compatible(supplier_name, e)]
    if len(ok) == 1:
        return ok, ok[0]
    live = [e for e in ok if e.live]
    if len(live) == 1:
        return ok, live[0]
    return ok, None


def _pass1_one(name: str, index: EntityIndex) -> Match | None:
    n = normalize(name)
    if not n or n in PLACEHOLDER_NAMES:
        return None
    for method, table, base in (("exact", index.by_current, 1.0), ("former_name", index.by_former, 0.9)):
        idxs = table.get(n)
        if not idxs:
            continue
        ok, winner = _pick(idxs, index, name)
        if not ok:
            continue  # Same spelling cannot override a conflicting legal form.
        cands = [e.brief(method) for e in ok]
        if winner is not None:
            conf = base if len(ok) == 1 else base - 0.05
            return M(name, winner.uen, round(conf, 3), method, cands)
        # several live entities share this normalised name: leave for the tie-break
        return M(name, None, 0.0, "unresolved", cands)
    return None


def pass1(names: Iterable[str], index: EntityIndex) -> list[Match]:
    """Deterministic layers only. Names not resolved here come back with method 'unresolved'."""
    return [(_pass1_one(n, index) or M(n, None, 0.0, "unresolved", [])) for n in names]


def _fuzzy_candidates(name: str, index: EntityIndex, top: int = 3) -> list[tuple[float, Entity, str]]:
    n = normalize(name)
    if not n:
        return []
    toks = set(n.split())
    first = n.split()[0]
    best: dict[int, tuple[float, str]] = {}
    for idx, variant, src in index.by_first.get(first, []):
        score = fuzz.token_set_ratio(n, variant)
        vt = set(variant.split())
        if score >= 100 and vt != toks and abs(len(vt) - len(toks)) >= 1:
            score = 91.0  # subset of tokens is not the same name ('ABC' vs 'ABC CONSTRUCTION')
        if idx not in best or score > best[idx][0]:
            best[idx] = (score, src)
    ranked = sorted(((s, index.entities[i], src) for i, (s, src) in best.items()), key=lambda t: -t[0])
    return ranked[:top]


def _fuzzy_one(name: str, index: EntityIndex) -> tuple[Match | None, list[dict]]:
    ranked = [(s, e, src) for s, e, src in _fuzzy_candidates(name, index) if _compatible(name, e)]
    cands = [{**e.brief(f"fuzzy:{src}"), "score": round(s, 1)} for s, e, src in ranked]
    if not ranked or ranked[0][0] < FUZZY_AMBIGUOUS:
        return None, cands
    top = ranked[0]
    clear = len(ranked) == 1 or top[0] - ranked[1][0] >= 3 or ranked[1][1].uen == top[1].uen
    if top[0] >= FUZZY_MATCH and clear:
        return M(name, top[1].uen, round(top[0] / 100.0, 3), "fuzzy", cands), cands
    return None, cands  # ambiguous: 80-92 or a near-tie at the top


def _llm_batch(items: list[dict], tiebreak: TieBreak) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i in range(0, len(items), LLM_BATCH):
        try:
            out.update(tiebreak(items[i:i + LLM_BATCH]))
        except Exception as e:  # noqa: BLE001 - an LLM outage must not lose the deterministic results
            LLM_ERRORS.append(f"batch {i // LLM_BATCH}: {e}")
    return out


def _finish(name: str) -> str:
    return "unresolved" if has_local_suffix(name) else "out_of_scope"


def resolve(names: Sequence[str], index: EntityIndex, strategies: Sequence[str] = STRATEGIES,
            tiebreak: TieBreak | None = None, cache_pass1: dict[str, Match] | None = None) -> list[Match]:
    """Resolve each name through the requested layers, in order. Returns one Match per input, same order."""
    results: dict[str, Match] = {}
    pending: list[str] = []
    for name in dict.fromkeys(names):
        m = (cache_pass1 or {}).get(name)
        if m is None and ("exact" in strategies or "former_name" in strategies):
            m = _pass1_one(name, index)
            if m is not None and m.method == "exact" and "exact" not in strategies:
                m = None
            if m is not None and m.method == "former_name" and "former_name" not in strategies:
                m = None
        if m is not None and m.uen:
            results[name] = m
        else:
            pending.append(name)
            if m is not None:
                results[name] = m  # keep ambiguous candidates for the tie-break
    to_llm: list[dict] = []
    for name in pending:
        prior = results.get(name)
        cands = list(prior.candidates) if prior else []
        n = normalize(name)
        if not n or n in PLACEHOLDER_NAMES:
            results[name] = M(name, None, 0.0, "out_of_scope", [])
            continue
        if "fuzzy" in strategies:
            m, fc = _fuzzy_one(name, index)
            if m is not None:
                results[name] = m
                continue
            cands = (cands + fc)[:3] or fc
        # Privacy: names without a local legal suffix are mostly individuals/sole traders; never send those to an LLM
        # unless pass 1 already found several same-name entities.
        sendable = bool(prior and prior.candidates) or has_local_suffix(name)
        if "llm_tiebreak" in strategies and tiebreak is not None and cands and sendable:
            to_llm.append({"id": name, "name": name, "candidates": cands[:3]})
            results[name] = M(name, None, 0.0, _finish(name), cands)
        else:
            results[name] = M(name, None, 0.0, _finish(name), cands)
    if to_llm:
        answers = _llm_batch(to_llm, tiebreak)  # type: ignore[arg-type]
        for it in to_llm:
            ans = answers.get(it["id"])
            if ans and ans.get("uen") and any(c["uen"] == ans["uen"] for c in it["candidates"]):
                conf = min(float(ans.get("confidence", 0.7)), LLM_MAX_CONF)
                results[it["id"]] = M(it["id"], ans["uen"], round(conf, 3), "llm_tiebreak", it["candidates"])
    return [results[n] for n in names]
