# Agent instructions: Joon Hao (lead, orchestration, integration, submission)

You are Claude Code working for **Joon Hao**, team lead and submission owner of the Procurement Integrity Investigator (Open Agent Hackathon 2026, Track 02). **Read `docs/agents/CONTRACTS.md` first. It overrides anything here that conflicts with it.** The team plan explains the *why*: https://claude.ai/code/artifact/33db073a-a6f9-4f3d-a817-8e02bf03c74c

Joon Hao's background: full-stack (Python, FastAPI, Next.js, TypeScript, Tailwind, Supabase), Docker, CI/CD with GitHub Actions, Grafana/Loki observability, security (CSP, secret scanning), and OSINT/forensics from CTFs. He owns **the agent graph, the sponsor adapters, tracing, the API, the UI, Docker Compose, integration, and the final submission**. **Since 22 Oct he also owns everything that was Rae's** (Rae is unavailable): the H-MEM TypeScript service, the red-flag rules and wording, AGO excerpts, planted cases (with Inchara), UI components, and the deck and demo script. See §8.

---

## 1. Working agreement (how you work for Joon Hao)

- **Stay inside this repo:** `/Users/joonh/Coding/Open Agent Hackathon 2026/[OhMyFally] Open Agent Hackathon'26`. Never edit, commit in, or run git against the parent `Coding` repo.
- **No product code committed before 22 Oct 2026, 08:00 SGT.** Docs and config are fine.
- **Commit and push:**
  - Commit after each verified step, using Conventional Commits and the attribution trailer the session gives you.
  - **Push only when Joon Hao says so.** The repo is meant to be public, and pushing publishes.
  - Never force-push to `main`.
- **Secrets:**
  - Read `.env` only through code that loads it; never print, echo or log a value.
  - Show variable names with values masked (`sed -E 's/=.*/=<set>/'`).
  - Never put the NVIDIA key in `.env`; it lives in Nightshift.
- **Verify before claiming.** Every "done" needs proof: a test run, a Zetaris `SELECT` result, a Nightshift receipt or the conformance output. If something fails, say so with the output.
- **Teammates' areas:**
  - Inchara owns `scripts/fetch_*`, `scripts/seed.py`, `app/resolver/`, `sql/checks/`, `data/eval/` and `scripts/eval.py` **from D2**. On D1 you build them (§9) and hand them over.
  - Don't rewrite their files. Propose changes, or fix only what blocks integration and tell Joon Hao.
- **Contracts:** don't change CONTRACTS.md on your own. Propose the change, and when it's agreed, update the doc in the same commit as the code.
- **Bound everything:** timeouts on every call, max 2 retries, max 1 replan, a 40-call LLM cap. Don't start long-running jobs without saying so.

## 2. Verified environment facts (20–21 Oct)

- **Zetaris:**
  - Runs locally (Docker network `zetaris_default`), with REST on `http://localhost:8888/api/v1.0`.
  - `POST /sql-editor/sqls/run` takes the headers `Authorization: Bearer`, `X-Org-ID` and `X-Request-ID` (UUID), and a body of `{queryId (UUID), sql, source:"SqlEditor", limit}`.
  - Replies look like `{"headers":[...], "data":[[...]], "total", "timeUsed"}` and **every value is a string**.
  - One statement per call.
- **Federation works:**
  - `CREATE DATASOURCE ... jdbcurl "jdbc:postgresql://<container>:5432/<db>"`, then `REGISTER DATASOURCE TABLE`.
  - `CREATE LIGHTNING DATABASE`, then `CREATE LIGHTNING FILESTORE TABLE ... OPTIONS (PATH "s3a://bucket/key", s3Endpoint "http://<container>:8333", useS3PathStyleAccess "true", inferSchema "true", header "true", AWSACCESSKEYID "...", AWSSECRETACCESSKEY "...")`.
  - A join across both sources worked, and Spark SQL functions such as `datediff` and `regexp_replace` work.
  - Remove objects with `DROP DATASOURCE`, `DROP LIGHTNING DATABASE TABLE` and `DROP LIGHTNING DATABASE`.
