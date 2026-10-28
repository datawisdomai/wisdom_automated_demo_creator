-- ============================================================================
-- WisdomAI POC — Meridian Clinician Network
-- Snowflake DDL
-- Domain: fictional professional network for US clinicians (physicians, NPs, PAs,
--   pharmacists). B2B revenue from pharma brands (specialty-targeted campaigns,
--   sponsored content) and health systems (recruiting placements, employer branding).
-- Use case: three-way contract reconciliation across DocuSign (extracted contract
--   terms), Salesforce (closed-won opportunities) and NetSuite (sales orders and
--   billing schedules created by Boomi). There is NO precomputed results table: the
--   checks are derived live from the raw tables using RECONCILIATION_CONTROLS as the
--   rulebook and the V_ helper views for the joins.
-- Demo "today": 2026-09-30 (Q3 2026 quarter end). Data spans 2024-01-01 .. 2026-09-30.
-- ============================================================================

-- SECTION 0: ENVIRONMENT SETUP -------------------------------------------------
USE ROLE SYSADMIN;
CREATE DATABASE IF NOT EXISTS MERIDIAN_POC
    COMMENT = 'WisdomAI POC database for the Meridian Clinician Network demo (three-way contract reconciliation)';
CREATE SCHEMA IF NOT EXISTS MERIDIAN_POC.ANALYTICS
    COMMENT = 'Meridian order-to-cash reconciliation: DocuSign contract extraction, Salesforce opportunities, NetSuite sales orders and billing, and the reconciliation control matrix';
USE DATABASE MERIDIAN_POC;
USE SCHEMA ANALYTICS;

-- SECTION 1: DIMENSION TABLES -------------------------------------------------

CREATE OR REPLACE TABLE CUSTOMERS (
    customer_id            VARCHAR(10)  NOT NULL PRIMARY KEY  COMMENT 'Customer code (e.g. CUST-0017). Same id in Salesforce (Account) and NetSuite (Customer).',
    customer_name          VARCHAR(80)  NOT NULL              COMMENT 'Fictional customer name (e.g. Halvorsen Therapeutics, Lakeshore Regional Health)',
    customer_type          VARCHAR(20)  NOT NULL              COMMENT 'Pharma (pharma brand buying clinician marketing) or Health System (buying recruiting and employer branding)',
    segment                VARCHAR(30)  NOT NULL              COMMENT 'Pharma: Top 20 Pharma, Mid-size Pharma, Specialty Biotech. Health System: Academic Medical Center, Regional Health System, Community Hospital.',
    account_owner          VARCHAR(60)  NOT NULL              COMMENT 'Salesforce account owner (sales rep) responsible for the customer, e.g. Dana Whitfield',
    sales_pod              VARCHAR(30)  NOT NULL              COMMENT 'Sales team the owner belongs to: Pharma East, Pharma West, Health Systems East, Health Systems West',
    region                 VARCHAR(20)  NOT NULL              COMMENT 'Customer headquarters region: Northeast, Southeast, Midwest, West',
    hq_state               VARCHAR(2)                         COMMENT 'Headquarters US state code',
    customer_since         DATE                               COMMENT 'Date of the first signed agreement with Meridian'
) COMMENT = 'Customer master (140 rows): 85 pharma brands and 55 health systems. Shared key for DocuSign extraction, Salesforce and NetSuite.';

CREATE OR REPLACE TABLE PRODUCTS (
    product_id             VARCHAR(10)  NOT NULL PRIMARY KEY  COMMENT 'Product code (e.g. P-01)',
    product_name           VARCHAR(60)  NOT NULL              COMMENT 'Product name as it appears on contracts, Salesforce products and NetSuite items (e.g. Specialty Targeted Campaign, Recruiting Placement)',
    product_family         VARCHAR(30)  NOT NULL              COMMENT 'Pharma Marketing or Health System Talent',
    unit_of_measure        VARCHAR(20)  NOT NULL              COMMENT 'What one unit of quantity means (Campaign, Placement, Insertion, Program, Sponsorship, Profile-Year)',
    list_price             NUMBER(12,2) NOT NULL              COMMENT 'Standard list price per unit in USD; contracts may negotiate a different unit price',
    revenue_recognition    VARCHAR(40)  NOT NULL              COMMENT 'How NetSuite recognises revenue for the product (Ratably over the campaign period, Point in time at placement)',
    description            VARCHAR(300)                       COMMENT 'Plain-English description of the product'
) COMMENT = 'Product catalogue (8 rows): clinician marketing products sold to pharma brands and talent products sold to health systems.';

