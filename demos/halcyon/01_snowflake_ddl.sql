-- ============================================================================
-- WisdomAI POC — Halcyon Specialty Distribution (HSD)
-- Snowflake DDL
-- Domain: US specialty pharmaceutical distribution. Manufacturer -> Halcyon DC
--   network -> health systems, oncology practices, infusion centers, specialty
--   and retail pharmacies. Order fulfillment, allocation, cold chain, inventory
--   expiry, chargebacks, returns and customer service cases.
-- Demo "today": 2026-09-25. Data spans 2025-01-01 .. 2026-09-25.
-- Source systems represented: ERP order management, WMS, cold chain telemetry,
--   manufacturer allocation portals, contract/chargeback system, CRM cases.
-- ============================================================================

-- SECTION 0: ENVIRONMENT SETUP -------------------------------------------------
USE ROLE SYSADMIN;
CREATE DATABASE IF NOT EXISTS HALCYON_POC
    COMMENT = 'WisdomAI POC database for Halcyon Specialty Distribution demo';
CREATE SCHEMA IF NOT EXISTS HALCYON_POC.SPECIALTY_OPS
    COMMENT = 'Specialty pharma distribution operations: orders, fulfillment, allocation, cold chain, inventory, chargebacks, service';
USE DATABASE HALCYON_POC;
USE SCHEMA SPECIALTY_OPS;

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

CREATE OR REPLACE TABLE CALENDAR (
    calendar_date        DATE         NOT NULL PRIMARY KEY  COMMENT 'Calendar day',
    week_start_date      DATE         NOT NULL              COMMENT 'Monday of the ISO week containing this date',
    month_start_date     DATE         NOT NULL              COMMENT 'First day of the calendar month',
    fiscal_quarter       VARCHAR(7)   NOT NULL              COMMENT 'Halcyon fiscal quarter label, fiscal year = calendar year (e.g. 2026-Q3)',
    day_of_week          VARCHAR(9)   NOT NULL              COMMENT 'Monday..Sunday',
    is_weekend           BOOLEAN      NOT NULL              COMMENT 'TRUE for Saturday and Sunday',
    is_us_holiday        BOOLEAN      NOT NULL              COMMENT 'TRUE on major US holidays when DCs do not ship',
    holiday_name         VARCHAR(40)                        COMMENT 'Holiday name when is_us_holiday is TRUE',
    is_complete_week     BOOLEAN      NOT NULL              COMMENT 'TRUE when the full ISO week is on or before the demo as-of date 2026-09-25. Use to exclude the partial current week from trends.'
) COMMENT = 'Date dimension 2025-01-01 .. 2026-12-31 with holiday and complete-week flags. Join on calendar_date.';

CREATE OR REPLACE TABLE DISTRIBUTION_CENTERS (
    dc_id                VARCHAR(10)  NOT NULL PRIMARY KEY  COMMENT 'Distribution center code (DC-MEM, DC-DAL, DC-ATL, DC-CHI, DC-PHX, DC-EWR)',
    dc_name              VARCHAR(80)  NOT NULL              COMMENT 'Distribution center display name',
    city                 VARCHAR(50)                        COMMENT 'City',
    state                VARCHAR(2)                         COMMENT 'US state code',
    region               VARCHAR(20)                        COMMENT 'Service region: SOUTH, CENTRAL, SOUTHEAST, MIDWEST, WEST, NORTHEAST',
    cold_chain_capable   BOOLEAN                            COMMENT 'TRUE if the DC has validated 2-8C and frozen storage zones',
    ultra_cold_capable   BOOLEAN                            COMMENT 'TRUE if the DC has -70C ultra-cold storage',
    daily_line_capacity  NUMBER(8,0)                        COMMENT 'Approximate order lines the DC can pick per day',
    latitude             NUMBER(9,6)                        COMMENT 'Latitude for map visualization',
    longitude            NUMBER(9,6)                        COMMENT 'Longitude for map visualization'
) COMMENT = 'Halcyon distribution center network. Six DCs; Memphis is the national specialty hub.';

CREATE OR REPLACE TABLE MANUFACTURERS (
    manufacturer_id      VARCHAR(10)  NOT NULL PRIMARY KEY  COMMENT 'Manufacturer code (e.g. MFR-001)',
    manufacturer_name    VARCHAR(80)  NOT NULL              COMMENT 'Fictional manufacturer name (e.g. Veltrix Biopharma, Keldon Pharma)',
    hq_country           VARCHAR(30)                        COMMENT 'Headquarters country',
    supplier_tier        VARCHAR(12)                        COMMENT 'STRATEGIC, PREFERRED, or STANDARD supplier relationship',
    runs_allocation_program BOOLEAN                         COMMENT 'TRUE if the manufacturer limits Halcyon supply via a monthly allocation',
    chargeback_terms_days NUMBER(3,0)                       COMMENT 'Contractual days for the manufacturer to settle a chargeback claim'
) COMMENT = 'Pharmaceutical manufacturers Halcyon buys from. Source: supplier master.';

CREATE OR REPLACE TABLE GPOS (
    gpo_id               VARCHAR(10)  NOT NULL PRIMARY KEY  COMMENT 'Group purchasing organization code (e.g. GPO-01)',
    gpo_name             VARCHAR(80)  NOT NULL              COMMENT 'Fictional GPO name',
    gpo_type             VARCHAR(20)                        COMMENT 'NATIONAL, REGIONAL, or SPECIALTY'
) COMMENT = 'Group purchasing organizations whose contracts set customer pricing. Chargebacks reconcile WAC vs contract price.';

CREATE OR REPLACE TABLE PRODUCTS (
    ndc                  VARCHAR(13)  NOT NULL PRIMARY KEY  COMMENT 'National Drug Code in 5-4-2 format (fictional)',
    product_name         VARCHAR(80)  NOT NULL              COMMENT 'Brand or product name (fictional, e.g. Vanterra, Oncaryl)',
    generic_name         VARCHAR(80)                        COMMENT 'Fictional molecule / generic name',
    manufacturer_id      VARCHAR(10)  NOT NULL REFERENCES MANUFACTURERS(manufacturer_id) COMMENT 'FK to MANUFACTURERS',
    therapeutic_class    VARCHAR(30)  NOT NULL              COMMENT 'ONCOLOGY, IMMUNOLOGY, GLP1_METABOLIC, RARE_DISEASE, HEMATOLOGY, NEUROLOGY, INFECTIOUS_DISEASE, VACCINES, OPHTHALMOLOGY',
    dosage_form          VARCHAR(30)                        COMMENT 'VIAL, PREFILLED_PEN, PREFILLED_SYRINGE, TABLET, INFUSION_BAG, KIT',
    storage_class        VARCHAR(20)  NOT NULL              COMMENT 'AMBIENT, REFRIGERATED_2_8C, FROZEN_MINUS20, ULTRA_COLD_MINUS70. Anything other than AMBIENT requires cold chain handling.',
    is_specialty         BOOLEAN                            COMMENT 'TRUE for specialty (high-cost, special handling) products',
    is_limited_distribution BOOLEAN                         COMMENT 'TRUE if the manufacturer restricts which distributors and customers may receive the product',
    is_allocated         BOOLEAN                            COMMENT 'TRUE if supply to Halcyon is capped by a manufacturer allocation program (see CUSTOMER_ALLOCATIONS)',
    brand_generic        VARCHAR(8)                         COMMENT 'BRAND or GENERIC',
    wac_unit_price       NUMBER(12,2)                       COMMENT 'Current Wholesale Acquisition Cost per sellable unit in USD',
    unit_of_sale         VARCHAR(20)                        COMMENT 'Sellable unit description (e.g. 1 vial, carton of 4 pens)',
    shelf_life_days      NUMBER(5,0)                        COMMENT 'Manufacturer shelf life from production in days',
    launch_date          DATE                               COMMENT 'Date Halcyon began distributing the product'
) COMMENT = 'Product master at NDC level. ~180 SKUs across nine therapeutic classes. Source: item master / compendia.';

