-- ============================================================================
-- WisdomAI POC — Keelstone Data Systems
-- Snowflake DDL
-- Domain: fictional hybrid-cloud storage and data infrastructure vendor.
--   Storage arrays (KS-5000 / KS-7000 / KS-9000 / HD-3000 families), the KeelOS
--   storage operating system sold by subscription, Keelstone Cloud Volumes on the
--   hyperscalers, and support contracts, sold mostly through channel partners.
-- Demo "today": 2026-10-12 (Q2 FY27). Fiscal year ends 30 April (FY27 = 2026-05-01 .. 2027-04-30).
-- Data spans 2025-05-01 .. 2026-10-12 (contracts and installs reach back earlier).
-- Source systems represented: SAP S/4HANA (orders, contracts), Salesforce (renewal
--   opportunities), ServiceNow (support cases), AutoPulse telemetry (installed base).
-- ============================================================================

-- SECTION 0: ENVIRONMENT SETUP -------------------------------------------------
USE ROLE SYSADMIN;
CREATE DATABASE IF NOT EXISTS KEELSTONE_POC
    COMMENT = 'WisdomAI POC database for the Keelstone Data Systems demo';
CREATE SCHEMA IF NOT EXISTS KEELSTONE_POC.ANALYTICS
    COMMENT = 'Keelstone revenue operations analytics: bookings, installed base, contracts, renewals, cloud consumption, support cases';
USE DATABASE KEELSTONE_POC;
USE SCHEMA ANALYTICS;

-- SECTION 1: FILE FORMAT + STAGE ----------------------------------------------
CREATE OR REPLACE FILE FORMAT CSV_STANDARD
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    RECORD_DELIMITER = '\n'
    SKIP_HEADER = 1
    NULL_IF = ('', 'NULL')
    EMPTY_FIELD_AS_NULL = TRUE
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    DATE_FORMAT = 'YYYY-MM-DD'
    TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS';

CREATE OR REPLACE STAGE LOAD_STAGE
    FILE_FORMAT = (FORMAT_NAME = 'CSV_STANDARD');

-- SECTION 2: DIMENSION TABLES -------------------------------------------------

CREATE OR REPLACE TABLE FISCAL_CALENDAR (
    calendar_date          DATE         NOT NULL PRIMARY KEY  COMMENT 'Calendar day',
    month_start_date       DATE         NOT NULL              COMMENT 'First day of the calendar month',
    month_end_date         DATE         NOT NULL              COMMENT 'Last day of the calendar month',
    fiscal_year            VARCHAR(4)   NOT NULL              COMMENT 'Keelstone fiscal year label. The fiscal year ends 30 April and is named for the calendar year it ends in (FY27 = 2026-05-01 .. 2027-04-30).',
    fiscal_quarter         VARCHAR(8)   NOT NULL              COMMENT 'Fiscal quarter label, e.g. FY27-Q2 (Aug-Oct 2026). Q1 = May-Jul, Q2 = Aug-Oct, Q3 = Nov-Jan, Q4 = Feb-Apr.',
    fiscal_month_num       NUMBER(2,0)  NOT NULL              COMMENT 'Month number within the fiscal year (May = 1 .. April = 12)',
    fiscal_year_start_date DATE         NOT NULL              COMMENT 'First day of the fiscal year containing this date',
    calendar_quarter       VARCHAR(7)   NOT NULL              COMMENT 'Calendar quarter label, e.g. 2026-Q3',
    is_complete_month      BOOLEAN      NOT NULL              COMMENT 'TRUE when the whole calendar month is on or before the demo as-of date 2026-10-12. Use to exclude the partial current month from trends.',
    is_weekend             BOOLEAN      NOT NULL              COMMENT 'TRUE for Saturday and Sunday'
) COMMENT = 'Date dimension 2024-05-01 .. 2027-04-30 with Keelstone fiscal labels (fiscal year ends 30 April). Join on calendar_date.';

CREATE OR REPLACE TABLE PARTNERS (
    partner_id             VARCHAR(10)  NOT NULL PRIMARY KEY  COMMENT 'Partner code (e.g. PTR-003). PTR-000 is Keelstone Direct (no partner).',
    partner_name           VARCHAR(80)  NOT NULL              COMMENT 'Fictional channel partner name (e.g. Altura Technology Partners)',
    partner_type           VARCHAR(20)  NOT NULL              COMMENT 'VAR, DISTRIBUTOR, MSP, or DIRECT (Keelstone direct sales)',
    partner_tier           VARCHAR(10)  NOT NULL              COMMENT 'Program tier: PLATINUM, GOLD, SILVER, or NA for direct',
    primary_region         VARCHAR(20)  NOT NULL              COMMENT 'Region the partner mainly sells into: Americas East, Americas West, EMEA, APAC, or Global',
    hq_country             VARCHAR(30)                        COMMENT 'Headquarters country',
    partner_since          DATE                               COMMENT 'Date the partner joined the Keelstone partner program'
) COMMENT = 'Channel partners (VARs, distributors, MSPs) through which Keelstone sells. Source: partner master in Salesforce.';

CREATE OR REPLACE TABLE SALES_REPS (
    rep_id                 VARCHAR(10)  NOT NULL PRIMARY KEY  COMMENT 'Sales rep code (e.g. REP-017)',
    rep_name               VARCHAR(80)  NOT NULL              COMMENT 'Fictional rep name',
    rep_role               VARCHAR(30)  NOT NULL              COMMENT 'Account Executive, Renewals Specialist, or Cloud Specialist',
    region                 VARCHAR(20)  NOT NULL              COMMENT 'Sales region: Americas East, Americas West, EMEA, or APAC',
    theater                VARCHAR(15)  NOT NULL              COMMENT 'Americas or International',
    manager_name           VARCHAR(80)                        COMMENT 'Regional sales director the rep reports to',
    hire_date              DATE                               COMMENT 'Hire date',
    is_active              BOOLEAN      NOT NULL              COMMENT 'TRUE if the rep is currently employed'
) COMMENT = 'Sales reps and renewals specialists who own customer accounts and renewal opportunities. Source: Salesforce user records.';

