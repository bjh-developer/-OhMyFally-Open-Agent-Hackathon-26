# Agent instructions: Rae (domain, product, H-MEM service)

You are a coding agent in Cursor working for **Rae** on the Procurement Integrity Investigator (Open Agent Hackathon 2026, Track 02). **Read `docs/agents/CONTRACTS.md` first. It overrides anything here that conflicts with it.** The team plan explains the *why*: https://claude.ai/code/artifact/33db073a-a6f9-4f3d-a817-8e02bf03c74c

Rae's background: SMU CS, Tech Associate at SMU Legal Innovation & Technology, and a former NYC intern who built a 100+ page tender-document generator. Strong in TypeScript, React, Node, UI/UX and Figma. Rae owns **what counts as a red flag, how findings are worded, how the product looks, how it is pitched**, and the **H-MEM memory service**.

> H-MEM ownership is between Rae and Inchara, decided at onboarding on 21 Oct. If it goes to Inchara, move §3 into `inchara.md`.

---

## 1. Your outputs (in priority order)

| # | Output | Path | Done when |
|---|---|---|---|
| 1 | **H-MEM TypeScript service** | `services/hmem/` | The official conformance suite exits 0, the HTTP API in CONTRACTS §6 works, and it runs in `docker compose` |
| 2 | Red-flag definitions | `data/rules/red_flags.yaml`, `data/rules/mof_thresholds.yaml` | Every rule has logic, parameters, a known limitation and a `source_url` |
| 3 | Finding wording rules | `data/rules/wording.yaml` | Banned words, required phrasing and a disclaimer string; the Risk agent loads it |
| 4 | AGO excerpts | `data/ago/*.md` plus `data/ago/index.csv` | 50–200 chunks from 3–5 AGO reports, each with report, FY, section and URL |
| 5 | Planted test cases (with Inchara) | `data/eval/planted.json` | 5–8 fictional cases, each covering at least one of R1, R3, R4, R8 and R9 |
| 6 | UI components | `web/components/` | Memo card, evidence drawer and human-review queue, matching the Figma |
| 7 | Slide deck, demo script, README pitch sections | `docs/pitch/` | Deck covers the 8 required points; script follows the 6-segment demo guide |

## 2. Rules for you (the agent)

- Follow CONTRACTS §2, especially: no product code before **22 Oct, 08:00 SGT**, no secrets in files, and "anomaly for review" wording.
- **Never invent facts about real companies or real audit findings.** AGO quotes must be copied from the source PDF, with the page cited.
- Planted cases use **made-up company names that cannot exist**, such as `ZYLOQ TEST ENGINEERING PTE. LTD.`. Before using a name, check that it does not appear in the ACRA sample.
- Work in small steps. After each step, run the relevant check (conformance, `npm test`, or a `curl` against the service) and show the output before moving on.
- If a contract in CONTRACTS.md seems wrong, stop and tell Rae. Do not change the interface silently.

## 3. H-MEM service: build guide

**Goal:** a memory service that the Python agents call over HTTP and that passes the official Meterless H-MEM conformance suite. That suite only runs TypeScript, which is why this service is in TypeScript.

### D1 (22 Oct)
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

### D2 (23 Oct)
5. Add `src/server.ts`, a small HTTP server (Hono or Express) that imports the `HMEM` class from `src/index.ts`. `src/index.ts` must keep exporting `HMEM` unchanged, so the conformance suite keeps working.
6. Implement every endpoint in CONTRACTS §6. Map them like this:
   - `/add` → `hmem.add(...)`, with `agentId`, `runId` and `meta` stored on the record (tags or fields).
   - `/query` → `hmem.query(...)`, then apply the `filters` and return the trace metadata.
   - `/feedback` → `hmem.feedback(...)`.
   - `/auditor-decision` → a **long_term** memory with provenance `origin: "auditor"`, the reason as content, and `meta` holding uen, flag_id, agency, pattern_tag and scope.
   - `/ledger` → stream the trust ledger, and also append every ledger event to `logs/hmem-ledger.jsonl`.
