-- ============================================================================
-- WisdomAI POC — Harborline Private Capital
-- Snowflake DDL
-- Domain: fictional producer of private-capital benchmarks and indices (the
--   Harborline Private Capital Index family, HPCI). Fund cash flows and NAVs are
--   contributed by LPs and GPs; figures are also extracted from fund quarterly
--   reports; allocator clients compare their commitments to the indices.
-- Demo "today": 2026-10-15. Latest reported quarter: Q2 2026 (2026-06-30).
-- Data spans 2012-01-01 .. 2026-06-30 (vintages 2012-2024). All money in USD millions.
-- ============================================================================

-- SECTION 0: ENVIRONMENT SETUP -------------------------------------------------
USE ROLE SYSADMIN;
CREATE DATABASE IF NOT EXISTS HARBORLINE_POC
    COMMENT = 'WisdomAI POC database for the Harborline Private Capital demo';
CREATE SCHEMA IF NOT EXISTS HARBORLINE_POC.ANALYTICS
    COMMENT = 'Harborline private-capital analytics: funds, cash flows, NAVs, benchmarks, allocator commitments, report extractions';
USE DATABASE HARBORLINE_POC;
USE SCHEMA ANALYTICS;

-- SECTION 1: DIMENSION TABLES -------------------------------------------------

CREATE OR REPLACE TABLE MANAGERS (
    MANAGER_ID              VARCHAR(10)   NOT NULL PRIMARY KEY COMMENT 'General partner identifier (MGR-001 ...)',
    MANAGER_NAME            VARCHAR(80)   NOT NULL COMMENT 'General partner (fund manager) firm name',
    HEADQUARTERS_CITY       VARCHAR(40)   COMMENT 'City of the manager headquarters',
    HEADQUARTERS_COUNTRY    VARCHAR(40)   COMMENT 'Country of the manager headquarters',
    FOUNDED_YEAR            NUMBER(4,0)   COMMENT 'Year the firm was founded',
    PRIMARY_STRATEGY        VARCHAR(20)   COMMENT 'Strategy the firm is best known for: Buyout, Growth, Venture, Private Credit, Real Estate, Infrastructure',
    FIRM_AUM_USD_B          NUMBER(8,1)   COMMENT 'Firm-wide assets under management in USD billions (approximate, as reported)',
    IS_HPCI_CONTRIBUTOR     BOOLEAN       COMMENT 'TRUE when the manager contributes fund-level cash flows directly to Harborline'
) COMMENT = 'General partners (fund managers). One row per firm.';

CREATE OR REPLACE TABLE BENCHMARKS (
    BENCHMARK_ID            VARCHAR(20)   NOT NULL PRIMARY KEY COMMENT 'Harborline index identifier (HPCI-BROAD-PE, HPCI-BUYOUT-NA ...)',
    BENCHMARK_NAME          VARCHAR(80)   NOT NULL COMMENT 'Published index name',
    STRATEGY                VARCHAR(30)   COMMENT 'Strategy the index covers: Buyout, Growth, Venture, Private Credit, Real Estate, Infrastructure, All Private Equity, All Private Capital',
    REGION                  VARCHAR(20)   COMMENT 'Region the index covers: North America, Europe, Asia-Pacific, Global',
    CONSTITUENT_RULE        VARCHAR(300)  COMMENT 'Plain-language rule for which funds are constituents',
    INCEPTION_DATE          DATE          COMMENT 'First quarter the index was published for',
    IS_BROAD_INDEX          BOOLEAN       COMMENT 'TRUE for the two headline indices (Broad Private Equity and Private Capital Composite)'
) COMMENT = 'The Harborline Private Capital Index (HPCI) family. One row per published index.';

