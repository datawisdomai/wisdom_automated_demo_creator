# Data Platform Wiki — Store Analytics Mart (onboarding notes)

Letterhead: Nordmark Dagligvaror AB — Data Platform Team
Page: /wiki/data-platform/store-analytics-mart
Last edited: 2026-09-26 by Karl Öberg (Demand Planning Analytics); previous edit 2026-09-24 by Amir Rashidi
Audience: analysts, banner controllers, the AI analytics layer

## What this page covers

How the store analytics mart and the campaign mart are built, where each table comes from, which views to use for which question, and how the Grosshallen import-purchasing platform (still on Teradata) is federated into the same analytics domain.

## 1. Platforms

- **Snowflake** `NORDMARK_POC.ANALYTICS` is the store performance mart: daily store sales, weekly store x category sales with availability and waste, costs, promotions, loyalty, assortment, catchments and competitor events, plus nine certified views (`V_*`). Loaded nightly; the demo snapshot is as of 2026-09-30.
- **Teradata** (database `wisdomai`) is the import-purchasing platform that came with the Grosshallen acquisition in January 2025. It holds the supplier master, the imported SKU master and every inbound purchase-order line. It has not been migrated. It is attached to the analytics domain as the read-only federated connection **Ali-TD**; use Teradata SQL there (`TOP n`, tables qualified as `wisdomai.RTL_...`).
- The two platforms share keys: `NONFOOD_ASSORTMENT.PRODUCT_KEY` = `wisdomai.RTL_DIM_PRODUCT.product_key` and `NONFOOD_ASSORTMENT.SUPPLIER_KEY` = `wisdomai.RTL_DIM_SUPPLIER.supplier_key`.

## 2. Table lineage

| Table | Source | Grain | Refresh |
|---|---|---|---|
| STORE_DAILY_SALES | Extenda POS | store x day | nightly |
| SALES_WEEKLY_STORE_CATEGORY | POS + Relex availability audits | store x ISO week x category | weekly (Tuesday) |
| STORE_MONTHLY_COSTS | SAP | store x month | month-end + 5 |
| PROMOTIONS, PROMOTION_RESULTS | Campaign planning tool + POS | campaign; campaign x store | after each campaign |
| LOYALTY_ACTIVITY_MONTHLY | Loyalty CRM | home store x month x segment | month-end + 3 |
| STORE_ASSORTMENT_MONTHLY | Range management | store x month x category | monthly |
| NEIGHBORHOODS | Market-data provider | catchment | yearly (last 2026-02) |
| COMPETITOR_EVENTS | Regional manager log (SharePoint list) | event | ad hoc |
| NONFOOD_ASSORTMENT, NONFOOD_AVAILABILITY_MONTHLY | Relex (Grosshallen non-food) keyed by the purchasing platform | SKU; store x month x SKU | monthly |
| ARTIKEL | Range management (article master) | article | on change |
| KAMPANJ | Chain planning tool | campaign | daily (Airflow `dw_campaign_mart_daily`) |
| KAMPANJ_ARTIKEL_VECKA | Chain planning tool (purchase forecast, planned quantity) + CatBoost forecast feed + POS (actual sold) | campaign x week x article | daily; actuals land the Tuesday after the campaign week |
| KAMPANJ_BUTIK_VECKA | Chain planning tool allocation + POS | campaign x store x week | weekly (Tuesday) |
| ARTIKEL_KOSTNAD_MANAD | Finance system, NOT migrated: an illustrative monthly extract maintained by Demand Planning (column KALLA) | article x month | monthly, manual |
| CALENDAR, BANNERS, PRODUCT_CATEGORIES, STORES, DATA_DICTIONARY | Reference data | — | on change |

## 3. Which view answers which question

- Group or banner KPIs by month or quarter (sales, margin, transactions, basket, LFL, EBIT): `V_BANNER_KPI_MONTHLY`. Group = sum of banners. Quarter = sum of months with the same `QUARTER_LABEL`.
- Store KPIs by month, with last year and growth: `V_KPI_STORE_MONTHLY`.
- Which stores grow or decline over the rolling 12 months and whether it is transactions or basket: `V_STORE_GAP_DECOMPOSITION`.
- A store against similar stores (its peer cluster median): `V_PEER_COMPARISON`.
- Stores below their local potential, the SEK gap and its rank in the banner, with catchment demographics and competition: `V_CATCHMENT_POTENTIAL`.
- Promotions with strong sales but weak margin: `V_PROMO_EFFECTIVENESS` (`PROMO_VERDICT`, `UPLIFT_RANK`, `MARGIN_RANK_FROM_BOTTOM`).
- Availability against sales in the last 13 weeks, store x category: `V_AVAILABILITY_VS_SALES` (filter Dairy and Bread & Bakery for the weekly top-up trip story).
- Segments visiting or spending less: `V_LOYALTY_SEGMENT_TRENDS`.
- Non-food stockouts and lost sales by supplier: `V_NONFOOD_AVAILABILITY_BY_SUPPLIER` (Snowflake), then supplier names and purchase-order lateness from Teradata.

Campaign mart (added 2026-09):

