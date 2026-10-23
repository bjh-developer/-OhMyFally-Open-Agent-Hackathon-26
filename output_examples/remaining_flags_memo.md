# Procurement review memo: Synthetic Review Agency
Period 2025-01-01 to 2025-12-31. Run `run_20261023_153325_492c5c`.

**Six escalated procurement findings for Synthetic Review Agency during 2025-01-01 to 2025-12-31 are identified as an anomaly for review. QUILLORA TEST BAKERY PTE. LTD. was awarded S$120,000 for tender PLT000ETT25000007 on 2025-03-01 with a business description cosine similarity of 0.039395, below the 0.2 threshold. VELORIN TEST LOGISTICS PTE. LTD. received five S$10,000 tenders from January to May 2025 and holds S$50,000 of S$60,000 (83.33%) in the transport_and_logistics category across six tenders. These matters are an anomaly for review and may indicate a concern that requires auditor judgement.**

> Automated screening output. Each item is an anomaly for review that may indicate a procurement-integrity concern, and requires auditor judgement. It is not a finding of wrongdoing.

## Findings (6 awards in 6 entries)
### 1. [R5] QUILLORA TEST BAKERY PTE. LTD.: PLT000ETT25000007 (escalated, priority 61)
Supplier line of business far from tender: QUILLORA TEST BAKERY PTE. LTD. was awarded PLT000ETT25000007 by Synthetic Review Agency (S$120,000, 2025-03-01). Anomaly for review: tender description "Provision of computer software development and computer network server support services" versus registered activity "MANUFACTURE OF BREAD, CAKES AND CONFECTIONERY" has cosine similarity 0.039395 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN T99ZZ0007H
- Metric: business_description_cosine_similarity = 0.039395 (threshold 0.2)
- Evidence: Zetaris query `e66ea877-dd67-46b8-9460-d1f4526dda47` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 1 row(s)
- Note: Critic re-ran the SQL (query e66ea877-dd67-46b8-9460-d1f4526dda47) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 2. [R6] VELORIN TEST LOGISTICS PTE. LTD.: PLT000ETT25000080 (escalated, priority 60)
Supplier concentration within a category: VELORIN TEST LOGISTICS PTE. LTD. was awarded PLT000ETT25000080 by Synthetic Review Agency (S$10,000, 2025-01-10). Anomaly for review: in keyword category transport_and_logistics, this supplier holds S$50000.00 of S$60000.00 (83.33%) across 6 category tenders in this scope. Specialised markets and broad categories may explain concentration; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN T99ZZ0008J
- Metric: supplier_category_value_share = 0.833333 (threshold 0.5)
- Evidence: Zetaris query `21e700cc-e420-49a5-bd07-294fd600dae5` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, 5 row(s)
- Why it matters: AGO has noted that agencies should watch how contracts are spread across vendors, since a good spread keeps prices competitive (one vendor held 38 per cent). ([AGO FY2021/22, p. 6 (PDF p.15)](https://isomer-user-content.by.gov.sg/357/5ac84682-6d16-4123-a91b-e1c80a6f1b9a/ar_fy2021_22.pdf#page=15))
- Note: Critic re-ran the SQL (query 21e700cc-e420-49a5-bd07-294fd600dae5) and confirmed the cited row.
- Note: Escalated to human review: should-have flag

### 3. [R6] VELORIN TEST LOGISTICS PTE. LTD.: PLT000ETT25000081 (escalated, priority 60)
Supplier concentration within a category: VELORIN TEST LOGISTICS PTE. LTD. was awarded PLT000ETT25000081 by Synthetic Review Agency (S$10,000, 2025-02-10). Anomaly for review: in keyword category transport_and_logistics, this supplier holds S$50000.00 of S$60000.00 (83.33%) across 6 category tenders in this scope. Specialised markets and broad categories may explain concentration; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN T99ZZ0008J
- Metric: supplier_category_value_share = 0.833333 (threshold 0.5)
- Evidence: Zetaris query `21e700cc-e420-49a5-bd07-294fd600dae5` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, 5 row(s)
- Why it matters: AGO has noted that agencies should watch how contracts are spread across vendors, since a good spread keeps prices competitive (one vendor held 38 per cent). ([AGO FY2021/22, p. 6 (PDF p.15)](https://isomer-user-content.by.gov.sg/357/5ac84682-6d16-4123-a91b-e1c80a6f1b9a/ar_fy2021_22.pdf#page=15))
- Note: Critic re-ran the SQL (query 21e700cc-e420-49a5-bd07-294fd600dae5) and confirmed the cited row.
- Note: Escalated to human review: should-have flag

### 4. [R6] VELORIN TEST LOGISTICS PTE. LTD.: PLT000ETT25000082 (escalated, priority 60)
Supplier concentration within a category: VELORIN TEST LOGISTICS PTE. LTD. was awarded PLT000ETT25000082 by Synthetic Review Agency (S$10,000, 2025-03-10). Anomaly for review: in keyword category transport_and_logistics, this supplier holds S$50000.00 of S$60000.00 (83.33%) across 6 category tenders in this scope. Specialised markets and broad categories may explain concentration; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN T99ZZ0008J
- Metric: supplier_category_value_share = 0.833333 (threshold 0.5)
- Evidence: Zetaris query `21e700cc-e420-49a5-bd07-294fd600dae5` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, 5 row(s)
- Why it matters: AGO has noted that agencies should watch how contracts are spread across vendors, since a good spread keeps prices competitive (one vendor held 38 per cent). ([AGO FY2021/22, p. 6 (PDF p.15)](https://isomer-user-content.by.gov.sg/357/5ac84682-6d16-4123-a91b-e1c80a6f1b9a/ar_fy2021_22.pdf#page=15))
- Note: Critic re-ran the SQL (query 21e700cc-e420-49a5-bd07-294fd600dae5) and confirmed the cited row.
- Note: Escalated to human review: should-have flag

### 5. [R6] VELORIN TEST LOGISTICS PTE. LTD.: PLT000ETT25000083 (escalated, priority 60)
Supplier concentration within a category: VELORIN TEST LOGISTICS PTE. LTD. was awarded PLT000ETT25000083 by Synthetic Review Agency (S$10,000, 2025-04-10). Anomaly for review: in keyword category transport_and_logistics, this supplier holds S$50000.00 of S$60000.00 (83.33%) across 6 category tenders in this scope. Specialised markets and broad categories may explain concentration; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN T99ZZ0008J
- Metric: supplier_category_value_share = 0.833333 (threshold 0.5)
- Evidence: Zetaris query `21e700cc-e420-49a5-bd07-294fd600dae5` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, 5 row(s)
- Why it matters: AGO has noted that agencies should watch how contracts are spread across vendors, since a good spread keeps prices competitive (one vendor held 38 per cent). ([AGO FY2021/22, p. 6 (PDF p.15)](https://isomer-user-content.by.gov.sg/357/5ac84682-6d16-4123-a91b-e1c80a6f1b9a/ar_fy2021_22.pdf#page=15))
- Note: Critic re-ran the SQL (query 21e700cc-e420-49a5-bd07-294fd600dae5) and confirmed the cited row.
- Note: Escalated to human review: should-have flag

### 6. [R6] VELORIN TEST LOGISTICS PTE. LTD.: PLT000ETT25000084 (escalated, priority 60)
Supplier concentration within a category: VELORIN TEST LOGISTICS PTE. LTD. was awarded PLT000ETT25000084 by Synthetic Review Agency (S$10,000, 2025-05-10). Anomaly for review: in keyword category transport_and_logistics, this supplier holds S$50000.00 of S$60000.00 (83.33%) across 6 category tenders in this scope. Specialised markets and broad categories may explain concentration; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN T99ZZ0008J
- Metric: supplier_category_value_share = 0.833333 (threshold 0.5)
- Evidence: Zetaris query `21e700cc-e420-49a5-bd07-294fd600dae5` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, 5 row(s)
- Why it matters: AGO has noted that agencies should watch how contracts are spread across vendors, since a good spread keeps prices competitive (one vendor held 38 per cent). ([AGO FY2021/22, p. 6 (PDF p.15)](https://isomer-user-content.by.gov.sg/357/5ac84682-6d16-4123-a91b-e1c80a6f1b9a/ar_fy2021_22.pdf#page=15))
- Note: Critic re-ran the SQL (query 21e700cc-e420-49a5-bd07-294fd600dae5) and confirmed the cited row.
- Note: Escalated to human review: should-have flag

## Limitations
- R1: Needs a Resolver match (GeBIZ has no UEN). Unresolved names cannot be tested. Newly formed entities are legitimate for many reasons.
- R2: ACRA publishes the current status only, so the entity may have been live when it won. Compare award_date with the dates in the underlying registry before concluding anything.
- R3: Shared business centres and virtual offices produce benign matches. Address match is on postal code + block + street + level + unit.
- R4: GeBIZ here holds tender (ETT) awards only, no quotation (ETQ) records, so splitting below the quotation band is under-detected. Repeat call-offs under a framework can look like splitting.
- R5: Embedding similarity is noisy; always escalated to human review at low confidence.
- R6: Specialised categories legitimately have few suppliers.
- R8: Our ACRA subset is a candidate set, and renamed or typo'd names may fail to match. Treat as a lead for manual lookup.
- R9: Synthetic internal records for planted tenders only; no real evaluation data is used.