CREATE OR REPLACE TABLE RECONCILIATION_CONTROLS (
    control_id             VARCHAR(10)  NOT NULL PRIMARY KEY  COMMENT 'Reconciliation check id (RC-01 .. RC-11)',
    check_type             VARCHAR(40)  NOT NULL              COMMENT 'Machine name of the check used in every finding, e.g. TCV_MISMATCH, MISSING_BILLING_MILESTONE, AMENDMENT_NOT_IN_NETSUITE',
    check_name             VARCHAR(80)  NOT NULL              COMMENT 'Human name of the check',
    field_name             VARCHAR(40)  NOT NULL              COMMENT 'The contract field the check compares (total_contract_value, end_date, payment_terms, billing_frequency, billing_milestone, products, amendment, linkage)',
    systems_compared       VARCHAR(60)  NOT NULL              COMMENT 'Which systems the check compares, e.g. Contract vs Salesforce, Contract vs NetSuite, NetSuite vs Salesforce',
    tolerance              VARCHAR(40)                        COMMENT 'Tolerance before a difference becomes a finding (e.g. 100 USD, 7 days and 1 USD, exact match)',
    default_severity       VARCHAR(10)  NOT NULL              COMMENT 'Severity when the dollar variance is below the high threshold: High, Medium or Low',
    high_severity_usd      NUMBER(12,2)                       COMMENT 'Absolute dollar variance at or above which a finding of this check is High severity (NULL = severity never escalates on dollars)',
    owning_team            VARCHAR(30)  NOT NULL              COMMENT 'Team that reviews and resolves findings of this check: Sales Ops, Revenue Accounting or Billing',
    sox_control_ref        VARCHAR(60)  NOT NULL              COMMENT 'SOX order-to-cash control the check evidences, e.g. OTC-07 Amendment processing',
    description            VARCHAR(500) NOT NULL              COMMENT 'Plain-English statement of what the check does and why it exists',
    corrective_system      VARCHAR(40)                        COMMENT 'System usually corrected when the finding is confirmed: Salesforce, NetSuite or Contract re-review'
) COMMENT = 'The reconciliation rulebook (control matrix): one row per three-way check with systems compared, tolerance, severity rule, owning team and SOX control reference. Join findings to it by check_type.';

-- SECTION 2: DOCUSIGN CONTRACT EXTRACTION ------------------------------------

CREATE OR REPLACE TABLE CONTRACTS (
    contract_id            VARCHAR(12)  NOT NULL PRIMARY KEY  COMMENT 'Contract record id (e.g. CTR-00142). Each signed document (original agreement or amendment) is one row.',
    customer_id            VARCHAR(10)  NOT NULL REFERENCES CUSTOMERS(customer_id) COMMENT 'Customer the agreement is with',
    contract_number        VARCHAR(24)  NOT NULL              COMMENT 'Agreement number printed on the document. Originals look like MCN-2025-0142; amendments append the amendment suffix (MCN-2025-0142-A2). Salesforce linked_contract_number references this value.',
    docusign_envelope_id   VARCHAR(40)  NOT NULL              COMMENT 'DocuSign envelope id of the signed document',
    contract_type          VARCHAR(12)  NOT NULL              COMMENT 'New, Renewal or Amendment',
    parent_contract_id     VARCHAR(12)           REFERENCES CONTRACTS(contract_id) COMMENT 'For an amendment, the contract_id of the ORIGINAL agreement it amends (every amendment points at the original, not at the previous amendment). NULL for originals.',
    amendment_number       NUMBER(2,0)  NOT NULL              COMMENT '0 for the original agreement, 1..n for amendments in signing order',
    signed_date            DATE         NOT NULL              COMMENT 'Date the document was fully executed in DocuSign',
    effective_date         DATE         NOT NULL              COMMENT 'Start of the agreement term (restated on amendments; usually unchanged)',
    end_date               DATE         NOT NULL              COMMENT 'End of the agreement term as stated in THIS document. An amendment that extends the term restates the new end date.',
    term_months            NUMBER(3,0)  NOT NULL              COMMENT 'Term length in months as stated in this document',
    total_contract_value   NUMBER(14,2) NOT NULL              COMMENT 'Total contract value (TCV) in USD as stated in THIS document. An amendment restates the full agreement value after the amendment, not the increment.',
    currency               VARCHAR(3)   NOT NULL              COMMENT 'ISO currency code (USD)',
    payment_terms          VARCHAR(10)  NOT NULL              COMMENT 'Net 30, Net 45 or Net 60 as stated in this document',
    billing_frequency      VARCHAR(12)  NOT NULL              COMMENT 'Upfront, Quarterly, Monthly or Milestone as stated in this document',
    auto_renew             BOOLEAN      NOT NULL              COMMENT 'TRUE when the agreement renews automatically unless notice is given',
    cancellation_notice_days NUMBER(3,0) NOT NULL             COMMENT 'Days of written notice required to cancel or opt out of renewal',
    signatory_name         VARCHAR(60)  NOT NULL              COMMENT 'Customer signatory on the document',
    product_summary        VARCHAR(400) NOT NULL              COMMENT 'Free-text summary of the products or campaigns in the agreement as extracted from the document',
    special_terms          VARCHAR(500)                       COMMENT 'Free-text special clauses extracted from the document (price protection, exclusivity, make-goods, credits)',
    extracted_at           TIMESTAMP_NTZ NOT NULL             COMMENT 'When the terms were extracted from the signed PDF',
    extraction_confidence  NUMBER(4,3)  NOT NULL              COMMENT 'Confidence score of the extraction (0..1); below 0.90 the extraction was reviewed by Deal Desk',
    pdf_file_name          VARCHAR(60)  NOT NULL              COMMENT 'File name of the signed PDF in the contract archive (S3), e.g. MCN-2025-0142-A2.pdf'
) COMMENT = 'Terms extracted from every signed DocuSign document, 2024-01-01 .. 2026-09-30 (400 rows: ~270 original agreements and ~130 amendments). The legal truth the other two systems are reconciled against. An amendment row RESTATES the whole agreement (value, dates, terms, exhibits); use V_CONTRACT_CHAIN for the current state of each agreement.';

