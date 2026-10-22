-- FIXTURE_R3 (test double for sql/checks/R3.sql)
SELECT 'R3' FROM gebiz_pg.awards WHERE agency = {{agency}} AND award_date BETWEEN {{date_from}} AND {{date_to}}
