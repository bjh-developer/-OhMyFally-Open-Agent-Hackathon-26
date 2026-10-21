# Agent instructions: Inchara (data pipeline, Entity Resolver, red-flag SQL, evaluation)

You are a coding agent working for **Inchara** on the Procurement Integrity Investigator (Open Agent Hackathon 2026, Track 02). **Read `docs/agents/CONTRACTS.md` first. It overrides anything here that conflicts with it.** The team plan explains the *why*: https://claude.ai/code/artifact/33db073a-a6f9-4f3d-a817-8e02bf03c74c

Inchara's background: Year 2 CS, self-learning ML and web development, comfortable with Python, React, Node, Java and PostgreSQL, and interested in bioinformatics. Inchara owns **getting real data in, matching suppliers to companies, the red-flag SQL, and proving the system works with numbers**. This is the critical path: nothing else can be demoed until D1's data is queryable through Zetaris.

---

## 1. Your outputs (in priority order)

| # | Output | Path | Done when |
|---|---|---|---|
| 1 | Data fetch and seed | `scripts/fetch_gebiz.py`, `scripts/fetch_acra.py`, `scripts/seed.py`, `data/sample/` | `docker compose up` plus `python scripts/seed.py` loads Postgres and S3 with no manual steps; `data/sample/` is only a few MB |
| 2 | Zetaris registration SQL | `sql/register/*.sql` (with Joon Hao) | `SELECT count(*) FROM gebiz_pg.awards` and `FROM ACRA_FILES.entities` work through Zetaris REST |
| 3 | Entity Resolver (deterministic part) | `app/resolver/` | It writes `gebiz_pg.supplier_xwalk`, and accuracy on the labelled set is reported |
| 4 | Labelled set | `data/eval/entity_labels.csv` | About 100 hand-checked GeBIZ-to-ACRA pairs |
| 5 | Red-flag SQL | `sql/checks/R1.sql R2.sql R3.sql R4.sql R8.sql` | Each returns the exact columns in CONTRACTS §7.3, and each catches its planted case |
| 6 | Evaluation harness | `scripts/eval.py` | Writes `output_examples/metrics.json` with recall on planted cases, entity-match accuracy, precision labels, runtime and tokens |
| 7 | `data/README.md` | `data/README.md` | Covers sources, SODL licence attribution, the subset chosen, row counts and how to regenerate |
| 8 | Should-haves | R5 (embeddings), S5 synthetic internal DB, R6 | Only after 1–7 are done |

## 2. Rules for you (the agent)

- Follow CONTRACTS §2. Above all: no product code before **22 Oct, 08:00 SGT**, and no secrets in files.
- **Data rules:**
  - Keep only what the demo needs: 2–3 agencies, FY21–FY25 awards, and ACRA rows that are candidates for those suppliers.
  - Never commit full raw dumps. `data/raw/` is gitignored and `data/sample/` is committed.
  - Planted cases use **fictional** suppliers only (Joon Hao and Inchara write them together); never alter a real company's row.
  - Sole proprietorships stay in for matching, but their names are masked in the UI.
- **Zetaris rules:**
  - One SQL statement per REST call.
  - Every value comes back as a **string**, so cast it.
  - Send a fresh UUID as both `X-Request-ID` and `queryId`.
  - Never print the API key.
  - Use `scripts/zsql.py`, a helper Joon Hao provides on D1. Until then, use the `curl` pattern in the plan.
- **data.gov.sg API:**
  - Unauthenticated calls are limited to 5 requests a minute, so sleep between pages and cache raw responses in `data/raw/`.
  - Full downloads go through the initiate/poll-download API, which returns a presigned S3 URL that expires. The Zetaris getting-started repo's `scripts/fetch_datagovsg.py` shows the pattern.
- Work in small steps. After each step, run the check that proves it, such as a row count, a Zetaris `SELECT` or `pytest`, and show the output.

## 3. Verified facts you can rely on (checked 20–21 Oct)

- **GeBIZ awards:**
  - dataset `d_acde1106003906a75c3fa052592f2fcb`, 18,464 rows, Apr 2021 to Mar 2026;
  - fields `tender_no, tender_description, agency, award_date (d/m/yyyy), tender_detail_status, supplier_name, awarded_amt`;
  - **no UEN**.
  - Query it with `https://data.gov.sg/api/action/datastore_search?resource_id=<id>&limit=&offset=`.
- **ACRA entities:**
  - collection 2 on data.gov.sg: 27 CSVs (A–Z plus Others), about 58k rows in the first file alone;
  - includes `former_entity_name1..15` (no change dates), the full address, `primary_ssic_code` and `no_of_officers`.
- **Thresholds:** small-value up to S$6k; quotation S$6k–90k; tender above S$90k.
- **Zetaris storage:**
  - Zetaris can't read files on the laptop; it reads Postgres (via `CREATE DATASOURCE`) and S3 (via `CREATE LIGHTNING FILESTORE TABLE`).
  - SeaweedFS works as S3 with `s3Endpoint "http://pi-s3:8333"` and `useS3PathStyleAccess "true"`.
  - A federated join across Postgres and S3 was tested and works.

## 4. Day-by-day

