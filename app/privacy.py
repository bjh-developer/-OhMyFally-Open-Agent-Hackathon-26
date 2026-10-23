"""Public-view pseudonymisation of supplier names (the `public` role of CONTRACTS section 7.2).

Zetaris (2.4.x, local) has no column masking: only table/namespace GRANTs, so masking is done here instead.
Each supplier maps to a stable alias ``Supplier-7F3A`` = first 4 hex of HMAC-SHA256(PSEUDONYM_KEY, normalised name).
The same name always gets the same alias (given the same key), so a reader can still see that two findings share
a supplier. Fictional planted suppliers (a standalone word ``TEST`` in the name) stay readable.

The key is required: with no PSEUDONYM_KEY the public view fails closed (``PseudonymKeyMissing``) rather than
falling back to an unkeyed hash that could be reversed by hashing candidate names.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

_TEST = re.compile(r"\bTEST\b", re.IGNORECASE)
_NAME_KEYS = ("supplier_name", "entity_name")  # a key equal to / ending in one of these holds a supplier name
_LIST_KEYS = ("suppliers",)


class PseudonymKeyMissing(RuntimeError):
    pass


def _key() -> bytes:
    k = os.getenv("PSEUDONYM_KEY", "").strip()
    if not k:
        raise PseudonymKeyMissing("PSEUDONYM_KEY is not set")
    return k.encode()


def _norm(name: str) -> str:
    return " ".join(name.upper().split())


def is_exempt(name: str) -> bool:
    return bool(_TEST.search(name))


def pseudonym(name: str, hex_len: int = 4) -> str:
    """Deterministic alias for one supplier name (case/space-insensitive)."""
    digest = hmac.new(_key(), _norm(name).encode(), hashlib.sha256).hexdigest()
    return "Supplier-" + digest[:hex_len].upper()


def _collect(node: Any, out: set[str]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str) and k.endswith(_NAME_KEYS):
                out.add(v)
            elif isinstance(v, list) and k in _LIST_KEYS:
                out.update(x for x in v if isinstance(x, str))
            _collect(v, out)
    elif isinstance(node, list):
        for v in node:
            _collect(v, out)


def _replace(node: Any, pattern: re.Pattern, alias: dict[str, str]) -> Any:
    if isinstance(node, str):
        return pattern.sub(lambda m: alias[_norm(m.group(0))], node)
    if isinstance(node, dict):
        return {k: _replace(v, pattern, alias) for k, v in node.items()}
    if isinstance(node, list):
        return [_replace(v, pattern, alias) for v in node]
    return node


def mask_payload(payload: Any) -> Any:
    """Return a copy of a JSON-able structure with every supplier name replaced by its alias.

    Names are discovered from the structure itself (``supplier_name`` / ``entity_name`` keys and ``suppliers``
    lists) and then replaced everywhere they occur as text: summary, markdown, details, notes, evidence SQL and
    rows. Longest names first so a name that contains another one is replaced whole.
    """
    found: set[str] = set()
    _collect(payload, found)
    names = sorted({n.strip() for n in found if n.strip() and not is_exempt(n)}, key=lambda n: (-len(n), n))
    if not names:
        return payload
    alias: dict[str, str] = {}
    for n in names:
        alias[_norm(n)] = pseudonym(n)
    # two different names sharing 4 hex digits: lengthen the later one so aliases stay unique within a payload
    seen: dict[str, str] = {}
    for n in sorted(names):
        a = alias[_norm(n)]
        if a in seen and seen[a] != _norm(n):
            a = pseudonym(n, 8)
            alias[_norm(n)] = a
        seen[a] = _norm(n)
    pattern = re.compile("|".join(re.escape(n) for n in names), re.IGNORECASE)
    return _replace(payload, pattern, alias)
