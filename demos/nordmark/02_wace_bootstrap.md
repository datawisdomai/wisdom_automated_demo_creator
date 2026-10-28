# Nordmark Dagligvaror — Domain Bootstrap (wACE)

Domain: **Nordmark Dagligvaror AB**, a fictional Swedish grocery group with three banners.
Warehouse: Snowflake `NORDMARK_POC.ANALYTICS` (store POS mart) plus a federated read-only Teradata source
(connection **Ali-TD**, database `wisdomai`, the import-purchasing platform: `RTL_DIM_SUPPLIER`, `RTL_DIM_PRODUCT`,
`RTL_FACT_PURCHASE_ORDER_LINE`, `RTL_VW_PURCHASE_ORDER`).
Demo as-of date: **2026-09-30** (Wednesday). Calendar quarters; the latest complete month is September 2026.
Data spans 2024-10-01 to 2026-09-30. Rolling 12 months (R12) = 2025-10-01..2026-09-30; prior R12 = 2024-10-01..2025-09-30.
All amounts in SEK excluding VAT.

---

## 1. DOMAIN OVERVIEW

Nordmark runs three banners: **Kronmat** (discount, ~120 large supermarkets, "Sweden's cheapest basket", loyalty program
Kronmat Plus), **Torghallen** (~90 neighbourhood stores incl. franchise, fresh food and ready meals, Torghallen Klubb) and
**Grosshallen** (38 out-of-town hypermarkets acquired on 2025-01-01, grocery plus an imported non-food range, Grosshallen Kort).
Group R12 net sales are about SEK 20.3 bn (Kronmat 10.0, Grosshallen 6.7, Torghallen 3.6).

The primary user is the **Head of Store Operations** with the group FP&A analytics team, measured on like-for-like sales
growth, gross margin, transactions and basket, availability, waste and markdowns, and sales versus catchment potential.
Banner directors, category managers, the loyalty lead and the data steward use the same domain.

The business situation (Q3 2026): Swedish food prices are falling (about -2 percent year on year; the food VAT rate was cut
from 12 to 6 percent on 2026-04-01) so growth is volume driven. Torghallen is the star (LFL about +4.8 percent), Kronmat is
slightly behind the market (about +2 percent) and Grosshallen is the problem child: LFL about -1.4 percent, the gap is lost
customer visits (transactions -5.6 percent) not basket (+4.4 percent), gross margin 2.3 points below Kronmat, and the banner
has only just reached break-even (Q3 2026 EBIT about +SEK 9 m after about -SEK 35 m per quarter in 2025) through structural
cost measures. One Grosshallen store (Sundsvik, Helsingborg) was converted to Kronmat on 2026-08-15.

Core mechanics represented:

- **Daily store sales** (POS): net sales, gross profit, transactions, items, loyalty-identified and online sales per store and day.
- **Weekly store x category** (POS + Relex): sales, COGS, units, promotional sales, markdowns, waste, on-shelf availability (OSA)
  and stockout hours for 17 grocery/household categories (all banners) and 6 imported non-food categories (Grosshallen only).
- **Store costs** (SAP): monthly labour, occupancy, logistics, marketing, other opex and depreciation; EBIT = gross profit - costs.
- **Promotions**: 60 campaigns with per-store outcomes (uplift versus baseline, margin dilution, incremental gross profit).
- **Loyalty** (CRM): monthly active members, visits and spend per store and customer segment (Families, Seniors, Students,
  Urban singles, Value seekers, Premium).
- **Assortment**: monthly listed SKUs and private-label share per store and category.
- **Catchments** (market-data provider): demographics, competition and the annual sales potential per store location.
- **Competitor events**: openings, closures and campaigns near stores, logged by regional managers.
- **Non-food availability**: monthly availability and lost sales per Grosshallen store and imported SKU, keyed like the Teradata
  purchasing platform (PRODUCT_KEY, SUPPLIER_KEY).

Scale: 249 stores (235 like-for-like comparable), 176K store-days, 454K store-week-category rows, 199K non-food store-SKU-months.

---

## 2. TABLE CATALOG

### 2.1 `CALENDAR` (dimension, 822 rows)
One row per day 2024-10-01..2026-12-31. `MONTH_START_DATE` keys monthly tables, `WEEK_START_DATE` (Monday) keys the weekly
fact, `QUARTER_LABEL` (e.g. 2026-Q3), Swedish holidays, trading `SEASON`, and `ROLLING_12M_BUCKET` (R12_CUR / R12_PRIOR / NULL).

### 2.2 `BANNERS` (dimension, 3 rows)
`BANNER_ID` KRM/TRG/GRH, `BANNER_NAME`, `STORE_FORMAT`, positioning, loyalty program, `ACQUIRED_DATE` (Grosshallen 2025-01-01),
typical basket, price index versus market, target gross margin, banner director.

