# Red flags R1-R9

Part of the [ProcureLens README](../README.md).

From [data/rules/red_flags.yaml](../data/rules/red_flags.yaml). Each flag with SQL is one file in [sql/checks/](../sql/checks/); the
parameters are also loaded into the Zetaris-visible `rules` table.

| ID | Priority | Logic | Limitation (as written in the rules file) |
|---|---|---|---|
| **R1** | must | Supplier incorporated less than 183 days before the award | Needs a Resolver match (GeBIZ has no UEN). Newly formed entities are legitimate for many reasons. |
| **R2** | must | ACRA status is struck off, ceased, in liquidation or similar | ACRA publishes the current status only, so the entity may have been live when it won. |
| **R3** | must | Two or more winning suppliers at one agency share an exact ACRA address, from at least two different name groups | Shared business centres produce benign matches; the Critic's density check reduces this. Group companies with unrelated names are not recognised. |
| **R4** | must | Same agency and supplier: two or more awards under S$90,000 within 90 days that sum to over S$90,000 | **Partial.** GeBIZ here holds tender (ETT) awards only and **no quotation (ETQ) records** (0 of 18,464 rows), so splitting inside the quotation band cannot be seen. Framework call-offs can look like splitting. |
| **R5** | should | Embedding similarity between the supplier's SSIC description and the tender description is below 0.2, and the SSIC division is not a usual fit for the type of work | Uncalibrated; always escalated with confidence at most 0.6. Needs the one-time local model preparation. |
| **R6** | should | One supplier holds 50% or more of an agency's award value in a tender category (at least five tenders), across at least two of its own awards | Ten keyword categories, approximate. Specialised categories legitimately have few suppliers. |
| **R7** | stretch | Supplier has former names (informational) | **Not implemented**: it is defined in the rules file but has no SQL in `sql/checks/`. |
| **R8** | must | Local-looking name (PTE LTD, PRIVATE LIMITED, LLP) with no ACRA match above threshold | Our ACRA subset is a candidate set; typos and renames can fail to match. A lead for manual lookup. |
| **R9** | should | Awarded supplier is not rank 1 in the published evaluation scores | **Synthetic internal records only**; no real evaluation data is used. Ties are not flagged. |

Details and boundary cases: [docs/handover/d2-red-flags.md](../docs/handover/d2-red-flags.md) and [docs/handover/d1-data.md](../docs/handover/d1-data.md).
