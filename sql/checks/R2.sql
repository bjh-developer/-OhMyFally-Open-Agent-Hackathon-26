-- R2: supplier's ACRA status is not live (struck off, ceased, in liquidation, dissolved, cancelled, terminated...).
-- Status is the CURRENT registry status, not the status at award time. Params: {{agency}} {{date_from}} {{date_to}}
SELECT 'R2' AS flag_id,
       a.tender_no,
       a.agency,
       a.supplier_name,
       e.uen,
       a.award_date,
       a.awarded_amt,
       'acra_status' AS metric_name,
       e.entity_status_description AS metric_value,
       'Live' AS threshold,
       concat('Anomaly for review: ', e.entity_name, ' (', e.entity_type_description, ') has current ACRA status "',
              e.entity_status_description, '"; awarded ', CAST(a.award_date AS STRING),
              '. ACRA publishes the current status only, so the entity may have been live at award time.') AS detail
FROM gebiz_pg.awards a
JOIN gebiz_pg.supplier_xwalk x ON x.supplier_name = a.supplier_name AND x.uen IS NOT NULL
JOIN ACRA_FILES.entities e ON e.uen = x.uen
WHERE a.agency = {{agency}}
  AND a.award_date BETWEEN {{date_from}} AND {{date_to}}
  AND upper(e.entity_status_description) RLIKE 'STRUCK OFF|CEASED|LIQUIDATION|WINDING UP|DISSOLVED|CANCELLED|TERMINATED|REMOVED|EXPIRED'
ORDER BY a.awarded_amt DESC
