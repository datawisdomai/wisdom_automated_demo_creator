# Harborline Private Capital — Domain Bootstrap (wACE)

Demo as-of date: **2026-10-15**. Latest reported quarter: **Q2 2026 (2026-06-30)**. Data spans 2012-01-01 to 2026-06-30 (vintages 2012–2024, 58 quarter ends).
Warehouse: Snowflake `HARBORLINE_POC.ANALYTICS`. Dialect: Snowflake. All amounts are USD millions.

---

## 1. DOMAIN OVERVIEW

Harborline Private Capital is a fictional producer of private-markets benchmarks and indices: the **Harborline Private Capital Index (HPCI)** family. It is a quant shop that does not trade. It collects fund-level cash flows and NAVs contributed by limited partners (LPs) and general partners (GPs), extracts figures from GP quarterly reports with a document-extraction pipeline, and publishes pooled indices by strategy, region and vintage. Its allocator clients (pensions, endowments, insurers, family offices, sovereign funds) subscribe to a portal; **Premium Analytics** clients build custom indices, cash-flow pacing views and portfolio-versus-benchmark comparisons.

The audience is the Head of Product Development (who owns the index and analytics products) and, through the Live App, an allocator analyst. Questions are about custom index construction, fund performance (IRR, TVPI, DPI), subscription credit lines, cash-flow pacing by vintage, allocator portfolios against benchmarks, and whether report extractions match the published figures. Never frame answers as investment advice or forecasts; the domain reports what the funds and indices show.

---

## 2. TABLE CATALOG

### 2.1 `MANAGERS` (dimension, 116 rows)
General partners. `MANAGER_ID` (MGR-001), `MANAGER_NAME`, `HEADQUARTERS_CITY`, `HEADQUARTERS_COUNTRY`, `FOUNDED_YEAR`, `PRIMARY_STRATEGY`, `FIRM_AUM_USD_B`, `IS_HPCI_CONTRIBUTOR` (contributes cash flows directly).

### 2.2 `BENCHMARKS` (dimension, 12 rows)
The HPCI index family. `BENCHMARK_ID` (HPCI-BROAD-PE, HPCI-ALL-PC, HPCI-BUYOUT-NA, HPCI-BUYOUT-EU, HPCI-BUYOUT-APAC, HPCI-BUYOUT-GLOBAL, HPCI-GROWTH-GLOBAL, HPCI-VENTURE-NA, HPCI-VENTURE-GLOBAL, HPCI-CREDIT-GLOBAL, HPCI-RE-GLOBAL, HPCI-INFRA-GLOBAL), `BENCHMARK_NAME`, `STRATEGY`, `REGION`, `CONSTITUENT_RULE`, `INCEPTION_DATE`, `IS_BROAD_INDEX` (TRUE for the two headline indices).

### 2.3 `FUNDS` (dimension, 377 rows)
One row per fund. `FUND_ID` (FND-0001), `FUND_NAME`, `MANAGER_ID`, `STRATEGY` (Buyout, Growth, Venture, Private Credit, Real Estate, Infrastructure), `REGION` (North America, Europe, Asia-Pacific, Global), `VINTAGE_YEAR` (year of first capital call), `FIRST_CLOSE_DATE`, `FIRST_CALL_DATE`, `FUND_SIZE_USD_M` (total commitments), `SIZE_BUCKET` (SMALL under 1B, MID_MARKET 1–5B, MEGA over 5B), `BASE_CURRENCY`, `USES_SUBSCRIPTION_LINE` (boolean), `SUBSCRIPTION_LINE_LIMIT_USD_M`, `FUND_STATUS` (INVESTING, HARVESTING, LIQUIDATED), `BENCHMARK_ID` (the matching strategy-and-region index), `DATA_SOURCE`.

### 2.4 `ALLOCATORS` (dimension, 5 rows)
Portal clients. `ALLOCATOR_ID` (ALC-001), `ALLOCATOR_NAME`, `ALLOCATOR_TYPE`, `HEADQUARTERS`, `TOTAL_PC_COMMITMENT_USD_M`, `PORTAL_TIER` (Standard, Premium Analytics).