CREATE OR REPLACE TABLE CUSTOMERS (
    customer_id            VARCHAR(10)  NOT NULL PRIMARY KEY  COMMENT 'Customer code (e.g. CUST-0042)',
    customer_name          VARCHAR(100) NOT NULL              COMMENT 'Fictional customer company name',
    crm_account_id         VARCHAR(18)  NOT NULL              COMMENT 'Salesforce account id (18 characters)',
    segment                VARCHAR(15)  NOT NULL              COMMENT 'ENTERPRISE, COMMERCIAL, or PUBLIC_SECTOR',
    industry               VARCHAR(40)                        COMMENT 'Customer industry (Financial Services, Healthcare, Manufacturing, Retail, Technology, Public Sector, Education, Media, Energy, Life Sciences)',
    region                 VARCHAR(20)  NOT NULL              COMMENT 'Keelstone sales region: Americas East, Americas West, EMEA, or APAC',
    country                VARCHAR(30)                        COMMENT 'Headquarters country',
    partner_id             VARCHAR(10)  NOT NULL REFERENCES PARTNERS(partner_id)  COMMENT 'Partner of record for the account (PTR-000 when sold direct)',
    rep_id                 VARCHAR(10)  NOT NULL REFERENCES SALES_REPS(rep_id)    COMMENT 'Owning account executive',
    customer_since         DATE                               COMMENT 'Date of the first Keelstone purchase',
    is_active              BOOLEAN      NOT NULL              COMMENT 'TRUE if the customer has at least one active contract or system'
) COMMENT = 'Customer accounts. Source: Salesforce account master, enriched with SAP sold-to attributes. ~400 rows.';

CREATE OR REPLACE TABLE PRODUCTS (
    product_id             VARCHAR(15)  NOT NULL PRIMARY KEY  COMMENT 'Product SKU (e.g. KS-7400, KOS-CORE, KCV-AZURE, SUP-PREM)',
    product_name           VARCHAR(80)  NOT NULL              COMMENT 'Product display name',
    product_family         VARCHAR(40)  NOT NULL              COMMENT 'Family: KS-5000, KS-7000, KS-9000, HD-3000 (arrays); KeelOS (software); Keelstone Cloud Volumes, Keelstone Object Store (cloud); Support',
    product_line           VARCHAR(25)  NOT NULL              COMMENT 'HARDWARE, SOFTWARE_SUBSCRIPTION, CLOUD_SERVICE, or SUPPORT',
    support_tier           VARCHAR(20)                        COMMENT 'For SUPPORT products: STANDARD, PREMIUM, MISSION_CRITICAL, or EXTENDED. NULL otherwise.',
    list_price             NUMBER(12,2) NOT NULL              COMMENT 'List price per unit of measure in USD',
    unit_of_measure        VARCHAR(20)  NOT NULL              COMMENT 'SYSTEM (one-time hardware), TB_PER_YEAR, COMMIT_USD_PER_YEAR, or SYSTEM_PER_YEAR',
    general_availability_date DATE                            COMMENT 'Date the product became generally available',
    end_of_sale_date       DATE                               COMMENT 'Last date the product can be ordered. NULL if still sold.',
    end_of_support_date    DATE                               COMMENT 'Date Keelstone stops supporting the product. KS-7000 family ends support 2027-01-31 (bulletin PLB-2026-014, announced 2026-06-15).',
    is_recurring           BOOLEAN      NOT NULL              COMMENT 'TRUE for products that generate ARR (subscriptions, cloud commits, support). Hardware is a one-time booking, never ARR.',
    description            VARCHAR(300)                       COMMENT 'Short plain-language description'
) COMMENT = 'Product catalog: arrays, KeelOS subscriptions, cloud services and support tiers, with lifecycle dates. Source: SAP material master.';

-- SECTION 3: FACT TABLES ------------------------------------------------------

CREATE OR REPLACE TABLE ORDERS (
    order_line_id          VARCHAR(16)  NOT NULL PRIMARY KEY  COMMENT 'Order line id (e.g. OL-00012345)',
    order_id               VARCHAR(14)  NOT NULL              COMMENT 'Order header id; one order can have several lines',
    sap_sales_order        VARCHAR(12)  NOT NULL              COMMENT 'SAP S/4HANA sales order number',
    order_date             DATE         NOT NULL              COMMENT 'Booking date (the date the order was accepted). Bookings are recognised on this date; revenue is not modelled here.',
    customer_id            VARCHAR(10)  NOT NULL REFERENCES CUSTOMERS(customer_id)  COMMENT 'Sold-to customer',
    product_id             VARCHAR(15)  NOT NULL REFERENCES PRODUCTS(product_id)    COMMENT 'Product ordered',
    partner_id             VARCHAR(10)  NOT NULL REFERENCES PARTNERS(partner_id)    COMMENT 'Partner the order was booked through (PTR-000 = direct)',
    rep_id                 VARCHAR(10)  NOT NULL REFERENCES SALES_REPS(rep_id)      COMMENT 'Rep credited with the booking',
    booking_type           VARCHAR(12)  NOT NULL              COMMENT 'NEW (first purchase of the product), EXPANSION (additional capacity or systems), or RENEWAL (renewal of a contract)',
    quantity               NUMBER(10,2) NOT NULL              COMMENT 'Units ordered in the product unit of measure (systems, TB, commit USD, or system-years)',
    list_amount            NUMBER(14,2) NOT NULL              COMMENT 'Quantity times list price in USD',
    discount_pct           NUMBER(5,2)  NOT NULL              COMMENT 'Discount from list, percent (0-100)',
    net_amount             NUMBER(14,2) NOT NULL              COMMENT 'Booked amount in USD after discount. For multi-year contracts this is the total contract value, not ARR.',
    source_system          VARCHAR(20)  NOT NULL              COMMENT 'System of record: SAP S/4HANA'
) COMMENT = 'Bookings at order-line grain from SAP S/4HANA, 2025-05-01 onward. Hardware, subscription, cloud commit and support bookings. Bookings are not ARR: use CONTRACTS / V_ARR_MONTHLY for ARR.';

