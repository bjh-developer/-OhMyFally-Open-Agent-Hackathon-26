# Pre-existing components and repository layout

Part of the [ProcureLens README](../README.md).

| Component | Origin | Licence |
|---|---|---|
| H-MEM reference implementation (`services/hmem-upstream/`; our service in `services/hmem/` is adapted from it) | Meterless, github.com/Meterless/Meterless | Apache-2.0 |
| Open-source libraries: LangGraph, FastAPI, uvicorn, httpx, pydantic, rapidfuzz, fastembed, pandas, pyarrow, psycopg, boto3 (see [requirements.txt](../requirements.txt)); Hono and tsx (H-MEM service); Next.js and Radix UI (web) | Public packages | Their own licences |
| Public datasets: GeBIZ, ACRA, AGO reports | data.gov.sg; ago.gov.sg | See [Data and licences](data-and-privacy.md) |
| Container images: Postgres 16, SeaweedFS 3.80, Node 22, Python 3.11 | Docker Hub | Their own licences |

**Our work began on 22 October 2026 (the first product-code commit is 22 Oct, 10:16 SGT; the window opened at 08:00 SGT).**
The eight commits dated 21 Oct (`git log`) contain only `.gitignore`, `.gitattributes`, the agent instruction files `AGENTS.md` and
`CLAUDE.md`, and planning documents under `docs/agents/`. No product code and no data were committed before the window.
Repository licence: there is no top-level `LICENSE` file yet; `services/hmem/` and `services/hmem-upstream/` carry the Apache-2.0 licence.

## Repository layout

```text
run.py                  CLI and API entry point (run.py --input FILE | run.py --serve)
app/                    Python 3.11 package
  agents/               planner, resolver, analyst, critic, risk, reporter, ago
  orchestration/        graph.py (LangGraph wiring), state.py, factory.py
  adapters/             zetaris.py, nightshift.py, hmem_client.py, config.py
  resolver/             supplier-name matching (exact, former name, fuzzy, LLM tie-break)
  checks/               loads sql/checks/*.sql and builds findings
  api.py replay.py privacy.py run_summary.py schemas.py tracing.py
services/hmem/          H-MEM service (TypeScript, Apache-2.0), with NOTICE
services/hmem-upstream/ Meterless reference and the official conformance suite
sql/                    register/ (Zetaris sources and USL), checks/ (R1-R6, R8, R9), critic/
data/                   sample/ (committed samples), replay/ (5 recorded sets), rules/, ago/, eval/
scripts/                seed, register_zetaris, prepare_r5, smoke_test, eval, eval_resolver, record_replay, token_baseline
web/                    Next.js UI on port 3100 (web/Dockerfile; `docker compose up --build api web`)
input_examples/         request files (example_1 to example_4, example_remaining)
output_examples/        memos, traces and metrics from live runs
logs/evidence/          H-MEM conformance output
tests/                  pytest suite
docs/                   agents/ (contracts), handover/ (data, red flags, evaluation), drafts/run-it.md
Dockerfile docker-compose.yml .env.example metadata.json
```