### 2.5 `ALLOCATOR_COMMITMENTS` (fact, 156 rows)
`COMMITMENT_ID`, `ALLOCATOR_ID`, `FUND_ID`, `COMMITMENT_USD_M`, `COMMITMENT_DATE`. One row per allocator and fund.

### 2.6 `FUND_QUARTERLY_NAV` (fact, 12,141 rows)
One row per fund and quarter end from the first capital call. `FUND_ID`, `QUARTER_END`, `FUND_AGE_QUARTERS` (1 = quarter of the first call), `NAV_USD_M` (net to LPs, net of the line balance), `CUMULATIVE_CALLED_USD_M`, `CUMULATIVE_DISTRIBUTED_USD_M`, `PAID_IN_PCT`, `CREDIT_LINE_BALANCE_USD_M`, `IRR_SINCE_INCEPTION_PCT`, `TVPI`, `DPI`, `RVPI`, `QUARTERLY_RETURN_PCT`, `REPORT_RECEIVED_DATE`.

### 2.7 `FUND_CASH_FLOWS` (fact, 28,861 rows)
Dated LP cash flows. `CASH_FLOW_ID`, `FUND_ID`, `FLOW_DATE`, `QUARTER_END`, `FLOW_TYPE` (CAPITAL_CALL, DISTRIBUTION), `FLOW_PURPOSE` (Investment, Management fee, Line repayment, Realization, Dividend, Recapitalization), `AMOUNT_USD_M` (always positive), `IS_RECALLABLE`.

### 2.8 `BENCHMARK_QUARTERLY` (fact, 4,858 rows)
Published index values. `BENCHMARK_ID`, `VINTAGE_YEAR` (NULL = all vintages pooled), `QUARTER_END`, `FUND_COUNT`, `POOLED_IRR_PCT` (capital-weighted), `QUARTERLY_RETURN_PCT` (NAV-weighted), `POOLED_TVPI`, `POOLED_DPI`, `TOTAL_NAV_USD_M`, `TOTAL_CALLED_USD_M`.

### 2.9 `FUND_REPORT_EXTRACTS` (fact, 711 rows)
Figures the extraction pipeline read from GP quarterly reports for 2026-03-31 and 2026-06-30. `EXTRACT_ID`, `FUND_ID`, `REPORT_QUARTER_END`, `SOURCE_DOCUMENT`, `EXTRACTED_NAV_USD_M`, `EXTRACTED_CALLS_IN_QUARTER_USD_M`, `EXTRACTED_DISTRIBUTIONS_IN_QUARTER_USD_M`, `EXTRACTED_CREDIT_LINE_BALANCE_USD_M`, `EXTRACTION_CONFIDENCE`, `EXTRACTION_MODEL`, `EXTRACTED_AT`, `REVIEW_STATUS` (AUTO_ACCEPTED, ANALYST_REVIEW, CORRECTED).

### 2.10 `DATA_DICTIONARY` (91 rows)
`TABLE_NAME`, `COLUMN_NAME`, `DATA_TYPE`, `DESCRIPTION`, `EXAMPLE_VALUE`.

---

## 3. ANALYTICAL VIEWS (use these first)