CREATE OR REPLACE TABLE FUNDS (
    FUND_ID                 VARCHAR(10)   NOT NULL PRIMARY KEY COMMENT 'Fund identifier (FND-0001 ...)',
    FUND_NAME               VARCHAR(100)  NOT NULL COMMENT 'Fund legal name as contributed',
    MANAGER_ID              VARCHAR(10)   NOT NULL REFERENCES MANAGERS(MANAGER_ID) COMMENT 'General partner that manages the fund',
    STRATEGY                VARCHAR(20)   NOT NULL COMMENT 'Fund strategy: Buyout, Growth, Venture, Private Credit, Real Estate, Infrastructure',
    REGION                  VARCHAR(20)   NOT NULL COMMENT 'Primary investment region: North America, Europe, Asia-Pacific, Global',
    VINTAGE_YEAR            NUMBER(4,0)   NOT NULL COMMENT 'Vintage year = year of the first capital call (Harborline convention)',
    FIRST_CLOSE_DATE        DATE          COMMENT 'Date of the fund first close',
    FIRST_CALL_DATE         DATE          COMMENT 'Date of the first capital call; defines the vintage year',
    FUND_SIZE_USD_M         NUMBER(10,1)  NOT NULL COMMENT 'Total LP commitments (fund size) in USD millions',
    SIZE_BUCKET             VARCHAR(20)   NOT NULL COMMENT 'Size bucket by fund size: SMALL (under 1B), MID_MARKET (1B to 5B), MEGA (over 5B)',
    BASE_CURRENCY           VARCHAR(3)    COMMENT 'Fund base currency (USD, EUR, GBP, JPY, AUD); all amounts in this schema are converted to USD',
    USES_SUBSCRIPTION_LINE  BOOLEAN       NOT NULL COMMENT 'TRUE when the fund uses a subscription credit line (line of credit secured on LP commitments) to bridge capital calls',
    SUBSCRIPTION_LINE_LIMIT_USD_M NUMBER(10,1) COMMENT 'Committed size of the subscription credit line in USD millions; NULL when the fund has no line',
    FUND_STATUS             VARCHAR(15)   COMMENT 'Lifecycle status at the latest quarter: INVESTING, HARVESTING, LIQUIDATED',
    BENCHMARK_ID            VARCHAR(20)   NOT NULL REFERENCES BENCHMARKS(BENCHMARK_ID) COMMENT 'The matching Harborline strategy and region index for this fund',
    DATA_SOURCE             VARCHAR(30)   COMMENT 'How Harborline receives the fund data: LP contribution, GP contribution, Report extraction'
) COMMENT = 'Private-capital funds covered by Harborline. One row per fund. Fund size is total LP commitments.';

CREATE OR REPLACE TABLE ALLOCATORS (
    ALLOCATOR_ID            VARCHAR(10)   NOT NULL PRIMARY KEY COMMENT 'Allocator client identifier (ALC-001 ...)',
    ALLOCATOR_NAME          VARCHAR(80)   NOT NULL COMMENT 'Allocator (limited partner client) name',
    ALLOCATOR_TYPE          VARCHAR(30)   COMMENT 'Public pension, Endowment, Insurance, Family office, Sovereign wealth fund',
    HEADQUARTERS            VARCHAR(60)   COMMENT 'City and country of the allocator',
    TOTAL_PC_COMMITMENT_USD_M NUMBER(10,1) COMMENT 'Total private-capital commitments across all funds in USD millions (as reported to Harborline)',
    PORTAL_TIER             VARCHAR(30)   COMMENT 'Harborline portal subscription tier: Standard or Premium Analytics'
) COMMENT = 'Allocator clients (limited partners) who subscribe to the Harborline portal. One row per client.';

-- SECTION 2: FACT TABLES (FK order) -------------------------------------------

CREATE OR REPLACE TABLE ALLOCATOR_COMMITMENTS (
    COMMITMENT_ID           VARCHAR(12)   NOT NULL PRIMARY KEY COMMENT 'Commitment identifier (CMT-0001 ...)',
    ALLOCATOR_ID            VARCHAR(10)   NOT NULL REFERENCES ALLOCATORS(ALLOCATOR_ID) COMMENT 'Allocator that made the commitment',
    FUND_ID                 VARCHAR(10)   NOT NULL REFERENCES FUNDS(FUND_ID) COMMENT 'Fund the allocator committed to',
    COMMITMENT_USD_M        NUMBER(10,1)  NOT NULL COMMENT 'Amount committed by the allocator to the fund in USD millions',
    COMMITMENT_DATE         DATE          COMMENT 'Date the commitment was signed'
) COMMENT = 'Allocator commitments to funds (the client portfolio). One row per allocator and fund.';

