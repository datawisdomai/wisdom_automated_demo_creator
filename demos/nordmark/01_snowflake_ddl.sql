-- ============================================================================
-- WisdomAI POC — Nordmark Dagligvaror AB
-- Snowflake DDL
-- Domain: fictional Swedish grocery group with three banners — Kronmat (discount,
--   ~120 stores), Torghallen (neighbourhood stores, ~90 incl. franchise) and
--   Grosshallen (38 hypermarkets acquired 2025-01-01). Store POS mart (daily store
--   sales, weekly store x category sales incl. availability, waste and markdowns),
--   store costs, promotions, loyalty activity by segment, assortment, catchment
--   demographics, competitor events, and the imported non-food range sold in
--   Grosshallen (keyed like the import-purchasing platform on Teradata).
-- Demo "today": 2026-09-30. Data spans 2024-10-01 .. 2026-09-30 (24 months).
--   Rolling-12-month windows: R12_CUR = 2025-10-01..2026-09-30, R12_PRIOR = 2024-10-01..2025-09-30.
-- Amounts in SEK excluding VAT. Source systems represented: Visma/Extenda POS,
--   SAP (costs), Relex (availability/waste), the loyalty CRM, the market-data
--   provider (catchments), and the Teradata import-purchasing platform (federated).
-- ============================================================================

-- SECTION 0: ENVIRONMENT SETUP -------------------------------------------------
USE ROLE SYSADMIN;
CREATE DATABASE IF NOT EXISTS NORDMARK_POC
    COMMENT = 'WisdomAI POC database for the Nordmark Dagligvaror demo (fictional Swedish grocery group)';
CREATE SCHEMA IF NOT EXISTS NORDMARK_POC.ANALYTICS
    COMMENT = 'Nordmark store performance analytics: sales, margin, availability, waste, promotions, loyalty, catchments, costs, non-food availability';
USE DATABASE NORDMARK_POC;
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

CREATE OR REPLACE TABLE CALENDAR (
    calendar_date          DATE         NOT NULL PRIMARY KEY  COMMENT 'Calendar day',
    year_num               NUMBER(4,0)  NOT NULL              COMMENT 'Calendar year',
    month_num              NUMBER(2,0)  NOT NULL              COMMENT 'Calendar month number 1-12',
    month_start_date       DATE         NOT NULL              COMMENT 'First day of the calendar month (the month key used by all monthly tables and views)',
    month_name             VARCHAR(10)  NOT NULL              COMMENT 'Month name in English',
    quarter_label          VARCHAR(7)   NOT NULL              COMMENT 'Calendar quarter label, e.g. 2026-Q3 (Nordmark reports on calendar quarters)',
    iso_year               NUMBER(4,0)  NOT NULL              COMMENT 'ISO week-numbering year',
    iso_week               NUMBER(2,0)  NOT NULL              COMMENT 'ISO week number 1-53',
    week_start_date        DATE         NOT NULL              COMMENT 'Monday of the ISO week (the week key used by SALES_WEEKLY_STORE_CATEGORY)',
    week_label             VARCHAR(8)   NOT NULL              COMMENT 'ISO week label, e.g. 2026-W39',
    day_of_week            NUMBER(1,0)  NOT NULL              COMMENT 'Day of week 1=Monday .. 7=Sunday',
    day_name               VARCHAR(9)   NOT NULL              COMMENT 'Weekday name in English',
    is_weekend             BOOLEAN      NOT NULL              COMMENT 'TRUE on Saturday and Sunday',
    is_holiday             BOOLEAN      NOT NULL              COMMENT 'TRUE on Swedish public holidays and Midsummer Eve / Christmas Eve / New Year Eve',
    holiday_name           VARCHAR(40)                        COMMENT 'Holiday name when is_holiday',
    season                 VARCHAR(12)  NOT NULL              COMMENT 'Trading season: Winter, Spring, Easter, Summer, Midsummer, Autumn, Christmas',
    rolling_12m_bucket     VARCHAR(9)                         COMMENT 'R12_CUR for 2025-10-01..2026-09-30, R12_PRIOR for 2024-10-01..2025-09-30, NULL outside the two comparison windows',
    is_in_data_window      BOOLEAN      NOT NULL              COMMENT 'TRUE for 2024-10-01..2026-09-30 (days with sales data)'
) COMMENT = 'Day-level calendar with ISO weeks, calendar quarters, Swedish holidays, trading seasons and the two rolling-12-month comparison windows used for like-for-like analysis.';

CREATE OR REPLACE TABLE BANNERS (
    banner_id              VARCHAR(4)   NOT NULL PRIMARY KEY  COMMENT 'Banner code: KRM = Kronmat, TRG = Torghallen, GRH = Grosshallen',
    banner_name            VARCHAR(20)  NOT NULL              COMMENT 'Banner name as used in all other tables (Kronmat, Torghallen, Grosshallen)',
    store_format           VARCHAR(20)  NOT NULL              COMMENT 'Store format: Discount, Neighbourhood, Hypermarket',
    positioning            VARCHAR(200) NOT NULL              COMMENT 'One-sentence positioning statement',
    loyalty_program        VARCHAR(30)  NOT NULL              COMMENT 'Loyalty program name (Kronmat Plus, Torghallen Klubb, Grosshallen Kort)',
    acquired_date          DATE                               COMMENT 'Date the banner joined the group; NULL for the founding banners. Grosshallen was acquired 2025-01-01.',
    typical_basket_sek     NUMBER(8,2)  NOT NULL              COMMENT 'Typical average basket in SEK excl. VAT for the format',
    price_index            NUMBER(5,3)  NOT NULL              COMMENT 'Shelf price index versus the Swedish grocery market (1.000 = market)',
    target_gp_pct          NUMBER(5,3)  NOT NULL              COMMENT 'Budgeted gross margin percent for the banner',
    banner_director        VARCHAR(40)  NOT NULL              COMMENT 'Banner director (fictional)'
) COMMENT = 'The three Nordmark banners with format, positioning, loyalty program and budget margin.';

CREATE OR REPLACE TABLE NEIGHBORHOODS (
    neighborhood_id        VARCHAR(8)   NOT NULL PRIMARY KEY  COMMENT 'Catchment id NBH-nnn (one per store)',
    neighborhood_name      VARCHAR(60)  NOT NULL              COMMENT 'Neighbourhood / catchment name, e.g. Vasterhamn (Goteborg)',
    municipality           VARCHAR(40)  NOT NULL              COMMENT 'Swedish municipality (kommun)',
    region                 VARCHAR(12)  NOT NULL              COMMENT 'Nordmark sales region: Stockholm, Vast, Syd, Ost, Mitt, Norr',
    catchment_type         VARCHAR(20)  NOT NULL              COMMENT 'Neighbourhood type: Urban core, Suburban family, Small town, Commuter belt, Rural hub',
    population_2km         NUMBER(8,0)  NOT NULL              COMMENT 'Residents within 2 km of the store',
    households_2km         NUMBER(8,0)  NOT NULL              COMMENT 'Households within 2 km',
    median_income_ksek     NUMBER(6,1)  NOT NULL              COMMENT 'Median household disposable income in kSEK per year',
    share_families         NUMBER(5,3)  NOT NULL              COMMENT 'Share of households with children (0-1)',
    share_students         NUMBER(5,3)  NOT NULL              COMMENT 'Share of residents aged 18-26 in education (0-1)',
    share_seniors          NUMBER(5,3)  NOT NULL              COMMENT 'Share of residents aged 65+ (0-1)',
    car_access_share       NUMBER(5,3)  NOT NULL              COMMENT 'Share of households with a car (0-1)',
    competitor_count_2km   NUMBER(3,0)  NOT NULL              COMMENT 'Grocery competitors within 2 km at the as-of date',
    discount_competitor_flag BOOLEAN    NOT NULL              COMMENT 'TRUE when a discount grocery competitor trades within 2 km at the as-of date',
    nearest_competitor_km  NUMBER(4,2)  NOT NULL              COMMENT 'Distance to the nearest grocery competitor in km',
    grocery_spend_potential_msek NUMBER(8,2) NOT NULL         COMMENT 'Annual grocery spend of the catchment in MSEK (market-data provider estimate)',
    fair_share_pct         NUMBER(5,3)  NOT NULL              COMMENT 'Fair share of catchment spend a store of this format should capture given local competition (0-1)',
    catchment_potential_msek NUMBER(8,2) NOT NULL             COMMENT 'Expected annual net sales for the store in MSEK = grocery_spend_potential_msek x fair_share_pct. The denominator of the potential index.'
) COMMENT = 'Catchment demographics, competition and sales potential for every store location (market-data provider, refreshed annually). Drives the "underperforming versus local potential" analysis.';

CREATE OR REPLACE TABLE STORES (
    store_id               VARCHAR(8)   NOT NULL PRIMARY KEY  COMMENT 'Store id ST-nnnn',
    store_name             VARCHAR(60)  NOT NULL              COMMENT 'Store name = banner + location, e.g. Grosshallen Vasterhamn',
    banner_id              VARCHAR(4)   NOT NULL REFERENCES BANNERS(banner_id) COMMENT 'Banner code',
    banner                 VARCHAR(20)  NOT NULL              COMMENT 'Banner name (Kronmat, Torghallen, Grosshallen)',
    store_format           VARCHAR(20)  NOT NULL              COMMENT 'Discount, Neighbourhood or Hypermarket',
    region                 VARCHAR(12)  NOT NULL              COMMENT 'Nordmark sales region: Stockholm, Vast, Syd, Ost, Mitt, Norr',
    municipality           VARCHAR(40)  NOT NULL              COMMENT 'Municipality (kommun)',
    city                   VARCHAR(40)  NOT NULL              COMMENT 'City or town',
    neighborhood_id        VARCHAR(8)   NOT NULL REFERENCES NEIGHBORHOODS(neighborhood_id) COMMENT 'Catchment of the store',
    catchment_type         VARCHAR(20)  NOT NULL              COMMENT 'Catchment type copied from NEIGHBORHOODS for convenience',
    peer_cluster           VARCHAR(40)  NOT NULL              COMMENT 'Peer cluster = banner + catchment type, e.g. Grosshallen / Suburban family. Stores are compared with their cluster, not the whole chain.',
    sales_area_sqm         NUMBER(6,0)  NOT NULL              COMMENT 'Sales area in square metres',
    opened_date            DATE         NOT NULL              COMMENT 'Date the store opened under its current banner (for Grosshallen the original opening date)',
    acquired_date          DATE                               COMMENT 'Date the store joined Nordmark through an acquisition (2025-01-01 for Grosshallen stores)',
    closed_date            DATE                               COMMENT 'Date the store stopped trading under this banner (NULL if trading)',
    converted_to_banner    VARCHAR(20)                        COMMENT 'Banner the store was converted to when closed_date is set (Grosshallen Sundsvik became Kronmat on 2026-08-15)',
    store_status           VARCHAR(12)  NOT NULL              COMMENT 'OPEN, CONVERTED or CLOSED at the as-of date',
    is_franchise           BOOLEAN      NOT NULL              COMMENT 'TRUE for franchise (merchant-owned) Torghallen stores',
    is_lfl_comparable      BOOLEAN      NOT NULL              COMMENT 'TRUE when the store traded for the whole of both rolling-12-month windows (opened before 2024-10-01, not closed): the like-for-like population',
    store_manager          VARCHAR(40)  NOT NULL              COMMENT 'Store manager (fictional)',
    parking_spaces         NUMBER(5,0)  NOT NULL              COMMENT 'Customer parking spaces',
    online_pickup          BOOLEAN      NOT NULL              COMMENT 'TRUE when the store offers click-and-collect',
    latitude               NUMBER(9,6)  NOT NULL              COMMENT 'Latitude',
    longitude              NUMBER(9,6)  NOT NULL              COMMENT 'Longitude'
) COMMENT = 'Store master for all Nordmark stores (Kronmat, Torghallen, Grosshallen) with banner, region, catchment, peer cluster, size and lifecycle dates.';

