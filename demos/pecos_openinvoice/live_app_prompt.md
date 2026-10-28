# Live App prompt — Pecos Ridge Supply Chain Spend Cube

Paste into Wisdom on the O&G (Pecos Ridge) domain. One prompt builds the whole app; the Supply Chain
Category Manager sees it in the side panel during the demo. Read-only: the app never writes to Snowflake
or OpenInvoice. Demo as-of 2026-09-30.

```
Create a live app called "Pecos Ridge Supply Chain Spend Cube" for Pecos Ridge Energy, a Permian, Anadarko and Hugoton oil and gas operator that receives supplier invoices through Enverus OpenInvoice. It is the working cockpit for the Supply Chain Category Manager, not a reporting dashboard. Every page answers "what are we really paying for each generic product, from whom, against what contract, and what is still unclassified". Use five connected pages.

DATA RULES
Use V_INVOICE_LINE_CLASSIFIED as the primary source for spend: one row per OpenInvoice line with SUPPLIER_NAME, LEVEL1_FAMILY, GENERIC_PRODUCT_NAME (the value 'Unclassified' when no approved classification exists), IS_CLASSIFIED, LINE_AMOUNT_USD, STD_QUANTITY, INVOICE_YEAR, INVOICE_MONTH, INVOICED_UOM and BASIN. Use V_SUPPLIER_ALTERNATIVES for supplier price comparison, V_GENERIC_PRODUCT_PRICE_MONTHLY for price trends, V_PRICEBOOK_VARIANCE for contract rate checks, V_UNCLASSIFIED_SPEND for the steward queue and V_AFE_PRODUCT_COST for cost per well. Use SCM_PRODUCT_TAXONOMY for the list of generic products and families. Aggregate each source before combining; never join fact views as raw rows.
Anchor "today" to 2026-09-30. Data runs from 2022-01-01 to 2026-09-30; September 2026 is the latest complete month and 2026 is a nine-month year, label it YTD wherever it sits beside full years. Exclude lines whose INVOICE_STATUS is Rejected. A standard unit price is always SUM(LINE_AMOUNT_USD) / SUM(STD_QUANTITY) in the product's STANDARD_UOM; never average STD_UNIT_PRICE_USD or AVG_STD_UNIT_PRICE_USD across rows. Exclude LEVEL1_FAMILY 'Fees & surcharges' from every price comparison but keep it in total spend. Only Approved classifications count as classified; the views already apply this. This app only reads data; it never writes to Snowflake or OpenInvoice.

PAGE 1: CATEGORY OVERVIEW
KPI tiles for 2026 YTD: total invoiced spend, classified share of spend (SUM of LINE_AMOUNT_USD where IS_CLASSIFIED = 1 over total), unclassified spend in USD, spend invoiced above contract rate (SUM of PRICE_VARIANCE_USD where IS_OVER_CONTRACT = 1 in V_PRICEBOOK_VARIANCE) and the total SAVINGS_AT_BEST_PRICE_USD for 2025 from V_SUPPLIER_ALTERNATIVES, each with the change versus the same period of 2025.
One chart that is the point of the page: spend by INVOICE_YEAR stacked by LEVEL1_FAMILY with Unclassified as its own segment, 2022 to 2026 YTD.
A treemap or bar breakdown of 2026 YTD spend by LEVEL1_FAMILY then GENERIC_PRODUCT_NAME, and a table by generic product: spend, STD_QUANTITY, standard unit price, number of suppliers and the price dispersion percent from V_SUPPLIER_ALTERNATIVES. Clicking a generic product carries it to the Price Dispersion page. Preselect 'Corrosion inhibitor, water-soluble, filming amine'.

PAGE 2: PRICE DISPERSION
A generic product picker (default 'Corrosion inhibitor, water-soluble, filming amine') and a year picker (default 2025). From V_SUPPLIER_ALTERNATIVES for that product and INVOICE_YEAR show a table by SUPPLIER_NAME: STD_QUANTITY, SPEND_USD, AVG_STD_UNIT_PRICE_USD, VOLUME_SHARE, BEST_STD_UNIT_PRICE_USD and SAVINGS_AT_BEST_PRICE_USD, with a headline line "N suppliers, dispersion X percent, savings at best price $Y".
A bar chart of standard unit price by supplier with the best price as a reference line, and a second table from V_INVOICE_LINE_CLASSIFIED by SUPPLIER_NAME and INVOICED_UOM (tote, drum, pail, bulk gallon) showing the standard unit price per pack so the small-pack premium is visible.
A line chart of AVG_STD_UNIT_PRICE_USD by INVOICE_MONTH per supplier from V_GENERIC_PRODUCT_PRICE_MONTHLY for the selected product, with BENCHMARK_PRICE_USD_PER_STD_UOM as a dashed reference.
One plain-language sentence naming the cheapest and most expensive supplier per standard unit and the gap in percent.

PAGE 3: PRICEBOOK VARIANCE & DISPUTES
From V_PRICEBOOK_VARIANCE, lines with IS_OVER_CONTRACT = 1. Filters: SUPPLIER_NAME, INVOICE_YEAR (default 2026), LINE_STATUS. Preselect Redline Sand LLC so the demo starts on the RL100 story.
KPI tiles: over-contract line count, SUM(PRICE_VARIANCE_USD), the disputed amount (SUM of PRICE_VARIANCE_USD where LINE_STATUS is Disputed or Short-paid) and the share of over-contract variance that is disputed.
A chart of SUM(PRICE_VARIANCE_USD) by INVOICE_MONTH stacked by SUPPLIER_NAME, and a table by SUPPLIER_NAME and INVOICE_MONTH: over-contract lines, invoiced amount, variance USD, average PRICE_VARIANCE_PCT, disputed amount and the PRICEBOOK_VERSION in force.
A drill-down table of the lines for the selected supplier: SUPPLIER_INVOICE_NUMBER, SERVICE_DATE, SUPPLIER_ITEM_CODE, SUPPLIER_ITEM_DESCRIPTION, QUANTITY, UNIT_PRICE_USD, PRICEBOOK_RATE_USD, PRICE_VARIANCE_USD, LINE_STATUS, DISPUTE_REASON and PRICEBOOK_SOURCE_DOCUMENT (the Exhibit B file the rate came from).

PAGE 4: CLASSIFICATION QUEUE
From V_UNCLASSIFIED_SPEND. KPI tiles for 2026 YTD: unclassified spend, its share of total spend from V_INVOICE_LINE_CLASSIFIED, number of distinct supplier and description pairs, and the share of unclassified spend whose OI_SUPPLIER_CATEGORY is Rental Equipment.
A table grouped by SUPPLIER_NAME and SUPPLIER_ITEM_DESCRIPTION: line count, SUM(LINE_AMOUNT_USD), INVOICED_UOM, OI_SUPPLIER_CATEGORY, OI_COST_CODE, REVIEW_STATUS (Unclassified or Needs review) and the last INVOICE_DATE, sorted by amount descending. Filters: supplier, REVIEW_STATUS, OI_SUPPLIER_CATEGORY, INVOICE_YEAR and a free-text search on the description.
Selecting a row opens a review panel: the description and recent lines, a proposed generic product chosen from SCM_PRODUCT_TAXONOMY.GENERIC_PRODUCT_NAME, a conversion factor to the standard UOM, a note and a Save button. Saved proposals persist within the app session, show as a badge on the row and are listed as a JSON array on the page with a Copy button. State plainly that the proposals are what the data steward would load into SCM_ITEM_CLASSIFICATION and that this app writes nothing.

PAGE 5: COST PER LATERAL FOOT
Use V_AFE_PRODUCT_COST filtered to USE_PHASE = 'Completion' and FIRST_INVOICE_DATE on or after 2025-01-01, joined on CORP_WELL_ID to OI_REF_WELL (OpenInvoice's synced copy of the well master, in the same database) for WELL_NAME, BASIN and LATERAL_LENGTH_FT; keep only wells with LATERAL_LENGTH_FT greater than zero. Aggregate spend to the well before joining so lateral length is counted once per well; cost per lateral foot is SUM(SPEND_USD) / SUM(LATERAL_LENGTH_FT) across the wells in the group, never the average of per-well ratios and never lateral length multiplied by the number of product rows.
KPI tiles: wells with completion-phase invoice lines, total completion spend, total lateral feet and the blended cost per lateral foot.
A table by BASIN and GENERIC_PRODUCT_NAME: wells, spend, STD_QUANTITY, standard unit price and cost per lateral foot, with a grouped bar chart of cost per lateral foot by basin for the top eight generic products.
A table by well: WELL_NAME, BASIN, PAD_ID, AFE_NUMBER, LATERAL_LENGTH_FT, completion spend, cost per lateral foot and the proppant share.
An editable assumptions panel, clearly labelled as assumptions, with a proppant price change (default +10 percent) applied to the Proppant family: show the resulting cost per lateral foot by basin, the delta per foot and the delta on total 2026 YTD completion spend beside the baseline. No forecast beyond that arithmetic.

DESIGN
Calm, operational, few KPI tiles, tabular numerals for money, unit prices with two decimals and the standard UOM in the column header (USD per GAL, USD per TON, USD per FT). Top stepper Category Overview -> Price Dispersion -> Pricebook Variance & Disputes -> Classification Queue -> Cost per Lateral Foot. Preserve the selected generic product, supplier and year across pages. Label 2026 as YTD everywhere it appears. Everything shown is invoiced data to 2026-09-30; this app only reads.
```
