# Data sources, licences and privacy

Part of the [ProcureLens README](../README.md).

| Source | What we used | Licence |
|---|---|---|
| **GeBIZ awards** (data.gov.sg dataset `d_acde1106003906a75c3fa052592f2fcb`) | 18,464 rows, Apr 2021 to Mar 2026. Tender (ETT) awards only, no UEN. The committed sample is 2,465 awards for HDB, People's Association and National Parks Board. | Singapore Open Data Licence v1.0 |
| **ACRA Information on Corporate Entities** (data.gov.sg collection 2) | 2,124,508 rows downloaded; a candidate set of 23,067 matched by name is kept locally and **not committed**. The committed sample is 1,226 entities. | Singapore Open Data Licence v1.0 |
| **Auditor-General's Office annual reports** | Eleven verbatim excerpts (FY2021/22 to FY2024/25) in [data/ago/](../data/ago/), each with its source page link | Quoted with attribution; see [data/ago/README.md](../data/ago/README.md) |
| **Planted cases and synthetic internal records** | Written by us: fictional suppliers (UENs `T99ZZ...`, postcodes `9990xx`, `TEST` in every name) | Ours; agents never read `data/eval/planted.json` |

Contains information from GeBIZ and the ACRA register, accessed via data.gov.sg under the Singapore Open Data Licence v1.0.
Counts, regeneration commands and the full list of data weaknesses are in [data/README.md](../data/README.md) and
[docs/handover/d1-data.md](../docs/handover/d1-data.md).

**Privacy.** The repository is public, so the committed ACRA sample is minimised: it keeps only entities the Resolver matched to a
GeBIZ supplier (plus a few candidates for ambiguous names), and blanks `level_no` and `unit_no` for sole proprietorships and
partnerships (85 of the 1,226 rows are of that type). No real person gets a score or a flag by name that GeBIZ does not already publish.
The API has a **public view**: `GET /runs/{run_id}?view=public` and `GET /runs/{run_id}/summary?view=public` replace every supplier name with a
stable alias such as `Supplier-7F3A` (HMAC-SHA256 with `PSEUDONYM_KEY`; fictional `TEST` suppliers stay readable). It fails closed with
`503` if the key is not set. The default view is the auditor's full view. The web UI does not use the public view.