CREATE OR REPLACE TABLE PRODUCT_CATEGORIES (
    category_id            VARCHAR(6)   NOT NULL PRIMARY KEY  COMMENT 'Category id CAT-nn',
    category_name          VARCHAR(40)  NOT NULL              COMMENT 'Category name, e.g. Fresh & Produce, Dairy, Bread & Bakery',
    department             VARCHAR(20)  NOT NULL              COMMENT 'Department: Fresh, Ambient, Frozen, Household, Non-food',
    is_fresh               BOOLEAN      NOT NULL              COMMENT 'TRUE for short-shelf-life categories (waste-prone)',
    is_nonfood             BOOLEAN      NOT NULL              COMMENT 'TRUE for the imported non-food categories sold only in Grosshallen hypermarkets',
    sold_in_banners        VARCHAR(30)  NOT NULL              COMMENT 'Comma-separated banner names that range the category',
    target_gp_pct          NUMBER(5,3)  NOT NULL              COMMENT 'Budgeted gross margin percent for the category',
    waste_prone            BOOLEAN      NOT NULL              COMMENT 'TRUE when waste is a managed KPI for the category',
    category_manager       VARCHAR(40)  NOT NULL              COMMENT 'Category manager (fictional)',
    teradata_department    VARCHAR(30)                        COMMENT 'For non-food categories: the department name used in the import-purchasing platform (Teradata RTL_DIM_PRODUCT.department)'
) COMMENT = 'Product categories at the grain of the weekly sales fact: 17 grocery/household categories ranged by all banners plus 6 imported non-food categories ranged only by Grosshallen.';

CREATE OR REPLACE TABLE NONFOOD_ASSORTMENT (
    product_key            NUMBER(10,0) NOT NULL PRIMARY KEY  COMMENT 'Product key of the import-purchasing platform (same key as Teradata RTL_DIM_PRODUCT.product_key)',
    sku                    VARCHAR(12)  NOT NULL              COMMENT 'SKU code (same as RTL_DIM_PRODUCT.sku)',
    product_name           VARCHAR(80)  NOT NULL              COMMENT 'Product name',
    teradata_department    VARCHAR(30)  NOT NULL              COMMENT 'Department in the purchasing platform (Apparel, Footwear, Home, Electronics, Beauty, Toys & Games, Sports & Outdoors)',
    category_id            VARCHAR(6)   NOT NULL REFERENCES PRODUCT_CATEGORIES(category_id) COMMENT 'Nordmark non-food category',
    category_name          VARCHAR(40)  NOT NULL              COMMENT 'Nordmark non-food category name',
    subcategory            VARCHAR(60)  NOT NULL              COMMENT 'Subcategory from the purchasing platform',
    brand                  VARCHAR(40)  NOT NULL              COMMENT 'Brand',
    is_private_label       BOOLEAN      NOT NULL              COMMENT 'TRUE for private label',
    supplier_key           NUMBER(10,0) NOT NULL              COMMENT 'Supplier key in the import-purchasing platform (join to Teradata RTL_DIM_SUPPLIER.supplier_key for the supplier name, country, lead time and on-time rate, and to RTL_FACT_PURCHASE_ORDER_LINE for inbound purchase orders)',
    price_tier             VARCHAR(10)  NOT NULL              COMMENT 'Value, Mid or Premium',
    list_price_sek         NUMBER(10,2) NOT NULL              COMMENT 'Shelf price in SEK excl. VAT',
    unit_cost_sek          NUMBER(10,2) NOT NULL              COMMENT 'Landed unit cost in SEK',
    listed_since           DATE         NOT NULL              COMMENT 'First month the SKU was ranged in Grosshallen',
    range_role             VARCHAR(12)  NOT NULL              COMMENT 'Core or Seasonal',
    stores_listed          NUMBER(3,0)  NOT NULL              COMMENT 'Number of Grosshallen stores that range the SKU'
) COMMENT = 'The imported non-food range sold in Grosshallen hypermarkets (250 SKUs). Keys match the import-purchasing platform on Teradata, which Grosshallen brought into the group: join on product_key / supplier_key to see suppliers and inbound purchase orders.';

CREATE OR REPLACE TABLE PROMOTIONS (
    promotion_id           VARCHAR(8)   NOT NULL PRIMARY KEY  COMMENT 'Promotion id PRM-nnn',
    promotion_name         VARCHAR(60)  NOT NULL              COMMENT 'Campaign name, e.g. Sommarpris 2026',
    banner_id              VARCHAR(4)   NOT NULL REFERENCES BANNERS(banner_id) COMMENT 'Banner that ran the promotion',
    banner                 VARCHAR(20)  NOT NULL              COMMENT 'Banner name',
    category_id            VARCHAR(6)   NOT NULL REFERENCES PRODUCT_CATEGORIES(category_id) COMMENT 'Promoted category',
    category_name          VARCHAR(40)  NOT NULL              COMMENT 'Promoted category name',
    mechanic               VARCHAR(30)  NOT NULL              COMMENT 'Price cut, Multibuy, Loyalty price, Bundle or Clearance',
    discount_pct           NUMBER(5,3)  NOT NULL              COMMENT 'Headline discount (0-1)',
    start_date             DATE         NOT NULL              COMMENT 'First day of the campaign',
    end_date               DATE         NOT NULL              COMMENT 'Last day of the campaign',
    weeks                  NUMBER(2,0)  NOT NULL              COMMENT 'Campaign length in weeks',
    funding_source         VARCHAR(20)  NOT NULL              COMMENT 'Supplier, Retailer or Shared funding of the discount',
    supplier_funding_pct   NUMBER(5,3)  NOT NULL              COMMENT 'Share of the discount funded by the supplier (0-1)',
    is_loyalty_only        BOOLEAN      NOT NULL              COMMENT 'TRUE when the price was available only to loyalty members',
    objective              VARCHAR(40)  NOT NULL              COMMENT 'Traffic, Basket, Clearance, Margin or Loyalty acquisition',
    owner                  VARCHAR(40)  NOT NULL              COMMENT 'Category manager who owned the campaign'
) COMMENT = 'Promotional campaigns by banner and category over the 24 months, with mechanics, funding and objective.';

-- SECTION 3: FACT TABLES -------------------------------------------------------

CREATE OR REPLACE TABLE STORE_DAILY_SALES (
    store_id               VARCHAR(8)   NOT NULL REFERENCES STORES(store_id) COMMENT 'Store',
    calendar_date          DATE         NOT NULL REFERENCES CALENDAR(calendar_date) COMMENT 'Trading day',
    net_sales_sek          NUMBER(12,2) NOT NULL              COMMENT 'Net sales in SEK excluding VAT, after discounts and markdowns',
    gross_profit_sek       NUMBER(12,2) NOT NULL              COMMENT 'Gross profit in SEK = net sales minus cost of goods sold (incl. waste and markdown cost)',
    transactions           NUMBER(8,0)  NOT NULL              COMMENT 'Number of customer transactions (receipts)',
    items_sold             NUMBER(9,0)  NOT NULL              COMMENT 'Units sold',
    loyalty_transactions   NUMBER(8,0)  NOT NULL              COMMENT 'Transactions where a loyalty card was identified',
    loyalty_sales_sek      NUMBER(12,2) NOT NULL              COMMENT 'Net sales on identified loyalty transactions',
    online_orders          NUMBER(6,0)  NOT NULL              COMMENT 'Click-and-collect / delivery orders fulfilled by the store (included in transactions)',
    online_sales_sek       NUMBER(12,2) NOT NULL              COMMENT 'Net sales of online orders (included in net_sales_sek)',
    PRIMARY KEY (store_id, calendar_date)
) COMMENT = 'Daily store totals from the POS: the source of sales, transactions, basket and gross profit KPIs. Average basket = net_sales_sek / transactions.';

