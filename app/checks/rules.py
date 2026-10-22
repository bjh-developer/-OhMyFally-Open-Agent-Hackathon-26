"""Loads rule metadata (red_flags.yaml, wording.yaml) with safe fallbacks to CONTRACTS section 9."""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

from ..adapters.config import ROOT

RULES_DIR = ROOT / "data" / "rules"

# CONTRACTS section 9; used only when data/rules/red_flags.yaml is absent.
DEFAULT_FLAGS = {
    "R1": ("Supplier incorporated shortly before award", "must"),
    "R2": ("Supplier no longer live in ACRA", "must"),
    "R3": ("Winning suppliers share an address", "must"),
    "R4": ("Possible contract splitting", "must"),
    "R8": ("No ACRA match for a locally named supplier", "must"),
    "R5": ("Supplier line of business far from tender", "should"),
    "R6": ("Supplier concentration within a category", "should"),
    "R9": ("Winner not best-scored under published criteria", "should"),
    "R7": ("Supplier has former names", "stretch"),
}


@lru_cache(maxsize=1)
def red_flags() -> dict[str, dict]:
    p = RULES_DIR / "red_flags.yaml"
    out = {fid: {"flag_id": fid, "name": n, "priority": pr, "limitation": "", "why_it_matters": ""} for fid, (n, pr) in DEFAULT_FLAGS.items()}
    if p.exists():
        for e in yaml.safe_load(p.read_text()) or []:
            out[e["flag_id"]] = {**out.get(e["flag_id"], {}), **e}
    return out


@lru_cache(maxsize=1)
def wording() -> dict:
    return yaml.safe_load((RULES_DIR / "wording.yaml").read_text())


def banned_hits(text: str) -> list[str]:
    hits = []
    for term in wording().get("banned_terms", []):
        if re.search(rf"\b{re.escape(term)}\w*", text or "", re.I):
            hits.append(term)
    return hits


def sanitise(text: str) -> str:
    """Deterministic fallback: replace banned terms using wording.yaml replacements (longest first)."""
    reps = wording().get("replacements", {})
    for term in sorted(reps, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(term)}\b", reps[term], text, flags=re.I)
    return text
