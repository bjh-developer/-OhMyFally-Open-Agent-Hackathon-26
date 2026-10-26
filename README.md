# ProcureLens

**Open Agent Hackathon 2026 · Track 02: The Agent That Can Explain Why · Team OhMyFally**

ProcureLens (the code calls it the *Procurement Integrity Investigator*) helps an **agency internal auditor** answer one
question: *which of our procurement awards in this period need a closer look, and why?*

Auditors sample today: the Auditor-General's reports say audits are done on a test-check basis and do not reveal all
irregularities, while GeBIZ lists S$123.8 billion of tender awards from 113 agencies in FY2021/22 to FY2025/26. A team of agents
checks **every** award in a period against the ACRA company registry and agency records through Zetaris, and **explains each
result**: every item cites the Zetaris query and source rows behind it, the red-flag rule that fired, and an Auditor-General
excerpt on why the pattern matters.

> **Wording.** Everything ProcureLens produces is an **"anomaly for review"**, never a finding of fraud or wrongdoing.
> A human auditor decides. See [Limitations and responsible AI](docs/limitations.md).

| | |
|---|---|
| **Input** | An agency, a date range, optionally a list of red flags ([input_examples/](input_examples/)) |
| **Output** | A ranked review memo (JSON and Markdown), a JSONL trace of every agent step, and a run summary |
| **Entry points** | CLI `run.py`, HTTP API `run.py --serve` (`POST /run`), web UI in `web/` (port 3100) |

## Try it in two minutes (no keys, no services)

```bash
docker compose up --build api web
```

The first build takes a few minutes. Open **http://localhost:3100**, choose *Housing and Development Board*, keep *FY2024/25*
and press **Start review**: the live agent timeline, ranked results, evidence and the *Technical view* all work offline, marked
**Recorded data**. The API is on port 8000:

```bash
curl -X POST http://localhost:8000/run -H "Content-Type: application/json" -d @input_examples/example_1.json
```

Without Docker (Python 3.11): `pip install -r requirements.txt`, then
`SAMPLE_MODE=true python run.py --input input_examples/example_1.json`.

**Offline is honest, not faked.** It replays live-recorded Zetaris rows and Nightshift replies for the five recorded requests in
`input_examples/`; the agents, rules, Critic and Reporter really run. Replayed ids start with `replay:`, the memo says so, and any
other request is refused with the list of what is recorded. With real keys in `.env` the same commands run live.
Details: [How SAMPLE_MODE works](docs/sample-mode.md). **Full live setup** (Zetaris, Nightshift, data loading), Docker notes,
configuration and tests: [docs/setup.md](docs/setup.md).

## How it works

```mermaid
flowchart TD
    START([request]) --> gate[Gate]
    gate -- "rejected: bad scope or unrecorded offline request" --> END([end])
    gate --> planner[Planner]
    planner --> resolver[Resolver]
    resolver --> plan_review["Critic: plan review"]
    plan_review -- "replan (once)" --> planner
    plan_review --> analyst[Analyst]
    analyst --> critic[Critic]
    critic -- "revise a check (max 2 per flag)" --> analyst
    critic -- "weak supplier match (max 2)" --> resolver
    critic --> risk[Risk]
    risk -- "replan (once)" --> planner
    risk --> reporter[Reporter]
    reporter --> END
```

| Agent | What it does |
|---|---|
| **Gate** | Rejects malformed or out-of-scope requests |
| **Planner** | Chooses the checks; reads the Zetaris catalog and past auditor decisions from H-MEM |
| **Resolver** | Links GeBIZ supplier names to ACRA companies (exact, former name, fuzzy, then a model tie-break) |
| **Analyst** | Runs one federated SQL check per red flag through Zetaris; each row becomes a finding with its evidence |
| **Critic** | Re-runs each check in Zetaris to reproduce the cited row, rejects weak supplier matches, recalls H-MEM, reviews shared addresses, and asks the model whether each summary is supported |
| **Risk** | Enforces the wording rules, escalates uncertain items to a human, scores priority |
| **Reporter** | Writes the ranked memo with Auditor-General citations |

Every loop is bounded: at most 2 retries per flag, 1 replan and 40 model calls per run, with a timeout on every external call.
Agent details, the loops and the trace format: [docs/architecture.md](docs/architecture.md).

**Red flags** ([full table](docs/red-flags.md)): R1 new company · R2 inactive company · R3 shared address · R4 possible contract
splitting (partial: no quotation data) · R5 business type far from the tender · R6 supplier concentration · R8 not in the registry ·
R9 not the best-scored bidder (synthetic records only). R7 is defined but not implemented.

## Sponsor technology

Full explanation: [docs/sponsor-tech.md](docs/sponsor-tech.md).