| View | Grain | Use for |
|---|---|---|
| `V_FUND_PERFORMANCE_QUARTERLY` | fund × quarter end | IRR / TVPI / DPI time series with fund attributes; adds `CREDIT_LINE_PCT_OF_NAV` |
| `V_FUND_PERFORMANCE_LATEST` | fund (latest quarter) | "current" performance; filter `QUARTER_END = 2026-06-30` for active funds |
| `V_COHORT_INDEX_QUARTERLY` | strategy × region × vintage × size bucket × quarter | the custom-index engine: `FUND_COUNT`, `MEDIAN_IRR_PCT`, `AVG_IRR_PCT`, `CAPITAL_WEIGHTED_IRR_PCT`, `POOLED_TVPI`, `POOLED_DPI`, `NAV_WEIGHTED_QUARTERLY_RETURN_PCT`, totals |
| `V_BENCHMARK_QUARTERLY` | index × vintage cohort × quarter | published indices; `VINTAGE_COHORT` = year or "All vintages" |
| `V_CASH_FLOW_PACING_QUARTERLY` | fund × quarter | `CALLS_USD_M`, `DISTRIBUTIONS_USD_M`, `NET_CASH_FLOW_USD_M`, `PAID_IN_PCT`, `DISTRIBUTED_PCT_OF_COMMITMENT`, `DPI` with `FUND_AGE_QUARTERS` |
| `V_SUBSCRIPTION_LINE_IRR_GAP` | vintage × strategy × fund age | `AVG_IRR_WITH_LINE_PCT`, `AVG_IRR_WITHOUT_LINE_PCT`, `IRR_GAP_PTS`, fund counts |
| `V_ALLOCATOR_HOLDINGS` | allocator × fund | commitment, fund IRR / TVPI / DPI, matching benchmark IRR, `IRR_GAP_VS_BENCHMARK_PTS` |
| `V_ALLOCATOR_VINTAGE_VS_BENCHMARK` | allocator × vintage | `PORTFOLIO_IRR_PCT`, `BENCHMARK_IRR_PCT`, `IRR_GAP_PTS` (commitment weighted), `FUNDS_BELOW_BENCHMARK` |
| `V_REPORT_EXTRACTION_RECONCILIATION` | extraction | extracted vs published NAV, calls, distributions, line balance; `NAV_VARIANCE_USD_M`, `MATCHES_PUBLISHED` |

---

## 4. ENTITY RELATIONSHIP MAP

- `MANAGERS 1 — n FUNDS` (MANAGER_ID); `BENCHMARKS 1 — n FUNDS` (BENCHMARK_ID = matching index).
- `FUNDS 1 — n FUND_QUARTERLY_NAV`, `FUND_CASH_FLOWS`, `FUND_REPORT_EXTRACTS`, `ALLOCATOR_COMMITMENTS` (FUND_ID).
- `ALLOCATORS 1 — n ALLOCATOR_COMMITMENTS` (ALLOCATOR_ID).
- `BENCHMARKS 1 — n BENCHMARK_QUARTERLY` (BENCHMARK_ID); join a fund to its benchmark row on `BENCHMARK_ID`, `VINTAGE_YEAR` and `QUARTER_END`.
- Cash flows roll up to `FUND_QUARTERLY_NAV` on `FUND_ID` and `QUARTER_END` (quarterly calls equal the change in cumulative called capital).

---

## 5. METRICS DICTIONARY

Certified definitions live in `metrics.csv` (29 metrics). The ones used most:
- **median_fund_irr_pct** = MEDIAN(IRR_SINCE_INCEPTION_PCT) over `V_FUND_PERFORMANCE_LATEST` — the custom-index headline.
- **capital_weighted_irr_pct** = SUM(IRR × CUMULATIVE_CALLED) / SUM(CUMULATIVE_CALLED) — how published indices pool.
- **pooled_tvpi** = SUM(NAV + CUMULATIVE_DISTRIBUTED) / SUM(CUMULATIVE_CALLED); **pooled_dpi**, **pooled_rvpi** likewise. Never average ratio columns.
- **credit_line_pct_of_nav** = 100 × SUM(CREDIT_LINE_BALANCE) / SUM(NAV); watch threshold 15 percent per fund.
- **subscription_line_irr_gap_pts** from `V_SUBSCRIPTION_LINE_IRR_GAP` at a chosen fund age.
- **allocator_irr_gap_pts** = commitment-weighted (fund IRR − benchmark IRR) over `V_ALLOCATOR_HOLDINGS`.
- **extraction_match_rate** = share of `MATCHES_PUBLISHED` over `V_REPORT_EXTRACTION_RECONCILIATION`.

