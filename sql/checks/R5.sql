-- R5: low cosine similarity between tender and registered business descriptions.
-- Setup: scripts/prepare_r5.py writes computed scores to the existing rules.params JSON.
-- Exact description joins prevent reuse after source descriptions change. No runtime model download.
-- Free-text activity descriptions are often loose, so a low score alone is not enough: the award is only flagged when
-- the official SSIC division (first two digits of the code) is also not a usual fit for the type of work in the tender.
-- Work types and divisions: built environment (41-43 construction, 71 engineering, 81 building and landscape services,
-- 68 property management, 33 repair, 01-02 horticulture, 37-39 sewerage and waste), consultancy (69-74), security (80),
-- cleaning (81, 37-39), IT (58, 61-63), administration and managing agents (70, 78, 80-82). Other tenders keep the score rule.
WITH scores AS (
  SELECT explode(from_json(get_json_object(params, '$.similarities'),
    'array<struct<tender_description:string,ssic_description:string,similarity:double>>')) AS s,
    get_json_object(params, '$.model') AS model,
    CAST(get_json_object(params, '$.max_similarity') AS DOUBLE) AS max_similarity
  FROM gebiz_pg.rules WHERE flag_id = 'R5'
), typed AS (
  SELECT a.*,
    CASE
      WHEN lower(a.tender_description) RLIKE 'security|surveillance|cctv|guard' THEN 'security'
      WHEN lower(a.tender_description) RLIKE 'software|computer|network|information technology|digital|data centre|data center|cyber' THEN 'it'
      WHEN lower(a.tender_description) RLIKE 'managing agent|call centre|call center|feedback|customer service|helpdesk' THEN 'admin'
      WHEN lower(a.tender_description) RLIKE 'consultan|feasibility|survey' THEN 'consultancy'
      WHEN lower(a.tender_description) RLIKE 'clean|pest|waste|refuse|sanitation' THEN 'cleaning'
      WHEN lower(a.tender_description) RLIKE 'construct|building|build|renovat|upgrad|civil|structural|engineering|repair|maintenance|park|trail|playground|connector|landscap|horticultur|arbor|turf|electrical|plumbing|sewage|sludge|lift|facilit|works' THEN 'built'
      ELSE 'other'
    END AS work_type
  FROM gebiz_pg.awards a
  WHERE a.agency = {{agency}} AND a.award_date BETWEEN {{date_from}} AND {{date_to}}
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
FROM typed a
JOIN gebiz_pg.supplier_xwalk x ON x.supplier_name = a.supplier_name AND x.uen IS NOT NULL
JOIN ACRA_FILES.entities e ON e.uen = x.uen
JOIN scores c ON c.s.tender_description = a.tender_description
             AND c.s.ssic_description = e.primary_ssic_description
WHERE x.confidence >= 0.92
  AND c.s.similarity < c.max_similarity
  AND lower(trim(e.primary_ssic_description)) NOT IN ('na', 'n.a.', 'n/a', '-')
  AND NOT (
       (a.work_type = 'built'       AND substr(e.primary_ssic_code, 1, 2) IN ('41','42','43','71','81','68','33','01','02','37','38','39'))
    OR (a.work_type = 'consultancy' AND substr(e.primary_ssic_code, 1, 2) IN ('69','70','71','72','73','74'))
    OR (a.work_type = 'security'    AND substr(e.primary_ssic_code, 1, 2) IN ('80'))
    OR (a.work_type = 'cleaning'    AND substr(e.primary_ssic_code, 1, 2) IN ('81','37','38','39'))
    OR (a.work_type = 'it'          AND substr(e.primary_ssic_code, 1, 2) IN ('58','61','62','63'))
    OR (a.work_type = 'admin'       AND substr(e.primary_ssic_code, 1, 2) IN ('70','78','80','81','82'))
  )
ORDER BY c.s.similarity ASC, a.awarded_amt DESC