CREATE OR REPLACE TABLE CONTRACT_LINE_ITEMS (
    line_id                VARCHAR(12)  NOT NULL PRIMARY KEY  COMMENT 'Line id (e.g. CL-000412)',
    contract_id            VARCHAR(12)  NOT NULL REFERENCES CONTRACTS(contract_id) COMMENT 'Document the line belongs to. An amendment carries the FULL restated set of lines (Exhibit A), not just the changes.',
    line_number            NUMBER(2,0)  NOT NULL              COMMENT 'Line order within the document',
    product_id             VARCHAR(10)  NOT NULL REFERENCES PRODUCTS(product_id) COMMENT 'Product',
    product_name           VARCHAR(60)  NOT NULL              COMMENT 'Product name as printed on the document (matches PRODUCTS.product_name)',
    specialty_targeted     VARCHAR(40)                        COMMENT 'Clinician specialty the campaign targets (pharma products only), e.g. Cardiology, Oncology; NULL for talent products',
    quantity               NUMBER(6,0)  NOT NULL              COMMENT 'Units purchased',
    unit_price             NUMBER(12,2) NOT NULL              COMMENT 'Negotiated price per unit in USD',
    line_amount            NUMBER(14,2) NOT NULL              COMMENT 'quantity x unit_price in USD',
    start_date             DATE         NOT NULL              COMMENT 'Line service start',
    end_date               DATE         NOT NULL              COMMENT 'Line service end'
) COMMENT = 'Exhibit A of each signed document: product lines with quantity and negotiated price. Sum of line_amount equals the document total_contract_value.';

CREATE OR REPLACE TABLE CONTRACT_BILLING_SCHEDULE (
    schedule_id            VARCHAR(12)  NOT NULL PRIMARY KEY  COMMENT 'Schedule row id (e.g. CB-001203)',
    contract_id            VARCHAR(12)  NOT NULL REFERENCES CONTRACTS(contract_id) COMMENT 'Document the schedule belongs to. An amendment carries the FULL restated schedule (Exhibit B).',
    milestone_number       NUMBER(2,0)  NOT NULL              COMMENT 'Milestone order within the document',
    milestone_description  VARCHAR(80)  NOT NULL              COMMENT 'What triggers the bill (e.g. Campaign launch, Quarterly instalment 3, Amendment 2 execution)',
    scheduled_date         DATE         NOT NULL              COMMENT 'Date the customer may be invoiced per the document',
    scheduled_amount       NUMBER(14,2) NOT NULL              COMMENT 'Amount to invoice in USD'
) COMMENT = 'Exhibit B of each signed document: the billing schedule or milestones. Sum of scheduled_amount equals the document total_contract_value. Reconciled against NETSUITE_BILLING_SCHEDULE.';

-- SECTION 3: SALESFORCE REPLICA -----------------------------------------------

