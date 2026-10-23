-- Demo query for the Zetaris UI (SQL Workspace). Run each statement on its own.
-- USL `procurement_usl` (namespace lightning.metastore.procurement) joins
--   GeBIZ awards (Postgres) -> Resolver crosswalk (Postgres) -> ACRA registry (Parquet on S3).
-- Tables: award, supplier_xwalk, supplier_registry (FK-linked) and award_profile (the flat, friendly view of all three).
-- Rebuild: python scripts/register_zetaris.py   (sql/register/40-47)

-- 1. Awards to companies incorporated within 6 months of the award (red flag R1), one friendly table, no joins to write:
SELECT tender_no, agency, supplier_name, awarded_amt, award_date, incorporation_date,
       datediff(award_date, incorporation_date) AS company_age_days,
       registry_status, address, industry
FROM lightning.metastore.procurement.procurement_usl.award_profile
WHERE datediff(award_date, incorporation_date) BETWEEN 0 AND 183
ORDER BY awarded_amt DESC
LIMIT 10;

-- 2. Same data through the FK-related model tables (shows the semantic layer's relationships):
SELECT a.tender_no, a.supplier_name, r.uen, r.registry_status, r.incorporation_date, r.industry
FROM lightning.metastore.procurement.procurement_usl.award a
JOIN lightning.metastore.procurement.procurement_usl.supplier_xwalk x ON x.supplier_name = a.supplier_name
JOIN lightning.metastore.procurement.procurement_usl.supplier_registry r ON r.uen = x.uen
LIMIT 5;

-- 3. Model definition (tables, keys, relationships):
LOAD USL procurement_usl NAMESPACE lightning.metastore.procurement;
