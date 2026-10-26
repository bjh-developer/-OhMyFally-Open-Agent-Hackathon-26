# Procurement review memo: Housing and Development Board
Period 2024-04-01 to 2025-03-31. Run `run_20261023_185852_8201f9`.

**HDB accepted findings for tenders awarded from 2024-04-01 to 2025-03-31 as anomalies for review, including two sub-S$90,000 awards to GROUND INSTRUMENTATION & ENGINEERING PTE. LTD. totaling S$158,291 above the tender threshold. The accepted items include LCA PRIVATE LIMITED awarded while showing ACRA status Struck Off, distinct winning suppliers sharing addresses that shared business centres can explain, and supplier concentration in the information technology category. Each item is an anomaly for review and may indicate a concern that requires auditor judgement. Of the findings, 45 were shown, 6 were suppressed, and none were rejected.**

> Automated screening output. Each item is an anomaly for review that may indicate a procurement-integrity concern, and requires auditor judgement. It is not a finding of wrongdoing.

## Findings (45 awards in 37 entries)
### 1. [R4] GROUND INSTRUMENTATION & ENGINEERING PTE. LTD.: HDB000ETT25000037 (accepted, priority 59)
Possible contract splitting: GROUND INSTRUMENTATION & ENGINEERING PTE. LTD. was awarded HDB000ETT25000037 by Housing and Development Board (S$79,701, 2025-03-24). Anomaly for review: 2 sub-S$90k awards to this supplier within 90 days total S$158291.00 (window starting 2025-03-24), above the S$90k tender threshold. May indicate splitting; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN 200618674H
- Metric: window_total_sgd = 158291 (threshold 90000)
- Evidence: Zetaris query `94f77d4d-1ca8-4b22-a76b-1c33a1df961a` over gebiz_pg.awards, 2 row(s)
- Why it matters: AGO has found a contract grown well beyond its approved value without a fresh tender, which, like splitting, can avoid open competition. ([AGO FY2023/24, p. 31 (PDF p.42)](https://isomer-user-content.by.gov.sg/357/baf0b405-c14b-4621-a70e-f370d71bbd76/ar_fy2023_24.pdf#page=42))
- Note: Critic re-ran the SQL (query 94f77d4d-1ca8-4b22-a76b-1c33a1df961a) and confirmed the cited row.

### 2. [R4] GROUND INSTRUMENTATION & ENGINEERING PTE. LTD.: HDB000ETT24000286 (accepted, priority 59)
Possible contract splitting: GROUND INSTRUMENTATION & ENGINEERING PTE. LTD. was awarded HDB000ETT24000286 by Housing and Development Board (S$78,590, 2025-03-28). Anomaly for review: 2 sub-S$90k awards to this supplier within 90 days total S$158291.00 (window starting 2025-03-24), above the S$90k tender threshold. May indicate splitting; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN 200618674H
- Metric: window_total_sgd = 158291 (threshold 90000)
- Evidence: Zetaris query `94f77d4d-1ca8-4b22-a76b-1c33a1df961a` over gebiz_pg.awards, 2 row(s)
- Why it matters: AGO has found a contract grown well beyond its approved value without a fresh tender, which, like splitting, can avoid open competition. ([AGO FY2023/24, p. 31 (PDF p.42)](https://isomer-user-content.by.gov.sg/357/baf0b405-c14b-4621-a70e-f370d71bbd76/ar_fy2023_24.pdf#page=42))
- Note: Critic re-ran the SQL (query 94f77d4d-1ca8-4b22-a76b-1c33a1df961a) and confirmed the cited row.

### 3. [R2] LCA PRIVATE LIMITED: HDB000ETT24000183 (accepted, priority 57)
Supplier no longer live in ACRA: LCA PRIVATE LIMITED was awarded HDB000ETT24000183 by Housing and Development Board (S$16,341, 2024-11-01). Anomaly for review: LCA PRIVATE LIMITED (Local Company) has current ACRA status "Struck Off"; awarded 2024-11-01. ACRA publishes the current status only, so the entity may have been live at award time. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN 201608442G
- Metric: acra_status = Struck Off (threshold Live)
- Evidence: Zetaris query `8c0e8611-a808-437e-9a9a-8ebc46c32ed1` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, 1 row(s)
- Note: Critic re-ran the SQL (query 8c0e8611-a808-437e-9a9a-8ebc46c32ed1) and confirmed the cited row.

### 4. [R3] 2 winning suppliers share 430 TAGORE INDUSTRIAL AVENUE #na-na S787810 (escalated, priority 91)
Anomaly for review: 2 distinct winning suppliers at this agency share the ACRA address 430 TAGORE INDUSTRIAL AVENUE #na-na S787810. Shared business centres can explain this; requires auditor judgement. Together these 4 awards total S$344,910,000.

| Supplier | UEN | Tender | Award date | Amount (S$) |
|---|---|---|---|---|
| LBD ENGINEERING PTE. LTD. | 200803146G | HDB000ETT24000011 | 2024-05-31 | 175,000,000 |
| THONG HUAT BROTHERS (PTE) LIMITED | 197201236H | HDB000ETT24000087 | 2024-09-30 | 98,000,000 |
| THONG HUAT BROTHERS (PTE) LIMITED | 197201236H | HDB000ETT24000147 | 2025-01-31 | 37,555,000 |
| THONG HUAT BROTHERS (PTE) LIMITED | 197201236H | HDB000ETT24000151 | 2025-01-31 | 34,355,000 |
- Evidence: Zetaris query `53b9c887-70ef-4c80-8154-4063477a9fd2` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, 18 row(s)
- Note: Critic re-ran the SQL (query 53b9c887-70ef-4c80-8154-4063477a9fd2) and confirmed the cited row.
- Note: Address check: level/unit missing (2 entities at the block); escalated to human review.
- Note: Escalated to human review: level and unit are missing, so a shared address cannot be told apart from a shared building.

### 5. [R3] 2 winning suppliers share 1 GATEWAY DRIVE #25-01 S608531 (escalated, priority 78)
Anomaly for review: 2 distinct winning suppliers at this agency share the ACRA address 1 GATEWAY DRIVE #25-01 S608531. Shared business centres can explain this; requires auditor judgement. Together these 3 awards total S$1,190,560.

| Supplier | UEN | Tender | Award date | Amount (S$) |
|---|---|---|---|---|
| CPG FACILITIES MANAGEMENT PTE LTD | 199806367G | HDB000ETT24000094 | 2024-08-08 | 1,039,680 |
| CPG CONSULTANTS PTE LTD | 199806365E | HDB000ETT24000136 | 2024-09-10 | 72,000 |
| CPG FACILITIES MANAGEMENT PTE LTD | 199806367G | HDB000ETT24000226 | 2025-01-24 | 78,880 |
- Evidence: Zetaris query `53b9c887-70ef-4c80-8154-4063477a9fd2` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, 18 row(s)
- Note: Critic re-ran the SQL (query 53b9c887-70ef-4c80-8154-4063477a9fd2) and confirmed the cited row.
- Note: Address check: quiet address (3 entities) with the same unit shared; escalated to human review.
- Note: Escalated to human review: only 3 entities at this address, so the shared unit is ambiguous.

### 6. [R3] 2 winning suppliers share 5 ANG MO KIO STREET 62 #na-na S569141 (escalated, priority 77)
Anomaly for review: 2 distinct winning suppliers at this agency share the ACRA address 5 ANG MO KIO STREET 62 #na-na S569141. Shared business centres can explain this; requires auditor judgement. Together these 3 awards total S$2,766,538.

| Supplier | UEN | Tender | Award date | Amount (S$) |
|---|---|---|---|---|
| NCS COMMUNICATIONS ENGINEERING PTE. LTD. | 199603123G | HDB000ETT23000261 | 2024-04-19 | 2,126,937 |
| NCS COMMUNICATIONS ENGINEERING PTE. LTD. | 199603123G | HDB000ETT24000010 | 2024-07-10 | 629,975 |
| NCS PTE. LTD. | 198101793G | HDB000ETT24000200 | 2024-12-04 | 9,626 |
- Evidence: Zetaris query `53b9c887-70ef-4c80-8154-4063477a9fd2` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, 18 row(s)
- Note: Critic re-ran the SQL (query 53b9c887-70ef-4c80-8154-4063477a9fd2) and confirmed the cited row.
- Note: Address check: level/unit missing (2 entities at the block); escalated to human review.
- Note: Escalated to human review: level and unit are missing, so a shared address cannot be told apart from a shared building.

### 7. [R6] ST ENGINEERING TRAINING & SIMULATION SYSTEMS PTE. LTD.: HDB000ETT24000065 (escalated, priority 74)
Supplier concentration within a category: ST ENGINEERING TRAINING & SIMULATION SYSTEMS PTE. LTD. was awarded HDB000ETT24000065 by Housing and Development Board (S$21,506,353, 2024-06-26). Anomaly for review: in keyword category information_technology, this supplier holds S$21506353.29 of S$26384891.04 (81.51%) across 12 category tenders in this scope. Specialised markets and broad categories may explain concentration; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN 199607423R
- Metric: supplier_category_value_share = 0.815101 (threshold 0.5)
- Evidence: Zetaris query `3de294b5-9ff0-4acb-9f93-d0a78a796766` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, 3 row(s)
- Why it matters: AGO has noted that agencies should watch how contracts are spread across vendors, since a good spread keeps prices competitive (one vendor held 38 per cent). ([AGO FY2021/22, p. 6 (PDF p.15)](https://isomer-user-content.by.gov.sg/357/5ac84682-6d16-4123-a91b-e1c80a6f1b9a/ar_fy2021_22.pdf#page=15))
- Note: Critic re-ran the SQL (query 3de294b5-9ff0-4acb-9f93-d0a78a796766) and confirmed the cited row.
- Note: Escalated to human review: should-have flag

### 8. [R3] 2 winning suppliers share 77 SHARED TEST AVENUE #05-12 S999003 (escalated, priority 73)
Anomaly for review: 2 distinct winning suppliers at this agency share the ACRA address 77 SHARED TEST AVENUE #05-12 S999003. Shared business centres can explain this; requires auditor judgement. Together these 2 awards total S$310,000.

| Supplier | UEN | Tender | Award date | Amount (S$) |
|---|---|---|---|---|
| BRAXTON TEST TRADING PTE. LTD. | T99ZZ0003C | PLT000ETT24000003 | 2024-05-10 | 150,000 |
| KELVARO TEST SUPPLIES PTE. LTD. | T99ZZ0013D | PLT000ETT24000013 | 2024-06-14 | 160,000 |
- Evidence: Zetaris query `53b9c887-70ef-4c80-8154-4063477a9fd2` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, 18 row(s)
- Note: Critic re-ran the SQL (query 53b9c887-70ef-4c80-8154-4063477a9fd2) and confirmed the cited row.
- Note: Address check: quiet address (2 entities) with the same unit shared; escalated to human review.
- Note: Escalated to human review: only 2 entities at this address, so the shared unit is ambiguous.

### 9. [R6] DHI WATER & ENVIRONMENT (S) PTE. LTD.: HDB000ETT24000073 (escalated, priority 73)
Supplier concentration within a category: DHI WATER & ENVIRONMENT (S) PTE. LTD. was awarded HDB000ETT24000073 by Housing and Development Board (S$14,388,888, 2024-09-05). Anomaly for review: in keyword category professional_services, this supplier holds S$14388888.00 of S$20824603.00 (69.1%) across 14 category tenders in this scope. Specialised markets and broad categories may explain concentration; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN 200301802D
- Metric: supplier_category_value_share = 0.690956 (threshold 0.5)
- Evidence: Zetaris query `3de294b5-9ff0-4acb-9f93-d0a78a796766` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, 3 row(s)
- Why it matters: AGO has noted that agencies should watch how contracts are spread across vendors, since a good spread keeps prices competitive (one vendor held 38 per cent). ([AGO FY2021/22, p. 6 (PDF p.15)](https://isomer-user-content.by.gov.sg/357/5ac84682-6d16-4123-a91b-e1c80a6f1b9a/ar_fy2021_22.pdf#page=15))
- Note: Critic re-ran the SQL (query 3de294b5-9ff0-4acb-9f93-d0a78a796766) and confirmed the cited row.
- Note: Escalated to human review: should-have flag

### 10. [R6] HITACHI ELEVATOR ASIA PTE. LTD.: HDB000ETT23000217 (escalated, priority 72)
Supplier concentration within a category: HITACHI ELEVATOR ASIA PTE. LTD. was awarded HDB000ETT23000217 by Housing and Development Board (S$12,294,565, 2024-04-18). Anomaly for review: in keyword category transport_and_logistics, this supplier holds S$12294565.00 of S$23968852.43 (51.29%) across 11 category tenders in this scope. Specialised markets and broad categories may explain concentration; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 1.00; UEN 197201468W
- Metric: supplier_category_value_share = 0.512939 (threshold 0.5)
- Evidence: Zetaris query `3de294b5-9ff0-4acb-9f93-d0a78a796766` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, 3 row(s)
- Why it matters: AGO has noted that agencies should watch how contracts are spread across vendors, since a good spread keeps prices competitive (one vendor held 38 per cent). ([AGO FY2021/22, p. 6 (PDF p.15)](https://isomer-user-content.by.gov.sg/357/5ac84682-6d16-4123-a91b-e1c80a6f1b9a/ar_fy2021_22.pdf#page=15))
- Note: Critic re-ran the SQL (query 3de294b5-9ff0-4acb-9f93-d0a78a796766) and confirmed the cited row.
- Note: Escalated to human review: should-have flag

### 11. [R5] TOA CORPORATION: HDB000ETT23000167 (escalated, priority 72)
Supplier line of business far from tender: TOA CORPORATION was awarded HDB000ETT23000167 by Housing and Development Board (S$108,597,000, 2024-05-31). Anomaly for review: tender description "Infilling Works (Phase 4)" versus registered activity "DEVELOPMENT & CONSTRUCTION WORKS" has cosine similarity 0.131644 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN S64FC1646L
- Metric: business_description_cosine_similarity = 0.131644 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 12. [R5] WING TUCK ENGINEERING PTE LTD: HDB000ETT24000161 (escalated, priority 66)
Supplier line of business far from tender: WING TUCK ENGINEERING PTE LTD was awarded HDB000ETT24000161 by Housing and Development Board (S$36,888,000, 2025-01-31). Anomaly for review: tender description "(A) DESIGN AND BUILD OF UPGRADING PROJECTS FOR G33E; (B) CONTINGENCY WORKS" versus registered activity "CONSTRUCTION, CARPENTRY, STEEL FABRICATION & INSTALLATION WORKS" has cosine similarity 0.173316 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 198801102Z
- Metric: business_description_cosine_similarity = 0.173316 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 13. [R5] COSBY PTE. LTD.: HDB000ETT24000191 (escalated, priority 63)
Supplier line of business far from tender: COSBY PTE. LTD. was awarded HDB000ETT24000191 by Housing and Development Board (S$27,729,900, 2025-03-18). Anomaly for review: tender description "ELECTRICAL LOAD UPGRADING PROGRAMME (ELUP) BATCH 3 PROJECT 4 (CENTRAL ZONE)" versus registered activity "BUSINESS & MANAGEMENT CONSULTANCY SERVICES" has cosine similarity 0.070639 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 201417546Z
- Metric: business_description_cosine_similarity = 0.070639 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 14. [R5] ORIENT NATURAL RESOURCES PTE. LTD.: HDB000ETT24000250 (escalated, priority 62)
Supplier line of business far from tender: ORIENT NATURAL RESOURCES PTE. LTD. was awarded HDB000ETT24000250 by Housing and Development Board (S$24,690,785, 2025-01-24). Anomaly for review: tender description "Proposed Relocation Works at Designated Sites" versus registered activity "WHOLESALING OF SAND (INCLUDING QUARRYING), PETROLEUM, MINING & PROSPECTING SVC" has cosine similarity 0.174614 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 201015702G
- Metric: business_description_cosine_similarity = 0.174614 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 15. [R5] ST ENGINEERING TRAINING & SIMULATION SYSTEMS PTE. LTD.: HDB000ETT24000065 (escalated, priority 62)
Supplier line of business far from tender: ST ENGINEERING TRAINING & SIMULATION SYSTEMS PTE. LTD. was awarded HDB000ETT24000065 by Housing and Development Board (S$21,506,353, 2024-06-26). Anomaly for review: tender description "RENEWAL OF IBM SYSTEM SOFTWARE AND MAINTENANCE FOR THREE (3) YEARS" versus registered activity "DESIGN DEVT, MAINT OF SIMULATOR, GAMES &EDUTAINMENT AND PROVIDING TRG SVC." has cosine similarity 0.15608 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 199607423R
- Metric: business_description_cosine_similarity = 0.15608 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 16. [R5] ST ENGINEERING URBAN SOLUTIONS LTD.: HDB000ETT24000110 (escalated, priority 60)
Supplier line of business far from tender: ST ENGINEERING URBAN SOLUTIONS LTD. was awarded HDB000ETT24000110 by Housing and Development Board (S$11,230,000, 2024-11-22). Anomaly for review: tender description "THE DEVELOPMENT OF STRUCTURAL HEALTH MONITORING SYSTEM (SHM)" versus registered activity "EGOVERNMENT, TRANSPORTATION ELECTRONICS, SATCOM, INTERACTIVE MEDIA & INFOCOMM" has cosine similarity 0.177939 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 196900084E
- Metric: business_description_cosine_similarity = 0.177939 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 17. [R5] CHIONG CONSTRUCTION PTE. LTD.: HDB000ETT24000103 (escalated, priority 58)
Supplier line of business far from tender: CHIONG CONSTRUCTION PTE. LTD. was awarded HDB000ETT24000103 by Housing and Development Board (S$4,868,000, 2024-10-24). Anomaly for review: tender description "IMPROVEMENT WORKS TO HDB HUB" versus registered activity "GENERAL CONSTRUCTION" has cosine similarity 0.030614 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 201015983H
- Metric: business_description_cosine_similarity = 0.030614 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 18. [R5] CYCLECT FACILITIES MANAGEMENT PTE. LTD.: HDB000ETT24000296 (escalated, priority 58)
Supplier line of business far from tender: CYCLECT FACILITIES MANAGEMENT PTE. LTD. was awarded HDB000ETT24000296 by Housing and Development Board (S$3,800,290, 2025-03-25). Anomaly for review: tender description "PROVISION OF MANAGING AGENT AND COMPREHENSIVE MAINTENANCE OF THE HDB MECHANISED PARKING SYSTEM (MPS) AND BUILDING FACILITIES" versus registered activity "MECHANICAL & ELECTRICAL WORKS,BUILDING CONSTRUCTION & MIXED CONSTRUCTION" has cosine similarity 0.184344 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 198400980E
- Metric: business_description_cosine_similarity = 0.184344 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 19. [R5] PERMA-LINER INDUSTRIES (SINGAPORE) PTE. LTD.: HDB000ETT23000289 (escalated, priority 56)
Supplier line of business far from tender: PERMA-LINER INDUSTRIES (SINGAPORE) PTE. LTD. was awarded HDB000ETT23000289 by Housing and Development Board (S$1,889,123, 2024-05-08). Anomaly for review: tender description "Repair of Trunk Sewer No. 9 at Anchorvale St, Anchorvale Crescent, Anchorvale Link and Sengkang East Road" versus registered activity "SUPPLY AND INSTALLATION OF TRENCHLESS LINING PRODUCTS" has cosine similarity 0.195072 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 201413940G
- Metric: business_description_cosine_similarity = 0.195072 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 20. [R5] SETSCO SERVICES PTE LTD: HDB000ETT24000076 (escalated, priority 53)
Supplier line of business far from tender: SETSCO SERVICES PTE LTD was awarded HDB000ETT24000076 by Housing and Development Board (S$578,481, 2024-09-05). Anomaly for review: tender description "Laboratory Services For The Environmental Monitoring And Management Plan For Coastal Development At Pulau Sudong" versus registered activity "IN A WIDE SPECTRUM OF INDUSTRIES INCLUDING PETROLUEM & PROCESS PLANTS" has cosine similarity 0.154294 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 196900269D
- Metric: business_description_cosine_similarity = 0.154294 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 21. [R5] ML INTERNATIONAL TRADING PTE. LTD.: HDB000ETT24000100 (escalated, priority 51)
Supplier line of business far from tender: ML INTERNATIONAL TRADING PTE. LTD. was awarded HDB000ETT24000100 by Housing and Development Board (S$272,368, 2024-08-23). Anomaly for review: tender description "IMPROVEMENT WORKS TO WOODLANDS NORTH PLAZA AND 888 PLAZA" versus registered activity "PROJECT DEVELOPMENT" has cosine similarity 0.164937 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 200416877K
- Metric: business_description_cosine_similarity = 0.164937 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 22. [R5] KELVARO TEST SUPPLIES PTE. LTD.: PLT000ETT24000013 (escalated, priority 49)
Supplier line of business far from tender: KELVARO TEST SUPPLIES PTE. LTD. was awarded PLT000ETT24000013 by Housing and Development Board (S$160,000, 2024-06-14). Anomaly for review: tender description "PLANTED TEST TENDER (FICTIONAL)" versus registered activity "OTHER INFORMATION TECHNOLOGY SERVICE ACTIVITIES" has cosine similarity -0.00792 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN T99ZZ0013D
- Metric: business_description_cosine_similarity = -0.00792 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 23. [R5] BRAXTON TEST TRADING PTE. LTD.: PLT000ETT24000003 (escalated, priority 49)
Supplier line of business far from tender: BRAXTON TEST TRADING PTE. LTD. was awarded PLT000ETT24000003 by Housing and Development Board (S$150,000, 2024-05-10). Anomaly for review: tender description "PLANTED TEST TENDER (FICTIONAL)" versus registered activity "OTHER INFORMATION TECHNOLOGY SERVICE ACTIVITIES" has cosine similarity -0.00792 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN T99ZZ0003C
- Metric: business_description_cosine_similarity = -0.00792 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 24. [R5] ELEMENT CONSTRUCTION TESTING (S) PTE. LTD.: HDB000ETT24000171 (escalated, priority 48)
Supplier line of business far from tender: ELEMENT CONSTRUCTION TESTING (S) PTE. LTD. was awarded HDB000ETT24000171 by Housing and Development Board (S$86,290, 2024-11-22). Anomaly for review: tender description "Structural Inspection at MND Complex" versus registered activity "TECHNICAL TESTING, CONSULTANCY & PRODUCT CERTIFICATION BODY" has cosine similarity 0.126301 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 200805959C
- Metric: business_description_cosine_similarity = 0.126301 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 25. [R5] HEPTACON CONSTRUCTION PTE. LTD.: HDB000ETT24000034 (escalated, priority 48)
Supplier line of business far from tender: HEPTACON CONSTRUCTION PTE. LTD. was awarded HDB000ETT24000034 by Housing and Development Board (S$85,294, 2024-08-12). Anomaly for review: tender description "SPRUCING WORKS FOR HDB FLATS (CONTRACT 2)" versus registered activity "GENERAL BUILDING AND CONSTRUCTION" has cosine similarity 0.165878 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 200902017M
- Metric: business_description_cosine_similarity = 0.165878 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 26. [R5] KIM YEW INTEGRATED PTE. LTD.: HDB000ETT24000028 (escalated, priority 47)
Supplier line of business far from tender: KIM YEW INTEGRATED PTE. LTD. was awarded HDB000ETT24000028 by Housing and Development Board (S$65,008, 2024-08-13). Anomaly for review: tender description "Provision of Managing Agent Services and Improvement Works within HDB Flats for a period of 2 years (North-East Zone)" versus registered activity "INCLUDING OF ELECTRICAL WORKS, BUILDING CONSTRUCTION & MIXED CONSTRUCTION" has cosine similarity 0.166433 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 199606507M
- Metric: business_description_cosine_similarity = 0.166433 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 27. [R5] CAMBRIAN ENGINEERING CORPORATION PTE LTD: HDB000ETT24000020 (escalated, priority 44)
Supplier line of business far from tender: CAMBRIAN ENGINEERING CORPORATION PTE LTD was awarded HDB000ETT24000020 by Housing and Development Board (S$24,940, 2024-06-14). Anomaly for review: tender description "Maintenance of Tremor Monitoring System (TRS) 2024" versus registered activity "MIXED CONSTRUCTION ACTIVITIES - FOUNDATION WORKS" has cosine similarity 0.070597 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 199701215C
- Metric: business_description_cosine_similarity = 0.070597 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 28. [R5] FOCUS ARCHITECTS: HDB000ETT24000183 (escalated, priority 43)
Supplier line of business far from tender: FOCUS ARCHITECTS was awarded HDB000ETT24000183 by Housing and Development Board (S$16,341, 2024-11-01). Anomaly for review: tender description "APPOINTMENT OF REGISTERED INSPECTORS (ARCHITECTURAL) TO THE HDB PANEL OF REGISTERED INSPECTORS (BATCH 7)" versus registered activity "BUILDING DESIGN & PROJECT MANAGEMENT" has cosine similarity 0.13222 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 53395256E
- Metric: business_description_cosine_similarity = 0.13222 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 29. [R5] SETSCO SERVICES PTE LTD: HDB000ETT24000047 (escalated, priority 43)
Supplier line of business far from tender: SETSCO SERVICES PTE LTD was awarded HDB000ETT24000047 by Housing and Development Board (S$15,666, 2024-05-30). Anomaly for review: tender description "SUPPLY OF TESTING SERVICES TO MECHANICAL COUPLER FOR REINFORCEMENT BAR SIZE OF 16MM DIAMETER AND 20MM DIAMETER" versus registered activity "IN A WIDE SPECTRUM OF INDUSTRIES INCLUDING PETROLUEM & PROCESS PLANTS" has cosine similarity 0.086695 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 196900269D
- Metric: business_description_cosine_similarity = 0.086695 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 30. [R5] CALVARY PROJECTS & CONSULTANCY: HDB000ETT24000182 (escalated, priority 42)
Supplier line of business far from tender: CALVARY PROJECTS & CONSULTANCY was awarded HDB000ETT24000182 by Housing and Development Board (S$11,260, 2024-11-01). Anomaly for review: tender description "APPOINTMENT OF REGISTERED INSPECTORS (M&E) TO THE HDB PANEL OF REGISTERED INSPECTORS (BATCH 7)" versus registered activity "CONSULTANCY AND MANAGEMENT OF BUILDING SERVICES" has cosine similarity 0.19698 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 53243477C
- Metric: business_description_cosine_similarity = 0.19698 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 31. [R5] SETSCO SERVICES PTE LTD: HDB000ETT24000260 (escalated, priority 31)
Supplier line of business far from tender: SETSCO SERVICES PTE LTD was awarded HDB000ETT24000260 by Housing and Development Board (S$150, 2025-03-21). Anomaly for review: tender description "Term Contract for the Provision of Testing Services for Semi- Destructive and Non-Destructive Tests on HDB Buildings (Batch 16)" versus registered activity "IN A WIDE SPECTRUM OF INDUSTRIES INCLUDING PETROLUEM & PROCESS PLANTS" has cosine similarity 0.071612 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 196900269D
- Metric: business_description_cosine_similarity = 0.071612 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 32. [R5] NANYANG TECH PTE. LTD.: HDB000ETT24000137 (escalated, priority 27)
Supplier line of business far from tender: NANYANG TECH PTE. LTD. was awarded HDB000ETT24000137 by Housing and Development Board (S$35, 2024-10-09). Anomaly for review: tender description "SUPPLY AND DELIVERY OF BACKPACKS FOR HDB" versus registered activity "SYSTEM INTEGRATOR" has cosine similarity -0.05252 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 200816975W
- Metric: business_description_cosine_similarity = -0.05252 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 33. [R5] ORIENT NATURAL RESOURCES PTE. LTD.: HDB000ETT24000074 (escalated, priority 27)
Supplier line of business far from tender: ORIENT NATURAL RESOURCES PTE. LTD. was awarded HDB000ETT24000074 by Housing and Development Board (S$27, 2024-07-31). Anomaly for review: tender description "Supply of Fine Aggregates to the HDB (Batch 82)" versus registered activity "WHOLESALING OF SAND (INCLUDING QUARRYING), PETROLEUM, MINING & PROSPECTING SVC" has cosine similarity 0.161117 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 201015702G
- Metric: business_description_cosine_similarity = 0.161117 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 34. [R5] ORIENT NATURAL RESOURCES PTE. LTD.: HDB000ETT24000008 (escalated, priority 27)
Supplier line of business far from tender: ORIENT NATURAL RESOURCES PTE. LTD. was awarded HDB000ETT24000008 by Housing and Development Board (S$27, 2024-04-12). Anomaly for review: tender description "Supply of Fine Aggregates to the HDB (Batch 81)" versus registered activity "WHOLESALING OF SAND (INCLUDING QUARRYING), PETROLEUM, MINING & PROSPECTING SVC" has cosine similarity 0.165828 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 201015702G
- Metric: business_description_cosine_similarity = 0.165828 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 35. [R5] ORIENT NATURAL RESOURCES PTE. LTD.: HDB000ETT24000223 (escalated, priority 27)
Supplier line of business far from tender: ORIENT NATURAL RESOURCES PTE. LTD. was awarded HDB000ETT24000223 by Housing and Development Board (S$26, 2025-01-07). Anomaly for review: tender description "Supply of Fine Aggregates to the HDB (Batch 83)" versus registered activity "WHOLESALING OF SAND (INCLUDING QUARRYING), PETROLEUM, MINING & PROSPECTING SVC" has cosine similarity 0.15304 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 201015702G
- Metric: business_description_cosine_similarity = 0.15304 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 36. [R5] HL BUILDING MATERIALS PTE. LTD.: HDB000ETT24000130 (escalated, priority 26)
Supplier line of business far from tender: HL BUILDING MATERIALS PTE. LTD. was awarded HDB000ETT24000130 by Housing and Development Board (S$24, 2024-10-15). Anomaly for review: tender description "Supply of 20MM Aggregate to the HDB (Batch 90)" versus registered activity "BUILDING MATERIALS TRADING AND INVESTMENT DEALING" has cosine similarity 0.062501 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 199206970H
- Metric: business_description_cosine_similarity = 0.062501 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
- Note: Escalated to human review: low confidence

### 37. [R5] TECH-CARE PTE. LTD.: HDB000ETT24000279 (escalated, priority 18)
Supplier line of business far from tender: TECH-CARE PTE. LTD. was awarded HDB000ETT24000279 by Housing and Development Board (S$0, 2025-01-24). Anomaly for review: tender description "SUPPLY AND DELIVERY OF RADIO FREQUENCY IDENTIFICATION (RFID) TAGS TO HDB ENGINEERING MATERIALS LABORATORY (BATCH 2)" versus registered activity "WHOLESALE OF MOBILITY RETROFITS, CONSTRUCTION MATERIALS, HEALTH CONTROL SYSTEM" has cosine similarity 0.185852 below 0.2 using sentence-transformers/all-MiniLM-L6-v2. Semantic similarity is a screening heuristic; requires auditor judgement. This is an anomaly for review and may indicate a concern that requires auditor judgement.
- Confidence: 0.60; UEN 201721440K
- Metric: business_description_cosine_similarity = 0.185852 (threshold 0.2)
- Evidence: Zetaris query `b82baeb8-e244-4b16-87bc-b20d87b611e6` over gebiz_pg.awards, gebiz_pg.supplier_xwalk, ACRA_FILES.entities, gebiz_pg.rules, 27 row(s)
- Note: Critic re-ran the SQL (query b82baeb8-e244-4b16-87bc-b20d87b611e6) and confirmed the cited row.
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
