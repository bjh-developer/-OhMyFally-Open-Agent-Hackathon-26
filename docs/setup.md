# Setup, configuration and tests

Part of the [ProcureLens README](../README.md).

## Path A: offline sample mode (no services, no credentials)

This replays live-recorded Zetaris results and Nightshift replies for the five recorded inputs. The agents, rules, Critic and
Reporter still run. Read [How SAMPLE_MODE works](sample-mode.md) for exactly what is and is not real.

**Recommended: the web UI and the API together (Docker Compose).** No `.env` is needed.

```bash
docker compose up --build api web
```

The first build takes a few minutes. Then open **http://localhost:3100**, choose *Housing and Development Board*, keep
*FY2024/25* and press **Start review**: the live agent timeline, the ranked results, the evidence for each item and the
*Technical view* (trace, loops, model calls) all work offline. The page marks the run as **Recorded data**. Other requests
with recordings (use *Custom* for the period):

| Agency | Period | Same as |
|---|---|---|
| Housing and Development Board | 1 Apr 2024 to 31 Mar 2025 | `example_1.json` |
| People's Association | 1 Jan 2024 to 31 Dec 2024, checks R1 and R4 | `example_2.json` |
| National Parks Board | 1 Jan 2023 to 31 Dec 2025 | `example_3.json` |
| People's Association | 1 Apr 2021 to 31 Mar 2026 | `example_4.json` (shows the Critic's retries) |
| Synthetic Review Agency | 1 Jan 2025 to 31 Dec 2025, checks R5 and R6 | `example_remaining.json` |

The same stack serves the API on port 8000, so the `curl` below works too. If 3100 or 8000 is taken, pick other host ports:
`API_PORT=8001 WEB_PORT=3101 docker compose up --build api web`. `api` and `web` sit in a Compose profile, so they never need
Zetaris's Docker network; a plain `docker compose up` still starts only the data services of Path B. Stop with
`docker compose down`. Confirm and Dismiss need H-MEM, so offline they are not saved.

**With Python 3.11:**

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
SAMPLE_MODE=true python run.py --input input_examples/example_1.json
```

Try the other recorded inputs the same way: `example_2.json`, `example_3.json`, `example_4.json`, `example_remaining.json`.

**API only, with Docker:**

```bash
docker build -t oah-submission .
docker run --rm -p 8000:8000 -e SAMPLE_MODE=true oah-submission
```

If port 8000 is busy, use another host port, for example `-p 8101:8000`, and change the URL below to match. In a second terminal:

```bash
curl -X POST http://localhost:8000/run -H "Content-Type: application/json" -d @input_examples/example_1.json
```

You will see one line per agent step on stdout, the full trace in `logs/<run_id>.jsonl`, and the memo in `logs/<run_id>.md` and
`logs/<run_id>.memo.json`. The CLI prints the memo after the trace; the API returns it in the response. A request that has no
recorded data is refused with a message that lists what is recorded.

## Path B: full live setup

Needs Docker (Zetaris alone wants 8 GB of memory and 4 CPUs), Zetaris running locally, and Meterless Nightshift running with
an NVIDIA key in its **Providers** tab (never in this project). Follow the Participant Setup Guide for Zetaris and Nightshift,
then:

1. **Nightshift apps.** In the Nightshift Console, under *Apps*, create two apps: `procurement-integrity` bound to the **deep**
   mode and `procurement-integrity-fast` bound to the **fast** mode. Nightshift binds one mode per app, so the app name is how
   this project picks a lane.
2. **Configure.** Copy the example file and fill in the Zetaris API key, the Nightshift runtime token, a Postgres password and a
   long random `PSEUDONYM_KEY`. Set `SAMPLE_MODE=false` so a live run can never fall back to a recording.

   ```bash
   cp .env.example .env
   python3.11 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Containers.** Start Zetaris first (it creates the `zetaris_default` Docker network), then ours: `pi-postgres`, `pi-s3`
   (SeaweedFS) and `pi-hmem`. Building `pi-hmem` runs the official H-MEM conformance suite and fails the build if it does not pass.

   ```bash
   docker compose up -d
   python scripts/smoke_test.py      # 3 checks: Zetaris REST, Nightshift deep lane, Nightshift fast lane
   ```

4. **Load and register the data, then resolve suppliers.** Order matters: `seed.py` empties the supplier crosswalk and the
   derived R5 scores, so rerun the later steps after any reseed.

   ```bash
   python scripts/seed.py                       # Postgres tables, ACRA Parquet on S3, fictional planted cases
   python scripts/register_zetaris.py           # registers the sources and the procurement_usl model in Zetaris
   python -m app.resolver.run --pass 1          # Resolver pass 1: exact and former-name matches
   python -m app.resolver.run --pass 2          # Resolver pass 2: fuzzy, fast-lane LLM tie-break, unresolved
   python scripts/prepare_r5.py --download-model   # once: R5 text-similarity scores (see below)
   ```

   Nightshift does not serve `/embeddings` (it returned HTTP 501 when we checked on 23 Oct; the script also handles 404 and 405), so R5 uses a small
   local model, `sentence-transformers/all-MiniLM-L6-v2` through fastembed. `--download-model` fetches it once into the
   gitignored `.cache/embeddings/`. Investigation runs never download or load a model; they read the precomputed scores from
   Zetaris.

5. **Run.**

   ```bash
   python run.py --input input_examples/example_1.json     # one run from the command line
   # or serve the API:
   python run.py --serve                                    # 0.0.0.0:$PORT, default 8000
   curl -X POST http://localhost:8000/run -H "Content-Type: application/json" -d @input_examples/example_1.json
   ```

   `POST /run` waits and returns the finished run. Add `?wait=false` to get `202` and a `run_id` at once, then poll
   `GET /runs/{run_id}` or stream `GET /runs/{run_id}/events` (server-sent events). Live runs of the three examples took about
   4 minutes, 1 minute and 5 minutes; a run is capped at 40 model calls (`LLM_CALL_CAP`).

