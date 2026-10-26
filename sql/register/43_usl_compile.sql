-- Unified Semantic Layer model: award -> supplier_xwalk (supplier_name) -> supplier_registry (uen).
-- Mirrors the EDGAR->PUDL crosswalk pattern of zetaris/getting-started. Lightning SQL needs the whole
-- COMPILE statement in ONE call, so all CREATE TABLEs live in this file.
COMPILE USL procurement_usl DEPLOY NAMESPACE lightning.metastore.procurement DDL
CREATE TABLE supplier_registry (
    uen varchar(20) NOT NULL PRIMARY KEY,
    entity_name varchar(300),
    entity_type varchar(100),
    registry_status varchar(100),
    incorporation_date date,
    address varchar(500),
    postal_code varchar(10),
    industry_code varchar(10),
    industry varchar(300)
);
CREATE TABLE supplier_xwalk (
    supplier_name varchar(500) NOT NULL PRIMARY KEY,
    uen varchar(20) FOREIGN KEY REFERENCES supplier_registry(uen),
    match_method varchar(30),
    match_confidence float
);
CREATE TABLE award (
    award_key varchar(700) NOT NULL PRIMARY KEY,
    tender_no varchar(100),
    tender_description varchar(2000),
    agency varchar(200),
    award_date date,
    awarded_amt decimal(18,2),
    supplier_name varchar(500) FOREIGN KEY REFERENCES supplier_xwalk(supplier_name)
);
CREATE TABLE award_profile (
    award_key varchar(700) NOT NULL PRIMARY KEY,
    tender_no varchar(100),
    agency varchar(200),
    award_date date,
    awarded_amt decimal(18,2),
    supplier_name varchar(500),
    uen varchar(20),
    match_method varchar(30),
    match_confidence float,
    registry_status varchar(100),
    incorporation_date date,
    address varchar(500),
    industry varchar(300)
)
