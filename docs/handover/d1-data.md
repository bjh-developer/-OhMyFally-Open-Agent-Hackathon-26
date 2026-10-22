# D1 data handover (stream B, Thu 22 Oct 2026) — for Inchara

Everything below was run against live Zetaris on 22 Oct. Contracts: `docs/agents/CONTRACTS.md` (it wins).

## 1. Quotation check (R4 depends on it)

`tender_no` type code (characters 7-9) over all 18,464 GeBIZ awards (data.gov.sg `d_acde1106003906a75c3fa052592f2fcb`):

| Pattern | Rows |
|---|---|
| `ETT` (tender) | 17,755 |
| `ETQ` (quotation) | **0** |
| numeric interface-record IDs (e.g. `MHA00003000011991`) | 709 |

**GeBIZ here holds tender awards only; no quotation records.** But 7,244 ETT awards are below S$90k (4,348 below S$6k), so R4 has data. It cannot see splitting that stays inside the quotation band, which is stated in `red_flags.yaml` as the limitation.
Reproduce: `python scripts/fetch_gebiz.py check`.

## 2. Agencies chosen

Housing and Development Board (1,268 awards, 5 R4-candidate suppliers), People's Association (786 awards, 4), National Parks Board (411 awards, 3). Mix of very large (HDB), event/services small-value (PA), and mid-value (NParks) work, each with repeat sub-S$90k suppliers. Agency strings must match exactly, `People's Association` included.
Runner-ups from the same stats: Ministry of Education (679, 2), A*STAR (937, 2).

## 3. Row counts (through Zetaris, after seed + planted)

| Zetaris object | Rows |
|---|---|
| `gebiz_pg.awards` | 2,474 (2,465 real + 9 planted) |
| `gebiz_pg.rules` | 9 |
| `gebiz_pg.ago_chunks` | 11 (loaded from `data/ago/`; `embedding` is NULL until R5) |
| `gebiz_pg.supplier_xwalk` | 1,267 |
| `ACRA_FILES.entities` | 1,233 from the committed minimised sample (1,226 real + 7 planted). With the gitignored full set in `data/local/` it is 23,074 (23,067 candidates + 7 planted), out of 2,124,508 ACRA rows |
| `internal_pg.bids / evaluations / coi_declarations` | 2 / 4 / 1 (planted P6 only) |

ACRA candidate rule (`scripts/fetch_acra.py`): keep an entity if any of its names (current or `former_entity_name1..15`) shares the first two normalised tokens with a supplier, or the first token when that token is rare in ACRA (<= 50 entities). Raw downloads live in `data/raw/` and the **full candidate set (23,067 rows) in `data/local/`; both are gitignored.**

**Committed ACRA sample is privacy-minimised** (repo is public; the full set had 11,648 sole-proprietorship rows, often personal names with unit-level addresses). `python scripts/fetch_acra.py minimise` (run after the Resolver) keeps only: entities the Resolver matched to a GeBIZ supplier (any method except unresolved/out_of_scope), the top-3 candidates of unresolved / llm_tiebreak suppliers, and nothing else (planted entities are injected by `seed.py` from `planted.json`). `level_no` and `unit_no` are blanked for Sole Proprietorship/ Partnership rows. Result: 1,226 rows (~0.4 MB):

| entity_type_description | rows |
|---|---|
| Local Company | 1,103 |
| Sole Proprietorship/ Partnership | 85 |
| Limited Liability Partnership | 28 |
| Foreign Company Branch | 10 |

`seed.py` uses `data/local/acra_entities_full.parquet` when it exists, otherwise the minimised sample (`--sample-only` forces the sample). I re-ran seed, register, Resolver passes 1-2 and all checks on the minimised sample: identical Resolver counts (section 5), every planted case still caught, R1-R4 still return real rows, 46 tests pass. A fresh clone only has the sample, so that is what judges get.

## 4. Reseed and re-register (order matters)

```bash
docker compose up -d                       # pi-postgres, pi-s3 (external network zetaris_default must exist)
python scripts/seed.py                     # idempotent (uses data/local/ full ACRA set if present, else the sample); --no-planted skips the fictional cases; EMPTIES supplier_xwalk
python scripts/register_zetaris.py         # idempotent; drops+recreates only gebiz_pg, internal_pg, ACRA_FILES; --csv for the CSV fallback
python -m app.resolver.run --pass 1        # exact + former_name (R1/R2/R3 join through supplier_xwalk)
python -m app.resolver.run --pass 2        # fuzzy + fast-lane LLM tie-break + unresolved/out_of_scope (R8 needs it)
python scripts/run_check.py R1 "People's Association" 2021-04-01 2026-03-31
pytest                                     # 40 tests incl. tests/test_planted_checks.py (needs Zetaris up)
```

Re-download only if needed: `python scripts/fetch_gebiz.py --force`; `python scripts/fetch_acra.py download` (rate limited, about 8 min), `python scripts/fetch_acra.py` (builds the full set in `data/local/`), run seed/register/Resolver, then `python scripts/fetch_acra.py minimise` to refresh the committed sample.

Parquet works in Zetaris (date column typed as `date`). Verified syntax, found by trial since there is no local doc:
- `CREATE DATASOURCE n OPTIONS (jdbcurl "...", jdbcdriver "org.postgresql.Driver", username "...", password "...")` — **`jdbcdriver` is required**, otherwise "Unknown DataSource Exception".
- `REGISTER DATASOURCE TABLE "awards" FROM gebiz_pg` (bare table name; other forms are silent no-ops), then query `gebiz_pg.awards`.
- `CREATE LIGHTNING FILESTORE TABLE entities FROM ACRA_FILES FORMAT parquet OPTIONS (PATH "s3a://...", ...)`.
- Spark SQL escapes a single quote as `\'`, **not** `''` (`'People''s Association'` silently matches 0 rows). `app/checks/runner.py::_lit` (stream A) used `''`; I told stream A. `scripts/run_check.py` and `tests/test_planted_checks.py` monkeypatch it until that is fixed.
- Numerics come back as `'10400.000000000000000000'` strings; cast with float.

