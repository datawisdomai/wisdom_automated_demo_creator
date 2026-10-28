# Data Platform wiki — HARBORLINE_POC onboarding notes

Space: Data Platform / Analytics Warehouse
Page owner: Analytics Engineering
Last edited: 2026-09-30 by the analytics engineering lead
Audience: new analysts, index researchers and anyone building a custom index or pacing view on the warehouse

## What this schema is

HARBORLINE_POC.ANALYTICS is the curated layer behind the portal and the conversational analytics tier. It holds the fund universe (FUNDS, MANAGERS), the quarterly series (FUND_QUARTERLY_NAV, FUND_CASH_FLOWS), the published indices (BENCHMARKS, BENCHMARK_QUARTERLY), client commitments (ALLOCATORS, ALLOCATOR_COMMITMENTS) and the report-extraction outputs (FUND_REPORT_EXTRACTS). Nine V_ views sit on top; use them before touching the base tables.

Snapshot: as of 15 October 2026 the latest published quarter is 30 June 2026. Quarter ends run from 31 March 2012 to 30 June 2026 (58 quarter ends). 377 funds, 116 managers, 12 indices, 5 allocator clients, 12,141 fund-quarter rows, 28,861 cash flows, 4,858 index rows, 711 extractions.

## Start here: the views

- V_FUND_PERFORMANCE_QUARTERLY: one row per fund and quarter with the fund attributes already joined (name, manager, strategy, region, vintage, size bucket, line usage). Also gives CREDIT_LINE_PCT_OF_NAV. If you are plotting an IRR time series, this is the table.
- V_FUND_PERFORMANCE_LATEST: the most recent row per fund. For active funds that is 30 June 2026; liquidated funds (25 of them, mostly vintages 2012 and 2013) have an earlier latest row. Filter QUARTER_END = DATE '2026-06-30' when you mean "funds reporting today".
- V_COHORT_INDEX_QUARTERLY: every elementary cohort (strategy x region x vintage year x size bucket x quarter) with FUND_COUNT, MEDIAN_IRR_PCT, CAPITAL_WEIGHTED_IRR_PCT, POOLED_TVPI, POOLED_DPI and the totals. To build a wider custom index sum TOTAL_NAV_USD_M, TOTAL_CALLED_USD_M and TOTAL_DISTRIBUTED_USD_M across the cohorts you want and recompute the ratios. Do not average the median or pooled columns across cohorts; for a cross-cohort median go back to V_FUND_PERFORMANCE_QUARTERLY and take MEDIAN over the funds.
- V_BENCHMARK_QUARTERLY: published indices with names. VINTAGE_YEAR is NULL for the all-vintages row; VINTAGE_COHORT spells it out ("All vintages" or the year). The broad PE benchmark is BENCHMARK_ID = 'HPCI-BROAD-PE'.
- V_CASH_FLOW_PACING_QUARTERLY: calls, distributions and net cash flow per fund and quarter with FUND_AGE_QUARTERS. Pacing curves are GROUP BY VINTAGE_YEAR, FUND_AGE_QUARTERS with SUM(flow) / SUM(FUND_SIZE_USD_M) * 100 for percent of commitments.
- V_SUBSCRIPTION_LINE_IRR_GAP: average IRR with and without a subscription line by vintage, strategy and fund age, plus the gap in points.
- V_ALLOCATOR_HOLDINGS and V_ALLOCATOR_VINTAGE_VS_BENCHMARK: client commitments against the matching index at the fund's vintage year, commitment weighted.
- V_REPORT_EXTRACTION_RECONCILIATION: extracted versus published figures for each GP report with NAV_VARIANCE_USD_M and MATCHES_PUBLISHED.

## Join paths