CREATE OR REPLACE TABLE FUND_QUARTERLY_NAV (
    FUND_ID                 VARCHAR(10)   NOT NULL REFERENCES FUNDS(FUND_ID) COMMENT 'Fund',
    QUARTER_END             DATE          NOT NULL COMMENT 'Quarter-end date the figures are reported as of',
    FUND_AGE_QUARTERS       NUMBER(3,0)   NOT NULL COMMENT 'Quarters since the first capital call (1 = the quarter of the first call)',
    NAV_USD_M               NUMBER(12,1)  NOT NULL COMMENT 'Net asset value attributable to LPs at quarter end in USD millions (net of the subscription line balance)',
    CUMULATIVE_CALLED_USD_M NUMBER(12,1)  NOT NULL COMMENT 'Cumulative capital called from LPs since inception in USD millions (paid-in capital)',
    CUMULATIVE_DISTRIBUTED_USD_M NUMBER(12,1) NOT NULL COMMENT 'Cumulative distributions to LPs since inception in USD millions',
    PAID_IN_PCT             NUMBER(6,2)   COMMENT 'Cumulative called as a percent of fund size (commitments)',
    CREDIT_LINE_BALANCE_USD_M NUMBER(12,1) COMMENT 'Subscription credit line balance drawn at quarter end in USD millions (0 when no line or nothing drawn)',
    IRR_SINCE_INCEPTION_PCT NUMBER(6,2)   COMMENT 'Net since-inception IRR to LPs in percent as of the quarter end (NULL before the first capital call)',
    TVPI                    NUMBER(6,3)   COMMENT 'Total value to paid-in: (NAV + cumulative distributions) / cumulative called',
    DPI                     NUMBER(6,3)   COMMENT 'Distributions to paid-in: cumulative distributions / cumulative called',
    RVPI                    NUMBER(6,3)   COMMENT 'Residual value to paid-in: NAV / cumulative called',
    QUARTERLY_RETURN_PCT    NUMBER(6,2)   COMMENT 'Net time-weighted return for the quarter in percent: (NAV change + distributions - calls) / opening NAV',
    REPORT_RECEIVED_DATE    DATE          COMMENT 'Date the quarterly figures were received by Harborline (typically 45 to 90 days after quarter end)'
) COMMENT = 'Quarterly fund valuations and performance as published by Harborline. One row per fund and quarter end from the first capital call.';

CREATE OR REPLACE TABLE FUND_CASH_FLOWS (
    CASH_FLOW_ID            VARCHAR(14)   NOT NULL PRIMARY KEY COMMENT 'Cash flow identifier (CF-00000001 ...)',
    FUND_ID                 VARCHAR(10)   NOT NULL REFERENCES FUNDS(FUND_ID) COMMENT 'Fund',
    FLOW_DATE               DATE          NOT NULL COMMENT 'Date the cash moved',
    QUARTER_END             DATE          NOT NULL COMMENT 'Quarter end the flow belongs to',
    FLOW_TYPE               VARCHAR(15)   NOT NULL COMMENT 'CAPITAL_CALL (LP pays in) or DISTRIBUTION (fund pays out)',
    FLOW_PURPOSE            VARCHAR(30)   COMMENT 'Calls: Investment, Management fee, Line repayment. Distributions: Realization, Dividend, Recapitalization',
    AMOUNT_USD_M            NUMBER(12,2)  NOT NULL COMMENT 'Amount in USD millions, always positive; direction is given by FLOW_TYPE',
    IS_RECALLABLE           BOOLEAN       COMMENT 'TRUE for distributions the fund may recall under the LPA (NULL for calls)'
) COMMENT = 'Dated LP cash flows for every fund: capital calls and distributions. One row per cash movement.';

CREATE OR REPLACE TABLE BENCHMARK_QUARTERLY (
    BENCHMARK_ID            VARCHAR(20)   NOT NULL REFERENCES BENCHMARKS(BENCHMARK_ID) COMMENT 'Harborline index',
    VINTAGE_YEAR            NUMBER(4,0)   COMMENT 'Vintage-year cohort of the index row; NULL for the all-vintages pooled row',
    QUARTER_END             DATE          NOT NULL COMMENT 'Quarter end the index values are reported as of',
    FUND_COUNT              NUMBER(5,0)   NOT NULL COMMENT 'Number of constituent funds with data in the quarter',
    POOLED_IRR_PCT          NUMBER(6,2)   COMMENT 'Capital-weighted since-inception net IRR of the constituents in percent (the published benchmark IRR)',
    QUARTERLY_RETURN_PCT    NUMBER(6,2)   COMMENT 'NAV-weighted net time-weighted return of the constituents for the quarter in percent',
    POOLED_TVPI             NUMBER(6,3)   COMMENT 'Pooled TVPI: sum of NAV and distributions over sum of called capital',
    POOLED_DPI              NUMBER(6,3)   COMMENT 'Pooled DPI: sum of distributions over sum of called capital',
    TOTAL_NAV_USD_M         NUMBER(14,1)  COMMENT 'Sum of constituent NAV in USD millions',
    TOTAL_CALLED_USD_M      NUMBER(14,1)  COMMENT 'Sum of constituent cumulative called capital in USD millions'
) COMMENT = 'Published Harborline index values. One row per index, vintage cohort (or all vintages) and quarter end.';

