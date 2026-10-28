-- ============================================================================
-- Pecos Ridge Energy — Enverus OpenInvoice e-invoicing + Supply Chain product taxonomy
-- Snowflake DDL (our account; added to the partner's O&G domain on digitz)
-- Database PECOS_RIDGE_SCM_OPENINVOICE, schema OPENINVOICE (one system-named schema per
-- source, like the 26 PECOS_RIDGE_* databases already in the domain, e.g. PROCUREMENT_SCM.SCM).
-- Demo "today": 2026-09-30. OpenInvoice went live 2022-01-01. Spend-analytics invoice ids
-- (SPEND_INVOICE.INVOICE_ID) are stamped back onto OpenInvoice headers from 2025-01-01.
-- Keys shared with the rest of the domain: LIFNR (S4_VENDOR_LFA1 / SPEND_INVOICE), CORP_WELL_ID
-- (WELL_MASTER), PAD_ID (PAD), AFE_NUMBER (OD_AFE_HEADER), PROPERTY_NUMBER (ZFI_SYSTEM_XWALK /
-- PC_COMPLETION), CLM_CONTRACT_ID (CLM_CONTRACT), ERP_INVOICE_ID = SPEND_INVOICE.INVOICE_ID.
-- ============================================================================

-- SECTION 0: ENVIRONMENT SETUP -------------------------------------------------
USE ROLE SYSADMIN;
CREATE DATABASE IF NOT EXISTS PECOS_RIDGE_SCM_OPENINVOICE
    COMMENT = 'Pecos Ridge Energy - Enverus OpenInvoice e-invoicing (invoice headers, line items, field tickets, supplier price books) and the Supply Chain generic product taxonomy';
CREATE SCHEMA IF NOT EXISTS PECOS_RIDGE_SCM_OPENINVOICE.OPENINVOICE
    COMMENT = 'OpenInvoice extract: OI_* tables mirror the Enverus OpenInvoice objects; SCM_* tables are Supply Chain master data (taxonomy and item classification)';
USE DATABASE PECOS_RIDGE_SCM_OPENINVOICE;
USE SCHEMA OPENINVOICE;

-- SECTION 1: MASTER DATA ------------------------------------------------------

CREATE OR REPLACE TABLE OI_SUPPLIER (
    OI_SUPPLIER_ID          VARCHAR(12)   NOT NULL PRIMARY KEY COMMENT 'OpenInvoice supplier id (OIS-nnnnn). One row per supplier onboarded to OpenInvoice',
    LIFNR                   VARCHAR(10)   NOT NULL COMMENT 'SAP vendor number, 10 characters with leading zeros; joins to PECOS_RIDGE_MAINT_SAP.S4_PM.S4_VENDOR_LFA1.LIFNR and PECOS_RIDGE_PROCUREMENT_SCM.SCM.SPEND_INVOICE.LIFNR',
    SUPPLIER_NAME           VARCHAR(80)   NOT NULL COMMENT 'Supplier legal name as registered in OpenInvoice (SAP NAME1 in title case)',
    SUPPLIER_CITY           VARCHAR(40)   COMMENT 'Supplier city from the SAP vendor master',
    SUPPLIER_STATE          VARCHAR(2)    COMMENT 'Supplier state from the SAP vendor master',
    DUNS_NUMBER             VARCHAR(12)   COMMENT 'D-U-N-S number when the supplier also exists in COUNTERPARTY_MASTER; NULL otherwise',
    OI_SUPPLIER_CATEGORY    VARCHAR(40)   COMMENT 'OpenInvoice supplier category (coarse, accounting-grade): same vocabulary as SPEND_INVOICE.SPEND_CATEGORY (Chemicals, Sand/Proppant, Tubulars / OCTG, Rental Equipment, Trucking/Water Hauling, Other)',
    ONBOARDED_DATE          DATE          COMMENT 'Date the supplier was enabled in OpenInvoice (go-live wave 2022-01-01, later waves after sourcing events)',
    EINVOICE_ENABLED        BOOLEAN       COMMENT 'TRUE when the supplier submits invoices electronically with line items; FALSE for PDF-upload suppliers',
    PRICEBOOK_LOADED        BOOLEAN       COMMENT 'TRUE when a contract price book is loaded for the supplier (only the hero chemical, proppant and hauling suppliers)',
    PRIMARY_BASIN           VARCHAR(20)   COMMENT 'Basin where most of the supplier spend lands: Midland, Delaware, Anadarko, Hugoton',
    PAYMENT_TERMS           VARCHAR(6)    COMMENT 'Payment terms NT30 / NT45 / NT60 (same codes as SAP RBKP.ZTERM)',
    SUPPLIER_STATUS         VARCHAR(12)   COMMENT 'Active or Inactive in OpenInvoice'
) COMMENT = 'Suppliers onboarded to Enverus OpenInvoice. LIFNR links to the SAP vendor master and to spend analytics.';

CREATE OR REPLACE TABLE SCM_PRODUCT_TAXONOMY (
    TAXONOMY_NODE_ID        VARCHAR(16)   NOT NULL PRIMARY KEY COMMENT 'Generic product node id SCM-FF-CC-NNN (family-class-leaf), taxonomy version 3.0',
    LEVEL1_FAMILY           VARCHAR(50)   NOT NULL COMMENT 'Level 1 family: Production & completion chemicals, Proppant, OCTG & wellhead, Rental equipment, Water logistics, Fees & surcharges, Downhole & artificial lift, MRO & consumables',
    LEVEL2_CLASS            VARCHAR(50)   NOT NULL COMMENT 'Level 2 class inside the family, e.g. Corrosion control, Regional sand, Casing',
    GENERIC_PRODUCT_NAME    VARCHAR(120)  NOT NULL COMMENT 'The generic (supplier-neutral) product or service name used for price comparison, e.g. Corrosion inhibitor, water-soluble, filming amine. This is the name supply chain analyses spend by, not the supplier marketing name',
    PRIMARY_USE             VARCHAR(200)  COMMENT 'What the product or service is used for in operations',
    USE_PHASE               VARCHAR(12)   COMMENT 'Lifecycle phase the use belongs to: Drilling, Completion, Production, Facilities',
    STANDARD_UOM            VARCHAR(6)    COMMENT 'Standard unit of measure for price comparison: GAL, LB, TON, FT, EA, DAY, BBL, HR. Invoiced packs convert to this unit through SCM_ITEM_CLASSIFICATION.CONVERSION_FACTOR_TO_STD_UOM',
    KEY_SPEC_ATTRIBUTES     VARCHAR(200)  COMMENT 'The specification attributes that make two supplier items the same generic product (mesh size, grade, OD and weight, active content)',
    UNSPSC_CODE             VARCHAR(8)    COMMENT 'Closest UNSPSC commodity code',
    ALTERNATE_SUPPLIER_ELIGIBLE BOOLEAN   COMMENT 'TRUE when supply chain considers the product substitutable across qualified suppliers (FALSE for fees and catch-all nodes)',
    CATEGORY_MANAGER        VARCHAR(40)   COMMENT 'Supply chain category manager who owns the family',
    BENCHMARK_PRICE_USD_PER_STD_UOM NUMBER(12,2) COMMENT 'Supply chain 2025 benchmark price per standard UOM used in the category reviews (NULL for fees)',
    TAXONOMY_VERSION        VARCHAR(6)    COMMENT 'Taxonomy version the node was published in (3.0)'
) COMMENT = 'Supply Chain generic product taxonomy v3.0: the context that did not exist in the accounting cost codes. One row per generic product (leaf).';

CREATE OR REPLACE TABLE OI_PRICEBOOK_ITEM (
    PRICEBOOK_ITEM_ID       VARCHAR(16)   NOT NULL PRIMARY KEY COMMENT 'Price book line id (PBI-nnnnnn)',
    OI_SUPPLIER_ID          VARCHAR(12)   NOT NULL COMMENT 'Supplier whose price book this is (OI_SUPPLIER)',
    LIFNR                   VARCHAR(10)   NOT NULL COMMENT 'SAP vendor number of the supplier',
    CLM_CONTRACT_ID         VARCHAR(12)   COMMENT 'Contract the price book is an exhibit of; joins to PECOS_RIDGE_PROCUREMENT_SCM.SCM.CLM_CONTRACT.CLM_CONTRACT_ID',
    PRICEBOOK_VERSION       VARCHAR(16)   NOT NULL COMMENT 'Price book version loaded in OpenInvoice (e.g. CCC-PB-2025A)',
    SUPPLIER_ITEM_CODE      VARCHAR(20)   NOT NULL COMMENT 'Supplier item code as printed on invoice lines',
    SUPPLIER_ITEM_DESCRIPTION VARCHAR(120) COMMENT 'Supplier item description in the price book (marketing name and pack size)',
    UOM                     VARCHAR(6)    COMMENT 'Unit the contract rate is quoted in (the pack: TOTE, DRUM, PAIL, TON, BBL, DAY, HR, EA)',
    CONTRACT_RATE_USD       NUMBER(12,2)  NOT NULL COMMENT 'Contracted price per invoiced UOM for the version period',
    EFFECTIVE_FROM          DATE          NOT NULL COMMENT 'First day the rate applies',
    EFFECTIVE_TO            DATE          NOT NULL COMMENT 'Last day the rate applies',
    ESCALATION_PCT          NUMBER(5,2)   COMMENT 'Annual escalation written into the exhibit, percent',
    SOURCE_DOCUMENT         VARCHAR(120)  COMMENT 'File name of the MSA pricing exhibit the rate was loaded from (in the supplier document archive)',
    LOADED_DATE             DATE          COMMENT 'Date the version was loaded in OpenInvoice'
) COMMENT = 'Supplier price books loaded in OpenInvoice (contract rates per supplier item). Invoice lines are matched to the rate in force on the service date.';

CREATE OR REPLACE TABLE SCM_ITEM_CLASSIFICATION (
    CLASSIFICATION_ID       VARCHAR(16)   NOT NULL PRIMARY KEY COMMENT 'Classification row id (CLS-nnnnnn)',
    OI_SUPPLIER_ID          VARCHAR(12)   NOT NULL COMMENT 'Supplier of the item (OI_SUPPLIER)',
    LIFNR                   VARCHAR(10)   NOT NULL COMMENT 'SAP vendor number of the supplier',
    SUPPLIER_ITEM_CODE      VARCHAR(20)   NOT NULL COMMENT 'Supplier item code; with LIFNR the join key to OI_INVOICE_LINE',
    SUPPLIER_ITEM_DESCRIPTION VARCHAR(120) COMMENT 'Supplier item description as invoiced (the marketing name)',
    INVOICED_UOM            VARCHAR(6)    COMMENT 'Unit the supplier invoices in (TOTE, DRUM, PAIL, JT, FT, TON, DAY, WEEK, MONTH, BBL, HR, EA)',
    TAXONOMY_NODE_ID        VARCHAR(16)   COMMENT 'Generic product the item maps to (SCM_PRODUCT_TAXONOMY); NULL while unclassified',
    CONVERSION_FACTOR_TO_STD_UOM NUMBER(12,4) COMMENT 'Standard units per invoiced unit: a 55 gal drum is 55, a 42 ft casing joint is 42, a monthly rental is 30 days; 1 when the item is invoiced in the standard UOM',
    CLASSIFICATION_METHOD   VARCHAR(24)   COMMENT 'How the mapping was made: Rule (code pattern), Spec sheet review (supplier technical data sheet), Steward (manual), ML suggested (model proposal awaiting review)',
    CONFIDENCE              NUMBER(4,2)   COMMENT 'Confidence of the mapping 0-1 (1.00 for rule and spec-sheet mappings)',
    SOURCE_DOCUMENT         VARCHAR(120)  COMMENT 'Supplier spec sheet or pricing exhibit file name that evidences the mapping (in the supplier document archive)',
    CLASSIFIED_BY           VARCHAR(40)   COMMENT 'Steward or process that classified the item',
    CLASSIFIED_DATE         DATE          COMMENT 'Date of the classification',
    REVIEW_STATUS           VARCHAR(14)   COMMENT 'Approved (counts as classified), Needs review (ML suggestion not yet approved) or Unclassified (no generic product yet)',
    STEWARD_NOTE            VARCHAR(200)  COMMENT 'Free-text note from the steward queue'
) COMMENT = 'Crosswalk from supplier item (LIFNR + item code) to the generic product taxonomy, with the pack-to-standard-UOM conversion. Only Approved rows count as classified spend.';

-- SECTION 2: TRANSACTIONS -----------------------------------------------------

CREATE OR REPLACE TABLE OI_FIELD_TICKET (
    FIELD_TICKET_ID         VARCHAR(16)   NOT NULL PRIMARY KEY COMMENT 'Field ticket id (FT-nnnnnnn)',
    OI_SUPPLIER_ID          VARCHAR(12)   NOT NULL COMMENT 'Supplier that raised the ticket',
    LIFNR                   VARCHAR(10)   NOT NULL COMMENT 'SAP vendor number of the supplier',
    TICKET_NUMBER           VARCHAR(20)   COMMENT 'Supplier ticket number as printed',
    TICKET_DATE             DATE          NOT NULL COMMENT 'Service or delivery date on the ticket',
    TICKET_TYPE             VARCHAR(10)   COMMENT 'Delivery (material), Service (labor and trucks) or Rental',
    CORP_WELL_ID            VARCHAR(12)   COMMENT 'Well the ticket was approved against; joins to PECOS_RIDGE_CORP_MDM.MASTER.WELL_MASTER.CORP_WELL_ID',
    PAD_ID                  VARCHAR(10)   COMMENT 'Pad of the well; joins to PECOS_RIDGE_CORP_MDM.MASTER.PAD.PAD_ID',
    PROPERTY_NUMBER         VARCHAR(10)   COMMENT 'Quorum property for LOE tickets; NULL for capital tickets',
    AFE_NUMBER              VARCHAR(14)   COMMENT 'AFE for capital tickets; joins to PECOS_RIDGE_REV_ACCOUNTING.QUORUM_FIN.OD_AFE_HEADER.AFE_NUMBER; NULL for LOE tickets',
    BASIN                   VARCHAR(20)   COMMENT 'Basin of the well',
    APPROVED_BY             VARCHAR(40)   COMMENT 'Company man or foreman who approved the ticket in the field',
    APPROVED_TS             TIMESTAMP_NTZ COMMENT 'Field approval timestamp',
    APPROVAL_STATUS         VARCHAR(10)   COMMENT 'Approved or Rejected',
    TICKET_TOTAL_USD        NUMBER(14,2)  COMMENT 'Ticket total in USD',
    OI_INVOICE_ID           VARCHAR(16)   COMMENT 'Invoice the ticket was billed on (NULL for rejected tickets)'
) COMMENT = 'OpenInvoice field tickets: the field approval that precedes each invoice line for services, deliveries and rentals.';

CREATE OR REPLACE TABLE OI_INVOICE (
    OI_INVOICE_ID           VARCHAR(16)   NOT NULL PRIMARY KEY COMMENT 'OpenInvoice invoice id (OI-YYYY-nnnnnn)',
    SUPPLIER_INVOICE_NUMBER VARCHAR(24)   COMMENT 'Supplier invoice number exactly as submitted',
    OI_SUPPLIER_ID          VARCHAR(12)   NOT NULL COMMENT 'Submitting supplier (OI_SUPPLIER)',
    LIFNR                   VARCHAR(10)   NOT NULL COMMENT 'SAP vendor number of the submitting supplier',
    SUPPLIER_NAME_AS_SUBMITTED VARCHAR(80) COMMENT 'Supplier name as typed on the invoice (varies in case and suffix; same vendor as LIFNR)',
    INVOICE_DATE            DATE          NOT NULL COMMENT 'Invoice date on the document (equals SPEND_INVOICE.INVOICE_DATE for stamped invoices)',
    SUBMITTED_TS            TIMESTAMP_NTZ COMMENT 'When the supplier submitted it in OpenInvoice',
    APPROVED_DATE           DATE          COMMENT 'Date the invoice completed company approval (NULL while in workflow or rejected)',
    PAID_DATE               DATE          COMMENT 'Payment date from the ERP (NULL if unpaid)',
    INVOICE_STATUS          VARCHAR(16)   COMMENT 'OpenInvoice status: Paid, Approved, Submitted, Disputed, On hold - coding, Rejected',
    SOURCE_LEDGER           VARCHAR(32)   COMMENT 'Where the cost lands: AFE actual (capex) or LOE (lease operating statement); same vocabulary as SPEND_INVOICE.SOURCE_LEDGER',
    OI_SUPPLIER_CATEGORY    VARCHAR(40)   COMMENT 'Supplier category on the invoice (same vocabulary as SPEND_INVOICE.SPEND_CATEGORY)',
    COST_CODE               VARCHAR(10)   COMMENT 'OpenInvoice header cost code (LOE-CHEM, CAP-PROP, CAP-OCTG, CAP-RENT, LOE-SWD, CAP-WTR)',
    PO_NUMBER               VARCHAR(12)   COMMENT 'SAP purchase order when PO-backed (45000nnnnn); NULL for field-ticket invoices',
    AFE_NUMBER              VARCHAR(14)   COMMENT 'AFE charged for capital invoices; NULL for LOE',
    PROPERTY_NUMBER         VARCHAR(10)   COMMENT 'Quorum property charged for LOE invoices; NULL for capital',
    CORP_WELL_ID            VARCHAR(12)   COMMENT 'Well derived from the AFE (OD_AFE_HEADER) or the property (ZFI_SYSTEM_XWALK)',
    PAD_ID                  VARCHAR(10)   COMMENT 'Pad of that well',
    BASIN                   VARCHAR(20)   COMMENT 'Basin of that well',
    BUSINESS_UNIT           VARCHAR(20)   COMMENT 'Business unit: Midland Basin, Delaware Basin, Midcon, Hugoton',
    SUBTOTAL_USD            NUMBER(14,2)  COMMENT 'Sum of material and service lines before fees and surcharges',
    SURCHARGES_USD          NUMBER(14,2)  COMMENT 'Sum of fee and surcharge lines (fuel surcharge, delivery, environmental fee, standby, minimum charge)',
    INVOICE_TOTAL_USD       NUMBER(14,2)  NOT NULL COMMENT 'Invoice total in USD = sum of OI_INVOICE_LINE.LINE_AMOUNT_USD; equals SPEND_INVOICE.AMOUNT_USD when ERP_INVOICE_ID is populated',
    LINE_COUNT              NUMBER(4,0)   COMMENT 'Number of lines on the invoice',
    COUPA_DOC_ID            VARCHAR(14)   COMMENT 'Coupa document id the invoice was routed under (all invoices)',
    ERP_INVOICE_ID          VARCHAR(14)   COMMENT 'Spend-analytics invoice id stamped back from the ERP integration = PECOS_RIDGE_PROCUREMENT_SCM.SCM.SPEND_INVOICE.INVOICE_ID. Populated for invoices dated 2025-01-01 or later (the January 2025 integration upgrade); NULL before that, when only COUPA_DOC_ID links the records',
    ERP_MATCH_STATUS        VARCHAR(30)   COMMENT 'Stamped (ERP_INVOICE_ID present) or Legacy - Coupa id only (pre-2025 invoices)',
    APPROVER_NAME           VARCHAR(40)   COMMENT 'Company approver who released the invoice',
    DISPUTE_REASON          VARCHAR(80)   COMMENT 'Reason when INVOICE_STATUS is Disputed (e.g. Unit price above contract rate)'
) COMMENT = 'OpenInvoice invoice headers 2022-01-01 to 2026-09-30 for the supply-chain managed categories. One row per supplier invoice; totals equal the sum of their lines.';

CREATE OR REPLACE TABLE OI_INVOICE_LINE (
    OI_LINE_ID              VARCHAR(20)   NOT NULL PRIMARY KEY COMMENT 'Line id (invoice id + line number)',
    OI_INVOICE_ID           VARCHAR(16)   NOT NULL COMMENT 'Parent invoice (OI_INVOICE)',
    LINE_NO                 NUMBER(4,0)   NOT NULL COMMENT 'Line number on the invoice',
    FIELD_TICKET_ID         VARCHAR(16)   COMMENT 'Field ticket the line was billed from (OI_FIELD_TICKET); NULL for PO material lines',
    SERVICE_DATE            DATE          COMMENT 'Service or delivery date of the line',
    SUPPLIER_ITEM_CODE      VARCHAR(20)   COMMENT 'Supplier item code; with LIFNR the join key to SCM_ITEM_CLASSIFICATION and OI_PRICEBOOK_ITEM',
    SUPPLIER_ITEM_DESCRIPTION VARCHAR(120) COMMENT 'Supplier item description exactly as invoiced: the marketing product name and pack (e.g. CorroShield CS-7000 Corrosion Inhibitor 55 gal drum). Not a generic product name',
    UOM                     VARCHAR(6)    COMMENT 'Invoiced unit of measure: GAL, TOTE, DRUM, PAIL, BAG, TON, JT, FT, EA, DAY, WEEK, MONTH, BBL, HR',
    QUANTITY                NUMBER(14,3)  COMMENT 'Quantity in the invoiced UOM',
    UNIT_PRICE_USD          NUMBER(12,4)  COMMENT 'Price per invoiced unit',
    LINE_AMOUNT_USD         NUMBER(14,2)  NOT NULL COMMENT 'Extended amount = QUANTITY x UNIT_PRICE_USD (rounded to cents)',
    OI_COST_CODE            VARCHAR(10)   COMMENT 'OpenInvoice cost code the line is coded to (accounting view)',
    OI_COST_CODE_DESC       VARCHAR(60)   COMMENT 'Cost code description',
    OI_SUPPLIER_CATEGORY    VARCHAR(40)   COMMENT 'Supplier category of the invoice (accounting view)',
    LIFNR                   VARCHAR(10)   NOT NULL COMMENT 'SAP vendor number of the supplier',
    OI_SUPPLIER_ID          VARCHAR(12)   NOT NULL COMMENT 'Supplier (OI_SUPPLIER)',
    AFE_NUMBER              VARCHAR(14)   COMMENT 'AFE charged (capital lines)',
    PROPERTY_NUMBER         VARCHAR(10)   COMMENT 'Quorum property charged (LOE lines)',
    CORP_WELL_ID            VARCHAR(12)   COMMENT 'Well the line relates to (WELL_MASTER.CORP_WELL_ID)',
    PAD_ID                  VARCHAR(10)   COMMENT 'Pad of that well',
    BASIN                   VARCHAR(20)   COMMENT 'Basin of that well',
    PRICEBOOK_ITEM_ID       VARCHAR(16)   COMMENT 'Price book line the item was matched to on the service date (OI_PRICEBOOK_ITEM); NULL when the supplier has no price book or the item is not in it',
    PRICEBOOK_RATE_USD      NUMBER(12,4)  COMMENT 'Contract rate per invoiced unit from the matched price book line',
    PRICE_VARIANCE_USD      NUMBER(14,2)  COMMENT '(UNIT_PRICE_USD - PRICEBOOK_RATE_USD) x QUANTITY; positive means invoiced above contract',
    LINE_STATUS             VARCHAR(12)   COMMENT 'Approved, Disputed or Short-paid',
    APPROVER_NAME           VARCHAR(40)   COMMENT 'Company approver of the line',
    DISPUTE_REASON          VARCHAR(80)   COMMENT 'Reason when the line is Disputed or Short-paid'
) COMMENT = 'OpenInvoice invoice line items: the product, quantity and unit price detail that spend analytics does not hold. The generic product is NOT on this table; join SCM_ITEM_CLASSIFICATION on LIFNR and SUPPLIER_ITEM_CODE (or use V_INVOICE_LINE_CLASSIFIED).';

CREATE OR REPLACE TABLE DATA_DICTIONARY (
    TABLE_NAME              VARCHAR(40)   NOT NULL COMMENT 'Table or view name',
    COLUMN_NAME             VARCHAR(40)   NOT NULL COMMENT 'Column name',
    DESCRIPTION             VARCHAR(400)  COMMENT 'Business meaning, units and join hints',
    EXAMPLE_VALUE           VARCHAR(120)  COMMENT 'An example value'
) COMMENT = 'Data dictionary for the OpenInvoice schema.';

-- SECTION 3: VIEWS --------------------------------------------------------------

CREATE OR REPLACE VIEW V_INVOICE_LINE_CLASSIFIED
    COMMENT = 'Every invoice line with its supplier, invoice header, approved generic product (or Unclassified) and standard-UOM quantity and unit price. Start here for any price or product question.'
AS
SELECT
    l.OI_LINE_ID,
    l.OI_INVOICE_ID,
    i.SUPPLIER_INVOICE_NUMBER,
    i.ERP_INVOICE_ID,
    i.INVOICE_DATE,
    DATE_TRUNC('MONTH', i.INVOICE_DATE) AS INVOICE_MONTH,
    EXTRACT(YEAR FROM i.INVOICE_DATE) AS INVOICE_YEAR,
    l.SERVICE_DATE,
    i.INVOICE_STATUS,
    i.SOURCE_LEDGER,
    l.OI_SUPPLIER_ID,
    l.LIFNR,
    s.SUPPLIER_NAME,
    l.OI_SUPPLIER_CATEGORY,
    l.OI_COST_CODE,
    l.OI_COST_CODE_DESC,
    l.SUPPLIER_ITEM_CODE,
    l.SUPPLIER_ITEM_DESCRIPTION,
    l.UOM AS INVOICED_UOM,
    l.QUANTITY,
    l.UNIT_PRICE_USD,
    l.LINE_AMOUNT_USD,
    l.LINE_STATUS,
    l.DISPUTE_REASON,
    l.PRICEBOOK_ITEM_ID,
    l.PRICEBOOK_RATE_USD,
    l.PRICE_VARIANCE_USD,
    l.AFE_NUMBER,
    l.PROPERTY_NUMBER,
    l.CORP_WELL_ID,
    l.PAD_ID,
    l.BASIN,
    c.CLASSIFICATION_ID,
    c.REVIEW_STATUS,
    c.CLASSIFICATION_METHOD,
    c.SOURCE_DOCUMENT AS CLASSIFICATION_SOURCE_DOCUMENT,
    CASE WHEN c.REVIEW_STATUS = 'Approved' THEN c.TAXONOMY_NODE_ID END AS TAXONOMY_NODE_ID,
    CASE WHEN c.REVIEW_STATUS = 'Approved' THEN t.LEVEL1_FAMILY ELSE 'Unclassified' END AS LEVEL1_FAMILY,
    CASE WHEN c.REVIEW_STATUS = 'Approved' THEN t.LEVEL2_CLASS ELSE 'Unclassified' END AS LEVEL2_CLASS,
    CASE WHEN c.REVIEW_STATUS = 'Approved' THEN t.GENERIC_PRODUCT_NAME ELSE 'Unclassified' END AS GENERIC_PRODUCT_NAME,
    CASE WHEN c.REVIEW_STATUS = 'Approved' THEN t.PRIMARY_USE END AS PRIMARY_USE,
    CASE WHEN c.REVIEW_STATUS = 'Approved' THEN t.USE_PHASE END AS USE_PHASE,
    CASE WHEN c.REVIEW_STATUS = 'Approved' THEN t.STANDARD_UOM END AS STANDARD_UOM,
    CASE WHEN c.REVIEW_STATUS = 'Approved' THEN t.ALTERNATE_SUPPLIER_ELIGIBLE END AS ALTERNATE_SUPPLIER_ELIGIBLE,
    CASE WHEN c.REVIEW_STATUS = 'Approved' THEN t.BENCHMARK_PRICE_USD_PER_STD_UOM END AS BENCHMARK_PRICE_USD_PER_STD_UOM,
    CASE WHEN c.REVIEW_STATUS = 'Approved' THEN 1 ELSE 0 END AS IS_CLASSIFIED,
    CASE WHEN c.REVIEW_STATUS = 'Approved' THEN l.QUANTITY * c.CONVERSION_FACTOR_TO_STD_UOM END AS STD_QUANTITY,
    CASE WHEN c.REVIEW_STATUS = 'Approved' AND l.QUANTITY * c.CONVERSION_FACTOR_TO_STD_UOM > 0
         THEN l.LINE_AMOUNT_USD / (l.QUANTITY * c.CONVERSION_FACTOR_TO_STD_UOM) END AS STD_UNIT_PRICE_USD
FROM OI_INVOICE_LINE l
JOIN OI_INVOICE i ON i.OI_INVOICE_ID = l.OI_INVOICE_ID
JOIN OI_SUPPLIER s ON s.OI_SUPPLIER_ID = l.OI_SUPPLIER_ID
LEFT JOIN SCM_ITEM_CLASSIFICATION c ON c.LIFNR = l.LIFNR AND c.SUPPLIER_ITEM_CODE = l.SUPPLIER_ITEM_CODE
LEFT JOIN SCM_PRODUCT_TAXONOMY t ON t.TAXONOMY_NODE_ID = c.TAXONOMY_NODE_ID;

CREATE OR REPLACE VIEW V_GENERIC_PRODUCT_PRICE_MONTHLY
    COMMENT = 'Classified spend by generic product, supplier and invoice month with standard-UOM quantity and volume-weighted standard unit price. Fees and surcharges excluded.'
AS
SELECT
    v.TAXONOMY_NODE_ID,
    v.LEVEL1_FAMILY,
    v.LEVEL2_CLASS,
    v.GENERIC_PRODUCT_NAME,
    v.STANDARD_UOM,
    v.OI_SUPPLIER_ID,
    v.LIFNR,
    v.SUPPLIER_NAME,
    v.INVOICE_MONTH,
    v.INVOICE_YEAR,
    v.BASIN,
    COUNT(*) AS LINE_COUNT,
    SUM(v.STD_QUANTITY) AS STD_QUANTITY,
    SUM(v.LINE_AMOUNT_USD) AS SPEND_USD,
    SUM(v.LINE_AMOUNT_USD) / NULLIF(SUM(v.STD_QUANTITY), 0) AS AVG_STD_UNIT_PRICE_USD,
    MAX(v.BENCHMARK_PRICE_USD_PER_STD_UOM) AS BENCHMARK_PRICE_USD_PER_STD_UOM
FROM V_INVOICE_LINE_CLASSIFIED v
WHERE v.IS_CLASSIFIED = 1 AND v.LEVEL1_FAMILY <> 'Fees & surcharges'
GROUP BY v.TAXONOMY_NODE_ID, v.LEVEL1_FAMILY, v.LEVEL2_CLASS, v.GENERIC_PRODUCT_NAME, v.STANDARD_UOM,
         v.OI_SUPPLIER_ID, v.LIFNR, v.SUPPLIER_NAME, v.INVOICE_MONTH, v.INVOICE_YEAR, v.BASIN;

CREATE OR REPLACE VIEW V_SUPPLIER_ALTERNATIVES
    COMMENT = 'For each generic product and year: every supplier that sold it, its standard-UOM volume, average standard unit price, the best (lowest) observed supplier price that year and the savings had all volume been bought at that price. Only alternate-supplier-eligible products.'
AS
WITH by_supplier AS (
    SELECT
        v.TAXONOMY_NODE_ID, v.LEVEL1_FAMILY, v.GENERIC_PRODUCT_NAME, v.STANDARD_UOM, v.INVOICE_YEAR,
        v.OI_SUPPLIER_ID, v.LIFNR, v.SUPPLIER_NAME,
        SUM(v.STD_QUANTITY) AS STD_QUANTITY,
        SUM(v.LINE_AMOUNT_USD) AS SPEND_USD,
        SUM(v.LINE_AMOUNT_USD) / NULLIF(SUM(v.STD_QUANTITY), 0) AS AVG_STD_UNIT_PRICE_USD
    FROM V_INVOICE_LINE_CLASSIFIED v
    WHERE v.IS_CLASSIFIED = 1 AND v.ALTERNATE_SUPPLIER_ELIGIBLE = TRUE AND v.LEVEL1_FAMILY <> 'Fees & surcharges'
    GROUP BY v.TAXONOMY_NODE_ID, v.LEVEL1_FAMILY, v.GENERIC_PRODUCT_NAME, v.STANDARD_UOM, v.INVOICE_YEAR,
             v.OI_SUPPLIER_ID, v.LIFNR, v.SUPPLIER_NAME
)
SELECT
    b.TAXONOMY_NODE_ID, b.LEVEL1_FAMILY, b.GENERIC_PRODUCT_NAME, b.STANDARD_UOM, b.INVOICE_YEAR,
    b.OI_SUPPLIER_ID, b.LIFNR, b.SUPPLIER_NAME, b.STD_QUANTITY, b.SPEND_USD, b.AVG_STD_UNIT_PRICE_USD,
    COUNT(*) OVER (PARTITION BY b.TAXONOMY_NODE_ID, b.INVOICE_YEAR) AS SUPPLIER_COUNT,
    SUM(b.STD_QUANTITY) OVER (PARTITION BY b.TAXONOMY_NODE_ID, b.INVOICE_YEAR) AS PRODUCT_STD_QUANTITY,
    b.STD_QUANTITY / NULLIF(SUM(b.STD_QUANTITY) OVER (PARTITION BY b.TAXONOMY_NODE_ID, b.INVOICE_YEAR), 0) AS VOLUME_SHARE,
    MIN(b.AVG_STD_UNIT_PRICE_USD) OVER (PARTITION BY b.TAXONOMY_NODE_ID, b.INVOICE_YEAR) AS BEST_STD_UNIT_PRICE_USD,
    MAX(b.AVG_STD_UNIT_PRICE_USD) OVER (PARTITION BY b.TAXONOMY_NODE_ID, b.INVOICE_YEAR) AS HIGHEST_STD_UNIT_PRICE_USD,
    (b.AVG_STD_UNIT_PRICE_USD - MIN(b.AVG_STD_UNIT_PRICE_USD) OVER (PARTITION BY b.TAXONOMY_NODE_ID, b.INVOICE_YEAR)) * b.STD_QUANTITY AS SAVINGS_AT_BEST_PRICE_USD,
    (MAX(b.AVG_STD_UNIT_PRICE_USD) OVER (PARTITION BY b.TAXONOMY_NODE_ID, b.INVOICE_YEAR)
       / NULLIF(MIN(b.AVG_STD_UNIT_PRICE_USD) OVER (PARTITION BY b.TAXONOMY_NODE_ID, b.INVOICE_YEAR), 0) - 1) * 100 AS PRICE_DISPERSION_PCT
FROM by_supplier b;

CREATE OR REPLACE VIEW V_PRICEBOOK_VARIANCE
    COMMENT = 'Invoice lines matched to a loaded price book: invoiced unit price vs contract rate, variance in USD and percent, and the line status. Positive variance = invoiced above contract.'
AS
SELECT
    v.OI_LINE_ID, v.OI_INVOICE_ID, v.SUPPLIER_INVOICE_NUMBER, v.INVOICE_DATE, v.INVOICE_MONTH, v.INVOICE_YEAR, v.SERVICE_DATE,
    v.OI_SUPPLIER_ID, v.LIFNR, v.SUPPLIER_NAME, v.SUPPLIER_ITEM_CODE, v.SUPPLIER_ITEM_DESCRIPTION, v.GENERIC_PRODUCT_NAME, v.LEVEL1_FAMILY,
    v.INVOICED_UOM, v.QUANTITY, v.UNIT_PRICE_USD, v.PRICEBOOK_RATE_USD, v.LINE_AMOUNT_USD, v.PRICE_VARIANCE_USD,
    (v.UNIT_PRICE_USD / NULLIF(v.PRICEBOOK_RATE_USD, 0) - 1) * 100 AS PRICE_VARIANCE_PCT,
    CASE WHEN v.PRICE_VARIANCE_USD > 0.005 THEN 1 ELSE 0 END AS IS_OVER_CONTRACT,
    v.LINE_STATUS, v.DISPUTE_REASON, v.AFE_NUMBER, v.PROPERTY_NUMBER, v.CORP_WELL_ID, v.BASIN,
    p.PRICEBOOK_VERSION, p.CLM_CONTRACT_ID, p.SOURCE_DOCUMENT AS PRICEBOOK_SOURCE_DOCUMENT
FROM V_INVOICE_LINE_CLASSIFIED v
JOIN OI_PRICEBOOK_ITEM p ON p.PRICEBOOK_ITEM_ID = v.PRICEBOOK_ITEM_ID;

CREATE OR REPLACE VIEW V_UNCLASSIFIED_SPEND
    COMMENT = 'Invoice lines without an approved generic product (no classification row, Needs review, or Unclassified): the steward queue, with supplier, description and amount.'
AS
SELECT
    v.OI_LINE_ID, v.OI_INVOICE_ID, v.INVOICE_DATE, v.INVOICE_YEAR, v.INVOICE_MONTH,
    v.OI_SUPPLIER_ID, v.LIFNR, v.SUPPLIER_NAME, v.OI_SUPPLIER_CATEGORY, v.OI_COST_CODE,
    v.SUPPLIER_ITEM_CODE, v.SUPPLIER_ITEM_DESCRIPTION, v.INVOICED_UOM, v.QUANTITY, v.UNIT_PRICE_USD, v.LINE_AMOUNT_USD,
    COALESCE(v.REVIEW_STATUS, 'Unclassified') AS REVIEW_STATUS, v.CLASSIFICATION_METHOD, v.BASIN, v.CORP_WELL_ID
FROM V_INVOICE_LINE_CLASSIFIED v
WHERE v.IS_CLASSIFIED = 0;

CREATE OR REPLACE VIEW V_AFE_PRODUCT_COST
    COMMENT = 'Capital invoice lines rolled up by AFE, well, family and generic product: the hook for joining OpenInvoice spend to WellView jobs (WVJOB.AFE_NUMBER), the AFE headers and the well master (lateral length) for cost-per-foot analysis.'
AS
SELECT
    v.AFE_NUMBER, v.CORP_WELL_ID, v.PAD_ID, v.BASIN,
    v.LEVEL1_FAMILY, v.GENERIC_PRODUCT_NAME, v.STANDARD_UOM, v.USE_PHASE,
    MIN(v.INVOICE_DATE) AS FIRST_INVOICE_DATE,
    MAX(v.INVOICE_DATE) AS LAST_INVOICE_DATE,
    COUNT(*) AS LINE_COUNT,
    SUM(v.STD_QUANTITY) AS STD_QUANTITY,
    SUM(v.LINE_AMOUNT_USD) AS SPEND_USD,
    SUM(v.LINE_AMOUNT_USD) / NULLIF(SUM(v.STD_QUANTITY), 0) AS AVG_STD_UNIT_PRICE_USD
FROM V_INVOICE_LINE_CLASSIFIED v
WHERE v.AFE_NUMBER IS NOT NULL
GROUP BY v.AFE_NUMBER, v.CORP_WELL_ID, v.PAD_ID, v.BASIN, v.LEVEL1_FAMILY, v.GENERIC_PRODUCT_NAME, v.STANDARD_UOM, v.USE_PHASE;

-- SECTION 4: SYNCED REFERENCE DATA ---------------------------------------------
-- OpenInvoice keeps its own copies of the cost objects it validates invoices against (wells, AFEs,
-- vendors) synced nightly from the corporate MDM, Quorum and SAP, plus the ERP posting log written
-- back by the integration. They let OpenInvoice questions join to wells and AFEs inside this
-- database; the golden records remain in PECOS_RIDGE_CORP_MDM, PECOS_RIDGE_REV_ACCOUNTING and SAP.

CREATE OR REPLACE TABLE OI_REF_WELL (
    CORP_WELL_ID            VARCHAR(12)   NOT NULL PRIMARY KEY COMMENT 'Corporate well id PRW-nnnnnn, synced from PECOS_RIDGE_CORP_MDM.MASTER.WELL_MASTER (the golden record)',
    WELL_NAME               VARCHAR(80)   COMMENT 'Well name',
    API14                   VARCHAR(20)   COMMENT 'API-14 identifier',
    PAD_ID                  VARCHAR(10)   COMMENT 'Pad id PAD-nnnn',
    DSU_ID                  VARCHAR(10)   COMMENT 'Drilling spacing unit id',
    BASIN                   VARCHAR(20)   COMMENT 'Basin: Midland, Delaware, Anadarko, Hugoton',
    COUNTY                  VARCHAR(40)   COMMENT 'County',
    STATE_CODE              VARCHAR(2)    COMMENT 'State',
    WELL_TYPE               VARCHAR(12)   COMMENT 'Oil, Gas, SWD',
    TRAJECTORY              VARCHAR(12)   COMMENT 'Horizontal or Vertical',
    IS_OPERATED             BOOLEAN       COMMENT 'TRUE for Pecos Ridge operated wells',
    WORKING_INTEREST_PCT    NUMBER(8,4)   COMMENT 'Pecos Ridge working interest, percent 0-100',
    SPUD_DATE               DATE          COMMENT 'Spud date',
    FIRST_PRODUCTION_DATE   DATE          COMMENT 'First production date',
    LATERAL_LENGTH_FT       NUMBER(8,0)   COMMENT 'Completed lateral length in feet (0 for vertical wells); divide completion spend by it for cost per lateral foot',
    WELL_STATUS             VARCHAR(30)   COMMENT 'Corporate well status',
    SYNCED_DATE             DATE          COMMENT 'Date of the nightly sync that wrote the row'
) COMMENT = 'Well list synced into OpenInvoice from the corporate MDM for invoice coding and validation. Same keys and values as WELL_MASTER.';

CREATE OR REPLACE TABLE OI_REF_AFE (
    AFE_NUMBER              VARCHAR(14)   NOT NULL PRIMARY KEY COMMENT 'AFE number STYY-NNNNNT synced from PECOS_RIDGE_REV_ACCOUNTING.QUORUM_FIN.OD_AFE_HEADER',
    CORP_WELL_ID            VARCHAR(12)   COMMENT 'Well the AFE belongs to (OI_REF_WELL)',
    PROPERTY_NUMBER         VARCHAR(10)   COMMENT 'Quorum property number when assigned',
    AFE_TYPE                VARCHAR(12)   COMMENT 'Drilling, Completion or Facilities',
    AFE_DATE                DATE          COMMENT 'AFE date',
    GROSS_AFE_AMOUNT        NUMBER(14,2)  COMMENT 'Gross (8/8ths) approved AFE amount in USD',
    COMPANY_WI_DECIMAL      NUMBER(8,6)   COMMENT 'Pecos Ridge working interest decimal',
    AFE_STATUS              VARCHAR(12)   COMMENT 'AFE status',
    SYNCED_DATE             DATE          COMMENT 'Date of the nightly sync that wrote the row'
) COMMENT = 'Approved AFE list synced into OpenInvoice for capital invoice coding. Same keys and values as OD_AFE_HEADER.';

CREATE OR REPLACE TABLE OI_REF_VENDOR (
    LIFNR                   VARCHAR(10)   NOT NULL PRIMARY KEY COMMENT 'SAP vendor number synced from PECOS_RIDGE_MAINT_SAP.S4_PM.S4_VENDOR_LFA1',
    NAME1                   VARCHAR(80)   COMMENT 'SAP vendor name',
    ORT01                   VARCHAR(40)   COMMENT 'City',
    REGIO                   VARCHAR(2)    COMMENT 'State',
    VENDOR_CATEGORY         VARCHAR(40)   COMMENT 'SAP vendor category (accounting-grade)',
    BLOCKED                 BOOLEAN       COMMENT 'TRUE when payment blocked in SAP',
    SYNCED_DATE             DATE          COMMENT 'Date of the nightly sync that wrote the row'
) COMMENT = 'SAP vendor master list synced into OpenInvoice. Same keys and values as S4_VENDOR_LFA1.';

CREATE OR REPLACE TABLE OI_ERP_INTEGRATION_LOG (
    ERP_INVOICE_ID          VARCHAR(14)   NOT NULL PRIMARY KEY COMMENT 'Spend-analytics invoice id written back by the ERP integration (= SPEND_INVOICE.INVOICE_ID)',
    OI_INVOICE_ID           VARCHAR(16)   COMMENT 'OpenInvoice invoice the stamp was applied to',
    LIFNR                   VARCHAR(10)   COMMENT 'Vendor',
    ERP_PLATFORM            VARCHAR(40)   COMMENT 'ERP platform the invoice posted through (Coupa non-PO / SAP PO invoice)',
    ERP_INVOICE_DATE        DATE          COMMENT 'Invoice date as posted in the ERP',
    ERP_AMOUNT_USD          NUMBER(14,2)  COMMENT 'Amount posted in the ERP (spend analytics AMOUNT_USD)',
    ERP_COST_CATEGORY       VARCHAR(40)   COMMENT 'Accounting cost category assigned in the ERP',
    ERP_SOURCE_LEDGER       VARCHAR(32)   COMMENT 'Ledger the posting landed in',
    ERP_APPROVAL_STATUS     VARCHAR(20)   COMMENT 'Approval status in the ERP',
    ERP_PAID_DATE           DATE          COMMENT 'Paid date in the ERP',
    POSTED_TS               TIMESTAMP_NTZ COMMENT 'When the stamp-back message was received'
) COMMENT = 'ERP stamp-back log since the January 2025 integration upgrade: one row per stamped invoice with the amount and coding the ERP recorded, for OpenInvoice-to-ERP reconciliation.';
