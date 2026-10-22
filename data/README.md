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
