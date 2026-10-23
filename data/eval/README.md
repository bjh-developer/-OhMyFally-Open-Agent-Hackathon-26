# Entity Resolver labels and accuracy

`entity_labels.csv` contains 103 observed GeBIZ supplier names: 100 source-supported, agent-reviewed labels and 3 pending cases. `correct_uen` is the expected UEN; `NONE` explicitly means that no UEN should be assigned. An empty answer means pending review and is excluded from every accuracy denominator.

The labels were assembled and reviewed on 23 Oct 2026 against the existing registry sample through live Zetaris. They were not copied from `supplier_xwalk` or Resolver predictions. Each positive row retains the registry name, entity type, and the current/former-name field used as evidence. The sources are GeBIZ awards and ACRA Information on Corporate Entities via data.gov.sg, under the Singapore Open Data Licence; see `../README.md`.

These are **agent-reviewed labels, not human-reviewed ground truth**. The current evidence supports a name-to-UEN association in this sample. It does not establish historical identity at the award date. In particular, former names lack change dates, and registration can postdate an award. A human can verify a row, correct its answer if needed, and change `review_status` to `human_reviewed` with their name in `reviewer`. Evaluation reports human-reviewed results separately; currently that denominator is zero and its accuracy is null.

| Category | Scored rows | Evidence |
|---|---:|---|
| Current corporate name | 50 | Unique corresponding current-name row |
| PRIVATE LIMITED | 15 | Observed expanded legal suffix |
| Punctuation, case, whitespace or omitted suffix | 9 | Both original strings retained |
| LLP | 10 | Registry type is Limited Liability Partnership |
| Former name | 5 | Specific former-name field retained |
| Registered foreign branch | 10 | Registry type is Foreign Company Branch |
| Placeholder | 1 | `Unknown` is not a legal entity; expected `NONE` |

Selection first included all five source-supported former-name cases and all ten registered foreign branches. Other categories used a fixed ascending SHA-256 ordering of supplier names, without examining Resolver predictions, to fill the table above. Only unique corporate candidate pairs were selected; no sole-proprietor names, addresses, or planted suppliers were added. The 99 positive labels were checked against their displayed source names and UENs. Expanded-versus-abbreviated suffix equivalence, typos, token subsets, conflicting legal forms, and ambiguous candidates are also tested separately with fictional entities in `tests/test_resolver.py`; these tests are not counted as real-data accuracy.

`ANRICA GmbH`, `BENTLEY SYSTEMS INTERNATIONAL LIMITED`, and `Lotek UK Limited` remain pending. Neither a fuzzy candidate nor absence from the small registry subset establishes an identity or a `NONE` label. They need independent identity evidence before scoring.

## Reproduce

With the handover stack running and seeded/registered:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/eval_resolver.py
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/test_eval_resolver.py tests/test_resolver.py tests/test_graph.py tests/test_checks.py -q
```

The evaluator loads entities and checks supplier membership through live Zetaris, disables replay, runs the production Resolver from scratch, and writes `output_examples/resolver_metrics.json`. Labels are only used to score its answers; they are never supplied to the Resolver. `--deterministic` disables Nightshift tie-breaks; `--output PATH` saves a separate report. This evaluates matching only; it does not implement the later pipeline/anomaly evaluation task.

The saved report records the label-file SHA-256, source query IDs, denominators, category/method breakdowns, errors, elapsed time, LLM calls and available receipt IDs. `entity_labels_provenance.json` records the queries used when preparing the labels. Raw source snapshots remain local under gitignored `logs/resolver-eval/`.

## Results and limits

The live run after the legal-form fix scored **100/100 correct**: 99 correct UEN links and one correct abstention. Three pending rows were excluded. Methods were 94 exact, 5 former-name, and 1 outside registry scope; no LLM calls were needed. There is no measured fuzzy or LLM tie-break accuracy in this set.

At the Critic's unchanged 0.92 threshold, only 94 of the 99 correct links pass: the five former-name matches have confidence 0.90. That gives accepted-link recall of **94/99 (94.95%)**, despite perfect raw matching on these selected rows. The evaluator reports this separately rather than treating a correct UEN as automatic acceptance. Thresholds were not tuned against these same labels.

This is an **in-sample diagnostic, not a held-out benchmark**. The original ACRA sample was already minimised using Resolver candidates, and these labels deliberately cover source-supported cases. The set is positive-heavy, with only one negative and three unresolved labels. It cannot establish general accuracy, negative-case performance, or coverage of the full registry. Broader independent labels and human sign-off remain necessary before making those claims.

The separate fictional tests exposed a legal-form bug: when no current/former-name candidate passed the legal-form check, `_pick` fell back to the incompatible candidates. The fix preserves the rejection instead, preventing an LLP from being assigned a company UEN solely because their names normalise alike. Three regression cases failed before this fix and passed afterward. No real supplier records were altered.

## Combined evaluation and precision labels

Run `python -X utf8 scripts/eval.py` to evaluate the three sample requests, supplemental planted scopes, fresh Resolver accuracy and `precision_review.csv`, writing `output_examples/metrics.json`. The script runs the production SQL checks rather than the full LLM investigation pipeline. No saved outputs are reused as answers.

`precision_review.csv` is a human review queue, initially containing 30 pending nonplanted findings. Leave `label` blank while pending. After review, use `plausible`, `explained` or `unclear`, set `review_status=human_reviewed` and provide a reviewer and reason. Precision is `plausible / (plausible + explained)` on matching human-reviewed findings; unclear/pending/agent-reviewed rows are excluded. Until there are decided human labels, precision is null. Existing review files are never overwritten. See `docs/handover/d2-evaluation.md` for definitions, limitations and reproduction steps.
