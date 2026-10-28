# Build notes from Slack (Ali Alladin, Oct 2026) — Axfood via Teradata

Axfoods is the group behind Willys, Hemköp, City Gross, and several smaller store chains. One of their recent
acquisitions (City Gross) is not doing so well.

Structure the POC in 3 levels: key KPIs → medium complexity → deeper analysis. Show the basics first, then how
someone can keep digging using WisdomAI.

## 1. Key KPIs
- sales and sales growth (like-for-like / YoY)
- gross profit and margin %
- transaction count and average basket value
- sales by store, banner and category
- availability / stockouts
- waste and markdowns
- active customers and visit frequency, if we have loyalty data
Filterable by store, region, category and time period.

## 2. Medium complexity — what's driving performance?
- which stores are growing or declining, and is it transactions, basket size or both?
- which categories/products explain most of the change?
- how does a store compare with similar stores, rather than the whole chain?
- where are sales growing but margins getting worse?
- which promotions have strong sales but weak margins?
- where do availability issues line up with weak sales?
- which customer segments are visiting less or spending less, where we have the data?

## 3. High complexity — where's the opportunity and what should we do?
- which stores are underperforming relative to their neighborhood and local potential?
- what store formats / assortments perform well in different neighborhood types?
- why does one store outperform another with a similar catchment?
- is the gap related to assortment, availability, pricing, promotions, customer retention or competition?
- what can we learn from successful peer stores and test in the weaker ones?
- which actions have the biggest estimated sales/profit upside, and how should we measure whether they work?

Demo flow: start with a KPI summary → pick an underperforming store → break down the gap → compare peers and
neighborhoods → investigate possible causes → recommend a specific action and a test.

Build: start with one banner and 12–24 months of data. Core tables are POS, store/product masters, costs,
inventory, assortment and promotions. Loyalty + neighborhood data unlock the deeper customer/local-market questions.
Run the plan by Talal before building.

## Follow-up (after the Teradata connectivity test)
"altho the dataset is very skimpy. I would use Snowflake and Databricks to create some synthetic data and build
majority of the liveapp from there but make a connection to TD to show the account team federation. we only have
read access and can only connect via jdbc, no direct access to TD as of yet."

## Axfood Q3 2026 context (reported 2026-10-22)
Group net sales +2%, retail +2.8% volume-led; food prices ~-2% YoY (deflation), food VAT cut 12%→6% on 1 Apr 2026;
group margin 4.9%. Willys +2%, LFL modest, margin 4.7%, slightly behind market; ~4.0M Willys Plus members; ~70 stores
on the 5.0 concept by year-end. Hemköp +7%, LFL very strong, margin 5.8%, gaining share; ~2.2M loyalty members.
City Gross: LFL positive and improving, profitable in Q3, rolling-12-month break-even, driven by "structural measures";
5th store closed (Helsingborg → converted to Willys); ~38 stores. Snabbgross flat, margin 5.1%. Private label share
stable at group level. Long-term group margin target 4.5%.
