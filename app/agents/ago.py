"""Curated red flag -> AGO excerpt mapping (data/rules/ago_map.yaml). Deterministic: no search, no LLM."""
from __future__ import annotations

import csv
from functools import lru_cache

import yaml

from ..adapters.config import ROOT

MAP_PATH = ROOT / "data" / "rules" / "ago_map.yaml"
INDEX_PATH = ROOT / "data" / "ago" / "index.csv"
MAX_REFS = 2  # design-system §5: "Why this matters" is at most two sentences, so cite at most two excerpts


@lru_cache(maxsize=1)
def ago_map() -> dict[str, list[dict]]:
    return {k: (v or []) for k, v in (yaml.safe_load(MAP_PATH.read_text(encoding="utf-8")) or {}).items()}


@lru_cache(maxsize=1)
def ago_index() -> dict[str, dict]:
    with INDEX_PATH.open(encoding="utf-8", newline="") as fh:
        return {r["chunk_id"]: r for r in csv.DictReader(fh)}


def refs_for(flag_id: str) -> list[str]:
    """Chunk ids to attach to a finding of this flag; empty when no excerpt fits."""
    idx = ago_index()
    return [e["chunk_id"] for e in ago_map().get(flag_id, []) if e["chunk_id"] in idx][:MAX_REFS]


def why_line(flag_id: str) -> str | None:
    """One markdown line for the memo, or None when the flag has no mapped excerpt."""
    refs = refs_for(flag_id)
    if not refs:
        return None
    by_id = {e["chunk_id"]: e for e in ago_map()[flag_id]}
    idx = ago_index()
    e, c = by_id[refs[0]], idx[refs[0]]
    return f"- Why it matters: {e['rationale']} ([AGO {c['fy']}, p. {c['page']}]({c['url']}))"
