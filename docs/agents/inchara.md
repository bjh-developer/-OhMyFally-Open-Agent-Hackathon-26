# Agent instructions: Inchara (data pipeline, Entity Resolver, red-flag SQL, evaluation)

You are a coding agent working for **Inchara** on the Procurement Integrity Investigator (Open Agent Hackathon 2026, Track 02). **Read `docs/agents/CONTRACTS.md` first. It overrides anything here that conflicts with it.** The team plan explains the *why*: https://claude.ai/code/artifact/33db073a-a6f9-4f3d-a817-8e02bf03c74c

Inchara's background: Year 2 CS, self-learning ML and web development, comfortable with Python, React, Node, Java and PostgreSQL, and interested in bioinformatics. Inchara owns **getting real data in, matching suppliers to companies, the red-flag SQL, and proving the system works with numbers**. Joon Hao builds the D1 data work while Inchara is unavailable (22 Oct). Inchara takes it over from D2 morning.

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

Everything ships by **Sat 24 Oct, 20:00 SGT**, with full scope. Sun 25 to Tue 27 are buffer only.

### D1 (Thu 22): done by Joon Hao (you start D2)
Inchara is unavailable on D1, so Joon Hao builds the D1 data work. That covers:
- the GeBIZ quotation check and the agency shortlist;
- `fetch_gebiz.py`, `fetch_acra.py` and `seed.py`;
- the Zetaris registration;
- the Resolver (`app/resolver/`);
- `sql/checks/` R1–R4 and R8, plus `red_flags.yaml`;
- `planted.json` and its injection.

These areas are **yours from D2 onwards**: you maintain and improve them, and you own their numbers.

**D2 first hour, handover:**
1. `git pull`; `docker compose up -d`; `python scripts/seed.py`; `python scripts/register_zetaris.py`.
2. Read `docs/handover/d1-data.md`, which Joon Hao writes at the end of D1. It covers what was built, the quotation-check result, the chosen agencies, known Resolver weaknesses and open TODOs.
3. Run every `sql/checks/R*.sql` through Zetaris and confirm each planted case appears.

### D2 (Fri 23): labels, evaluation and the rest of the flags
8a. `data/eval/entity_labels.csv`: hand-check about 100 GeBIZ-to-ACRA pairs (supplier_name, correct uen or NONE). Include hard cases: punctuation, "PRIVATE LIMITED" against "PTE LTD", renamed companies, and branches. Then measure Resolver accuracy and tune the thresholds in `app/resolver/` if needed.
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