- **Storage:** MinIO's Docker image is no longer public; SeaweedFS `chrislusf/seaweedfs:3.80 server -s3` works as the S3 store.
- **Nightshift:**
  - OpenAI-compatible at `http://127.0.0.1:8088/v1`.
  - **Binds one mode per app:** `procurement-integrity` goes to the deep lane (Nemotron 3.5 Super, about 13 s on a trivial prompt, about 500 reasoning tokens), and `procurement-integrity-fast` goes to the fast lane (Nemotron lightning).
  - Responses include a `meterless` receipt; keep `receipt_id`, `routed_model`, `usage.latency_ms` and `egress`.
- **Smoke test:** the guide's `smoke_test.py` passed 3 of 3 on 21 Oct. Commit it as `scripts/smoke_test.py` on D1.

## 3. What you build (Joon Hao's outputs)

| Area | Path | Done when |
|---|---|---|
| Repo skeleton | layout in CONTRACTS §3, `requirements.txt` (Python 3.11), `.env.example`, `README.md` stub | `pip install -r requirements.txt` works in a fresh venv |
| Docker Compose | `docker-compose.yml` with `pi-postgres`, `pi-s3`, `pi-hmem`, all on the external network `zetaris_default` | `docker compose up -d` brings all three up healthy |
| Zetaris adapter | `app/adapters/zetaris.py`, `scripts/zsql.py` | `run_sql(sql) -> Result(headers, rows, query_id, ms)` with timeout, ≤2 retries, typed casting helpers; logged with `query_id` |
| Nightshift adapter | `app/adapters/nightshift.py` | `chat(lane="deep"\|"fast", messages, json_schema=None, max_tokens)` with the right `meterless-app` header, a 180 s timeout and receipt capture; JSON-mode parsing with one repair retry; enforces the global call cap |
| H-MEM client | `app/adapters/hmem_client.py` | Typed calls to CONTRACTS §6, plus a contract test against the running service |
| Tracing | `app/tracing.py` | JSONL in `logs/<run_id>.jsonl` (CONTRACTS §8), also streamed to the UI |
| Agent graph | `app/orchestration/`, `app/agents/` | LangGraph with the loops below, bounded |
| API and CLI | `app/api.py`, `run.py` | `python run.py --input input_examples/example_1.json` and `POST /run` both produce a memo and a trace |
| Zetaris registration and USL | `scripts/register_zetaris.py` plus `sql/register/` (with Inchara) | Idempotent: it drops and recreates our objects only, and creates the USL model `procurement_usl` |
| Web UI | `web/` (Next.js, port 3100) | Request bar, live timeline (SSE from the API), memo and evidence drawer, human-review queue, Confirm and Dismiss buttons calling `/auditor-decision` |
| Submission | `README.md`, `metadata.json`, `output_examples/`, `logs/`, video, HackOS form | Every item on the plan's submission checklist ticked |

## 4. Agent graph (LangGraph)

State holds the request, plan, matches, findings, critiques, retries, memory_refs and the LLM-call count.

1. **Gate:** a rules check (Scout Intent is a stretch goal). Reject out-of-scope requests and record the intent in the trace.
2. **Planner (deep):**
   - Reads the Zetaris catalog (`SHOW LIGHTNING DATABASES`, `SHOW DATASOURCES`), `rules`, and H-MEM recall for this agency.
   - Outputs a plan: which checks to run, the parameters, and which sources.
3. **Resolver (fast for tie-breaks):** calls Inchara's `resolve()` for unresolved supplier names and writes `supplier_xwalk`.
4. **Analyst:** for each check, substitutes parameters into `sql/checks/R*.sql`, runs it through Zetaris, and builds `Finding` objects whose evidence holds the `query_id`, SQL and up to 20 rows.
5. **Critic (fast):**
   - Re-runs the SQL behind each finding and confirms the cited rows exist. Mismatch sends it back to the Analyst (max 2 retries).
   - Rejects Resolver matches below the threshold, sending them back to the Resolver with a different strategy (max 2).
   - Queries H-MEM: an exact dismiss memory means `suppressed` with `memory_refs`.
   - Sends `helpful` / `not_helpful` feedback to H-MEM about the memories it used.
6. **Risk (deep):**
   - Applies `data/rules/wording.yaml`; a banned term sends the finding back to the Reporter.
   - Escalates low-confidence or should-have flags (R5) to human review.
   - Can request **one** replan when coverage is missing.
7. **Reporter (deep):**
   - Builds the ranked memo: summary, findings, confidence, limitations, and AGO citations from `ago_chunks`.
   - Every claim is tied to evidence.

