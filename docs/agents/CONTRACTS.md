# Shared contracts: read this before writing code

Every agent instruction file in `docs/agents/` points here. These are the interfaces between the three owners, so three people (and their coding agents) can build in parallel without breaking each other. **Do not change a contract on your own.** Propose the change to the team first, then update this file in the same commit as the code.

The team plan is the source of truth for *why*: https://claude.ai/code/artifact/33db073a-a6f9-4f3d-a817-8e02bf03c74c

---

## 1. What we are building (one paragraph)

**Procurement Integrity Investigator**, Open Agent Hackathon 2026, **Track 02: The Agent That Can Explain Why**. An agency internal auditor asks "which of Agency X's procurement awards in period P need review, and why?". Agents federate GeBIZ awards, the ACRA company registry, MOF thresholds, Auditor-General (AGO) findings and synthetic internal records through **Zetaris**. They reason with **NVIDIA Nemotron via Meterless Nightshift**, remember auditor feedback in **Meterless H-MEM**, and return a ranked review memo where every flag cites the source rows and SQL behind it.

## 2. Hard rules (all owners, all agents)

1. **No product code committed before 22 Oct 2026, 08:00 SGT** (00:00 UTC). Docs and config are fine.
2. **Develop in Cursor.** This is required by the hackathon.
3. **Secrets live only in `.env`, which is gitignored.** Commit `.env.example` with placeholders. Never print, log, paste or put a key in a URL. The NVIDIA key lives only in Nightshift's Providers tab.
4. **All LLM calls go through Nightshift.** Use the two app headers in §5, and never call build.nvidia.com directly except as the logged fallback.
5. **All data access goes through Zetaris.** Do not query Postgres or S3 directly from agent code (setup and seed scripts are the exception).
6. **Wording:** findings say "anomaly for review" and never "fraud", "corrupt" or "illegal".
7. **No real personal data.** Sole-proprietor names are masked. Synthetic and planted cases use **fictional** suppliers only, and a real company never gets a fake score, bid or flag.
8. **Bounded runs.** Max 2 retries per loop, max 1 replan, about 40 LLM calls, under 10 minutes total. Every external call has a timeout.
9. **No hardcoded outputs.** Planted cases must be found by the same code that scans real data. `output_examples/` holds real saved outputs, never returned at runtime.

## 3. Repository layout

```text
app/                      # Python 3.11, owner: Joon Hao (orchestration)
  agents/                 # planner.py resolver.py analyst.py critic.py risk.py reporter.py
  orchestration/          # graph.py (LangGraph), state.py
  adapters/               # zetaris.py, nightshift.py, hmem_client.py
  checks/                 # red-flag runners that load sql/checks/*.sql
  schemas.py              # Finding, Match, TraceEvent (pydantic), see §7
  tracing.py              # JSONL writer, see §8
  api.py                  # FastAPI: POST /run, GET /runs/{id}
services/hmem/            # TypeScript H-MEM service, see §6
sql/
  register/               # Lightning SQL that registers sources in Zetaris (one statement per file)
  checks/                 # R1.sql R2.sql R3.sql R4.sql R8.sql ... (one red flag per file)
data/
  sample/                 # small curated CSV/Parquet + seed SQL (a few MB)
  eval/planted.json       # ground truth; agents NEVER read this
  eval/entity_labels.csv  # ~100 hand-labelled GeBIZ-to-ACRA pairs
  rules/                  # red_flags.yaml, mof_thresholds.yaml (owner: Joon Hao)
  ago/                    # AGO excerpts as text chunks (owner: Joon Hao)
  README.md               # sources, SODL licence, subset, counts, how to regenerate
scripts/                  # fetch_*.py, seed.py, register_zetaris.py, eval.py, smoke_test.py
web/                      # Next.js + shadcn UI
input_examples/  output_examples/  logs/
docker-compose.yml  .env.example  run.py  README.md  metadata.json
```

## 4. Ports and containers

| Thing | Address | Notes |
|---|---|---|
| Zetaris UI | `http://localhost:3000` | Zetaris owns port 3000, so **our web UI uses 3100** |
| Zetaris REST | `http://localhost:8888/api/v1.0` | `POST /sql-editor/sqls/run` |
| Nightshift runtime | `http://127.0.0.1:8088/v1` | Also auto-detects 8090, 8787 and 11434, so **avoid those ports** |
| Our Postgres | container `pi-postgres`; host `127.0.0.1:55432` | Joins Docker network `zetaris_default` |
| Our S3 (SeaweedFS) | container `pi-s3:8333`; host `127.0.0.1:18333` | MinIO's image is no longer public |
| H-MEM service | container `pi-hmem:7070`; host `127.0.0.1:7070` | TypeScript |
| FastAPI | `127.0.0.1:8000` | `POST /run` |
| Web UI | `127.0.0.1:3100` | |