CREATE OR REPLACE TABLE FUND_REPORT_EXTRACTS (
    EXTRACT_ID              VARCHAR(12)   NOT NULL PRIMARY KEY COMMENT 'Extraction identifier (EXT-00001 ...)',
    FUND_ID                 VARCHAR(10)   NOT NULL REFERENCES FUNDS(FUND_ID) COMMENT 'Fund the report belongs to',
    REPORT_QUARTER_END      DATE          NOT NULL COMMENT 'Quarter end the GP quarterly report covers',
    SOURCE_DOCUMENT         VARCHAR(120)  COMMENT 'File name of the GP quarterly report the figures were extracted from',
    EXTRACTED_NAV_USD_M     NUMBER(12,1)  COMMENT 'NAV read from the report in USD millions',
    EXTRACTED_CALLS_IN_QUARTER_USD_M NUMBER(12,1) COMMENT 'Capital called during the quarter as stated in the report in USD millions',
    EXTRACTED_DISTRIBUTIONS_IN_QUARTER_USD_M NUMBER(12,1) COMMENT 'Distributions during the quarter as stated in the report in USD millions',
    EXTRACTED_CREDIT_LINE_BALANCE_USD_M NUMBER(12,1) COMMENT 'Subscription line balance as stated in the report in USD millions (NULL when the report does not mention one)',
    EXTRACTION_CONFIDENCE   NUMBER(4,3)   COMMENT 'Model confidence for the extracted figures (0 to 1); below 0.90 goes to analyst review',
    EXTRACTION_MODEL        VARCHAR(30)   COMMENT 'Extraction pipeline version (harborline-docai-2.3)',
    EXTRACTED_AT            TIMESTAMP_NTZ COMMENT 'When the extraction ran',
    REVIEW_STATUS           VARCHAR(20)   COMMENT 'AUTO_ACCEPTED, ANALYST_REVIEW or CORRECTED'
) COMMENT = 'Figures extracted automatically from GP quarterly reports (PDF) for the two latest quarters. One row per fund and report.';

CREATE OR REPLACE TABLE DATA_DICTIONARY (
    TABLE_NAME              VARCHAR(50)   NOT NULL COMMENT 'Table or view name',
    COLUMN_NAME             VARCHAR(60)   NOT NULL COMMENT 'Column name',
    DATA_TYPE               VARCHAR(30)   COMMENT 'Snowflake data type',
    DESCRIPTION             VARCHAR(400)  COMMENT 'Business meaning of the column',
    EXAMPLE_VALUE           VARCHAR(100)  COMMENT 'A representative value'
) COMMENT = 'Data dictionary for HARBORLINE_POC.ANALYTICS. One row per column.';

-- SECTION 3: VIEWS (portable: ANSI CASE, DATE literals, no :: or IFF, named GROUP BY) --

CREATE OR REPLACE VIEW V_FUND_PERFORMANCE_QUARTERLY
    COMMENT = 'Fund quarterly performance with fund attributes: one row per fund and quarter end. The source for custom indices, IRR time series and subscription-line analysis.'
