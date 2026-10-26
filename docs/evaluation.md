# Evaluation

Part of the [ProcureLens README](../README.md).

Scripts by Inchara: [scripts/eval.py](../scripts/eval.py) (combined harness) and [scripts/eval_resolver.py](../scripts/eval_resolver.py)
(Resolver only). Both need live Zetaris; they disable replay. Method and reproduction: [docs/handover/d2-evaluation.md](../docs/handover/d2-evaluation.md)
and [data/eval/README.md](../data/eval/README.md). The numbers below are quoted from
[output_examples/metrics.json](../output_examples/metrics.json) and [output_examples/resolver_metrics.json](../output_examples/resolver_metrics.json).

| Measure | Result in the file | Scope |
|---|---|---|
| Planted cases caught | 8 of 8 cases; 15 of 15 expected awards; negative controls passed | SQL candidate findings, **before** the Critic, Risk or memory. Fictional cases only. |
| Resolver accuracy | 100 of 100 labelled names correct (99 links, 1 correct abstention) | In-sample, agent-reviewed labels. Human-reviewed accuracy: 0 labels, so not measured. |
| Resolver links passing the Critic threshold (0.92) | 94 of 99 | Same set |
| Precision on real awards (SQL stage) | **28.6%** after the fixes below: 8 plausible, 20 explained, 2 unclear on a fresh sample of 30 ([round 2](../data/eval/precision_review_round2.csv)). **9.5%** before them: 2 plausible, 19 explained, 9 unclear ([baseline](../data/eval/precision_review.csv), [metrics_baseline.json](../output_examples/metrics_baseline.json)) | Human review by Joon Hao, evidence prepared with an AI assistant. Findings before the Critic, Risk or memory; top 30 by award value |
| LLM calls in the eval | 0 (SQL checks only) | So it says nothing about a full investigation's model use |

**How precision was improved.** The baseline review showed three noise patterns: group companies sharing an office (R3),
loose free-text business descriptions (R5), and single large contracts or mislabelled keyword categories (R6). Each fix is a
general rule, not a list of the reviewed cases: R3 counts suppliers whose names start with the same word as one group; R5 also
requires the SSIC division to be an unusual fit for the type of work; R6 needs at least two awards to the supplier and no longer
treats "supply, delivery" wording as logistics. Candidates fell from 92 to 53 and all 8 planted cases are still caught. To avoid
grading the fix on the cases it was built from, round 2 is a fresh sample that excludes every baseline finding. Precision
counts "plausible" (worth an auditor's look) against "explained"; it is not a rate of wrongdoing. Round 2 also found two
remaining patterns: R5 treats "managing agent and improvement works" tenders as administration, and R4 only sees tendered awards.

These are check-level results on samples of 30. They do not measure final-memo accuracy, and the files say so
under `limitations`. One more caveat: `metrics.json` was generated from an earlier version of `input_examples/` (its three sample
rows are HDB calendar 2025, People's Association 2024 and NParks 2023-2025; the hashes in its `provenance` block no longer match the current example files).
The planted-case and Resolver numbers do not depend on those inputs.

Other saved outputs: [output_examples/remaining_flags_verification.json](../output_examples/remaining_flags_verification.json) and
[remaining_flags_memo.md](../output_examples/remaining_flags_memo.md) (R5, R6, R9 on the synthetic agency),
[token_savings.md](../output_examples/token_savings.md).
