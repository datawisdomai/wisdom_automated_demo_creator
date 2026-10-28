# Business Glossary and Data Ownership

Letterhead: Nordmark Dagligvaror AB — Data Governance Office
Document: Business Glossary, Store Analytics Domain, edition 2026-09
Owner: Data Governance Lead (Helena Strand)
Stewards: Amir Rashidi (Store Analytics), Linnea Forsberg (Loyalty and CRM), Per Hedlund (Supply Chain), Maria Holm (Grosshallen)
Classification: Internal

## 1. Organisation

| Term | Meaning | Owner |
|---|---|---|
| Nordmark Dagligvaror | The group. Three banners, about 250 stores, SEK 20 bn annual net sales. | Group CEO |
| Banner | A store chain with its own name, format and positioning: Kronmat, Torghallen, Grosshallen. Synonyms: chain, format, fascia. | Banner directors |
| Kronmat | Discount banner, about 120 large supermarkets, "Sweden's cheapest basket", price index 0.915 versus market, loyalty program Kronmat Plus. Director Johanna Lindqvist. | Kronmat |
| Torghallen | Neighbourhood banner, about 90 smaller stores (one third franchise), fresh food and ready meals, Torghallen Klubb. Director Erik Sandström. | Torghallen |
| Grosshallen | Hypermarket banner, 38 out-of-town stores acquired 2025-01-01, grocery plus imported non-food, Grosshallen Kort. Director Maria Holm. Synonyms: the acquired banner, the hypermarkets. | Grosshallen |
| Region | Sales region: Stockholm, Vast (west, Göteborg), Syd (south, Malmö and Helsingborg), Ost (east, Linköping), Mitt (Uppsala, Västerås, Örebro), Norr (Umeå, Luleå). | Store Operations |
| Franchise store | A Torghallen store owned by a merchant under a franchise agreement; included in all KPIs. | Torghallen |
| Store conversion | Re-opening a store under another banner. Grosshallen Sundsvik (Helsingborg) closed 2026-08-15 and reopened as Kronmat Sundsvik 2026-09-05. | Store Development |

## 2. Customers and catchments

| Term | Meaning | Owner |
|---|---|---|
| Catchment | The local market of a store, measured within 2 km: residents, households, income, age mix, car access, competitors. Synonyms: trade area, neighbourhood, upptagningsområde. Source: market-data provider, refreshed yearly. | Store Development |
| Catchment type | Urban core, Suburban family, Small town, Commuter belt, Rural hub. | Store Development |
| Peer cluster | Banner combined with catchment type, e.g. Grosshallen / Suburban family. The benchmark group of a store. Synonyms: peers, similar stores. | Store Analytics |
| Catchment potential | Expected annual net sales of a store in its catchment (spend times fair share). | Store Development |
| Potential index, potential gap | R12 sales divided by potential; potential minus sales in SEK. "The gap" in store reviews. | Store Analytics |
| Loyalty segment | Families, Seniors, Students, Urban singles, Value seekers, Premium. Assigned monthly by the CRM. | Loyalty and CRM |
| Home store | The store a member visits most in the month. | Loyalty and CRM |
| Competitor event | An opening, closure, price campaign or refurbishment by a competitor near a store, logged by the regional manager with distance and an impact estimate. | Store Operations |

## 3. Sales and margin

| Term | Meaning | Owner |
|---|---|---|
| Net sales | Sales excluding VAT after discounts and markdowns. Synonyms: revenue, turnover, omsättning. | FP&A |
| Like-for-like (LFL) | Growth of comparable stores only. Synonyms: comparable, same-store, jämförbara butiker. | FP&A |
| Transactions | Customer receipts. Synonyms: baskets, visits (in the POS sense), kvitton. | Store Operations |
| Average basket | Net sales per transaction. Synonym: snittköp. | Store Operations |
| Gross margin | Gross profit over net sales. Synonym: bruttomarginal. | FP&A |
| EBIT | Store operating result: gross profit minus store operating costs. Synonym: rörelseresultat. | FP&A |
| Markdown | A price reduction on a short-dated or clearance item. Not a promotion. Synonym: nedsättning. | Category Management |
| Promotion | A planned campaign with a mechanic (Price cut, Multibuy, Loyalty price, Bundle, Clearance), dates and funding. Synonyms: campaign, offer, kampanj. | Category Management |
| Private label | Own-brand products. Synonyms: own brand, EMV, egna märkesvaror. | Category Management |