### 2.3 `NEIGHBORHOODS` (dimension, 249 rows)
One catchment per store: `CATCHMENT_TYPE` (Urban core, Suburban family, Small town, Commuter belt, Rural hub), population and
households within 2 km, median income, family/student/senior shares, car access, `COMPETITOR_COUNT_2KM`,
`DISCOUNT_COMPETITOR_FLAG`, `NEAREST_COMPETITOR_KM`, `GROCERY_SPEND_POTENTIAL_MSEK`, `FAIR_SHARE_PCT` and
`CATCHMENT_POTENTIAL_MSEK` (= spend x fair share: the expected annual net sales of the store).

### 2.4 `STORES` (dimension, 249 rows)
`STORE_ID`, `STORE_NAME` (banner + location, e.g. Grosshallen Västerhamn), `BANNER`, `STORE_FORMAT`, `REGION` (Stockholm, Vast,
Syd, Ost, Mitt, Norr), municipality, city, `NEIGHBORHOOD_ID`, `CATCHMENT_TYPE`, `PEER_CLUSTER` (banner / catchment type),
`SALES_AREA_SQM`, `OPENED_DATE`, `ACQUIRED_DATE`, `CLOSED_DATE`, `CONVERTED_TO_BANNER`, `STORE_STATUS`, `IS_FRANCHISE`,
`IS_LFL_COMPARABLE`, store manager, parking, online pickup, coordinates.

### 2.5 `PRODUCT_CATEGORIES` (dimension, 23 rows)
`CATEGORY_ID`, `CATEGORY_NAME`, `DEPARTMENT` (Fresh, Ambient, Frozen, Household, Non-food), `IS_FRESH`, `IS_NONFOOD`,
`SOLD_IN_BANNERS`, target margin, waste-prone flag, category manager, `TERADATA_DEPARTMENT` for the non-food categories.

### 2.6 `NONFOOD_ASSORTMENT` (dimension, 250 rows)
The imported non-food range sold in Grosshallen: `PRODUCT_KEY` and `SKU` (same keys as Teradata `RTL_DIM_PRODUCT`),
name, `TERADATA_DEPARTMENT`, Nordmark `CATEGORY_NAME`, subcategory, brand, private-label flag, `SUPPLIER_KEY` (same key as
Teradata `RTL_DIM_SUPPLIER`), price tier, SEK list price and unit cost, listed since, range role, stores listed.

### 2.7 `PROMOTIONS` (dimension, 60 rows)
Campaigns by banner and category: `PROMOTION_NAME`, `MECHANIC` (Price cut, Multibuy, Loyalty price, Bundle, Clearance),
`DISCOUNT_PCT`, start/end dates, weeks, funding source and supplier funding share, loyalty-only flag, objective, owner.

### 2.8 `STORE_DAILY_SALES` (fact, 176K rows, grain = store x day)
`NET_SALES_SEK`, `GROSS_PROFIT_SEK`, `TRANSACTIONS`, `ITEMS_SOLD`, `LOYALTY_TRANSACTIONS`, `LOYALTY_SALES_SEK`, `ONLINE_ORDERS`,
`ONLINE_SALES_SEK`. Average basket = net sales / transactions.

### 2.9 `SALES_WEEKLY_STORE_CATEGORY` (fact, 454K rows, grain = store x ISO week x category)
`NET_SALES_SEK`, `COGS_SEK`, `GROSS_PROFIT_SEK`, `UNITS_SOLD`, `PROMO_SALES_SEK`, `MARKDOWN_SEK`, `WASTE_SEK`, `WASTE_UNITS`,
`ON_SHELF_AVAILABILITY_PCT` (0-1, target 0.96, alert below 0.94), `STOCKOUT_HOURS`, `INVENTORY_DAYS`.

### 2.10 `STORE_MONTHLY_COSTS` (fact, 5.8K rows, grain = store x month)
Labour, occupancy, logistics, marketing, other opex, depreciation, FTE and hours.

### 2.11 `PROMOTION_RESULTS` (fact, 5.3K rows, grain = promotion x participating store)
`PROMO_SALES_SEK`, `BASELINE_SALES_SEK`, `UPLIFT_PCT`, `PROMO_GP_PCT`, `BASELINE_GP_PCT`, `MARGIN_DILUTION_PTS`,
`MARKDOWN_COST_SEK`, `INCREMENTAL_GP_SEK`, `PROMO_UNITS`.

### 2.12 `LOYALTY_ACTIVITY_MONTHLY` (fact, 35K rows, grain = home store x month x segment)
`ACTIVE_MEMBERS`, `VISITS`, `SPEND_SEK`, `NEW_MEMBERS`, `LAPSED_MEMBERS`, `AVG_VISITS_PER_MEMBER`.