AS
SELECT
    n.FUND_ID,
    f.FUND_NAME,
    m.MANAGER_NAME,
    f.STRATEGY,
    f.REGION,
    f.VINTAGE_YEAR,
    f.FUND_SIZE_USD_M,
    f.SIZE_BUCKET,
    f.USES_SUBSCRIPTION_LINE,
    f.SUBSCRIPTION_LINE_LIMIT_USD_M,
    f.FUND_STATUS,
    f.BENCHMARK_ID,
    n.QUARTER_END,
    n.FUND_AGE_QUARTERS,
    n.NAV_USD_M,
    n.CUMULATIVE_CALLED_USD_M,
    n.CUMULATIVE_DISTRIBUTED_USD_M,
    n.PAID_IN_PCT,
    n.CREDIT_LINE_BALANCE_USD_M,
    CASE WHEN n.NAV_USD_M > 0 THEN ROUND(100.0 * n.CREDIT_LINE_BALANCE_USD_M / n.NAV_USD_M, 2) ELSE NULL END AS CREDIT_LINE_PCT_OF_NAV,
    n.IRR_SINCE_INCEPTION_PCT,
    n.TVPI,
    n.DPI,
    n.RVPI,
    n.QUARTERLY_RETURN_PCT
FROM FUND_QUARTERLY_NAV n
JOIN FUNDS f ON f.FUND_ID = n.FUND_ID
JOIN MANAGERS m ON m.MANAGER_ID = f.MANAGER_ID;

CREATE OR REPLACE VIEW V_FUND_PERFORMANCE_LATEST
    COMMENT = 'Latest reported quarter for every fund (2026-06-30 for active funds): one row per fund with IRR, TVPI, DPI, NAV, paid-in and subscription-line usage.'
AS
SELECT p.*
FROM V_FUND_PERFORMANCE_QUARTERLY p
WHERE p.QUARTER_END = (SELECT MAX(n2.QUARTER_END) FROM FUND_QUARTERLY_NAV n2 WHERE n2.FUND_ID = p.FUND_ID);

CREATE OR REPLACE VIEW V_COHORT_INDEX_QUARTERLY
    COMMENT = 'The custom-index engine: fund performance pooled by strategy, region, vintage year, size bucket and quarter end. Sum the totals and recompute ratios when combining cohorts; never average MEDIAN or POOLED columns.'
AS
SELECT
    STRATEGY,
    REGION,
    VINTAGE_YEAR,
    SIZE_BUCKET,
    QUARTER_END,
    COUNT(FUND_ID)                                    AS FUND_COUNT,
    ROUND(MEDIAN(IRR_SINCE_INCEPTION_PCT), 2)         AS MEDIAN_IRR_PCT,
    ROUND(AVG(IRR_SINCE_INCEPTION_PCT), 2)            AS AVG_IRR_PCT,
    ROUND(SUM(IRR_SINCE_INCEPTION_PCT * CUMULATIVE_CALLED_USD_M) / NULLIF(SUM(CASE WHEN IRR_SINCE_INCEPTION_PCT IS NULL THEN 0 ELSE CUMULATIVE_CALLED_USD_M END), 0), 2) AS CAPITAL_WEIGHTED_IRR_PCT,
    ROUND(SUM(NAV_USD_M + CUMULATIVE_DISTRIBUTED_USD_M) / NULLIF(SUM(CUMULATIVE_CALLED_USD_M), 0), 3) AS POOLED_TVPI,
    ROUND(SUM(CUMULATIVE_DISTRIBUTED_USD_M) / NULLIF(SUM(CUMULATIVE_CALLED_USD_M), 0), 3)            AS POOLED_DPI,
    ROUND(SUM(QUARTERLY_RETURN_PCT * NAV_USD_M) / NULLIF(SUM(CASE WHEN QUARTERLY_RETURN_PCT IS NULL THEN 0 ELSE NAV_USD_M END), 0), 2) AS NAV_WEIGHTED_QUARTERLY_RETURN_PCT,
    ROUND(SUM(NAV_USD_M), 1)                          AS TOTAL_NAV_USD_M,
    ROUND(SUM(CUMULATIVE_CALLED_USD_M), 1)            AS TOTAL_CALLED_USD_M,
    ROUND(SUM(CUMULATIVE_DISTRIBUTED_USD_M), 1)       AS TOTAL_DISTRIBUTED_USD_M,
    ROUND(SUM(CREDIT_LINE_BALANCE_USD_M), 1)          AS TOTAL_CREDIT_LINE_BALANCE_USD_M,
    SUM(CASE WHEN USES_SUBSCRIPTION_LINE THEN 1 ELSE 0 END) AS FUNDS_WITH_SUBSCRIPTION_LINE
FROM V_FUND_PERFORMANCE_QUARTERLY
GROUP BY STRATEGY, REGION, VINTAGE_YEAR, SIZE_BUCKET, QUARTER_END;