CREATE OR REPLACE TABLE SALES_WEEKLY_STORE_CATEGORY (
    store_id               VARCHAR(8)   NOT NULL REFERENCES STORES(store_id) COMMENT 'Store',
    week_start_date        DATE         NOT NULL              COMMENT 'Monday of the ISO week (CALENDAR.week_start_date)',
    category_id            VARCHAR(6)   NOT NULL REFERENCES PRODUCT_CATEGORIES(category_id) COMMENT 'Category',
    net_sales_sek          NUMBER(12,2) NOT NULL              COMMENT 'Net sales in SEK excl. VAT',
    cogs_sek               NUMBER(12,2) NOT NULL              COMMENT 'Cost of goods sold incl. waste and markdown cost',
    gross_profit_sek       NUMBER(12,2) NOT NULL              COMMENT 'Gross profit = net sales minus COGS',
    units_sold             NUMBER(9,0)  NOT NULL              COMMENT 'Units sold',
    promo_sales_sek        NUMBER(12,2) NOT NULL              COMMENT 'Net sales sold on promotion',
    markdown_sek           NUMBER(11,2) NOT NULL              COMMENT 'Value of price markdowns (short-dated and clearance reductions) given in the week',
    waste_sek              NUMBER(11,2) NOT NULL              COMMENT 'Cost value of goods written off as waste',
    waste_units            NUMBER(8,0)  NOT NULL              COMMENT 'Units written off as waste',
    on_shelf_availability_pct NUMBER(5,4) NOT NULL            COMMENT 'On-shelf availability (OSA): share of audited SKU-hours the item was on the shelf (0-1). Target 0.96.',
    stockout_hours         NUMBER(7,1)  NOT NULL              COMMENT 'Shelf-hours out of stock across the category in the week',
    inventory_days         NUMBER(5,1)  NOT NULL              COMMENT 'Days of inventory cover at week end',
    PRIMARY KEY (store_id, week_start_date, category_id)
) COMMENT = 'Weekly store x category sales, margin, promotion share, markdowns, waste and on-shelf availability (POS + Relex). The grain for category drivers, availability and waste analysis.';

CREATE OR REPLACE TABLE STORE_MONTHLY_COSTS (
    store_id               VARCHAR(8)   NOT NULL REFERENCES STORES(store_id) COMMENT 'Store',
    month_start_date       DATE         NOT NULL              COMMENT 'Month (first day)',
    labour_cost_sek        NUMBER(12,2) NOT NULL              COMMENT 'Store labour cost incl. social charges',
    occupancy_cost_sek     NUMBER(12,2) NOT NULL              COMMENT 'Rent, energy and maintenance',
    logistics_cost_sek     NUMBER(12,2) NOT NULL              COMMENT 'Inbound logistics charged to the store',
    marketing_cost_sek     NUMBER(12,2) NOT NULL              COMMENT 'Local marketing and loyalty costs',
    other_opex_sek         NUMBER(12,2) NOT NULL              COMMENT 'Other operating expenses',
    depreciation_sek       NUMBER(12,2) NOT NULL              COMMENT 'Depreciation of store assets',
    fte                    NUMBER(6,1)  NOT NULL              COMMENT 'Full-time equivalents',
    labour_hours           NUMBER(9,1)  NOT NULL              COMMENT 'Hours worked',
    PRIMARY KEY (store_id, month_start_date)
) COMMENT = 'Monthly store operating costs from SAP. Store EBIT = gross profit minus these costs; used for the banner P&L and the Grosshallen turnaround.';

CREATE OR REPLACE TABLE PROMOTION_RESULTS (
    promotion_id           VARCHAR(8)   NOT NULL REFERENCES PROMOTIONS(promotion_id) COMMENT 'Promotion',
    store_id               VARCHAR(8)   NOT NULL REFERENCES STORES(store_id) COMMENT 'Participating store',
    promo_sales_sek        NUMBER(12,2) NOT NULL              COMMENT 'Net sales of the promoted category during the campaign',
    baseline_sales_sek     NUMBER(12,2) NOT NULL              COMMENT 'Expected sales of the category over the same weeks without the promotion (pre-period baseline)',
    uplift_pct             NUMBER(6,3)  NOT NULL              COMMENT 'Sales uplift = promo_sales / baseline_sales - 1',
    promo_gp_pct           NUMBER(5,3)  NOT NULL              COMMENT 'Gross margin percent during the campaign',
    baseline_gp_pct        NUMBER(5,3)  NOT NULL              COMMENT 'Gross margin percent in the baseline period',
    margin_dilution_pts    NUMBER(5,3)  NOT NULL              COMMENT 'baseline_gp_pct - promo_gp_pct (positive = margin got worse)',
    markdown_cost_sek      NUMBER(11,2) NOT NULL              COMMENT 'Retailer-funded discount cost',
    incremental_gp_sek     NUMBER(12,2) NOT NULL              COMMENT 'Incremental gross profit versus baseline (can be negative)',
    promo_units            NUMBER(9,0)  NOT NULL              COMMENT 'Units sold on promotion',
    PRIMARY KEY (promotion_id, store_id)
) COMMENT = 'Promotion outcome per participating store: uplift versus baseline and margin dilution.';

CREATE OR REPLACE TABLE LOYALTY_ACTIVITY_MONTHLY (
    store_id               VARCHAR(8)   NOT NULL REFERENCES STORES(store_id) COMMENT 'Home store of the members (store they visit most)',
    month_start_date       DATE         NOT NULL              COMMENT 'Month (first day)',
    segment                VARCHAR(20)  NOT NULL              COMMENT 'Customer segment: Families, Seniors, Students, Urban singles, Value seekers, Premium',
    active_members         NUMBER(7,0)  NOT NULL              COMMENT 'Members with at least one identified purchase in the month',
    visits                 NUMBER(8,0)  NOT NULL              COMMENT 'Identified visits (transactions) in the month',
    spend_sek              NUMBER(12,2) NOT NULL              COMMENT 'Identified net spend in SEK',
    new_members            NUMBER(6,0)  NOT NULL              COMMENT 'Members who joined in the month',
    lapsed_members         NUMBER(6,0)  NOT NULL              COMMENT 'Members with no purchase for 90 days as of month end',
    avg_visits_per_member  NUMBER(6,2)  NOT NULL              COMMENT 'visits / active_members (visit frequency)',
    PRIMARY KEY (store_id, month_start_date, segment)
) COMMENT = 'Loyalty CRM activity by home store, month and customer segment: active members, visit frequency and spend.';

CREATE OR REPLACE TABLE STORE_ASSORTMENT_MONTHLY (
    store_id               VARCHAR(8)   NOT NULL REFERENCES STORES(store_id) COMMENT 'Store',
    month_start_date       DATE         NOT NULL              COMMENT 'Month (first day)',
    category_id            VARCHAR(6)   NOT NULL REFERENCES PRODUCT_CATEGORIES(category_id) COMMENT 'Category',
    listed_skus            NUMBER(5,0)  NOT NULL              COMMENT 'SKUs ranged in the store in the category',
    private_label_skus     NUMBER(5,0)  NOT NULL              COMMENT 'Private-label SKUs ranged',
    pl_sales_share         NUMBER(5,4)  NOT NULL              COMMENT 'Private-label share of category net sales (0-1)',
    new_skus               NUMBER(4,0)  NOT NULL              COMMENT 'SKUs added in the month',
    delisted_skus          NUMBER(4,0)  NOT NULL              COMMENT 'SKUs removed in the month',
    range_depth_index      NUMBER(5,3)  NOT NULL              COMMENT 'listed_skus versus the banner average for the category (1.000 = banner average)',
    PRIMARY KEY (store_id, month_start_date, category_id)
) COMMENT = 'Monthly assortment by store and category: range depth and private-label share.';

CREATE OR REPLACE TABLE COMPETITOR_EVENTS (
    event_id               VARCHAR(8)   NOT NULL PRIMARY KEY  COMMENT 'Event id CEV-nnn',
    store_id               VARCHAR(8)   NOT NULL REFERENCES STORES(store_id) COMMENT 'Nordmark store affected',
    event_date             DATE         NOT NULL              COMMENT 'Date of the event',
    competitor_name        VARCHAR(40)  NOT NULL              COMMENT 'Competitor banner (fictional)',
    competitor_format      VARCHAR(20)  NOT NULL              COMMENT 'Discount, Supermarket, Hypermarket, Convenience or Online',
    event_type             VARCHAR(20)  NOT NULL              COMMENT 'Opening, Closure, Price campaign or Refurbishment',
    distance_km            NUMBER(4,2)  NOT NULL              COMMENT 'Distance from the Nordmark store in km',
    estimated_sales_impact_pct NUMBER(5,3) NOT NULL           COMMENT 'Estimated impact on the store annual sales (negative = loss)',
    notes                  VARCHAR(200)                       COMMENT 'Free-text note from the regional manager'
) COMMENT = 'Competitor openings, closures and campaigns near Nordmark stores, logged by regional managers.';

CREATE OR REPLACE TABLE NONFOOD_AVAILABILITY_MONTHLY (
    store_id               VARCHAR(8)   NOT NULL REFERENCES STORES(store_id) COMMENT 'Grosshallen store',
    month_start_date       DATE         NOT NULL              COMMENT 'Month (first day)',
    product_key            NUMBER(10,0) NOT NULL REFERENCES NONFOOD_ASSORTMENT(product_key) COMMENT 'Imported non-food SKU (same key as Teradata RTL_DIM_PRODUCT.product_key)',
    units_sold             NUMBER(7,0)  NOT NULL              COMMENT 'Units sold in the month',
    net_sales_sek          NUMBER(11,2) NOT NULL              COMMENT 'Net sales in SEK',
    on_shelf_availability_pct NUMBER(5,4) NOT NULL            COMMENT 'Share of trading days the SKU was on the shelf (0-1)',
    stockout_days          NUMBER(3,0)  NOT NULL              COMMENT 'Trading days with no stock',
    lost_sales_sek         NUMBER(11,2) NOT NULL              COMMENT 'Estimated sales lost to stockouts in SEK',
    PRIMARY KEY (store_id, month_start_date, product_key)
) COMMENT = 'Monthly availability and lost sales of the imported non-food range per Grosshallen store and SKU. Join supplier_key via NONFOOD_ASSORTMENT to the Teradata purchasing tables to explain stockouts with late inbound purchase orders.';

CREATE OR REPLACE TABLE DATA_DICTIONARY (
    table_name             VARCHAR(60)  NOT NULL              COMMENT 'Table or view name',
    column_name            VARCHAR(60)  NOT NULL              COMMENT 'Column or metric name',
    data_type              VARCHAR(30)                        COMMENT 'Snowflake data type',
    description            VARCHAR(500)                       COMMENT 'Business description',
    sample_value           VARCHAR(100)                       COMMENT 'Example value',
    metric_formula         VARCHAR(500)                       COMMENT 'Formula for derived metrics',
    business_owner         VARCHAR(60)                        COMMENT 'Business owner of the definition (e.g. Store Operations, FP&A)',
    source_system          VARCHAR(30)                        COMMENT 'Upstream system of record'
) COMMENT = 'Self-describing metadata with business ownership and source system, the physical half of the business glossary.';