---

## 6. SYNONYMS MASTER LIST

- custom index, cohort, peer group, universe cut → a filtered set of funds pooled in `V_COHORT_INDEX_QUARTERLY`
- broad PE benchmark, broad index, the PE index, HPCI broad → HPCI-BROAD-PE (Harborline Broad Private Equity Index)
- composite, all private capital → HPCI-ALL-PC
- GP, manager, sponsor, firm → MANAGERS; LP, allocator, client, investor, pension → ALLOCATORS
- vintage, vintage year → VINTAGE_YEAR; buyout, PE, private equity → STRATEGY = 'Buyout' (private equity in the broad sense = Buyout + Growth + Venture)
- VC, venture capital → Venture; private debt, direct lending → Private Credit; infra → Infrastructure; real assets → Real Estate + Infrastructure
- NA, US, North American → REGION = 'North America'; EU, European → Europe; APAC, Asia → Asia-Pacific
- subscription line, sub line, capital call facility, credit facility, line of credit, LOC, bridge facility → USES_SUBSCRIPTION_LINE / CREDIT_LINE_BALANCE_USD_M
- NAV, net asset value, residual value → NAV_USD_M; paid-in, called, contributed, drawn → CUMULATIVE_CALLED_USD_M; distributions, realizations, cash back → CUMULATIVE_DISTRIBUTED_USD_M
- net IRR, since-inception IRR, SI IRR → IRR_SINCE_INCEPTION_PCT; multiple, MOIC → TVPI
- mid-market, middle market → MID_MARKET; mega, large cap → MEGA; small, lower mid → SMALL
- pacing, J-curve, cash-flow profile → V_CASH_FLOW_PACING_QUARTERLY by FUND_AGE_QUARTERS
- quarterly report, LP report, GP report, capital account statement → FUND_REPORT_EXTRACTS / the attached PDF
- latest quarter, current, as of today → QUARTER_END = 2026-06-30

---

## 7. DOMAIN KNOWLEDGE

- The as-of date is 2026-10-15; the latest reported quarter is 2026-06-30 because private-capital figures arrive 45–90 days after quarter end. "Latest" and "current" mean the 2026-06-30 rows.
- Vintage year is the year of the first capital call. Fund size equals total LP commitments.
- A custom index is any pooled cohort; its headline is the median fund IRR (fund-level comparisons) while published indices use capital-weighted pooled IRR. The North American buyout custom index of vintages 2015–2020 holds 49 funds with a median IRR of 15.9 percent against 13.3 percent for HPCI-BROAD-PE (all vintages) at 2026-06-30; mid-market funds in the cohort show 16.3 percent against 13.1 percent for mega funds.
- Subscription lines flatter early IRR. For vintages 2019–2022, funds with a line show an average IRR of about 7.4 percent at eight quarters of age versus 2.3 percent without; for vintages 2014–2017 the gap at the latest quarter is under 1.5 points. 156 of 377 funds use a line; 89 had a balance drawn at 2026-06-30 totalling about 17 billion USD.
- Calder Ridge Capital Partners IV (FND-0117, Calder Ridge Capital, Boston) is the hero fund: 3.2 billion USD, North American buyout, vintage 2018, 400 million line. At 2026-06-30: NAV 2,614.0; called 2,880.0 (90 percent paid in); distributed 1,152.0; line balance 210.0; IRR 18.4 percent; TVPI 1.31; DPI 0.40. Q2 2026 flows: calls of 40.0 (2026-04-14) and 24.0 (2026-06-02), distribution of 96.0 (2026-05-20). Its Q2 2026 LP report is attached and the extraction matches exactly (confidence 0.97).
- Distribution drought: vintages 2021–2022 have a median DPI of about 0.16 at sixteen quarters versus 0.55–0.60 for vintages 2014–2016 at the same age; H1 2026 distributions (about 36 billion) are about 44 percent below H1 2021 (about 64 billion).
- Westbrook State Retirement System (ALC-001): 38 covered commitments, 2.71 billion USD. Its 2018 sleeve (8 funds, 760 million) lags its matching benchmarks by about 3.5 points (8.5 vs 12.0 percent) because of Bramblewood Ventures III (IRR about −3.5 percent, 15.7 points below HPCI-VENTURE-NA 2018) and Sable Point Ventures II (about 0.1 percent, 12.2 points below). Every other Westbrook vintage is at or above benchmark.
- Extractions: 711 rows for the two latest quarters; about 91 percent AUTO_ACCEPTED, confidence below 0.90 goes to ANALYST_REVIEW, CORRECTED rows were fixed by an analyst.