## 5. Resolver method counts (1,267 distinct supplier names)

| method | count |
|---|---|
| exact | 1,223 |
| former_name | 5 |
| fuzzy | 0 |
| llm_tiebreak | 2 (capped at confidence 0.85) |
| unresolved | 1 (planted P5, the intended R8 hit) |
| out_of_scope | 36 (individuals, foreign firms, charities/co-ops with no local suffix, `Unknown`) |

Layers (`app/resolver/match.py`): pass 1 = exact then former_name on the normalised name (legal-form filter: LLP vs company; several same-name entities resolve only when exactly one is live); pass 2 = rapidfuzz `token_set_ratio` blocked on the first token (>= 92 match, 80-92 ambiguous; a pure token-subset such as `ABC` vs `ABC CONSTRUCTION` is capped at 91) then `llm_tiebreak` on the fast lane, then `unresolved` (has PTE LTD / PRIVATE LIMITED / LLP) or `out_of_scope`.
`resolve(names, index, strategies=..., tiebreak=...)` lets the Resolver agent retry with a different strategy. Receipts from the tie-break are collected in `app.resolver.llm.RECEIPTS`.

## 6. Checks and planted cases

`sql/checks/R1,R2,R3,R4,R8.sql` return exactly the CONTRACTS §7.3 columns. Hits on 2021-04-01..2026-03-31 incl. planted:

| Check | HDB | PA | NParks | Planted case caught |
|---|---|---|---|---|
| R1 incorporated < 183 days | 1 | 3 | 0 | P1 (HDB) |
| R2 status not live | 15 | 9 | 3 | P2 (NParks) |
| R3 shared exact address | 212 | 42 | 29 | P3 (HDB, two suppliers) |
| R4 splitting | 14 | 11 | 6 | P4 (PA, three awards) |
| R8 local-looking, no match | 0 | 0 | 1 | P5 (NParks) |

`data/eval/planted.json` has P1-P6, **fictional suppliers only** (UENs `T99ZZ...`, postcodes `9990xx`, `TEST` in every name). Schema is a superset of the §8.2 example: each case has `awards[]` and `entities[]` lists so multi-award cases fit. `scripts/seed.py` injects them into awards, the S3 entities file and `agency_internal`. P6 is the R9 case (rank-2 winner, synthetic bids/evaluations/COI); the R9 check itself is yours on D2. Nothing in `app/` reads `planted.json`.
`tests/test_planted_checks.py` asserts each check finds its case.

## 7. Known weaknesses and open TODOs

1. **R3 is noisy** (212 HDB rows): most groups are 2 suppliers in one multi-tenant building or industrial lot (Raffles Quay, Tampines Industrial Drive, ...), often sister companies. R3 skips sole proprietorships/partnerships because their unit-level address is blanked in the sample. Ideas: down-weight when `unit_no`/`level_no` are `na`, or when the building hosts many unrelated suppliers; the Critic or Risk step should cap R3 confidence.
2. **R2 uses current status only** (ACRA has no history) and sole proprietorships that closed are included (`Terminated`, `Cancelled`); many hits are benign. R2 is the largest false-positive risk after R3.
3. **R1 ignores negative ages.** Some sole-proprietor names match an ACRA row registered after the award (a re-registration of the same trading name); `BETWEEN 0 AND 183` excludes them, so those are silently not tested. Also, real R1 hits include `OVV` (a sole proprietorship, 156 days), which is a legitimate small trader.
4. **R4:** the data has no quotations (section 1), and call-offs under a framework look like splitting.
5. **Out-of-scope is name-suffix based.** A sole proprietor or partnership with a trade name and no PTE LTD, absent from the 23k-entity subset, becomes `out_of_scope`, not R8. Personal supplier names are in `supplier_xwalk.supplier_name` and `awards` unmasked (GeBIZ publishes them), and the 85 sole-proprietorship entity names kept in the sample may be personal names; masking in the `public` role is still to do (D2).
6. **Subset risk:** `fetch_acra.py` only keeps entities sharing leading tokens with a supplier, so a renamed entity whose old and new names share no first token is missed (`former_name` covers the usual case).
7. **LLM tie-break:** only 2 live matches, so the labelled-set accuracy is not measured yet (your `entity_labels.csv`, D2). Nightshift's fast lane sometimes returns 502 `empty_response` or 499; the Resolver retries twice and then leaves those suppliers unresolved rather than failing. A batch of 8 takes 10-40 s. The fast model ignores "JSON only" unless the system prompt says "Do not explain".
8. The Resolver reads entities/awards through Zetaris but writes `supplier_xwalk` straight to Postgres (Zetaris sources are read-only). `app/resolver/entities.py` has its own small Zetaris REST client; swap it for `app/adapters/zetaris.py` if you want one code path.
9. `data/README.md` now covers sources, SODL attribution, counts and regeneration; extend it with eval numbers on D2.
10. `red_flags.yaml` `why_it_matters` lines are deliberately generic: I did not attach AGO claims I had not checked. Stream C's `data/ago/` excerpts can be cited there.
11. `requirements.txt`: I appended `pandas` (used by the fetch/seed scripts). Everything else I use was already listed.
12. Not done (D2 per plan): R5, R6, R9 SQL, `entity_labels.csv`, `eval.py`, USL model.