All our containers join the **external** Docker network `zetaris_default`, so Zetaris can reach them by container name. This was verified on 21 Oct.

## 5. Environment variables (`.env.example`)

```bash
# Zetaris (local Docker)
ZETARIS_REST_URL=http://localhost:8888/api/v1.0
ZETARIS_ORG_ID=1
ZETARIS_API_KEY=your-zetaris-api-key
# Meterless Nightshift (copy URL + key from Nightshift Console)
METERLESS_BASE_URL=http://127.0.0.1:8088/v1
METERLESS_RUNTIME_TOKEN=your-nightshift-runtime-token
METERLESS_MODEL_DEEP=meterless/deep
METERLESS_MODEL_FAST=meterless/fast
METERLESS_APP_DEEP=procurement-integrity          # bound to "deep" in Console > Apps
METERLESS_APP_FAST=procurement-integrity-fast     # bound to "fast" in Console > Apps
# Our containers
POSTGRES_USER=pi
POSTGRES_PASSWORD=change-me
S3_ENDPOINT=http://pi-s3:8333
S3_BUCKET=pi-acra
HMEM_URL=http://127.0.0.1:7070
# Runtime
SAMPLE_MODE=true
MAX_RETRIES=2
LLM_CALL_CAP=40
SOURCE_TIMEOUT_SECONDS=20
```

**Nightshift binds one mode per app.** Requests are coerced to the app's mode in Console → Apps. So the deep lane (Planner, Risk, Reporter) sends `meterless-app: $METERLESS_APP_DEEP`, and the fast lane (Resolver tie-breaks, Critic) sends `$METERLESS_APP_FAST`. Every request also sends `meterless-scope: user` and `Authorization: Bearer $METERLESS_RUNTIME_TOKEN`. Use a 180 s timeout. Each response carries a `meterless` receipt; the tracer keeps `receipt_id`, `routed_model`, `latency_ms` and `egress`.

## 6. H-MEM service HTTP contract (TypeScript, `services/hmem/`)

The service is adapted from `engines/hmem/reference` in github.com/Meterless/Meterless (Apache-2.0). It is done when `HMEM_IMPL=/abs/path/services/hmem/src/index.ts npx tsx conformance/runner.ts` exits 0.

| Method + path | Request JSON | Response JSON |
|---|---|---|
| `GET /healthz` | – | `{"ok": true, "conformance": "pass" \| "unknown"}` |
| `POST /add` | `{content, type, layer, tags[], source, confidence, agentId, runId, entities[], meta{agency?, uen?, flag_id?, tender_no?}}` | `{id}` |
| `POST /query` | `{query, topN=5, filters{agency?, uen?, flag_id?}, agentId, runId}` | `{memories:[{id, content, score, meta, provenance}], trace{retrievalReason, strategy}}` |
| `POST /feedback` | `{memoryId, signal: "helpful" \| "not_helpful" \| "wrong", agentId, runId}` | `{ok, confidence}` |
| `POST /auditor-decision` | `{runId, finding_id, uen, flag_id, agency, decision: "confirm" \| "dismiss", reason, pattern_tag?, scope: "agency" \| "global"}` | `{memoryId}` (stored long_term) |
| `GET /ledger?runId=` | – | JSONL trust-ledger lines |

The service writes its trust ledger to `logs/hmem-ledger.jsonl`.

**Recall rules used by the Critic:**
- An exact match on (uen, flag_id, agency) with a `dismiss` decision suppresses the finding and cites the memory.
- The same `pattern_tag` at the same agency down-weights the finding.
- Memories never cross agencies unless `scope=global`.

## 7. Data contracts

### 7.1 Zetaris object names (created by `scripts/register_zetaris.py` from `sql/register/`)

| Source | Zetaris object | Backing store |
|---|---|---|
| S1 GeBIZ awards | datasource `gebiz_pg`, table `awards` | Postgres db `gebiz` |
| S3 rules | `gebiz_pg.rules` | Postgres db `gebiz` |
| S4 AGO chunks | `gebiz_pg.ago_chunks` | Postgres db `gebiz` |
| Crosswalk (Resolver output) | `gebiz_pg.supplier_xwalk` | Postgres db `gebiz` |
| S2 ACRA entities | lightning db `ACRA_FILES`, table `entities` | S3 `s3a://pi-acra/acra/entities.parquet` (CSV fallback) |
| S5 internal (synthetic) | datasource `internal_pg`: `bids`, `evaluations`, `coi_declarations` | Postgres db `agency_internal` |
| Semantic model | USL `procurement_usl` joining `awards` → `supplier_xwalk` → `entities` | – |