-- SECTION 4: ANALYTICAL VIEWS -------------------------------------------------
-- Demo as-of date is 2026-09-30. Rolling-12-month windows come from CALENDAR.rolling_12m_bucket.
-- Portable SQL (runs in DuckDB and Snowflake): ANSI CASE, DATE literals, NULLIF for ratios, named GROUP BY.

CREATE OR REPLACE VIEW V_KPI_STORE_MONTHLY
    COMMENT = 'Level-1 KPIs by store and month: net sales, gross profit and margin percent, transactions, average basket, items per basket, loyalty share, plus the same month last year and growth rates. lfl_growth_pct is populated only for like-for-like comparable stores (is_lfl_comparable). Filter by banner, region, catchment type, store or month.'
AS
WITH m AS (
    SELECT
        d.store_id,
        c.month_start_date,
        c.year_num,
        c.month_num,
        c.quarter_label,
        SUM(d.net_sales_sek)        AS net_sales_sek,
        SUM(d.gross_profit_sek)     AS gross_profit_sek,
        SUM(d.transactions)         AS transactions,
        SUM(d.items_sold)           AS items_sold,
        SUM(d.loyalty_sales_sek)    AS loyalty_sales_sek,
        SUM(d.online_sales_sek)     AS online_sales_sek,
        COUNT(*)                    AS trading_days
    FROM STORE_DAILY_SALES d
    JOIN CALENDAR c ON c.calendar_date = d.calendar_date
    GROUP BY d.store_id, c.month_start_date, c.year_num, c.month_num, c.quarter_label
)
SELECT
    s.store_id,
    s.store_name,
    s.banner,
    s.region,
    s.catchment_type,
    s.peer_cluster,
    s.is_lfl_comparable,
    m.month_start_date,
    m.year_num,
    m.month_num,
    m.quarter_label,
    m.trading_days,
    m.net_sales_sek,
    m.gross_profit_sek,
    m.gross_profit_sek / NULLIF(m.net_sales_sek, 0)                     AS gp_pct,
    m.transactions,
    m.net_sales_sek / NULLIF(m.transactions, 0)                         AS avg_basket_sek,
    m.items_sold * 1.0 / NULLIF(m.transactions, 0)                      AS items_per_basket,
    m.loyalty_sales_sek / NULLIF(m.net_sales_sek, 0)                    AS loyalty_sales_share,
    m.online_sales_sek / NULLIF(m.net_sales_sek, 0)                     AS online_sales_share,
    ly.net_sales_sek                                                    AS ly_net_sales_sek,
    ly.transactions                                                     AS ly_transactions,
    ly.gross_profit_sek / NULLIF(ly.net_sales_sek, 0)                   AS ly_gp_pct,
    m.net_sales_sek / NULLIF(ly.net_sales_sek, 0) - 1                   AS sales_growth_pct,
    CASE WHEN s.is_lfl_comparable THEN m.net_sales_sek / NULLIF(ly.net_sales_sek, 0) - 1 END AS lfl_growth_pct,
    m.transactions * 1.0 / NULLIF(ly.transactions, 0) - 1               AS transactions_growth_pct,
    (m.net_sales_sek / NULLIF(m.transactions, 0)) / NULLIF(ly.net_sales_sek / NULLIF(ly.transactions, 0), 0) - 1 AS basket_growth_pct
FROM m
JOIN STORES s ON s.store_id = m.store_id
LEFT JOIN m ly ON ly.store_id = m.store_id AND ly.year_num = m.year_num - 1 AND ly.month_num = m.month_num;

CREATE OR REPLACE VIEW V_BANNER_KPI_MONTHLY
    COMMENT = 'Banner P&L and KPIs by month: stores trading, net sales, gross profit and margin percent, transactions, average basket, like-for-like growth (comparable stores only), operating costs, EBIT and EBIT percent. Sum months within a quarter_label for quarterly figures. Group total = sum over banners.'
AS
WITH sales AS (
    SELECT
        s.banner,
        c.month_start_date,
        c.year_num,
        c.month_num,
        c.quarter_label,
        COUNT(DISTINCT d.store_id)  AS stores_trading,
        SUM(d.net_sales_sek)        AS net_sales_sek,
        SUM(d.gross_profit_sek)     AS gross_profit_sek,
        SUM(d.transactions)         AS transactions,
        SUM(d.loyalty_sales_sek)    AS loyalty_sales_sek,
        SUM(CASE WHEN s.is_lfl_comparable THEN d.net_sales_sek ELSE 0 END)   AS lfl_net_sales_sek,
        SUM(CASE WHEN s.is_lfl_comparable THEN d.transactions ELSE 0 END)    AS lfl_transactions
    FROM STORE_DAILY_SALES d
    JOIN STORES s   ON s.store_id = d.store_id
    JOIN CALENDAR c ON c.calendar_date = d.calendar_date
    GROUP BY s.banner, c.month_start_date, c.year_num, c.month_num, c.quarter_label
),
costs AS (
    SELECT s.banner, k.month_start_date,
           SUM(k.labour_cost_sek + k.occupancy_cost_sek + k.logistics_cost_sek + k.marketing_cost_sek + k.other_opex_sek + k.depreciation_sek) AS operating_costs_sek,
           SUM(k.labour_cost_sek) AS labour_cost_sek
    FROM STORE_MONTHLY_COSTS k
    JOIN STORES s ON s.store_id = k.store_id
    GROUP BY s.banner, k.month_start_date
)
SELECT
    cur.banner,
    cur.month_start_date,
    cur.year_num,
    cur.month_num,
    cur.quarter_label,
    cur.stores_trading,
    cur.net_sales_sek,
    cur.gross_profit_sek,
    cur.gross_profit_sek / NULLIF(cur.net_sales_sek, 0)                 AS gp_pct,
    cur.transactions,
    cur.net_sales_sek / NULLIF(cur.transactions, 0)                     AS avg_basket_sek,
    cur.loyalty_sales_sek / NULLIF(cur.net_sales_sek, 0)                AS loyalty_sales_share,
    ly.net_sales_sek                                                    AS ly_net_sales_sek,
    cur.net_sales_sek / NULLIF(ly.net_sales_sek, 0) - 1                 AS sales_growth_pct,
    cur.lfl_net_sales_sek / NULLIF(ly.lfl_net_sales_sek, 0) - 1         AS lfl_growth_pct,
    cur.lfl_transactions * 1.0 / NULLIF(ly.lfl_transactions, 0) - 1     AS lfl_transactions_growth_pct,
    (cur.lfl_net_sales_sek / NULLIF(cur.lfl_transactions, 0)) / NULLIF(ly.lfl_net_sales_sek / NULLIF(ly.lfl_transactions, 0), 0) - 1 AS lfl_basket_growth_pct,
    k.operating_costs_sek,
    k.labour_cost_sek,
    k.labour_cost_sek / NULLIF(cur.net_sales_sek, 0)                    AS labour_cost_pct,
    cur.gross_profit_sek - COALESCE(k.operating_costs_sek, 0)           AS ebit_sek,
    (cur.gross_profit_sek - COALESCE(k.operating_costs_sek, 0)) / NULLIF(cur.net_sales_sek, 0) AS ebit_pct
FROM sales cur
LEFT JOIN sales ly ON ly.banner = cur.banner AND ly.year_num = cur.year_num - 1 AND ly.month_num = cur.month_num
LEFT JOIN costs k  ON k.banner = cur.banner AND k.month_start_date = cur.month_start_date;

CREATE OR REPLACE VIEW V_STORE_GAP_DECOMPOSITION
    COMMENT = 'Level-2 driver analysis per store: rolling-12-month sales to 2026-09-30 versus the prior 12 months, with the change split into a transactions effect and a basket effect (SEK and share). growth_driver names the dominant driver. Comparable stores only (is_lfl_comparable).'
AS
WITH w AS (
    SELECT
        d.store_id,
        c.rolling_12m_bucket,
        SUM(d.net_sales_sek)    AS net_sales_sek,
        SUM(d.gross_profit_sek) AS gross_profit_sek,
        SUM(d.transactions)     AS transactions
    FROM STORE_DAILY_SALES d
    JOIN CALENDAR c ON c.calendar_date = d.calendar_date
    WHERE c.rolling_12m_bucket IS NOT NULL
    GROUP BY d.store_id, c.rolling_12m_bucket
),
cur AS (SELECT * FROM w WHERE rolling_12m_bucket = 'R12_CUR'),
pri AS (SELECT * FROM w WHERE rolling_12m_bucket = 'R12_PRIOR')
SELECT
    s.store_id,
    s.store_name,
    s.banner,
    s.region,
    s.catchment_type,
    s.peer_cluster,
    cur.net_sales_sek                                                   AS sales_r12_sek,
    pri.net_sales_sek                                                   AS sales_prior_r12_sek,
    cur.net_sales_sek - pri.net_sales_sek                               AS sales_change_sek,
    cur.net_sales_sek / NULLIF(pri.net_sales_sek, 0) - 1                AS sales_change_pct,
    cur.gross_profit_sek / NULLIF(cur.net_sales_sek, 0)                 AS gp_pct_r12,
    pri.gross_profit_sek / NULLIF(pri.net_sales_sek, 0)                 AS gp_pct_prior_r12,
    cur.transactions                                                    AS transactions_r12,
    pri.transactions                                                    AS transactions_prior_r12,
    cur.transactions * 1.0 / NULLIF(pri.transactions, 0) - 1            AS transactions_change_pct,
    cur.net_sales_sek / NULLIF(cur.transactions, 0)                     AS basket_r12_sek,
    pri.net_sales_sek / NULLIF(pri.transactions, 0)                     AS basket_prior_r12_sek,
    (cur.net_sales_sek / NULLIF(cur.transactions, 0)) / NULLIF(pri.net_sales_sek / NULLIF(pri.transactions, 0), 0) - 1 AS basket_change_pct,
    (cur.transactions - pri.transactions) * (pri.net_sales_sek / NULLIF(pri.transactions, 0))                        AS transactions_effect_sek,
    ((cur.net_sales_sek / NULLIF(cur.transactions, 0)) - (pri.net_sales_sek / NULLIF(pri.transactions, 0))) * cur.transactions AS basket_effect_sek,
    CASE
        WHEN ABS((cur.transactions - pri.transactions) * (pri.net_sales_sek / NULLIF(pri.transactions, 0)))
             >= ABS(((cur.net_sales_sek / NULLIF(cur.transactions, 0)) - (pri.net_sales_sek / NULLIF(pri.transactions, 0))) * cur.transactions)
        THEN 'Transactions' ELSE 'Basket' END                           AS growth_driver,
    CASE WHEN cur.net_sales_sek >= pri.net_sales_sek THEN 'Growing' ELSE 'Declining' END AS trend