CREATE OR REPLACE TABLE CUSTOMERS (
    customer_id          VARCHAR(12)  NOT NULL PRIMARY KEY  COMMENT 'Customer account identifier (e.g. CUST-0001)',
    customer_name        VARCHAR(100) NOT NULL              COMMENT 'Fictional customer organization name (e.g. Bayview Regional Health)',
    customer_type        VARCHAR(30)  NOT NULL              COMMENT 'HEALTH_SYSTEM, ACADEMIC_MEDICAL_CENTER, ONCOLOGY_PRACTICE, INFUSION_CENTER, SPECIALTY_PHARMACY, RETAIL_PHARMACY_CHAIN',
    customer_tier        VARCHAR(12)  NOT NULL              COMMENT 'STRATEGIC (top ~10 percent of revenue), KEY, or CORE',
    gpo_id               VARCHAR(10)           REFERENCES GPOS(gpo_id) COMMENT 'FK to GPOS. Determines contract pricing. NULL for customers buying at direct contract.',
    region               VARCHAR(20)                        COMMENT 'Service region matching DISTRIBUTION_CENTERS.region',
    hq_state             VARCHAR(2)                         COMMENT 'Headquarters state',
    hq_city              VARCHAR(50)                        COMMENT 'Headquarters city',
    primary_dc_id        VARCHAR(10)  NOT NULL REFERENCES DISTRIBUTION_CENTERS(dc_id) COMMENT 'FK to the DC that normally serves this customer',
    account_manager      VARCHAR(60)                        COMMENT 'Halcyon strategic account manager name (fictional)',
    onboarded_date       DATE                               COMMENT 'Date the customer first ordered from Halcyon',
    contract_start_date  DATE                               COMMENT 'Start of the current prime vendor / distribution agreement',
    contract_renewal_date DATE                              COMMENT 'Date the current distribution agreement renews. Drives renewal-risk questions.',
    annual_contract_value NUMBER(14,2)                      COMMENT 'Expected annual purchase value under the agreement in USD',
    payment_terms_days   NUMBER(3,0)                        COMMENT 'Net payment terms in days',
    is_active            BOOLEAN                            COMMENT 'FALSE if the customer has churned'
) COMMENT = 'Customer accounts (the organizations Halcyon sells to). 120 customers; Strategic tier drives most revenue. Source: CRM / ERP customer master.';

CREATE OR REPLACE TABLE CUSTOMER_SITES (
    site_id              VARCHAR(12)  NOT NULL PRIMARY KEY  COMMENT 'Ship-to site identifier (e.g. SITE-00001)',
    customer_id          VARCHAR(12)  NOT NULL REFERENCES CUSTOMERS(customer_id) COMMENT 'FK to parent CUSTOMERS',
    site_name            VARCHAR(120) NOT NULL              COMMENT 'Site display name (e.g. Bayview Regional Health - Main Campus Pharmacy)',
    site_type            VARCHAR(30)                        COMMENT 'HOSPITAL_PHARMACY, OUTPATIENT_INFUSION, CLINIC, RETAIL_STORE, CENTRAL_FILL, MAIL_ORDER',
    city                 VARCHAR(50)                        COMMENT 'City',
    state                VARCHAR(2)                         COMMENT 'US state code',
    serving_dc_id        VARCHAR(10)  NOT NULL REFERENCES DISTRIBUTION_CENTERS(dc_id) COMMENT 'FK to the DC that ships to this site',
    cold_chain_receiving BOOLEAN                            COMMENT 'TRUE if the site can receive 2-8C and frozen product',
    ordering_channel     VARCHAR(20)                        COMMENT 'Default ordering channel: EDI, PORTAL, PHONE, AUTO_REPLENISH',
    latitude             NUMBER(9,6)                        COMMENT 'Latitude for map visualization',
    longitude            NUMBER(9,6)                        COMMENT 'Longitude for map visualization'
) COMMENT = 'Ship-to locations under each customer. Health systems have many sites; practices have one to three. Source: ERP ship-to master.';

CREATE OR REPLACE TABLE CONTRACT_PRICES (
    contract_price_id    VARCHAR(16)  NOT NULL PRIMARY KEY  COMMENT 'Contract price row identifier (e.g. CP-000001)',
    gpo_id               VARCHAR(10)  NOT NULL REFERENCES GPOS(gpo_id) COMMENT 'FK to GPOS whose contract sets this price',
    ndc                  VARCHAR(13)  NOT NULL REFERENCES PRODUCTS(ndc) COMMENT 'FK to PRODUCTS',
    manufacturer_id      VARCHAR(10)  NOT NULL REFERENCES MANUFACTURERS(manufacturer_id) COMMENT 'FK to MANUFACTURERS (denormalized for chargeback questions)',
    contract_price       NUMBER(12,2) NOT NULL              COMMENT 'Contracted unit price the GPO member pays in USD',
    wac_at_contract      NUMBER(12,2)                       COMMENT 'WAC in effect when the contract price was set',
    effective_date       DATE         NOT NULL              COMMENT 'Contract price effective date',
    expiration_date      DATE                               COMMENT 'Contract price expiration date. NULL means open-ended.',
    price_file_version   VARCHAR(12)                        COMMENT 'Manufacturer price file version that loaded this row (e.g. 2026-04A). The Keldon 2026-04 file is the source of the dispute spike.'
) COMMENT = 'GPO contract prices by NDC. Chargeback amount = (WAC - contract price) x units for contract-priced sales.';

-- SECTION 3: FACT TABLES ------------------------------------------------------

CREATE OR REPLACE TABLE ORDERS (
    order_id             VARCHAR(16)  NOT NULL PRIMARY KEY  COMMENT 'Sales order identifier (e.g. ORD-00000001)',
    customer_id          VARCHAR(12)  NOT NULL REFERENCES CUSTOMERS(customer_id) COMMENT 'FK to CUSTOMERS',
    site_id              VARCHAR(12)  NOT NULL REFERENCES CUSTOMER_SITES(site_id) COMMENT 'FK to ship-to CUSTOMER_SITES',
    dc_id                VARCHAR(10)  NOT NULL REFERENCES DISTRIBUTION_CENTERS(dc_id) COMMENT 'FK to fulfilling DC',
    order_date           DATE         NOT NULL              COMMENT 'Date the order was received',
    order_channel        VARCHAR(20)                        COMMENT 'EDI, PORTAL, PHONE, AUTO_REPLENISH',
    order_priority       VARCHAR(10)                        COMMENT 'STANDARD (next day), URGENT (same day cut-off), STAT (courier)',
    requested_delivery_date DATE                            COMMENT 'Customer requested delivery date',
    order_status         VARCHAR(16)                        COMMENT 'COMPLETE, PARTIAL, OPEN, CANCELLED',
    line_count           NUMBER(5,0)                        COMMENT 'Number of order lines',
    order_value_wac      NUMBER(14,2)                       COMMENT 'Sum of ordered quantity x WAC across lines in USD'
) COMMENT = 'Sales order headers. ~60K orders. Source: ERP order management.';

