import run


def test_serve_binds_all_interfaces_on_port(monkeypatch):
    seen = {}
    monkeypatch.setattr("uvicorn.run", lambda app, **kw: seen.update(app=app, **kw))
    monkeypatch.setenv("PORT", "8123")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    assert run.main(["--serve"]) == 0
    assert seen == {"app": "app.api:app", "host": "0.0.0.0", "port": 8123, "log_level": "warning"}


def test_serve_defaults_to_8000_and_is_the_no_argument_default(monkeypatch):
    seen = {}
    monkeypatch.setattr("uvicorn.run", lambda app, **kw: seen.update(kw))
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    assert run.main([]) == 0
    assert seen["host"] == "0.0.0.0" and seen["port"] == 8000


def test_cli_flags_still_parse_without_serving(monkeypatch):
    called = []
    monkeypatch.setattr("uvicorn.run", lambda *a, **k: called.append(1))
    try:
        run.main(["--agency", "X"])
    except SystemExit as e:
        assert e.code == 2  # argparse: dates missing
    assert not called