---

## 8. BUSINESS NUANCES

- IRR is a since-inception, compounding figure: never sum or average it over quarters. Compare funds at the same quarter end or the same fund age.
- TVPI, DPI and RVPI are NULL until a fund has called at least 2 percent of commitments; exclude NULLs from medians.
- Liquidated funds (25, mostly 2012–2013) stop reporting; their latest row predates 2026-06-30. Filter `QUARTER_END = 2026-06-30` when "active funds" are meant.
- Benchmark rows with `VINTAGE_YEAR` NULL are the all-vintages pooled index; vintage cohorts need at least two constituents to be published.
- `NAV_USD_M` is net of the subscription line balance; the line is a liability of the fund, not an LP cash flow.
- Allocator comparisons use the matching index at the fund's vintage year and quarter end, commitment weighted; a fund without a published cohort row has a NULL benchmark and is excluded from the gap.
- `TOTAL_PC_COMMITMENT_USD_M` on `ALLOCATORS` covers all of a client's commitments, including funds Harborline does not cover; `ALLOCATOR_COMMITMENTS` holds only covered funds.

---

## 9. TRIBAL KNOWLEDGE

- "The index" in a question from an allocator means the matching strategy-and-region index at their vintage; "the broad benchmark" means HPCI-BROAD-PE.
- Sixteen quarters is the house convention for "four years in" when comparing pacing across vintages; eight quarters is where the subscription-line effect peaks.
- Q2 2026 is the second quarter in which the extraction pipeline (harborline-docai-2.3) ran on every GP report; extraction disagreements are reconciled before publication, which is why `MATCHES_PUBLISHED` is TRUE for almost every AUTO_ACCEPTED row.
- Westbrook's 2018 venture positions are known internally as "the two Vs"; the index desk expects the question every quarter.

---

## 10. QUERY ROUTING HINTS

- Custom index / cohort / compare to benchmark → `V_FUND_PERFORMANCE_QUARTERLY` (or `V_COHORT_INDEX_QUARTERLY`) filtered by STRATEGY, REGION, VINTAGE_YEAR range, SIZE_BUCKET; join `V_BENCHMARK_QUARTERLY` on QUARTER_END with `VINTAGE_YEAR IS NULL` for the broad index.
- Latest performance of a fund → `V_FUND_PERFORMANCE_LATEST` by FUND_NAME.
- Subscription line effect → `V_SUBSCRIPTION_LINE_IRR_GAP` by FUND_AGE_QUARTERS and vintage range; line exposure → `V_FUND_PERFORMANCE_LATEST.CREDIT_LINE_PCT_OF_NAV`.
- Pacing / J-curve / DPI by age → `V_CASH_FLOW_PACING_QUARTERLY` grouped by VINTAGE_YEAR and FUND_AGE_QUARTERS (percent of commitments = SUM(flow) / SUM(FUND_SIZE_USD_M)).
- Calls and distributions by calendar year or half year → `FUND_CASH_FLOWS` by FLOW_DATE and FLOW_TYPE.
- Allocator vs benchmark → `V_ALLOCATOR_VINTAGE_VS_BENCHMARK` (by vintage) then `V_ALLOCATOR_HOLDINGS` (which funds).
- Report extraction / does the report match → `V_REPORT_EXTRACTION_RECONCILIATION`; the report text itself is the attached PDF.
