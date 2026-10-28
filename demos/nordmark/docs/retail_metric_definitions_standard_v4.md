# Store Performance Metric Definitions Standard

Letterhead: Nordmark Dagligvaror AB — Group Finance, FP&A and Store Operations Analytics
Document: FIN-STD-011 Store Performance Metric Definitions, version 4.1
Effective: 2026-09-15
Owner: Head of FP&A (Cecilia Marklund)
Data steward: Store Analytics Data Domain Steward (Amir Rashidi)
Classification: Internal. Certified definitions for group, banner and store reporting.

## 1. Purpose

This standard defines the sales, margin, customer, availability and local-market metrics used in the weekly store review, the monthly banner P&L and the board pack. Any report, dashboard or AI-generated answer that uses one of these names must use the definition here. Variants must carry a different name.

## 2. Periods and calendar

- Nordmark reports on calendar quarters. 2026-Q3 is July to September 2026. The physical key is CALENDAR.QUARTER_LABEL.
- Months are keyed by CALENDAR.MONTH_START_DATE (first day of the month). Weeks are ISO weeks keyed by CALENDAR.WEEK_START_DATE (Monday).
- "Rolling 12 months" (R12) is the 12 months ending at the reporting date. At the 2026-09-30 reporting date R12 is 2025-10-01 to 2026-09-30 and the prior R12 is 2024-10-01 to 2025-09-30 (CALENDAR.ROLLING_12M_BUCKET R12_CUR and R12_PRIOR).
- "Last 13 weeks" means the 13 complete ISO weeks before the reporting date: weeks starting 2026-06-29 through 2026-09-21.

## 3. Net sales

**Definition.** Net sales are sales to customers in SEK excluding VAT, after promotional discounts and markdowns, including online orders fulfilled by the store. Physical mapping: STORE_DAILY_SALES.NET_SALES_SEK (store x day) and SALES_WEEKLY_STORE_CATEGORY.NET_SALES_SEK (store x week x category). The two agree within rounding for any store and week.

Note on 2026: the food VAT rate was cut from 12 to 6 percent on 2026-04-01. Net sales exclude VAT, so the cut does not change reported net sales directly; it lifted volumes. Shelf prices fell about 2 percent year on year in 2026 (food price deflation), so 2026 growth is volume driven.

## 4. Like-for-like growth (LFL)

**Definition.** Like-for-like growth is the net sales of comparable stores in the period divided by the net sales of the same stores in the same period a year earlier, minus one. A comparable store traded for the whole of both periods: opened before 2024-10-01 and not closed or converted (STORES.IS_LFL_COMPARABLE = TRUE).

- Banner and group LFL are ratios of summed sales. Never average store percentages.
- Total sales growth includes new, closed and converted stores and is reported separately as sales growth.
- Physical mapping: V_BANNER_KPI_MONTHLY.LFL_GROWTH_PCT (month versus same month last year) and, for the rolling 12 months, SUM(SALES_R12_SEK) / SUM(SALES_PRIOR_R12_SEK) - 1 from V_STORE_GAP_DECOMPOSITION.

**Decomposition.** The change in a store's sales between the prior R12 and the current R12 is split into a transactions effect, (transactions now - transactions before) x average basket before, and a basket effect, (basket now - basket before) x transactions now. The larger absolute effect is the growth driver (V_STORE_GAP_DECOMPOSITION.GROWTH_DRIVER).

## 5. Gross profit and gross margin percent

**Definition.** Gross profit is net sales minus cost of goods sold, where cost of goods sold includes the cost of waste and the cost of markdowns. Gross margin percent is gross profit divided by net sales for the slice, computed as a ratio of sums. Banner budget margins: Kronmat 27.0 percent, Torghallen 30.5 percent, Grosshallen 24.5 percent (BANNERS.TARGET_GP_PCT).

## 6. Transactions and average basket

- Transactions are customer receipts (STORE_DAILY_SALES.TRANSACTIONS). Online orders count as one transaction each.
- Average basket is net sales divided by transactions, in SEK. Items per basket is units sold divided by transactions.
- Loyalty sales share is the net sales on identified loyalty transactions divided by net sales.

