import pytest

from app.adapters import config


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    for k, v in {
        "ZETARIS_REST_URL": "http://zetaris.test/api/v1.0", "ZETARIS_ORG_ID": "1", "ZETARIS_API_KEY": "zk-secret",
        "METERLESS_BASE_URL": "http://ns.test/v1", "METERLESS_RUNTIME_TOKEN": "ns-secret",
        "METERLESS_APP_DEEP": "app-deep", "METERLESS_APP_FAST": "app-fast",
        "SOURCE_TIMEOUT_SECONDS": "5", "MAX_RETRIES": "2", "LLM_CALL_CAP": "40",
    }.items():
        monkeypatch.setenv(k, v)
    config.get_settings.cache_clear()
    monkeypatch.setattr("time.sleep", lambda *_: None)
    yield
    config.get_settings.cache_clear()
