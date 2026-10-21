# Agent instructions: Joon Hao (lead, orchestration, integration, submission)

You are Claude Code working for **Joon Hao**, team lead and submission owner of the Procurement Integrity Investigator (Open Agent Hackathon 2026, Track 02). **Read `docs/agents/CONTRACTS.md` first. It overrides anything here that conflicts with it.** The team plan explains the *why*: https://claude.ai/code/artifact/33db073a-a6f9-4f3d-a817-8e02bf03c74c

Joon Hao's background: full-stack (Python, FastAPI, Next.js, TypeScript, Tailwind, Supabase), Docker, CI/CD with GitHub Actions, Grafana/Loki observability, security (CSP, secret scanning), and OSINT/forensics from CTFs. He owns **the agent graph, the sponsor adapters, tracing, the API, the main UI, Docker Compose, integration, and the final submission**.

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
  - Rae owns `services/hmem/`, `data/rules/`, `data/ago/`, `web/components/` and `docs/pitch/`.
  - Inchara owns `scripts/fetch_*`, `scripts/seed.py`, `app/resolver/`, `sql/checks/`, `data/eval/` and `scripts/eval.py`.
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
| Web UI | `web/` (Next.js, port 3100) | Request bar, live timeline (SSE from the API), memo using Rae's components, Confirm and Dismiss buttons calling `/auditor-decision` |
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
   - Applies Rae's `wording.yaml`; a banned term sends the finding back to the Reporter.
   - Escalates low-confidence or should-have flags (R5) to human review.
   - Can request **one** replan when coverage is missing.
7. **Reporter (deep):**
   - Builds the ranked memo: summary, findings, confidence, limitations, and AGO citations from `ago_chunks`.
   - Every claim is tied to evidence.

Log every agent hop as a trace line. Put the Zetaris `query_id`s and the Meterless `receipt_id` on the line that used them.

## 5. Day-by-day

**Tonight (21 Oct):** no product code. Prep only: read CONTRACTS.md, confirm `.env` names, and draft the Compose file and adapter design in your head or in notes.

- [ ] **D1, 22 Oct (from 08:00).** Commit the skeleton, Compose, `.env.example`, `scripts/smoke_test.py` and `scripts/zsql.py`. Write the Zetaris and Nightshift adapters with tests against recorded fixtures. Register S1 and S2 with Inchara. **Walking skeleton:** request → Planner → Analyst runs R1 → Reporter JSON, written to `logs/`. Help Rae get `pi-hmem` into Compose.
- [ ] **D2, 23 Oct.** The Critic loop with real retries; the Resolver agent around `resolve()`; R2–R4 via the Analyst; `POST /run` and `run.py`; replay mode, which re-serves recorded Zetaris and Nightshift responses from `logs/` when `SAMPLE_MODE` and a service is down, clearly labelled.
- [ ] **D3, 24 Oct.** The Risk agent and replan; the H-MEM client wired in, with the Planner and Critic using recall; the `/auditor-decision` flow; the demo memory moment working end to end. The USL model. The web UI timeline and memo.
- [ ] **D4, 25 Oct.** AGO citations in the Reporter. Measure tokens with Zetaris pushdown against a naive baseline that dumps raw rows into the prompt. Zetaris masking roles (`auditor` / `public`); research the syntax first, and if it's not feasible, pseudonymise in the API and say so honestly. **Feature freeze 23:59.**
- [ ] **D5, 26 Oct.**
  - Clean-setup test on a fresh clone.
  - `README.md` covering setup, usage, dependencies, Track 02, the sponsor explanation and limitations.
  - `metadata.json` saying where Zetaris sits and which Meterless engines are used where.
  - 3 or more `input_examples/` and their real `output_examples/`.
  - TruffleHog in CI.
- [ ] **D6, 27 Oct.**
  - Record and edit the video with Rae; follow the demo script in the plan and keep it to 2:30–3:30.
  - Final pass over the submission checklist.
  - **Submit on HackOS by 22:00 SGT.**
  - Confirm the roster before creating the submission, since the team locks then.

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
