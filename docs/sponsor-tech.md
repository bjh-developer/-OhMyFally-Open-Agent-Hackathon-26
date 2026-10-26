# Sponsor technology explanation

Part of the [ProcureLens README](../README.md).

## Zetaris: the data layer

All data access goes through Zetaris ([app/adapters/zetaris.py](../app/adapters/zetaris.py), `POST /sql-editor/sqls/run`). The only
direct database access is in the setup scripts that load the data.

- **Federated SQL over two kinds of store.** Zetaris sees `gebiz_pg` (Postgres: `awards`, `rules`, `ago_chunks`, `supplier_xwalk`),
  `internal_pg` (synthetic bids, evaluations and conflict-of-interest declarations) and `ACRA_FILES.entities` (the ACRA registry as
  Parquet on S3). A check such as R1 is a single statement that joins Postgres awards, the crosswalk and the S3 Parquet registry
  ([sql/checks/R1.sql](../sql/checks/R1.sql)); registration lives in [sql/register/](../sql/register/) and `scripts/register_zetaris.py`.
- **USL model `procurement_usl`.** A Unified Semantic Layer model in the namespace `lightning.metastore.procurement` links
  `award` to `supplier_xwalk` to `supplier_registry` with foreign keys, plus a flat `award_profile` table. Be precise about its role:
  it is registered and verified by `register_zetaris.py` and demonstrated in [scripts/usl_demo.sql](../scripts/usl_demo.sql); the
  agents' red-flag SQL queries the registered sources directly.
- **The Critic re-queries Zetaris to verify its own claims.** For each flag it re-runs the check SQL and confirms the cited row is
  reproduced, then appends a fresh evidence entry with the new query id. A second Zetaris query measures R3 address density.
- **Pushdown saves tokens.** Joins and filters run in Zetaris, so the model sees only flagged rows. From
  [output_examples/token_savings.json](../output_examples/token_savings.json) (HDB FY2024/25, recorded live run):

  | | Rows | Characters | Estimated tokens |
  |---|---|---|---|
  | Pushdown: what the 8 model calls actually received | flagged rows only | 47,909 | 11,977 |
  | Naive: dump the joined awards x crosswalk x ACRA rows once | 278 rows, 36 columns | 145,115 | 36,279 |

  That is about **3.0x fewer tokens (67%)**. Tokens are estimated as characters / 4, not counted by a tokenizer; the provider
  reported 27,837 prompt tokens for the pushdown calls, so the ratio rests on the estimate for both sides. The naive figure is a
  lower bound (one dump, no instructions). The sample is a few hundred joined rows, so the gap would widen on the full registry.
  See the caveats in the file.
- **Masking.** The local Zetaris (2.4.x) has only table and namespace grants, no column masking, so the public view is
  implemented in the API ([Privacy](data-and-privacy.md)).

## Meterless H-MEM: auditor memory

The Meterless engine we implemented is **H-MEM**. It is a TypeScript service in [services/hmem/](../services/hmem/), adapted from the
Meterless reference implementation (`engines/hmem/reference` in github.com/Meterless/Meterless), which is licensed Apache-2.0. The
`LICENSE` is kept and [services/hmem/NOTICE](../services/hmem/NOTICE) lists our changes: file-backed persistence so memory survives a
restart, an HTTP server (`src/server.ts`) with `/healthz`, `/add`, `/query`, `/feedback`, `/auditor-decision` and `/ledger`, a
Dockerfile, and HTTP tests. `src/index.ts` still exports `HMEM`, so the official suite runs against it unchanged.

**The feature it powers.** An auditor presses *Confirm* or *Dismiss* on a finding. The decision is stored in H-MEM as a long-term
memory tagged with the agency, UEN and flag. On the next run:

- the **Critic** recalls memories for each accepted finding and **suppresses** one that the auditor already dismissed (exact
  agency, UEN and flag), citing the memory id in the finding, or lowers the confidence of a dismissed pattern;
