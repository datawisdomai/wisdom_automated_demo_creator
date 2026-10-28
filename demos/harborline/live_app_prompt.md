# Live App prompt — Custom Index Studio

Paste into Wisdom on the Harborline Private Capital domain. In the demo the SE types the short
allocator prompt first (the one-liner below) and refines live; this full prompt is the pre-built
safety net that ends where the live refinement would end.

Allocator one-liner for the live build:
"Build me a custom index of North American buyout funds, vintages 2015-2020, and compare quarterly IRR to the broad PE benchmark."
Refinements: "now split by fund size" and "add a cash-flow pacing view".

```
Create a live app called "Custom Index Studio" for Harborline Private Capital, a producer of private-capital benchmarks and indices. It is the portal view an allocator analyst gets when they ask for a custom index in plain English, not a reporting dashboard. Every page answers "how does my chosen cohort of funds perform against the Harborline benchmark and what does its cash flow look like". Use three connected pages.

DATA RULES
Use V_FUND_PERFORMANCE_QUARTERLY as the primary source for the cohort: filter STRATEGY = 'Buyout', REGION = 'North America' and VINTAGE_YEAR between 2015 and 2020. Use V_BENCHMARK_QUARTERLY with BENCHMARK_ID = 'HPCI-BROAD-PE' and VINTAGE_YEAR null (the all-vintages row) for the broad PE benchmark, and BENCHMARK_ID = 'HPCI-BUYOUT-NA' per vintage year for the matching index. Use V_CASH_FLOW_PACING_QUARTERLY for pacing. Aggregate each source before combining; never join fact tables as raw rows.
The latest reported quarter is 2026-06-30 (Q2 2026); anchor "today" to 2026-10-15. The cohort statistic is the median fund IRR (MEDIAN of IRR_SINCE_INCEPTION_PCT across the funds in the quarter); the benchmark statistic is the published POOLED_IRR_PCT. Pooled TVPI and DPI are SUM(NAV_USD_M + CUMULATIVE_DISTRIBUTED_USD_M) / SUM(CUMULATIVE_CALLED_USD_M) and SUM(CUMULATIVE_DISTRIBUTED_USD_M) / SUM(CUMULATIVE_CALLED_USD_M); never average ratio columns and never sum or average IRR across quarters. Exclude rows with null IRR.

PAGE 1: INDEX BUILDER
Filter controls at the top, preset to the cohort: strategy (Buyout), region (North America), vintage range (2015 to 2020), size bucket (All). Changing a control rebuilds the index.
KPI tiles for 2026-06-30: fund count in the index; cohort median IRR with the gap in points against the Harborline Broad Private Equity Index; cohort pooled TVPI against the benchmark pooled TVPI; cohort pooled DPI.
One chart that is the point of the page: cohort median IRR by quarter end from 2017-12-31 to 2026-06-30 as a line, with the broad PE benchmark POOLED_IRR_PCT as a second line on the same axis.
A table by vintage year for 2026-06-30: fund count, median IRR, pooled TVPI, pooled DPI, and the HPCI-BUYOUT-NA pooled IRR for that vintage with the gap.
A short plain-language summary line generated from the numbers, for example "49 funds; median IRR 15.9 percent, 2.6 points above the broad PE benchmark".

PAGE 2: FUND SIZE SPLIT
Same cohort and filters carried over. Split by SIZE_BUCKET (SMALL under 1B, MID_MARKET 1B to 5B, MEGA over 5B).
A grouped bar chart of median IRR by size bucket at 2026-06-30 with the broad PE benchmark as a reference line.
A line chart of median IRR by quarter end for each size bucket.
A table by size bucket: fund count, total commitments, median IRR, pooled TVPI, pooled DPI, number of funds using a subscription line.
Call out in one sentence which bucket leads and by how many points, and note that the published index is capital weighted so mega funds carry more weight there than in the median.

PAGE 3: CASH-FLOW PACING
Same cohort carried over. Use V_CASH_FLOW_PACING_QUARTERLY grouped by FUND_AGE_QUARTERS: capital calls, distributions and net cash flow as a percent of commitments (SUM of the flow divided by SUM of FUND_SIZE_USD_M times 100) and median DPI at each age.
A pacing chart of calls (negative) and distributions (positive) by fund age with net cash flow as a line (the J-curve).
A second chart of median DPI by fund age for the cohort against vintages 2021 to 2022 (same strategy and region) to show the slower distribution pace of the newer vintages.
A table by vintage year for the cohort: paid-in percent, distributed percent of commitment, pooled DPI at 2026-06-30, and the last four quarters of net cash flow.
One sentence that states at which fund age the cohort turned cash-flow positive.

DESIGN
Calm and quantitative, few KPI tiles, tabular numerals, percent with one decimal, multiples with two decimals and an x suffix. Top stepper Index Builder -> Fund Size Split -> Cash-Flow Pacing. Preserve the filters across pages. Label every benchmark series "Harborline Broad PE Index" or "HPCI-BUYOUT-NA" so the comparison is explicit. No forecasts; everything shown is reported data to 2026-06-30.
```