CREATE OR REPLACE VIEW V_BENCHMARK_QUARTERLY
    COMMENT = 'Published Harborline index values with index attributes: one row per index, vintage cohort (VINTAGE_COHORT = year or All vintages) and quarter end.'
AS
SELECT
    q.BENCHMARK_ID,
    b.BENCHMARK_NAME,
    b.STRATEGY,
    b.REGION,
    b.IS_BROAD_INDEX,
    q.VINTAGE_YEAR,
    CASE WHEN q.VINTAGE_YEAR IS NULL THEN 'All vintages' ELSE CAST(q.VINTAGE_YEAR AS VARCHAR) END AS VINTAGE_COHORT,
    q.QUARTER_END,
    q.FUND_COUNT,
    q.POOLED_IRR_PCT,
    q.QUARTERLY_RETURN_PCT,
    q.POOLED_TVPI,
    q.POOLED_DPI,
    q.TOTAL_NAV_USD_M,
    q.TOTAL_CALLED_USD_M
FROM BENCHMARK_QUARTERLY q
JOIN BENCHMARKS b ON b.BENCHMARK_ID = q.BENCHMARK_ID;

CREATE OR REPLACE VIEW V_CASH_FLOW_PACING_QUARTERLY
    COMMENT = 'Cash-flow pacing: calls, distributions and net cash flow per fund and quarter with fund age, cumulative paid-in percent and DPI. Group by VINTAGE_YEAR and FUND_AGE_QUARTERS for pacing curves.'
AS
SELECT
    n.FUND_ID,
    f.FUND_NAME,
    f.STRATEGY,
    f.REGION,
    f.VINTAGE_YEAR,
    f.SIZE_BUCKET,
    f.FUND_SIZE_USD_M,
    f.USES_SUBSCRIPTION_LINE,
    n.QUARTER_END,
    n.FUND_AGE_QUARTERS,
    COALESCE(c.CALLS_USD_M, 0)                        AS CALLS_USD_M,
    COALESCE(c.DISTRIBUTIONS_USD_M, 0)                AS DISTRIBUTIONS_USD_M,
    COALESCE(c.DISTRIBUTIONS_USD_M, 0) - COALESCE(c.CALLS_USD_M, 0) AS NET_CASH_FLOW_USD_M,
    n.CUMULATIVE_CALLED_USD_M,
    n.CUMULATIVE_DISTRIBUTED_USD_M,
    n.PAID_IN_PCT,
    ROUND(100.0 * n.CUMULATIVE_DISTRIBUTED_USD_M / f.FUND_SIZE_USD_M, 2) AS DISTRIBUTED_PCT_OF_COMMITMENT,
    n.DPI,
    n.NAV_USD_M,
    n.CREDIT_LINE_BALANCE_USD_M
FROM FUND_QUARTERLY_NAV n
JOIN FUNDS f ON f.FUND_ID = n.FUND_ID
LEFT JOIN (
    SELECT FUND_ID, QUARTER_END,
           SUM(CASE WHEN FLOW_TYPE = 'CAPITAL_CALL' THEN AMOUNT_USD_M ELSE 0 END)  AS CALLS_USD_M,
           SUM(CASE WHEN FLOW_TYPE = 'DISTRIBUTION' THEN AMOUNT_USD_M ELSE 0 END)  AS DISTRIBUTIONS_USD_M
    FROM FUND_CASH_FLOWS
    GROUP BY FUND_ID, QUARTER_END
) c ON c.FUND_ID = n.FUND_ID AND c.QUARTER_END = n.QUARTER_END;

CREATE OR REPLACE VIEW V_SUBSCRIPTION_LINE_IRR_GAP
    COMMENT = 'Subscription-line effect on IRR: for each vintage year, strategy and fund age in quarters, the average IRR of funds with a subscription line versus funds without, and the gap in points.'
