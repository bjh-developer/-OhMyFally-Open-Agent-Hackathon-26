# Run it (draft for the README)

Every command below was run on 23 Oct 2026 from this branch. Timings are in the last section.

## 1. No credentials, no services: sample mode

`SAMPLE_MODE=true` with no `ZETARIS_API_KEY` and no `METERLESS_RUNTIME_TOKEN` runs offline. The agents (Gate, Planner,
Resolver, Analyst, Critic, Risk, Reporter) and the red-flag checks run for real. Their Zetaris rows and Nemotron replies
are read from `data/replay/<set>/`, recorded earlier from live runs. Nothing opens a network connection.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
SAMPLE_MODE=true python run.py --input input_examples/example_1.json
SAMPLE_MODE=true python run.py --input input_examples/example_2.json
SAMPLE_MODE=true python run.py --input input_examples/example_3.json
```

What you will see:

- One trace line per step on stdout (agent, action, status, model, ids), and the full trace in `logs/<run_id>.jsonl`.
- Ids that start with `replay:` and a model name ending `(replayed)`: those answers came from a recording.
- A limitation line at the top of the memo saying so.
- `H-MEM skipped`: auditor memory needs the H-MEM service, which sample mode does not call.

Limits of sample mode:

- Only the three recorded requests (the `input_examples/`) can run offline. Any other agency or period is refused with a
  message that lists what is recorded. To run anything else, set the Zetaris and Nightshift variables (section 3).
- If a recorded model reply is missing, that step uses its rule-based fallback (deterministic scores, template
  narrative) and the memo says how many.

## 2. Docker

```bash
docker build -t oah-submission .
docker run --rm -p 8000:8000 -e SAMPLE_MODE=true oah-submission
```

In another terminal:

```bash
curl -X POST http://localhost:8000/run -H "Content-Type: application/json" -d @input_examples/example_1.json
```

`POST /run` waits and returns the finished run: `{run_id, status, memo, trace_id, execution_time_seconds, ...}`.
Add `?wait=false` to get `202` and a `run_id` at once, then poll `GET /runs/{run_id}`.

A failed or refused run returns `{run_id, status:"error", error:{type, message, recoverable}, trace_id, execution_time_seconds}`
and never a stack trace.

Other endpoints: `GET /healthz`, `GET /runs/{id}`, `GET /runs/{id}/summary`, `GET /runs/{id}/events` (server-sent events).

## 3. Live services

Copy `.env.example` to `.env` and fill in the Zetaris key and the Nightshift runtime token. Inside Docker, use the
`host.docker.internal` URLs that are commented in `.env.example`.

```bash
cp .env.example .env
docker run --rm -p 8000:8000 --env-file .env oah-submission
```

Without Docker: `python run.py --serve` (port from `PORT`, default 8000), or run one request from the command line:
`python run.py --input input_examples/example_1.json`.

With keys set and `SAMPLE_MODE=true`, live services are tried first and the recording answers only if they are down.
Set `SAMPLE_MODE=false` to never fall back.

## 4. Tests

```bash
pytest -m "not live"
```

## 5. Where the examples come from

`output_examples/example_N.memo.json`, `.memo.md` and `.trace.jsonl` are the outputs of live runs of
`input_examples/example_N.json` (Zetaris and Nightshift up, H-MEM on). They are not read at runtime.