CREATE OR REPLACE TABLE SALESFORCE_OPPORTUNITIES (
    opportunity_id         VARCHAR(18)  NOT NULL PRIMARY KEY  COMMENT 'Salesforce opportunity id (e.g. 006Q000000A0142)',
    customer_id            VARCHAR(10)  NOT NULL REFERENCES CUSTOMERS(customer_id) COMMENT 'Salesforce account (same id as CUSTOMERS)',
    opportunity_name       VARCHAR(120) NOT NULL              COMMENT 'Opportunity name, e.g. Halvorsen Therapeutics - Cardiology Campaign FY25 or ... - Amendment 2',
    opportunity_type       VARCHAR(14)  NOT NULL              COMMENT 'New Business, Renewal or Amendment. An amendment is booked as its OWN opportunity for the incremental amount.',
    stage                  VARCHAR(12)  NOT NULL              COMMENT 'Always Closed Won in this extract',
    amount                 NUMBER(14,2) NOT NULL              COMMENT 'Booked amount in USD entered by the rep. For an amendment opportunity this is the INCREMENT (positive or negative), so the Salesforce value of a chain is the sum of its opportunities.',
    close_date             DATE         NOT NULL              COMMENT 'Closed-won date (normally the signature date)',
    contract_start_date    DATE         NOT NULL              COMMENT 'Contract start as entered by the rep',
    contract_end_date      DATE         NOT NULL              COMMENT 'Contract end as entered by the rep (an amendment opportunity carries the restated end date)',
    term_months            NUMBER(3,0)  NOT NULL              COMMENT 'Term in months as entered by the rep',
    owner                  VARCHAR(60)  NOT NULL              COMMENT 'Opportunity owner (sales rep)',
    linked_contract_number VARCHAR(24)                        COMMENT 'Contract number the rep linked (CONTRACTS.contract_number of the specific document, e.g. MCN-2025-0142-A1). Sometimes NULL or pointing at the wrong agreement.',
    last_modified_date     TIMESTAMP_NTZ NOT NULL             COMMENT 'Last modification timestamp in Salesforce'
) COMMENT = 'Closed-won opportunities replicated from Salesforce (one per signed document when the rep booked it). Entered by sales reps; the rep-side view of every deal.';

CREATE OR REPLACE TABLE SALESFORCE_OPPORTUNITY_PRODUCTS (
    opp_product_id         VARCHAR(18)  NOT NULL PRIMARY KEY  COMMENT 'Opportunity product line id',
    opportunity_id         VARCHAR(18)  NOT NULL REFERENCES SALESFORCE_OPPORTUNITIES(opportunity_id) COMMENT 'Opportunity',
    product_name           VARCHAR(60)  NOT NULL              COMMENT 'Product name (matches PRODUCTS.product_name)',
    quantity               NUMBER(6,0)  NOT NULL              COMMENT 'Units booked',
    unit_price             NUMBER(12,2) NOT NULL              COMMENT 'Price per unit booked by the rep in USD',
    total_price            NUMBER(14,2) NOT NULL              COMMENT 'quantity x unit_price in USD'
) COMMENT = 'Opportunity products replicated from Salesforce. Sum of total_price equals the opportunity amount.';

-- SECTION 4: NETSUITE REPLICA -------------------------------------------------

CREATE OR REPLACE TABLE NETSUITE_SALES_ORDERS (
    sales_order_id         VARCHAR(12)  NOT NULL PRIMARY KEY  COMMENT 'NetSuite sales order id (e.g. SO-10142)',
    customer_id            VARCHAR(10)  NOT NULL REFERENCES CUSTOMERS(customer_id) COMMENT 'NetSuite customer (same id as CUSTOMERS)',
    opportunity_id         VARCHAR(18)           REFERENCES SALESFORCE_OPPORTUNITIES(opportunity_id) COMMENT 'Salesforce opportunity the order was created from (populated by Boomi; sometimes missing)',
    order_date             DATE         NOT NULL              COMMENT 'Date the order was created in NetSuite',
    order_total            NUMBER(14,2) NOT NULL              COMMENT 'Order total in USD (sum of order lines). Boomi is supposed to restate it when an amendment arrives.',
    start_date             DATE         NOT NULL              COMMENT 'Service start used for revenue scheduling',
    end_date               DATE         NOT NULL              COMMENT 'Service end used for revenue scheduling. Boomi is supposed to restate it when an amendment extends the term.',
    payment_terms          VARCHAR(10)  NOT NULL              COMMENT 'Payment terms on the order (Net 30, Net 45, Net 60)',
    billing_schedule_type  VARCHAR(12)  NOT NULL              COMMENT 'NetSuite billing schedule type on the order: Upfront, Quarterly, Monthly or Milestone',
    status                 VARCHAR(20)  NOT NULL              COMMENT 'Pending Billing, Partially Billed, Billed or Closed',
    boomi_sync_timestamp   TIMESTAMP_NTZ NOT NULL             COMMENT 'Last time Boomi created or updated this order from Salesforce. If it precedes an amendment signature the order does not reflect that amendment.'
) COMMENT = 'Sales orders replicated from NetSuite. Normally one order per agreement that Boomi updates on amendments; occasionally Boomi creates a second order instead. Drives billing and revenue recognition.';

CREATE OR REPLACE TABLE NETSUITE_SALES_ORDER_LINES (
    so_line_id             VARCHAR(14)  NOT NULL PRIMARY KEY  COMMENT 'Order line id',
    sales_order_id         VARCHAR(12)  NOT NULL REFERENCES NETSUITE_SALES_ORDERS(sales_order_id) COMMENT 'Sales order',
    line_number            NUMBER(2,0)  NOT NULL              COMMENT 'Line order within the order',
    item_name              VARCHAR(60)  NOT NULL              COMMENT 'NetSuite item (matches PRODUCTS.product_name)',
    quantity               NUMBER(6,0)  NOT NULL              COMMENT 'Units',
    rate                   NUMBER(12,2) NOT NULL              COMMENT 'Price per unit in USD',
    amount                 NUMBER(14,2) NOT NULL              COMMENT 'quantity x rate in USD'
) COMMENT = 'Sales order lines replicated from NetSuite. Sum of amount equals the order total.';