### 7.2 Table columns

- `awards(tender_no text, tender_description text, agency text, award_date date, tender_detail_status text, supplier_name text, awarded_amt numeric)`. GeBIZ gives dates as `d/m/yyyy`; parse them on load.
- `entities`: ACRA columns as published (`uen, entity_name, entity_type_description, entity_status_description, registration_incorporation_date, block, street_name, level_no, unit_no, building_name, postal_code, primary_ssic_code, primary_ssic_description, no_of_officers, former_entity_name1..15`). Sole proprietorships are kept for matching; their names are masked in the `public` role.
- `supplier_xwalk(supplier_name text, uen text null, confidence real, method text, candidates jsonb, resolved_at timestamptz)`. `method` is one of `exact | former_name | fuzzy | llm_tiebreak | unresolved | out_of_scope`.
- `rules(flag_id text, name text, params jsonb, source_url text)`
- `ago_chunks(chunk_id text, report text, fy text, section text, text text, embedding jsonb)`

### 7.3 Red-flag SQL output (`sql/checks/R*.sql`)

Every check returns rows with exactly these columns:

`flag_id, tender_no, agency, supplier_name, uen, award_date, awarded_amt, metric_name, metric_value, threshold, detail`

Parameters arrive as `{{agency}}`, `{{date_from}}` and `{{date_to}}`, which `app/checks` substitutes safely. Lightning SQL runs **one statement per call**, and REST returns **every value as a string**, so cast them in Python.

### 7.4 Python schemas (`app/schemas.py`)

```python
Match:   supplier_name, uen | None, confidence: float, method: str, candidates: list[dict]
Evidence: query_id (uuid we send to Zetaris), sql, row_count, rows (<=20), source_objects: list[str]
Finding: finding_id, flag_id, tender_no, agency, supplier_name, uen, summary, confidence,
         status: "accepted" | "escalated" | "rejected" | "suppressed",
         evidence: list[Evidence], ago_refs: list[str], memory_refs: list[str], wording_checked: bool
```

## 8. Trace format (`logs/<run_id>.jsonl`)

One line per agent step:

```json
{"timestamp":"...","trace_id":"run_...","agent_name":"CriticAgent","action":"validate_claims",
 "input_summary":"...","output_summary":"...","target_agent":"AnalystAgent","confidence":0.82,
 "retry_count":1,"status":"needs_revision","zetaris_query_ids":["..."],"meterless_receipt_id":"rcpt_..."}
```

`status` is one of `success | needs_revision | retrying | escalated | partial_success | failed`.

## 9. Red flags (definitions are owned by Joon Hao in `data/rules/red_flags.yaml`)

| ID | Priority | Flag |
|---|---|---|
| R1 | Must | Supplier incorporated less than 6 months before award date |
| R2 | Must | ACRA status struck off, ceased or in liquidation (status is current, not at award time) |
| R3 | Must | 2 or more distinct winning suppliers at the same agency share an exact address |
| R4 | Must | Same agency and supplier: 2 or more awards each below S$90k within 90 days, together above S$90k |
| R8 | Must | Name looks locally registered but has no ACRA match above threshold. Foreign firms and government bodies are labelled "outside registry scope" instead |
| R5 | Should | SSIC description far from tender description (embedding similarity); always escalated |
| R6 | Should | Supplier concentration within a category |
| R9 | Should | Winner not best-scored under published criteria (synthetic S5 only) |
| R7 | Stretch | Has former names (informational only) |

## 10. Timeline (SGT) and cut order

**Everything ships in three days, with full scope.** Our coding agents carry the volume.

| Day | Date (SGT) | By the end of the day |
|---|---|---|
| D1 | Thu 22 Oct, 08:00–24:00 | Real data queryable through Zetaris; an R1 memo produced end to end; H-MEM API up with conformance passing |
| D2 | Fri 23 Oct | Full system: all loops, H-MEM memory moment, all red flags, UI, evaluation numbers. **Feature freeze 23:59** |
| D3 | Sat 24 Oct | Clean-setup test, README, `metadata.json`, examples, video, deck. **Submit on HackOS by 20:00** |
| Buffer | Sun 25 to Tue 27 | Fixes and resubmits only. The hard deadline is 28 Oct, 07:45 SGT |

- **Cut order, only if a day slips:** R9 and S5, then R6, then R5, then Scout Intent, then World Model.
- **Never cut:** the Critic loop, H-MEM, Zetaris federation, the Nightshift-to-Nemotron path, or the evidence drawer.