CREATE OR REPLACE TABLE INSTALLED_SYSTEMS (
    system_id              VARCHAR(16)  NOT NULL PRIMARY KEY  COMMENT 'System serial number (e.g. KS7-2024-01234)',
    customer_id            VARCHAR(10)  NOT NULL REFERENCES CUSTOMERS(customer_id)  COMMENT 'Customer the system is installed at',
    product_id             VARCHAR(15)  NOT NULL REFERENCES PRODUCTS(product_id)    COMMENT 'Array model (HARDWARE product)',
    partner_id             VARCHAR(10)  NOT NULL REFERENCES PARTNERS(partner_id)    COMMENT 'Partner that sold and installed the system',
    order_line_id          VARCHAR(16)           REFERENCES ORDERS(order_line_id)   COMMENT 'Hardware order line that shipped this system. NULL for systems installed before 2025-05-01.',
    install_date           DATE         NOT NULL              COMMENT 'Date the system went into production',
    site_city              VARCHAR(50)                        COMMENT 'Installation site city',
    site_country           VARCHAR(30)                        COMMENT 'Installation site country',
    raw_capacity_tb        NUMBER(8,1)  NOT NULL              COMMENT 'Raw capacity in terabytes',
    workload_type          VARCHAR(30)                        COMMENT 'Primary workload: Virtualization, Databases, File Services, Backup Target, Analytics, or EHR',
    current_firmware       VARCHAR(15)  NOT NULL              COMMENT 'KeelOS version currently running (e.g. KeelOS 9.14.2) as of 2026-10-12',
    system_status          VARCHAR(15)  NOT NULL              COMMENT 'ACTIVE or DECOMMISSIONED',
    decommission_date      DATE                               COMMENT 'Date the system was retired. NULL while active.'
) COMMENT = 'Installed base: every array Keelstone has shipped, from the AutoPulse telemetry registry. ~2,500 rows. Attach rate and end-of-support exposure start here.';

CREATE OR REPLACE TABLE SYSTEM_TELEMETRY_MONTHLY (
    telemetry_id           VARCHAR(24)  NOT NULL PRIMARY KEY  COMMENT 'Row id (system id plus month)',
    system_id              VARCHAR(16)  NOT NULL REFERENCES INSTALLED_SYSTEMS(system_id)  COMMENT 'System reporting',
    snapshot_month         DATE         NOT NULL              COMMENT 'First day of the month the snapshot summarises',
    firmware_version       VARCHAR(15)  NOT NULL              COMMENT 'KeelOS version running at month end',
    capacity_used_pct      NUMBER(5,2)  NOT NULL              COMMENT 'Percent of raw capacity in use at month end (0-100)',
    health_score           NUMBER(5,1)  NOT NULL              COMMENT 'AutoPulse health score 0-100; below 70 is poor',
    critical_alerts        NUMBER(4,0)  NOT NULL              COMMENT 'Critical AutoPulse alerts raised during the month',
    uptime_pct             NUMBER(6,3)  NOT NULL              COMMENT 'Percent uptime in the month',
    avg_latency_ms         NUMBER(6,2)  NOT NULL              COMMENT 'Average I/O latency in milliseconds',
    source_system          VARCHAR(20)  NOT NULL              COMMENT 'System of record: AutoPulse'
) COMMENT = 'Monthly telemetry per active system from AutoPulse (Keelstone call-home service), 2025-05 .. 2026-09. ~40K rows. Use the latest month for current state.';