CREATE OR REPLACE TABLE NETSUITE_BILLING_SCHEDULE (
    bill_id                VARCHAR(14)  NOT NULL PRIMARY KEY  COMMENT 'Billing schedule row id',
    sales_order_id         VARCHAR(12)  NOT NULL REFERENCES NETSUITE_SALES_ORDERS(sales_order_id) COMMENT 'Sales order the bill belongs to',
    bill_number            NUMBER(2,0)  NOT NULL              COMMENT 'Bill order within the sales order',
    bill_date              DATE         NOT NULL              COMMENT 'Scheduled invoice date',
    bill_amount            NUMBER(14,2) NOT NULL              COMMENT 'Scheduled invoice amount in USD',
    billed                 BOOLEAN      NOT NULL              COMMENT 'TRUE when the invoice has been issued (bill_date on or before 2026-09-30)',
    invoice_number         VARCHAR(16)                        COMMENT 'Invoice number once billed'
) COMMENT = 'Billing schedule lines replicated from NetSuite: what NetSuite will actually invoice and when. Reconciled against CONTRACT_BILLING_SCHEDULE (the schedule the customer signed).';

CREATE OR REPLACE TABLE DATA_DICTIONARY (
    table_name             VARCHAR(60)  NOT NULL              COMMENT 'Table or view name',
    column_name            VARCHAR(60)  NOT NULL              COMMENT 'Column or metric name',
    data_type              VARCHAR(30)                        COMMENT 'Snowflake data type',
    description            VARCHAR(500)                       COMMENT 'Business description',
    sample_value           VARCHAR(100)                       COMMENT 'Example value',
    metric_formula         VARCHAR(500)                       COMMENT 'Formula for derived metrics',
    business_owner         VARCHAR(60)                        COMMENT 'Business owner of the definition (e.g. Revenue Accounting)',
    source_system          VARCHAR(30)                        COMMENT 'Upstream system of record (DocuSign, Salesforce, NetSuite, Deal Desk)'
) COMMENT = 'Self-describing metadata with business ownership and source system, the physical half of the business glossary.';

-- SECTION 5: JOIN HELPER VIEWS ------------------------------------------------
-- These views make the three-way match possible but do NOT pre-decide it: there is
-- no status column anywhere. The comparison logic lives in the certified queries.
-- Demo as-of date 2026-09-30 is hardcoded where "today" is needed.

CREATE OR REPLACE VIEW V_CONTRACT_CHAIN
    COMMENT = 'One row per agreement (contract chain = the original document plus all its amendments) with the CURRENT state taken from the latest signed document: current TCV, end date, payment terms, billing frequency, distinct product count and milestone count, plus the original values and the amendment count. The grain for every reconciliation question (one chain = one closed deal). No reconciliation status here.'
AS
WITH v AS (
    SELECT
        c.*,
        COALESCE(c.parent_contract_id, c.contract_id) AS chain_id,
        ROW_NUMBER() OVER (PARTITION BY COALESCE(c.parent_contract_id, c.contract_id) ORDER BY c.amendment_number DESC) AS rn_latest,
        COUNT(*) OVER (PARTITION BY COALESCE(c.parent_contract_id, c.contract_id)) - 1 AS amendment_count
    FROM CONTRACTS c
),
lines AS (
    SELECT contract_id, COUNT(DISTINCT product_id) AS product_count, SUM(line_amount) AS line_total
    FROM CONTRACT_LINE_ITEMS GROUP BY contract_id
),
ms AS (
    SELECT contract_id, COUNT(*) AS milestone_count, SUM(scheduled_amount) AS milestone_total
    FROM CONTRACT_BILLING_SCHEDULE GROUP BY contract_id
)
SELECT
    o.contract_id                 AS chain_id,
    o.contract_number             AS contract_number,
    o.customer_id,
    cu.customer_name,
    cu.customer_type,
    cu.segment,
    cu.account_owner,
    cu.sales_pod,
    cu.region,
    o.contract_type               AS original_contract_type,
    o.signed_date                 AS original_signed_date,
    o.effective_date              AS effective_date,
    o.end_date                    AS original_end_date,
    o.total_contract_value        AS original_tcv,
    o.payment_terms               AS original_payment_terms,
    o.billing_frequency           AS original_billing_frequency,
    o.amendment_count,
    l.contract_id                 AS latest_contract_id,
    l.contract_number             AS latest_contract_number,
    l.amendment_number            AS latest_version,
    l.signed_date                 AS latest_signed_date,
    l.contract_type               AS latest_document_type,
    l.total_contract_value        AS current_tcv,
    l.end_date                    AS current_end_date,
    l.term_months                 AS current_term_months,
    l.payment_terms               AS current_payment_terms,
    l.billing_frequency           AS current_billing_frequency,
    l.auto_renew,
    l.cancellation_notice_days,
    l.product_summary             AS current_product_summary,
    l.pdf_file_name               AS latest_pdf_file_name,
    COALESCE(ln.product_count, 0) AS current_product_count,
    COALESCE(m.milestone_count, 0) AS current_milestone_count,
    CASE WHEN l.end_date >= DATE '2026-09-30' THEN TRUE ELSE FALSE END AS is_active_today
