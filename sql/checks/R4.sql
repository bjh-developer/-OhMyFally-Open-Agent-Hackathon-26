-- R4: possible contract splitting. Same agency and supplier: >= 2 awards, each below S$90,000, within a 90-day
-- window, together above S$90,000. One row per award that sits in at least one qualifying window.
-- GeBIZ data here has tender (ETT) awards only, so splitting below the quotation band is under-detected.
-- Params: {{agency}} {{date_from}} {{date_to}}
WITH s AS (
  SELECT tender_no, agency, supplier_name, award_date, awarded_amt
  FROM gebiz_pg.awards
  WHERE agency = {{agency}} AND award_date BETWEEN {{date_from}} AND {{date_to}}
    AND awarded_amt > 0 AND awarded_amt < 90000
),
win AS (
  SELECT s1.agency, s1.supplier_name, s1.award_date AS win_start,
         count(DISTINCT s2.tender_no) AS n_awards, sum(s2.awarded_amt) AS total_amt
  FROM s s1
  JOIN s s2 ON s1.agency = s2.agency AND s1.supplier_name = s2.supplier_name
           AND s2.award_date BETWEEN s1.award_date AND date_add(s1.award_date, 90)
  GROUP BY s1.agency, s1.supplier_name, s1.award_date
  HAVING count(DISTINCT s2.tender_no) >= 2 AND sum(s2.awarded_amt) > 90000
)
SELECT 'R4' AS flag_id,
       m.tender_no,
       m.agency,
       m.supplier_name,
       max(x.uen) AS uen,
       m.award_date,
       m.awarded_amt,
       'window_total_sgd' AS metric_name,
       max(w.total_amt) AS metric_value,
       '90000' AS threshold,
       concat('Anomaly for review: ', CAST(max(w.n_awards) AS STRING), ' sub-S$90k awards to this supplier within 90 days total S$',
              CAST(round(max(w.total_amt), 2) AS STRING), ' (window starting ', CAST(min(w.win_start) AS STRING),
              '), above the S$90k tender threshold. May indicate splitting; requires auditor judgement.') AS detail
FROM s m
JOIN win w ON w.agency = m.agency AND w.supplier_name = m.supplier_name
          AND m.award_date BETWEEN w.win_start AND date_add(w.win_start, 90)
LEFT JOIN gebiz_pg.supplier_xwalk x ON x.supplier_name = m.supplier_name
GROUP BY m.tender_no, m.agency, m.supplier_name, m.award_date, m.awarded_amt
ORDER BY max(w.total_amt) DESC, m.supplier_name, m.award_date