### 2.13 `STORE_ASSORTMENT_MONTHLY` (fact, 104K rows, grain = store x month x category)
`LISTED_SKUS`, `PRIVATE_LABEL_SKUS`, `PL_SALES_SHARE`, `NEW_SKUS`, `DELISTED_SKUS`, `RANGE_DEPTH_INDEX`.

### 2.14 `COMPETITOR_EVENTS` (fact, 73 rows, grain = event)
`EVENT_DATE`, `COMPETITOR_NAME`, `COMPETITOR_FORMAT`, `EVENT_TYPE`, `DISTANCE_KM`, `ESTIMATED_SALES_IMPACT_PCT`, notes.
Event CEV-001 is the Billigmat discount opening 1.1 km from Grosshallen Västerhamn on 2026-03-12.

### 2.15 `NONFOOD_AVAILABILITY_MONTHLY` (fact, 199K rows, grain = Grosshallen store x month x imported SKU)
`UNITS_SOLD`, `NET_SALES_SEK`, `ON_SHELF_AVAILABILITY_PCT`, `STOCKOUT_DAYS`, `LOST_SALES_SEK`. Join `PRODUCT_KEY` to
`NONFOOD_ASSORTMENT` for `SUPPLIER_KEY` and then to the Teradata purchasing tables.

### 2.16 `DATA_DICTIONARY` (metadata, 30 rows)
Business definitions, formulas, owners and source systems of the key columns and metrics.

### Federated (Teradata, connection Ali-TD, database `wisdomai`, read-only)
`RTL_DIM_SUPPLIER` (60 suppliers: name, country, lead_time_days, on_time_rate, payment_terms, supplier_tier),
`RTL_DIM_PRODUCT` (2,000 SKUs: sku, product_name, department, category, brand, is_private_label, supplier_key, prices),
`RTL_FACT_PURCHASE_ORDER_LINE` (134K lines: po_number, order_date, expected_date, received_date, supplier_key, product_key,
ordered_qty, received_qty, days_late, po_status Received / Short-Received / Open) and `RTL_VW_PURCHASE_ORDER` (the same lines
with supplier and product names). Teradata SQL: `TOP n` not `LIMIT`; qualify tables as `wisdomai.<table>`.

### Campaign mart (Revision 2)
- `ARTIKEL` — article master (Artikel): `ARTIKEL_ID`, `ARTIKEL_NAMN`, `KATEGORI`, `VARUMARKE`, `EGNA_MARKESVAROR`, `FARSKVARA`,
  `HALLBARHET_DAGAR`, `ENHET`, `KOLLI` (units per case), `LAV` (cases per layer), `PALL`, `ORDINARIE_PRIS_SEK`, `STATUS`.
- `KAMPANJ` — campaigns by chain and week: `KAMPANJ_ID`, `KAMPANJ_NAMN`, `KEDJA`, `TAKTIK_TYP_KOD`/`TAKTIK_TYP`,
  `KALENDER_VECKA_ID` (YYYYWW), `VECKA_LABEL`, `LEVERANS_FRAN`/`LEVERANS_TILL`, `KAMPANJ_START`/`KAMPANJ_SLUT`, `ANTAL_ARTIKLAR`,
  `PROMOTION_ID` (link to PROMOTIONS when the campaign belongs to a category promotion), `TEMA`, `ANSVARIG_PLANERARE`, `STATUS`
  (Avslutad / Pagaende / Planerad).
- `KAMPANJ_ARTIKEL_VECKA` — the report grain: `NYCKEL`, `KAMPANJ_ID`, `KEDJA`, `KALENDER_VECKA_ID`, `VECKA_LABEL`, `VECKA_START`,
  `ARTIKEL_ID`, `PLANERAD_KVANTITET`, `SALD_PROGNOS_CATBOOST`, `KOPT_PROGNOS_KEDJAN`, `LEVERERAD_KVANTITET`, `FAKTISK_SALD`,
  `KAMPANJPRIS_SEK`, `ORDINARIE_PRIS_SEK`, `KAMPANJFORSALJNING_SEK`.
- `KAMPANJ_BUTIK_VECKA` — campaign x store x week: `PROGNOS_KVANTITET` (chain forecast allocated by store size), `FAKTISK_SALD`,
  `AVVIKELSE_PCT`.
- `ARTIKEL_KOSTNAD_MANAD` — ILLUSTRATIVE article cost by month: `INKOPSPRIS_SEK`, `LISTPRIS_SEK`, `MARGINAL_PCT`, `SVINNANDEL_PCT`,
  `KALLA` = 'ILLUSTRATIV - finanssystem ej migrerat' (finance has not been migrated; never present as booked cost).

