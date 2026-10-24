"""FastAPI: POST /run, GET /runs/{id}, GET /runs/{id}/events (SSE), GET /healthz.

    uvicorn app.api:app --port 8000
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import threading
import time
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from .adapters.config import get_settings
from .orchestration.factory import make_deps
from .orchestration.graph import run_investigation
from .run_summary import read_events, summarise
from .privacy import PseudonymKeyMissing, mask_payload
from .schemas import Memo, RunRequest
from .tracing import Tracer, format_event, new_run_id

app = FastAPI(title="Procurement Integrity Investigator")
# The web UI's origin; CORS_ORIGINS (comma-separated) overrides it, e.g. when the UI runs on another port.
_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://127.0.0.1:3100,http://localhost:3100").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=_ORIGINS,
                   allow_methods=["GET", "POST"], allow_headers=["*"])

_RUNS: dict[str, dict[str, Any]] = {}
_ID = re.compile(r"^run_[A-Za-z0-9_\-]{1,64}$")


WAIT_TIMEOUT_S = 600


def _error_body(run_id: str | None, etype: str, message: str, recoverable: bool, started: float | None = None) -> dict:
    return {"run_id": run_id, "status": "error", "error": {"type": etype, "message": message, "recoverable": recoverable},
            "trace_id": run_id, "execution_time_seconds": round(time.monotonic() - started, 2) if started else 0.0}


@app.exception_handler(RequestValidationError)
async def _invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
    msg = "; ".join(f"{'.'.join(str(x) for x in e['loc'][1:]) or 'body'}: {e['msg']}" for e in exc.errors())[:400]
    return JSONResponse(_error_body(None, "invalid_request", msg, True), status_code=422)


def _execute(run_id: str, req: RunRequest) -> None:
    rec = _RUNS[run_id]
    try:
        tracer = rec["tracer"]
        final = run_investigation(req, make_deps(tracer))
        rec["memo"] = final.get("memo")
        rec["status"] = "done" if final.get("memo") else "rejected"
        rec["error"] = final.get("rejected_reason")
    except Exception as e:  # never leave a run hanging
        rec["status"], rec["error"] = "failed", f"{type(e).__name__}: {str(e)[:200]}"
        rec["error_type"] = type(e).__name__
        rec["tracer"].emit("Orchestrator", "run_failed", output=rec["error"], status="failed")
    finally:
        rec["finished"] = time.monotonic()


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.post("/run")
def post_run(req: RunRequest, wait: bool = True) -> JSONResponse:
    """Run an investigation. By default the call blocks and returns the finished result (memo included), so a plain
    ``curl -X POST /run -d @input.json`` gets the answer. ``?wait=false`` returns 202 at once with a run_id to poll
    (``GET /runs/{id}``, ``GET /runs/{id}/events``). A failed or rejected run returns
    ``{run_id, status:"error", error:{type, message, recoverable}, trace_id, execution_time_seconds}``."""
    run_id = new_run_id()
    started = time.monotonic()
    tracer = Tracer(run_id)
    tracer.subscribe(lambda e: print(format_event(e), flush=True))
    _RUNS[run_id] = {"status": "running", "tracer": tracer, "memo": None, "error": None, "started": started}
    t = threading.Thread(target=_execute, args=(run_id, req), daemon=True)
    t.start()
    if not wait:
        return JSONResponse(_view(run_id), status_code=202)
    t.join(timeout=WAIT_TIMEOUT_S)
    rec = _RUNS[run_id]
    if rec["status"] == "running":  # still going after the wait budget: hand back the id to poll
        return JSONResponse({**_view(run_id), "execution_time_seconds": round(time.monotonic() - started, 2)}, status_code=202)
    secs = round(rec.get("finished", time.monotonic()) - started, 2)
    if rec["status"] == "done":
        return JSONResponse({**_view(run_id), "trace_id": run_id, "execution_time_seconds": secs})
    if rec["status"] == "rejected":
        return JSONResponse(_error_body(run_id, "request_rejected", str(rec["error"]), True, started), status_code=422)
    msg = "The investigation could not finish. The trace holds the details: " + str(rec["tracer"].path.name)
    return JSONResponse(_error_body(run_id, "run_failed", msg, False, started), status_code=500)


def _from_disk(run_id: str) -> tuple[dict, list[dict]] | None:
    """A run this process didn't start (API restarted, or a CLI run): rebuilt from logs/<run_id>.jsonl and .memo.json."""
    logs = get_settings().logs_dir
    path = logs / f"{run_id}.jsonl"
    if not path.is_file():
        return None
    events = read_events(path)
    memo_path = logs / f"{run_id}.memo.json"
    memo = json.loads(memo_path.read_text(encoding="utf-8")) if memo_path.is_file() else None
    failed = next((e for e in events if e.get("action") == "run_failed"), None)
    ended = any(e.get("action") == "end_run" for e in events)
    if memo:
        status, error = "done", None
    elif failed:
        status, error = "failed", failed.get("output_summary")
    elif ended:
        status, error = "rejected", (events[-1].get("output_summary") if events else None)
    else:  # no end line: the run was cut off (process stopped mid-run)
        status, error = "failed", "trace ends before the run finished"
    view = {"run_id": run_id, "status": status, "error": error, "trace_path": str(path), "memo": memo, "events": len(events)}
    return view, events


