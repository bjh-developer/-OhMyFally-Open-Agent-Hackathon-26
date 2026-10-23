# D2 remaining red flags: R5, R6 and R9

Implemented and checked against live Zetaris on 23 Oct 2026. The standard eleven-column SQL result contract and public Python schemas are unchanged.

## What changed

All three checks now have SQL files in `sql/checks/`, so the existing Planner can discover them and the Analyst can run them. The runner records their source objects in finding evidence. `scripts/run_check.py` now calls the same `run_check()` helper as the Analyst, including the R5 preparation check.

### R5: business description mismatch

The local Nightshift runtime returned HTTP 404 for `/v1/embeddings`. `scripts/prepare_r5.py` checks that endpoint first; unsupported endpoints fall back to the small `sentence-transformers/all-MiniLM-L6-v2` encoder through FastEmbed. Authentication, transport, or server errors are reported rather than silently treated as missing embedding support. FastEmbed's upstream documentation: https://qdrant.tech/documentation/embeddings/fastembed/.

Setup reads distinct tender/activity-description pairs through live Zetaris. It embeds the descriptions, calculates cosine similarity, and writes the computed scores and model provenance to the existing R5 row's `gebiz.rules.params` JSON. This is a setup-only backing-store write, as with seeding. No table columns or shared contracts were added. No agent reads planted-case ground truth, and no source company records are altered.

The MiniLM model is cached under gitignored `.cache/embeddings/`. Download is allowed only with the explicit setup option `--download-model`; ordinary preparation reuses the local cache, and investigation runs use SQL only. They do not download or load a model.

`R5.sql` joins the stored similarity to the current tender and SSIC descriptions and returns similarities strictly below 0.2. Only stored supplier matches at confidence >=0.92 with sufficiently long descriptions are prepared. `app/checks/semantic.py` verifies that preparation exists and covers every eligible pair in the requested scope. Missing or changed descriptions cause an explicit coverage error until preparation is rerun, instead of a misleading zero-finding result.

R5 finding confidence is capped at 0.6 in the runner and Risk, and Risk always escalates it. The Critic still re-runs its SQL and verifies the supplier identity. It checks the Resolver's actual match confidence for R5, separately from semantic confidence; otherwise the intentionally low semantic score would cause erroneous Resolver retries/rejection.

The 0.2 threshold is a screening heuristic, not a calibrated accuracy result. Broad, outdated, abbreviated or long descriptions can give misleading similarities. Historical company activities are not available. Low-confidence identity matches and missing descriptions remain outside R5 coverage. The model truncates long inputs according to its tokenizer configuration.

### R6: supplier concentration

`R6.sql` assigns each tender to the first matching keyword category: landscaping, cleaning/waste, IT, security, education/training, professional services, events/catering, transport/logistics, construction/maintenance, or other.

For each category in the requested agency and period, it calculates:

```text
supplier value share = supplier's positive award value / category's positive award value
```

It returns the supplier's awards when the category has at least five distinct tenders and the share is strictly above 50%. Exactly 50% does not qualify. One result row represents one award, so several rows may describe the same concentration pattern.

Keyword categories are approximate and first-match order matters. `other` can mix unrelated work. Supplier names are not consolidated by UEN, and zero/negative award values are excluded from both numerator and denominator. Specialised markets can legitimately be concentrated. Current thresholds are written in SQL, consistent with the existing checks; editing YAML metadata alone does not change R6 SQL execution.

### R9: winner below the best weighted score

`R9.sql` joins awards to synthetic `internal_pg.evaluations` and calculates `sum(weight * score)` per bidder. It compares the winner with the highest score; the bid table's `bid_rank` is not treated as an evaluation score.

It requires at least two bidders, identical complete criteria, consistent positive weights summing to one, unique criterion rows, and scores between 0 and 100. If any bidder is incomplete or invalid, the tender is not compared. Ties at the best score are not flagged. This check covers synthetic evaluation records only, and a non-top-scoring award may have a documented explanation requiring review.

## Fictional cases and measured results

- Existing P6: R9 returns the winner's weighted score **82.4**, below the best score **89.6**.
- New P7: a fictional bakery wins computer/network support work. Measured MiniLM cosine similarity is **0.039395**, below 0.2.
- New P8: a fictional logistics supplier receives five of six equal-value transport awards, a value share of **0.833333**. Its five awards qualify; the competitor's award does not.

P7/P8 use a separate `Synthetic Review Agency`, so adding the tests does not change any real company's data or scores. The seeded data now contains 2,481 awards, 1,236 ACRA entities and 1,270 distinct supplier names. The committed source sample is unchanged; the additions are injected by `seed.py` from `data/eval/planted.json`.

All eight planted cases P1-P8 pass through the production check runner with the exact required result columns. Fourteen additional live SQL tests cover threshold boundaries, concentration sample size, tied scores, duplicate/missing criteria, inconsistent weights and invalid scores. The non-live Python suite passed 81 tests. Evidence with actual query IDs and fictional-case metrics is saved in `output_examples/remaining_flags_verification.json`; embedding preparation metadata is in gitignored `logs/r5-preparation.json`.

Live investigation `run_20261023_153325_492c5c` completed in 283.6 seconds with five Nightshift calls and no replay. The Critic independently reproduced the new SQL findings, Risk escalated all six award findings (including R5 at confidence 0.60), and Reporter generated the memo saved as `output_examples/remaining_flags_memo.md`. All traced steps succeeded.

## Reproduce setup

Start Docker, Zetaris and Nightshift, then use the repository virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -X utf8 scripts/seed.py
.\.venv\Scripts\python.exe -X utf8 scripts/register_zetaris.py
.\.venv\Scripts\python.exe -X utf8 -m app.resolver.run --pass 1
.\.venv\Scripts\python.exe -X utf8 -m app.resolver.run --pass 2
.\.venv\Scripts\python.exe -X utf8 scripts/prepare_r5.py --download-model
```

On later runs, omit `--download-model`. Preparation must be repeated after seeding (which clears R5 scores and the crosswalk), or after descriptions/matches change. Set `METERLESS_EMBEDDING_MODEL` if a Nightshift installation supports embeddings with a separately configured model; `--backend local` explicitly selects the cached fallback.

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/test_planted_checks.py -v
$env:RUN_LIVE_SQL_TESTS = '1'
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/test_check_sql_edges.py -v
.\.venv\Scripts\python.exe -X utf8 run.py --input input_examples/example_remaining.json
.\.venv\Scripts\python.exe -X utf8 scripts/run_check.py R9 'Housing and Development Board' 2021-04-01 2026-03-31
```

The sample investigation includes the fictional R5/R6 agency. P6/R9 uses Housing and Development Board. No examples are returned as hardcoded runtime results.