FROM cur
JOIN pri    ON pri.store_id = cur.store_id
JOIN STORES s ON s.store_id = cur.store_id
WHERE s.is_lfl_comparable;

CREATE OR REPLACE VIEW V_PEER_COMPARISON
    COMMENT = 'Level-2/3 peer comparison: each comparable store rolling-12-month KPIs (sales per sqm, like-for-like growth, gross margin percent, average basket, on-shelf availability, markdown rate, waste rate, private-label share, transactions per household) next to the median of its peer cluster (banner x catchment type) and the gap to that median. Compare a store with its cluster, not the whole chain.'
AS
WITH daily AS (
    SELECT d.store_id, c.rolling_12m_bucket,
           SUM(d.net_sales_sek) AS net_sales_sek, SUM(d.gross_profit_sek) AS gross_profit_sek, SUM(d.transactions) AS transactions
    FROM STORE_DAILY_SALES d JOIN CALENDAR c ON c.calendar_date = d.calendar_date
    WHERE c.rolling_12m_bucket IS NOT NULL
    GROUP BY d.store_id, c.rolling_12m_bucket
),
weekly AS (
    SELECT w.store_id,
           SUM(w.net_sales_sek) AS cat_sales_sek,
           SUM(w.markdown_sek) AS markdown_sek,
           SUM(w.waste_sek) AS waste_sek,
           SUM(w.on_shelf_availability_pct * w.net_sales_sek) / NULLIF(SUM(w.net_sales_sek), 0) AS osa_pct
    FROM SALES_WEEKLY_STORE_CATEGORY w
    WHERE w.week_start_date >= DATE '2025-10-01' AND w.week_start_date <= DATE '2026-09-30'
    GROUP BY w.store_id
),
pl AS (
    SELECT a.store_id, AVG(a.pl_sales_share) AS pl_sales_share
    FROM STORE_ASSORTMENT_MONTHLY a
    WHERE a.month_start_date >= DATE '2025-10-01' AND a.month_start_date <= DATE '2026-09-01'
    GROUP BY a.store_id
),
store_kpi AS (
    SELECT
        s.store_id, s.store_name, s.banner, s.region, s.catchment_type, s.peer_cluster, s.sales_area_sqm,
        cur.net_sales_sek                                                AS sales_r12_sek,
        cur.net_sales_sek / NULLIF(s.sales_area_sqm, 0)                  AS sales_per_sqm_sek,
        cur.net_sales_sek / NULLIF(pri.net_sales_sek, 0) - 1             AS lfl_growth_pct,
        cur.gross_profit_sek / NULLIF(cur.net_sales_sek, 0)              AS gp_pct,
        cur.net_sales_sek / NULLIF(cur.transactions, 0)                  AS avg_basket_sek,
        cur.transactions * 1.0 / NULLIF(n.households_2km, 0)             AS transactions_per_household,
        wk.osa_pct,
        wk.markdown_sek / NULLIF(wk.cat_sales_sek, 0)                    AS markdown_rate,
        wk.waste_sek / NULLIF(wk.cat_sales_sek, 0)                       AS waste_rate,
        pl.pl_sales_share
    FROM STORES s
    JOIN NEIGHBORHOODS n ON n.neighborhood_id = s.neighborhood_id
    JOIN daily cur ON cur.store_id = s.store_id AND cur.rolling_12m_bucket = 'R12_CUR'
    JOIN daily pri ON pri.store_id = s.store_id AND pri.rolling_12m_bucket = 'R12_PRIOR'
    LEFT JOIN weekly wk ON wk.store_id = s.store_id
    LEFT JOIN pl ON pl.store_id = s.store_id
    WHERE s.is_lfl_comparable
),
cluster AS (
    SELECT peer_cluster,
           COUNT(*)                          AS cluster_stores,
           MEDIAN(sales_per_sqm_sek)         AS cluster_sales_per_sqm_sek,
           MEDIAN(lfl_growth_pct)            AS cluster_lfl_growth_pct,
           MEDIAN(gp_pct)                    AS cluster_gp_pct,
           MEDIAN(avg_basket_sek)            AS cluster_avg_basket_sek,
           MEDIAN(transactions_per_household) AS cluster_transactions_per_household,
           MEDIAN(osa_pct)                   AS cluster_osa_pct,
           MEDIAN(markdown_rate)             AS cluster_markdown_rate,
           MEDIAN(waste_rate)                AS cluster_waste_rate,
           MEDIAN(pl_sales_share)            AS cluster_pl_sales_share
    FROM store_kpi
    GROUP BY peer_cluster
)
SELECT
    k.store_id, k.store_name, k.banner, k.region, k.catchment_type, k.peer_cluster, k.sales_area_sqm,
    c.cluster_stores,
    k.sales_r12_sek,
    k.sales_per_sqm_sek,            c.cluster_sales_per_sqm_sek,       k.sales_per_sqm_sek - c.cluster_sales_per_sqm_sek               AS sales_per_sqm_gap_sek,
    k.lfl_growth_pct,               c.cluster_lfl_growth_pct,          k.lfl_growth_pct - c.cluster_lfl_growth_pct                     AS lfl_growth_gap_pts,
    k.gp_pct,                       c.cluster_gp_pct,                  k.gp_pct - c.cluster_gp_pct                                     AS gp_pct_gap_pts,
    k.avg_basket_sek,               c.cluster_avg_basket_sek,          k.avg_basket_sek - c.cluster_avg_basket_sek                     AS avg_basket_gap_sek,
    k.transactions_per_household,   c.cluster_transactions_per_household, k.transactions_per_household - c.cluster_transactions_per_household AS transactions_per_household_gap,
    k.osa_pct,                      c.cluster_osa_pct,                 k.osa_pct - c.cluster_osa_pct                                   AS osa_gap_pts,
    k.markdown_rate,                c.cluster_markdown_rate,           k.markdown_rate - c.cluster_markdown_rate                       AS markdown_rate_gap_pts,
    k.waste_rate,                   c.cluster_waste_rate,              k.waste_rate - c.cluster_waste_rate                             AS waste_rate_gap_pts,
    k.pl_sales_share,               c.cluster_pl_sales_share,          k.pl_sales_share - c.cluster_pl_sales_share                     AS pl_sales_share_gap_pts
FROM store_kpi k
JOIN cluster c ON c.peer_cluster = k.peer_cluster;

CREATE OR REPLACE VIEW V_CATCHMENT_POTENTIAL
    COMMENT = 'Level-3 local-potential analysis: rolling-12-month net sales of every trading store versus the catchment potential from the market-data provider. potential_index = sales / potential (1.0 = capturing the expected fair share); potential_gap_sek = potential minus sales; cluster_median_index for the peer cluster; gap_rank_in_banner = 1 for the store with the largest SEK gap in its banner. Includes competition and demographics for the "why" questions.'
AS
WITH r12 AS (
    SELECT d.store_id, SUM(d.net_sales_sek) AS sales_r12_sek, SUM(d.transactions) AS transactions_r12
    FROM STORE_DAILY_SALES d JOIN CALENDAR c ON c.calendar_date = d.calendar_date
    WHERE c.rolling_12m_bucket = 'R12_CUR'
    GROUP BY d.store_id
),
base AS (
    SELECT
        s.store_id, s.store_name, s.banner, s.region, s.city, s.catchment_type, s.peer_cluster, s.sales_area_sqm, s.store_status,
        n.neighborhood_name, n.population_2km, n.households_2km, n.median_income_ksek, n.share_families, n.share_students, n.share_seniors,
        n.competitor_count_2km, n.discount_competitor_flag, n.nearest_competitor_km,
        n.grocery_spend_potential_msek, n.fair_share_pct, n.catchment_potential_msek,
        r.sales_r12_sek,
        r.transactions_r12,
        r.sales_r12_sek / NULLIF(n.catchment_potential_msek * 1000000, 0)      AS potential_index,
        n.catchment_potential_msek * 1000000 - r.sales_r12_sek                 AS potential_gap_sek
    FROM STORES s
    JOIN NEIGHBORHOODS n ON n.neighborhood_id = s.neighborhood_id
    JOIN r12 r ON r.store_id = s.store_id
    WHERE s.is_lfl_comparable
),
cl AS (
    SELECT peer_cluster, MEDIAN(potential_index) AS cluster_median_index, COUNT(*) AS cluster_stores
    FROM base GROUP BY peer_cluster
)
SELECT
    b.*,
    cl.cluster_median_index,
    cl.cluster_stores,
    b.potential_index - cl.cluster_median_index                               AS index_gap_vs_cluster,
    ROW_NUMBER() OVER (PARTITION BY b.banner ORDER BY b.potential_gap_sek DESC) AS gap_rank_in_banner,
    ROW_NUMBER() OVER (PARTITION BY b.peer_cluster ORDER BY b.potential_index DESC) AS index_rank_in_cluster,
    CASE WHEN b.potential_index < 0.75 THEN 'Underperforming'
         WHEN b.potential_index < 0.90 THEN 'Below potential'
         WHEN b.potential_index <= 1.10 THEN 'At potential'
         ELSE 'Outperforming' END                                             AS potential_band
FROM base b
JOIN cl ON cl.peer_cluster = b.peer_cluster;

CREATE OR REPLACE VIEW V_PROMO_EFFECTIVENESS
    COMMENT = 'Promotion scorecard: for every campaign the participating stores, promotional and baseline sales, uplift percent, margin during versus before, margin dilution in points, incremental gross profit, and ranks (uplift_rank 1 = strongest uplift; margin_rank_from_bottom 1 = worst margin dilution). Use to find promotions with strong sales but weak margins.'