**Zetaris is the data layer.** All agent data access goes through its REST SQL endpoint. One statement joins GeBIZ awards,
rules and the supplier crosswalk in Postgres with the ACRA registry stored as Parquet on S3, plus synthetic agency records. The
Critic re-queries Zetaris to reproduce every finding and to count the companies at a shared address. Pushing joins down to
Zetaris means the model sees only flagged rows: about **3.0x fewer prompt tokens** than a naive dump (estimated,
[token_savings.json](output_examples/token_savings.json)). A USL model `procurement_usl` is registered and demonstrated.

**Meterless H-MEM is the engine we implemented**, as a TypeScript service in [services/hmem/](services/hmem/) adapted from the
Meterless reference (Apache-2.0). It powers auditor memory: *Confirm* and *Dismiss* are stored as long-term memories, so the next
run's Critic clears a finding the auditor already dismissed and cites the memory id. The official conformance suite passes
**13/13** ([evidence](logs/evidence/hmem-conformance-d1-final.txt)), plus 21 unit and HTTP tests:

```bash
cd services/hmem && npm install
HMEM_IMPL="$(pwd)/src/index.ts" npx tsx ../hmem-upstream/conformance/runner.ts
```

**Meterless Nightshift is the only AI provider.** Every model call goes through its OpenAI-compatible endpoint, with no provider
key in the app. Two Nightshift apps give two lanes: deep (Planner, Risk, Reporter) and fast (Critic, Resolver tie-break). Each
trace line keeps the receipt id, the routed model, latency and egress.

**NVIDIA Nemotron does the reasoning.** Every model call in the four saved live traces was answered by
`nvidia/nemotron-3.5-super-vl-120b-a12b`, logged per call.

**What is unique:** Zetaris is the evidence trail (the Critic reproduces each finding before it reaches the memo); registry
density decides escalation; auditor memory changes the next report; and offline mode replays real recordings through the same
agents, labelled everywhere. **Cursor** was not used; the rules allow any coding tool.

## Traces

Every run writes `logs/<run_id>.jsonl` and prints one line per agent step: agent, action, status, target agent, Zetaris query ids,
Nightshift receipt and routed model. `GET /runs/{run_id}/summary` returns critiques, retries, escalations, loops and memory use.
[output_examples/example_4.trace.jsonl](output_examples/example_4.trace.jsonl) is a live run where the Critic sends work back to
the Analyst and the Resolver. Field list and examples: [docs/architecture.md](docs/architecture.md#traces-and-logs).

## Results

| Measure | Result |
|---|---|
| Planted test cases caught | 8 of 8 (15 of 15 awards), fictional companies, before the Critic |
| Resolver accuracy | 100 of 100 labelled names (in-sample, agent-reviewed labels) |
| Precision on real awards | **9.5% → 28.6%**: after a human review of 30 flags we fixed three noise patterns with general rules and re-measured on a fresh sample. "Plausible" means worth a look, not wrongdoing |
| Tests | 155 Python tests (132 run with no services), web tests, H-MEM conformance; CI runs a TruffleHog secret scan and the tests |

Method, scope and caveats: [docs/evaluation.md](docs/evaluation.md).

## Data and licences

GeBIZ awards and the ACRA registry from data.gov.sg (Singapore Open Data Licence v1.0), Auditor-General report excerpts with page
links, and fictional planted cases. *Contains information from GeBIZ and the ACRA register, accessed via data.gov.sg under the
Singapore Open Data Licence v1.0.* The committed ACRA sample is minimised for privacy, and the API offers a pseudonymised public
view. Details: [docs/data-and-privacy.md](docs/data-and-privacy.md).

## Limitations

- R4 is partial: the open GeBIZ data has no quotation records. ACRA status is today's, not the status at award time.
- Flags are leads: SQL-stage precision is 28.6% on a reviewed sample; R5 and R6 are uncalibrated and R9 uses synthetic records.
- Offline mode covers the five recorded requests only. Live runs take 1 to 5 minutes; Nightshift 499/502 errors fall back to rule-based text.
- A prototype: no API authentication, single node. Human review is always required.

Full list and responsible-AI measures: [docs/limitations.md](docs/limitations.md).

## Pre-existing components

The H-MEM reference implementation (Meterless, Apache-2.0), open-source libraries, public datasets and container images. Our
work began on 22 October 2026; earlier commits hold only planning docs and agent instructions. Details and the repository layout:
[docs/project-info.md](docs/project-info.md).

## Team

**OhMyFally**: **Joon Hao** (lead: agents, orchestration, adapters, API, web UI, H-MEM service, rules, replay mode) and
**Inchara** (data pipeline, entity Resolver, red-flag SQL, evaluation). Rae: absent with apologies.
