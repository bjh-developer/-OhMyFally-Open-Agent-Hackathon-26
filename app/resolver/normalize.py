"""Supplier / company name normalisation shared by the fetch scripts and the Resolver."""
from __future__ import annotations

import re

# Dropped from the normalised key: legal-form noise.
DROP_TOKENS = {"PTE", "LTD", "PRIVATE", "LIMITED", "LLP", "LP"}
# A name ending in one of these looks locally registered (R8 relevance, out_of_scope split).
LOCAL_SUFFIX_RE = re.compile(r"\b(PTE\.?\s*LTD\.?|PRIVATE\s+LIMITED|LLP|L\.L\.P\.?|LP)\s*\)?\s*$")
_PUNCT_RE = re.compile(r"[^A-Z0-9 ]")
_WS_RE = re.compile(r"\s+")


def normalize(name: str | None) -> str:
    """Upper-case, '&' -> AND, strip punctuation, drop PTE/LTD/PRIVATE/LIMITED/LLP tokens."""
    if not name:
        return ""
    s = str(name).upper().replace("&", " AND ")
    s = _PUNCT_RE.sub(" ", s)
    toks = [t for t in _WS_RE.split(s) if t and t not in DROP_TOKENS]
    return " ".join(toks)


def tokens(name: str | None) -> list[str]:
    n = normalize(name)
    return n.split() if n else []


def blocking_keys(name: str | None) -> tuple[str, str]:
    """(first token, first two tokens) of the normalised name; '' when absent."""
    t = tokens(name)
    return (t[0] if t else "", " ".join(t[:2]) if t else "")


def has_local_suffix(name: str | None) -> bool:
    if not name:
        return False
    s = str(name).upper().strip()
    s = re.sub(r"\s+", " ", s)
    return bool(LOCAL_SUFFIX_RE.search(s))