AS
WITH agg AS (
    SELECT
        p.promotion_id, p.promotion_name, p.banner, p.category_name, p.mechanic, p.discount_pct, p.start_date, p.end_date, p.weeks,
        p.funding_source, p.supplier_funding_pct, p.is_loyalty_only, p.objective, p.owner,
        COUNT(*)                        AS participating_stores,
        SUM(r.promo_sales_sek)          AS promo_sales_sek,
        SUM(r.baseline_sales_sek)       AS baseline_sales_sek,
        SUM(r.promo_sales_sek) / NULLIF(SUM(r.baseline_sales_sek), 0) - 1                       AS uplift_pct,
        SUM(r.promo_gp_pct * r.promo_sales_sek) / NULLIF(SUM(r.promo_sales_sek), 0)             AS promo_gp_pct,
        SUM(r.baseline_gp_pct * r.baseline_sales_sek) / NULLIF(SUM(r.baseline_sales_sek), 0)    AS baseline_gp_pct,
        SUM(r.markdown_cost_sek)        AS markdown_cost_sek,
        SUM(r.incremental_gp_sek)       AS incremental_gp_sek,
        SUM(r.promo_units)              AS promo_units
    FROM PROMOTIONS p
    JOIN PROMOTION_RESULTS r ON r.promotion_id = p.promotion_id
    GROUP BY p.promotion_id, p.promotion_name, p.banner, p.category_name, p.mechanic, p.discount_pct, p.start_date, p.end_date, p.weeks,
             p.funding_source, p.supplier_funding_pct, p.is_loyalty_only, p.objective, p.owner
)
SELECT
    a.*,
    a.baseline_gp_pct - a.promo_gp_pct                                   AS margin_dilution_pts,
    ROW_NUMBER() OVER (ORDER BY a.uplift_pct DESC)                       AS uplift_rank,
    ROW_NUMBER() OVER (ORDER BY (a.baseline_gp_pct - a.promo_gp_pct) DESC) AS margin_rank_from_bottom,
    CASE WHEN a.uplift_pct >= 0.25 AND (a.baseline_gp_pct - a.promo_gp_pct) >= 0.04 THEN 'Strong sales weak margin'
         WHEN a.uplift_pct >= 0.25 THEN 'Strong sales healthy margin'
         WHEN (a.baseline_gp_pct - a.promo_gp_pct) >= 0.04 THEN 'Weak sales weak margin'
         ELSE 'Modest' END                                               AS promo_verdict
FROM agg a;

CREATE OR REPLACE VIEW V_AVAILABILITY_VS_SALES
    COMMENT = 'Availability versus sales by store and category over the last 13 weeks (weeks starting 2026-06-29 to 2026-09-21): on-shelf availability, stockout hours, waste and markdown rates, category sales growth versus the same 13 weeks a year earlier, and the store like-for-like growth over the rolling 12 months. low_availability_flag = OSA below the 0.94 threshold. Use to find where availability issues line up with weak sales.'
AS
WITH last13 AS (
    SELECT w.store_id, w.category_id,
           SUM(w.net_sales_sek) AS net_sales_13w_sek,
           SUM(w.on_shelf_availability_pct * w.net_sales_sek) / NULLIF(SUM(w.net_sales_sek), 0) AS osa_pct,
           SUM(w.stockout_hours) AS stockout_hours,
           SUM(w.waste_sek) / NULLIF(SUM(w.net_sales_sek), 0) AS waste_rate,
           SUM(w.markdown_sek) / NULLIF(SUM(w.net_sales_sek), 0) AS markdown_rate,
           AVG(w.inventory_days) AS inventory_days
    FROM SALES_WEEKLY_STORE_CATEGORY w
    WHERE w.week_start_date >= DATE '2026-06-29' AND w.week_start_date <= DATE '2026-09-21'
    GROUP BY w.store_id, w.category_id
),
ly13 AS (
    SELECT w.store_id, w.category_id, SUM(w.net_sales_sek) AS net_sales_ly13_sek
    FROM SALES_WEEKLY_STORE_CATEGORY w
    WHERE w.week_start_date >= DATE '2025-06-30' AND w.week_start_date <= DATE '2025-09-22'
    GROUP BY w.store_id, w.category_id
),
store_lfl AS (
    SELECT d.store_id,
           SUM(CASE WHEN c.rolling_12m_bucket = 'R12_CUR' THEN d.net_sales_sek ELSE 0 END) AS cur_sales,
           SUM(CASE WHEN c.rolling_12m_bucket = 'R12_PRIOR' THEN d.net_sales_sek ELSE 0 END) AS prior_sales
    FROM STORE_DAILY_SALES d JOIN CALENDAR c ON c.calendar_date = d.calendar_date
    WHERE c.rolling_12m_bucket IS NOT NULL
    GROUP BY d.store_id
)
SELECT
    s.store_id, s.store_name, s.banner, s.region, s.catchment_type, s.peer_cluster, s.is_lfl_comparable,
    pc.category_id, pc.category_name, pc.department, pc.is_fresh,
    l.net_sales_13w_sek,
    y.net_sales_ly13_sek,
    l.net_sales_13w_sek / NULLIF(y.net_sales_ly13_sek, 0) - 1            AS category_sales_growth_pct,
    l.osa_pct,
    l.stockout_hours,
    l.waste_rate,
    l.markdown_rate,
    l.inventory_days,
    CASE WHEN l.osa_pct < 0.94 THEN TRUE ELSE FALSE END                   AS low_availability_flag,
    CASE WHEN s.is_lfl_comparable THEN sl.cur_sales / NULLIF(sl.prior_sales, 0) - 1 END AS store_lfl_growth_pct
FROM last13 l
JOIN STORES s ON s.store_id = l.store_id
JOIN PRODUCT_CATEGORIES pc ON pc.category_id = l.category_id
LEFT JOIN ly13 y ON y.store_id = l.store_id AND y.category_id = l.category_id
LEFT JOIN store_lfl sl ON sl.store_id = l.store_id;

CREATE OR REPLACE VIEW V_LOYALTY_SEGMENT_TRENDS
    COMMENT = 'Loyalty trends by store and customer segment: rolling-12-month active members, visits, spend and visit frequency versus the prior 12 months, with change percentages. Which segments visit less or spend less, and where.'
AS
WITH w AS (
    SELECT l.store_id, l.segment, c.rolling_12m_bucket,
           AVG(l.active_members) AS active_members, SUM(l.visits) AS visits, SUM(l.spend_sek) AS spend_sek,
           SUM(l.new_members) AS new_members, SUM(l.lapsed_members) AS lapsed_members
    FROM LOYALTY_ACTIVITY_MONTHLY l
    JOIN CALENDAR c ON c.calendar_date = l.month_start_date
    WHERE c.rolling_12m_bucket IS NOT NULL
    GROUP BY l.store_id, l.segment, c.rolling_12m_bucket
)
SELECT
    s.store_id, s.store_name, s.banner, s.region, s.catchment_type, s.peer_cluster,
    cur.segment,
    cur.active_members                                                  AS active_members_r12,
    pri.active_members                                                  AS active_members_prior_r12,
    cur.active_members / NULLIF(pri.active_members, 0) - 1              AS active_members_change_pct,
    cur.visits                                                          AS visits_r12,
    pri.visits                                                          AS visits_prior_r12,
    cur.visits * 1.0 / NULLIF(pri.visits, 0) - 1                        AS visits_change_pct,
    cur.spend_sek                                                       AS spend_r12_sek,
    pri.spend_sek                                                       AS spend_prior_r12_sek,
    cur.spend_sek / NULLIF(pri.spend_sek, 0) - 1                        AS spend_change_pct,
    cur.visits / NULLIF(cur.active_members, 0)                          AS visits_per_member_r12,
    pri.visits / NULLIF(pri.active_members, 0)                          AS visits_per_member_prior_r12,
    cur.spend_sek / NULLIF(cur.visits, 0)                               AS spend_per_visit_r12_sek,
    cur.new_members                                                     AS new_members_r12,
    cur.lapsed_members                                                  AS lapsed_members_r12
FROM w cur
JOIN w pri ON pri.store_id = cur.store_id AND pri.segment = cur.segment AND pri.rolling_12m_bucket = 'R12_PRIOR'
JOIN STORES s ON s.store_id = cur.store_id
WHERE cur.rolling_12m_bucket = 'R12_CUR';

CREATE OR REPLACE VIEW V_NONFOOD_AVAILABILITY_BY_SUPPLIER
    COMMENT = 'Grosshallen imported non-food availability by store, month and supplier_key: SKUs ranged, units and sales, availability, stockout days and lost sales. supplier_key is the key of the import-purchasing platform on Teradata: join to wisdomai.RTL_DIM_SUPPLIER (name, country, lead time, on-time rate) and wisdomai.RTL_FACT_PURCHASE_ORDER_LINE (days_late, po_status) to explain lost sales with late inbound purchase orders.'
AS
SELECT
    s.store_id,
    s.store_name,
    s.region,
    s.catchment_type,
    a.month_start_date,
    n.supplier_key,
    n.teradata_department,
    n.category_name,
    COUNT(DISTINCT a.product_key)                                       AS skus,
    SUM(a.units_sold)                                                   AS units_sold,
    SUM(a.net_sales_sek)                                                AS net_sales_sek,
    SUM(a.on_shelf_availability_pct * (a.net_sales_sek + a.lost_sales_sek)) / NULLIF(SUM(a.net_sales_sek + a.lost_sales_sek), 0) AS osa_pct,
    SUM(a.stockout_days)                                                AS stockout_days,
    SUM(a.lost_sales_sek)                                               AS lost_sales_sek,
    SUM(a.lost_sales_sek) / NULLIF(SUM(a.net_sales_sek + a.lost_sales_sek), 0) AS lost_sales_share
FROM NONFOOD_AVAILABILITY_MONTHLY a
JOIN NONFOOD_ASSORTMENT n ON n.product_key = a.product_key
JOIN STORES s ON s.store_id = a.store_id
GROUP BY s.store_id, s.store_name, s.region, s.catchment_type, a.month_start_date, n.supplier_key, n.teradata_department, n.category_name;

-- SECTION 5: CAMPAIGNS AND FORECASTS (Revision 2, 2026-10-27) ---------------
-- The campaign planners' "Kampanjrapport": campaign performance and forecast accuracy
-- by chain (kedja) and week (vecka). Swedish business terms in the identifiers (ASCII),
-- English descriptions. Forecast error = (forecast - actual sold) / actual sold, positive
-- = over-forecast. Campaign week = the ISO week of the first delivery day (leverans_fran).
-- Cost data in ARTIKEL_KOSTNAD_MANAD is ILLUSTRATIVE (finance not yet migrated).

