ACTIVATE USL TABLE lightning.metastore.procurement.procurement_usl.award_profile AS
SELECT
    concat_ws('|', a.tender_no, a.supplier_name, cast(a.awarded_amt AS string)) AS award_key,
    a.tender_no,
    a.agency,
    a.award_date,
    cast(a.awarded_amt AS decimal(18,2)) AS awarded_amt,
    a.supplier_name,
    x.uen,
    x.method AS match_method,
    x.confidence AS match_confidence,
    e.entity_status_description AS registry_status,
    e.registration_incorporation_date AS incorporation_date,
    trim(concat_ws(' ', nullif(e.block, 'na'), nullif(e.street_name, 'na'), nullif(e.building_name, 'na'))) AS address,
    e.primary_ssic_description AS industry
FROM gebiz_pg.awards a
LEFT JOIN gebiz_pg.supplier_xwalk x ON x.supplier_name = a.supplier_name
LEFT JOIN ACRA_FILES.entities e ON e.uen = x.uen