---

## 3. ANALYTICAL VIEWS

### `V_KPI_STORE_MONTHLY`
Level-1 KPIs per store and month: net sales, gross profit, `GP_PCT`, transactions, `AVG_BASKET_SEK`, items per basket, loyalty
and online shares, same month last year (`LY_*`), `SALES_GROWTH_PCT`, `LFL_GROWTH_PCT` (comparable stores only),
`TRANSACTIONS_GROWTH_PCT`, `BASKET_GROWTH_PCT`. Filter by `BANNER`, `REGION`, `CATCHMENT_TYPE`, `STORE_NAME`, `MONTH_START_DATE`.

### `V_BANNER_KPI_MONTHLY`
Banner P&L per month: stores trading, net sales, gross profit, `GP_PCT`, transactions, basket, loyalty share, `LFL_GROWTH_PCT`,
`LFL_TRANSACTIONS_GROWTH_PCT`, `LFL_BASKET_GROWTH_PCT`, operating costs, labour cost percent, `EBIT_SEK`, `EBIT_PCT`,
`QUARTER_LABEL`. Sum months for quarters; sum banners for the group.

### `V_STORE_GAP_DECOMPOSITION`
Per comparable store: R12 versus prior R12 sales, transactions and basket with `TRANSACTIONS_EFFECT_SEK`, `BASKET_EFFECT_SEK`,
`GROWTH_DRIVER` (Transactions / Basket) and `TREND` (Growing / Declining).

### `V_PEER_COMPARISON`
Per comparable store: R12 sales per sqm, LFL growth, GP percent, basket, transactions per household, OSA, markdown rate, waste
rate, private-label share, each next to the `CLUSTER_*` median of its peer cluster and the `*_GAP_*` difference.

### `V_CATCHMENT_POTENTIAL`
Per comparable store: R12 sales, `CATCHMENT_POTENTIAL_MSEK`, `POTENTIAL_INDEX`, `POTENTIAL_GAP_SEK`, `CLUSTER_MEDIAN_INDEX`,
`GAP_RANK_IN_BANNER`, `INDEX_RANK_IN_CLUSTER`, `POTENTIAL_BAND` (Underperforming < 0.75, Below potential < 0.90, At potential,
Outperforming), plus the catchment demographics and competition columns.

### `V_PROMO_EFFECTIVENESS`
Per campaign: participating stores, promo and baseline sales, `UPLIFT_PCT`, promo and baseline GP percent,
`MARGIN_DILUTION_PTS`, markdown cost, `INCREMENTAL_GP_SEK`, `UPLIFT_RANK`, `MARGIN_RANK_FROM_BOTTOM`, `PROMO_VERDICT`.

### `V_AVAILABILITY_VS_SALES`
Per store and category over the last 13 weeks: `NET_SALES_13W_SEK`, `NET_SALES_LY13_SEK`, `CATEGORY_SALES_GROWTH_PCT`,
`OSA_PCT`, `STOCKOUT_HOURS`, waste and markdown rates, `LOW_AVAILABILITY_FLAG` (OSA < 0.94), `STORE_LFL_GROWTH_PCT` (R12).

### `V_LOYALTY_SEGMENT_TRENDS`
Per store and segment: R12 versus prior active members, visits, spend, visit frequency, `VISITS_CHANGE_PCT`, `SPEND_CHANGE_PCT`,
new and lapsed members.

### `V_NONFOOD_AVAILABILITY_BY_SUPPLIER`
Per Grosshallen store, month, `SUPPLIER_KEY`, Teradata department and category: SKUs, units, sales, `OSA_PCT`, stockout days,
`LOST_SALES_SEK`, `LOST_SALES_SHARE`. The Snowflake half of the federation question.

### `V_KAMPANJRAPPORT`
The campaign planners' Kampanjrapport grid: one row per campaign week and article (`NYCKEL` = `VECKA_LABEL` || - || `ARTIKEL_ID`)
with `KEDJA`, `KAMPANJ_NAMN`, `TAKTIK_TYP`, `KATEGORI`, `FARSKVARA`, `PLANERAD_KVANTITET`, `SALD_PROGNOS_CATBOOST`,
`KOPT_PROGNOS_KEDJAN`, `FAKTISK_SALD` (NULL for future weeks), `PROGNOSFEL_CATBOOST_PCT`, `PROGNOSFEL_KEDJAN_PCT`
(= (forecast - actual) / actual, positive = over-forecast), `OVERPROGNOS_KVANTITET`, `KAMPANJFORSALJNING_SEK`, `AR_AVSLUTAD`.
Filter by `KEDJA` and `VECKA_LABEL` (e.g. 'Kronmat', '2026-W36'); totals are ratios of sums.