## 4. Supply and availability

| Term | Meaning | Owner |
|---|---|---|
| On-shelf availability (OSA) | Share of audited SKU-hours in stock on the shelf. Target 96 percent, alert 94 percent. Synonyms: availability, in-stock, tillgänglighet. | Supply Chain |
| Stockout | An item not available on the shelf. Stockout hours are summed per category and week. | Supply Chain |
| Waste | Goods written off. Synonym: svinn, shrink. | Store Operations |
| Inventory days | Days of cover at week end. | Supply Chain |
| Imported non-food range | The 250 apparel, footwear, home, electronics, toys, sports and cosmetics SKUs sold in Grosshallen, bought through the import-purchasing platform. | Grosshallen Non-food |
| Import-purchasing platform | The supplier, SKU and purchase-order system Grosshallen brought into the group. Runs on Teradata (database wisdomai, tables RTL_DIM_SUPPLIER, RTL_DIM_PRODUCT, RTL_FACT_PURCHASE_ORDER_LINE, RTL_VW_PURCHASE_ORDER). Attached to the analytics domain as the federated connection Ali-TD. | Grosshallen Non-food |
| Lost sales | Estimated sales lost while a non-food SKU was out of stock. | Grosshallen Non-food |
| Days late | Days a purchase-order line was received after its expected date (Teradata RTL_FACT_PURCHASE_ORDER_LINE.days_late). Short-received means fewer units arrived than ordered. | Grosshallen Non-food |

## 4b. Campaign planning and forecasting

Owner: Head of Campaign Planning (Sofia Lindahl). Steward: Demand Planning Analytics (Karl Öberg). Chain planners: Oskar Lindgren (Kronmat), Maja Sjöberg (Torghallen), Viktor Holmgren (Grosshallen), with Elsa Nyström, Hugo Bergman and Linnea Åkerman.

| Term | Meaning | Owner |
|---|---|---|
| Kedja | Chain, the same thing as banner in the campaign mart: Kronmat, Torghallen, Grosshallen (KAMPANJ.KEDJA). | Campaign Planning |
| Kampanj | A campaign: a set of articles sold on one tactic for one or two weeks in one chain (KAMPANJ). Identified by KAMPANJ_ID, named like "Höstskörd 3 för 2". Linked to the category promotion in PROMOTIONS where one exists. | Campaign Planning |
| Taktiktyp | Tactic type, the promotion mechanic: Prisnedsättning (PN), Multiköp 3 för 2 (MK), Medlemspris (MP), Halva priset (HP), Kupong (KU). Synonyms: tactic, mechanic, Tactic_Type. | Campaign Planning |
| Vecka, campaign week | The ISO week of the first delivery day (LEVERANS_FRAN); key KALENDER_VECKA_ID (YYYYWW), label VECKA_LABEL. Synonyms: week, Calendar_Week_Id. | Demand Planning Analytics |
| Artikel | Article, the product or SKU in the article master (ARTIKEL). Synonyms: article, SKU, product, item. | Range Management |
| Nyckel | The row key of the Kampanjrapport: week label and article id. Synonym: key. | Demand Planning Analytics |
| Såld prognos | Sold forecast from the group's CatBoost demand model (SALD_PROGNOS_CATBOOST). Synonyms: CatBoost forecast, demand forecast, sold forecast. | Demand Planning Analytics |
| Köpt prognos, kedjans prognos | Purchase forecast from the chain's own plan (KOPT_PROGNOS_KEDJAN). Synonyms: chain forecast, purchase forecast, the plan. | Chain planners |
| Planerad kvantitet | The purchase plan rounded up to whole cases; what was ordered (PLANERAD_KVANTITET). Synonym: Quantity. | Chain planners |
| Faktisk såld | Actual units sold in the campaign week (FAKTISK_SALD). Synonyms: actual, actual sold, sold. | Store Analytics |
| Prognosfel | Forecast error: (forecast − actual sold) / actual sold, positive = over-forecast. Bias for a group is the ratio of sums. | Demand Planning Analytics |
| Överprognos | Over-forecast quantity: units bought but not sold (OVERPROGNOS_KVANTITET). | Demand Planning Analytics |
| Prognosgap | For an upcoming campaign: chain forecast / CatBoost − 1. Flag threshold 15 percent on perishables (V_KAMPANJ_KOMMANDE.FLAGGA). | Campaign Planning |
| Färskvara | Perishable article (ARTIKEL.FARSKVARA): fresh produce, dairy, bread, meat, fish, deli. Synonym: perishable, fresh. | Range Management |
| Kolli, Lav, Pall | Case (units per case), pallet layer (cases per layer), pallet (cases per pallet) in ARTIKEL. Orders and adjustments are in whole cases rounded to layers. | Supply Chain |
| Kvitto | Receipt, one customer transaction. | Store Operations |
| Orderjustering | An order adjustment before delivery: a draft in whole layers for the responsible planner to approve; never written automatically. | Chain planners |
| Marginaleffekt | Margin cost of over-forecasting: waste on perishables plus clearance markdown (V_KAMPANJ_MARGINALEFFEKT). Computed on ILLUSTRATIVE cost data because purchase cost and margin live in the finance system that has not been migrated; every figure carries KALLA = 'ILLUSTRATIV - finanssystem ej migrerat'. | Demand Planning Analytics with FP&A |

