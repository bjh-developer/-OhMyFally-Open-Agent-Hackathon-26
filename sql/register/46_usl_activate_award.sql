ACTIVATE USL TABLE lightning.metastore.procurement.procurement_usl.award AS
SELECT
    concat_ws('|', tender_no, supplier_name, cast(awarded_amt AS string)) AS award_key,
    tender_no,
    tender_description,
    agency,
    award_date,
    cast(awarded_amt AS decimal(18,2)) AS awarded_amt,
    supplier_name
FROM gebiz_pg.awards
