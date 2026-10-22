-- R8: supplier name looks locally registered (PTE LTD / PRIVATE LIMITED / LLP...) but the Resolver found no ACRA
-- entity above the confidence threshold. Names without a local suffix (foreign firms, government bodies, individuals)
-- are labelled out_of_scope by the Resolver and are NOT flagged here ("outside registry scope").
-- Params: {{agency}} {{date_from}} {{date_to}}
SELECT 'R8' AS flag_id,
       a.tender_no,
       a.agency,
       a.supplier_name,
       x.uen AS uen,
       a.award_date,
       a.awarded_amt,
       'resolver_confidence' AS metric_name,
       x.confidence AS metric_value,
       '0.8' AS threshold,
       concat('Anomaly for review: the supplier name "', a.supplier_name, '" looks locally registered but no ACRA entity matched above 0.8 (',
              CASE WHEN x.uen IS NULL THEN 'unresolved' ELSE concat('best match ', x.uen, ' via ', x.method) END,
              '). Closest candidate: ', coalesce(get_json_object(x.candidates, '$[0].entity_name'), 'none'),
              '. May be a renamed, mistyped or unregistered entity; requires auditor judgement.') AS detail
FROM gebiz_pg.awards a
JOIN gebiz_pg.supplier_xwalk x ON x.supplier_name = a.supplier_name
WHERE a.agency = {{agency}}
  AND a.award_date BETWEEN {{date_from}} AND {{date_to}}
  AND (x.method = 'unresolved' OR (x.uen IS NOT NULL AND x.confidence < 0.8))
ORDER BY a.awarded_amt DESC