7. Add `Dockerfile` plus a `docker-compose.yml` service `pi-hmem` on port 7070, on network `zetaris_default`, with a volume for `state/`.
8. Re-run conformance after your changes and save `logs/evidence/hmem-conformance-d2.txt`. **It must stay green.**
9. Write `services/hmem/test/http.test.ts`. Cover:
   - add, then query returns it;
   - an auditor-decision dismiss is recalled by an exact (uen, flag_id, agency) filter;
   - a memory from another agency is **not** returned unless `scope=global`;
   - the memory survives a restart.

### D3 (24 Oct)
10. Pair with Joon Hao while he wires `app/adapters/hmem_client.py` to your API. Fix any contract mismatches together and update CONTRACTS.md in the same commit.
11. Prove the demo moment end to end: run 1 flags X → the auditor dismisses it with a reason → run 2 suppresses X and cites the memory ID.

**Using the Meterless prompt:** at meterless.ai/engines.html, choose IMPLEMENT → **"Give my agent memory"**, paste it into Cursor, and add: *"Target is `services/hmem/` (already adapted from the reference). Keep `src/index.ts` exporting `HMEM` so the conformance suite still runs. Expose it via the HTTP contract in `docs/agents/CONTRACTS.md` §6."*

## 4. Domain outputs

### Red-flag definitions (draft tonight, final on D1)
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

### Wording rules (D2)
`wording.yaml` lists:
- banned terms: fraud, corrupt, illegal, criminal, guilty, scam;
- required phrasing: "anomaly for review", "may indicate", "requires auditor judgement";
- a one-line disclaimer for the UI and the memo.

The Risk agent rejects any finding text containing a banned term.

### AGO excerpts (tonight and D1)
Take procurement chapters from 3–5 AGO annual reports (FY2021/22 to FY2024/25). Chunk them into roughly 150–300-word sections. In `index.csv`, record `chunk_id, report, fy, section, page, url`. Quote only; don't paraphrase into new claims.

### Planted cases (D2, with Inchara)
Write `planted.json` entries like this:

```json
{"case_id":"P1","flags":["R1"],"agency":"<sample agency>","supplier":"ZYLOQ TEST ENGINEERING PTE. LTD.",
 "uen":"T99ZZ0001A","award":{"tender_no":"PLT000ETT25000001","awarded_amt":400000,"award_date":"2025-06-20"},
 "acra":{"incorporation_date":"2025-05-30","status":"Live Company","postal_code":"999001"},"expected":"flag R1"}
```

Inchara's seed script injects them.

## 5. Product, UX and pitch

- **Figma (tonight):** one screen with a request bar, a live run timeline and a review memo with evidence drawer, plus a human-review queue tab. Use the colours and type of shadcn defaults.
- **UI (D3–D4):** build the components in `web/components/` against the `Finding` schema in CONTRACTS §7.4, using mock JSON from `output_examples/` until the API is live. The web UI runs on **port 3100**.
- **Deck (D4–D6):** problem and users, solution, architecture (reuse the plan diagram), stack, Zetaris and Meterless use, what was unique (the Critic re-queries Zetaris to verify every claim, the USL crosswalk, auditor memory in H-MEM), product visuals, future work.
- **Demo script (D4):** follow the 6 segments in the plan doc. Keep it to 2:30–3:30.

## 6. Daily checklist

- [ ] D1: H-MEM reference in the repo, conformance green and saved; red_flags.yaml final; AGO chunks drafted
- [ ] D2: HTTP server and Docker done; conformance still green; HTTP tests pass; wording.yaml; planted.json with Inchara
- [ ] D3: H-MEM wired to the agents with Joon Hao; demo memory moment works; UI components started
- [ ] D4: hand-review the top 30 real flags with Inchara (`plausible` / `explained` / `unclear`); deck v1; demo script; **feature freeze 23:59**
- [ ] D5: README pitch and sponsor sections; deck v2; rehearsal
- [ ] D6: record the video with Joon Hao; final deck; check the submission checklist

## 7. When to stop and ask Joon Hao

- Any change to CONTRACTS.md.
- The conformance suite goes red and you can't make it green within 1 hour.
- Anything that would put a real company's name next to a fabricated fact.