### `V_PROGNOSFEL_TAKTIK`
Forecast bias per chain, tactic type, perishability and campaign week (completed weeks only): summed actual and both
forecasts, `BIAS_CATBOOST_PCT`, `BIAS_KEDJAN_PCT`, `ABS_FEL_KEDJAN`, `OVERPROGNOS_KVANTITET`. Sum the columns across weeks
before computing a bias.

### `V_KAMPANJ_BUTIK_AVVIKELSE`
Campaign forecast deviation per store and week (`PROGNOS_KVANTITET`, `FAKTISK_SALD`, `AVVIKELSE_PCT`) with `STORE_NAME`,
`BANNER`, `REGION`, `PEER_CLUSTER` and `HAR_KONKURRENTHANDELSE_90D` (a competitor event within 2 km in the 90 days before
the week). The store drill of a forecast variance.

### `V_KAMPANJ_MARGINALEFFEKT`
Margin cost of over-forecasting per campaign, week, quarter and perishability on ILLUSTRATIVE cost data: `SVINNKOSTNAD_SEK`
(waste on perishables), `NEDSATTNINGSKOSTNAD_SEK` (clearance markdowns), `MARGINALEFFEKT_SEK`, `KALLA` (always
'ILLUSTRATIV - finanssystem ej migrerat'; show it with every cost figure).

### `V_KAMPANJ_KOMMANDE`
Upcoming campaign weeks after 2026-09-30 with both forecasts, `PROGNOSGAP_PCT` (chain forecast / CatBoost - 1), `FLAGGA`
(perishable and gap > 15 percent), `FORESLAGEN_MINSKNING_KOLLI` (cases rounded down to whole layers), `SKYDDAD_MARGINAL_SEK`,
`DAGAR_TILL_LEVERANS`, `KOLLI`, `LAV`. The agent's and the order-adjustment draft's source.

---

## 4. ENTITY RELATIONSHIP MAP

- `STORES.BANNER_ID` -> `BANNERS.BANNER_ID`; `STORES.NEIGHBORHOOD_ID` -> `NEIGHBORHOODS.NEIGHBORHOOD_ID` (1:1).
- `STORE_DAILY_SALES.STORE_ID` -> `STORES`; `STORE_DAILY_SALES.CALENDAR_DATE` -> `CALENDAR.CALENDAR_DATE`.
- `SALES_WEEKLY_STORE_CATEGORY.STORE_ID` -> `STORES`; `.CATEGORY_ID` -> `PRODUCT_CATEGORIES`; `.WEEK_START_DATE` = `CALENDAR.WEEK_START_DATE`.
- `STORE_MONTHLY_COSTS`, `LOYALTY_ACTIVITY_MONTHLY`, `STORE_ASSORTMENT_MONTHLY`, `NONFOOD_AVAILABILITY_MONTHLY`: `STORE_ID` -> `STORES`,
  `MONTH_START_DATE` = `CALENDAR.MONTH_START_DATE`.
- `PROMOTION_RESULTS.PROMOTION_ID` -> `PROMOTIONS`; `PROMOTIONS.CATEGORY_ID` -> `PRODUCT_CATEGORIES`; `PROMOTIONS.BANNER_ID` -> `BANNERS`.
- `COMPETITOR_EVENTS.STORE_ID` -> `STORES`.
- `NONFOOD_AVAILABILITY_MONTHLY.PRODUCT_KEY` -> `NONFOOD_ASSORTMENT.PRODUCT_KEY` -> (federated) `wisdomai.RTL_DIM_PRODUCT.product_key`;
  `NONFOOD_ASSORTMENT.SUPPLIER_KEY` -> (federated) `wisdomai.RTL_DIM_SUPPLIER.supplier_key` and `wisdomai.RTL_FACT_PURCHASE_ORDER_LINE.supplier_key`.
- Views join on `STORE_ID` / `STORE_NAME`; `V_PEER_COMPARISON` and `V_CATCHMENT_POTENTIAL` share `STORE_ID`.

---

## 5. METRICS DICTIONARY

- **Net sales**: SUM(NET_SALES_SEK), SEK excluding VAT after discounts and markdowns.
- **Gross margin percent**: SUM(GROSS_PROFIT_SEK) / SUM(NET_SALES_SEK). Ratio of sums; never average percentages.
- **Transactions**: SUM(TRANSACTIONS). **Average basket**: SUM(NET_SALES_SEK) / SUM(TRANSACTIONS).
- **Like-for-like (LFL) growth**: comparable-store sales this period / same period last year - 1 (IS_LFL_COMPARABLE = TRUE).
  Banner and group LFL in `V_BANNER_KPI_MONTHLY.LFL_GROWTH_PCT` (monthly) and from `V_STORE_GAP_DECOMPOSITION` (rolling 12 months).