CREATE OR REPLACE TABLE CONTRACTS (
    contract_id            VARCHAR(14)  NOT NULL PRIMARY KEY  COMMENT 'Contract id (e.g. CTR-0012345)',
    customer_id            VARCHAR(10)  NOT NULL REFERENCES CUSTOMERS(customer_id)  COMMENT 'Contracting customer',
    product_id             VARCHAR(15)  NOT NULL REFERENCES PRODUCTS(product_id)    COMMENT 'Recurring product: support tier, KeelOS subscription, or cloud commit',
    system_id              VARCHAR(16)           REFERENCES INSTALLED_SYSTEMS(system_id)  COMMENT 'System covered, for SUPPORT and per-array KeelOS Core subscriptions. NULL for customer-level add-ons and cloud commits.',
    partner_id             VARCHAR(10)  NOT NULL REFERENCES PARTNERS(partner_id)    COMMENT 'Partner of record on the contract (PTR-000 = direct)',
    rep_id                 VARCHAR(10)  NOT NULL REFERENCES SALES_REPS(rep_id)      COMMENT 'Rep or renewals specialist who owns the contract',
    order_line_id          VARCHAR(16)           REFERENCES ORDERS(order_line_id)   COMMENT 'Booking that created this contract. NULL for contracts booked before 2025-05-01.',
    contract_type          VARCHAR(22)  NOT NULL              COMMENT 'SUPPORT, SOFTWARE_SUBSCRIPTION, or CLOUD_COMMIT',
    start_date             DATE         NOT NULL              COMMENT 'First day the contract is in force',
    end_date               DATE         NOT NULL              COMMENT 'Day after the last day in force (exclusive). ARR counts the contract while start_date <= date < end_date.',
    term_months            NUMBER(3,0)  NOT NULL              COMMENT 'Contract term in months (12, 24, or 36)',
    annual_value           NUMBER(14,2) NOT NULL              COMMENT 'Annualised contract value in USD: the ARR contribution while in force',
    total_contract_value   NUMBER(14,2) NOT NULL              COMMENT 'annual_value times term in years',
    contract_status        VARCHAR(16)  NOT NULL              COMMENT 'As of 2026-10-12: ACTIVE (end_date in the future), RENEWED (a successor contract was signed), CHURNED (lapsed with no successor), or PENDING_RENEWAL (lapsed, renewal still open)',
    outcome_date           DATE                               COMMENT 'Date the renewal outcome was recorded: the successor start date for RENEWED, the Closed Lost date for CHURNED. NULL while ACTIVE or PENDING_RENEWAL.',
    successor_contract_id  VARCHAR(14)           REFERENCES CONTRACTS(contract_id)  COMMENT 'The renewal contract that replaced this one, when RENEWED',
    predecessor_contract_id VARCHAR(14)          REFERENCES CONTRACTS(contract_id)  COMMENT 'The contract this one renewed, when it is a renewal',
    source_system          VARCHAR(20)  NOT NULL              COMMENT 'System of record: SAP S/4HANA'
) COMMENT = 'Recurring contracts from SAP: support on installed systems, KeelOS subscriptions, cloud commits. ~5K rows including history. ARR = sum of annual_value of contracts in force on a date.';

CREATE OR REPLACE TABLE RENEWAL_OPPORTUNITIES (
    opportunity_id         VARCHAR(18)  NOT NULL PRIMARY KEY  COMMENT 'Salesforce opportunity id',
    contract_id            VARCHAR(14)  NOT NULL REFERENCES CONTRACTS(contract_id)  COMMENT 'Contract being renewed',
    customer_id            VARCHAR(10)  NOT NULL REFERENCES CUSTOMERS(customer_id)  COMMENT 'Customer',
    rep_id                 VARCHAR(10)  NOT NULL REFERENCES SALES_REPS(rep_id)      COMMENT 'Opportunity owner',
    created_date           DATE         NOT NULL              COMMENT 'Opportunity creation date, 120 days before the contract end date',
    expected_close_date    DATE         NOT NULL              COMMENT 'Expected close date (the contract end date)',
    actual_close_date      DATE                               COMMENT 'Date the opportunity was Closed Won or Closed Lost. NULL while open.',
    stage                  VARCHAR(20)  NOT NULL              COMMENT 'Qualification, Quote Sent, Negotiation, Closed Won, or Closed Lost',
    quote_amount           NUMBER(14,2) NOT NULL              COMMENT 'Quoted annual value in USD',
    risk_flag              VARCHAR(10)  NOT NULL              COMMENT 'ON_TRACK or AT_RISK, set by the renewals team',
    risk_reason            VARCHAR(60)                        COMMENT 'Why the renewal is at risk: End of support product, Open P1 case, Budget, Competitive, Consolidation. NULL when on track.',
    competitor             VARCHAR(40)                        COMMENT 'Competing vendor named by the customer, when known',
    source_system          VARCHAR(20)  NOT NULL              COMMENT 'System of record: Salesforce'
) COMMENT = 'Renewal opportunities from Salesforce, one per contract ending between 2025-05-01 and 2027-04-10. A renewal opportunity stays open after the contract lapses until renewals ops closes it lost (up to a year); Finance stops counting ARR at end_date.';

CREATE OR REPLACE TABLE CLOUD_CONSUMPTION_MONTHLY (
    consumption_id         VARCHAR(20)  NOT NULL PRIMARY KEY  COMMENT 'Row id (customer plus month)',
    customer_id            VARCHAR(10)  NOT NULL REFERENCES CUSTOMERS(customer_id)  COMMENT 'Consuming customer',
    product_id             VARCHAR(15)  NOT NULL REFERENCES PRODUCTS(product_id)    COMMENT 'Cloud service consumed',
    contract_id            VARCHAR(14)  NOT NULL REFERENCES CONTRACTS(contract_id)  COMMENT 'Cloud commit contract in force for the month',
    usage_month            DATE         NOT NULL              COMMENT 'First day of the usage month',
    cloud_provider         VARCHAR(10)  NOT NULL              COMMENT 'Azure, AWS, or GCP',
    monthly_commit_amount  NUMBER(12,2) NOT NULL              COMMENT 'One twelfth of the annual commit in USD',
    consumed_amount        NUMBER(12,2) NOT NULL              COMMENT 'Metered consumption in USD for the month',
    consumed_tb            NUMBER(10,2) NOT NULL              COMMENT 'Average provisioned terabytes in the month',
    overage_amount         NUMBER(12,2) NOT NULL              COMMENT 'Consumption above the monthly commit in USD (0 when under)'
) COMMENT = 'Monthly cloud consumption against commit for Keelstone Cloud Volumes and Object Store customers, 2025-05 .. 2026-09. Commit utilisation = consumed / commit.';