CREATE OR REPLACE TABLE ARTIKEL (
    artikel_id             VARCHAR(10)  NOT NULL PRIMARY KEY  COMMENT 'Article id (Artikel) A-nnnnn, the article master key',
    artikel_namn           VARCHAR(80)  NOT NULL              COMMENT 'Article name: brand, product and pack size, e.g. Fjällmejeriet Mellanmjölk 1,5% 1 l',
    category_id            VARCHAR(6)   NOT NULL REFERENCES PRODUCT_CATEGORIES(category_id) COMMENT 'Product category of the article',
    kategori               VARCHAR(40)  NOT NULL              COMMENT 'Category name (Kategori), copied from PRODUCT_CATEGORIES.category_name',
    varumarke              VARCHAR(40)  NOT NULL              COMMENT 'Brand (Varumärke); Nordmark and Nordmark Eko are the private labels',
    egna_markesvaror       BOOLEAN      NOT NULL              COMMENT 'TRUE for private label (egna märkesvaror, EMV)',
    farskvara              BOOLEAN      NOT NULL              COMMENT 'TRUE for perishables (färskvara): fresh produce, dairy, bread, meat, fish, deli, ready meals, flowers',
    hallbarhet_dagar       NUMBER(4,0)  NOT NULL              COMMENT 'Shelf life in days (hållbarhet)',
    enhet                  VARCHAR(10)  NOT NULL              COMMENT 'Selling unit (enhet): st = piece, kg, l',
    kolli                  NUMBER(4,0)  NOT NULL              COMMENT 'Units per case (kolli); the order unit',
    lav                    NUMBER(3,0)  NOT NULL              COMMENT 'Cases per pallet layer (lav); order adjustments are rounded to whole layers',
    pall                   NUMBER(4,0)  NOT NULL              COMMENT 'Cases per pallet (pall)',
    ordinarie_pris_sek     NUMBER(9,2)  NOT NULL              COMMENT 'Regular shelf price in SEK excluding VAT (ordinarie pris)',
    status                 VARCHAR(12)  NOT NULL              COMMENT 'Aktiv or Utgaende (being delisted)'
) COMMENT = 'Article master (Artikel) for the grocery and household range: category, brand, private label, perishability, shelf life, packaging units (kolli, lav, pall) and regular price.';

CREATE OR REPLACE TABLE KAMPANJ (
    kampanj_id             VARCHAR(16)  NOT NULL PRIMARY KEY  COMMENT 'Campaign id K-yyyy-www-banner[-n], e.g. K-2026-036-KRM-2 when a banner runs several campaigns in one week',
    kampanj_namn           VARCHAR(60)  NOT NULL              COMMENT 'Campaign name (Kampanj), e.g. Höstskörd 3 för 2',
    kedja                  VARCHAR(20)  NOT NULL              COMMENT 'Chain (Kedja) = banner name: Kronmat, Torghallen or Grosshallen',
    banner_id              VARCHAR(4)   NOT NULL REFERENCES BANNERS(banner_id) COMMENT 'Banner code',
    koncept_kod            VARCHAR(8)   NOT NULL              COMMENT 'Chain concept code (Concept_Cd) = banner code + tactic code',
    taktik_typ_kod         VARCHAR(4)   NOT NULL              COMMENT 'Tactic type code (Tactic_Type_Cd): PN, MK, MP, HP, KU',
    taktik_typ             VARCHAR(30)  NOT NULL              COMMENT 'Tactic type (Tactic_Type_Desc), the promotion mechanic used to group campaigns: Prisnedsättning, Multiköp 3 för 2, Medlemspris, Halva priset, Kupong',
    kalender_vecka_id      NUMBER(6,0)  NOT NULL              COMMENT 'Campaign week key (Calendar_Week_Id, YYYYWW) = ISO week of the first delivery day',
    vecka_label            VARCHAR(8)   NOT NULL              COMMENT 'Campaign week label (Vecka), e.g. 2026-W36',
    leverans_fran          DATE         NOT NULL              COMMENT 'First delivery day of the campaign goods (Delivery_From)',
    leverans_till          DATE         NOT NULL              COMMENT 'Last delivery day (Delivery_To)',
    kampanj_start          DATE         NOT NULL              COMMENT 'First selling day of the campaign (Monday)',
    kampanj_slut           DATE         NOT NULL              COMMENT 'Last selling day of the campaign (Sunday)',
    antal_veckor           NUMBER(1,0)  NOT NULL              COMMENT 'Campaign length in weeks (1 or 2)',
    antal_artiklar         NUMBER(3,0)  NOT NULL              COMMENT 'Number of articles in the campaign',
    promotion_id           VARCHAR(8)   REFERENCES PROMOTIONS(promotion_id) COMMENT 'Category promotion in PROMOTIONS that this campaign belongs to, when it overlaps one (e.g. Sommarpris 2026)',
    tema                   VARCHAR(40)  NOT NULL              COMMENT 'Campaign theme, e.g. Fredagsmys, Höstskörd, Julbord',
    ansvarig_planerare     VARCHAR(40)  NOT NULL              COMMENT 'Responsible campaign planner (fictional)',
    status                 VARCHAR(12)  NOT NULL              COMMENT 'Avslutad (completed), Pagaende (running at the as-of date) or Planerad (planned, no actuals yet)'
) COMMENT = 'Campaigns (Kampanj) by chain and week with tactic type, delivery window and planner. Planned campaigns for weeks 2026-W41..W44 have forecasts but no actual sales yet.';

CREATE OR REPLACE TABLE ARTIKEL_KOSTNAD_MANAD (
    artikel_id             VARCHAR(10)  NOT NULL REFERENCES ARTIKEL(artikel_id) COMMENT 'Article',
    manad                  DATE         NOT NULL              COMMENT 'Month (first day)',
    inkopspris_sek         NUMBER(9,2)  NOT NULL              COMMENT 'Purchase cost per unit in SEK (inköpspris); illustrative',
    listpris_sek           NUMBER(9,2)  NOT NULL              COMMENT 'List selling price per unit in SEK excluding VAT (listpris); illustrative',
    marginal_pct           NUMBER(6,4)  NOT NULL              COMMENT 'Gross margin percent = 1 - purchase cost / list price (0-1); illustrative',
    svinnandel_pct         NUMBER(6,4)  NOT NULL              COMMENT 'Share of over-bought units written off as waste (svinn) for perishables, by shelf life; 0 for dry goods',
    kalla                  VARCHAR(60)  NOT NULL              COMMENT 'Source label: always ILLUSTRATIV - finanssystem ej migrerat',
    PRIMARY KEY (artikel_id, manad)
) COMMENT = 'ILLUSTRATIVE article cost and margin by month. Purchase cost and margin live in the finance system (SAP BW-type) that is not yet migrated into the warehouse, so these figures are a labelled synthetic stand-in; every answer that uses them must say so.';

CREATE OR REPLACE TABLE KAMPANJ_ARTIKEL_VECKA (
    nyckel                 VARCHAR(20)  NOT NULL              COMMENT 'Report key (Nyckel) = campaign week label || - || article id, e.g. 2026-W36-A-00012',
    kampanj_id             VARCHAR(16)  NOT NULL REFERENCES KAMPANJ(kampanj_id) COMMENT 'Campaign',
    kedja                  VARCHAR(20)  NOT NULL              COMMENT 'Chain (Kedja)',
    kalender_vecka_id      NUMBER(6,0)  NOT NULL              COMMENT 'Campaign week key (Calendar_Week_Id, YYYYWW)',
    vecka_label            VARCHAR(8)   NOT NULL              COMMENT 'Week label (Vecka), e.g. 2026-W36',
    vecka_start            DATE         NOT NULL              COMMENT 'Monday of the campaign week',
    artikel_id             VARCHAR(10)  NOT NULL REFERENCES ARTIKEL(artikel_id) COMMENT 'Article',
    planerad_kvantitet     NUMBER(10,0) NOT NULL              COMMENT 'Planned campaign quantity (Quantity): the purchase forecast rounded up to whole cases',
    sald_prognos_catboost  NUMBER(10,0) NOT NULL              COMMENT 'Sold forecast (Såld prognos - CatBoost) from the group demand model, units',
    kopt_prognos_kedjan    NUMBER(10,0) NOT NULL              COMMENT 'Purchase forecast (Köpt prognos - KEDJANS PROGNOS) from the chain own plan, units',
    levererad_kvantitet    NUMBER(10,0)                       COMMENT 'Units delivered to stores; NULL for weeks after the as-of date',
    faktisk_sald           NUMBER(10,0)                       COMMENT 'Actual units sold in the campaign week (faktisk såld); NULL for weeks after the as-of date 2026-09-30',
    kampanjpris_sek        NUMBER(9,2)  NOT NULL              COMMENT 'Campaign selling price per unit in SEK excluding VAT',
    ordinarie_pris_sek     NUMBER(9,2)  NOT NULL              COMMENT 'Regular price per unit in SEK excluding VAT',
    kampanjforsaljning_sek NUMBER(12,2)                       COMMENT 'Campaign sales in SEK = actual units sold x campaign price; NULL for future weeks',
    PRIMARY KEY (kampanj_id, kalender_vecka_id, artikel_id)
) COMMENT = 'The grain of the Kampanjrapport: one row per campaign week and article with planned quantity, the CatBoost sold forecast, the chain purchase forecast, deliveries and actual sales. Weeks 2026-W40..W44 have no actuals.';

CREATE OR REPLACE TABLE KAMPANJ_BUTIK_VECKA (
    kampanj_id             VARCHAR(16)  NOT NULL REFERENCES KAMPANJ(kampanj_id) COMMENT 'Campaign',
    kedja                  VARCHAR(20)  NOT NULL              COMMENT 'Chain (Kedja)',
    store_id               VARCHAR(8)   NOT NULL REFERENCES STORES(store_id) COMMENT 'Store (Butik)',
    kalender_vecka_id      NUMBER(6,0)  NOT NULL              COMMENT 'Campaign week key (YYYYWW)',
    vecka_label            VARCHAR(8)   NOT NULL              COMMENT 'Week label, e.g. 2026-W36',
    vecka_start            DATE         NOT NULL              COMMENT 'Monday of the campaign week',
    prognos_kvantitet      NUMBER(10,0) NOT NULL              COMMENT 'Chain purchase forecast allocated to the store by store size, all campaign articles, units',
    faktisk_sald           NUMBER(10,0) NOT NULL              COMMENT 'Actual campaign units sold in the store in the week',
    avvikelse_pct          NUMBER(8,4)  NOT NULL              COMMENT 'Store forecast deviation = (forecast - actual) / actual; positive = over-forecast',
    PRIMARY KEY (kampanj_id, store_id, kalender_vecka_id)
) COMMENT = 'Campaign forecast versus actual by store and week (completed weeks only), for drilling a forecast variance to the store level.';