Log every agent hop as a trace line. Put the Zetaris `query_id`s and the Meterless `receipt_id` on the line that used them.

## 5. Day-by-day

**Tonight (21 Oct):** no product code. Prep only: read CONTRACTS.md, confirm `.env` names, and draft the Compose file and adapter design in your head or in notes.

Everything ships by **Sat 24 Oct, 20:00 SGT**, with full scope. Sun 25 to Tue 27 are buffer only. Run work in parallel with subagents or extra sessions where the pieces are independent.

- [ ] **D1, Thu 22 (08:00 to midnight): three parallel streams.** Inchara is out today, so her D1 data work is ours (§9). Run streams B and C as separate sessions, each on its own branch or worktree, merging into `main` as each piece passes. File ownership never overlaps:
  - **A** (this session) owns `app/adapters/`, `app/orchestration/`, `app/agents/`, `app/schemas.py`, `app/tracing.py`, `app/api.py`, `run.py` and `docker-compose.yml`.
  - **B** owns `scripts/fetch_*`, `scripts/seed.py`, `scripts/register_zetaris.py`, `sql/`, `app/resolver/` and `data/`.
  - **C** owns `services/hmem/`.

  | Time (SGT) | A: core and agents (this session) | B: data pipeline (parallel session, §9) | C: H-MEM service (parallel session, §8.1) |
  |---|---|---|---|
  | **First hour, unblockers** | Repo skeleton, `requirements.txt`, `.env.example`, `docker-compose.yml` (`pi-postgres`, `pi-s3`, a stub `pi-hmem`), `scripts/zsql.py`, `scripts/smoke_test.py`. **Commit and push.** | GeBIZ quotation check (ETT against ETQ counts) and the agency shortlist; download the raw GeBIZ and ACRA CSVs into `data/raw/` | Copy the reference into `services/hmem/`; run conformance; it must pass before any change |
  | **To about 13:00** | Zetaris and Nightshift adapters, `schemas.py`, `tracing.py`; graph skeleton running against **recorded fixtures**, so it doesn't wait on data | `fetch_gebiz.py`, `fetch_acra.py`, `seed.py` (idempotent), `sql/register/` plus `register_zetaris.py`. **Milestone: `SELECT count(*)` works on `gebiz_pg.awards` and `ACRA_FILES.entities`.** Push | File persistence; `src/server.ts` HTTP API (CONTRACTS §6) |
  | **To about 18:00** | Switch the skeleton to live data. Walking skeleton: request → Planner → Analyst runs **R1** → Reporter memo in `logs/` | **Resolver pass 1** (exact and former-name only) fills `supplier_xwalk`, which R1 joins through; then **`sql/checks/R1.sql`, pushed** (A needs it); then `red_flags.yaml` and `mof_thresholds.yaml`; then R2, R3, R4 and R8; then Resolver pass 2 (fuzzy and LLM tie-break) | Dockerfile, replacing the `pi-hmem` stub in Compose (coordinate the one edit with A); HTTP tests; conformance still passing, saved to `logs/evidence/` |
  | **To midnight** | LangGraph state and the first Critic loop; Resolver agent around `resolve()`; R2–R4 and R8 through the Analyst; `POST /run` and `run.py`; `wording.yaml` | `planted.json` (fictional cases) injected by `seed.py`; every check catches its planted case; write `docs/handover/d1-data.md` for Inchara | AGO chunks, `data/ago/` (§8.2), once H-MEM is done |

  **Nothing blocks A:**
  - A builds against fixtures until B's 13:00 milestone.
  - R1 SQL is B's first check. It needs `supplier_xwalk`, so the deterministic Resolver pass comes right before it, about 30 minutes after registration.
  - Until the YAML exists, the red-flag definitions come from CONTRACTS §9.
  - H-MEM isn't needed by A until D2.

  **Midnight check:** real data queryable through Zetaris, an R1 memo produced end to end, the H-MEM API up with conformance passing, and the handover note written.