def _view(run_id: str) -> dict:
    rec = _RUNS.get(run_id)
    if not rec:
        disk = _from_disk(run_id)
        if not disk:
            raise HTTPException(404, "unknown run")
        return disk[0]
    memo: Memo | None = rec["memo"]
    return {"run_id": run_id, "status": rec["status"], "error": rec["error"], "trace_path": str(rec["tracer"].path),
            "memo": memo.model_dump(mode="json") if memo else None, "events": len(rec["tracer"].events)}


@app.get("/runs/{run_id}")
def get_run(run_id: str, view: Literal["full", "public"] = "full") -> dict:
    """``?view=public`` pseudonymises supplier names (app/privacy.py); the default is the auditor's full view."""
    if not _ID.match(run_id):
        raise HTTPException(404, "unknown run")
    out = _view(run_id)
    if view == "public":
        try:
            out["memo"] = mask_payload(out["memo"])
        except PseudonymKeyMissing:
            raise HTTPException(503, "public view unavailable: PSEUDONYM_KEY is not configured")
    return out


@app.get("/runs/{run_id}/summary")
def get_run_summary(run_id: str, view: Literal["full", "public"] = "full") -> dict:
    """How the agents worked, computed from the run's trace. Works for live, finished and replayed runs."""
    if not _ID.match(run_id):
        raise HTTPException(404, "unknown run")
    rec = _RUNS.get(run_id)
    path = get_settings().logs_dir / f"{run_id}.jsonl"
    if rec:
        events = [e.model_dump(mode="json", exclude_none=True) for e in list(rec["tracer"].events)]
    elif path.is_file():
        events = read_events(path)
    else:
        raise HTTPException(404, "unknown run")
    out = {"run_id": run_id, **summarise(events)}
    if view == "public":
        try:
            out = mask_payload(out)
        except PseudonymKeyMissing:
            raise HTTPException(503, "public view unavailable: PSEUDONYM_KEY is not configured")
    return out


@app.get("/runs/{run_id}/events")
async def run_events(run_id: str) -> StreamingResponse:
    """Server-sent events: replays the trace so far, then streams new lines until the run ends."""
    if not _ID.match(run_id):
        raise HTTPException(404, "unknown run")
    if run_id not in _RUNS:
        disk = _from_disk(run_id)
        if not disk:
            raise HTTPException(404, "unknown run")
        view, events = disk

        async def replay():
            for e in events:
                yield f"data: {json.dumps(e)}\n\n"
            yield f"event: end\ndata: {json.dumps({'status': view['status']})}\n\n"

        return StreamingResponse(replay(), media_type="text/event-stream")
    rec = _RUNS[run_id]

    async def gen():
        sent = 0
        while True:
            evs = rec["tracer"].events
            while sent < len(evs):
                yield f"data: {evs[sent].model_dump_json(exclude_none=True)}\n\n"
                sent += 1
            if rec["status"] != "running" and sent >= len(rec["tracer"].events):
                yield f"event: end\ndata: {json.dumps({'status': rec['status']})}\n\n"
                return
            await asyncio.sleep(0.4)

    return StreamingResponse(gen(), media_type="text/event-stream")
