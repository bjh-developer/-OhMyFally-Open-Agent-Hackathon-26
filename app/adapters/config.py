"""Settings read from .env / the environment. Values are never logged."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    zetaris_url: str
    zetaris_org_id: str
    zetaris_api_key: str
    meterless_url: str
    meterless_token: str
    model_deep: str
    model_fast: str
    app_deep: str
    app_fast: str
    hmem_url: str
    sample_mode: bool
    max_retries: int
    llm_call_cap: int
    source_timeout: float
    logs_dir: Path
    replay_dir: Path


def _bool(v: str | None, default: bool) -> bool:
    return default if v is None else v.strip().lower() in {"1", "true", "yes", "on"}


def _replay_dir(name: str) -> Path:
    """REPLAY_SET is a set name under data/replay/, or a path."""
    return Path(name) if os.sep in name else ROOT / "data" / "replay" / name


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv(ROOT / ".env", override=False)
    e = os.environ.get
    return Settings(
        zetaris_url=e("ZETARIS_REST_URL", "http://localhost:8888/api/v1.0").rstrip("/"),
        zetaris_org_id=e("ZETARIS_ORG_ID", "1"),
        zetaris_api_key=e("ZETARIS_API_KEY", ""),
        meterless_url=e("METERLESS_BASE_URL", "http://127.0.0.1:8088/v1").rstrip("/"),
        meterless_token=e("METERLESS_RUNTIME_TOKEN", ""),
        model_deep=e("METERLESS_MODEL_DEEP", "meterless/deep"),
        model_fast=e("METERLESS_MODEL_FAST", "meterless/fast"),
        app_deep=e("METERLESS_APP_DEEP", "procurement-integrity"),
        app_fast=e("METERLESS_APP_FAST", "procurement-integrity-fast"),
        hmem_url=e("HMEM_URL", "http://127.0.0.1:7070").rstrip("/"),
        sample_mode=_bool(e("SAMPLE_MODE"), True),
        max_retries=int(e("MAX_RETRIES", "2")),
        llm_call_cap=int(e("LLM_CALL_CAP", "40")),
        source_timeout=float(e("SOURCE_TIMEOUT_SECONDS", "20")),
        logs_dir=ROOT / "logs",
        replay_dir=_replay_dir(e("REPLAY_SET", "hdb-fy2425")),
    )