CREATE OR REPLACE TABLE ORDER_LINES (
    order_line_id        VARCHAR(20)  NOT NULL PRIMARY KEY  COMMENT 'Order line identifier (e.g. OL-000000001)',
    order_id             VARCHAR(16)  NOT NULL REFERENCES ORDERS(order_id) COMMENT 'FK to ORDERS',
    customer_id          VARCHAR(12)  NOT NULL REFERENCES CUSTOMERS(customer_id) COMMENT 'Denormalized FK to CUSTOMERS',
    site_id              VARCHAR(12)  NOT NULL REFERENCES CUSTOMER_SITES(site_id) COMMENT 'Denormalized FK to CUSTOMER_SITES',
    dc_id                VARCHAR(10)  NOT NULL REFERENCES DISTRIBUTION_CENTERS(dc_id) COMMENT 'Denormalized FK to DISTRIBUTION_CENTERS',
    ndc                  VARCHAR(13)  NOT NULL REFERENCES PRODUCTS(ndc) COMMENT 'FK to PRODUCTS',
    order_date           DATE         NOT NULL              COMMENT 'Denormalized order date for single-table time filtering',
    qty_ordered          NUMBER(8,0)  NOT NULL              COMMENT 'Units ordered',
    qty_shipped          NUMBER(8,0)  NOT NULL              COMMENT 'Units shipped from the first release. Line fill compares this to qty_ordered.',
    qty_backordered      NUMBER(8,0)  NOT NULL              COMMENT 'Units placed on backorder at first release',
    qty_cancelled        NUMBER(8,0)  NOT NULL              COMMENT 'Units cancelled by the customer or Halcyon',
    unit_price           NUMBER(12,2)                       COMMENT 'Price charged to the customer per unit (contract price when a GPO contract applies, else WAC)',
    wac_at_order         NUMBER(12,2)                       COMMENT 'WAC per unit on the order date',
    is_contract_priced   BOOLEAN                            COMMENT 'TRUE when a GPO contract price applied (generates a chargeback)',
    line_status          VARCHAR(14)                        COMMENT 'FILLED (shipped complete), PARTIAL, BACKORDERED (nothing shipped), CANCELLED',
    short_reason_code    VARCHAR(20)                        COMMENT 'Reason units were not shipped: ALLOCATION_LIMIT, STOCKOUT, MFR_SHORTAGE, QUALITY_HOLD, CREDIT_HOLD, SHORT_DATED_REJECT. NULL when filled complete.',
    promised_ship_date   DATE                               COMMENT 'Date Halcyon committed to ship',
    actual_ship_date     DATE                               COMMENT 'Date the first release shipped. NULL if nothing shipped.'
) COMMENT = 'Order lines, one per NDC per order. ~200K rows. The primary grain for fill rate, backorder, and revenue questions.';

CREATE OR REPLACE TABLE SHIPMENTS (
    shipment_id          VARCHAR(16)  NOT NULL PRIMARY KEY  COMMENT 'Shipment identifier (e.g. SHP-00000001)',
    order_id             VARCHAR(16)  NOT NULL REFERENCES ORDERS(order_id) COMMENT 'FK to ORDERS (one shipment per order in this build)',
    customer_id          VARCHAR(12)  NOT NULL REFERENCES CUSTOMERS(customer_id) COMMENT 'Denormalized FK to CUSTOMERS',
    site_id              VARCHAR(12)  NOT NULL REFERENCES CUSTOMER_SITES(site_id) COMMENT 'Denormalized FK to CUSTOMER_SITES',
    dc_id                VARCHAR(10)  NOT NULL REFERENCES DISTRIBUTION_CENTERS(dc_id) COMMENT 'FK to shipping DC',
    carrier              VARCHAR(20)                        COMMENT 'HALCYON_FLEET, UPS, FEDEX, COURIER',
    service_level        VARCHAR(20)                        COMMENT 'NEXT_DAY, SAME_DAY, GROUND, STAT_COURIER',
    ship_date            DATE                               COMMENT 'Date the shipment left the DC',
    promised_delivery_date DATE                             COMMENT 'Delivery date promised to the customer',
    actual_delivery_date DATE                               COMMENT 'Actual delivery date. NULL if not yet delivered.',
    delivery_status      VARCHAR(14)                        COMMENT 'DELIVERED, IN_TRANSIT, DELAYED, EXCEPTION, RETURNED',
    cold_chain_required  BOOLEAN                            COMMENT 'TRUE if any line required 2-8C or colder handling',
    packaging_type       VARCHAR(20)                        COMMENT 'AMBIENT_BOX, GEL_PACK_STD, PHASE_CHANGE_48H, DRY_ICE, LN2_DEWAR. GEL_PACK_STD is the lower-cost refrigerated option.',
    total_units          NUMBER(8,0)                        COMMENT 'Units in the shipment',
    shipment_value_wac   NUMBER(14,2)                       COMMENT 'WAC value of the shipment in USD'
) COMMENT = 'Outbound shipments from DC to site. ~58K rows. Source: WMS / carrier tracking.';

CREATE OR REPLACE TABLE COLD_CHAIN_EVENTS (
    event_id             VARCHAR(16)  NOT NULL PRIMARY KEY  COMMENT 'Temperature event identifier (e.g. CCE-00000001)',
    shipment_id          VARCHAR(16)  NOT NULL REFERENCES SHIPMENTS(shipment_id) COMMENT 'FK to SHIPMENTS',
    dc_id                VARCHAR(10)  NOT NULL REFERENCES DISTRIBUTION_CENTERS(dc_id) COMMENT 'FK to originating DC',
    customer_id          VARCHAR(12)  NOT NULL REFERENCES CUSTOMERS(customer_id) COMMENT 'Denormalized FK to CUSTOMERS',
    event_timestamp      TIMESTAMP_NTZ                      COMMENT 'Time the monitoring reading was logged',
    event_date           DATE         NOT NULL              COMMENT 'Date of the reading',
    stage                VARCHAR(14)  NOT NULL              COMMENT 'DC_STORAGE, PACKOUT, IN_TRANSIT, DELIVERY',
    storage_class        VARCHAR(20)                        COMMENT 'Required storage class of the monitored product',
    packaging_type       VARCHAR(20)                        COMMENT 'Packaging on the shipment at the time of the reading',
    temp_reading_c       NUMBER(5,1)                        COMMENT 'Temperature reading in Celsius',
    is_excursion         BOOLEAN      NOT NULL              COMMENT 'TRUE if the reading was outside the allowed range',
    excursion_minutes    NUMBER(6,0)                        COMMENT 'Minutes outside range. NULL when not an excursion.',
    excursion_severity   VARCHAR(8)                         COMMENT 'MINOR (< 30 min), MAJOR (30-120 min), CRITICAL (> 120 min or > 15C). NULL when not an excursion.',
    disposition          VARCHAR(14)                        COMMENT 'Outcome for excursions: RELEASED, QUARANTINED, DESTROYED, RETURNED. NULL when not an excursion.',
    units_affected       NUMBER(8,0)                        COMMENT 'Units affected by the excursion',
    value_affected_wac   NUMBER(14,2)                       COMMENT 'WAC value of affected units in USD'
) COMMENT = 'Cold chain monitoring events. One row per monitored reading; only a small share are excursions. Source: temperature loggers and WMS.';

