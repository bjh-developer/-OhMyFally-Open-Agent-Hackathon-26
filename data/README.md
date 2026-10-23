# Data

Sources (both from data.gov.sg, Singapore Open Data Licence v1.0; attribute "Contains information from ... accessed via data.gov.sg"):

- **GeBIZ awards**, dataset `d_acde1106003906a75c3fa052592f2fcb` (18,464 rows, Apr 2021 to Mar 2026). Tender (ETT) awards only; no quotation (ETQ) records. No UEN.
- **ACRA Information on Corporate Entities**, collection 2 (27 CSVs, 2,124,508 rows).
- **AGO excerpts** in `data/ago/` (verbatim chunks, see its README) and hand-written rules in `data/rules/`.
- **Planted cases** in `data/eval/planted.json`: fictional suppliers only; injected by `scripts/seed.py`; agents never read them.

## What is committed (`data/sample/`)

| File | Rows | Notes |
|---|---|---|
| `awards.csv` | 2,465 | HDB 1,268, People's Association 786, National Parks Board 411; dates ISO |
| `acra_entities.parquet` / `.csv` | 1,226 | Privacy-minimised, see below |

**ACRA sample minimisation.** The repo is public and ACRA includes sole proprietorships (often personal names with unit-level
addresses). The committed sample keeps only the entities the Resolver matched to a GeBIZ supplier and the top-3 candidates of
ambiguous suppliers; `level_no` and `unit_no` are blanked for Sole Proprietorship/ Partnership rows (85 of 1,226 rows are of that
type). The full candidate set (23,067 rows) lives in gitignored `data/local/`, raw downloads in gitignored `data/raw/`.
`seed.py` uses `data/local/` when present, otherwise the sample.

## Regenerate

```bash
python scripts/fetch_gebiz.py            # awards.csv (add `check` for the quotation check + agency stats)
python scripts/fetch_acra.py download    # raw CSVs -> data/raw/ (about 8 min, rate limited)
python scripts/fetch_acra.py             # full candidate set -> data/local/
python scripts/seed.py && python scripts/register_zetaris.py
python -m app.resolver.run --pass 1 && python -m app.resolver.run --pass 2
python scripts/fetch_acra.py minimise    # refresh the committed ACRA sample
```

More detail, row counts and known weaknesses: `docs/handover/d1-data.md`.

## Remaining checks (D2)

R5, R6 and R9 are implemented. After seed/register/Resolver, run `python -X utf8 scripts/prepare_r5.py --download-model` once to cache the local model and prepare R5; omit the download flag on later preparations. Seed clears the derived scores, so repeat preparation after a reseed. R6 uses ten keyword categories and R9 compares synthetic weighted evaluation scores.

Fictional P7/P8 add seven awards and three entities under `Synthetic Review Agency`, bringing the seeded totals to 2,481 awards and 1,236 entities. Existing P6 exercises R9. All eight planted cases and fourteen live SQL boundary tests pass. See `docs/handover/d2-red-flags.md` for implementation details, limitations and reproduction commands.

## Resolver evaluation (23 Oct 2026)

`eval/entity_labels.csv` provides 100 agent-reviewed, source-supported labels plus 3 pending cases. The live Resolver run scored 100/100 on this selected in-sample set; at the Critic's unchanged confidence threshold, 94/99 correct UEN links qualify. No human-reviewed accuracy or fuzzy/LLM accuracy is established by this set. See `eval/README.md` for provenance, category counts, reproduction commands, and limitations, and `output_examples/resolver_metrics.json` for the actual report.