## 7. Store operating result (EBIT)

**Definition.** Store EBIT is gross profit minus store operating costs: labour (including social charges), occupancy, inbound logistics charged to the store, local marketing, other opex and depreciation (STORE_MONTHLY_COSTS). Central costs are not allocated. Banner EBIT is the sum of its stores; quarterly EBIT is the sum of the three months (V_BANNER_KPI_MONTHLY.EBIT_SEK grouped by QUARTER_LABEL). EBIT percent is EBIT divided by net sales.

## 8. On-shelf availability (OSA)

**Definition.** On-shelf availability is the share of audited SKU-hours in which the item was available on the shelf, from the Relex availability audits, reported per store, week and category (SALES_WEEKLY_STORE_CATEGORY.ON_SHELF_AVAILABILITY_PCT). When aggregating, weight by net sales. Target 96 percent. Alert threshold 94 percent: a store below 94 percent in Dairy and Bread & Bakery for four consecutive weeks is escalated to the regional manager. Stockout hours are the shelf-hours out of stock across the category in the week.

For the imported non-food range the equivalent is the share of trading days the SKU was in stock (NONFOOD_AVAILABILITY_MONTHLY.ON_SHELF_AVAILABILITY_PCT), weighted by demand (sales plus lost sales). Lost sales are the estimated sales lost to stockouts.

## 9. Waste and markdowns

- Waste rate is the cost value of goods written off divided by net sales (SALES_WEEKLY_STORE_CATEGORY.WASTE_SEK). Managed in fresh categories.
- Markdown rate is the value of price reductions on short-dated and clearance items divided by net sales (MARKDOWN_SEK). Markdowns are not promotions.

## 10. Promotions

- Uplift is promotional-period sales of the promoted category divided by the baseline (the expected sales over the same weeks without the campaign, from the pre-period), minus one.
- Margin dilution is the baseline gross margin percent minus the gross margin percent during the campaign, in points.
- Incremental gross profit is promotional gross profit minus baseline gross profit; it is negative when the discount cost more than the extra volume earned.
- Verdicts (V_PROMO_EFFECTIVENESS.PROMO_VERDICT): "Strong sales weak margin" means uplift of at least 25 percent with dilution of at least 4 points.

## 11. Loyalty metrics

- Active members: members with at least one identified purchase in the month, by home store (the store they visit most).
- Visits: identified transactions; visit frequency: visits divided by active members.
- Segments: Families, Seniors, Students, Urban singles, Value seekers, Premium (LOYALTY_ACTIVITY_MONTHLY.SEGMENT). R12 versus prior changes are in V_LOYALTY_SEGMENT_TRENDS.

## 12. Local potential

- Catchment potential is the annual net sales a store of its format should achieve in its catchment: catchment grocery spend (market-data provider) times a fair share that falls with the number of competitors within 2 km (NEIGHBORHOODS.CATCHMENT_POTENTIAL_MSEK). Refreshed once a year.
- Potential index is R12 net sales divided by the catchment potential (V_CATCHMENT_POTENTIAL.POTENTIAL_INDEX). Bands: Underperforming below 0.75, Below potential 0.75 to 0.90, At potential 0.90 to 1.10, Outperforming above 1.10.
- Potential gap is the potential minus R12 sales in SEK; "the gap" in store reviews always means this number ranked within the banner.
- Peer cluster is the banner combined with the catchment type. Stores are benchmarked against the median of their own cluster (V_PEER_COMPARISON), never against the whole chain.

## 13. Private-label share

Private-label share is private-label net sales divided by category net sales (STORE_ASSORTMENT_MONTHLY.PL_SALES_SHARE), weighted by sales when aggregated. Group ambition for 2027: 30 percent at Kronmat, 25 percent at Torghallen, 22 percent at Grosshallen.

## 14. Campaign forecast accuracy

**Scope.** The campaign mart (KAMPANJ, KAMPANJ_ARTIKEL_VECKA, KAMPANJ_BUTIK_VECKA, ARTIKEL) and its views. Owner: Head of Campaign Planning; steward: Demand Planning Analytics.