CREATE OR REPLACE TABLE BACKORDERS (
    backorder_id         VARCHAR(16)  NOT NULL PRIMARY KEY  COMMENT 'Backorder identifier (e.g. BO-00000001)',
    order_line_id        VARCHAR(20)  NOT NULL REFERENCES ORDER_LINES(order_line_id) COMMENT 'FK to the ORDER_LINES row that was short',
    customer_id          VARCHAR(12)  NOT NULL REFERENCES CUSTOMERS(customer_id) COMMENT 'Denormalized FK to CUSTOMERS',
    site_id              VARCHAR(12)  NOT NULL REFERENCES CUSTOMER_SITES(site_id) COMMENT 'Denormalized FK to CUSTOMER_SITES',
    dc_id                VARCHAR(10)  NOT NULL REFERENCES DISTRIBUTION_CENTERS(dc_id) COMMENT 'Denormalized FK to DISTRIBUTION_CENTERS',
    ndc                  VARCHAR(13)  NOT NULL REFERENCES PRODUCTS(ndc) COMMENT 'FK to PRODUCTS',
    backorder_date       DATE         NOT NULL              COMMENT 'Date the backorder was created',
    qty_backordered      NUMBER(8,0)  NOT NULL              COMMENT 'Units on backorder',
    reason_code          VARCHAR(20)                        COMMENT 'ALLOCATION_LIMIT, STOCKOUT, MFR_SHORTAGE, QUALITY_HOLD',
    expected_release_date DATE                              COMMENT 'Date Halcyon expects to release the backorder',
    released_date        DATE                               COMMENT 'Date the backorder shipped. NULL while open.',
    status               VARCHAR(10)  NOT NULL              COMMENT 'OPEN, RELEASED, CANCELLED',
    days_open            NUMBER(5,0)                        COMMENT 'Days from backorder_date to released_date, or to the as-of date 2026-09-25 while open',
    backorder_value_wac  NUMBER(14,2)                       COMMENT 'WAC value of backordered units in USD'
) COMMENT = 'Backorder ledger. ~9K rows. Aging over 14 days is the operational threshold that drives escalation.';

CREATE OR REPLACE TABLE INVENTORY_SNAPSHOTS (
    snapshot_id          VARCHAR(20)  NOT NULL PRIMARY KEY  COMMENT 'Snapshot row identifier',
    snapshot_date        DATE         NOT NULL              COMMENT 'Monday snapshot date (weekly)',
    dc_id                VARCHAR(10)  NOT NULL REFERENCES DISTRIBUTION_CENTERS(dc_id) COMMENT 'FK to DISTRIBUTION_CENTERS',
    ndc                  VARCHAR(13)  NOT NULL REFERENCES PRODUCTS(ndc) COMMENT 'FK to PRODUCTS',
    on_hand_units        NUMBER(9,0)                        COMMENT 'Total units physically on hand',
    allocated_units      NUMBER(9,0)                        COMMENT 'Units reserved against open orders',
    available_units      NUMBER(9,0)                        COMMENT 'on_hand_units minus allocated_units',
    on_order_units       NUMBER(9,0)                        COMMENT 'Units on open purchase orders from the manufacturer',
    avg_weekly_demand_units NUMBER(9,1)                     COMMENT 'Trailing 8-week average weekly demand at this DC',
    days_of_supply       NUMBER(6,1)                        COMMENT 'available_units / (avg_weekly_demand_units / 7). NULL when there is no demand.',
    expiring_30d_units   NUMBER(9,0)                        COMMENT 'Units expiring within 30 days of the snapshot',
    expiring_90d_units   NUMBER(9,0)                        COMMENT 'Units expiring within 90 days of the snapshot',
    inventory_value_wac  NUMBER(14,2)                       COMMENT 'on_hand_units x WAC in USD',
    expiring_90d_value_wac NUMBER(14,2)                     COMMENT 'expiring_90d_units x WAC in USD',
    reorder_point_units  NUMBER(9,0)                        COMMENT 'Reorder trigger for this DC and NDC'
) COMMENT = 'Weekly inventory position by DC and NDC. ~90K rows. Use the latest snapshot_date for current position questions.';

CREATE OR REPLACE TABLE CUSTOMER_ALLOCATIONS (
    allocation_id        VARCHAR(20)  NOT NULL PRIMARY KEY  COMMENT 'Allocation row identifier',
    period_month         DATE         NOT NULL              COMMENT 'First day of the allocation month',
    ndc                  VARCHAR(13)  NOT NULL REFERENCES PRODUCTS(ndc) COMMENT 'FK to PRODUCTS (allocated products only)',
    manufacturer_id      VARCHAR(10)  NOT NULL REFERENCES MANUFACTURERS(manufacturer_id) COMMENT 'FK to MANUFACTURERS',
    customer_id          VARCHAR(12)  NOT NULL REFERENCES CUSTOMERS(customer_id) COMMENT 'FK to CUSTOMERS',
    halcyon_total_allocation_units NUMBER(9,0)              COMMENT 'Units the manufacturer allocated to Halcyon for the month (same value on every customer row for the NDC and month)',
    allocation_basis     VARCHAR(20)                        COMMENT 'HISTORICAL_SHARE (default), FAIR_SHARE, CONTRACT_MINIMUM',
    customer_allocated_units NUMBER(9,0)                    COMMENT 'Units Halcyon allocated to this customer for the month',
    customer_requested_units NUMBER(9,0)                    COMMENT 'Units the customer ordered or requested in the month',
    customer_consumed_units NUMBER(9,0)                     COMMENT 'Units actually shipped to the customer in the month',
    utilization_pct      NUMBER(6,2)                        COMMENT 'customer_consumed_units / customer_allocated_units x 100',
    shortfall_units      NUMBER(9,0)                        COMMENT 'GREATEST(customer_requested_units - customer_allocated_units, 0)'
) COMMENT = 'Monthly allocation of constrained products to customers. The Vanterra allocation cut in June 2026 is visible in halcyon_total_allocation_units.';