**Running the API in Docker against live services.** Inside a container `localhost` is the container itself, so point the
app at the host with the `host.docker.internal` URLs that are commented in `.env.example`:

```text
ZETARIS_REST_URL=http://host.docker.internal:8888/api/v1.0
METERLESS_BASE_URL=http://host.docker.internal:8088/v1
HMEM_URL=http://host.docker.internal:7070
```

Mounting `.env` lets the app read it with `python-dotenv` exactly as on the host; `--env-file .env` also works, as long as
comments stay on their own lines (Docker keeps an inline `# ...` as part of the value). On Linux, add `--add-host=host.docker.internal:host-gateway`. Mount `logs/` to keep the traces.

```bash
docker run --rm -p 8000:8000 -v "$PWD/.env:/app/.env:ro" -v "$PWD/logs:/app/logs" oah-submission
```

(`S3_ENDPOINT=http://pi-s3:8333` stays as is: it is the address Zetaris uses to reach our S3 container, not one the app uses.)

## Web UI

`web/` is a Next.js 15 interface on **port 3100** (Zetaris owns 3000). `docker compose up --build api web` runs it with the API
(Path A above; with your `.env` keys the same command runs live, reaching Zetaris, Nightshift and H-MEM on the host through
`host.docker.internal`). For development, start the API first, then:

```bash
cd web
cp .env.example .env.local     # optional; the defaults point at the API on 127.0.0.1:8000
npm install
npm run dev                    # http://127.0.0.1:3100
```

It shows a live agent timeline (the SSE stream), the ranked memo, an evidence drawer with the SQL and rows, and a human-review
queue with **Confirm** and **Dismiss**. A decision is forwarded by the Next.js route `web/app/api/auditor-decision/route.ts` to
H-MEM (`HMEM_URL`), so Confirm and Dismiss need the `pi-hmem` service. A *Replay mock run* button plays `web/mocks/run_demo.json`
(fictional suppliers) without any backend. Details: [web/README.md](../web/README.md).

## Configuration

From [.env.example](../.env.example). Secrets live only in `.env`, which is gitignored.

| Variable | Default / example | Purpose |
|---|---|---|
| `ZETARIS_REST_URL` | `http://localhost:8888/api/v1.0` | Zetaris REST (use `host.docker.internal` inside Docker) |
| `ZETARIS_ORG_ID` | `1` | Sent as `X-Org-ID` |
| `ZETARIS_API_KEY` | placeholder | Zetaris bearer key |
| `METERLESS_BASE_URL` | `http://127.0.0.1:8088/v1` | Nightshift runtime |
| `METERLESS_RUNTIME_TOKEN` | placeholder | Nightshift bearer token |
| `METERLESS_MODEL_DEEP` / `METERLESS_MODEL_FAST` | `meterless/deep` / `meterless/fast` | Model names sent per lane |
| `METERLESS_APP_DEEP` / `METERLESS_APP_FAST` | `procurement-integrity` / `procurement-integrity-fast` | Nightshift apps bound to each lane |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` | `pi` / `change-me` | Our Postgres container |
| `S3_ENDPOINT`, `S3_BUCKET` | `http://pi-s3:8333`, `pi-acra` | Our S3 container, as Zetaris sees it |
| `HMEM_URL` | `http://127.0.0.1:7070` | H-MEM service |
| `PSEUDONYM_KEY` | placeholder | HMAC key for `?view=public` aliases |
| `PORT` | `8000` | API port for `run.py --serve` |
| `LOG_LEVEL` | `info` | API log level |
| `SAMPLE_MODE` | `true` (also when unset) | See [How SAMPLE_MODE works](sample-mode.md) |
| `REPLAY_SET` | `hdb-fy2425` | Default recorded set for scripts; a run only replays the set recorded for its own agency and dates |
| `CORS_ORIGINS` | `http://127.0.0.1:3100,http://localhost:3100` | Web UI origins the API accepts |
| `API_PORT`, `WEB_PORT` | `8000`, `3100` | Host ports for `docker compose up --build api web` |
| `MAX_RETRIES` | `2` | Per-loop retry limit (capped at 2 in code) |
| `LLM_CALL_CAP` | `40` | Model calls per run |
| `SOURCE_TIMEOUT_SECONDS` | `20` | Zetaris timeout (checks use at least 60) |

`S3_ACCESS_KEY` and `S3_SECRET_KEY` are optional overrides read by `register_zetaris.py` (defaults are local-only SeaweedFS values).

## Tests

```bash
pytest -m "not live"
```

Current result: **132 passed, 23 skipped** in about 6 seconds with no services running; with Zetaris and H-MEM up, 141 pass and 14 skip.
The skips are live tests, which skip themselves when their service is missing: `tests/test_planted_checks.py` (needs Zetaris), `tests/test_check_sql_edges.py` (needs
Zetaris and `RUN_LIVE_SQL_TESTS=1`) and `tests/test_hmem_client.py` (needs the `pi-hmem` service). The `live` marker is registered in
`pytest.ini`; live tests also skip on their own when a service is missing. With Zetaris and H-MEM up they run, including the
planted-case checks against real data. Web tests: `cd web && npm test`.

**CI.** `.github/workflows/ci.yml` runs a TruffleHog secret scan over the full git history and `pytest -m "not live"`; on every push to `main` and every pull request.

**H-MEM conformance and tests:** see [Sponsor technology: H-MEM](sponsor-tech.md#meterless-h-mem-auditor-memory) (13/13 conformance checks; `npm test` 21 passed).
