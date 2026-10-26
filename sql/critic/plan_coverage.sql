-- Critic, plan review: what GeBIZ data exists for this agency and period?
-- n_period = awards inside the requested period; n_etq = quotation (ETQ) records for the agency (R4 needs them to be complete).
-- Params: {{agency}} {{date_from}} {{date_to}}
SELECT count(*) AS n_all,
       CAST(min(award_date) AS STRING) AS min_date,
       CAST(max(award_date) AS STRING) AS max_date,
       sum(CASE WHEN award_date BETWEEN {{date_from}} AND {{date_to}} THEN 1 ELSE 0 END) AS n_period,
       sum(CASE WHEN upper(tender_no) LIKE '%ETQ%' THEN 1 ELSE 0 END) AS n_etq
FROM gebiz_pg.awards
WHERE agency = {{agency}}
