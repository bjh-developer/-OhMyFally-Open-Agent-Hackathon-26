#!/usr/bin/env python3
"""Smoke test: Zetaris REST + Nightshift deep lane + Nightshift fast lane.

    python scripts/smoke_test.py

Exit code 0 only if all 3 checks pass. Stdlib only; secrets come from .env and
are never printed.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zsql import load_env, run_sql  # noqa: E402


def check_zetaris(env: dict) -> str:
    res = run_sql("SELECT 1 AS ok", env=env, limit=1, timeout=30)
    assert res["data"] == [["1"]], f"unexpected result {res.get('data')}"
    return f"SELECT 1 -> {res['data']} ({res.get('timeUsed')} ms, query_id={res['query_id']})"


def check_lane(env: dict, lane: str) -> str:
    app = env[f"METERLESS_APP_{lane.upper()}"]
    model = env[f"METERLESS_MODEL_{lane.upper()}"]
    body = {"model": model, "max_tokens": 1500, "messages": [{"role": "user", "content": "Reply with the single word: pong"}]}
    req = urllib.request.Request(
        env["METERLESS_BASE_URL"].rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {env['METERLESS_RUNTIME_TOKEN']}",
            "meterless-app": app,
            "meterless-scope": "user",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            out = json.load(resp)
    except urllib.error.HTTPError as e:
        raise AssertionError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}")
    content = (out["choices"][0]["message"].get("content") or "").strip()
    rcpt = out.get("meterless") or {}
    assert rcpt.get("receipt_id"), "no meterless receipt in response"
    assert content, "empty completion"
    return f"app={app} routed_model={rcpt.get('routed_model')} receipt={rcpt['receipt_id']} {time.time() - t:.1f}s reply={content[:40]!r}"


def main() -> int:
    env = load_env()
    checks = [
        ("zetaris REST SELECT", lambda: check_zetaris(env)),
        ("nightshift deep lane", lambda: check_lane(env, "deep")),
        ("nightshift fast lane", lambda: check_lane(env, "fast")),
    ]
    passed = 0
    for name, fn in checks:
        try:
            print(f"PASS  {name}: {fn()}")
            passed += 1
        except (AssertionError, KeyError, SystemExit, urllib.error.URLError, TimeoutError) as e:
            print(f"FAIL  {name}: {e!r}")
    print(f"{passed}/{len(checks)} passed")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
