# D2 evaluation harness

Implemented on branch `evaluation`, based on red-flag commit `16a98a3`. The red-flag implementation is committed and pushed to `origin/red-flags`.

## Run

With the handover data and R5 preparation already loaded:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/eval.py
```

This writes actual measured results to `output_examples/metrics.json`. It does not reseed data, overwrite source records, submit auditor decisions or return saved examples as runtime outputs. It always disables replay and uses Zetaris for source reads. External queries have timeouts and the evaluation has a maximum 600-second query budget; `--timeout` can reduce it.

The harness uses the permitted **checks-only** evaluation route: production Resolver crosswalk reads and the Analyst's actual check runner. It does not invoke the Planner, Critic, Risk or Reporter. Explicit input flags are respected; empty flags mean all implemented checks. This distinction is recorded in the report: these are SQL candidate findings, not final accepted findings or memo-quality scores.

It runs the three existing files `input_examples/example_1.json`, `example_2.json` and `example_3.json`. Use `--inputs FILE1 FILE2 FILE3` to select three other requests. `--output`, `--entity-labels` and `--precision-labels` select different report/label files.

## What is measured

1. **Three sample requests.** HDB 2025, People's Association 2024 (R1/R4 only), and NParks 2023-2025. The report records checks, candidate counts, coverage gaps, query IDs, trace paths and elapsed time. The live snapshot returned 50, 7 and 45 candidate award findings respectively, with no coverage gaps.
2. **Planted recall.** Ground truth is used only by the evaluation script after detection, never passed to the Analyst as expected results. Findings must match the expected flag, tender and supplier. Every expected award is counted; a multi-award case is fully caught only when all its expected awards appear. A case with several flags requires every flag. Failed checks remain in the denominator and are marked unevaluated, so failures cannot inflate recall.
3. **Supplemental planted scopes.** The three samples omit HDB's 2024 shared-address case and the synthetic R5/R6 agency. Additional scopes run HDB/R3 and Synthetic Review Agency/R5/R6. Their results are kept separate from sample counts. R6's competitor award is a negative control and must remain unflagged.
4. **Resolver accuracy.** `scripts/eval_resolver.py` now exposes `evaluate_live()` so both CLIs share the same measurement. It reloads registry data and reruns the Resolver; the combined report does not reuse the older saved accuracy report. Prediction rows are omitted from combined public metrics to avoid exporting supplier names.
5. **Precision labels.** The harness reads `data/eval/precision_review.csv`, validates it and scores matching human-reviewed findings only. If the file is missing, it creates up to 30 pending rows from nonplanted sample findings, ordered by award value. These are not risk-agent rankings or a random statistical sample. Planted awards, including the R6 competitor control, are excluded.
6. **Runtime and tokens.** Runtime is measured with a monotonic clock. SQL checks make no LLM calls. The current Resolver labels also need no tie-break calls, giving known total token use of zero. Provider-reported token usage remains null when no provider usage was collected; if future labels need LLM calls, unknown token totals remain null instead of being estimated or called zero. This does not measure the tokens of a full investigation.

The live snapshot caught **8/8 cases and 15/15 expected award findings**, with the R6 negative control passing. Fresh Resolver accuracy was **100/100**, with three pending labels excluded; human-reviewed Resolver accuracy is still unmeasured, and only 94/99 correct links meet the unchanged Critic threshold. See `data/eval/README.md` for the in-sample limitations of those labels.

`complete` means all requested measurements executed without missing check coverage or Resolver batch failures. `quality_checks_passed` separately means all planted cases were caught and negative controls passed. The CLI exits nonzero on execution failure or a failed planted-case check. Missing human precision labels do not prevent the other measurements from completing and are never invented.

## Complete human precision reviews

The initial `precision_review.csv` contains 30 rows, all pending. It includes finding/tender IDs, agency, observed metric/threshold, award value and evidence query ID, but no supplier names or addresses. To inspect a finding, use its flag, the sample request's period and `scripts/run_check.py` to reproduce its source rows through Zetaris. The trace paths and query IDs in `metrics.json` provide provenance.

For a reviewed row:

- Set `label` to `plausible`, `explained` or `unclear`.
- Set `review_status` to `human_reviewed`.
- Fill in `reviewer` and `reason`.

Then rerun `scripts/eval.py`. Existing review files are preserved, including any custom columns; the harness never overwrites them. If source changes alter finding IDs, unmatched labels are counted and excluded. Pass a new `--precision-labels` path to create a separate review queue without losing earlier reviews.

```text
precision = plausible / (plausible + explained)
```

`unclear`, pending and agent-reviewed rows are excluded from that denominator. Review coverage and each exclusion are reported separately. With no decided human labels, precision is **null**, not zero or 100%. This measures review plausibility in a selected sample, not proven wrongdoing or population-wide precision.

## Validation

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/test_eval.py tests/test_eval_resolver.py tests/test_remaining_checks.py tests/test_graph.py tests/test_checks.py tests/test_resolver.py -q
```

48 focused tests passed. They cover missed/wrong-supplier awards, failed-check denominators, multi-flag cases, negative controls, supplemental dates and flags, precision exclusions and invalid labels, preserving existing files, excluding names from the review queue and deadline enforcement. The live harness also checks for replayed or truncated source results. Metrics include input/label/evaluator/SQL hashes and live query IDs for reproduction.
