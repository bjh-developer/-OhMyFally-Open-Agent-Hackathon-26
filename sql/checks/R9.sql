-- R9: a winner scores strictly below the best bidder on comparable weighted criteria.
-- internal_pg contains synthetic evaluation records only. bid_rank is not substituted for evaluation rank.
-- Require unique criterion rows, consistent weights across bidders, weights summing to 1,
-- and identical criterion sets. Tied top scores are not anomalies.
WITH criterion_rows AS (
  SELECT tender_no, supplier_name, criterion, max(weight) AS weight, max(score) AS score,
         count(*) AS n
  FROM internal_pg.evaluations GROUP BY tender_no, supplier_name, criterion
), criterion_catalog AS (
  SELECT tender_no, criterion, min(weight) AS min_weight, max(weight) AS max_weight
  FROM criterion_rows GROUP BY tender_no, criterion
), valid_tenders AS (
  SELECT tender_no, count(*) AS n_criteria
  FROM criterion_catalog GROUP BY tender_no
  HAVING max(abs(max_weight - min_weight)) < 0.000001
     AND abs(sum(max_weight) - 1.0) < 0.000001
     AND min(min_weight) > 0
), complete_scores AS (
  SELECT e.tender_no, e.supplier_name, sum(e.weight * e.score) AS weighted_score
  FROM criterion_rows e JOIN valid_tenders v ON v.tender_no = e.tender_no
  GROUP BY e.tender_no, e.supplier_name, v.n_criteria
  HAVING count(*) = v.n_criteria AND max(e.n) = 1
     AND count(e.score) = v.n_criteria AND min(e.score) >= 0 AND max(e.score) <= 100
     AND count(e.weight) = v.n_criteria
), comparable AS (
  SELECT tender_no, max(weighted_score) AS best_score, count(*) AS n_bidders
  FROM complete_scores GROUP BY tender_no
), eligible AS (
  SELECT e.tender_no, count(DISTINCT e.supplier_name) AS expected_bidders FROM internal_pg.evaluations e
  GROUP BY e.tender_no
  HAVING count(DISTINCT e.supplier_name) >= 2
)
SELECT 'R9' AS flag_id,
       a.tender_no, a.agency, a.supplier_name, x.uen, a.award_date, a.awarded_amt,
       'winner_weighted_score' AS metric_name,
       round(w.weighted_score, 6) AS metric_value,
       CAST(round(b.best_score, 6) AS STRING) AS threshold,
       concat('Anomaly for review: synthetic evaluation records give the awarded supplier weighted score ',
              CAST(round(w.weighted_score, 6) AS STRING), ' versus best score ',
              CAST(round(b.best_score, 6) AS STRING), ' under the same criteria.',
              ' Synthetic data only; documented award exceptions require auditor judgement.') AS detail
FROM gebiz_pg.awards a
JOIN complete_scores w ON w.tender_no = a.tender_no AND w.supplier_name = a.supplier_name
JOIN comparable b ON b.tender_no = a.tender_no
JOIN eligible e ON e.tender_no = a.tender_no
LEFT JOIN gebiz_pg.supplier_xwalk x ON x.supplier_name = a.supplier_name
WHERE a.agency = {{agency}} AND a.award_date BETWEEN {{date_from}} AND {{date_to}}
  AND b.n_bidders >= 2 AND w.weighted_score < b.best_score - 0.000001
  AND b.n_bidders = e.expected_bidders
ORDER BY (b.best_score - w.weighted_score) DESC, a.awarded_amt DESC