- Campaign week is the ISO week of the first delivery day, KAMPANJ.LEVERANS_FRAN. Physical key KALENDER_VECKA_ID (YYYYWW), label VECKA_LABEL. The Kampanjrapport is keyed on the delivery week, not the selling days.
- Såld prognos (CatBoost) is the group demand model's sold forecast per campaign week and article (KAMPANJ_ARTIKEL_VECKA.SALD_PROGNOS_CATBOOST). Köpt prognos (kedjans prognos) is the chain's purchase forecast (KOPT_PROGNOS_KEDJAN). Planerad kvantitet is the purchase forecast rounded up to whole cases (PLANERAD_KVANTITET). Faktisk såld is the actual campaign-week sales in units (FAKTISK_SALD), NULL for weeks after the reporting date.
- Forecast error percent = (forecast − actual sold) / actual sold, for one row. Positive is an over-forecast. Physical mapping: V_KAMPANJRAPPORT.PROGNOSFEL_CATBOOST_PCT and PROGNOSFEL_KEDJAN_PCT.
- Bias for any group of rows (tactic type, chain, week, perishability) = SUM(forecast) / SUM(actual sold) − 1, a ratio of sums. Never average row percentages. Physical mapping: V_PROGNOSFEL_TAKTIK.BIAS_CATBOOST_PCT and BIAS_KEDJAN_PCT.
- Over-forecast quantity = MAX(köpt prognos − actual sold, 0) per row, summed (V_KAMPANJRAPPORT.OVERPROGNOS_KVANTITET, V_PROGNOSFEL_TAKTIK.OVERPROGNOS_KVANTITET). Absolute error = SUM(ABS(köpt prognos − actual sold)) (ABS_FEL_KEDJAN).
- Store deviation = (SUM(store forecast) − SUM(store actual)) / SUM(store actual) from KAMPANJ_BUTIK_VECKA (V_KAMPANJ_BUTIK_AVVIKELSE.AVVIKELSE_PCT per row). Stores are compared with the median of their peer cluster, as in section 12.
- Prognosgap for an upcoming campaign = köpt prognos / CatBoost − 1 (V_KAMPANJ_KOMMANDE.PROGNOSGAP_PCT). The planning flag is a perishable article with a gap above 15 percent (FLAGGA).

## 15. Margin effect of over-forecasting (illustrative)

**Status.** Purchase cost, list price and margin per article live in the finance system, which has not been migrated to the warehouse. Until it is, the campaign mart carries an illustrative monthly extract, ARTIKEL_KOSTNAD_MANAD, with the column KALLA = 'ILLUSTRATIV - finanssystem ej migrerat'. Every figure computed from it must show that label and must not be reported as a booked cost or saving.

- Margin effect = waste cost + clearance markdown cost, per campaign, week and perishability (V_KAMPANJ_MARGINALEFFEKT.MARGINALEFFEKT_SEK). Waste cost = over-forecast units × purchase cost × write-off share (SVINNKOSTNAD_SEK; the write-off share SVINNANDEL_PCT is set by shelf life and is zero for dry articles). Markdown cost = the remaining over-forecast units × half the campaign discount (NEDSATTNINGSKOSTNAD_SEK).
- Quarterly totals use CALENDAR.QUARTER_LABEL of the campaign week's Monday.
- Margin protected by an order adjustment = units cut × purchase cost × write-off share (V_KAMPANJ_KOMMANDE.SKYDDAD_MARGINAL_SEK), same illustrative status.
- Layer rounding rule: an order adjustment is expressed in whole cases (ARTIKEL.KOLLI units per case) rounded down to full pallet layers (ARTIKEL.LAV cases per layer): FLOOR((köpt prognos − CatBoost) / kolli / lav) × lav cases (FORESLAGEN_MINSKNING_KOLLI). Never cut below the CatBoost forecast.

## 16. Change log

- v4.1 (2026-09-15): added campaign forecast accuracy (section 14) and the illustrative margin effect of over-forecasting (section 15) at the request of Demand Planning.
- v4.0 (2026-07-01): added local potential, peer clusters and the sales decomposition; OSA alert threshold set to 94 percent.
- v3.2 (2025-02-01): Grosshallen added to the group reporting scope after the January 2025 acquisition.
