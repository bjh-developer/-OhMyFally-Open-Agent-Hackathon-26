-- FIXTURE_R1 (test double for stream B's sql/checks/R1.sql; same output columns)
SELECT 'R1' AS flag_id, a.tender_no, a.agency, a.supplier_name, x.uen, a.award_date, a.awarded_amt,
       'age_days' AS metric_name, 20 AS metric_value, '183' AS threshold, 'incorporated before award' AS detail
FROM gebiz_pg.awards a WHERE a.agency = '{{agency}}' AND a.award_date BETWEEN {{date_from}} AND {{date_to}}
