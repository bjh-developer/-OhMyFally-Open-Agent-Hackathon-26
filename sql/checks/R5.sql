-- R5: low cosine similarity between tender and registered business descriptions.
-- Setup: scripts/prepare_r5.py writes computed scores to the existing rules.params JSON.
-- Exact description joins prevent reuse after source descriptions change. No runtime model download.
WITH scores AS (
  SELECT explode(from_json(get_json_object(params, '$.similarities'),
    'array<struct<tender_description:string,ssic_description:string,similarity:double>>')) AS s,
    get_json_object(params, '$.model') AS model,
    CAST(get_json_object(params, '$.max_similarity') AS DOUBLE) AS max_similarity
  FROM gebiz_pg.rules WHERE flag_id = 'R5'
)
SELECT 'R5' AS flag_id,
       a.tender_no, a.agency, a.supplier_name, x.uen, a.award_date, a.awarded_amt,
       'business_description_cosine_similarity' AS metric_name,
       round(c.s.similarity, 6) AS metric_value,
       CAST(c.max_similarity AS STRING) AS threshold,
       concat('Anomaly for review: tender description "', a.tender_description,
              '" versus registered activity "', e.primary_ssic_description,
              '" has cosine similarity ', CAST(round(c.s.similarity, 6) AS STRING),
              ' below ', CAST(c.max_similarity AS STRING), ' using ', c.model,
              '. Semantic similarity is a screening heuristic; requires auditor judgement.') AS detail
FROM gebiz_pg.awards a
JOIN gebiz_pg.supplier_xwalk x ON x.supplier_name = a.supplier_name AND x.uen IS NOT NULL
JOIN ACRA_FILES.entities e ON e.uen = x.uen
JOIN scores c ON c.s.tender_description = a.tender_description
             AND c.s.ssic_description = e.primary_ssic_description
WHERE a.agency = {{agency}} AND a.award_date BETWEEN {{date_from}} AND {{date_to}}
  AND x.confidence >= 0.92
  AND c.s.similarity < c.max_similarity
ORDER BY c.s.similarity ASC, a.awarded_amt DESC