- [ ] **D2, Fri 23 (feature freeze 23:59):**
  - Agents:
    - Critic retries and evidence re-checks;
    - the Risk agent, with `wording.yaml` and one replan;
    - the H-MEM client wired in, with the Planner and Critic using recall;
    - the `/auditor-decision` flow and the demo memory moment end to end;
    - Reporter AGO citations.
  - Zetaris:
    - the USL model `procurement_usl`;
    - masking roles (`auditor` / `public`). Research the syntax first; if it isn't feasible, pseudonymise in the API and say so honestly.
  - Measure tokens with Zetaris pushdown against a naive baseline.
  - Replay mode: re-serve recorded Zetaris and Nightshift responses from `logs/` when `SAMPLE_MODE` is set and a service is down, clearly labelled.
  - Web UI: timeline (SSE), memo, evidence drawer and human-review queue, with Confirm and Dismiss (§8.3).
  - Deck v1 and demo script (§8.3).
  - Evening: hand-review the top 30 real flags with Inchara.
- [ ] **D3, Sat 24 (submit by 20:00):**
  - 09:00–13:00:
    - clean-setup test on a fresh clone, and fixes;
    - `README.md` covering setup, usage, dependencies, Track 02, the sponsor explanation and limitations;
    - `metadata.json` saying where Zetaris sits and which Meterless engines are used where;
    - 3 or more `input_examples/` with their real `output_examples/`;
    - TruffleHog in CI.
  - 13:00–17:00: final deck, then record and edit the video (Inchara helps with the metrics segment). Follow the demo script and keep it to 2:30–3:30.
  - 17:00–20:00:
    - final pass over the submission checklist;
    - confirm the roster first, because the team locks when the submission is created;
    - **submit on HackOS by 20:00 SGT**.

## 6. Known gaps and decisions to remember

- **No direct NVIDIA fallback.** The setup guide says the NVIDIA key must never be in the app's `.env`. If Nightshift is down, the fallback is replay mode, not build.nvidia.com. (The plan doc was corrected on 21 Oct.)
- **Parquet hasn't been tested** in Zetaris; only CSV over S3 has. If Parquet fails, use CSV.
- **Unconfirmed:** whether GeBIZ includes quotations (affects R4). Inchara checks tonight.
- **Unconfirmed:** whether Zetaris supports MCP and how its masking roles work. Don't build on either until verified.
- **Deep-lane latency** is about 13 s per call, so batch calls, run them in parallel where safe, cap `max_tokens`, and default to the fast lane.

## 7. Definition of done for the whole project

A judge with Zetaris and Nightshift running can:
1. clone the repo, copy `.env.example` to `.env` and fill in 3 values;
2. run `docker compose up -d`, `python scripts/seed.py` and `python scripts/register_zetaris.py`;
3. run `python run.py --input input_examples/example_1.json` and get a ranked memo in under 10 minutes;
4. find `logs/<run_id>.jsonl` showing the Critic rejecting something, a retry, an escalation, Zetaris query IDs and Nemotron receipts;
5. confirm that a second run after a dismissal suppresses the dismissed finding and cites H-MEM.

## 8. Scope taken over from Rae (22 Oct)

### 8.1 H-MEM service: build guide

**Goal:** a memory service that the Python agents call over HTTP and that passes the official Meterless H-MEM conformance suite. That suite only runs TypeScript, which is why this service is in TypeScript.

#### D1 morning (Thu 22). Best run as a separate parallel session, since it's independent of the agent graph
1. Pull the reference into the repo:
   ```bash
   npx degit meterless/meterless/engines/hmem services/hmem-upstream
   ```
   Copy `reference/` into `services/hmem/` and keep `services/hmem-upstream/conformance/` for testing. Keep the Apache-2.0 `LICENSE` and add a `NOTICE` saying it was adapted from Meterless.
2. Run the suite against the unmodified copy and confirm it is green **before changing anything**:
   ```bash
   cd services/hmem && npm install
   HMEM_IMPL="$(pwd)/src/index.ts" npx tsx ../hmem-upstream/conformance/runner.ts
   ```
   Save the output to `logs/evidence/hmem-conformance-d1.txt`.
3. Read `engines/hmem/AGENTS.md` §2 (memory record), §8 (reinjection) and §11 (trust ledger). Ignore dreaming and sleep for now.
4. Find how the reference stores data. If it is in-memory only, add file-backed persistence (a JSON or SQLite file under `services/hmem/state/`, mounted as a Docker volume). Memory **must survive a restart**, because the demo relies on run 2 remembering run 1.

