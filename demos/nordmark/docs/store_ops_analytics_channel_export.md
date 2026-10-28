# Channel export: #store-ops-analytics

Letterhead: Nordmark Dagligvaror AB — internal chat export (Slack), channel #store-ops-analytics
Export range: 2026-08-18 to 2026-09-29
Exported by: Amir Rashidi for the analytics domain knowledge base
Members: Store Operations, FP&A, banner controllers, Loyalty and CRM, Supply Chain, Data Platform

## 2026-08-18

**Cecilia Marklund (FP&A)** 08:41
Reminder for the Q3 pack: LFL is comparable stores only. Sundsvik left the Grosshallen comparable set on 2026-08-15 when it closed for conversion. Kronmat Sundsvik opens 2026-09-05 and is a new store, not comparable until autumn 2027.

**Amir Rashidi** 08:52
Done in the mart: STORES.IS_LFL_COMPARABLE is FALSE for ST-0003 (Grosshallen Sundsvik) and the new Kronmat store. V_BANNER_KPI_MONTHLY picks it up automatically.

**Jonas Petersson (Kronmat controller)** 09:10
Can someone confirm that total Kronmat growth of 6 to 7 percent in Q3 is mostly new stores? Our LFL feels closer to 2.

**Cecilia Marklund** 09:14
Correct. Eight new Kronmat stores since January 2025. Use LFL_GROWTH_PCT, not SALES_GROWTH_PCT, in anything you send to the banner director.

## 2026-08-25

**Maria Holm (Grosshallen)** 13:02
Q2 was our first near break-even quarter (about -8 MSEK). The structural measures are in: labour scheduling, logistics moved into the group network, Sundsvik conversion. Q3 should be positive. But LFL is still negative and I want to understand why before the board asks.

**Amir Rashidi** 13:20
V_STORE_GAP_DECOMPOSITION says it clearly: Grosshallen is losing transactions (about -5.6 percent R12) while basket is up (about +4.4 percent). We are losing trips, not spend per trip. Biggest single store effect is Västerhamn.

**Maria Holm** 13:24
Västerhamn again. How bad?

**Amir Rashidi** 13:31
R12 sales about 161 MSEK against a catchment potential of 259 MSEK. Potential index 0.62. The cluster median for Grosshallen / Suburban family is 0.92. Gap about 99 MSEK, rank 1 in the banner by a distance. Transactions down 11 percent.

## 2026-09-02

**Per Hedlund (Supply Chain)** 10:05
Availability escalation list for week 35: 25 comparable stores below 94 percent OSA in Dairy and Bread & Bakery over 13 weeks. Västerhamn is the worst in the group at about 89 percent. The pattern holds across banners: the low-availability stores run about 3 points weaker LFL than the rest.

**Erik Sandström (Torghallen)** 10:12
Three of ours on that list. Mostly Stockholm urban stores with small backrooms. Working on a second bread delivery.

**Linnea Forsberg (Loyalty)** 10:40
Related: Families visits at Grosshallen are down about 17 percent R12 while Kronmat and Torghallen families move in line with total visits. At Västerhamn specifically Families visits are down about 23 percent and the drop starts in March. That is when Billigmat opened 1.1 km away (CEV-001, 2026-03-12).

**Maria Holm** 10:48
So the weekly family shop moved to the discounter and we are not giving them a reason to come back. Dairy and bread out of stock does not help.

## 2026-09-10

**Tobias Wennerström (Grosshallen non-food)** 15:15
Non-food availability is also a problem at Västerhamn. Lost sales on the imported range are concentrated in SKUs from three suppliers. I pulled the PO data from the purchasing platform (Teradata, wisdomai.RTL_FACT_PURCHASE_ORDER_LINE): Sterling Trading, Frontier Trading and Lakeshore Industries have the highest average days late and the most short-received lines. Their SKUs are about 29 percent of non-food sales but about 68 percent of lost sales.

**Amir Rashidi** 15:22
For anyone repeating this: the Snowflake side is V_NONFOOD_AVAILABILITY_BY_SUPPLIER (lost sales by SUPPLIER_KEY), the Teradata side is RTL_DIM_SUPPLIER plus RTL_FACT_PURCHASE_ORDER_LINE on the Ali-TD connection. Same supplier keys in both. Run the two queries and join the results; the platform does not join across the two systems in one SQL statement.

**Tobias Wennerström** 15:30
Supplier keys for reference: 39 Sterling Trading (Germany), 26 Frontier Trading (Vietnam), 52 Lakeshore Industries (Mexico).

## 2026-09-17

**Anna Bergström (Fresh & Produce, Kronmat)** 09:02
Sommarpris post-mortem is out. Headline: best uplift of any campaign this year (about 52 percent) and the worst margin dilution (about 7.5 points). Fresh & Produce grew 12 percent R12 but margin fell 2 points. We will not run it retailer-funded at 30 percent again.

**Jonas Petersson** 09:15
V_PROMO_EFFECTIVENESS verdict: Strong sales weak margin. 14 campaigns in that band, Sommarpris is the extreme.

## 2026-09-23

**Maria Holm** 11:05
Peer comparison for the Västerhamn review: Nordstaden (Uppsala) is in the same cluster with a similar catchment and runs at 0.97 of potential, LFL +3.5. Private-label share 21 percent versus 14 at Västerhamn, OSA 98 percent versus 91, markdown rate 40 percent lower. That is the playbook.

**Cecilia Marklund** 11:20
Proposal for the 12-week test at Västerhamn: availability first (Dairy and Bread to 96 percent, second bread delivery, revised Relex parameters), relist the private-label core range, replace blanket markdowns with targeted Families offers through Grosshallen Kort. Measure weekly: transactions versus Nordstaden and the cluster, OSA, PL share, markdown rate, Families visits. Half the gap to the cluster median is roughly 40 MSEK of annual sales.

**Amir Rashidi** 11:26
I will put the test metrics in the weekly store review view. Playbook document is in the knowledge base as "Store review playbook".

## 2026-09-29

**Amir Rashidi** 16:40
Mart is frozen as of 2026-09-30 for the Q3 review. Latest complete month September 2026, last complete week starts 2026-09-21. Questions in here or ask the analytics assistant on the Nordmark domain.