- **Transactions / basket effect**: (tx_cur - tx_prior) x basket_prior and (basket_cur - basket_prior) x tx_cur.
- **EBIT**: gross profit - operating costs (`V_BANNER_KPI_MONTHLY.EBIT_SEK`); EBIT percent = EBIT / net sales.
- **On-shelf availability (OSA)**: sales-weighted ON_SHELF_AVAILABILITY_PCT; target 0.96, alert below 0.94.
- **Waste rate**: SUM(WASTE_SEK) / SUM(NET_SALES_SEK). **Markdown rate**: SUM(MARKDOWN_SEK) / SUM(NET_SALES_SEK).
- **Private-label share**: PL_SALES_SHARE (sales-weighted average).
- **Potential index**: R12 sales / (CATCHMENT_POTENTIAL_MSEK x 1e6). **Potential gap**: potential - R12 sales.
- **Promotion uplift**: promo sales / baseline sales - 1. **Margin dilution**: baseline GP percent - promo GP percent.
- **Visit frequency**: visits / active members. **Visits change**: visits R12 / visits prior R12 - 1.
- **Non-food lost sales**: SUM(LOST_SALES_SEK); **non-food OSA**: demand-weighted availability.

---

## 6. SYNONYMS MASTER LIST

- revenue, turnover, sales, omsättning -> NET_SALES_SEK
- margin, gross margin, GP, bruttomarginal -> GP_PCT / GROSS_PROFIT_SEK
- receipts, baskets, customer count, visits, kvitton -> TRANSACTIONS (or loyalty VISITS when the question is about members)
- basket size, ticket, snittköp -> AVG_BASKET_SEK
- LFL, like for like, comparable, jämförbara butiker, same-store -> LFL_GROWTH_PCT / IS_LFL_COMPARABLE
- availability, OSA, in-stock, stockouts, out of stock, tillgänglighet -> ON_SHELF_AVAILABILITY_PCT / STOCKOUT_HOURS
- shrink, waste, svinn -> WASTE_SEK / waste rate
- markdowns, price reductions, nedsättningar -> MARKDOWN_SEK / markdown rate
- EBIT, operating profit, rörelseresultat -> EBIT_SEK
- chain, format, fascia -> BANNER
- hypermarket banner, the acquired banner, the acquisition -> Grosshallen
- discount banner -> Kronmat; neighbourhood banner, convenience banner -> Torghallen
- catchment, trade area, neighbourhood, local market, upptagningsområde -> NEIGHBORHOODS / CATCHMENT_TYPE
- potential, fair share, local potential -> CATCHMENT_POTENTIAL_MSEK / POTENTIAL_INDEX
- peers, similar stores, comparable stores (in the peer sense), cluster -> PEER_CLUSTER
- private label, own brand, EMV, egna märkesvaror -> PL_SALES_SHARE
- promo, campaign, offer, kampanj -> PROMOTIONS / V_PROMO_EFFECTIVENESS
- members, loyalty customers, club, Plus, Klubb, Kort -> LOYALTY_ACTIVITY_MONTHLY
- import suppliers, purchasing platform, inbound, POs, purchase orders, Teradata -> federated RTL_* tables
- Västerhamn, Vasterhamn, the hero store, the problem store -> Grosshallen Västerhamn (ST-0001)
- Nordstaden, the benchmark store, the playbook store -> Grosshallen Nordstaden (ST-0002)
- kampanjrapport, campaign report, campaign performance and forecast accuracy, the planners' report -> V_KAMPANJRAPPORT (skill kampanjrapport)
- kedja -> KEDJA (chain = banner); vecka, campaign week, Calendar_Week_Id -> VECKA_LABEL / KALENDER_VECKA_ID
- taktik, taktiktyp, tactic, mechanic, Tactic_Type -> TAKTIK_TYP; multibuy, 3 for 2, 3 för 2 -> Multiköp 3 för 2
- artikel, article, SKU, item -> ARTIKEL / ARTIKEL_NAMN; nyckel, key -> NYCKEL
- såld prognos, sold forecast, CatBoost, the model forecast -> SALD_PROGNOS_CATBOOST
- köpt prognos, kedjans prognos, purchase forecast, the chain plan, the plan -> KOPT_PROGNOS_KEDJAN
- faktisk såld, actual sold, actuals, sell-through -> FAKTISK_SALD
- prognosfel, forecast error, forecast accuracy, bias, miss -> PROGNOSFEL_*_PCT / BIAS_*_PCT
- överprognos, over-forecast, over-bought, excess -> OVERPROGNOS_KVANTITET
- färskvara, perishable, fresh -> FARSKVARA; svinn, waste -> SVINNKOSTNAD_SEK / SVINNANDEL_PCT
- kolli, case; lav, layer; pall, pallet -> KOLLI / LAV / PALL
- orderjustering, order adjustment, cut the order, draft for the planner -> V_KAMPANJ_KOMMANDE (skill orderjustering-utkast)
- prognosavvikelse, variance explanation, why is forecast error high -> skill prognosavvikelse
- illustrative cost, indicative cost, finance not migrated -> KALLA