AS
SELECT
    VINTAGE_YEAR,
    STRATEGY,
    FUND_AGE_QUARTERS,
    QUARTER_END,
    SUM(CASE WHEN USES_SUBSCRIPTION_LINE THEN 1 ELSE 0 END)     AS FUNDS_WITH_LINE,
    SUM(CASE WHEN USES_SUBSCRIPTION_LINE THEN 0 ELSE 1 END)     AS FUNDS_WITHOUT_LINE,
    ROUND(AVG(CASE WHEN USES_SUBSCRIPTION_LINE THEN IRR_SINCE_INCEPTION_PCT END), 2)      AS AVG_IRR_WITH_LINE_PCT,
    ROUND(AVG(CASE WHEN USES_SUBSCRIPTION_LINE THEN NULL ELSE IRR_SINCE_INCEPTION_PCT END), 2) AS AVG_IRR_WITHOUT_LINE_PCT,
    ROUND(AVG(CASE WHEN USES_SUBSCRIPTION_LINE THEN IRR_SINCE_INCEPTION_PCT END)
        - AVG(CASE WHEN USES_SUBSCRIPTION_LINE THEN NULL ELSE IRR_SINCE_INCEPTION_PCT END), 2) AS IRR_GAP_PTS,
    ROUND(AVG(CASE WHEN USES_SUBSCRIPTION_LINE THEN CREDIT_LINE_PCT_OF_NAV END), 2)      AS AVG_LINE_PCT_OF_NAV
FROM V_FUND_PERFORMANCE_QUARTERLY
GROUP BY VINTAGE_YEAR, STRATEGY, FUND_AGE_QUARTERS, QUARTER_END;

CREATE OR REPLACE VIEW V_ALLOCATOR_HOLDINGS
    COMMENT = 'Each allocator commitment with the fund latest performance and the matching Harborline benchmark (same strategy, region and vintage year) at the same quarter end. One row per allocator and fund.'
AS
SELECT
    a.ALLOCATOR_ID,
    a.ALLOCATOR_NAME,
    a.ALLOCATOR_TYPE,
    c.COMMITMENT_ID,
    c.FUND_ID,
    p.FUND_NAME,
    p.MANAGER_NAME,
    p.STRATEGY,
    p.REGION,
    p.VINTAGE_YEAR,
    p.SIZE_BUCKET,
    c.COMMITMENT_USD_M,
    c.COMMITMENT_DATE,
    p.QUARTER_END,
    p.IRR_SINCE_INCEPTION_PCT                         AS FUND_IRR_PCT,
    p.TVPI                                            AS FUND_TVPI,
    p.DPI                                             AS FUND_DPI,
    p.BENCHMARK_ID,
    b.BENCHMARK_NAME,
    bq.POOLED_IRR_PCT                                 AS BENCHMARK_IRR_PCT,
    bq.POOLED_TVPI                                    AS BENCHMARK_TVPI,
    ROUND(p.IRR_SINCE_INCEPTION_PCT - bq.POOLED_IRR_PCT, 2) AS IRR_GAP_VS_BENCHMARK_PTS,
    ROUND(c.COMMITMENT_USD_M * p.NAV_USD_M / NULLIF(p.FUND_SIZE_USD_M, 0), 1) AS ALLOCATOR_SHARE_OF_NAV_USD_M
FROM ALLOCATOR_COMMITMENTS c
JOIN ALLOCATORS a ON a.ALLOCATOR_ID = c.ALLOCATOR_ID
JOIN V_FUND_PERFORMANCE_LATEST p ON p.FUND_ID = c.FUND_ID
JOIN BENCHMARKS b ON b.BENCHMARK_ID = p.BENCHMARK_ID
LEFT JOIN BENCHMARK_QUARTERLY bq
       ON bq.BENCHMARK_ID = p.BENCHMARK_ID
      AND bq.VINTAGE_YEAR = p.VINTAGE_YEAR
      AND bq.QUARTER_END = p.QUARTER_END;

CREATE OR REPLACE VIEW V_ALLOCATOR_VINTAGE_VS_BENCHMARK
    COMMENT = 'Allocator portfolio by vintage year versus the matching Harborline benchmarks: commitment-weighted fund IRR, commitment-weighted benchmark IRR and the gap in points. One row per allocator and vintage year.'