CREATE OR REPLACE TABLE SUPPORT_CASES (
    case_id                VARCHAR(12)  NOT NULL PRIMARY KEY  COMMENT 'ServiceNow case number (e.g. CS0412345)',
    customer_id            VARCHAR(10)  NOT NULL REFERENCES CUSTOMERS(customer_id)  COMMENT 'Customer who opened the case',
    system_id              VARCHAR(16)           REFERENCES INSTALLED_SYSTEMS(system_id)  COMMENT 'System the case is about. NULL for cloud and software-only cases.',
    product_id             VARCHAR(15)  NOT NULL REFERENCES PRODUCTS(product_id)    COMMENT 'Product the case is logged against',
    opened_date            DATE         NOT NULL              COMMENT 'Date opened',
    closed_date            DATE                               COMMENT 'Date closed. NULL while open.',
    priority               VARCHAR(2)   NOT NULL              COMMENT 'P1 (production down), P2 (severely degraded), P3 (minor impact), P4 (question)',
    case_status            VARCHAR(12)  NOT NULL              COMMENT 'OPEN or CLOSED as of 2026-10-12',
    category               VARCHAR(20)  NOT NULL              COMMENT 'Firmware, Hardware, Performance, Capacity, Configuration, Cloud, or Licensing',
    subcategory            VARCHAR(40)                        COMMENT 'Finer classification, e.g. Controller failover, Drive failure, Latency, Upgrade',
    firmware_version       VARCHAR(15)                        COMMENT 'KeelOS version on the system when the case was opened. NULL for cloud cases.',
    root_cause             VARCHAR(60)                        COMMENT 'Root cause recorded at closure, e.g. KeelOS 9.14.2 defect KB-2026-0917. NULL while open or if unknown.',
    resolution_hours       NUMBER(8,1)                        COMMENT 'Hours from open to close. NULL while open.',
    csat_score             NUMBER(2,0)                        COMMENT 'Customer satisfaction survey score 1-5 after closure. NULL if not answered.',
    case_notes             VARCHAR(3000) NOT NULL             COMMENT 'Free-text engineer notes: symptoms, actions taken, customer sentiment. Unstructured; read it to understand why a case matters.',
    source_system          VARCHAR(20)  NOT NULL              COMMENT 'System of record: ServiceNow'
) COMMENT = 'Support cases from ServiceNow, 2025-05-01 .. 2026-10-12. ~6K rows. case_notes is free text written by support engineers.';

CREATE OR REPLACE TABLE DATA_DICTIONARY (
    table_name             VARCHAR(60)  NOT NULL              COMMENT 'Table or view name',
    column_name            VARCHAR(60)  NOT NULL              COMMENT 'Column or metric name',
    data_type              VARCHAR(30)                        COMMENT 'Snowflake data type',
    description            VARCHAR(500)                       COMMENT 'Business description',
    sample_value           VARCHAR(100)                       COMMENT 'Example value',
    metric_formula         VARCHAR(500)                       COMMENT 'Formula for derived metrics',
    business_owner         VARCHAR(60)                        COMMENT 'Business owner of the definition (e.g. Finance - FP&A)',
    source_system          VARCHAR(30)                        COMMENT 'Upstream system of record'
) COMMENT = 'Self-describing metadata with business ownership and source system, the physical half of the business glossary.';

-- SECTION 4: ANALYTICAL VIEWS -------------------------------------------------
-- Demo as-of date is 2026-10-12 and is hardcoded where a "today" is needed.

CREATE OR REPLACE VIEW V_ARR_MONTHLY
    COMMENT = 'Certified Finance ARR by month: the sum of annual_value of contracts in force on the measurement date (month end, or 2026-10-12 for the current month), sliced by region, segment, contract type and product family (for support and KeelOS Core contracts the family of the covered array, e.g. KS-7000). This is the ARR definition of record (Finance Metric Definitions Standard v3.2). Sum ARR across slices within one month; never sum across months.'
AS
SELECT
    m.arr_month,
    m.arr_as_of_date,
    m.fiscal_year,
    m.fiscal_quarter,
    cu.region,
    cu.segment,
    c.contract_type,
    COALESCE(sp.product_family, p.product_family)   AS product_family,
    COUNT(*)                                  AS active_contracts,
    SUM(c.annual_value)                       AS arr
FROM (
    SELECT DISTINCT
        month_start_date                                                        AS arr_month,
        CASE WHEN month_end_date > DATE '2026-10-12' THEN DATE '2026-10-12' ELSE month_end_date END AS arr_as_of_date,
        fiscal_year,
        fiscal_quarter
    FROM FISCAL_CALENDAR
    WHERE month_start_date >= DATE '2025-05-01' AND month_start_date <= DATE '2026-10-12'
) m
JOIN CONTRACTS c   ON c.start_date <= m.arr_as_of_date AND c.end_date > m.arr_as_of_date
JOIN CUSTOMERS cu  ON cu.customer_id = c.customer_id
JOIN PRODUCTS p    ON p.product_id = c.product_id
LEFT JOIN INSTALLED_SYSTEMS s ON s.system_id = c.system_id
LEFT JOIN PRODUCTS sp ON sp.product_id = s.product_id
GROUP BY m.arr_month, m.arr_as_of_date, m.fiscal_year, m.fiscal_quarter, cu.region, cu.segment, c.contract_type, COALESCE(sp.product_family, p.product_family);

CREATE OR REPLACE VIEW V_ARR_FINANCE_VS_SALESOPS
    COMMENT = 'Finance ARR versus the Sales Ops ARR figure, by month and region. Finance stops counting a contract the day it lapses. Sales Ops keeps counting a lapsed contract while its renewal opportunity is still open in Salesforce (renewals ops closes lost up to a year after the lapse). lapsed_open_arr is the difference; gap_pct = lapsed_open_arr / finance_arr. Use to explain why the two numbers differ; Finance ARR is the certified figure.'
