"""FastAPI: POST /run, GET /runs/{id}, GET /runs/{id}/events (SSE), GET /healthz.

    uvicorn app.api:app --port 8000
"""
from __future__ import annotations

import asyncio
import json
import re
import threading
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .adapters.config import get_settings
from .orchestration.factory import make_deps
from .orchestration.graph import run_investigation
from .schemas import Memo, RunRequest
from .tracing import Tracer, new_run_id

app = FastAPI(title="Procurement Integrity Investigator")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:3100", "http://localhost:3100"],
                   allow_methods=["GET", "POST"], allow_headers=["*"])

_RUNS: dict[str, dict[str, Any]] = {}
_ID = re.compile(r"^run_[A-Za-z0-9_\-]{1,64}$")


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
        rec["tracer"].emit("Orchestrator", "run_failed", output=rec["error"], status="failed")


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.post("/run", status_code=202)
def post_run(req: RunRequest, wait: bool = False) -> dict:
    """Start a run. ``?wait=true`` blocks until the memo is ready (for scripts and tests)."""
    run_id = new_run_id()
    _RUNS[run_id] = {"status": "running", "tracer": Tracer(run_id), "memo": None, "error": None}
    t = threading.Thread(target=_execute, args=(run_id, req), daemon=True)
    t.start()
    if wait:
        t.join(timeout=600)
    return _view(run_id)


def _view(run_id: str) -> dict:
    rec = _RUNS.get(run_id)
    if not rec:
        raise HTTPException(404, "unknown run")
    memo: Memo | None = rec["memo"]
    return {"run_id": run_id, "status": rec["status"], "error": rec["error"], "trace_path": str(rec["tracer"].path),
            "memo": memo.model_dump(mode="json") if memo else None, "events": len(rec["tracer"].events)}


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> dict:
    if not _ID.match(run_id):
        raise HTTPException(404, "unknown run")
    return _view(run_id)


@app.get("/runs/{run_id}/events")
async def run_events(run_id: str) -> StreamingResponse:
    """Server-sent events: replays the trace so far, then streams new lines until the run ends."""
    if not _ID.match(run_id) or run_id not in _RUNS:
        raise HTTPException(404, "unknown run")
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