CREATE OR REPLACE TABLE RETURNS (
    return_id            VARCHAR(16)  NOT NULL PRIMARY KEY  COMMENT 'Return identifier (e.g. RET-00000001)',
    order_line_id        VARCHAR(20)  NOT NULL REFERENCES ORDER_LINES(order_line_id) COMMENT 'FK to the original ORDER_LINES row',
    customer_id          VARCHAR(12)  NOT NULL REFERENCES CUSTOMERS(customer_id) COMMENT 'Denormalized FK to CUSTOMERS',
    dc_id                VARCHAR(10)  NOT NULL REFERENCES DISTRIBUTION_CENTERS(dc_id) COMMENT 'Denormalized FK to the shipping DC',
    ndc                  VARCHAR(13)  NOT NULL REFERENCES PRODUCTS(ndc) COMMENT 'FK to PRODUCTS',
    return_date          DATE         NOT NULL              COMMENT 'Date the return was authorized',
    qty_returned         NUMBER(8,0)  NOT NULL              COMMENT 'Units returned',
    return_reason        VARCHAR(20)                        COMMENT 'DAMAGED, TEMP_EXCURSION, SHORT_DATED, WRONG_ITEM, OVERSTOCK, RECALL',
    disposition          VARCHAR(14)                        COMMENT 'RESTOCK, DESTROY, RETURN_TO_MFR',
    credit_amount        NUMBER(14,2)                       COMMENT 'Credit issued to the customer in USD',
    is_saleable          BOOLEAN                            COMMENT 'TRUE if the returned product can be resold'
) COMMENT = 'Customer returns. ~4K rows. TEMP_EXCURSION and SHORT_DATED returns are quality signals.';

CREATE OR REPLACE TABLE CHARGEBACKS (
    chargeback_id        VARCHAR(16)  NOT NULL PRIMARY KEY  COMMENT 'Chargeback claim identifier (e.g. CB-00000001)',
    order_line_id        VARCHAR(20)  NOT NULL REFERENCES ORDER_LINES(order_line_id) COMMENT 'FK to the contract-priced ORDER_LINES row',
    manufacturer_id      VARCHAR(10)  NOT NULL REFERENCES MANUFACTURERS(manufacturer_id) COMMENT 'FK to the MANUFACTURERS that owes the chargeback',
    ndc                  VARCHAR(13)  NOT NULL REFERENCES PRODUCTS(ndc) COMMENT 'FK to PRODUCTS',
    customer_id          VARCHAR(12)  NOT NULL REFERENCES CUSTOMERS(customer_id) COMMENT 'FK to CUSTOMERS',
    gpo_id               VARCHAR(10)           REFERENCES GPOS(gpo_id) COMMENT 'FK to GPOS contract used',
    submitted_date       DATE         NOT NULL              COMMENT 'Date the claim was submitted to the manufacturer',
    settled_date         DATE                               COMMENT 'Date the claim was paid or rejected. NULL while open.',
    units                NUMBER(8,0)                        COMMENT 'Units claimed',
    wac_amount           NUMBER(14,2)                       COMMENT 'units x WAC in USD',
    contract_amount      NUMBER(14,2)                       COMMENT 'units x contract price in USD',
    chargeback_amount    NUMBER(14,2)                       COMMENT 'wac_amount minus contract_amount in USD. What the manufacturer owes Halcyon.',
    status               VARCHAR(10)  NOT NULL              COMMENT 'SUBMITTED, APPROVED, PAID, DISPUTED, REJECTED',
    dispute_reason       VARCHAR(24)                        COMMENT 'PRICE_MISMATCH, INELIGIBLE_CUSTOMER, EXPIRED_CONTRACT, DUPLICATE_CLAIM, MISSING_DEA. NULL unless DISPUTED or REJECTED.',
    price_file_version   VARCHAR(12)                        COMMENT 'Manufacturer price file version the claim priced against'
) COMMENT = 'Chargeback claims to manufacturers for contract-priced sales. ~40K rows. Disputed and rejected claims are margin at risk.';

CREATE OR REPLACE TABLE SERVICE_CASES (
    case_id              VARCHAR(16)  NOT NULL PRIMARY KEY  COMMENT 'Service case identifier (e.g. CASE-00000001)',
    customer_id          VARCHAR(12)  NOT NULL REFERENCES CUSTOMERS(customer_id) COMMENT 'FK to CUSTOMERS',
    site_id              VARCHAR(12)           REFERENCES CUSTOMER_SITES(site_id) COMMENT 'FK to CUSTOMER_SITES when the case concerns a site',
    dc_id                VARCHAR(10)           REFERENCES DISTRIBUTION_CENTERS(dc_id) COMMENT 'FK to the DC involved',
    related_backorder_id VARCHAR(16)           REFERENCES BACKORDERS(backorder_id) COMMENT 'FK to BACKORDERS when the case was raised about a backorder',
    related_shipment_id  VARCHAR(16)           REFERENCES SHIPMENTS(shipment_id) COMMENT 'FK to SHIPMENTS when the case concerns a delivery',
    opened_date          DATE         NOT NULL              COMMENT 'Date the case was opened',
    closed_date          DATE                               COMMENT 'Date the case was closed. NULL while open.',
    case_type            VARCHAR(24)  NOT NULL              COMMENT 'PRODUCT_AVAILABILITY, DELIVERY_DELAY, SHORT_SHIP, TEMP_EXCURSION, DAMAGED_PRODUCT, BILLING_DISPUTE, ORDER_ERROR',
    severity             VARCHAR(8)   NOT NULL              COMMENT 'LOW, MEDIUM, HIGH, CRITICAL',
    status               VARCHAR(12)  NOT NULL              COMMENT 'OPEN, IN_PROGRESS, CLOSED',
    sla_hours            NUMBER(5,0)                        COMMENT 'Resolution SLA in hours for the severity',
    resolution_hours     NUMBER(7,1)                        COMMENT 'Hours to close. NULL while open.',
    sla_met              BOOLEAN                            COMMENT 'TRUE if resolution_hours <= sla_hours. NULL while open.',
    escalated_to_exec    BOOLEAN                            COMMENT 'TRUE if the customer escalated to Halcyon leadership',
    case_summary         VARCHAR(300)                       COMMENT 'Short plain-language summary of the issue'
) COMMENT = 'Customer service cases from CRM. ~3K rows. HIGH and CRITICAL severity with exec escalation are retention signals.';

CREATE OR REPLACE TABLE DATA_DICTIONARY (
    table_name           VARCHAR(60)  NOT NULL              COMMENT 'Table or view name',
    column_name          VARCHAR(60)  NOT NULL              COMMENT 'Column or metric name',
    data_type            VARCHAR(30)                        COMMENT 'Snowflake data type',
    description          VARCHAR(500)                       COMMENT 'Business description',
    sample_value         VARCHAR(100)                       COMMENT 'Example value',
    metric_formula       VARCHAR(500)                       COMMENT 'Formula for derived metrics'
) COMMENT = 'Self-describing metadata WisdomAI can use as a fallback during context discovery.';

-- SECTION 4: ANALYTICAL VIEWS -------------------------------------------------
-- Demo as-of date is 2026-09-25 and is hardcoded where a "today" is needed so the
-- demo is stable regardless of when it is run.

CREATE OR REPLACE VIEW V_ORDER_LINE_DETAIL
    COMMENT = 'Order lines enriched with customer, site, DC, product, manufacturer and derived fill metrics. Use for any fill rate, revenue, or short-ship question at line grain.'
