-- R3: two or more DISTINCT winning suppliers (different UENs) at the same agency share an exact registered address
-- (postal code + block + street + level + unit). One row per award by a supplier in the group.
-- Sole proprietorships/partnerships are excluded: their unit-level address is not published in the committed sample.
-- Companies of one group usually share an office and a leading name word (e.g. "ACME BUILDERS" and "ACME FACILITIES"),
-- so suppliers are grouped by the first word of their registered name (ignoring THE/SINGAPORE) and an address is only
-- flagged when at least two DIFFERENT groups share it. Groups with unrelated names are not detected (no officer data).
-- Params: {{agency}} {{date_from}} {{date_to}}
WITH won AS (
  SELECT DISTINCT a.agency, x.uen
  FROM gebiz_pg.awards a
  JOIN gebiz_pg.supplier_xwalk x ON x.supplier_name = a.supplier_name AND x.uen IS NOT NULL
  WHERE a.agency = {{agency}} AND a.award_date BETWEEN {{date_from}} AND {{date_to}}
),
addr AS (
  SELECT w.agency, w.uen,
         concat_ws('|', e.postal_code, upper(e.block), upper(e.street_name), upper(e.level_no), upper(e.unit_no)) AS addr_key,
         concat_ws(' ', e.block, e.street_name, concat('#', e.level_no, '-', e.unit_no), concat('S', e.postal_code)) AS addr_text,
         regexp_extract(regexp_replace(upper(e.entity_name), '^(THE |SINGAPORE )+', ''), '^[A-Z0-9]+', 0) AS group_key
  FROM won w
  JOIN ACRA_FILES.entities e ON e.uen = w.uen
  WHERE e.entity_type_description <> 'Sole Proprietorship/ Partnership'
    AND e.postal_code IS NOT NULL AND length(e.postal_code) = 6 AND e.street_name IS NOT NULL AND upper(e.street_name) <> 'NA'
),
grp AS (
  SELECT agency, addr_key, count(DISTINCT uen) AS n_suppliers, min(addr_text) AS addr_text
  FROM addr GROUP BY agency, addr_key HAVING count(DISTINCT uen) >= 2 AND count(DISTINCT group_key) >= 2
)
SELECT 'R3' AS flag_id,
       a.tender_no,
       a.agency,
       a.supplier_name,
       x.uen,
       a.award_date,
       a.awarded_amt,
       'suppliers_at_address' AS metric_name,
       g.n_suppliers AS metric_value,
       '2' AS threshold,
       concat('Anomaly for review: ', CAST(g.n_suppliers AS STRING), ' distinct winning suppliers at this agency share the ACRA address ',
              g.addr_text, '. Shared business centres can explain this; requires auditor judgement.') AS detail
FROM gebiz_pg.awards a
JOIN gebiz_pg.supplier_xwalk x ON x.supplier_name = a.supplier_name AND x.uen IS NOT NULL
JOIN addr d ON d.uen = x.uen AND d.agency = a.agency
JOIN grp g ON g.agency = d.agency AND g.addr_key = d.addr_key
WHERE a.agency = {{agency}} AND a.award_date BETWEEN {{date_from}} AND {{date_to}}
ORDER BY g.n_suppliers DESC, g.addr_text, a.award_date
