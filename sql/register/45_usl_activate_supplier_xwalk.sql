ACTIVATE USL TABLE lightning.metastore.procurement.procurement_usl.supplier_xwalk AS
SELECT
    COALESCE(supplier_name, '') AS supplier_name,
    uen,
    method AS match_method,
    confidence AS match_confidence
FROM gebiz_pg.supplier_xwalk