AS
SELECT
    m.arr_month,
    m.arr_as_of_date,
    m.fiscal_year,
    m.fiscal_quarter,
    cu.region,
    SUM(CASE WHEN c.start_date <= m.arr_as_of_date AND c.end_date > m.arr_as_of_date THEN c.annual_value ELSE 0 END)        AS finance_arr,
    SUM(CASE WHEN c.end_date <= m.arr_as_of_date THEN c.annual_value ELSE 0 END)                                              AS lapsed_open_arr,
    SUM(CASE WHEN c.start_date <= m.arr_as_of_date AND c.end_date > m.arr_as_of_date THEN c.annual_value ELSE 0 END)
      + SUM(CASE WHEN c.end_date <= m.arr_as_of_date THEN c.annual_value ELSE 0 END)                                          AS salesops_arr,
    SUM(CASE WHEN c.end_date <= m.arr_as_of_date THEN 1 ELSE 0 END)                                                           AS lapsed_open_contracts,
    ROUND(SUM(CASE WHEN c.end_date <= m.arr_as_of_date THEN c.annual_value ELSE 0 END)
          / NULLIF(SUM(CASE WHEN c.start_date <= m.arr_as_of_date AND c.end_date > m.arr_as_of_date THEN c.annual_value ELSE 0 END), 0), 4) AS gap_pct
FROM (
    SELECT DISTINCT
        month_start_date                                                        AS arr_month,
        CASE WHEN month_end_date > DATE '2026-10-12' THEN DATE '2026-10-12' ELSE month_end_date END AS arr_as_of_date,
        fiscal_year,
        fiscal_quarter
    FROM FISCAL_CALENDAR
    WHERE month_start_date >= DATE '2025-05-01' AND month_start_date <= DATE '2026-10-12'
) m
JOIN CONTRACTS c
  ON (c.start_date <= m.arr_as_of_date AND c.end_date > m.arr_as_of_date)
  OR (c.end_date <= m.arr_as_of_date AND c.end_date > m.arr_as_of_date - 365
      AND (c.outcome_date IS NULL OR c.outcome_date > m.arr_as_of_date))
JOIN CUSTOMERS cu ON cu.customer_id = c.customer_id
GROUP BY m.arr_month, m.arr_as_of_date, m.fiscal_year, m.fiscal_quarter, cu.region;

CREATE OR REPLACE VIEW V_RENEWAL_PERFORMANCE
    COMMENT = 'Renewal performance for contracts whose end_date fell between 2025-05-01 and 2026-10-12, by fiscal year, fiscal quarter, region, segment, contract type and product family. renewal_rate = arr_renewed / arr_due (certified definition: a contract counts as renewed only when a successor contract is signed; pending renewals count as not yet renewed). To get a rate across slices divide SUM(arr_renewed) by SUM(arr_due); do not average renewal_rate.'
AS
SELECT
    f.fiscal_year,
    f.fiscal_quarter,
    cu.region,
    cu.segment,
    c.contract_type,
    COALESCE(sp.product_family, p.product_family)                              AS product_family,
    COUNT(*)                                                                    AS contracts_due,
    SUM(c.annual_value)                                                         AS arr_due,
    SUM(CASE WHEN c.contract_status = 'RENEWED' THEN c.annual_value ELSE 0 END)          AS arr_renewed,
    SUM(CASE WHEN c.contract_status = 'CHURNED' THEN c.annual_value ELSE 0 END)          AS arr_churned,
    SUM(CASE WHEN c.contract_status = 'PENDING_RENEWAL' THEN c.annual_value ELSE 0 END)  AS arr_pending,
    SUM(CASE WHEN c.contract_status = 'RENEWED' THEN 1 ELSE 0 END)              AS contracts_renewed,
    SUM(CASE WHEN c.contract_status = 'CHURNED' THEN 1 ELSE 0 END)              AS contracts_churned,
    SUM(CASE WHEN c.contract_status = 'PENDING_RENEWAL' THEN 1 ELSE 0 END)      AS contracts_pending,
    ROUND(SUM(CASE WHEN c.contract_status = 'RENEWED' THEN c.annual_value ELSE 0 END) / NULLIF(SUM(c.annual_value), 0), 4)  AS renewal_rate,
    ROUND(SUM(CASE WHEN c.contract_status = 'CHURNED' THEN c.annual_value ELSE 0 END) / NULLIF(SUM(c.annual_value), 0), 4)  AS churn_rate
FROM CONTRACTS c
JOIN FISCAL_CALENDAR f ON f.calendar_date = c.end_date
JOIN CUSTOMERS cu      ON cu.customer_id = c.customer_id
JOIN PRODUCTS p        ON p.product_id = c.product_id
LEFT JOIN INSTALLED_SYSTEMS s ON s.system_id = c.system_id
LEFT JOIN PRODUCTS sp  ON sp.product_id = s.product_id
WHERE c.end_date >= DATE '2025-05-01' AND c.end_date <= DATE '2026-10-12'
GROUP BY f.fiscal_year, f.fiscal_quarter, cu.region, cu.segment, c.contract_type, COALESCE(sp.product_family, p.product_family);

CREATE OR REPLACE VIEW V_RENEWALS_AT_RISK_90D
    COMMENT = 'One row per active contract ending in the next 90 days (2026-10-13 .. 2027-01-10) with the customer, region, partner, rep, product, annual value, the Salesforce opportunity stage and risk flag, whether the product reaches end of support within 12 months, and the customer open P1 case count. Filter risk_flag = AT_RISK for the at-risk list. Sum annual_value for ARR up for renewal.'
