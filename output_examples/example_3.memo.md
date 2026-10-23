# Procurement review memo: National Parks Board
Period 2023-01-01 to 2025-12-31. Run `run_20261023_190400_926912`.

**45 award(s) at National Parks Board flagged as anomalies for review. (narrative unavailable: NightshiftUnavailable; findings below are generated from the SQL evidence directly.)**

> Automated screening output. Each item is an anomaly for review that may indicate a procurement-integrity concern, and requires auditor judgement. It is not a finding of wrongdoing.

## Findings (45 awards in 37 entries)
### 1. [R4] KIM BOCK CONTRACTOR PRIVATE LIMITED: NPB000ETT23000007 (accepted, priority 74)
Possible contract splitting: KIM BOCK CONTRACTOR PRIVATE LIMITED was awarded NPB000ETT23000007 by National Parks Board (S$45,258, 2023-05-02). Anomaly for review: 2 sub-S$90k awards to this supplier within 90 days total S$131482.00 (window starting 2023-02-24), above the S$90k tender threshold. May indicate splitting; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN 197800646E
- Metric: window_total_sgd = 131482 (threshold 90000)
- Evidence: Zetaris query `d748e2d0-8cac-41e7-a65e-930e299cb1d4` over gebiz_pg.awards, 2 row(s)
- Why it matters: AGO has found a contract grown well beyond its approved value without a fresh tender, which, like splitting, can avoid open competition. ([AGO FY2023/24, p. 31 (PDF p.42)](https://isomer-user-content.by.gov.sg/357/baf0b405-c14b-4621-a70e-f370d71bbd76/ar_fy2023_24.pdf#page=42))
- Note: Critic re-ran the SQL (query d748e2d0-8cac-41e7-a65e-930e299cb1d4) and confirmed the cited row.

### 2. [R2] QUORVEX TEST SERVICES PTE. LTD.: PLT000ETT24000002 (accepted, priority 72)
Supplier no longer live in ACRA: QUORVEX TEST SERVICES PTE. LTD. was awarded PLT000ETT24000002 by National Parks Board (S$250,000, 2024-03-12). Anomaly for review: QUORVEX TEST SERVICES PTE. LTD. (Local Company) has current ACRA status "Struck Off"; awarded 2024-03-12. ACRA publishes the current status only, so the entity may have been live at award time. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN T99ZZ0002B
- Metric: acra_status = Struck Off (threshold Live)
- Evidence: Zetaris query `95be2820-319b-48c1-b5c2-1896e1093a05` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, 1 row(s)
- Note: Critic re-ran the SQL (query 95be2820-319b-48c1-b5c2-1896e1093a05) and confirmed the cited row.

### 3. [R8] VORTEXA TEST HOLDINGS PTE. LTD.: PLT000ETT25000005 (accepted, priority 72)
Local-looking supplier with no ACRA match: VORTEXA TEST HOLDINGS PTE. LTD. was awarded PLT000ETT25000005 by National Parks Board (S$320,000, 2025-02-18). Anomaly for review: the supplier name "VORTEXA TEST HOLDINGS PTE. LTD." looks locally registered but no ACRA entity matched above 0.8 (unresolved). Closest candidate: none. May be a renamed, mistyped or unregistered entity; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.80
- Metric: resolver_confidence = 0 (threshold 0.8)
- Evidence: Zetaris query `247efa71-ca2e-4c3a-8280-f94015afd89f` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, 1 row(s)
- Note: Critic re-ran the SQL (query 247efa71-ca2e-4c3a-8280-f94015afd89f) and confirmed the cited row.

### 4. [R4] KIM BOCK CONTRACTOR PRIVATE LIMITED: NPB000ETT22000068 (accepted, priority 56)
Possible contract splitting: KIM BOCK CONTRACTOR PRIVATE LIMITED was awarded NPB000ETT22000068 by National Parks Board (S$86,224, 2023-02-24). Anomaly for review: 2 sub-S$90k awards to this supplier within 90 days total S$131482.00 (window starting 2023-02-24), above the S$90k tender threshold. May indicate splitting; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN 197800646E
- Metric: window_total_sgd = 131482 (threshold 90000)
- Evidence: Zetaris query `d748e2d0-8cac-41e7-a65e-930e299cb1d4` over gebiz_pg.awards, 2 row(s)
- Why it matters: AGO has found a contract grown well beyond its approved value without a fresh tender, which, like splitting, can avoid open competition. ([AGO FY2023/24, p. 31 (PDF p.42)](https://isomer-user-content.by.gov.sg/357/baf0b405-c14b-4621-a70e-f370d71bbd76/ar_fy2023_24.pdf#page=42))
- Note: Critic re-ran the SQL (query d748e2d0-8cac-41e7-a65e-930e299cb1d4) and confirmed the cited row.

### 5. [R3] 2 winning suppliers share 17 CHANGI SOUTH STREET 1 #na-na S486781 (escalated, priority 74)
Anomaly for review: 2 distinct winning suppliers at this agency share the ACRA address 17 CHANGI SOUTH STREET 1 #na-na S486781. Shared business centres can explain this; requires auditor judgement. Together these 5 awards total S$20,414,520.

| Supplier | UEN | Tender | Award date | Amount (S$) |
|---|---|---|---|---|
| BNL WASTE MANAGEMENT PTE. LTD. | 200922620M | NPB000ETT23000037 | 2023-10-02 | 1,577,220 |
| BNL SERVICES PTE LTD | 198801448Z | NPB000ETT24000068 | 2025-01-05 | 3,843,820 |
| BNL SERVICES PTE LTD | 198801448Z | NPB000ETT24000073 | 2025-03-05 | 6,393,100 |
| BNL SERVICES PTE LTD | 198801448Z | NPB000ETT25000006 | 2025-04-17 | 8,544,200 |
| BNL SERVICES PTE LTD | 198801448Z | NPB000ETT25000013 | 2025-05-31 | 56,180 |
- Evidence: Zetaris query `730760e0-d2d3-4be1-9776-bbc8880728c6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, 13 row(s)
- Note: Critic re-ran the SQL (query 730760e0-d2d3-4be1-9776-bbc8880728c6) and confirmed the cited row.
- Note: Address check: level/unit missing (2 entities at the block); escalated to human review.
- Note: Escalated to human review: level and unit are missing, so a shared address cannot be told apart from a shared building.

### 6. [R6] LIAN CHENG CONTRACTING PTE LTD: NPB000ETT24000097 (escalated, priority 74)
Supplier concentration within a category: LIAN CHENG CONTRACTING PTE LTD was awarded NPB000ETT24000097 by National Parks Board (S$4,251,570, 2025-06-10). Anomaly for review: in keyword category cleaning_and_waste, this supplier holds S$11305046.50 of S$20445425.25 (55.29%) across 5 category tenders in this scope. Specialised markets and broad categories may explain concentration; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN 198802394C
- Metric: supplier_category_value_share = 0.552938 (threshold 0.5)
- Evidence: Zetaris query `88402b12-0f80-4636-a01e-b8af5dcc02ec` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, 6 row(s)
- Why it matters: AGO has noted that agencies should watch how contracts are spread across vendors, since a good spread keeps prices competitive (one vendor held 38 per cent). ([AGO FY2021/22, p. 6 (PDF p.15)](https://isomer-user-content.by.gov.sg/357/5ac84682-6d16-4123-a91b-e1c80a6f1b9a/ar_fy2021_22.pdf#page=15))
- Note: Critic re-ran the SQL (query 88402b12-0f80-4636-a01e-b8af5dcc02ec) and confirmed the cited row.
- Note: Escalated to human review: should-have flag

### 7. [R3] 2 winning suppliers share 2 SCIENCE PARK DRIVE #05-01/12 S118222 (escalated, priority 72)
Anomaly for review: 2 distinct winning suppliers at this agency share the ACRA address 2 SCIENCE PARK DRIVE #05-01/12 S118222. Shared business centres can explain this; requires auditor judgement. Together these 2 awards total S$90,339.

| Supplier | UEN | Tender | Award date | Amount (S$) |
|---|---|---|---|---|
| MERCK PTE. LTD. | 199406040G | NPB000ETT24000071 | 2025-05-29 | 88,469 |
| SIGMA-ALDRICH PTE. LTD. | 199403788W | NPB000ETT24000071 | 2025-05-29 | 1,870 |
- Evidence: Zetaris query `730760e0-d2d3-4be1-9776-bbc8880728c6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, 13 row(s)
- Note: Critic re-ran the SQL (query 730760e0-d2d3-4be1-9776-bbc8880728c6) and confirmed the cited row.
- Note: Address check: quiet address (2 entities) with the same unit shared; escalated to human review.
- Note: Escalated to human review: only 2 entities at this address, so the shared unit is ambiguous.

### 8. [R6] LIAN CHENG CONTRACTING PTE LTD: NPB000ETT23000050 (escalated, priority 71)
Supplier concentration within a category: LIAN CHENG CONTRACTING PTE LTD was awarded NPB000ETT23000050 by National Parks Board (S$7,053,476, 2023-11-03). Anomaly for review: in keyword category cleaning_and_waste, this supplier holds S$11305046.50 of S$20445425.25 (55.29%) across 5 category tenders in this scope. Specialised markets and broad categories may explain concentration; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN 198802394C
- Metric: supplier_category_value_share = 0.552938 (threshold 0.5)
- Evidence: Zetaris query `88402b12-0f80-4636-a01e-b8af5dcc02ec` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, 6 row(s)
- Why it matters: AGO has noted that agencies should watch how contracts are spread across vendors, since a good spread keeps prices competitive (one vendor held 38 per cent). ([AGO FY2021/22, p. 6 (PDF p.15)](https://isomer-user-content.by.gov.sg/357/5ac84682-6d16-4123-a91b-e1c80a6f1b9a/ar_fy2021_22.pdf#page=15))
- Note: Critic re-ran the SQL (query 88402b12-0f80-4636-a01e-b8af5dcc02ec) and confirmed the cited row.
- Note: Escalated to human review: should-have flag

### 9. [R6] HENDERSON SECURITY SERVICES PTE. LTD.: NPB000ETT24000058 (escalated, priority 71)
Supplier concentration within a category: HENDERSON SECURITY SERVICES PTE. LTD. was awarded NPB000ETT24000058 by National Parks Board (S$6,420,300, 2024-12-12). Anomaly for review: in keyword category security, this supplier holds S$13399816.00 of S$21580600.00 (62.09%) across 6 category tenders in this scope. Specialised markets and broad categories may explain concentration; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN 200922107K
- Metric: supplier_category_value_share = 0.62092 (threshold 0.5)
- Evidence: Zetaris query `88402b12-0f80-4636-a01e-b8af5dcc02ec` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, 6 row(s)
- Why it matters: AGO has noted that agencies should watch how contracts are spread across vendors, since a good spread keeps prices competitive (one vendor held 38 per cent). ([AGO FY2021/22, p. 6 (PDF p.15)](https://isomer-user-content.by.gov.sg/357/5ac84682-6d16-4123-a91b-e1c80a6f1b9a/ar_fy2021_22.pdf#page=15))
- Note: Critic re-ran the SQL (query 88402b12-0f80-4636-a01e-b8af5dcc02ec) and confirmed the cited row.
- Note: Escalated to human review: should-have flag

### 10. [R6] HENDERSON SECURITY SERVICES PTE. LTD.: NPB000ETT23000057 (escalated, priority 70)
Supplier concentration within a category: HENDERSON SECURITY SERVICES PTE. LTD. was awarded NPB000ETT23000057 by National Parks Board (S$4,930,300, 2023-11-28). Anomaly for review: in keyword category security, this supplier holds S$13399816.00 of S$21580600.00 (62.09%) across 6 category tenders in this scope. Specialised markets and broad categories may explain concentration; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN 200922107K
- Metric: supplier_category_value_share = 0.62092 (threshold 0.5)
- Evidence: Zetaris query `88402b12-0f80-4636-a01e-b8af5dcc02ec` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, 6 row(s)
- Why it matters: AGO has noted that agencies should watch how contracts are spread across vendors, since a good spread keeps prices competitive (one vendor held 38 per cent). ([AGO FY2021/22, p. 6 (PDF p.15)](https://isomer-user-content.by.gov.sg/357/5ac84682-6d16-4123-a91b-e1c80a6f1b9a/ar_fy2021_22.pdf#page=15))
- Note: Critic re-ran the SQL (query 88402b12-0f80-4636-a01e-b8af5dcc02ec) and confirmed the cited row.
- Note: Escalated to human review: should-have flag

### 11. [R6] HENDERSON SECURITY SERVICES PTE. LTD.: NPB000ETT22000083 (escalated, priority 69)
Supplier concentration within a category: HENDERSON SECURITY SERVICES PTE. LTD. was awarded NPB000ETT22000083 by National Parks Board (S$2,049,216, 2023-04-06). Anomaly for review: in keyword category security, this supplier holds S$13399816.00 of S$21580600.00 (62.09%) across 6 category tenders in this scope. Specialised markets and broad categories may explain concentration; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN 200922107K
- Metric: supplier_category_value_share = 0.62092 (threshold 0.5)
- Evidence: Zetaris query `88402b12-0f80-4636-a01e-b8af5dcc02ec` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, 6 row(s)
- Why it matters: AGO has noted that agencies should watch how contracts are spread across vendors, since a good spread keeps prices competitive (one vendor held 38 per cent). ([AGO FY2021/22, p. 6 (PDF p.15)](https://isomer-user-content.by.gov.sg/357/5ac84682-6d16-4123-a91b-e1c80a6f1b9a/ar_fy2021_22.pdf#page=15))
- Note: Critic re-ran the SQL (query 88402b12-0f80-4636-a01e-b8af5dcc02ec) and confirmed the cited row.
- Note: Escalated to human review: should-have flag

### 12. [R6] A D LAB PTE. LTD.: NPB000ETT22000082 (escalated, priority 69)
Supplier concentration within a category: A D LAB PTE. LTD. was awarded NPB000ETT22000082 by National Parks Board (S$1,933,000, 2023-04-18). Anomaly for review: in keyword category professional_services, this supplier holds S$1933000.00 of S$3248589.48 (59.5%) across 10 category tenders in this scope. Specialised markets and broad categories may explain concentration; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN 200706795M
- Metric: supplier_category_value_share = 0.595027 (threshold 0.5)
- Evidence: Zetaris query `88402b12-0f80-4636-a01e-b8af5dcc02ec` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, 6 row(s)
- Why it matters: AGO has noted that agencies should watch how contracts are spread across vendors, since a good spread keeps prices competitive (one vendor held 38 per cent). ([AGO FY2021/22, p. 6 (PDF p.15)](https://isomer-user-content.by.gov.sg/357/5ac84682-6d16-4123-a91b-e1c80a6f1b9a/ar_fy2021_22.pdf#page=15))
- Note: Critic re-ran the SQL (query 88402b12-0f80-4636-a01e-b8af5dcc02ec) and confirmed the cited row.
- Note: Escalated to human review: should-have flag

### 13. [R3] 2 winning suppliers share 1 YUAN CHING ROAD #03-03 S618640 (escalated, priority 66)
Anomaly for review: 2 distinct winning suppliers at this agency share the ACRA address 1 YUAN CHING ROAD #03-03 S618640. Shared business centres can explain this; requires auditor judgement. Together these 2 awards total S$1,636,840.

| Supplier | UEN | Tender | Award date | Amount (S$) |
|---|---|---|---|---|
| CANOPY VETERINARY CENTRE PTE. LTD. | 202222493K | NPB000ETT23000044 | 2023-10-19 | 1,021,480 |
| VETTRUST SINGAPORE PTE. LTD. | 202032165C | NPB000ETT24000033 | 2024-09-13 | 615,360 |
- Evidence: Zetaris query `730760e0-d2d3-4be1-9776-bbc8880728c6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, 13 row(s)
- Note: Critic re-ran the SQL (query 730760e0-d2d3-4be1-9776-bbc8880728c6) and confirmed the cited row.
- Note: Address check: quiet address (2 entities) with the same unit shared; escalated to human review.
- Note: Escalated to human review: only 2 entities at this address, so the shared unit is ambiguous.

### 14. [R3] 2 winning suppliers share 33 MARSILING IND ESTATE ROAD 3 #07-06 S739256 (escalated, priority 63)
Anomaly for review: 2 distinct winning suppliers at this agency share the ACRA address 33 MARSILING IND ESTATE ROAD 3 #07-06 S739256. Shared business centres can explain this; requires auditor judgement. Together these 2 awards total S$26,532.

| Supplier | UEN | Tender | Award date | Amount (S$) |
|---|---|---|---|---|
| FISHER SCIENTIFIC PTE LTD | 197301974D | NPB000ETT24000071 | 2025-05-29 | 22,805 |
| LIFE TECHNOLOGIES HOLDINGS PTE. LTD. | 200104491K | NPB000ETT24000071 | 2025-05-29 | 3,728 |
- Evidence: Zetaris query `730760e0-d2d3-4be1-9776-bbc8880728c6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, 13 row(s)
- Note: Critic re-ran the SQL (query 730760e0-d2d3-4be1-9776-bbc8880728c6) and confirmed the cited row.
- Note: Address check: quiet address (3 entities) with the same unit shared; escalated to human review.
- Note: Escalated to human review: only 3 entities at this address, so the shared unit is ambiguous.

### 15. [R5] LANDSCAPE ENGINEERING PTE LTD: NPB000ETT24000065 (escalated, priority 60)
Supplier line of business far from tender: LANDSCAPE ENGINEERING PTE LTD was awarded NPB000ETT24000065 by National Parks Board (S$9,825,507, 2025-02-05). Anomaly for review: tender description "PROPOSED DEVELOPMENT OF PARK CONNECTOR ALONG KRANJI EXPRESSWAY (KJE), WOODLANDS ROAD, SUNGEI LANCHAR, PAN ISLAND EXPRESSWAY (PIE) AND PIONEER ROAD NORTH" versus registered activity "STRUCTURAL STEEL FABRICATION, ELECTRICAL AND MECHANICAL ENGINEERING WORKS" has cosine similarity 0.091993 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 199905617N
- Metric: business_description_cosine_similarity = 0.091993 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 16. [R5] SUMMER POND & LANDSCAPING PTE. LTD.: NPB000ETT25000003 (escalated, priority 59)
Supplier line of business far from tender: SUMMER POND & LANDSCAPING PTE. LTD. was awarded NPB000ETT25000003 by National Parks Board (S$7,203,080, 2025-03-27). Anomaly for review: tender description "PROVISION OF ARBORICULTURE, HORTICULTURE AND TURF MANAGEMENT SERVICES FOR BUKIT TIMAH NATURE RESERVE (BTNR) AND CENTRAL CATCHMENT NATURE RESERVE (CCNR) FOR A PERIOD OF THREE (3) YEARS" versus registered activity "GENERAL CLEANING SERVICES (81211)" has cosine similarity 0.153925 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 200307000D
- Metric: business_description_cosine_similarity = 0.153925 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 17. [R5] LANDSCAPE ENGINEERING PTE LTD: NPB000ETT24000063 (escalated, priority 59)
Supplier line of business far from tender: LANDSCAPE ENGINEERING PTE LTD was awarded NPB000ETT24000063 by National Parks Board (S$6,888,715, 2024-12-24). Anomaly for review: tender description "Proposed Development of Teachers' Estate Park" versus registered activity "STRUCTURAL STEEL FABRICATION, ELECTRICAL AND MECHANICAL ENGINEERING WORKS" has cosine similarity 0.002851 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 199905617N
- Metric: business_description_cosine_similarity = 0.002851 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 18. [R5] SUMMER POND & LANDSCAPING PTE. LTD.: NPB000ETT24000098 (escalated, priority 59)
Supplier line of business far from tender: SUMMER POND & LANDSCAPING PTE. LTD. was awarded NPB000ETT24000098 by National Parks Board (S$6,332,700, 2025-06-09). Anomaly for review: tender description "PROVISION OF ARBORICULTURE, HORTICULTURE AND TURF MAINTENANCE FOR FORT CANNING PARK BRANCH FOR A PERIOD OF THREE (3) YEARS WITH OPTION TO EXTEND FOR UP TO TWO (2) YEARS" versus registered activity "GENERAL CLEANING SERVICES (81211)" has cosine similarity 0.175703 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 200307000D
- Metric: business_description_cosine_similarity = 0.175703 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 19. [R5] LANDSCAPE ENGINEERING PTE LTD: NPB000ETT24000009 (escalated, priority 59)
Supplier line of business far from tender: LANDSCAPE ENGINEERING PTE LTD was awarded NPB000ETT24000009 by National Parks Board (S$5,818,251, 2024-07-24). Anomaly for review: tender description "Proposed development of Punggol Heritage Trail" versus registered activity "STRUCTURAL STEEL FABRICATION, ELECTRICAL AND MECHANICAL ENGINEERING WORKS" has cosine similarity 0.085718 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 199905617N
- Metric: business_description_cosine_similarity = 0.085718 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 20. [R5] CAMPHORA PTE. LTD.: NPB000ETT22000095 (escalated, priority 58)
Supplier line of business far from tender: CAMPHORA PTE. LTD. was awarded NPB000ETT22000095 by National Parks Board (S$5,246,507, 2023-04-24). Anomaly for review: tender description "APPOINTMENT OF A PANEL OF CONSULTANTS FOR THE PROVISION OF ENVIRONMENTAL CONSULTATION SERVICES FOR A PERIOD OF THREE (3) YEARS" versus registered activity "ARBORICULTURE" has cosine similarity 0.12215 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 200714651H
- Metric: business_description_cosine_similarity = 0.12215 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 21. [R3] 2 winning suppliers share 211 WOODLANDS AVENUE 9 #08-78/79 S738960 (escalated, priority 57)
Anomaly for review: 2 distinct winning suppliers at this agency share the ACRA address 211 WOODLANDS AVENUE 9 #08-78/79 S738960. Shared business centres can explain this; requires auditor judgement. Together these 2 awards total S$20,488.

| Supplier | UEN | Tender | Award date | Amount (S$) |
|---|---|---|---|---|
| CHEMOSCIENCE PTE LTD | 198204729R | NPB000ETT24000071 | 2025-05-29 | 348 |
| SCIENTIFIC RESOURCES PTE LTD | 199900346R | NPB000ETT24000071 | 2025-05-29 | 20,140 |
- Evidence: Zetaris query `730760e0-d2d3-4be1-9776-bbc8880728c6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, 13 row(s)
- Note: Critic re-ran the SQL (query 730760e0-d2d3-4be1-9776-bbc8880728c6) and confirmed the cited row.
- Note: Address check: quiet address (3 entities) with the same unit shared; escalated to human review.
- Note: Escalated to human review: only 3 entities at this address, so the shared unit is ambiguous.

### 22. [R5] TECHNO CE PTE. LTD.: NPB000ETT24000039 (escalated, priority 57)
Supplier line of business far from tender: TECHNO CE PTE. LTD. was awarded NPB000ETT24000039 by National Parks Board (S$3,554,747, 2025-01-07). Anomaly for review: tender description "PROPOSED DESIGN AND BUILD OF INCLUSIVE PLAYGROUND AT SUN PLAZA PARK INCLUDING 5 YEARS MAINTENANCE OF PLAY EQUIPMENT" versus registered activity "IMPORTERS & EXPORTERS FOR TECHNOLOGIES EQUUIPMENTS" has cosine similarity 0.071002 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 200210947C
- Metric: business_description_cosine_similarity = 0.071002 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 23. [R5] WSH EXPERTS PTE. LTD.: NPB000ETT22000100 (escalated, priority 56)
Supplier line of business far from tender: WSH EXPERTS PTE. LTD. was awarded NPB000ETT22000100 by National Parks Board (S$1,922,280, 2023-05-23). Anomaly for review: tender description "PROVISION OF A MANAGING AGENT FOR FEEDBACK MANAGEMENT SERVICES FOR A PERIOD OF TWO (2) YEARS, WITH AN OPTION FOR ONE (1) YEAR" versus registered activity "OUTSOURCING, CALL CENTRE, INSPECTION, LOGISTICS, QEHS AND OTHER SERVICES" has cosine similarity 0.194522 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 201805323R
- Metric: business_description_cosine_similarity = 0.194522 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 24. [R5] WINSTECH ENGINEERING PTE. LTD.: NPB000ETT24000021 (escalated, priority 55)
Supplier line of business far from tender: WINSTECH ENGINEERING PTE. LTD. was awarded NPB000ETT24000021 by National Parks Board (S$1,342,000, 2024-09-24). Anomaly for review: tender description "SEWAGE AND SLUDGE REMOVAL FROM SISTERS' ISLANDS MARINE PARK FOR A PERIOD OF THREE (3) YEARS" versus registered activity "ELECTRICITY, PLUMBING & OTHER CONSTRUCTION INSTALLATION" has cosine similarity 0.106458 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 200201329H
- Metric: business_description_cosine_similarity = 0.106458 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 25. [R5] SILVERSKY PTE. LTD.: NPB000ETT24000050 (escalated, priority 53)
Supplier line of business far from tender: SILVERSKY PTE. LTD. was awarded NPB000ETT24000050 by National Parks Board (S$625,627, 2025-01-15). Anomaly for review: tender description "PROVISION OF ANIMAL FOOD & ANIMAL LITTER SUPPLIES FOR A PERIOD OF 3 YEARS" versus registered activity "GENERAL TRADING" has cosine similarity 0.061477 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 200308322K
- Metric: business_description_cosine_similarity = 0.061477 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 26. [R5] QUORVEX TEST SERVICES PTE. LTD.: PLT000ETT24000002 (escalated, priority 50)
Supplier line of business far from tender: QUORVEX TEST SERVICES PTE. LTD. was awarded PLT000ETT24000002 by National Parks Board (S$250,000, 2024-03-12). Anomaly for review: tender description "PLANTED TEST TENDER (FICTIONAL)" versus registered activity "OTHER INFORMATION TECHNOLOGY SERVICE ACTIVITIES" has cosine similarity -0.00792 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN T99ZZ0002B
- Metric: business_description_cosine_similarity = -0.00792 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 27. [R5] PRECISION TECHNOLOGIES PTE LTD: NPB000ETT23000016 (escalated, priority 50)
Supplier line of business far from tender: PRECISION TECHNOLOGIES PTE LTD was awarded NPB000ETT23000016 by National Parks Board (S$236,220, 2023-07-18). Anomaly for review: tender description "SUPPLY AND DELIVERY OF BUGGIES FOR A PERIOD OF TWO (2) YEARS" versus registered activity "MANUF/ASSEMBLY/REPAIR/SERVICING AIRCRAFT & PARTS" has cosine similarity 0.194971 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 198306012C
- Metric: business_description_cosine_similarity = 0.194971 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 28. [R5] INTERNET X PTE. LTD.: NPB000ETT23000051 (escalated, priority 50)
Supplier line of business far from tender: INTERNET X PTE. LTD. was awarded NPB000ETT23000051 by National Parks Board (S$202,712, 2024-01-04). Anomaly for review: tender description "DESIGN, DEVELOPMENT, IMPLEMENTATION, COMMISSIONING AND SUPPORT OF A GARDEN CITY FUND'S DONOR DATABASE" versus registered activity "DEVELOPMENT OF E-COMMERCE WEBPAGE AND APPLICATIONS" has cosine similarity 0.058969 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 201320061W
- Metric: business_description_cosine_similarity = 0.058969 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 29. [R5] GREEN AVENTURINE TECHNOLOGIES: NPB000ETT24000050 (escalated, priority 49)
Supplier line of business far from tender: GREEN AVENTURINE TECHNOLOGIES was awarded NPB000ETT24000050 by National Parks Board (S$165,298, 2025-01-15). Anomaly for review: tender description "PROVISION OF ANIMAL FOOD & ANIMAL LITTER SUPPLIES FOR A PERIOD OF 3 YEARS" versus registered activity "MANUFACTURE AND REPAIR OF OTHER GENERAL PURPOSE MACHINERY AND EQUIPMENT" has cosine similarity 0.130039 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 53478233K
- Metric: business_description_cosine_similarity = 0.130039 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 30. [R5] CA M&E ENGINEERING PTE. LTD.: NPB000ETT23000036 (escalated, priority 48)
Supplier line of business far from tender: CA M&E ENGINEERING PTE. LTD. was awarded NPB000ETT23000036 by National Parks Board (S$96,300, 2024-01-31). Anomaly for review: tender description "TENDER FOR REPLACEMENT OF PASSENGER LIFT AT RAFFLES BUILDING" versus registered activity "DESIGN,SUPPLY,INSTALL,MAINTENANCE OF BMS,ACMV,COMMUNICATION & SECURITY SYSTEMS" has cosine similarity 0.116328 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 200501189G
- Metric: business_description_cosine_similarity = 0.116328 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 31. [R5] MERCK PTE. LTD.: NPB000ETT24000071 (escalated, priority 48)
Supplier line of business far from tender: MERCK PTE. LTD. was awarded NPB000ETT24000071 by National Parks Board (S$88,469, 2025-05-29). Anomaly for review: tender description "THREE-YEAR PERIOD CONTRACT FOR THE SUPPLY AND DELIVERY OF CONSUMABLES" versus registered activity "GENERAL TRADING COMPANY" has cosine similarity 0.198769 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 199406040G
- Metric: business_description_cosine_similarity = 0.198769 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 32. [R5] REPORTNOW ASIA PACIFIC PTE. LTD.: NPB000ETT25000020 (escalated, priority 47)
Supplier line of business far from tender: REPORTNOW ASIA PACIFIC PTE. LTD. was awarded NPB000ETT25000020 by National Parks Board (S$80,000, 2025-11-18). Anomaly for review: tender description "Request For Proposal (RFP) on Open Innovation Platform (OIP) for the Solution to Develop and Enhance a Wildlife Detection and Deterrent System, Specially for Long-Tailed Macaques" versus registered activity "SALE OF ENTERPRISE SOFTWARE APPL&PROV OF SUPPORT,TRAINING&CUSTOMIZE SERVICE" has cosine similarity 0.151465 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 202034044D
- Metric: business_description_cosine_similarity = 0.151465 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 33. [R5] JUST KEEP THINKING: NPB000ETT25000023 (escalated, priority 47)
Supplier line of business far from tender: JUST KEEP THINKING was awarded NPB000ETT25000023 by National Parks Board (S$75,600, 2025-08-20). Anomaly for review: tender description "OUTREACH AND EDUCATION SERVICES FOR SISTERS' ISLANDS MARINE PARK FOR A PERIOD OF ONE (1) YEAR, WITH OPTION FOR ANOTHER TWO (2) YEARS" versus registered activity "CREATE VIDEO ADS AND GFX ADS" has cosine similarity 0.037974 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 53409170M
- Metric: business_description_cosine_similarity = 0.037974 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 34. [R5] WETEC PTE. LTD.: NPB000ETT24000071 (escalated, priority 46)
Supplier line of business far from tender: WETEC PTE. LTD. was awarded NPB000ETT24000071 by National Parks Board (S$55,870, 2025-05-29). Anomaly for review: tender description "THREE-YEAR PERIOD CONTRACT FOR THE SUPPLY AND DELIVERY OF CONSUMABLES" versus registered activity "SUPPLY/INSTALL WATER, GEOTECHNICAL CONTROL/MONITORING SYSTEMS IN CIVIL WORKS" has cosine similarity 0.183949 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 200810252Z
- Metric: business_description_cosine_similarity = 0.183949 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 35. [R5] METTLER-TOLEDO (S) PTE LTD: NPB000ETT24000071 (escalated, priority 41)
Supplier line of business far from tender: METTLER-TOLEDO (S) PTE LTD was awarded NPB000ETT24000071 by National Parks Board (S$7,000, 2025-05-29). Anomaly for review: tender description "THREE-YEAR PERIOD CONTRACT FOR THE SUPPLY AND DELIVERY OF CONSUMABLES" versus registered activity "MANUF OF ELECTRONIC ENGINEERING SCIENTIFIC INSTRUMENT" has cosine similarity 0.109292 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 199206604Z
- Metric: business_description_cosine_similarity = 0.109292 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 36. [R5] AJJ HEALTHCARE MANAGEMENT PTE. LTD.: NPB000ETT24000071 (escalated, priority 41)
Supplier line of business far from tender: AJJ HEALTHCARE MANAGEMENT PTE. LTD. was awarded NPB000ETT24000071 by National Parks Board (S$5,742, 2025-05-29). Anomaly for review: tender description "THREE-YEAR PERIOD CONTRACT FOR THE SUPPLY AND DELIVERY OF CONSUMABLES" versus registered activity "MANUFACTURE AND REPAIR OF HIFU MACHINE AND OTHER MEDICAL EQUIPMENT" has cosine similarity 0.153464 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 201531723M
- Metric: business_description_cosine_similarity = 0.153464 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 37. [R5] SIGMA-ALDRICH PTE. LTD.: NPB000ETT24000071 (escalated, priority 38)
Supplier line of business far from tender: SIGMA-ALDRICH PTE. LTD. was awarded NPB000ETT24000071 by National Parks Board (S$1,870, 2025-05-29). Anomaly for review: tender description "THREE-YEAR PERIOD CONTRACT FOR THE SUPPLY AND DELIVERY OF CONSUMABLES" versus registered activity "GENERAL TRADING COMPANY" has cosine similarity 0.198769 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 199403788W
- Metric: business_description_cosine_similarity = 0.198769 (threshold 0.2)
- Evidence: Zetaris query `1019b83d-97de-40d7-af93-436a711e1e9a` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 22 row(s)
- Note: Critic re-ran the SQL (query 1019b83d-97de-40d7-af93-436a711e1e9a) and confirmed the cited row.
- Note: Escalated to human review: low confidence

## Limitations
- R1: Needs a Resolver match (GeBIZ has no UEN). Unresolved names cannot be tested. Newly formed entities are legitimate for many reasons.
- R2: ACRA publishes the current status only, so the entity may have been live when it won. Compare award_date with the dates in the underlying registry before concluding anything.
- R3: Shared business centres and virtual offices produce benign matches. Address match is on postal code + block + street + level + unit.
- R4: GeBIZ here holds tender (ETT) awards only, no quotation (ETQ) records, so splitting below the quotation band is under-detected. Repeat call-offs under a framework can look like splitting.
- R5: Embedding similarity is uncalibrated and business descriptions can be broad; always escalated at confidence at most 0.6. Only description pairs with a stored Resolver confidence of at least 0.92 and nonempty descriptions are scored. Run prepare_r5.py after seeding or source changes.
- R6: Ten first-match keyword categories are approximate; specialised categories legitimately have few suppliers. Requires at least five distinct category tenders, compares positive award value within the requested agency and period, and groups by supplier name without consolidating aliases.
- R8: Our ACRA subset is a candidate set, and renamed or typo'd names may fail to match. Treat as a lead for manual lookup.
- R9: Synthetic internal records only; no real evaluation data is used. Compares weighted scores only when every bidder has the same complete criteria and weights, weights sum to one and scores are between 0 and 100. Tied best scores are not flagged; documented award exceptions still require review.
