-- R1: supplier incorporated less than 6 months (183 days) before the award date.
-- Joins awards -> supplier_xwalk (Resolver) -> ACRA entities. Params: {{agency}} {{date_from}} {{date_to}}
SELECT 'R1' AS flag_id,
       a.tender_no,
       a.agency,
       a.supplier_name,
       e.uen,
       a.award_date,
       a.awarded_amt,
       'incorporation_age_days' AS metric_name,
       datediff(a.award_date, e.registration_incorporation_date) AS metric_value,
       '183' AS threshold,
       concat('Anomaly for review: ', e.entity_name, ' (', e.entity_type_description, ', ', e.entity_status_description,
              ') was incorporated ', CAST(e.registration_incorporation_date AS STRING), ', ',
              CAST(datediff(a.award_date, e.registration_incorporation_date) AS STRING),
              ' days before the award on ', CAST(a.award_date AS STRING),
              '. Resolver match: ', x.method, ' (confidence ', CAST(x.confidence AS STRING), ').') AS detail
FROM gebiz_pg.awards a
JOIN gebiz_pg.supplier_xwalk x ON x.supplier_name = a.supplier_name AND x.uen IS NOT NULL
JOIN ACRA_FILES.entities e ON e.uen = x.uen
WHERE a.agency = {{agency}}
  AND a.award_date BETWEEN {{date_from}} AND {{date_to}}
  AND datediff(a.award_date, e.registration_incorporation_date) BETWEEN 0 AND 183
ORDER BY metric_value ASC, a.awarded_amt DESC