- the **Planner** recalls memories for the agency and records how many it used.

H-MEM keeps an append-only trust ledger (`GET /ledger`, mirrored to `logs/hmem-ledger.jsonl`). The HTTP contract is in
[docs/agents/CONTRACTS.md](../docs/agents/CONTRACTS.md) section 6.

**The test.** Run the official conformance suite against our implementation:

```bash
cd services/hmem && npm install
HMEM_IMPL="$(pwd)/src/index.ts" npx tsx ../hmem-upstream/conformance/runner.ts
```

Result on 23 Oct: **13/13 checks passed** (saved in [logs/evidence/hmem-conformance-d1-final.txt](../logs/evidence/hmem-conformance-d1-final.txt);
the run on the unmodified reference is in `hmem-conformance-d1.txt`). The same suite runs when the `pi-hmem` image is built, and
`GET /healthz` reports `conformance: pass` only if it did. `npm test` in `services/hmem` runs 21 more tests (10 unit, 11 HTTP), all passing.

If H-MEM is down, runs continue without memory and the trace says so (`memory_skipped`). It is never fatal.

## Meterless Nightshift: the AI provider

Every model call goes through Nightshift's OpenAI-compatible `POST /v1/chat/completions`
([app/adapters/nightshift.py](../app/adapters/nightshift.py)). There is no direct provider call and no NVIDIA key in this project.

| | Deep lane | Fast lane |
|---|---|---|
| Nightshift app (header `meterless-app`) | `procurement-integrity` | `procurement-integrity-fast` |
| Model name sent | `meterless/deep` | `meterless/fast` |
| Used by | Planner, Risk, Reporter | Critic claim check, Resolver tie-break |

Each request sends `Authorization: Bearer <runtime token>`, `meterless-app` and `meterless-scope: user`. Every response carries a
`meterless` receipt; the tracer keeps the receipt id, the `routed_model`, the latency and a trimmed egress record
(`destination`, `coverage`, sizes) on the trace line. Replies are validated against a JSON schema with one repair retry, and
timeouts, 429, 499 and 5xx are retried a bounded number of times. A failed call degrades that agent to its rule-based fallback.

## NVIDIA: Nemotron through Nightshift

In the four saved live traces, every model call was routed to **`nvidia/nemotron-3.5-super-vl-120b-a12b`**, on both lanes:
the Planner (deep), Critic claim check (fast), Risk scoring (deep) and Reporter narrative (deep). The `routed_model` field on each
trace line is the evidence. The Resolver's fast-lane tie-break is not in those traces because it runs in the setup passes; the
handover note [docs/handover/d1-data.md](../docs/handover/d1-data.md) (section 8) records one, receipt `rcpt_req_6u2qusst`, routed to
`nvidia/nemotron-3.5-lightning-30b-a3b`; in our 24 Oct clean-setup test the same tie-break was routed to
`nvidia/nemotron-3.5-super-vl-120b-a12b`, so Nightshift decides the model per call. `meterless/auto` can route to a non-NVIDIA model, which is why we log the routed model on every call.

## What was unique about our use

- **Zetaris is the evidence trail, not just a database.** Every finding carries the query id, SQL and rows. The Critic re-queries
  Zetaris to reproduce the finding before it can reach the memo, and checks R3 against registry density.
- **Memory changes what the agent reports.** H-MEM is not a chat history. A recorded auditor decision removes a repeat finding
  from the next memo and the trace and memo cite the memory id.
- **One model, two lanes, visible routing.** The deep and fast lanes are separate Nightshift apps; every call's receipt and
  routed Nemotron model is on the trace.
- **Honest offline mode.** Recorded Zetaris and Nightshift answers are replayed through the same adapters and agents, labelled everywhere.

## Cursor

Not used, so we are not competing for the Cursor award. The rules allow any coding tool; we used AI coding assistants, and
`CLAUDE.md` and `AGENTS.md` are the instructions we gave them.