- The planners' Kampanjrapport (campaign performance and forecast accuracy by chain and week, one row per week and article with planned quantity, CatBoost sold forecast, chain purchase forecast, actual sold and both forecast errors): `V_KAMPANJRAPPORT`. This is the view the MicroStrategy report of the same name reads; the numbers are identical.
- Forecast bias by tactic type, perishability and week (ratio of sums): `V_PROGNOSFEL_TAKTIK`.
- A campaign's forecast deviation by store, with peer cluster and a flag for a competitor event within 2 km in the previous 90 days: `V_KAMPANJ_BUTIK_AVVIKELSE`.
- The margin cost of over-forecasting (waste plus clearance markdown) by campaign, week and quarter: `V_KAMPANJ_MARGINALEFFEKT`. ILLUSTRATIVE cost data; the `KALLA` column carries the label and must be shown with any figure.
- Upcoming campaign weeks with both forecasts, the gap, the planning flag (perishable and gap above 15 percent), the proposed cut in whole layers and the margin it protects: `V_KAMPANJ_KOMMANDE`.

## 4. Rules the views already apply

- Like-for-like uses `STORES.IS_LFL_COMPARABLE` (opened before 2024-10-01, not closed). Converted store Grosshallen Sundsvik is excluded.
- Ratios are computed as sums over sums. Do not average percentages across stores.
- Rolling-12-month windows come from `CALENDAR.ROLLING_12M_BUCKET`: R12_CUR 2025-10-01..2026-09-30, R12_PRIOR 2024-10-01..2025-09-30.
- Availability is sales-weighted. The last-13-weeks window is weeks starting 2026-06-29 through 2026-09-21.
- Cluster medians in `V_PEER_COMPARISON` and `V_CATCHMENT_POTENTIAL` are medians over comparable stores of the cluster.

## 4b. Campaign mart: join paths and rules

- `KAMPANJ_ARTIKEL_VECKA` joins `KAMPANJ` on `KAMPANJ_ID` and `ARTIKEL` on `ARTIKEL_ID`; the campaign week is the ISO week of `KAMPANJ.LEVERANS_FRAN` and is already materialised on the fact as `KALENDER_VECKA_ID` / `VECKA_LABEL` / `VECKA_START` (Monday). Join `CALENDAR` on `VECKA_START` for the quarter.
- `KAMPANJ_BUTIK_VECKA` joins `STORES` on `STORE_ID`; only stores of the campaign's chain that were open, completed weeks only.
- `ARTIKEL_KOSTNAD_MANAD` joins on `ARTIKEL_ID` and the month of the campaign week (`CALENDAR.MONTH_START_DATE` of `VECKA_START`, or of `LEVERANS_FRAN` for upcoming campaigns).
- `KAMPANJ.PROMOTION_ID` links a campaign to the category promotion in `PROMOTIONS` where one exists (for example Sommarpris Veckans pris, 2026-W26, belongs to Sommarpris 2026).
- Forecast error and bias are ratios of sums at every level; the views do this. Do not average `PROGNOSFEL_*_PCT` across rows.
- Rows with `FAKTISK_SALD IS NULL` are future weeks (after 2026-09-30); `V_KAMPANJRAPPORT.AR_AVSLUTAD` marks completed rows and `V_KAMPANJ_KOMMANDE` holds the future ones.
- The CatBoost forecast feed (`load_catboost_forecast_feed`) has been in production since February 2026; forecasts before that are back-filled from the model's historical runs.
- Cost: there is no cost in the warehouse from the finance system. `ARTIKEL_KOSTNAD_MANAD` is an illustrative extract and every row says so (`KALLA`). When the finance migration lands, the view definitions stay and the table is replaced.

## 5. Federated query pattern (Snowflake + Teradata)

The analytics layer runs SQL on one connection at a time. For questions that cross platforms, run two queries and combine the results on the shared key:

1. Snowflake: lost sales, availability and stockout days by `SUPPLIER_KEY` from `V_NONFOOD_AVAILABILITY_BY_SUPPLIER` (filter store and months).
2. Teradata: supplier name, country, lead time and on-time rate from `wisdomai.RTL_DIM_SUPPLIER`; average `days_late` and the share of `Short-Received` lines from `wisdomai.RTL_FACT_PURCHASE_ORDER_LINE` grouped by `supplier_key` (Teradata dialect: `SELECT TOP 10 ...`, `CAST(days_late AS DECIMAL(10,4))` before averaging).
3. Join on supplier key in the analysis step and present one table.

Known result for the record (September 2026): supplier keys 39 Sterling Trading, 26 Frontier Trading and 52 Lakeshore Industries have the highest average days late and account for about two thirds of Grosshallen non-food lost sales.

## 6. Gotchas

- `V_KPI_STORE_MONTHLY.LFL_GROWTH_PCT` is NULL for non-comparable stores by design; `SALES_GROWTH_PCT` is populated for all.
- `PROMOTION_RESULTS` only contains stores that ran the campaign; Kronmat campaigns have about 110 to 120 participating stores.
- `COMPETITOR_EVENTS.ESTIMATED_SALES_IMPACT_PCT` is a judgement by the regional manager, not a measured effect; measure the effect from `V_KPI_STORE_MONTHLY` before and after the event date.
- Teradata column names are lower case and `supplier_name` values are plain text; Snowflake identifiers are upper case.
- The Teradata connection is read-only and owned by the purchasing team; do not request write access through the platform team.

## 7. Contacts

Store Analytics steward Amir Rashidi (#store-ops-analytics), Demand Planning Analytics Karl Öberg (#demand-planning, campaign mart and the CatBoost feed), Loyalty data Linnea Forsberg, Supply Chain data Per Hedlund, Grosshallen non-food and the purchasing platform Maria Holm's team (Tobias Wennerström).