FROM v o
JOIN v l            ON l.chain_id = o.chain_id AND l.rn_latest = 1
JOIN CUSTOMERS cu   ON cu.customer_id = o.customer_id
LEFT JOIN lines ln  ON ln.contract_id = l.contract_id
LEFT JOIN ms m      ON m.contract_id = l.contract_id
WHERE o.parent_contract_id IS NULL;

CREATE OR REPLACE VIEW V_AMENDMENT_LINEAGE
    COMMENT = 'One row per signed document in each chain (version 0 = original, 1..n = amendments) with the values restated by that document and the change versus the previous version (TCV change, end date change in days, payment terms and billing frequency before and after). Neutral lineage: it does not say whether Salesforce or NetSuite reflect a version; compare with V_CHAIN_SYSTEM_SUMMARY for that.'
AS
WITH v AS (
    SELECT
        c.*,
        COALESCE(c.parent_contract_id, c.contract_id) AS chain_id,
        LAG(c.total_contract_value) OVER (PARTITION BY COALESCE(c.parent_contract_id, c.contract_id) ORDER BY c.amendment_number) AS previous_tcv,
        LAG(c.end_date)             OVER (PARTITION BY COALESCE(c.parent_contract_id, c.contract_id) ORDER BY c.amendment_number) AS previous_end_date,
        LAG(c.payment_terms)        OVER (PARTITION BY COALESCE(c.parent_contract_id, c.contract_id) ORDER BY c.amendment_number) AS previous_payment_terms,
        LAG(c.billing_frequency)    OVER (PARTITION BY COALESCE(c.parent_contract_id, c.contract_id) ORDER BY c.amendment_number) AS previous_billing_frequency,
        MAX(c.amendment_number)     OVER (PARTITION BY COALESCE(c.parent_contract_id, c.contract_id)) AS latest_version
    FROM CONTRACTS c
),
lines AS (
    SELECT contract_id, COUNT(DISTINCT product_id) AS product_count FROM CONTRACT_LINE_ITEMS GROUP BY contract_id
),
ms AS (
    SELECT contract_id, COUNT(*) AS milestone_count FROM CONTRACT_BILLING_SCHEDULE GROUP BY contract_id
)
SELECT
    v.chain_id,
    o.contract_number             AS chain_contract_number,
    v.customer_id,
    cu.customer_name,
    cu.customer_type,
    cu.account_owner,
    v.amendment_number            AS version,
    v.latest_version,
    CASE WHEN v.amendment_number = v.latest_version THEN TRUE ELSE FALSE END AS is_latest_version,
    v.contract_id,
    v.contract_number             AS document_number,
    v.contract_type               AS document_type,
    v.docusign_envelope_id,
    v.signed_date,
    v.effective_date,
    v.end_date,
    v.term_months,
    v.total_contract_value        AS tcv,
    v.previous_tcv,
    v.total_contract_value - COALESCE(v.previous_tcv, v.total_contract_value) AS tcv_change,
    v.previous_end_date,
    CASE WHEN v.previous_end_date IS NULL THEN 0 ELSE DATEDIFF('day', v.previous_end_date, v.end_date) END AS end_date_change_days,
    v.payment_terms,
    v.previous_payment_terms,
    v.billing_frequency,
    v.previous_billing_frequency,
    v.product_summary,
    v.special_terms,
    v.extraction_confidence,
    v.pdf_file_name,
    COALESCE(ln.product_count, 0) AS product_count,
    COALESCE(m.milestone_count, 0) AS milestone_count
FROM v
JOIN CONTRACTS o    ON o.contract_id = v.chain_id
JOIN CUSTOMERS cu   ON cu.customer_id = v.customer_id
LEFT JOIN lines ln  ON ln.contract_id = v.contract_id
LEFT JOIN ms m      ON m.contract_id = v.contract_id;

CREATE OR REPLACE VIEW V_DEAL_CROSSWALK
    COMMENT = 'Row-level map from each contract chain to its Salesforce opportunity(ies) and NetSuite sales order(s). Opportunities link by linked_contract_number (any version of the chain) for the same customer; sales orders link through the opportunity id or, when Boomi left it empty or the chain has no linked opportunity, by customer and service start date. Broken links are kept as NULL columns (a chain with no opportunity, an opportunity with no order) and opportunities that resolve to no agreement appear with NULL chain columns. Grain is chain x opportunity x sales order, so count DISTINCT ids when aggregating.'