CREATE OR REPLACE VIEW V_KAMPANJRAPPORT
    COMMENT = 'The Kampanjrapport grid: campaign performance and forecast accuracy by chain and week, one row per campaign week and article (Nyckel). Filters: kedja, vecka_label or kalender_vecka_id, kampanj_namn, taktik_typ. Forecast error = (forecast - actual sold) / actual sold; rows for future weeks have NULL actuals and ar_avslutad = FALSE.'
AS
SELECT
    r.kedja,
    r.kalender_vecka_id,
    r.vecka_label,
    r.vecka_start,
    r.kampanj_id,
    k.kampanj_namn,
    k.taktik_typ_kod,
    k.taktik_typ,
    r.nyckel,
    r.artikel_id,
    a.artikel_namn,
    a.kategori,
    a.farskvara,
    a.egna_markesvaror,
    r.planerad_kvantitet,
    r.sald_prognos_catboost,
    r.kopt_prognos_kedjan,
    r.levererad_kvantitet,
    r.faktisk_sald,
    (r.sald_prognos_catboost - r.faktisk_sald) / NULLIF(r.faktisk_sald, 0)           AS prognosfel_catboost_pct,
    (r.kopt_prognos_kedjan - r.faktisk_sald) / NULLIF(r.faktisk_sald, 0)             AS prognosfel_kedjan_pct,
    GREATEST(r.kopt_prognos_kedjan - r.faktisk_sald, 0)                               AS overprognos_kvantitet,
    r.kampanjpris_sek,
    r.kampanjforsaljning_sek,
    CASE WHEN r.faktisk_sald IS NOT NULL THEN TRUE ELSE FALSE END                     AS ar_avslutad
FROM KAMPANJ_ARTIKEL_VECKA r
JOIN KAMPANJ k ON k.kampanj_id = r.kampanj_id
JOIN ARTIKEL a ON a.artikel_id = r.artikel_id;

CREATE OR REPLACE VIEW V_PROGNOSFEL_TAKTIK
    COMMENT = 'Forecast bias by chain, tactic type, perishability and campaign week (completed weeks only): bias = SUM(forecast) / SUM(actual sold) - 1 for the chain plan (kedjan) and the CatBoost model; abs_fel_kedjan is the summed absolute error of the chain plan in units.'
AS
SELECT
    r.kedja,
    k.taktik_typ_kod,
    k.taktik_typ,
    a.farskvara,
    r.kalender_vecka_id,
    r.vecka_label,
    COUNT(*)                                                                           AS artiklar,
    SUM(r.faktisk_sald)                                                                AS faktisk_sald,
    SUM(r.sald_prognos_catboost)                                                       AS sald_prognos_catboost,
    SUM(r.kopt_prognos_kedjan)                                                         AS kopt_prognos_kedjan,
    (SUM(r.sald_prognos_catboost) - SUM(r.faktisk_sald)) / NULLIF(SUM(r.faktisk_sald), 0) AS bias_catboost_pct,
    (SUM(r.kopt_prognos_kedjan) - SUM(r.faktisk_sald)) / NULLIF(SUM(r.faktisk_sald), 0)   AS bias_kedjan_pct,
    SUM(ABS(r.kopt_prognos_kedjan - r.faktisk_sald))                                   AS abs_fel_kedjan,
    SUM(GREATEST(r.kopt_prognos_kedjan - r.faktisk_sald, 0))                           AS overprognos_kvantitet
FROM KAMPANJ_ARTIKEL_VECKA r
JOIN KAMPANJ k ON k.kampanj_id = r.kampanj_id
JOIN ARTIKEL a ON a.artikel_id = r.artikel_id
WHERE r.faktisk_sald IS NOT NULL
GROUP BY r.kedja, k.taktik_typ_kod, k.taktik_typ, a.farskvara, r.kalender_vecka_id, r.vecka_label;

CREATE OR REPLACE VIEW V_KAMPANJ_BUTIK_AVVIKELSE
    COMMENT = 'Campaign forecast deviation by store and week with store attributes and a flag for a competitor event within 2 km in the 90 days before the campaign week. avvikelse_pct = (forecast - actual) / actual; positive = over-forecast.'
AS
SELECT
    b.kampanj_id,
    k.kampanj_namn,
    k.taktik_typ,
    b.kedja,
    b.store_id,
    s.store_name,
    s.banner,
    s.region,
    s.peer_cluster,
    s.catchment_type,
    b.kalender_vecka_id,
    b.vecka_label,
    b.vecka_start,
    b.prognos_kvantitet,
    b.faktisk_sald,
    b.avvikelse_pct,
    CASE WHEN EXISTS (SELECT 1 FROM COMPETITOR_EVENTS e
                      WHERE e.store_id = b.store_id AND e.distance_km <= 2.0
                        AND e.event_date < b.vecka_start AND e.event_date >= b.vecka_start - 90)
         THEN TRUE ELSE FALSE END                                                      AS har_konkurrenthandelse_90d
FROM KAMPANJ_BUTIK_VECKA b
JOIN KAMPANJ k ON k.kampanj_id = b.kampanj_id
JOIN STORES s ON s.store_id = b.store_id;

CREATE OR REPLACE VIEW V_KAMPANJ_MARGINALEFFEKT
    COMMENT = 'Margin cost of over-forecasting per campaign, week and perishability (ILLUSTRATIVE cost data, see kalla): over-bought units = purchase forecast - actual sold; waste cost = units x purchase cost x waste share (perishables); markdown cost = remaining units x half the campaign discount; marginaleffekt_sek = waste + markdown.'
AS
SELECT
    r.kampanj_id,
    k.kampanj_namn,
    r.kedja,
    k.taktik_typ,
    r.vecka_label,
    c.quarter_label,
    a.farskvara,
    SUM(GREATEST(r.kopt_prognos_kedjan - r.faktisk_sald, 0))                                                           AS overprognos_kvantitet,
    SUM(GREATEST(r.kopt_prognos_kedjan - r.faktisk_sald, 0) * m.inkopspris_sek * m.svinnandel_pct)                     AS svinnkostnad_sek,
    SUM(GREATEST(r.kopt_prognos_kedjan - r.faktisk_sald, 0) * (1 - m.svinnandel_pct) * (r.ordinarie_pris_sek - r.kampanjpris_sek) * 0.5) AS nedsattningskostnad_sek,
    SUM(GREATEST(r.kopt_prognos_kedjan - r.faktisk_sald, 0) * m.inkopspris_sek * m.svinnandel_pct)
      + SUM(GREATEST(r.kopt_prognos_kedjan - r.faktisk_sald, 0) * (1 - m.svinnandel_pct) * (r.ordinarie_pris_sek - r.kampanjpris_sek) * 0.5) AS marginaleffekt_sek,
    MAX(m.kalla)                                                                                                        AS kalla
FROM KAMPANJ_ARTIKEL_VECKA r
JOIN KAMPANJ k ON k.kampanj_id = r.kampanj_id
JOIN ARTIKEL a ON a.artikel_id = r.artikel_id
JOIN CALENDAR c ON c.calendar_date = r.vecka_start
JOIN ARTIKEL_KOSTNAD_MANAD m ON m.artikel_id = r.artikel_id AND m.manad = c.month_start_date
WHERE r.faktisk_sald IS NOT NULL
GROUP BY r.kampanj_id, k.kampanj_namn, r.kedja, k.taktik_typ, r.vecka_label, c.quarter_label, a.farskvara;

CREATE OR REPLACE VIEW V_KAMPANJ_KOMMANDE
    COMMENT = 'Upcoming campaign weeks after the as-of date 2026-09-30 with both forecasts: prognosgap_pct = chain purchase forecast / CatBoost - 1; flagga = perishable and gap above 15 percent; foreslagen_minskning_kolli = proposed purchase cut in whole cases rounded down to full layers; skyddad_marginal_sek = waste cost avoided (ILLUSTRATIVE cost data).'
AS
SELECT
    kampanj_id, kampanj_namn, kedja, taktik_typ, vecka_label, leverans_fran, dagar_till_leverans, artikel_id, artikel_namn, kategori, farskvara, kolli, lav,
    planerad_kvantitet, sald_prognos_catboost, kopt_prognos_kedjan, prognosgap_pct,
    CASE WHEN farskvara AND prognosgap_pct > 0.15 THEN TRUE ELSE FALSE END                                             AS flagga,
    FLOOR(GREATEST(kopt_prognos_kedjan - sald_prognos_catboost, 0) / kolli / lav) * lav                                AS foreslagen_minskning_kolli,
    inkopspris_sek,
    FLOOR(GREATEST(kopt_prognos_kedjan - sald_prognos_catboost, 0) / kolli / lav) * lav * kolli * inkopspris_sek * svinnandel_pct AS skyddad_marginal_sek,
    kalla
FROM (
    SELECT
        r.kampanj_id, k.kampanj_namn, r.kedja, k.taktik_typ, r.vecka_label, k.leverans_fran,
        k.leverans_fran - DATE '2026-09-30'                                                                               AS dagar_till_leverans,
        r.artikel_id, a.artikel_namn, a.kategori, a.farskvara, a.kolli, a.lav,
        r.planerad_kvantitet, r.sald_prognos_catboost, r.kopt_prognos_kedjan,
        r.kopt_prognos_kedjan / NULLIF(r.sald_prognos_catboost, 0) - 1                                                    AS prognosgap_pct,
        m.inkopspris_sek, m.svinnandel_pct, m.kalla
    FROM KAMPANJ_ARTIKEL_VECKA r
    JOIN KAMPANJ k ON k.kampanj_id = r.kampanj_id
    JOIN ARTIKEL a ON a.artikel_id = r.artikel_id
    JOIN CALENDAR c ON c.calendar_date = k.leverans_fran
    JOIN ARTIKEL_KOSTNAD_MANAD m ON m.artikel_id = r.artikel_id AND m.manad = c.month_start_date
    WHERE r.vecka_start > DATE '2026-09-30'
) x;
