# Business Glossary and Data Ownership Register

Owner: Data Governance, Harborline Private Capital
Maintained by: Index Research (performance terms) and Fund Data Operations (contribution and extraction terms)
Last review: 2026-09-18
Scope: the private-capital analytics warehouse HARBORLINE_POC.ANALYTICS

## How to read this register

Each entry gives the business definition, the business owner accountable for it, the data steward who maintains it, the system of record and the warehouse table or column the term maps to. Synonyms are the words clients and analysts actually use on the portal, in Slack and in meetings.

## Funds, managers and indices

| Term | Definition | Synonyms | Business owner | Steward | System of record | Warehouse |
|---|---|---|---|---|---|---|
| Fund | A private-capital fund for which Harborline receives cash flows and NAVs | vehicle, partnership, L.P. | Head of Index Research | Fund Data Operations | Fund master (FundHub) | FUNDS |
| Manager | The general partner that manages the fund | GP, sponsor, firm, manager | Head of Index Research | Fund Data Operations | FundHub | MANAGERS |
| Strategy | Buyout, Growth, Venture, Private Credit, Real Estate or Infrastructure | asset class, sub-asset class, PE (buyout), VC (venture), private debt (private credit), infra | Head of Index Research | Index Research | FundHub | FUNDS.STRATEGY |
| Region | Primary investment region: North America, Europe, Asia-Pacific or Global | geography, NA, US, EU, APAC | Head of Index Research | Index Research | FundHub | FUNDS.REGION |
| Vintage year | Year of the fund's first capital call | vintage, cohort year | Head of Index Research | Index Research | FundHub | FUNDS.VINTAGE_YEAR |
| Fund size | Total limited-partner commitments in USD millions | commitments, committed capital, fund commitments | Head of Index Research | Fund Data Operations | FundHub | FUNDS.FUND_SIZE_USD_M |
| Size bucket | SMALL under 1B, MID_MARKET 1B to 5B, MEGA over 5B | mid-market, middle market, mega, large cap, lower mid | Head of Index Research | Index Research | derived | FUNDS.SIZE_BUCKET |
| Fund status | INVESTING (first five years), HARVESTING, LIQUIDATED | active, wound up, in liquidation | Head of Index Research | Fund Data Operations | derived | FUNDS.FUND_STATUS |
| Harborline index | A published pooled benchmark in the HPCI family | HPCI, benchmark, index, the broad PE benchmark (HPCI-BROAD-PE) | Head of Product Development | Index Research | Index engine | BENCHMARKS, BENCHMARK_QUARTERLY, V_BENCHMARK_QUARTERLY |
| Matching index | The strategy-and-region index assigned to a fund for comparisons | peer index, the index, comparable benchmark | Head of Index Research | Index Research | Index engine | FUNDS.BENCHMARK_ID |
| Custom index | A client-defined cohort pooled with the standard rules | cohort, peer group, custom benchmark, universe cut | Head of Product Development | Index Research | Portal (Premium Analytics) | V_COHORT_INDEX_QUARTERLY |

## Performance and cash flows

