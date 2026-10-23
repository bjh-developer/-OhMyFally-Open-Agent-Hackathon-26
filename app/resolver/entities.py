"""ACRA entity index for the Resolver. Entities are read through Zetaris (ACRA_FILES.entities)."""
from __future__ import annotations

import json
import os
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from app.resolver.normalize import normalize

ROOT = Path(__file__).resolve().parents[2]
FORMER_COLS = [f"former_entity_name{i}" for i in range(1, 16)]
ENTITY_SQL = (
    "SELECT uen, entity_name, entity_type_description, entity_status_description, "
    "registration_incorporation_date, postal_code, " + ", ".join(FORMER_COLS) + " FROM ACRA_FILES.entities"
)
NA = {"", "NA", "N/A", "NIL", "NONE", "NULL"}


def _env() -> dict[str, str]:
    env = {}
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.split(" #")[0].strip().strip("\"'")
    env.update({k: v for k, v in os.environ.items() if k.startswith(("ZETARIS_", "METERLESS_"))})
    return env


def zetaris_query(sql: str, limit: int = 100000, timeout: float = 170.0) -> tuple[list[str], list[list], str]:
    """One statement through Zetaris REST. Returns (headers, rows-as-strings, query_id).

    Goes through the adapter so replay mode (SAMPLE_MODE + recorded set, Zetaris down) can answer it."""
    from app.adapters.zetaris import run_sql

    r = run_sql(sql, limit=limit, timeout=timeout, retries=0)
    return r.headers, r.rows, r.query_id


@dataclass
class Entity:
    uen: str
    name: str
    etype: str
    status: str
    incorporated: str
    postal: str
    formers: list[str] = field(default_factory=list)

    @property
    def live(self) -> bool:
        return self.status.upper().startswith("LIVE")

    def brief(self, matched_on: str = "") -> dict:
        return {"uen": self.uen, "entity_name": self.name, "status": self.status, "type": self.etype,
                "incorporated": self.incorporated, "matched_on": matched_on}


class EntityIndex:
    def __init__(self, entities: list[Entity]):
        self.entities = entities
        self.by_current: dict[str, list[int]] = defaultdict(list)
        self.by_former: dict[str, list[int]] = defaultdict(list)
        self.by_first: dict[str, list[tuple[int, str, str]]] = defaultdict(list)  # first token -> (idx, norm, source)
        for i, e in enumerate(entities):
            n = normalize(e.name)
            if n:
                self.by_current[n].append(i)
                self.by_first[n.split()[0]].append((i, n, "current"))
            for f in e.formers:
                fn = normalize(f)
                if fn:
                    self.by_former[fn].append(i)
                    self.by_first[fn.split()[0]].append((i, fn, "former"))

    @classmethod
    def from_zetaris(cls) -> "EntityIndex":
        headers, rows, _ = zetaris_query(ENTITY_SQL)
        ix = {h: i for i, h in enumerate(headers)}
        out = []
        for r in rows:
            formers = [r[ix[c]] for c in FORMER_COLS if r[ix[c]] and r[ix[c]].strip().upper() not in NA]
            out.append(Entity(r[ix["uen"]], r[ix["entity_name"]] or "", r[ix["entity_type_description"]] or "",
                              r[ix["entity_status_description"]] or "", r[ix["registration_incorporation_date"]] or "",
                              r[ix["postal_code"]] or "", formers))
        return cls(out)
