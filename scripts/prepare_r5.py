#!/usr/bin/env python
"""Prepare R5 semantic scores after seed/register/Resolver, without changing source records.

    python scripts/prepare_r5.py --download-model  # one-time local model setup, if Nightshift has no endpoint
    python scripts/prepare_r5.py                   # reuse cached model; never download implicitly

Reads descriptions through live Zetaris; the setup-only write updates existing rules.params in Postgres.
No agent reads planted ground truth. No identity names or addresses are sent for embedding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from app.checks.semantic import PAIRS_SQL, validate_scores

LOCAL_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def cosine(left, right) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("Embedding dimensions differ or are empty")
    left, right = [float(x) for x in left], [float(x) for x in right]
    if not all(math.isfinite(x) for x in left + right):
        raise ValueError("Non-finite embedding")
    norm = math.sqrt(sum(x*x for x in left) * sum(x*x for x in right))
    if not norm:
        raise ValueError("Zero-length embedding")
    return max(-1.0, min(1.0, sum(x*y for x, y in zip(left, right)) / norm))


def nightshift_embeddings(texts):
    import httpx
    from app.adapters.config import get_settings
    from app.adapters.nightshift import budget_scope, current_budget
    settings = get_settings()
    model = os.getenv("METERLESS_EMBEDDING_MODEL", settings.model_fast)
    headers = {"Authorization": f"Bearer {settings.meterless_token}",
               "meterless-app": settings.app_fast, "meterless-scope": "user"}
    vectors, receipts = [], []
    with budget_scope(40), httpx.Client(timeout=60) as client:
        for start in range(0, len(texts), 128):
            current_budget().take()
            result = client.post(f"{settings.meterless_url}/embeddings", headers=headers,
                                 json={"model": model, "input": texts[start:start+128]})
            if start == 0 and result.status_code in (404, 405, 501):
                print(f"Nightshift /embeddings: HTTP {result.status_code}; using local fallback", flush=True)
                return None
            if not result.is_success:
                raise RuntimeError(f"Nightshift embedding request failed: HTTP {result.status_code}")
            body = result.json()
            data = sorted(body["data"], key=lambda row: row["index"])
            if [row["index"] for row in data] != list(range(len(texts[start:start+128]))):
                raise ValueError("Nightshift embedding response does not cover every input")
            vectors.extend(row["embedding"] for row in data)
            receipt = (body.get("meterless") or {}).get("receipt_id")
            if receipt:
                receipts.append(receipt)
    return vectors, model, "nightshift", receipts


def local_embeddings(texts, allow_download=False):
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "60")
    from fastembed import TextEmbedding
    model = TextEmbedding(model_name=LOCAL_MODEL, cache_dir=str(ROOT / ".cache/embeddings"),
                          threads=2, local_files_only=not allow_download)
    print(f"Local embedding model ready: {LOCAL_MODEL}; {len(texts)} distinct descriptions", flush=True)
    vectors = [vector.tolist() for vector in model.embed(texts, batch_size=64)]
    return vectors, LOCAL_MODEL, "local_fastembed", []


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download-model", action="store_true", help="Allow a one-time model download during setup")
    parser.add_argument("--backend", choices=["auto", "local", "nightshift"], default="auto")
    args = parser.parse_args(argv)
    os.environ["SAMPLE_MODE"] = "false"
    from app.adapters.config import get_settings
    from app.adapters.zetaris import run_sql
    get_settings.cache_clear()
    result = run_sql(PAIRS_SQL, limit=100000, timeout=90, retries=0)
    if result.replayed:
        raise ValueError("Preparation requires live data")
    pairs = result.dicts()
    rule = run_sql("SELECT params FROM gebiz_pg.rules WHERE flag_id = 'R5'", timeout=30, retries=0)
    if rule.replayed or len(rule.rows) != 1:
        raise ValueError("Live R5 rule configuration is missing")
    max_similarity = float(json.loads(rule.rows[0][0]).get("max_similarity", 0.2))
    texts = sorted({row[key] for row in pairs for key in ("tender_description", "ssic_description")})
    if not texts or len(texts) > 5000:
        raise ValueError("Expected between 1 and 5000 distinct descriptions for bounded preparation")
    embeddings = nightshift_embeddings(texts) if args.backend != "local" else None
    if embeddings is None:
        if args.backend == "nightshift":
            raise RuntimeError("Nightshift does not expose a supported embedding endpoint")
        embeddings = local_embeddings(texts, args.download_model)
    vectors, model, backend, receipts = embeddings
    if len(vectors) != len(texts):
        raise ValueError("Embedding count does not match description count")
    lookup = dict(zip(texts, vectors))
    scores = [{**row, "similarity": cosine(lookup[row["tender_description"]], lookup[row["ssic_description"]])}
              for row in pairs]
    params = {"max_similarity": max_similarity, "prepared": True, "model": model, "backend": backend,
              "prepared_at": datetime.now(timezone.utc).isoformat(), "source_query_id": result.query_id,
              "description_sha256": hashlib.sha256(json.dumps(texts, ensure_ascii=False).encode()).hexdigest(),
              "meterless_receipt_ids": receipts, "similarities": scores}
    validate_scores(params, pairs)
    # Setup scripts may write backing stores. Runtime agents continue reading through Zetaris only.
    from fetch_common import pg_conn
    with pg_conn("gebiz") as connection, connection.cursor() as cursor:
        cursor.execute("UPDATE rules SET params = %s::jsonb WHERE flag_id = 'R5'", (json.dumps(params),))
        if cursor.rowcount != 1:
            raise RuntimeError("R5 rule row missing; seed the rules first")
    evidence = {key: value for key, value in params.items() if key != "similarities"}
    evidence["pairs"] = len(scores)
    output = ROOT / "logs/r5-preparation.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(scores)} description pairs using {backend}; evidence: {output}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"R5 preparation failed ({type(exc).__name__}); check service availability and cached model setup. No successful preparation claimed.", file=sys.stderr)
        sys.exit(1)