## 5. Systems of record

| System | Holds | Platform |
|---|---|---|
| POS (Extenda) | Daily store sales, transactions, loyalty identification | Snowflake NORDMARK_POC.ANALYTICS (STORE_DAILY_SALES, SALES_WEEKLY_STORE_CATEGORY) |
| Relex | Availability audits, waste, inventory cover | Snowflake (SALES_WEEKLY_STORE_CATEGORY, NONFOOD_AVAILABILITY_MONTHLY) |
| SAP | Store operating costs | Snowflake (STORE_MONTHLY_COSTS) |
| Loyalty CRM | Members, segments, visits, spend | Snowflake (LOYALTY_ACTIVITY_MONTHLY) |
| Market-data provider | Catchments and potential | Snowflake (NEIGHBORHOODS) |
| Import-purchasing platform | Suppliers, imported SKUs, purchase orders | Teradata wisdomai (federated, read-only) |
| Chain planning tool | Campaigns, tactic, delivery windows, the chain purchase forecast | Warehouse campaign mart (KAMPANJ, KAMPANJ_ARTIKEL_VECKA) |
| CatBoost forecast feed | Sold forecast per campaign week and article | Warehouse campaign mart (KAMPANJ_ARTIKEL_VECKA.SALD_PROGNOS_CATBOOST) |
| Finance system (not migrated) | Purchase cost, list price, margin | Illustrative extract ARTIKEL_KOSTNAD_MANAD, labelled KALLA |

## 6. Named entities worth knowing

- Grosshallen Västerhamn (Göteborg, store ST-0001): the store with the largest potential gap in the group; subject of the Q3 2026 turnaround memo.
- Grosshallen Nordstaden (Uppsala, ST-0002): the benchmark store in the same cluster; source of the store review playbook.
- Billigmat: a discount competitor that opened 1.1 km from Grosshallen Västerhamn on 2026-03-12.
- Sommarpris 2026: Kronmat's summer Fresh & Produce price-cut campaign (2026-06-15 to 2026-08-09).
- Sterling Trading, Frontier Trading, Lakeshore Industries: the three import suppliers with the latest purchase-order deliveries in 2026 (supplier keys 39, 26, 52).
- Höstskörd, Kronmat week 2026-W36: the reference week for the Kampanjrapport (four campaigns, 28 article rows; chain forecast +18.0 percent, CatBoost +6.0 percent).
- Äpplen & Päron, Torghallen week 2026-W42 (delivery 2026-10-12, planner Viktor Holmgren): the upcoming perishable campaign with a draft order adjustment of 17.25 percent, margin protected SEK 637,078 on illustrative cost data.
- Mejerivecka 3 för 2 (Kronmat W41), Brödfest 3 för 2 (Grosshallen W43), Köttvecka 3 för 2 (Kronmat W44): the other upcoming campaigns flagged on 2026-09-30.