AS
SELECT
    c.contract_id,
    c.customer_id,
    cu.customer_name,
    cu.segment,
    cu.region,
    cu.industry,
    pt.partner_name,
    r.rep_name,
    c.contract_type,
    COALESCE(sp.product_family, p.product_family)                                  AS product_family,
    p.product_name,
    c.system_id,
    sp.product_name                                                                AS system_model,
    s.current_firmware,
    c.start_date,
    c.end_date,
    DATEDIFF('day', DATE '2026-10-12', c.end_date)                                 AS days_to_renewal,
    c.term_months,
    c.annual_value,
    o.opportunity_id,
    o.stage                                                                        AS opportunity_stage,
    o.quote_amount,
    o.risk_flag,
    o.risk_reason,
    o.competitor,
    COALESCE(sp.end_of_support_date, p.end_of_support_date)                        AS end_of_support_date,
    CASE WHEN COALESCE(sp.end_of_support_date, p.end_of_support_date) IS NOT NULL
          AND COALESCE(sp.end_of_support_date, p.end_of_support_date) <= c.end_date + 365 THEN 1 ELSE 0 END AS is_end_of_support_within_12m,
    COALESCE(k.open_p1_cases, 0)                                                   AS open_p1_cases,
    COALESCE(k.p1_cases_90d, 0)                                                    AS p1_cases_90d
FROM CONTRACTS c
JOIN CUSTOMERS cu   ON cu.customer_id = c.customer_id
JOIN PRODUCTS p     ON p.product_id = c.product_id
JOIN PARTNERS pt    ON pt.partner_id = c.partner_id
JOIN SALES_REPS r   ON r.rep_id = c.rep_id
LEFT JOIN INSTALLED_SYSTEMS s ON s.system_id = c.system_id
LEFT JOIN PRODUCTS sp ON sp.product_id = s.product_id
LEFT JOIN RENEWAL_OPPORTUNITIES o ON o.contract_id = c.contract_id
LEFT JOIN (
    SELECT customer_id,
           SUM(CASE WHEN case_status = 'OPEN' AND priority = 'P1' THEN 1 ELSE 0 END)                                   AS open_p1_cases,
           SUM(CASE WHEN priority = 'P1' AND opened_date >= DATE '2026-07-14' THEN 1 ELSE 0 END)                       AS p1_cases_90d
    FROM SUPPORT_CASES
    GROUP BY customer_id
) k ON k.customer_id = c.customer_id
WHERE c.contract_status = 'ACTIVE'
  AND c.end_date > DATE '2026-10-12'
  AND c.end_date <= DATE '2026-10-12' + 90;

CREATE OR REPLACE VIEW V_INSTALLED_BASE_HEALTH
    COMMENT = 'One row per active installed system as of 2026-10-12: customer, region, partner, model and family, age, capacity, current firmware, latest AutoPulse telemetry (September 2026), critical alerts in the last 3 months, end-of-support exposure, whether an active support contract covers it, and open P1 cases on the system. Use for end-of-support, firmware, health and support-coverage questions.'
AS
SELECT
    s.system_id,
    s.customer_id,
    cu.customer_name,
    cu.segment,
    cu.region,
    pt.partner_name,
    s.product_id,
    p.product_name,
    p.product_family,
    s.install_date,
    ROUND(DATEDIFF('day', s.install_date, DATE '2026-10-12') / 365.25, 1)             AS system_age_years,
    s.raw_capacity_tb,
    s.workload_type,
    s.current_firmware,
    t.capacity_used_pct                                                            AS latest_capacity_used_pct,
    t.health_score                                                                 AS latest_health_score,
    t.avg_latency_ms                                                               AS latest_avg_latency_ms,
    COALESCE(a.critical_alerts_3m, 0)                                              AS critical_alerts_3m,
    p.end_of_sale_date,
    p.end_of_support_date,
    CASE WHEN p.end_of_support_date IS NOT NULL AND p.end_of_support_date <= DATE '2027-10-12' THEN 1 ELSE 0 END AS is_end_of_support_within_12m,
    CASE WHEN sc.contract_id IS NOT NULL THEN 1 ELSE 0 END                         AS has_active_support,
    sc.end_date                                                                    AS support_end_date,
    sc.annual_value                                                                AS support_annual_value,
    COALESCE(k.open_p1_cases, 0)                                                   AS open_p1_cases,
    COALESCE(k.cases_90d, 0)                                                       AS cases_90d
FROM INSTALLED_SYSTEMS s
JOIN CUSTOMERS cu ON cu.customer_id = s.customer_id
JOIN PRODUCTS p   ON p.product_id = s.product_id
JOIN PARTNERS pt  ON pt.partner_id = s.partner_id
LEFT JOIN SYSTEM_TELEMETRY_MONTHLY t ON t.system_id = s.system_id AND t.snapshot_month = DATE '2026-09-01'
LEFT JOIN (
    SELECT system_id, SUM(critical_alerts) AS critical_alerts_3m
    FROM SYSTEM_TELEMETRY_MONTHLY
    WHERE snapshot_month >= DATE '2026-07-01'
    GROUP BY system_id
) a ON a.system_id = s.system_id
LEFT JOIN (
    SELECT system_id, MAX(contract_id) AS contract_id, MAX(end_date) AS end_date, MAX(annual_value) AS annual_value
    FROM CONTRACTS
    WHERE contract_type = 'SUPPORT' AND start_date <= DATE '2026-10-12' AND end_date > DATE '2026-10-12'
    GROUP BY system_id
) sc ON sc.system_id = s.system_id
LEFT JOIN (
    SELECT system_id,
           SUM(CASE WHEN case_status = 'OPEN' AND priority = 'P1' THEN 1 ELSE 0 END) AS open_p1_cases,
           SUM(CASE WHEN opened_date >= DATE '2026-07-14' THEN 1 ELSE 0 END)          AS cases_90d
    FROM SUPPORT_CASES
    WHERE system_id IS NOT NULL
    GROUP BY system_id
) k ON k.system_id = s.system_id
WHERE s.system_status = 'ACTIVE';