- FUNDS.MANAGER_ID -> MANAGERS.MANAGER_ID
- FUNDS.BENCHMARK_ID -> BENCHMARKS.BENCHMARK_ID (the matching index); to get the benchmark value for a fund join BENCHMARK_QUARTERLY on BENCHMARK_ID, VINTAGE_YEAR and QUARTER_END
- FUND_QUARTERLY_NAV, FUND_CASH_FLOWS, FUND_REPORT_EXTRACTS, ALLOCATOR_COMMITMENTS -> FUNDS.FUND_ID
- FUND_CASH_FLOWS rolls up to FUND_QUARTERLY_NAV on FUND_ID and QUARTER_END; the sum of CAPITAL_CALL flows in a quarter equals the change in CUMULATIVE_CALLED_USD_M (verified every load)
- ALLOCATOR_COMMITMENTS.ALLOCATOR_ID -> ALLOCATORS.ALLOCATOR_ID

## Gotchas

- IRR_SINCE_INCEPTION_PCT is a since-inception figure. Never SUM or AVG it across quarters. Compare funds at the same QUARTER_END or the same FUND_AGE_QUARTERS.
- IRR, TVPI, DPI and RVPI are NULL until a fund has called 2 percent of commitments; young funds with a subscription line can be NULL for two or three quarters because the line funds the first deals.
- NAV_USD_M is net of the credit line balance. Do not add CREDIT_LINE_BALANCE_USD_M to it.
- AMOUNT_USD_M in FUND_CASH_FLOWS is always positive; direction comes from FLOW_TYPE. Net cash flow = distributions minus calls.
- QUARTERLY_RETURN_PCT is NULL in a fund's first quarter and whenever the opening NAV is under 1 million.
- Index rows need at least two constituents; small vintage cohorts of regional indices can be missing, which is why V_ALLOCATOR_HOLDINGS uses a LEFT JOIN and the gap can be NULL.
- Vintage year = year of first capital call. FIRST_CLOSE_DATE is earlier and is not the vintage.
- "Private equity" in the broad sense means Buyout + Growth + Venture (the HPCI-BROAD-PE constituents). STRATEGY = 'Buyout' is the narrow meaning.
- Size buckets: SMALL < 1,000, MID_MARKET 1,000-5,000, MEGA > 5,000 (USD millions of commitments).
- H1 and H2 questions use FLOW_DATE on FUND_CASH_FLOWS, not QUARTER_END.

## Known story lines the index desk gets asked about

- North American buyout, vintages 2015-2020: 49 funds, median IRR 15.9 percent at 30 June 2026 against 13.3 percent for HPCI-BROAD-PE all vintages; mid-market 16.3 percent versus mega 13.1 percent.
- Subscription lines: 156 funds have one; 89 funds had a balance drawn at 30 June 2026 (about 17 billion USD in total). Vintages 2019-2022 show roughly a 5 point IRR gap in favour of line users at eight quarters; vintages 2014-2017 show under 1.5 points today.
- Calder Ridge Capital Partners IV (FND-0117): NAV 2,614.0, called 2,880.0, distributed 1,152.0, line 210.0, IRR 18.4 percent, TVPI 1.31, DPI 0.40 at 30 June 2026. Q2 2026 calls 40.0 + 24.0, distribution 96.0. Its Q2 2026 LP report is in the document store and the extraction (confidence 0.97) matches.
- Distribution drought: vintages 2021-2022 median DPI about 0.16 at sixteen quarters versus 0.55-0.60 for 2014-2016. H1 2026 distributions about 36 billion versus about 64 billion in H1 2021.
- Westbrook State Retirement System: 38 commitments, 2.71 billion. 2018 sleeve 8.5 percent versus 12.0 percent benchmark (gap about -3.5 points) because of Bramblewood Ventures III and Sable Point Ventures II; all other vintages at or above benchmark.

## Refresh and ownership

Quarterly refresh on the 90th day after quarter end once Fund Data Operations closes the contribution window; the Q3 2026 refresh is scheduled for 2026-12-29. Questions to #index-desk. Schema changes go through Analytics Engineering with a DATA_DICTIONARY update in the same change.