#### D1 afternoon to midnight (Thu 22)
5. Add `src/server.ts`, a small HTTP server (Hono or Express) that imports the `HMEM` class from `src/index.ts`. `src/index.ts` must keep exporting `HMEM` unchanged, so the conformance suite keeps working.
6. Implement every endpoint in CONTRACTS §6. Map them like this:
   - `/add` → `hmem.add(...)`, with `agentId`, `runId` and `meta` stored on the record (tags or fields).
   - `/query` → `hmem.query(...)`, then apply the `filters` and return the trace metadata.
   - `/feedback` → `hmem.feedback(...)`.
   - `/auditor-decision` → a **long_term** memory with provenance `origin: "auditor"`, the reason as content, and `meta` holding uen, flag_id, agency, pattern_tag and scope.
   - `/ledger` → stream the trust ledger, and also append every ledger event to `logs/hmem-ledger.jsonl`.
7. Add `Dockerfile` plus a `docker-compose.yml` service `pi-hmem` on port 7070, on network `zetaris_default`, with a volume for `state/`.
8. Re-run conformance after your changes and save `logs/evidence/hmem-conformance-d1-final.txt`. **It must stay green.**
9. Write `services/hmem/test/http.test.ts`. Cover:
   - add, then query returns it;
   - an auditor-decision dismiss is recalled by an exact (uen, flag_id, agency) filter;
   - a memory from another agency is **not** returned unless `scope=global`;
   - the memory survives a restart.

#### D2 (Fri 23)
10. Wire `app/adapters/hmem_client.py` to the API. Fix any contract mismatches, and update CONTRACTS.md in the same commit.
11. Prove the demo moment end to end: run 1 flags X → the auditor dismisses it with a reason → run 2 suppresses X and cites the memory ID.

**Using the Meterless prompt:** at meterless.ai/engines.html, choose IMPLEMENT → **"Give my agent memory"**, paste it into your coding agent, and add: *"Target is `services/hmem/` (already adapted from the reference). Keep `src/index.ts` exporting `HMEM` so the conformance suite still runs. Expose it via the HTTP contract in `docs/agents/CONTRACTS.md` §6."*

### 8.2 Domain outputs

#### Red-flag definitions (draft tonight, final on D1)
For each of R1–R9 (CONTRACTS §9), write it in `red_flags.yaml`:

```yaml
- flag_id: R4
  name: Possible contract splitting
  logic: Same agency and supplier; >=2 awards each < 90000 SGD within 90 days, summing > 90000
  params: {threshold_sgd: 90000, window_days: 90, min_awards: 2}
  priority: must
  limitation: Needs GeBIZ quotation records; tenders-only data under-detects
  why_it_matters: AGO FY2024/25 found ... (cite)
  source_url: https://mof.gov.sg/policies/government-procurement/procurement-process
```

Also put the MOF thresholds (S$6k / S$90k) in `mof_thresholds.yaml`, with the source URL.

#### Wording rules (D1)
`wording.yaml` lists:
- banned terms: fraud, corrupt, illegal, criminal, guilty, scam;
- required phrasing: "anomaly for review", "may indicate", "requires auditor judgement";
- a one-line disclaimer for the UI and the memo.

The Risk agent rejects any finding text containing a banned term.

#### AGO excerpts (tonight and D1)
Take procurement chapters from 3–5 AGO annual reports (FY2021/22 to FY2024/25). Chunk them into roughly 150–300-word sections. In `index.csv`, record `chunk_id, report, fy, section, page, url`. Quote only; don't paraphrase into new claims.

#### Planted cases (D1, with Inchara)
Write `planted.json` entries like this:

```json
{"case_id":"P1","flags":["R1"],"agency":"<sample agency>","supplier":"ZYLOQ TEST ENGINEERING PTE. LTD.",
 "uen":"T99ZZ0001A","award":{"tender_no":"PLT000ETT25000001","awarded_amt":400000,"award_date":"2025-06-20"},
 "acra":{"incorporation_date":"2025-05-30","status":"Live Company","postal_code":"999001"},"expected":"flag R1"}
```

Inchara's seed script injects them.

### 8.3 Product, UX and pitch

- **Figma (tonight):** one screen with a request bar, a live run timeline and a review memo with evidence drawer, plus a human-review queue tab. Use shadcn defaults; a quick sketch is enough, or skip Figma and build straight in code.
- **UI (D2):** build the components in `web/components/` against the `Finding` schema in CONTRACTS §7.4, using mock JSON from `output_examples/` until the API is live. The web UI runs on **port 3100**.
- **Deck (v1 on D2, final on D3):** problem and users, solution, architecture (reuse the plan diagram), stack, Zetaris and Meterless use, what was unique (the Critic re-queries Zetaris to verify every claim, the USL crosswalk, auditor memory in H-MEM), product visuals, future work.
- **Demo script (D2):** follow the 6 segments in the plan doc. Keep it to 2:30–3:30.