AS
WITH ch AS (
    SELECT chain_id, contract_number, customer_id, customer_name, customer_type, account_owner,
           effective_date, latest_contract_number, latest_version, current_tcv
    FROM V_CONTRACT_CHAIN
),
opp AS (
    SELECT o.*,
           SPLIT_PART(o.linked_contract_number, '-A', 1) AS linked_chain_number,
           CASE WHEN o.linked_contract_number LIKE '%-A%' THEN CAST(SPLIT_PART(o.linked_contract_number, '-A', 2) AS INTEGER) ELSE 0 END AS linked_version
    FROM SALESFORCE_OPPORTUNITIES o
),
linked AS (
    SELECT ch.chain_id, ch.contract_number, ch.customer_id, ch.customer_name, ch.customer_type, ch.account_owner,
           ch.effective_date, ch.latest_contract_number, ch.latest_version, ch.current_tcv,
           opp.opportunity_id, opp.opportunity_name, opp.opportunity_type, opp.amount AS opportunity_amount,
           opp.close_date, opp.contract_start_date AS opp_start_date, opp.contract_end_date AS opp_end_date,
           opp.owner AS opportunity_owner, opp.linked_contract_number, opp.linked_version,
           'linked' AS link_kind
    FROM ch
    LEFT JOIN opp ON opp.linked_chain_number = ch.contract_number AND opp.customer_id = ch.customer_id
),
orphan AS (
    SELECT CAST(NULL AS VARCHAR) AS chain_id, CAST(NULL AS VARCHAR) AS contract_number, opp.customer_id, cu.customer_name, cu.customer_type, cu.account_owner,
           CAST(NULL AS DATE) AS effective_date, CAST(NULL AS VARCHAR) AS latest_contract_number, CAST(NULL AS INTEGER) AS latest_version, CAST(NULL AS NUMERIC(14,2)) AS current_tcv,
           opp.opportunity_id, opp.opportunity_name, opp.opportunity_type, opp.amount AS opportunity_amount,
           opp.close_date, opp.contract_start_date AS opp_start_date, opp.contract_end_date AS opp_end_date,
           opp.owner AS opportunity_owner, opp.linked_contract_number, opp.linked_version,
           'orphan_opportunity' AS link_kind
    FROM opp
    JOIN CUSTOMERS cu ON cu.customer_id = opp.customer_id
    WHERE NOT EXISTS (SELECT 1 FROM ch WHERE ch.contract_number = opp.linked_chain_number AND ch.customer_id = opp.customer_id)
),
x AS (
    SELECT * FROM linked
    UNION ALL
    SELECT * FROM orphan
)
SELECT
    x.chain_id, x.contract_number, x.customer_id, x.customer_name, x.customer_type, x.account_owner,
    x.effective_date, x.latest_contract_number, x.latest_version, x.current_tcv,
    x.opportunity_id, x.opportunity_name, x.opportunity_type, x.opportunity_amount, x.close_date,
    x.opp_start_date, x.opp_end_date, x.opportunity_owner, x.linked_contract_number, x.linked_version, x.link_kind,
    so.sales_order_id,
    so.opportunity_id              AS so_opportunity_id,
    so.order_date,
    so.order_total,
    so.start_date                  AS so_start_date,
    so.end_date                    AS so_end_date,
    so.payment_terms               AS so_payment_terms,
    so.billing_schedule_type       AS so_billing_schedule_type,
    so.status                      AS so_status,
    so.boomi_sync_timestamp,
    CASE WHEN so.sales_order_id IS NULL THEN NULL
         WHEN so.opportunity_id IS NOT NULL AND so.opportunity_id = x.opportunity_id THEN 'opportunity_id'
         ELSE 'customer_and_start_date' END AS so_link_method
FROM x
LEFT JOIN NETSUITE_SALES_ORDERS so
       ON (x.opportunity_id IS NOT NULL AND so.opportunity_id = x.opportunity_id)
       OR ((so.opportunity_id IS NULL OR x.opportunity_id IS NULL) AND x.chain_id IS NOT NULL AND so.customer_id = x.customer_id AND so.start_date = x.effective_date);

CREATE OR REPLACE VIEW V_CHAIN_SYSTEM_SUMMARY
    COMMENT = 'One row per contract chain with the three systems side by side: the contract current values (from the latest signed document), the Salesforce chain values (sum of its opportunities, distinct products, highest amendment version linked) and the NetSuite chain values (distinct sales orders, total, end date, payment terms, billing schedule type, last Boomi sync, highest amendment version signed on or before that sync). Nothing is compared here; the certified checks compare these columns against the tolerances in RECONCILIATION_CONTROLS.'