AS
SELECT
    ol.order_line_id,
    ol.order_id,
    ol.order_date,
    DATE_TRUNC('MONTH', ol.order_date)               AS order_month,
    o.order_channel,
    o.order_priority,
    ol.customer_id,
    c.customer_name,
    c.customer_type,
    c.customer_tier,
    c.region                                          AS customer_region,
    c.contract_renewal_date,
    c.annual_contract_value,
    ol.site_id,
    s.site_name,
    ol.dc_id,
    d.dc_name,
    ol.ndc,
    p.product_name,
    p.generic_name,
    p.therapeutic_class,
    p.storage_class,
    p.is_allocated,
    p.manufacturer_id,
    m.manufacturer_name,
    ol.qty_ordered,
    ol.qty_shipped,
    ol.qty_backordered,
    ol.qty_cancelled,
    ol.unit_price,
    ol.wac_at_order,
    ol.is_contract_priced,
    ol.line_status,
    ol.short_reason_code,
    ol.promised_ship_date,
    ol.actual_ship_date,
    CASE WHEN ol.qty_shipped >= ol.qty_ordered THEN 1 ELSE 0 END          AS is_line_filled_complete,
    ol.qty_shipped * ol.unit_price                                         AS shipped_revenue,
    ol.qty_ordered * ol.wac_at_order                                       AS ordered_value_wac,
    ol.qty_backordered * ol.wac_at_order                                   AS backordered_value_wac,
    CASE WHEN ol.actual_ship_date IS NOT NULL AND ol.actual_ship_date <= ol.promised_ship_date THEN 1 ELSE 0 END AS is_shipped_on_time
FROM ORDER_LINES ol
JOIN ORDERS o                ON o.order_id = ol.order_id
JOIN CUSTOMERS c             ON c.customer_id = ol.customer_id
JOIN CUSTOMER_SITES s        ON s.site_id = ol.site_id
JOIN DISTRIBUTION_CENTERS d  ON d.dc_id = ol.dc_id
JOIN PRODUCTS p              ON p.ndc = ol.ndc
JOIN MANUFACTURERS m         ON m.manufacturer_id = p.manufacturer_id;

CREATE OR REPLACE VIEW V_FILL_RATE_CUSTOMER_MONTH
    COMMENT = 'Monthly service levels by customer and therapeutic class: line fill rate, unit fill rate, backorder rate, on-time ship rate, shipped revenue. Pre-aggregated; safe to sum units and revenue, average the rates with care.'
AS
SELECT
    customer_id,
    customer_name,
    customer_tier,
    customer_type,
    therapeutic_class,
    order_month,
    COUNT(*)                                                              AS line_count,
    SUM(is_line_filled_complete)                                          AS lines_filled_complete,
    ROUND(SUM(is_line_filled_complete) / NULLIF(COUNT(*), 0), 4)          AS line_fill_rate,
    SUM(qty_ordered)                                                      AS units_ordered,
    SUM(qty_shipped)                                                      AS units_shipped,
    SUM(qty_backordered)                                                  AS units_backordered,
    ROUND(SUM(qty_shipped) / NULLIF(SUM(qty_ordered), 0), 4)              AS unit_fill_rate,
    ROUND(SUM(qty_backordered) / NULLIF(SUM(qty_ordered), 0), 4)          AS backorder_rate,
    ROUND(SUM(is_shipped_on_time) / NULLIF(SUM(CASE WHEN actual_ship_date IS NOT NULL THEN 1 ELSE 0 END), 0), 4) AS on_time_ship_rate,
    SUM(shipped_revenue)                                                  AS shipped_revenue,
    SUM(ordered_value_wac)                                                AS ordered_value_wac
FROM V_ORDER_LINE_DETAIL
WHERE line_status <> 'CANCELLED'
GROUP BY customer_id, customer_name, customer_tier, customer_type, therapeutic_class, order_month;

CREATE OR REPLACE VIEW V_CUSTOMER_HEALTH
    COMMENT = 'One row per active customer as of 2026-09-25 with the operational risk indicators used by the Customer Supply Rescue workbench: recent (2026-07-27 to 2026-09-20) vs prior (2026-06-01 to 2026-07-26) 8-week line fill rate, discretionary (non-allocated product) order value change, open backorders and their age, open high severity cases, exec escalations, cold chain excursions, allocation shortfall, days to renewal, and a transparent 0-100 operational risk score (35 fill rate deterioration, 25 backorder aging, 25 service cases, 15 discretionary volume decline). Risk indicators support triage; they are not churn predictions.'