---

## 7. DOMAIN KNOWLEDGE

- The demo as-of date is 2026-09-30; the latest complete month is September 2026 and the latest complete week starts 2026-09-21.
- Grosshallen is the underperforming banner: R12 LFL about -1.4 percent versus Kronmat +2.0, Torghallen +4.8, group +1.3; transactions -5.6 percent, basket +4.4 percent.
- Grosshallen gross margin about 24.5 percent versus Kronmat 26.8 and Torghallen 30.5; EBIT about -SEK 35 m per quarter in 2025, break-even in Q2 2026, about +SEK 9 m in Q3 2026.
- Grosshallen Västerhamn (Göteborg): R12 sales about SEK 161 m = 62 percent of a SEK 259 m potential; cluster median 92 percent; gap about SEK 99 m, the largest in the banner; sales -7.5 percent with transactions -11 percent.
- Västerhamn Dairy and Bread availability about 89 percent (worst in the banner); overall OSA 91 percent versus 97 for the cluster; markdown rate 2.0 percent versus 1.3.
- 25 comparable stores have Dairy/Bread OSA below 94 percent; their LFL averages about 3.4 points below the rest.
- Billigmat discount store opened 1.1 km from Västerhamn on 2026-03-12; Västerhamn sales in the following six months were about 9.5 percent below the prior year.
- Families visits: Grosshallen -17 percent R12 (Västerhamn -23 percent); Kronmat and Torghallen Families move with total visits.
- Grosshallen Nordstaden (Uppsala, same cluster): 97 percent of potential, LFL +3.5 percent, private-label share 21 percent versus 14, OSA 98 percent, markdown rate 40 percent lower.
- Kronmat Fresh & Produce: sales +12 percent R12 with gross margin -2 points; Sommarpris 2026 (30 percent price cut, 2026-06-15..2026-08-09, retailer funded) is rank 1 on uplift (52 percent) and rank 1 on margin dilution (7.5 points).
- Three late import suppliers in the Teradata purchasing platform: Sterling Trading (key 39), Frontier Trading (26), Lakeshore Industries (52). Their SKUs drive about 68 percent of Grosshallen non-food lost sales (SEK 22 m of 32 m R12) from 29 percent of sales; at Västerhamn their availability is about 83 percent.
- Grosshallen Sundsvik (Helsingborg) closed 2026-08-15 and reopened as Kronmat Sundsvik on 2026-09-05.
- The Kampanjrapport (campaign performance and forecast accuracy by chain and week) used to be a MicroStrategy report and now reads V_KAMPANJRAPPORT; the same chain and week must always return the same grid and totals.
- Forecast error percent = (forecast - actual sold) / actual sold with positive = over-forecast; CatBoost is the group demand model, Köpt prognos is the chain's own purchase plan; totals are ratios of sums.
- Completed campaign weeks run 2024-W42 to 2026-W39; weeks 2026-W41 to 2026-W44 are planned campaigns with forecasts only (V_KAMPANJ_KOMMANDE).
- Kronmat week 2026-W36 (Höstskörd, four campaigns, 28 article rows): chain plan +18 percent over actual, CatBoost +6 percent.
- Multiköp 3 för 2 on perishables is the worst tactic: about +31 percent chain-plan bias over the last 13 completed weeks versus at most +9 percent on other tactics; perishables carry about 87 percent of the absolute error.
- Grosshallen Västerhamn is the worst Grosshallen store on campaign forecast deviation (about +37 percent R12, about +53 percent after the Billigmat opening); Grosshallen Nordstaden is in the best quartile.
- Over-forecasting cost about SEK 10.8 million of margin in Q3 2026 on the illustrative cost data, about 79 percent perishable waste, Kronmat Multiköp the largest share (about 32 percent); every cost figure carries the KALLA label.
- Four upcoming perishable campaigns are flagged (chain forecast more than 15 percent above CatBoost): Mejerivecka 3 för 2 (Kronmat W41), Äpplen & Päron (Torghallen W42), Brödfest 3 för 2 (Grosshallen W43), Köttvecka 3 för 2 (Kronmat W44).
- The Äpplen & Päron draft (Torghallen W42, delivery 2026-10-12, planner Viktor Holmgren, 20 fruit articles) cuts about 45 thousand units (17 percent) in whole layers and protects about SEK 640 thousand of margin (illustrative); a draft is never an order and the planner approves it.

