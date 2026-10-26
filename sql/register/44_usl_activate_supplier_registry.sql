ACTIVATE USL TABLE lightning.metastore.procurement.procurement_usl.supplier_registry AS
SELECT
    COALESCE(uen, '') AS uen,
    entity_name,
    entity_type_description AS entity_type,
    entity_status_description AS registry_status,
    registration_incorporation_date AS incorporation_date,
    trim(concat_ws(' ', nullif(block, 'na'), nullif(street_name, 'na'), nullif(building_name, 'na'))) AS address,
    postal_code,
    primary_ssic_code AS industry_code,
    primary_ssic_description AS industry
FROM ACRA_FILES.entities
