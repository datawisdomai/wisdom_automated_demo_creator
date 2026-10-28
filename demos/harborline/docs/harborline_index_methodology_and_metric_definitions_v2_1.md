# Harborline Private Capital Index — Methodology and Metric Definitions Standard v2.1

Letterhead: Harborline Private Capital — Index Research
Owner: Head of Index Research
Approved by: Head of Product Development
Effective: 2026-07-01 (applies to the quarter ended 30 June 2026 onward)
Classification: Client-shareable

## 1. Purpose

This standard defines every performance metric Harborline publishes and the rules for pooling funds into the Harborline Private Capital Index (HPCI) family and into client custom indices. The definitions below are certified: any figure published on the portal, in a custom index, or in a conversational answer must use them verbatim. The warehouse implementation is HARBORLINE_POC.ANALYTICS.

## 2. Universe and vintage convention

- The universe holds every fund for which Harborline receives fund-level cash flows and NAVs: 377 funds from 116 managers, vintages 2012 to 2024, six strategies (Buyout, Growth, Venture, Private Credit, Real Estate, Infrastructure) and four regions (North America, Europe, Asia-Pacific, Global).
- Vintage year is the calendar year of the fund's first capital call (FUNDS.VINTAGE_YEAR), not the year of first close. Fund age is counted in quarters from that call (FUND_QUARTERLY_NAV.FUND_AGE_QUARTERS = 1 in the quarter of the first call).
- Fund size is total limited-partner commitments in USD millions (FUNDS.FUND_SIZE_USD_M). Size buckets: SMALL under 1,000; MID_MARKET 1,000 to 5,000; MEGA above 5,000.
- All amounts are USD millions converted at the reporting date. Figures are published 45 to 90 days after quarter end; the latest published quarter is 30 June 2026.

## 3. Fund-level metrics (FUND_QUARTERLY_NAV)

| Metric | Column | Definition |
|---|---|---|
| Net asset value | NAV_USD_M | Residual value attributable to limited partners at quarter end, net of the subscription credit line balance |
| Paid-in capital | CUMULATIVE_CALLED_USD_M | Cumulative capital called from limited partners since inception |
| Paid-in percent | PAID_IN_PCT | Paid-in capital as a percent of fund size |
| Cumulative distributions | CUMULATIVE_DISTRIBUTED_USD_M | Cumulative cash and stock distributed to limited partners since inception |
| Net IRR since inception | IRR_SINCE_INCEPTION_PCT | Annualised internal rate of return of limited-partner cash flows and the closing NAV, net of fees and carry, in percent. NULL until 2 percent of commitments is called |
| TVPI | TVPI | (NAV + cumulative distributions) / paid-in capital |
| DPI | DPI | Cumulative distributions / paid-in capital |
| RVPI | RVPI | NAV / paid-in capital |
| Net quarterly return | QUARTERLY_RETURN_PCT | (closing NAV - opening NAV + distributions in quarter - calls in quarter) / opening NAV, in percent |
| Credit line balance | CREDIT_LINE_BALANCE_USD_M | Drawn balance of the subscription credit facility at quarter end |

## 4. Pooling rules (indices and custom indices)

- Pooled IRR (POOLED_IRR_PCT, CAPITAL_WEIGHTED_IRR_PCT): capital-weighted since-inception IRR of the constituents, weights = cumulative called capital. This is the published index statistic.
- Pooled TVPI: sum of NAV and cumulative distributions over sum of paid-in capital. Pooled DPI and RVPI likewise. Ratio columns are never averaged.
- Median fund IRR (MEDIAN_IRR_PCT): the median of constituent IRRs; the headline for fund-level comparisons and for client custom indices because it is not dominated by mega funds.
- Index quarterly return: NAV-weighted average of constituent net quarterly returns.
- A vintage cohort is published when it has at least two constituents; the all-vintages row (VINTAGE_YEAR NULL, VINTAGE_COHORT "All vintages") pools every constituent.
- A custom index is any cohort selected by strategy, region, vintage range and size bucket. V_COHORT_INDEX_QUARTERLY carries every elementary cohort; to combine cohorts sum TOTAL_NAV_USD_M, TOTAL_CALLED_USD_M and TOTAL_DISTRIBUTED_USD_M and recompute the ratios.

## 5. Index family

| Index | Constituents |
|---|---|
| HPCI-BROAD-PE Harborline Broad Private Equity Index | All buyout, growth and venture funds, every region and vintage (the "broad PE benchmark") |
| HPCI-ALL-PC Harborline Private Capital Composite | Every fund in the universe |
| HPCI-BUYOUT-NA / -EU / -APAC / -GLOBAL | Buyout funds by primary region; GLOBAL pools all buyout funds |
| HPCI-GROWTH-GLOBAL | All growth equity funds |
| HPCI-VENTURE-NA / -GLOBAL | Venture funds in North America; all venture funds |
| HPCI-CREDIT-GLOBAL, HPCI-RE-GLOBAL, HPCI-INFRA-GLOBAL | Private credit, private real estate, infrastructure |

Each fund carries its matching index in FUNDS.BENCHMARK_ID. Comparing a fund or a client sleeve to "the index" means the matching index at the same vintage year and quarter end.

## 6. Subscription credit lines

A subscription credit line (also capital call facility, line of credit) is borrowing secured on undrawn commitments that a general partner uses to bridge capital calls. Because limited-partner capital is called later, the reported net IRR is higher early in a fund's life. Harborline flags line usage (FUNDS.USES_SUBSCRIPTION_LINE, SUBSCRIPTION_LINE_LIMIT_USD_M) and publishes the drawn balance each quarter. V_SUBSCRIPTION_LINE_IRR_GAP reports the average IRR of funds with a line minus funds without at the same vintage, strategy and fund age. The watch threshold is a drawn balance above 15 percent of NAV, or an IRR gap above 3 points at the same age for vintages under four years old.

## 7. Cash-flow pacing

Pacing curves use V_CASH_FLOW_PACING_QUARTERLY: calls, distributions and net cash flow per fund and quarter, expressed as a percent of commitments when pooled (sum of flows over sum of fund size for the funds present at that age). Vintages are compared at the same fund age; sixteen quarters is the house convention for "four years in". Net cash flow is distributions minus calls and is negative during the investment period (the J-curve).

## 8. Allocator comparisons

Client sleeves are compared commitment weighted: portfolio IRR = sum(fund IRR x commitment) / sum(commitment); benchmark IRR = the same weighting applied to each fund's matching index at its vintage year; the gap is the difference in points. V_ALLOCATOR_VINTAGE_VS_BENCHMARK publishes this by vintage year and V_ALLOCATOR_HOLDINGS by fund.

## 9. Report extraction

Figures extracted from general-partner quarterly reports by the harborline-docai-2.3 pipeline (FUND_REPORT_EXTRACTS) are reconciled against the published figures before release. An extraction matches when NAV, calls and distributions agree within 0.5 million USD (V_REPORT_EXTRACTION_RECONCILIATION.MATCHES_PUBLISHED). Confidence below 0.90 routes the extraction to analyst review.

## 10. Change log

- v2.1 (2026-07-01): added size buckets, the subscription-line watch thresholds and the extraction reconciliation rule.
- v2.0 (2025-01-01): median fund IRR adopted as the custom-index headline; vintage cohort minimum lowered to two constituents.