---

## 8. BUSINESS NUANCES

- Like-for-like excludes stores opened after 2024-10-01 and the converted Sundsvik store; total growth includes them and is higher for Kronmat because of eight new stores.
- Compute margins, rates and LFL as ratios of sums across the chosen slice; never average store-level percentages.
- Compare a store with the median of its PEER_CLUSTER (banner x catchment type), not with the chain; hypermarkets and neighbourhood stores are not comparable.
- OSA is sales-weighted; the target is 0.96 and the alert threshold 0.94. Fresh categories (Dairy, Bread & Bakery) carry the availability story.
- Promotional margin dilution is baseline GP percent minus promo GP percent; supplier-funded campaigns dilute less. A campaign is "strong sales weak margin" at uplift >= 25 percent and dilution >= 4 points.
- EBIT is store-level operating result; central costs are not in the data. Quarterly EBIT = sum of the three months in QUARTER_LABEL.
- Catchment potential is refreshed once a year by the market-data provider; the potential index uses R12 sales for comparable stores only.
- Net sales exclude VAT; the April 2026 VAT cut lowered consumer prices but not reported net sales, while deflation lowered shelf prices by about 2 percent.
- The non-food range and purchase orders exist only for Grosshallen; the three late suppliers are a Teradata fact (days_late, po_status), the lost sales are a Snowflake fact.

---

## 9. TRIBAL KNOWLEDGE

- Regional managers log competitor events by hand; distances are straight-line and impact estimates are their judgement.
- "The gap" in store reviews always means the potential gap in SEK from V_CATCHMENT_POTENTIAL, ranked within the banner.
- Store Operations reviews Dairy and Bread availability weekly because they drive the weekly top-up trip; a store below 94 percent in both for four weeks is escalated.
- Loyalty "home store" is the store a member visits most; Families are weekly big-basket shoppers and the first to switch when a discounter opens nearby.
- Grosshallen's structural measures in 2026 were labour scheduling, logistics consolidation into the group network and the Sundsvik conversion; they fixed cost, not customer traffic.
- The import-purchasing platform came with the Grosshallen acquisition and still runs on Teradata; the group has not migrated it, so supplier performance is queried there.

---

## 10. QUERY ROUTING HINTS

- KPI summary questions (sales, margin, transactions, basket, growth by banner/region/month) -> V_BANNER_KPI_MONTHLY or V_KPI_STORE_MONTHLY.
- "Which stores are declining and is it transactions or basket" -> V_STORE_GAP_DECOMPOSITION (GROWTH_DRIVER).
- "Compared with similar stores" -> V_PEER_COMPARISON (CLUSTER_* and *_GAP_* columns).
- "Underperforming versus neighbourhood / local potential" -> V_CATCHMENT_POTENTIAL (POTENTIAL_INDEX, POTENTIAL_GAP_SEK, GAP_RANK_IN_BANNER).
- "Promotions with strong sales but weak margin" -> V_PROMO_EFFECTIVENESS (PROMO_VERDICT, ranks).
- "Availability issues lining up with weak sales" -> V_AVAILABILITY_VS_SALES filtered to Dairy and Bread & Bakery.
- "Segments visiting less" -> V_LOYALTY_SEGMENT_TRENDS. Competition -> COMPETITOR_EVENTS joined to STORES.
- Non-food stockouts and suppliers -> V_NONFOOD_AVAILABILITY_BY_SUPPLIER (Snowflake) plus wisdomai.RTL_DIM_SUPPLIER and
  wisdomai.RTL_FACT_PURCHASE_ORDER_LINE (Teradata, dialect teradata, TOP n) combined on SUPPLIER_KEY in the analysis step.
- Quarterly EBIT and the turnaround -> V_BANNER_KPI_MONTHLY grouped by QUARTER_LABEL.
- "Kampanjrapport", campaign vs forecast for a chain and week -> V_KAMPANJRAPPORT filtered by KEDJA and VECKA_LABEL (skill kampanjrapport; /kampanjrapport <kedja> <vecka>).
- "Why is forecast error high / which tactic / which store missed" -> V_PROGNOSFEL_TAKTIK then V_KAMPANJRAPPORT then V_KAMPANJ_BUTIK_AVVIKELSE (skill prognosavvikelse).
- "What did over-forecasting cost" -> V_KAMPANJ_MARGINALEFFEKT by QUARTER_LABEL, always with KALLA (illustrative).
- "Upcoming campaigns at risk / draft the order adjustment" -> V_KAMPANJ_KOMMANDE (FLAGGA, FORESLAGEN_MINSKNING_KOLLI, SKYDDAD_MARGINAL_SEK; skill orderjustering-utkast).