AS
WITH recent AS (
    SELECT customer_id,
           COUNT(*)                                            AS recent_lines,
           SUM(is_line_filled_complete)                        AS recent_filled,
           SUM(CASE WHEN is_allocated = FALSE THEN ordered_value_wac ELSE 0 END) AS recent_ordered_value_wac
    FROM V_ORDER_LINE_DETAIL
    WHERE order_date >= DATE '2026-07-27' AND order_date < DATE '2026-09-21'
      AND line_status <> 'CANCELLED'
    GROUP BY customer_id
), prior AS (
    SELECT customer_id,
           COUNT(*)                                            AS prior_lines,
           SUM(is_line_filled_complete)                        AS prior_filled,
           SUM(CASE WHEN is_allocated = FALSE THEN ordered_value_wac ELSE 0 END) AS prior_ordered_value_wac
    FROM V_ORDER_LINE_DETAIL
    WHERE order_date >= DATE '2026-06-01' AND order_date < DATE '2026-07-27'
      AND line_status <> 'CANCELLED'
    GROUP BY customer_id
), bo AS (
    SELECT customer_id,
           COUNT(*)                                            AS open_backorders,
           SUM(CASE WHEN days_open > 14 THEN 1 ELSE 0 END)     AS open_backorders_over_14d,
           MAX(days_open)                                      AS oldest_backorder_days,
           SUM(backorder_value_wac)                            AS open_backorder_value_wac
    FROM BACKORDERS
    WHERE status = 'OPEN'
    GROUP BY customer_id
), cases AS (
    SELECT customer_id,
           SUM(CASE WHEN status <> 'CLOSED' THEN 1 ELSE 0 END)                                                    AS open_cases,
           SUM(CASE WHEN status <> 'CLOSED' AND severity IN ('HIGH','CRITICAL') THEN 1 ELSE 0 END)                AS open_high_severity_cases,
           SUM(CASE WHEN escalated_to_exec AND opened_date >= DATE '2026-06-27' THEN 1 ELSE 0 END)                AS exec_escalations_90d
    FROM SERVICE_CASES
    GROUP BY customer_id
), cce AS (
    SELECT customer_id,
           SUM(CASE WHEN is_excursion THEN 1 ELSE 0 END)                                              AS excursions_90d,
           SUM(CASE WHEN is_excursion AND excursion_severity IN ('MAJOR','CRITICAL') THEN 1 ELSE 0 END) AS major_excursions_90d
    FROM COLD_CHAIN_EVENTS
    WHERE event_date >= DATE '2026-06-27'
    GROUP BY customer_id
), alloc AS (
    SELECT customer_id,
           SUM(shortfall_units)                                                          AS allocation_shortfall_units_90d,
           ROUND(AVG(utilization_pct), 1)                                                AS avg_allocation_utilization_pct_90d
    FROM CUSTOMER_ALLOCATIONS
    WHERE period_month >= DATE '2026-07-01'
    GROUP BY customer_id
), base AS (
    SELECT
        c.customer_id,
        c.customer_name,
        c.customer_type,
        c.customer_tier,
        c.region,
        c.primary_dc_id,
        c.account_manager,
        c.annual_contract_value,
        c.contract_renewal_date,
        DATEDIFF('day', DATE '2026-09-25', c.contract_renewal_date)                                     AS days_to_renewal,
        ROUND(r.recent_filled / NULLIF(r.recent_lines, 0), 4)                                            AS recent_line_fill_rate,
        ROUND(p.prior_filled / NULLIF(p.prior_lines, 0), 4)                                              AS prior_line_fill_rate,
        ROUND(r.recent_filled / NULLIF(r.recent_lines, 0) - p.prior_filled / NULLIF(p.prior_lines, 0), 4) AS fill_rate_change,
        r.recent_ordered_value_wac                                                                        AS recent_discretionary_value_wac,
        p.prior_ordered_value_wac                                                                         AS prior_discretionary_value_wac,
        ROUND((r.recent_ordered_value_wac - p.prior_ordered_value_wac) / NULLIF(p.prior_ordered_value_wac, 0), 4) AS discretionary_value_change_pct,
        COALESCE(bo.open_backorders, 0)                AS open_backorders,
        COALESCE(bo.open_backorders_over_14d, 0)       AS open_backorders_over_14d,
        COALESCE(bo.oldest_backorder_days, 0)          AS oldest_backorder_days,
        COALESCE(bo.open_backorder_value_wac, 0)       AS open_backorder_value_wac,
        COALESCE(cs.open_cases, 0)                     AS open_cases,
        COALESCE(cs.open_high_severity_cases, 0)       AS open_high_severity_cases,
        COALESCE(cs.exec_escalations_90d, 0)           AS exec_escalations_90d,
        COALESCE(ce.excursions_90d, 0)                 AS excursions_90d,
        COALESCE(ce.major_excursions_90d, 0)           AS major_excursions_90d,
        COALESCE(al.allocation_shortfall_units_90d, 0) AS allocation_shortfall_units_90d,
        al.avg_allocation_utilization_pct_90d
    FROM CUSTOMERS c
    LEFT JOIN recent r ON r.customer_id = c.customer_id
    LEFT JOIN prior  p ON p.customer_id = c.customer_id
    LEFT JOIN bo       ON bo.customer_id = c.customer_id
    LEFT JOIN cases cs ON cs.customer_id = c.customer_id
    LEFT JOIN cce   ce ON ce.customer_id = c.customer_id
    LEFT JOIN alloc al ON al.customer_id = c.customer_id
    WHERE c.is_active = TRUE
)
SELECT
    base.*,
    -- Transparent risk score: 35 fill rate deterioration, 25 backorder aging, 25 service cases, 15 volume decline. Capped 0..100.
    ROUND(
        LEAST(35, GREATEST(0, -fill_rate_change) * 175)
      + LEAST(25, open_backorders_over_14d * 5)
      + LEAST(25, open_high_severity_cases * 8 + exec_escalations_90d * 5)
      + LEAST(15, GREATEST(0, -discretionary_value_change_pct) * 75)
    , 1)                                                                      AS operational_risk_score,
    CASE
        WHEN fill_rate_change <= -0.10 THEN 'Fill rate down ' || CAST(CAST(ROUND(-fill_rate_change * 100, 0) AS INTEGER) AS VARCHAR) || ' pts'
        WHEN open_backorders_over_14d >= 3 THEN CAST(open_backorders_over_14d AS VARCHAR) || ' backorders over 14 days'
        WHEN open_high_severity_cases >= 2 THEN CAST(open_high_severity_cases AS VARCHAR) || ' open high severity cases'
        WHEN discretionary_value_change_pct <= -0.10 THEN 'Non-allocated order value down ' || CAST(CAST(ROUND(-discretionary_value_change_pct * 100, 0) AS INTEGER) AS VARCHAR) || ' pct'
        WHEN major_excursions_90d >= 2 THEN CAST(major_excursions_90d AS VARCHAR) || ' major cold chain excursions'
        ELSE 'Stable'
    END                                                                       AS top_risk_reason
FROM base;

CREATE OR REPLACE VIEW V_DC_SERVICE_PERFORMANCE
    COMMENT = 'Monthly DC service performance: line fill rate, on-time ship rate, on-time delivery rate, shipment count, cold chain excursion count. One row per DC per month.'
AS
WITH lines AS (
    SELECT dc_id, dc_name, order_month,
           COUNT(*) AS line_count,
           ROUND(SUM(is_line_filled_complete) / NULLIF(COUNT(*), 0), 4) AS line_fill_rate,
           ROUND(SUM(is_shipped_on_time) / NULLIF(SUM(CASE WHEN actual_ship_date IS NOT NULL THEN 1 ELSE 0 END), 0), 4) AS on_time_ship_rate,
           SUM(shipped_revenue) AS shipped_revenue
    FROM V_ORDER_LINE_DETAIL
    WHERE line_status <> 'CANCELLED'
    GROUP BY dc_id, dc_name, order_month
), ships AS (
    SELECT dc_id, DATE_TRUNC('MONTH', ship_date) AS ship_month,
           COUNT(*) AS shipment_count,
           ROUND(SUM(CASE WHEN actual_delivery_date IS NOT NULL AND actual_delivery_date <= promised_delivery_date THEN 1 ELSE 0 END)
                 / NULLIF(SUM(CASE WHEN actual_delivery_date IS NOT NULL THEN 1 ELSE 0 END), 0), 4) AS on_time_delivery_rate,
           SUM(CASE WHEN cold_chain_required THEN 1 ELSE 0 END) AS cold_chain_shipments
    FROM SHIPMENTS
    GROUP BY dc_id, DATE_TRUNC('MONTH', ship_date)
), exc AS (
    SELECT dc_id, DATE_TRUNC('MONTH', event_date) AS event_month,
           SUM(CASE WHEN is_excursion THEN 1 ELSE 0 END) AS excursion_count,
           SUM(CASE WHEN is_excursion THEN value_affected_wac ELSE 0 END) AS excursion_value_wac
    FROM COLD_CHAIN_EVENTS
    GROUP BY dc_id, DATE_TRUNC('MONTH', event_date)
)
SELECT l.dc_id, l.dc_name, l.order_month AS month,
       l.line_count, l.line_fill_rate, l.on_time_ship_rate, l.shipped_revenue,
       s.shipment_count, s.on_time_delivery_rate, s.cold_chain_shipments,
       COALESCE(e.excursion_count, 0) AS excursion_count,
       COALESCE(e.excursion_value_wac, 0) AS excursion_value_wac,
       ROUND(COALESCE(e.excursion_count, 0) / NULLIF(s.cold_chain_shipments, 0), 4) AS excursion_rate
FROM lines l
LEFT JOIN ships s ON s.dc_id = l.dc_id AND s.ship_month = l.order_month
LEFT JOIN exc   e ON e.dc_id = l.dc_id AND e.event_month = l.order_month;

CREATE OR REPLACE VIEW V_INVENTORY_RISK
    COMMENT = 'Latest weekly inventory position (snapshot 2026-09-21) by DC and NDC with expiry exposure and stockout risk flags. Use for expiring inventory, days of supply, and overstock questions.'
