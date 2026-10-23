-- R6: value concentration in ten deterministic keyword categories (first matching category wins).
-- Denominator: all positive-value awards in the requested agency, period and category.
-- Supplier identity is the published name; aliases are not consolidated. At least five category awards.
WITH categorized AS (
  SELECT a.*,
    CASE
      WHEN lower(tender_description) RLIKE 'landscap|horticultur|arbor|tree |trees|gardening|grass|turf' THEN 'landscaping'
      WHEN lower(tender_description) RLIKE 'cleaning|cleansing|pest control|waste|refuse|sanitation' THEN 'cleaning_and_waste'
      WHEN lower(tender_description) RLIKE 'cyber|software|computer|network|information technology|data centre|data center|digital|(^|[^a-z])ict([^a-z]|$)|server' THEN 'information_technology'
      WHEN lower(tender_description) RLIKE 'security|surveillance|cctv|guarding' THEN 'security'
      WHEN lower(tender_description) RLIKE 'training|education|course|workshop|tuition' THEN 'education_and_training'
      WHEN lower(tender_description) RLIKE 'consultancy|consulting|audit|legal|valuation|survey' THEN 'professional_services'
      WHEN lower(tender_description) RLIKE 'event|festival|catering|exhibition|concert' THEN 'events_and_catering'
      WHEN lower(tender_description) RLIKE 'transport|logistic|freight|vehicle|bus service|delivery' THEN 'transport_and_logistics'
      WHEN lower(tender_description) RLIKE 'construction|building|renovation|civil|structural|engineering|repair|maintenance' THEN 'construction_and_maintenance'
      ELSE 'other'
    END AS category
  FROM gebiz_pg.awards a
  WHERE agency = {{agency}} AND award_date BETWEEN {{date_from}} AND {{date_to}}
    AND awarded_amt > 0
), totals AS (
  SELECT category, sum(awarded_amt) AS category_total, count(DISTINCT tender_no) AS category_awards
  FROM categorized GROUP BY category
), supplier_totals AS (
  SELECT category, supplier_name, sum(awarded_amt) AS supplier_total
  FROM categorized GROUP BY category, supplier_name
), concentrated AS (
  SELECT s.*, t.category_total, t.category_awards,
         CAST(s.supplier_total AS DOUBLE) / CAST(t.category_total AS DOUBLE) AS value_share
  FROM supplier_totals s JOIN totals t ON t.category = s.category
  WHERE t.category_awards >= 5
    AND CAST(s.supplier_total AS DOUBLE) / CAST(t.category_total AS DOUBLE) > 0.5
)
SELECT 'R6' AS flag_id,
       a.tender_no, a.agency, a.supplier_name, x.uen, a.award_date, a.awarded_amt,
       'supplier_category_value_share' AS metric_name,
       round(c.value_share, 6) AS metric_value,
       '0.5' AS threshold,
       concat('Anomaly for review: in keyword category ', a.category,
              ', this supplier holds S$', CAST(round(c.supplier_total, 2) AS STRING),
              ' of S$', CAST(round(c.category_total, 2) AS STRING), ' (',
              CAST(round(c.value_share * 100, 2) AS STRING), '%) across ',
              CAST(c.category_awards AS STRING), ' category tenders in this scope.',
              ' Specialised markets and broad categories may explain concentration; requires auditor judgement.') AS detail
FROM categorized a
JOIN concentrated c ON c.category = a.category AND c.supplier_name = a.supplier_name
LEFT JOIN gebiz_pg.supplier_xwalk x ON x.supplier_name = a.supplier_name
ORDER BY c.value_share DESC, a.supplier_name, a.award_date