AS
SELECT
    ALLOCATOR_ID,
    ALLOCATOR_NAME,
    VINTAGE_YEAR,
    QUARTER_END,
    COUNT(FUND_ID)                                    AS FUND_COUNT,
    ROUND(SUM(COMMITMENT_USD_M), 1)                   AS COMMITTED_USD_M,
    ROUND(SUM(FUND_IRR_PCT * COMMITMENT_USD_M) / NULLIF(SUM(COMMITMENT_USD_M), 0), 2)      AS PORTFOLIO_IRR_PCT,
    ROUND(SUM(BENCHMARK_IRR_PCT * COMMITMENT_USD_M) / NULLIF(SUM(COMMITMENT_USD_M), 0), 2) AS BENCHMARK_IRR_PCT,
    ROUND((SUM(FUND_IRR_PCT * COMMITMENT_USD_M) - SUM(BENCHMARK_IRR_PCT * COMMITMENT_USD_M)) / NULLIF(SUM(COMMITMENT_USD_M), 0), 2) AS IRR_GAP_PTS,
    ROUND(SUM(FUND_TVPI * COMMITMENT_USD_M) / NULLIF(SUM(COMMITMENT_USD_M), 0), 3)         AS PORTFOLIO_TVPI,
    SUM(CASE WHEN IRR_GAP_VS_BENCHMARK_PTS < 0 THEN 1 ELSE 0 END) AS FUNDS_BELOW_BENCHMARK
FROM V_ALLOCATOR_HOLDINGS
GROUP BY ALLOCATOR_ID, ALLOCATOR_NAME, VINTAGE_YEAR, QUARTER_END;

CREATE OR REPLACE VIEW V_REPORT_EXTRACTION_RECONCILIATION
    COMMENT = 'Figures extracted from GP quarterly reports compared with the published fund figures for the same quarter: NAV variance, call and distribution variance, credit line variance, confidence and review status. One row per extraction.'
AS
SELECT
    e.EXTRACT_ID,
    e.FUND_ID,
    f.FUND_NAME,
    f.STRATEGY,
    f.REGION,
    f.VINTAGE_YEAR,
    e.REPORT_QUARTER_END,
    e.SOURCE_DOCUMENT,
    e.EXTRACTED_NAV_USD_M,
    n.NAV_USD_M                                       AS PUBLISHED_NAV_USD_M,
    ROUND(e.EXTRACTED_NAV_USD_M - n.NAV_USD_M, 1)     AS NAV_VARIANCE_USD_M,
    e.EXTRACTED_CALLS_IN_QUARTER_USD_M,
    COALESCE(c.CALLS_USD_M, 0)                        AS PUBLISHED_CALLS_IN_QUARTER_USD_M,
    e.EXTRACTED_DISTRIBUTIONS_IN_QUARTER_USD_M,
    COALESCE(c.DISTRIBUTIONS_USD_M, 0)                AS PUBLISHED_DISTRIBUTIONS_IN_QUARTER_USD_M,
    e.EXTRACTED_CREDIT_LINE_BALANCE_USD_M,
    n.CREDIT_LINE_BALANCE_USD_M                       AS PUBLISHED_CREDIT_LINE_BALANCE_USD_M,
    e.EXTRACTION_CONFIDENCE,
    e.EXTRACTION_MODEL,
    e.EXTRACTED_AT,
    e.REVIEW_STATUS,
    CASE WHEN ABS(e.EXTRACTED_NAV_USD_M - n.NAV_USD_M) <= 0.5
          AND ABS(e.EXTRACTED_CALLS_IN_QUARTER_USD_M - COALESCE(c.CALLS_USD_M, 0)) <= 0.5
          AND ABS(e.EXTRACTED_DISTRIBUTIONS_IN_QUARTER_USD_M - COALESCE(c.DISTRIBUTIONS_USD_M, 0)) <= 0.5
         THEN TRUE ELSE FALSE END                     AS MATCHES_PUBLISHED
FROM FUND_REPORT_EXTRACTS e
JOIN FUNDS f ON f.FUND_ID = e.FUND_ID
LEFT JOIN FUND_QUARTERLY_NAV n ON n.FUND_ID = e.FUND_ID AND n.QUARTER_END = e.REPORT_QUARTER_END
LEFT JOIN (
    SELECT FUND_ID, QUARTER_END,
           SUM(CASE WHEN FLOW_TYPE = 'CAPITAL_CALL' THEN AMOUNT_USD_M ELSE 0 END)  AS CALLS_USD_M,
           SUM(CASE WHEN FLOW_TYPE = 'DISTRIBUTION' THEN AMOUNT_USD_M ELSE 0 END)  AS DISTRIBUTIONS_USD_M
    FROM FUND_CASH_FLOWS
    GROUP BY FUND_ID, QUARTER_END
) c ON c.FUND_ID = e.FUND_ID AND c.QUARTER_END = e.REPORT_QUARTER_END;