CREATE OR REPLACE VIEW V_CLOUD_COMMIT_UTILIZATION
    COMMENT = 'Cloud commit utilisation per customer and fiscal year (complete months only): committed versus consumed dollars, terabytes, overage and utilization_pct = consumed / commit. is_under_utilized = 1 when utilization is below 60 percent with at least 3 months of data. FY27 covers May-Sep 2026 so far.'
AS
SELECT
    cc.customer_id,
    cu.customer_name,
    cu.segment,
    cu.region,
    cu.industry,
    cc.product_id,
    p.product_name,
    cc.cloud_provider,
    f.fiscal_year,
    COUNT(*)                                                      AS months_reported,
    MIN(cc.usage_month)                                           AS first_month,
    MAX(cc.usage_month)                                           AS last_month,
    SUM(cc.monthly_commit_amount)                                 AS commit_amount,
    SUM(cc.consumed_amount)                                       AS consumed_amount,
    ROUND(AVG(cc.consumed_tb), 2)                                 AS avg_consumed_tb,
    SUM(cc.overage_amount)                                        AS overage_amount,
    ROUND(SUM(cc.consumed_amount) / NULLIF(SUM(cc.monthly_commit_amount), 0), 4)  AS utilization_pct,
    CASE WHEN COUNT(*) >= 3 AND SUM(cc.consumed_amount) / NULLIF(SUM(cc.monthly_commit_amount), 0) < 0.60 THEN 1 ELSE 0 END AS is_under_utilized
FROM CLOUD_CONSUMPTION_MONTHLY cc
JOIN CUSTOMERS cu       ON cu.customer_id = cc.customer_id
JOIN PRODUCTS p         ON p.product_id = cc.product_id
JOIN FISCAL_CALENDAR f  ON f.calendar_date = cc.usage_month
GROUP BY cc.customer_id, cu.customer_name, cu.segment, cu.region, cu.industry, cc.product_id, p.product_name, cc.cloud_provider, f.fiscal_year;

CREATE OR REPLACE VIEW V_SUPPORT_CASE_SUMMARY
    COMMENT = 'Support cases aggregated by opened month, region, segment, product family, priority, category and firmware version: case counts, open count, average resolution hours and average CSAT. Use for case volume and P1 trend questions; go to SUPPORT_CASES for case_notes text.'
AS
SELECT
    DATE_TRUNC('MONTH', sc.opened_date)                           AS opened_month,
    f.fiscal_year,
    f.fiscal_quarter,
    cu.region,
    cu.segment,
    p.product_family,
    sc.priority,
    sc.category,
    sc.firmware_version,
    COUNT(*)                                                      AS cases,
    SUM(CASE WHEN sc.case_status = 'OPEN' THEN 1 ELSE 0 END)      AS open_cases,
    SUM(CASE WHEN sc.priority = 'P1' THEN 1 ELSE 0 END)           AS p1_cases,
    ROUND(AVG(sc.resolution_hours), 1)                            AS avg_resolution_hours,
    ROUND(AVG(sc.csat_score), 2)                                  AS avg_csat,
    COUNT(DISTINCT sc.customer_id)                                AS customers_affected
FROM SUPPORT_CASES sc
JOIN CUSTOMERS cu      ON cu.customer_id = sc.customer_id
JOIN PRODUCTS p        ON p.product_id = sc.product_id
JOIN FISCAL_CALENDAR f ON f.calendar_date = sc.opened_date
GROUP BY DATE_TRUNC('MONTH', sc.opened_date), f.fiscal_year, f.fiscal_quarter, cu.region, cu.segment, p.product_family, sc.priority, sc.category, sc.firmware_version;

CREATE OR REPLACE VIEW V_PARTNER_ATTACH_RATE
    COMMENT = 'Support attach rate by partner and fiscal quarter for systems installed since 2024-05-01: systems installed, systems with a support contract starting within 60 days of install, attach_rate = attached / installed. To compare fiscal years divide SUM(systems_with_support) by SUM(systems_installed); do not average attach_rate.'
AS
SELECT
    s.partner_id,
    pt.partner_name,
    pt.partner_tier,
    pt.primary_region,
    f.fiscal_year,
    f.fiscal_quarter,
    COUNT(*)                                                      AS systems_installed,
    SUM(CASE WHEN a.system_id IS NOT NULL THEN 1 ELSE 0 END)      AS systems_with_support,
    ROUND(SUM(CASE WHEN a.system_id IS NOT NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 4) AS attach_rate
FROM INSTALLED_SYSTEMS s
JOIN PARTNERS pt       ON pt.partner_id = s.partner_id
JOIN FISCAL_CALENDAR f ON f.calendar_date = s.install_date
LEFT JOIN (
    SELECT DISTINCT c.system_id
    FROM CONTRACTS c
    JOIN INSTALLED_SYSTEMS i ON i.system_id = c.system_id
    WHERE c.contract_type = 'SUPPORT' AND c.start_date <= i.install_date + 60
) a ON a.system_id = s.system_id
WHERE s.install_date >= DATE '2024-05-01'
GROUP BY s.partner_id, pt.partner_name, pt.partner_tier, pt.primary_region, f.fiscal_year, f.fiscal_quarter;

-- ============================================================================
-- END OF SNOWFLAKE DDL  (read-only grants: `demo ddl keelstone --apply --grants`)
-- ============================================================================
