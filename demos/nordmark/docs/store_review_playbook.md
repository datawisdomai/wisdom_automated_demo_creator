# Store Review Playbook — From KPI to Action

Letterhead: Nordmark Dagligvaror AB — Store Operations
Document: Store Review Playbook, edition 2026-09
Owner: Head of Store Operations
Contributors: FP&A, Store Analytics, Loyalty and CRM, Supply Chain, Grosshallen
Classification: Internal

## 1. Purpose

A common way to go from a KPI summary to a specific action and a test. Every store review follows the six steps below. The analytics domain holds the data; the views named here are the certified ones.

## 2. The six steps

### Step 1. KPI summary

Start with the banner and the period: net sales, like-for-like growth, gross margin percent, transactions, average basket, on-shelf availability, waste and markdown rates, active loyalty members and visit frequency (V_BANNER_KPI_MONTHLY, V_KPI_STORE_MONTHLY, V_PEER_COMPARISON). Filter by banner, region, category and period.

### Step 2. Pick the store

Rank stores by the potential gap in SEK within the banner (V_CATCHMENT_POTENTIAL.GAP_RANK_IN_BANNER) and by like-for-like growth. The review store is the one with the largest gap that is not already in a test.

### Step 3. Break down the gap

Use V_STORE_GAP_DECOMPOSITION: is the change in sales a transactions effect or a basket effect? A transactions problem is a traffic problem (availability, competition, price perception, loyalty). A basket problem is a range or merchandising problem.

### Step 4. Compare with peers and the catchment

Use V_PEER_COMPARISON (the store against its peer cluster median) and V_CATCHMENT_POTENTIAL (the store against its local potential, with demographics and competition). Never compare a hypermarket with a neighbourhood store.

### Step 5. Investigate causes

Check, in this order:

1. Availability: V_AVAILABILITY_VS_SALES for Dairy and Bread & Bakery; below 94 percent is a traffic problem in itself.
2. Competition: COMPETITOR_EVENTS within 2 km and the store's monthly sales before and after the event date.
3. Customer segments: V_LOYALTY_SEGMENT_TRENDS; Families are the weekly big-basket shoppers and leave first.
4. Assortment and private label: STORE_ASSORTMENT_MONTHLY against the peer.
5. Promotions and markdowns: V_PROMO_EFFECTIVENESS and the markdown rate against the cluster.
6. For Grosshallen non-food: V_NONFOOD_AVAILABILITY_BY_SUPPLIER and the purchase-order lateness of the suppliers in the import-purchasing platform (Teradata).

### Step 6. Recommend an action and a test

Pick the peer store in the same cluster with the best potential index and copy what it does differently. Write the test as: actions, start week, 12-week duration, weekly measures, control group (the peer cluster), success threshold, estimated upside and cost.

## 3. Worked example: Grosshallen Västerhamn (September 2026)

- KPI summary: Grosshallen LFL about -1.4 percent, transactions -5.6 percent, basket +4.4 percent, margin 24.5 percent, EBIT just turned positive.
- Store: Västerhamn, potential index 0.62 against a cluster median of 0.92, gap about SEK 99 million, rank 1 in the banner.
- Gap: transactions effect about SEK -20 million, basket effect about SEK +7 million. Growth driver: transactions.
- Peers: Nordstaden (same cluster) at 0.97 of potential; availability 98 percent against 91; private-label share 21 against 14 percent; markdown rate 40 percent lower.
- Causes: Dairy and Bread availability about 89 percent (worst in banner); Billigmat opened 1.1 km away on 2026-03-12 with sales about 9.5 percent down in the six months after; Families visits -23 percent; non-food lost sales concentrated in three late import suppliers (Sterling Trading, Frontier Trading, Lakeshore Industries).
- Action and test: the Nordstaden playbook for 12 weeks from 2026-10-12 — availability to 96 percent with a second bread delivery and revised order parameters, relist the private-label core range above 20 percent share, targeted Families offers instead of blanket markdowns, safety stock for the late suppliers' core SKUs. Weekly measures: transactions, Families visits, OSA, private-label share, markdown rate, margin. Success: transactions within 5 percent of prior year by week 12. Upside: about SEK 40 million of annual sales for half the gap; cost about SEK 1.5 million.

## 4. Measuring whether it worked

- Compare the test store with its peer cluster, not with its own past alone; use the weekly views and the same windows.
- Report transactions and availability weekly, margin and private-label share monthly.
- Stop rules: if availability is not above 95 percent by week 4 the test is paused and fixed before anything else is judged.
- Scale rule: if transactions recover within 5 percent of prior year by week 12, roll the playbook to the next four stores on the gap ranking.
