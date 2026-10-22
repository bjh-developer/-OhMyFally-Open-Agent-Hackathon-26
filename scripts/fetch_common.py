"""Shared helpers for the data.gov.sg fetch scripts (rate limit aware, cached in data/raw/)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
SAMPLE = ROOT / "data" / "sample"
LOCAL = ROOT / "data" / "local"  # gitignored: full ACRA candidate set (contains sole-proprietor rows)
API = "https://api-open.data.gov.sg/v1/public/api/datasets"
TIMEOUT = 60

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def download_dataset(dataset_id: str, dest: Path, force: bool = False, max_polls: int = 20) -> Path:
    """initiate-download -> poll -> presigned S3 URL -> dest. Cached unless force."""
    if dest.exists() and dest.stat().st_size > 0 and not force:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = None
    for _ in range(max_polls):
        r = httpx.get(f"{API}/{dataset_id}/initiate-download", timeout=TIMEOUT)
        if r.status_code == 429:
            time.sleep(15)
            continue
        r.raise_for_status()
        url = (r.json().get("data") or {}).get("url")
        if url:
            break
        r = httpx.get(f"{API}/{dataset_id}/poll-download", timeout=TIMEOUT)
        if r.is_success:
            url = (r.json().get("data") or {}).get("url")
            if url:
                break
        time.sleep(3)
    if not url:
        raise RuntimeError(f"no download url for {dataset_id}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    with httpx.stream("GET", url, timeout=TIMEOUT, follow_redirects=True) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_bytes(1 << 20):
                f.write(chunk)
    tmp.replace(dest)
    return dest


# ---- local container access for setup scripts (seed.py, resolver writes) -------------------------
# Setup scripts are the one place allowed to talk to Postgres/S3 directly (CONTRACTS §2.5).
# Host-side addresses differ from the in-network ones Zetaris uses (pi-postgres:5432, pi-s3:8333).
import os  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")


def pg_conn(dbname: str = "gebiz"):
    import psycopg

    return psycopg.connect(
        host=os.getenv("PI_PG_HOST", "127.0.0.1"),
        port=int(os.getenv("PI_PG_PORT", "55432")),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=dbname,
        connect_timeout=10,
        autocommit=False,
    )


def s3_client():
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=os.getenv("PI_S3_HOST_ENDPOINT", "http://127.0.0.1:18333"),
        aws_access_key_id=os.getenv("S3_ACCESS_KEY", "pi"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY", "pi-secret"),
        region_name="us-east-1",
        config=Config(s3={"addressing_style": "path"}, connect_timeout=10, read_timeout=60, retries={"max_attempts": 2}),
    )