AS
SELECT
    i.snapshot_date,
    i.dc_id,
    d.dc_name,
    i.ndc,
    p.product_name,
    p.therapeutic_class,
    p.storage_class,
    p.manufacturer_id,
    m.manufacturer_name,
    p.wac_unit_price,
    i.on_hand_units,
    i.allocated_units,
    i.available_units,
    i.on_order_units,
    i.avg_weekly_demand_units,
    i.days_of_supply,
    i.expiring_30d_units,
    i.expiring_90d_units,
    i.inventory_value_wac,
    i.expiring_90d_value_wac,
    i.expiring_30d_units * p.wac_unit_price                                      AS expiring_30d_value_wac,
    i.reorder_point_units,
    CASE WHEN i.days_of_supply IS NOT NULL AND i.days_of_supply < 7 THEN 1 ELSE 0 END   AS is_stockout_risk,
    CASE WHEN i.days_of_supply IS NOT NULL AND i.days_of_supply > 120 THEN 1 ELSE 0 END AS is_overstock,
    CASE WHEN i.expiring_90d_units > 0 AND i.avg_weekly_demand_units * 12 < i.expiring_90d_units THEN 1 ELSE 0 END AS is_expiry_write_off_risk
FROM INVENTORY_SNAPSHOTS i
JOIN DISTRIBUTION_CENTERS d ON d.dc_id = i.dc_id
JOIN PRODUCTS p             ON p.ndc = i.ndc
JOIN MANUFACTURERS m        ON m.manufacturer_id = p.manufacturer_id
WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM INVENTORY_SNAPSHOTS);

CREATE OR REPLACE VIEW V_ALLOCATION_UTILIZATION
    COMMENT = 'Monthly allocation utilization for constrained products by customer: allocated vs requested vs consumed, shortfall, and utilization percent, with customer and product context.'
AS
SELECT
    a.period_month,
    a.ndc,
    p.product_name,
    p.therapeutic_class,
    a.manufacturer_id,
    m.manufacturer_name,
    a.customer_id,
    c.customer_name,
    c.customer_tier,
    c.contract_renewal_date,
    a.halcyon_total_allocation_units,
    a.allocation_basis,
    a.customer_allocated_units,
    a.customer_requested_units,
    a.customer_consumed_units,
    a.utilization_pct,
    a.shortfall_units,
    a.shortfall_units * p.wac_unit_price AS shortfall_value_wac
FROM CUSTOMER_ALLOCATIONS a
JOIN PRODUCTS p      ON p.ndc = a.ndc
JOIN MANUFACTURERS m ON m.manufacturer_id = a.manufacturer_id
JOIN CUSTOMERS c     ON c.customer_id = a.customer_id;

CREATE OR REPLACE VIEW V_COLD_CHAIN_EXCURSIONS
    COMMENT = 'Monthly cold chain excursion summary by DC, stage, storage class and packaging type: readings, excursions, excursion rate, severity mix, and value quarantined or destroyed.'
AS
SELECT
    dc_id,
    DATE_TRUNC('MONTH', event_date)                                        AS event_month,
    stage,
    storage_class,
    packaging_type,
    COUNT(*)                                                               AS readings,
    SUM(CASE WHEN is_excursion THEN 1 ELSE 0 END)                          AS excursions,
    ROUND(SUM(CASE WHEN is_excursion THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 4) AS excursion_rate,
    SUM(CASE WHEN excursion_severity = 'MINOR' THEN 1 ELSE 0 END)          AS minor_excursions,
    SUM(CASE WHEN excursion_severity = 'MAJOR' THEN 1 ELSE 0 END)          AS major_excursions,
    SUM(CASE WHEN excursion_severity = 'CRITICAL' THEN 1 ELSE 0 END)       AS critical_excursions,
    SUM(CASE WHEN disposition IN ('QUARANTINED','DESTROYED') THEN value_affected_wac ELSE 0 END) AS value_quarantined_or_destroyed_wac,
    SUM(CASE WHEN disposition = 'DESTROYED' THEN value_affected_wac ELSE 0 END)                  AS value_destroyed_wac
FROM COLD_CHAIN_EVENTS
GROUP BY dc_id, DATE_TRUNC('MONTH', event_date), stage, storage_class, packaging_type;

CREATE OR REPLACE VIEW V_CHARGEBACK_SUMMARY
    COMMENT = 'Monthly chargeback performance by manufacturer: claims, amount claimed, dispute and rejection rates, amount disputed or rejected, and average days to settle.'
AS
SELECT
    cb.manufacturer_id,
    m.manufacturer_name,
    DATE_TRUNC('MONTH', cb.submitted_date)                                          AS submitted_month,
    COUNT(*)                                                                        AS claims,
    SUM(cb.chargeback_amount)                                                       AS amount_claimed,
    SUM(CASE WHEN cb.status = 'PAID' THEN cb.chargeback_amount ELSE 0 END)          AS amount_paid,
    SUM(CASE WHEN cb.status IN ('DISPUTED','REJECTED') THEN 1 ELSE 0 END)           AS disputed_or_rejected_claims,
    ROUND(SUM(CASE WHEN cb.status IN ('DISPUTED','REJECTED') THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 4) AS dispute_rate,
    SUM(CASE WHEN cb.status IN ('DISPUTED','REJECTED') THEN cb.chargeback_amount ELSE 0 END) AS amount_disputed_or_rejected,
    SUM(CASE WHEN cb.status IN ('SUBMITTED','APPROVED') THEN cb.chargeback_amount ELSE 0 END) AS amount_open,
    ROUND(AVG(CASE WHEN cb.settled_date IS NOT NULL THEN DATEDIFF('day', cb.submitted_date, cb.settled_date) END), 1) AS avg_days_to_settle
FROM CHARGEBACKS cb
JOIN MANUFACTURERS m ON m.manufacturer_id = cb.manufacturer_id
GROUP BY cb.manufacturer_id, m.manufacturer_name, DATE_TRUNC('MONTH', cb.submitted_date);

CREATE OR REPLACE VIEW V_BACKORDER_AGING
    COMMENT = 'Open backorders as of 2026-09-25 with customer, product and DC context and an aging bucket (0-7, 8-14, 15-30, 31+ days). Use for backorder aging, escalation, and allocation questions.'
AS
SELECT
    b.backorder_id,
    b.order_line_id,
    b.backorder_date,
    b.days_open,
    CASE WHEN b.days_open <= 7 THEN '0-7'
         WHEN b.days_open <= 14 THEN '8-14'
         WHEN b.days_open <= 30 THEN '15-30'
         ELSE '31+' END                                   AS aging_bucket,
    b.customer_id,
    c.customer_name,
    c.customer_tier,
    c.contract_renewal_date,
    b.site_id,
    b.dc_id,
    b.ndc,
    p.product_name,
    p.therapeutic_class,
    p.is_allocated,
    p.manufacturer_id,
    m.manufacturer_name,
    b.qty_backordered,
    b.backorder_value_wac,
    b.reason_code,
    b.expected_release_date
FROM BACKORDERS b
JOIN CUSTOMERS c     ON c.customer_id = b.customer_id
JOIN PRODUCTS p      ON p.ndc = b.ndc
JOIN MANUFACTURERS m ON m.manufacturer_id = p.manufacturer_id
WHERE b.status = 'OPEN';

-- ============================================================================
-- END OF SNOWFLAKE DDL  (role grants are in 01b_wisdomai_grants.sql)
-- ============================================================================