## 9. Data pipeline: Inchara's D1 work, done by Joon Hao (stream B, 22 Oct)

Inchara is unavailable on D1. Follow `docs/agents/inchara.md` §1–3 for rules and verified facts. The D1 steps are:

### 9.0 First hour (stream B)
- [ ] **Check whether GeBIZ includes quotations.** Count `tender_no` patterns, ETT (tender) against ETQ (quotation), with the datastore API. Record the counts in the handover note, because R4 depends on it.
- [ ] Pick 2–3 agencies with enough awards, a mix of values, and some sub-S$90k repeat suppliers. Record the shortlist in the handover note.
- [ ] Download the raw GeBIZ and ACRA CSVs into `data/raw/` (gitignored; data only, no code).

### 9.1 To about 13:00: data queryable through Zetaris
1. `fetch_gebiz.py`: pull awards for the chosen agencies, parse dates, and write `data/sample/awards.csv`.
2. `fetch_acra.py`: build the candidate subset. Normalise names (upper case, strip punctuation, drop PTE/LTD/PRIVATE/LIMITED/LLP). Keep every ACRA entity that shares the first 1–2 significant tokens with any supplier, by current or former name. Write `data/sample/acra_entities.parquet` (pyarrow), with a CSV copy as fallback.
3. `seed.py`:
   - create DBs `gebiz` and `agency_internal` in `pi-postgres`;
   - load `awards`, `rules` (from `data/rules/` YAML) and `ago_chunks` (from `data/ago/`);
   - create an empty `supplier_xwalk`;
   - upload the ACRA file to `s3://pi-acra/acra/`.
   It must be **idempotent**: running it twice gives the same state.
4. Write `sql/register/` and `scripts/register_zetaris.py` (idempotent: it drops and recreates our objects only) and register the sources. Confirm both `SELECT count(*)` queries through Zetaris.

### 9.2 Afternoon to midnight: Resolver, red-flag SQL, planted cases
5. Resolver `app/resolver/match.py`, in **two passes**. Pass 1 (layers 1–2) runs **before R1**, because R1 joins through `supplier_xwalk`. Pass 2 (layers 3–5) runs after the checks are in. Apply these layers in order and record the `method`:
   1. `exact` on the normalised name
   2. `former_name` match
   3. `fuzzy`: `rapidfuzz` token_set_ratio with blocking on the first token; ≥ 92 counts as a match, 80–92 is ambiguous
   4. ambiguous top 3 goes to `llm_tiebreak` through the **fast** Nightshift lane, about 20 suppliers per call, returning JSON
   5. otherwise `unresolved`. Names without a local suffix (foreign firms, government bodies) are `out_of_scope`.

   Write the results to `supplier_xwalk`. Expose `resolve(names) -> list[Match]` (CONTRACTS §7.4) so the Resolver agent can call it and retry a different strategy when the Critic rejects a match.
6. (The labelled set moves to Inchara on D2. It doesn't block anything on D1.)
7. Red-flag SQL. Write **R1 first, right after Resolver pass 1, and push it**, because stream A needs it; then R2, R3, R4 and R8. Write `data/rules/red_flags.yaml` from CONTRACTS §9 alongside:
   - `awards` joins to `supplier_xwalk` on supplier_name, and `supplier_xwalk` joins to `entities` on uen;
   - output columns exactly as in CONTRACTS §7.3;
   - use `{{agency}}`, `{{date_from}}` and `{{date_to}}` placeholders;
   - Spark SQL functions: `datediff`, `date_add`, window functions for R4.
8. Write `planted.json` (fictional suppliers only; format in §8.2), and make `seed.py` inject the fictional rows into awards, entities and (for R9) agency_internal. Then run each check and confirm its planted case appears.

### 9.3 End of D1: handover
Write `docs/handover/d1-data.md`, covering:
- the agencies chosen and the quotation-check result;
- row counts per table;
- how to reseed and re-register;
- Resolver method counts (exact, former_name, fuzzy, llm_tiebreak, unresolved, out_of_scope);
- known weaknesses;
- open TODOs for Inchara.
