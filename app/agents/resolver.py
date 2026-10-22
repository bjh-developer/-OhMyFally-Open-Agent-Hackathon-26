"""Resolver agent: ensures every supplier in scope has a crosswalk match.

Reads ``supplier_xwalk`` (written by app/resolver), and calls ``resolve()`` for names that are missing or that
the Critic sent back with a different strategy.
"""
from __future__ import annotations

import inspect

from ..adapters.zetaris import to_float
from ..checks.runner import render
from ..orchestration.state import Deps, RunState
from ..schemas import Match

NAME = "ResolverAgent"
STRATEGIES = ["default", "fuzzy", "llm_tiebreak"]

NAMES_SQL = ("SELECT DISTINCT supplier_name FROM gebiz_pg.awards "
             "WHERE agency = {{agency}} AND award_date BETWEEN {{date_from}} AND {{date_to}}")
XWALK_SQL = ("SELECT x.supplier_name, x.uen, x.confidence, x.method FROM gebiz_pg.supplier_xwalk x "
             "WHERE x.supplier_name IN (SELECT DISTINCT supplier_name FROM gebiz_pg.awards "
             "WHERE agency = {{agency}} AND award_date BETWEEN {{date_from}} AND {{date_to}})")


def _call_resolve(fn, names: list[str], strategy: str) -> list[Match]:
    params = inspect.signature(fn).parameters
    return fn(names, strategy=strategy) if "strategy" in params else fn(names)


def make(deps: Deps):
    def resolver(state: RunState) -> dict:
        req = state["request"]
        retry = state.get("resolver_retry", 0)
        matches: dict[str, Match] = dict(state.get("matches") or {})
        redo = list(state.get("resolver_names") or [])
        strategy = "default" if not redo else STRATEGIES[min(retry, len(STRATEGIES) - 1)]
        qids: list[str] = []
        status, note = "success", ""
        try:
            kw = dict(agency=req.agency, date_from=req.date_from, date_to=req.date_to)
            r1 = deps.sql(render(NAMES_SQL, **kw)); qids.append(r1.query_id)
            names = [row[0] for row in r1.rows]
            r2 = deps.sql(render(XWALK_SQL, **kw)); qids.append(r2.query_id)
            for d in r2.dicts():
                matches[d["supplier_name"]] = Match(supplier_name=d["supplier_name"], uen=d["uen"] if d["uen"] not in ("", "null") else None,
                                                   confidence=to_float(d["confidence"]) or 0.0, method=d["method"] or "unresolved")
            todo = redo or [n for n in names if n not in matches]
            if todo and deps.resolve:
                for m in _call_resolve(deps.resolve, todo, strategy):
                    matches[m.supplier_name] = m
                note = f"resolve() on {len(todo)} names (strategy={strategy})"
            elif todo:
                note = f"{len(todo)} names without crosswalk rows and no resolver available"
                status = "partial_success"
        except Exception as e:
            status, note = "partial_success", f"resolver failed: {type(e).__name__}: {str(e)[:150]}"
        methods: dict[str, int] = {}
        for m in matches.values():
            methods[m.method] = methods.get(m.method, 0) + 1
        deps.tracer.emit(NAME, "resolve_suppliers", input=f"{len(redo) or 'all'} names, strategy={strategy}",
                         output=f"{len(matches)} matches {methods}. {note}", target="AnalystAgent", status=status,
                         retry=retry, query_ids=qids)
        return {"matches": matches, "resolver_names": [], "resolver_strategy": strategy}

    return resolver
