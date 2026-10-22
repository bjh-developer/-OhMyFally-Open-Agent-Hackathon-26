"""Builds the production Deps (live Zetaris, Nightshift, optional resolver and H-MEM)."""
from __future__ import annotations

import importlib
import logging

from ..tracing import Tracer
from .state import Deps

log = logging.getLogger("pi.factory")


_INDEX = None
_STRATEGY_LAYERS = {
    "default": ("exact", "former_name", "fuzzy", "llm_tiebreak"),
    "fuzzy": ("exact", "former_name", "fuzzy"),            # Critic retry 1: stop at fuzzy matching
    "llm_tiebreak": ("exact", "former_name", "fuzzy", "llm_tiebreak"),  # Critic retry 2: add the fast-lane tie-break
}


def resolver_adapter():
    """Wraps app/resolver ``resolve(names, index, strategies, tiebreak)`` as ``resolve(names, strategy)``."""
    match = importlib.import_module("app.resolver.match")
    entities = importlib.import_module("app.resolver.entities")

    def resolve(names, strategy: str = "default"):
        global _INDEX
        if _INDEX is None:
            _INDEX = entities.EntityIndex.from_zetaris()
        tb = None
        if "llm_tiebreak" in _STRATEGY_LAYERS.get(strategy, ()):
            tb = importlib.import_module("app.resolver.llm").nightshift_tiebreak
        return match.resolve(list(names), _INDEX, strategies=_STRATEGY_LAYERS.get(strategy, _STRATEGY_LAYERS["default"]), tiebreak=tb)

    return resolve


def make_deps(tracer: Tracer | None = None, **overrides) -> Deps:
    d = Deps(tracer=tracer or Tracer(), **overrides)
    if d.resolve is None:  # stream B's resolver, wired in when present
        try:
            d.resolve = resolver_adapter()
        except Exception as e:
            log.warning("app.resolver not available (%s); Resolver agent reads supplier_xwalk only", type(e).__name__)
    if d.hmem is None:
        try:
            d.hmem = importlib.import_module("app.adapters.hmem_client").HMemClient()
        except Exception:
            pass
    return d