| Term | Definition | Synonyms | Business owner | Steward | System of record | Warehouse |
|---|---|---|---|---|---|---|
| NAV | Residual value attributable to LPs at quarter end, net of the credit line balance | net asset value, residual value, unrealised value | Head of Index Research | Fund Data Operations | Contribution feed | FUND_QUARTERLY_NAV.NAV_USD_M |
| Paid-in capital | Cumulative capital called from LPs | called capital, contributed capital, drawn, called down | Head of Index Research | Fund Data Operations | Contribution feed | FUND_QUARTERLY_NAV.CUMULATIVE_CALLED_USD_M |
| Distributions | Cumulative cash and stock returned to LPs | realizations, proceeds, cash back, capital returned | Head of Index Research | Fund Data Operations | Contribution feed | FUND_QUARTERLY_NAV.CUMULATIVE_DISTRIBUTED_USD_M |
| Net IRR | Annualised since-inception return to LPs net of fees and carry | IRR, SI IRR, since-inception IRR, net return | Head of Index Research | Index Research | Index engine | FUND_QUARTERLY_NAV.IRR_SINCE_INCEPTION_PCT |
| TVPI | (NAV + distributions) / paid-in | total value multiple, MOIC, multiple | Head of Index Research | Index Research | Index engine | FUND_QUARTERLY_NAV.TVPI |
| DPI | Distributions / paid-in | realised multiple, cash-on-cash | Head of Index Research | Index Research | Index engine | FUND_QUARTERLY_NAV.DPI |
| RVPI | NAV / paid-in | residual multiple, unrealised multiple | Head of Index Research | Index Research | Index engine | FUND_QUARTERLY_NAV.RVPI |
| Capital call | A dated LP payment into the fund | drawdown, call notice, contribution | Head of Index Research | Fund Data Operations | Contribution feed | FUND_CASH_FLOWS where FLOW_TYPE = CAPITAL_CALL |
| Distribution (flow) | A dated payment from the fund to LPs | realization, dividend, recap | Head of Index Research | Fund Data Operations | Contribution feed | FUND_CASH_FLOWS where FLOW_TYPE = DISTRIBUTION |
| Pacing | Calls, distributions and net cash flow by fund age | J-curve, cash-flow profile, pacing curve | Head of Product Development | Index Research | derived | V_CASH_FLOW_PACING_QUARTERLY |
| Subscription credit line | Borrowing secured on undrawn commitments used to bridge calls | sub line, capital call facility, credit facility, line of credit, LOC, bridge line | Head of Index Research | Fund Data Operations | Contribution feed and GP reports | FUNDS.USES_SUBSCRIPTION_LINE, SUBSCRIPTION_LINE_LIMIT_USD_M, FUND_QUARTERLY_NAV.CREDIT_LINE_BALANCE_USD_M |
| Line IRR gap | Average IRR with a line minus without, same vintage strategy and age | sub-line effect, IRR flattering, line uplift | Head of Index Research | Index Research | derived | V_SUBSCRIPTION_LINE_IRR_GAP |

## Clients and extraction

| Term | Definition | Synonyms | Business owner | Steward | System of record | Warehouse |
|---|---|---|---|---|---|---|
| Allocator | A limited-partner client on the Harborline portal | LP, client, investor, pension, endowment | Head of Client Solutions | Client Data | Portal CRM | ALLOCATORS |
| Commitment | An allocator's commitment to a covered fund | position, holding, allocation, sleeve (by vintage) | Head of Client Solutions | Client Data | Portal CRM | ALLOCATOR_COMMITMENTS, V_ALLOCATOR_HOLDINGS |
| Portfolio vs benchmark | Commitment-weighted fund IRR against the matching indices | relative performance, gap to index, excess return | Head of Product Development | Index Research | derived | V_ALLOCATOR_VINTAGE_VS_BENCHMARK |
| Portal tier | Standard or Premium Analytics subscription | tier, SKU, premium | Head of Product Development | Client Data | Portal CRM | ALLOCATORS.PORTAL_TIER |
| Report extraction | Figures read from a GP quarterly report by harborline-docai-2.3 | extraction, parsed report, OCR figures | Head of Fund Data Operations | Fund Data Operations | Document pipeline | FUND_REPORT_EXTRACTS |
| Extraction reconciliation | Comparison of extracted and published figures | match check, variance check | Head of Fund Data Operations | Fund Data Operations | derived | V_REPORT_EXTRACTION_RECONCILIATION |
| Review status | AUTO_ACCEPTED, ANALYST_REVIEW (confidence below 0.90) or CORRECTED | review queue, exceptions | Head of Fund Data Operations | Fund Data Operations | Document pipeline | FUND_REPORT_EXTRACTS.REVIEW_STATUS |

## Standing facts the stewards certify

- The latest published quarter is 30 June 2026; the as-of date for the warehouse is 15 October 2026.
- Calder Ridge Capital Partners IV (FND-0117) is the reference fund used in client training: NAV 2,614.0, paid-in 2,880.0, distributions 1,152.0, line balance 210.0, net IRR 18.4 percent at 30 June 2026.
- Westbrook State Retirement System (ALC-001) is the reference allocator; its 2018 sleeve lags its matching indices because of Bramblewood Ventures III and Sable Point Ventures II.