AS
WITH sf AS (
    SELECT chain_id,
           COUNT(DISTINCT opportunity_id)        AS sf_opportunity_count,
           SUM(opportunity_amount)               AS sf_amount,
           MAX(opp_end_date)                     AS sf_end_date,
           MAX(close_date)                       AS sf_last_close_date,
           MAX(linked_version)                   AS sf_version_reflected
    FROM (SELECT DISTINCT chain_id, opportunity_id, opportunity_amount, opp_end_date, close_date, linked_version
          FROM V_DEAL_CROSSWALK WHERE chain_id IS NOT NULL AND opportunity_id IS NOT NULL) d
    GROUP BY chain_id
),
sfp AS (
    SELECT d.chain_id, COUNT(DISTINCT p.product_name) AS sf_product_count
    FROM (SELECT DISTINCT chain_id, opportunity_id FROM V_DEAL_CROSSWALK WHERE chain_id IS NOT NULL AND opportunity_id IS NOT NULL) d
    JOIN SALESFORCE_OPPORTUNITY_PRODUCTS p ON p.opportunity_id = d.opportunity_id
    GROUP BY d.chain_id
),
ns AS (
    SELECT chain_id,
           COUNT(DISTINCT sales_order_id)        AS ns_sales_order_count,
           SUM(order_total)                      AS ns_amount,
           MAX(so_end_date)                      AS ns_end_date,
           MIN(so_start_date)                    AS ns_start_date,
           MAX(so_payment_terms)                 AS ns_payment_terms,
           MAX(so_billing_schedule_type)         AS ns_billing_schedule_type,
           MAX(boomi_sync_timestamp)             AS ns_last_sync,
           SUM(CASE WHEN so_opportunity_id IS NULL THEN 1 ELSE 0 END) AS ns_orders_without_opportunity
    FROM (SELECT DISTINCT chain_id, sales_order_id, order_total, so_end_date, so_start_date, so_payment_terms, so_billing_schedule_type, boomi_sync_timestamp, so_opportunity_id
          FROM V_DEAL_CROSSWALK WHERE chain_id IS NOT NULL AND sales_order_id IS NOT NULL) d
    GROUP BY chain_id
),
nsb AS (
    SELECT d.chain_id, COUNT(*) AS ns_bill_count, SUM(b.bill_amount) AS ns_bill_total,
           SUM(CASE WHEN b.billed THEN b.bill_amount ELSE 0 END) AS ns_billed_to_date
    FROM (SELECT DISTINCT chain_id, sales_order_id FROM V_DEAL_CROSSWALK WHERE chain_id IS NOT NULL AND sales_order_id IS NOT NULL) d
    JOIN NETSUITE_BILLING_SCHEDULE b ON b.sales_order_id = d.sales_order_id
    GROUP BY d.chain_id
),
nsv AS (
    SELECT l.chain_id, MAX(l.version) AS ns_version_reflected
    FROM V_AMENDMENT_LINEAGE l
    JOIN ns ON ns.chain_id = l.chain_id AND l.signed_date <= CAST(ns.ns_last_sync AS DATE)
    GROUP BY l.chain_id
)
SELECT
    ch.chain_id, ch.contract_number, ch.customer_id, ch.customer_name, ch.customer_type, ch.segment, ch.account_owner, ch.sales_pod, ch.region,
    ch.original_signed_date, ch.effective_date, ch.amendment_count, ch.latest_version, ch.latest_signed_date, ch.latest_contract_number, ch.is_active_today,
    ch.current_tcv, ch.current_end_date, ch.current_payment_terms, ch.current_billing_frequency, ch.current_product_count, ch.current_milestone_count,
    ch.original_tcv, ch.original_end_date,
    COALESCE(sf.sf_opportunity_count, 0)  AS sf_opportunity_count,
    sf.sf_amount,
    sf.sf_end_date,
    sf.sf_last_close_date,
    sf.sf_version_reflected,
    sfp.sf_product_count,
    COALESCE(ns.ns_sales_order_count, 0)  AS ns_sales_order_count,
    ns.ns_amount,
    ns.ns_start_date,
    ns.ns_end_date,
    ns.ns_payment_terms,
    ns.ns_billing_schedule_type,
    ns.ns_last_sync,
    COALESCE(nsv.ns_version_reflected, CASE WHEN ns.chain_id IS NULL THEN NULL ELSE 0 END) AS ns_version_reflected,
    COALESCE(ns.ns_orders_without_opportunity, 0) AS ns_orders_without_opportunity,
    nsb.ns_bill_count,
    nsb.ns_bill_total,
    nsb.ns_billed_to_date
FROM V_CONTRACT_CHAIN ch
LEFT JOIN sf  ON sf.chain_id = ch.chain_id
LEFT JOIN sfp ON sfp.chain_id = ch.chain_id
LEFT JOIN ns  ON ns.chain_id = ch.chain_id
LEFT JOIN nsb ON nsb.chain_id = ch.chain_id
LEFT JOIN nsv ON nsv.chain_id = ch.chain_id;