### Tonight (21 Oct, no product code)
- [ ] Install Zetaris and Nightshift and get `smoke_test.py` to print 3 PASS lines. Do this first.
- [ ] **Check whether GeBIZ includes quotations.** Count `tender_no` patterns, ETT (tender) against ETQ (quotation), with the datastore API. Report the counts to the team, because R4 depends on it.
- [ ] Pick 2–3 agencies with enough awards, a mix of values, and some sub-S$90k repeat suppliers. Share the shortlist.
- [ ] Download the raw GeBIZ and ACRA CSVs into `data/raw/` (gitignored; data only, no code).

Everything ships by **Sat 24 Oct, 20:00 SGT**, with full scope. Sun 25 to Tue 27 are buffer only.

### D1 morning (Thu 22, target 13:00): data queryable through Zetaris (**blocks everyone**)
1. `fetch_gebiz.py`: pull awards for the chosen agencies, parse dates, and write `data/sample/awards.csv`.
2. `fetch_acra.py`: build the candidate subset. Normalise names (upper case, strip punctuation, drop PTE/LTD/PRIVATE/LIMITED/LLP). Keep every ACRA entity that shares the first 1–2 significant tokens with any supplier, by current or former name. Write `data/sample/acra_entities.parquet` (pyarrow), with a CSV copy as fallback.
3. `seed.py`:
   - create DBs `gebiz` and `agency_internal` in `pi-postgres`;
   - load `awards`, `rules` (from `data/rules/` YAML) and `ago_chunks` (from `data/ago/`);
   - create an empty `supplier_xwalk`;
   - upload the ACRA file to `s3://pi-acra/acra/`.
   It must be **idempotent**: running it twice gives the same state.
4. With Joon Hao, write `sql/register/` and register the sources. Confirm both `SELECT count(*)` queries through Zetaris.

### D1 afternoon to midnight (Thu 22): Resolver, red-flag SQL, planted cases
5. Resolver `app/resolver/match.py`. Apply these layers in order and record the `method`:
   1. `exact` on the normalised name
   2. `former_name` match
   3. `fuzzy`: `rapidfuzz` token_set_ratio with blocking on the first token; ≥ 92 counts as a match, 80–92 is ambiguous
   4. ambiguous top 3 goes to `llm_tiebreak` through the **fast** Nightshift lane, about 20 suppliers per call, returning JSON
   5. otherwise `unresolved`. Names without a local suffix (foreign firms, government bodies) are `out_of_scope`.

   Write the results to `supplier_xwalk`. Expose `resolve(names) -> list[Match]` (CONTRACTS §7.4) so the Resolver agent can call it and retry a different strategy when the Critic rejects a match.
6. `entity_labels.csv`: hand-check about 100 pairs (supplier_name, correct uen or NONE). Include hard cases: punctuation, "PRIVATE LIMITED" against "PTE LTD", renamed companies, and branches.
7. Red-flag SQL, R1, R2, R3, R4 and R8 (definitions are in `data/rules/red_flags.yaml`):
   - `awards` joins to `supplier_xwalk` on supplier_name, and `supplier_xwalk` joins to `entities` on uen;
   - output columns exactly as in CONTRACTS §7.3;
   - use `{{agency}}`, `{{date_from}}` and `{{date_to}}` placeholders;
   - Spark SQL functions: `datediff`, `date_add`, window functions for R4.
8. With Joon Hao, write `planted.json`, and make `seed.py` inject the fictional rows into awards, entities and (for R9) agency_internal. Then run each check and confirm its planted case appears.

### D2 (Fri 23): evaluation and the rest of the flags
9. `scripts/eval.py`:
   - run the pipeline (or just the checks) on 3 sample requests;
   - compute recall on planted cases and Resolver accuracy against `entity_labels.csv`;
   - read the precision labels from `data/eval/precision_review.csv`;
   - write `output_examples/metrics.json`.
10. R8 edge cases, then R5 and R6:
    - first check whether Nightshift answers `POST /v1/embeddings`;
    - if not, use a small local `sentence-transformers` model (cached, no runtime download);
    - R5 findings are always low-confidence and escalated;
    - for R6, cluster tender descriptions into about 10 categories (embeddings, or a keyword taxonomy), then write `sql/checks/R6.sql`.
11. Generate the S5 synthetic internal DB (bids, evaluation scores and COI declarations for the ~30 planted tenders only) and write `sql/checks/R9.sql`.

### D2 evening (Fri 23): numbers and freeze
12. Hand-review the top 30 non-planted flags with Joon Hao into `precision_review.csv` (`plausible` / `explained` / `unclear`).
13. Final `metrics.json`; `data/README.md`. **Feature freeze 23:59.**

### D3 (Sat 24): ship
14. 09:00–13:00: clean-setup test (fresh clone, `docker compose up`, `seed.py`, run). Fix anything that needs a manual step, and save the final `metrics.json`.
15. 13:00–20:00: support the video (the metrics slide and the "Resolver retried with a former name" moment in the trace) and the final submission check.

## 5. Interfaces you consume and provide

- **Consume:** Joon Hao's `data/rules/*.yaml`, `data/ago/*`, `planted.json`, `app/adapters/zetaris.py`, `app/adapters/nightshift.py` (fast lane) and `app/schemas.py`.
- **Provide:** the Postgres and S3 data and Zetaris objects (CONTRACTS §7.1); `resolve()`; `sql/checks/*.sql`; `metrics.json`.

## 6. When to stop and ask Joon Hao

- Any change to table or column names in CONTRACTS §7.
- Zetaris refuses a registration (for example, a Parquet type it can't read). Fall back to CSV, then tell Joon Hao.
- The data.gov.sg API blocks you, or the GeBIZ quotation check shows ETT only, which changes R4.
