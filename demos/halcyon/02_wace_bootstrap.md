# Halcyon Specialty Distribution — Domain Bootstrap (wACE)

Domain: **Halcyon Specialty Distribution (HSD)**, a US specialty pharmaceutical distributor.
Warehouse: Snowflake `HALCYON_POC.SPECIALTY_OPS`.
Demo as-of date: **2026-09-25** (Friday). Latest complete ISO week: Mon 2026-09-14 to Sun 2026-09-20.
Data spans 2025-01-01 to 2026-09-25.

---

## 1. DOMAIN OVERVIEW

Halcyon buys specialty pharmaceuticals (oncology, immunology, GLP-1 metabolic, rare disease, hematology,
neurology, infectious disease, vaccines, ophthalmology) from 22 manufacturers and distributes them from six
distribution centers (DCs) to 120 customer organizations with 736 ship-to sites: health systems, academic
medical centers, oncology practices, infusion centers, specialty pharmacies and retail pharmacy chains.

The primary user is the **Director of Customer Supply Operations**, whose daily question is
*"which customers and products need intervention today, and what do we do about it."* Secondary users are
regional DC operations managers, the contracts and chargebacks team, and strategic account managers.

Core business mechanics represented:

- **Order fulfillment**: customers order by EDI, portal, phone or auto-replenishment; Halcyon ships same
  business day for next-day delivery from the serving DC. Lines ship complete, partial, or go on backorder.
- **Manufacturer allocation**: some products are supply-constrained. The manufacturer allocates a monthly
  quantity to Halcyon, which Halcyon splits across customers (usually by historical share). Requests above
  allocation become `ALLOCATION_LIMIT` backorders.
- **Cold chain**: most specialty product is refrigerated (2-8C), frozen (-20C) or ultra-cold (-70C).
  Temperature loggers record readings at DC storage, packout, in transit and delivery. Readings outside
  range are excursions and lead to release, quarantine, destruction or return.
- **Inventory and expiry**: weekly DC-by-NDC snapshots track on-hand, available, on-order, days of supply
  and units expiring within 30 and 90 days.
- **Contract pricing and chargebacks**: customers buy at GPO contract prices below WAC. Halcyon claims the
  difference (the chargeback) back from the manufacturer. Disputed or rejected claims are margin at risk.
- **Returns and service cases**: returns carry reason and disposition; service cases from CRM carry type,
  severity, SLA and exec-escalation flag.

Scale: ~$2.9B shipped revenue over the period, 45K orders, 162K order lines, 45K shipments,
130K cold chain readings, 3.7K backorders, 102K chargeback claims, 1.4K service cases.

---

## 2. TABLE CATALOG

### 2.1 `CALENDAR` (dimension, 730 rows)
One row per day 2025-01-01 to 2026-12-31. `WEEK_START_DATE` is the Monday of the ISO week.
`IS_COMPLETE_WEEK` is TRUE for weeks fully on or before 2026-09-20; use it to drop the partial current week
from trends. `IS_US_HOLIDAY` marks days DCs do not ship.

### 2.2 `DISTRIBUTION_CENTERS` (dimension, 6 rows)
`DC-MEM` Memphis (national specialty hub, ultra-cold capable), `DC-DAL` Dallas, `DC-ATL` Atlanta,
`DC-CHI` Chicago (ultra-cold capable), `DC-PHX` Phoenix, `DC-EWR` Newark. Each has a `REGION`
(SOUTH, CENTRAL, SOUTHEAST, MIDWEST, WEST, NORTHEAST) that matches `CUSTOMERS.REGION`.

### 2.3 `MANUFACTURERS` (dimension, 22 rows)
Fictional manufacturers. `RUNS_ALLOCATION_PROGRAM` flags those that cap supply. `CHARGEBACK_TERMS_DAYS`
is the contractual settlement window. Notable: **Veltrix Biopharma** (MFR-001, GLP-1, allocation program),
**Keldon Pharma** (MFR-002, oncology and immunology), **Amberline Oncology** (MFR-005).

### 2.4 `GPOS` (dimension, 8 rows)
Group purchasing organizations. Customers belong to at most one GPO; the GPO contract sets the price.

### 2.5 `PRODUCTS` (dimension, 180 rows)
NDC-level product master. Key columns: `THERAPEUTIC_CLASS`, `STORAGE_CLASS` (AMBIENT, REFRIGERATED_2_8C,
FROZEN_MINUS20, ULTRA_COLD_MINUS70), `IS_ALLOCATED`, `IS_LIMITED_DISTRIBUTION`, `BRAND_GENERIC`,
`WAC_UNIT_PRICE`, `SHELF_LIFE_DAYS`. Eight products are allocated, including **Vanterra**
(velmaglutide, GLP-1 pen, Veltrix, NDC 61234-0101-04, WAC $985 per carton of 4 pens).
**Oncaryl** (ambertuzumab, oncology infusion vial, Amberline, NDC 58771-0410-01, WAC $2,850) is the
short-dated inventory example.

### 2.6 `CUSTOMERS` (dimension, 120 rows)
Customer organizations. `CUSTOMER_TIER` is STRATEGIC (12), KEY (30), CORE (78) by contract value.
`CONTRACT_RENEWAL_DATE` and `ANNUAL_CONTRACT_VALUE` drive renewal questions. `PRIMARY_DC_ID` is the
serving DC. `ACCOUNT_MANAGER` is the Halcyon owner. Largest customer: **Bayview Regional Health**
(CUST-0001, Strategic, Florida health system, $48.2M ACV, renews 2026-12-15, served by DC-ATL,
account manager Dana Whitfield). Other named accounts: Northgate Health Alliance (CUST-0003, Strategic,
Ohio, renews 2026-11-30), Cascade Oncology Partners (CUST-0007, Key, Oregon, renews 2027-01-20).

### 2.7 `CUSTOMER_SITES` (dimension, 736 rows)
Ship-to sites. `SITE_TYPE`, `SERVING_DC_ID`, `ORDERING_CHANNEL` (EDI, PORTAL, PHONE, AUTO_REPLENISH),
`COLD_CHAIN_RECEIVING`. Health systems have 6 to 14 sites; retail chains 8 to 18; practices 1 to 4.

### 2.8 `CONTRACT_PRICES` (dimension, 978 rows)
GPO x NDC contract prices with `EFFECTIVE_DATE`, `EXPIRATION_DATE`, `PRICE_FILE_VERSION`.
Keldon Pharma rows carry version `2026-04A`, effective 2026-04-15.

### 2.9 `ORDERS` (fact, 45,357 rows)
Order headers: `ORDER_DATE`, `ORDER_CHANNEL`, `ORDER_PRIORITY` (STANDARD, URGENT, STAT), `ORDER_STATUS`,
`LINE_COUNT`, `ORDER_VALUE_WAC`. One shipment per order.

### 2.10 `ORDER_LINES` (fact, 162,201 rows)
**The primary analytical grain.** One row per NDC per order. `QTY_ORDERED`, `QTY_SHIPPED`,
`QTY_BACKORDERED`, `QTY_CANCELLED`, `UNIT_PRICE` (contract price or WAC), `WAC_AT_ORDER`,
`IS_CONTRACT_PRICED`, `LINE_STATUS` (FILLED, PARTIAL, BACKORDERED, CANCELLED), `SHORT_REASON_CODE`
(ALLOCATION_LIMIT, STOCKOUT, MFR_SHORTAGE, QUALITY_HOLD, CREDIT_HOLD), `PROMISED_SHIP_DATE`,
`ACTUAL_SHIP_DATE`. Customer, site and DC are denormalized onto the line.

### 2.11 `SHIPMENTS` (fact, 45,318 rows)
One per order with shipped units. `CARRIER` (HALCYON_FLEET, UPS, FEDEX, COURIER), `SERVICE_LEVEL`,
`PROMISED_DELIVERY_DATE`, `ACTUAL_DELIVERY_DATE`, `DELIVERY_STATUS`, `COLD_CHAIN_REQUIRED`,
`PACKAGING_TYPE` (AMBIENT_BOX, GEL_PACK_STD, PHASE_CHANGE_48H, DRY_ICE, LN2_DEWAR), `SHIPMENT_VALUE_WAC`.

### 2.12 `COLD_CHAIN_EVENTS` (fact, 129,968 rows)
Temperature logger readings for cold chain shipments, 2 to 4 per shipment across `STAGE`
(DC_STORAGE, PACKOUT, IN_TRANSIT, DELIVERY). Only ~1% are excursions (`IS_EXCURSION = TRUE`) with
`EXCURSION_SEVERITY` (MINOR, MAJOR, CRITICAL), `DISPOSITION` (RELEASED, QUARANTINED, DESTROYED, RETURNED),
`UNITS_AFFECTED`, `VALUE_AFFECTED_WAC`. Always filter or count on `IS_EXCURSION`; a raw row count is
readings, not problems.

### 2.13 `BACKORDERS` (fact, 3,682 rows)
One per short line with backordered units. `REASON_CODE`, `STATUS` (OPEN, RELEASED, CANCELLED),
`DAYS_OPEN` (to release, or to 2026-09-25 while open), `BACKORDER_VALUE_WAC`, `EXPECTED_RELEASE_DATE`.
As of 2026-09-25 there are 213 open backorders; 77 are older than 14 days.

### 2.14 `INVENTORY_SNAPSHOTS` (fact, 97,200 rows)
Weekly Monday snapshots by DC and NDC (90 weeks x 6 DCs x 180 NDCs). Latest snapshot **2026-09-21**.
`ON_HAND_UNITS`, `AVAILABLE_UNITS`, `ON_ORDER_UNITS`, `AVG_WEEKLY_DEMAND_UNITS`, `DAYS_OF_SUPPLY`,
`EXPIRING_30D_UNITS`, `EXPIRING_90D_UNITS`, `INVENTORY_VALUE_WAC`, `EXPIRING_90D_VALUE_WAC`.
For "current" questions filter to the latest snapshot or use `V_INVENTORY_RISK`.

### 2.15 `CUSTOMER_ALLOCATIONS` (fact, 5,738 rows)
Month x allocated NDC x customer. `HALCYON_TOTAL_ALLOCATION_UNITS` is the manufacturer's allocation to
Halcyon and repeats on every customer row for that NDC and month (take MAX, never SUM).
`CUSTOMER_ALLOCATED_UNITS`, `CUSTOMER_REQUESTED_UNITS`, `CUSTOMER_CONSUMED_UNITS`, `UTILIZATION_PCT`,
`SHORTFALL_UNITS`.

### 2.16 `RETURNS` (fact, 3,312 rows)
`RETURN_REASON` (DAMAGED, TEMP_EXCURSION, SHORT_DATED, WRONG_ITEM, OVERSTOCK, RECALL), `DISPOSITION`
(RESTOCK, DESTROY, RETURN_TO_MFR), `CREDIT_AMOUNT`, `IS_SALEABLE`.

### 2.17 `CHARGEBACKS` (fact, 101,580 rows)
One claim per contract-priced shipped line. `CHARGEBACK_AMOUNT = WAC_AMOUNT - CONTRACT_AMOUNT`.
`STATUS` (SUBMITTED, APPROVED, PAID, DISPUTED, REJECTED), `DISPUTE_REASON` (PRICE_MISMATCH,
INELIGIBLE_CUSTOMER, EXPIRED_CONTRACT, DUPLICATE_CLAIM, MISSING_DEA), `PRICE_FILE_VERSION`.

### 2.18 `SERVICE_CASES` (fact, 1,419 rows)
CRM cases. `CASE_TYPE` (PRODUCT_AVAILABILITY, DELIVERY_DELAY, SHORT_SHIP, TEMP_EXCURSION,
DAMAGED_PRODUCT, BILLING_DISPUTE, ORDER_ERROR), `SEVERITY` (LOW, MEDIUM, HIGH, CRITICAL), `STATUS`,
`SLA_HOURS`, `RESOLUTION_HOURS`, `SLA_MET`, `ESCALATED_TO_EXEC`, `RELATED_BACKORDER_ID`,
`RELATED_SHIPMENT_ID`, `CASE_SUMMARY`.

### 2.19 `DATA_DICTIONARY` (metadata, 22 rows)
Column and metric descriptions with formulas.

---

## 3. ANALYTICAL VIEWS

Prefer these views for aggregate questions. They pre-join dimensions and pre-aggregate at safe grains.

### `V_ORDER_LINE_DETAIL`
Order lines with customer, site, DC, product and manufacturer attributes plus `IS_LINE_FILLED_COMPLETE`,
`SHIPPED_REVENUE`, `ORDERED_VALUE_WAC`, `BACKORDERED_VALUE_WAC`, `IS_SHIPPED_ON_TIME`, `ORDER_MONTH`.
Use for any fill rate, revenue, short ship or product mix question. Exclude `LINE_STATUS = 'CANCELLED'`
from fill rate calculations.

### `V_FILL_RATE_CUSTOMER_MONTH`
Customer x therapeutic class x month: `LINE_FILL_RATE`, `UNIT_FILL_RATE`, `BACKORDER_RATE`,
`ON_TIME_SHIP_RATE`, units and revenue. To roll up across classes, recompute rates from the unit and line
sums rather than averaging the rates.

### `V_CUSTOMER_HEALTH`
**The workbench queue.** One row per active customer with recent (2026-07-27 to 2026-09-20) vs prior
(2026-06-01 to 2026-07-26) 8-week `RECENT_LINE_FILL_RATE`, `PRIOR_LINE_FILL_RATE`, `FILL_RATE_CHANGE`,
`DISCRETIONARY_VALUE_CHANGE_PCT` (order value change on non-allocated products), `OPEN_BACKORDERS`,
`OPEN_BACKORDERS_OVER_14D`, `OLDEST_BACKORDER_DAYS`, `OPEN_BACKORDER_VALUE_WAC`, `OPEN_CASES`,
`OPEN_HIGH_SEVERITY_CASES`, `EXEC_ESCALATIONS_90D`, `EXCURSIONS_90D`, `MAJOR_EXCURSIONS_90D`,
`ALLOCATION_SHORTFALL_UNITS_90D`, `DAYS_TO_RENEWAL`, `OPERATIONAL_RISK_SCORE` (0 to 100) and
`TOP_RISK_REASON` (plain language). Score weights: 35 fill rate deterioration, 25 backorder aging,
25 service cases and escalations, 15 discretionary volume decline. The score is a triage aid, not a
churn prediction; say "operational risk indicator" rather than "churn risk".

### `V_DC_SERVICE_PERFORMANCE`
DC x month: `LINE_FILL_RATE`, `ON_TIME_SHIP_RATE`, `ON_TIME_DELIVERY_RATE`, `SHIPMENT_COUNT`,
`COLD_CHAIN_SHIPMENTS`, `EXCURSION_COUNT`, `EXCURSION_RATE`, `EXCURSION_VALUE_WAC`.

### `V_INVENTORY_RISK`
Latest snapshot (2026-09-21) by DC and NDC with product context and flags `IS_STOCKOUT_RISK`
(days of supply < 7), `IS_OVERSTOCK` (> 120), `IS_EXPIRY_WRITE_OFF_RISK` (12 weeks of demand cannot
consume units expiring in 90 days). Use for expiring inventory, days of supply and overstock questions.

### `V_ALLOCATION_UTILIZATION`
`CUSTOMER_ALLOCATIONS` with product, manufacturer and customer context plus `SHORTFALL_VALUE_WAC`.

### `V_COLD_CHAIN_EXCURSIONS`
DC x month x stage x storage class x packaging type: `READINGS`, `EXCURSIONS`, `EXCURSION_RATE`,
severity counts, `VALUE_QUARANTINED_OR_DESTROYED_WAC`, `VALUE_DESTROYED_WAC`. To compare DCs, divide
SUM(EXCURSIONS) by SUM(READINGS); do not average `EXCURSION_RATE` across rows.

### `V_CHARGEBACK_SUMMARY`
Manufacturer x month: `CLAIMS`, `AMOUNT_CLAIMED`, `AMOUNT_PAID`, `DISPUTED_OR_REJECTED_CLAIMS`,
`DISPUTE_RATE`, `AMOUNT_DISPUTED_OR_REJECTED`, `AMOUNT_OPEN`, `AVG_DAYS_TO_SETTLE`.

### `V_BACKORDER_AGING`
Open backorders as of 2026-09-25 with `AGING_BUCKET` (0-7, 8-14, 15-30, 31+) and customer, product,
manufacturer and DC context.

---

## 4. ENTITY RELATIONSHIP MAP

```
MANUFACTURERS 1--* PRODUCTS 1--* ORDER_LINES *--1 ORDERS *--1 CUSTOMER_SITES *--1 CUSTOMERS *--1 GPOS
                        |              |                |
                        |              |                +--1 SHIPMENTS 1--* COLD_CHAIN_EVENTS
                        |              +--1 BACKORDERS 1--* SERVICE_CASES (related_backorder_id)
                        |              +--1 CHARGEBACKS
                        |              +--* RETURNS
                        +--* INVENTORY_SNAPSHOTS (by DC)
                        +--* CUSTOMER_ALLOCATIONS (by customer, month)
                        +--* CONTRACT_PRICES (by GPO)
DISTRIBUTION_CENTERS 1--* CUSTOMER_SITES (serving_dc_id), ORDERS, ORDER_LINES, SHIPMENTS, INVENTORY_SNAPSHOTS
CALENDAR 1--* any date column
```

Join keys: `CUSTOMER_ID`, `SITE_ID`, `DC_ID`, `NDC`, `MANUFACTURER_ID`, `GPO_ID`, `ORDER_ID`,
`ORDER_LINE_ID`, `SHIPMENT_ID`, `BACKORDER_ID`.

**Grain warning.** Never join ORDER_LINES, SHIPMENTS, COLD_CHAIN_EVENTS, CHARGEBACKS and BACKORDERS as raw
rows in one query. Aggregate each to the customer, DC or month level first, then join the aggregates.
`V_CUSTOMER_HEALTH` and `V_DC_SERVICE_PERFORMANCE` already do this.

---

## 5. METRICS DICTIONARY

| Metric | Formula | Notes |
|---|---|---|
| **Line fill rate** | `SUM(IS_LINE_FILLED_COMPLETE) / COUNT(*)` on non-cancelled lines | The headline service metric. 97 to 98% is normal. Below 90% for a customer is a problem. |
| **Unit fill rate** | `SUM(QTY_SHIPPED) / SUM(QTY_ORDERED)` | Softer than line fill; a partial ship still counts partially. |
| **Backorder rate** | `SUM(QTY_BACKORDERED) / SUM(QTY_ORDERED)` | |
| **On-time ship rate** | `SUM(ACTUAL_SHIP_DATE <= PROMISED_SHIP_DATE) / COUNT(shipped lines)` | |
| **On-time delivery rate (OTD)** | `SUM(ACTUAL_DELIVERY_DATE <= PROMISED_DELIVERY_DATE) / COUNT(delivered shipments)` | From SHIPMENTS. |
| **OTIF** | Shipment delivered on time AND every line filled complete | Approximate with line fill x OTD when asked. |
| **Shipped revenue** | `SUM(QTY_SHIPPED * UNIT_PRICE)` | What customers were invoiced. |
| **Ordered value (WAC)** | `SUM(QTY_ORDERED * WAC_AT_ORDER)` | Demand at list; use for volume trends. |
| **Backorder aging** | `DAYS_OPEN` on open backorders | Over 14 days is the escalation threshold. |
| **Allocation utilization** | `CUSTOMER_CONSUMED_UNITS / CUSTOMER_ALLOCATED_UNITS` | 100% means the customer used everything it was given. |
| **Allocation shortfall** | `GREATEST(CUSTOMER_REQUESTED_UNITS - CUSTOMER_ALLOCATED_UNITS, 0)` | Unmet demand caused by allocation. |
| **Excursion rate** | `SUM(IS_EXCURSION) / COUNT(readings)` | Under 1% is normal. |
| **Value at risk from excursions** | `SUM(VALUE_AFFECTED_WAC) WHERE DISPOSITION IN ('QUARANTINED','DESTROYED')` | |
| **Days of supply** | `AVAILABLE_UNITS / (AVG_WEEKLY_DEMAND_UNITS / 7)` | Under 7 is stockout risk; over 120 is overstock. |
| **Expiry exposure** | `SUM(EXPIRING_90D_VALUE_WAC)` at the latest snapshot | |
| **Chargeback amount** | `WAC_AMOUNT - CONTRACT_AMOUNT` | What the manufacturer owes Halcyon. |
| **Dispute rate** | `COUNT(STATUS IN ('DISPUTED','REJECTED')) / COUNT(*)` | 3 to 5% is normal. |
| **SLA attainment** | `COUNT(SLA_MET) / COUNT(closed cases)` | |
| **Days to renewal** | `DATEDIFF('day', DATE '2026-09-25', CONTRACT_RENEWAL_DATE)` | |
| **Operational risk score** | see `V_CUSTOMER_HEALTH` | Triage aid, 0 to 100. |

---

## 6. SYNONYMS MASTER LIST

**Service and fulfillment**
- "fill rate", "service level", "first-pass fill", "complete lines" → `LINE_FILL_RATE`
- "unit fill", "quantity fill" → `UNIT_FILL_RATE`
- "short ship", "shorted", "cut", "partial" → `LINE_STATUS IN ('PARTIAL','BACKORDERED')` or `QTY_SHIPPED < QTY_ORDERED`
- "backorder", "BO", "on backorder", "open backorders", "aged backorders" → `BACKORDERS` (status OPEN) / `V_BACKORDER_AGING`
- "stockout", "out of stock", "OOS" → `SHORT_REASON_CODE = 'STOCKOUT'` or `IS_STOCKOUT_RISK`
- "on time", "OTD", "delivered on time", "late deliveries" → `ON_TIME_DELIVERY_RATE` / `ACTUAL_DELIVERY_DATE > PROMISED_DELIVERY_DATE`
- "OTIF", "perfect order" → on time and complete (see metrics)
- "STAT", "emergency order", "rush" → `ORDER_PRIORITY = 'STAT'`
- "auto-replenish", "auto replenishment", "VMI", "standing order" → `ORDER_CHANNEL = 'AUTO_REPLENISH'`

**Allocation and supply**
- "allocation", "allocated product", "constrained product", "on allocation", "limited supply" → `PRODUCTS.IS_ALLOCATED` / `CUSTOMER_ALLOCATIONS`
- "fair share", "historical share" → `ALLOCATION_BASIS`
- "shortfall", "unmet demand", "gap to request" → `SHORTFALL_UNITS`
- "manufacturer cut", "allocation cut", "reduced allocation" → change in `HALCYON_TOTAL_ALLOCATION_UNITS` month over month
- "GLP-1", "GLP1", "weight loss drugs", "semaglutide-class", "metabolic" → `THERAPEUTIC_CLASS = 'GLP1_METABOLIC'`
- "Vanterra", "velmaglutide" → `NDC = '61234-0101-04'`
- "Veltrix" → `MANUFACTURER_ID = 'MFR-001'`

**Cold chain**
- "cold chain", "temperature", "temp", "excursion", "temp excursion", "out of range" → `COLD_CHAIN_EVENTS` with `IS_EXCURSION = TRUE`
- "refrigerated", "2-8", "fridge product" → `STORAGE_CLASS = 'REFRIGERATED_2_8C'`
- "frozen" → `'FROZEN_MINUS20'`; "ultra cold", "-70", "deep frozen" → `'ULTRA_COLD_MINUS70'`
- "gel packs", "standard packaging" → `PACKAGING_TYPE = 'GEL_PACK_STD'`; "phase change", "PCM", "48 hour packs" → `'PHASE_CHANGE_48H'`
- "quarantined", "on hold", "destroyed", "written off" → `DISPOSITION`
- "packout", "packing" → `STAGE = 'PACKOUT'`

**Inventory**
- "on hand", "stock", "inventory position" → `ON_HAND_UNITS`
- "available to promise", "ATP", "available" → `AVAILABLE_UNITS`
- "days of supply", "DOS", "weeks of supply", "cover" → `DAYS_OF_SUPPLY`
- "short dated", "expiring", "near expiry", "expiry risk", "dated product" → `EXPIRING_30D_UNITS` / `EXPIRING_90D_UNITS`
- "overstock", "excess", "too much inventory" → `IS_OVERSTOCK`
- "write off", "waste", "obsolescence" → `IS_EXPIRY_WRITE_OFF_RISK` or `RETURNS.DISPOSITION = 'DESTROY'`
- "Oncaryl", "ambertuzumab" → `NDC = '58771-0410-01'`

**Commercial**
- "customer", "account", "client", "health system", "IDN", "provider" → `CUSTOMERS`
- "site", "ship-to", "location", "facility", "pharmacy" (as a place) → `CUSTOMER_SITES`
- "strategic accounts", "top accounts", "tier 1" → `CUSTOMER_TIER = 'STRATEGIC'`
- "renewal", "renewing", "contract expiring", "up for renewal" → `CONTRACT_RENEWAL_DATE` / `DAYS_TO_RENEWAL`
- "ACV", "contract value", "book of business" → `ANNUAL_CONTRACT_VALUE`
- "revenue", "sales", "net sales" → `SHIPPED_REVENUE`
- "volume", "demand" → `QTY_ORDERED` or `ORDERED_VALUE_WAC`
- "GPO", "buying group", "purchasing alliance" → `GPOS`
- "WAC", "list price", "wholesale acquisition cost" → `WAC_UNIT_PRICE` / `WAC_AT_ORDER`
- "contract price", "GPO price", "member price" → `CONTRACT_PRICE` / `UNIT_PRICE` when `IS_CONTRACT_PRICED`
- "chargeback", "CB", "rebate claim", "manufacturer credit" → `CHARGEBACKS`
- "disputed", "denied", "rejected chargebacks", "chargeback leakage" → `STATUS IN ('DISPUTED','REJECTED')`
- "price file", "contract load" → `PRICE_FILE_VERSION`
- "Keldon" → `MANUFACTURER_ID = 'MFR-002'`

**Service**
- "case", "ticket", "complaint", "escalation", "issue" → `SERVICE_CASES`
- "exec escalation", "escalated to leadership" → `ESCALATED_TO_EXEC = TRUE`
- "SLA", "resolution time", "time to resolve" → `SLA_HOURS`, `RESOLUTION_HOURS`, `SLA_MET`
- "sev 1", "critical" → `SEVERITY = 'CRITICAL'`; "high sev" → `SEVERITY IN ('HIGH','CRITICAL')`

**Time**
- "today", "now", "current" → 2026-09-25 (the data as-of date)
- "this week" → week starting 2026-09-21 (partial); "last complete week" → 2026-09-14 to 2026-09-20
- "last 8 weeks", "recent" → 2026-07-27 to 2026-09-20; "prior 8 weeks" → 2026-06-01 to 2026-07-26
- "this quarter" → 2026-Q3 (Jul to Sep); "next 120 days" → through 2027-01-23
- "summer" → June to August 2026

---

## 7. DOMAIN KNOWLEDGE

- Specialty distribution runs on thin margins. Most gross margin comes from the spread between WAC and
  contract price being recovered via chargebacks, plus manufacturer service fees. A disputed chargeback is
  margin that has not been collected, and a rejected one is margin lost unless resubmitted.
- Line fill rate is the service metric customers hold distributors to in prime vendor agreements; 97 to 98%
  is typical, and sustained periods under 90% on a strategic account trigger contract conversations.
- Allocated products are the exception to "just ship it". When a manufacturer cuts Halcyon's monthly
  allocation, Halcyon must decide how to split the reduced quantity across customers. Historical share
  protects long-standing buyers and penalizes fast-growing ones. Customers on the wrong side of that will
  source the product elsewhere and often move other categories with it.
- Cold chain excursions are quality events. Product in a MAJOR or CRITICAL excursion is normally
  quarantined pending manufacturer stability data, and destroyed if it cannot be released. Packaging
  choice (gel packs vs phase change material) is the largest controllable driver of packout excursions,
  especially in summer.
- Short-dated specialty inventory cannot be returned to most manufacturers for full credit once inside
  90 days of expiry. The options are transfer to a DC with demand, a short-dated sale at a discount to a
  customer who can use it quickly, or write-off.
- Backorders older than 14 days are the point at which customers escalate to their account manager and
  pharmacy leadership; the data shows most HIGH and CRITICAL product availability cases are attached to
  backorders past that age.
- Auto-replenishment (Halcyon manages the par levels) fills better and generates almost no STAT orders
  because demand is visible earlier. It is Halcyon's preferred channel and an expansion lever.

---

## 8. BUSINESS NUANCES

- `ORDER_LINES.QTY_SHIPPED` is the first release. Backorders that later ship are recorded in `BACKORDERS`
  (`STATUS = 'RELEASED'`), not by updating the line. Line fill rate therefore measures first-pass service.
- `HALCYON_TOTAL_ALLOCATION_UNITS` repeats on every customer row for the NDC and month. Use MAX or a
  DISTINCT subquery; summing it multiplies the allocation by the number of customers.
- `COLD_CHAIN_EVENTS` rows are readings. Excursion questions must filter `IS_EXCURSION = TRUE`.
- `SERVICE_CASES` is customer-reported. A quiet customer is not necessarily a healthy one; combine cases
  with fill rate and backorder signals.
- `INVENTORY_SNAPSHOTS` is weekly. "Current inventory" means the 2026-09-21 snapshot. Summing across
  snapshot dates double counts.
- `CHARGEBACKS` exist only for contract-priced shipped lines. Lines with `IS_CONTRACT_PRICED = FALSE`
  (customers with no GPO, or products not on their GPO contract) generate no claim.
- Contract renewal date is on `CUSTOMERS`; one agreement per customer in this build.
- `ORDER_DATE` is denormalized onto `ORDER_LINES`, `BACKORDER_DATE` equals the order date of the short line.
- The current week (starting 2026-09-21) is partial. Use `CALENDAR.IS_COMPLETE_WEEK` or an explicit
  cutoff of 2026-09-20 for weekly trends.
- Holidays (`CALENDAR.IS_US_HOLIDAY`) have no orders. Do not read a holiday week dip as a demand change.

---

## 9. TRIBAL KNOWLEDGE

- When a customer's overall fill rate drops, check the therapeutic class breakdown first. A problem
  confined to one allocated product looks very different from a DC-wide issue.
- Order value on allocated products is not a demand signal, because customers over-request when they
  expect to be shorted. Use non-allocated (discretionary) order value to judge whether a customer is
  shifting business away; `V_CUSTOMER_HEALTH.DISCRETIONARY_VALUE_CHANGE_PCT` does this.
- Compare DC excursion rates within the same storage class and stage. Ultra-cold and frozen product
  rarely excurse; a DC with more refrigerated volume will look worse on a blended number.
- When a chargeback dispute rate jumps for one manufacturer and the reasons are PRICE_MISMATCH and
  INELIGIBLE_CUSTOMER, look at `PRICE_FILE_VERSION`. A new price file with different eligibility or
  pricing is the usual cause, and the fix is a reconciliation with the manufacturer, not customer by
  customer rework.
- For expiring inventory, always check whether another DC or a nearby customer still has demand for the
  same NDC before treating it as a write-off. Oncology practices served by the same DC are the first
  place to look.
- Strategic customers renewing inside 120 days with a rising risk score are reviewed weekly by the
  Director of Customer Supply Operations with the account manager. The review asks: what is the root
  cause, what can operations fix this week, and what commercial cover is needed until then.

---

## 10. QUERY ROUTING HINTS

- "Which customers need attention / are at risk / renewing with problems" → `V_CUSTOMER_HEALTH`, order by
  `OPERATIONAL_RISK_SCORE DESC`, filter `DAYS_TO_RENEWAL BETWEEN 0 AND 120` when renewal is mentioned.
- Fill rate over time for a customer, class or DC → `V_FILL_RATE_CUSTOMER_MONTH` or
  `V_ORDER_LINE_DETAIL` grouped by `ORDER_MONTH`; recompute rates from sums when rolling up.
- Allocation requested vs allocated vs consumed → `V_ALLOCATION_UTILIZATION` by `PERIOD_MONTH`.
- Manufacturer allocation trend → `MAX(HALCYON_TOTAL_ALLOCATION_UNITS)` by `NDC, PERIOD_MONTH`.
- Open backorders, aging, oldest → `V_BACKORDER_AGING`.
- Cold chain by DC, packaging, month → `V_COLD_CHAIN_EXCURSIONS`; excursion rate = SUM(EXCURSIONS)/SUM(READINGS).
- Individual excursion events, dispositions, timestamps → `COLD_CHAIN_EVENTS` with `IS_EXCURSION = TRUE`.
- Expiring or excess inventory now → `V_INVENTORY_RISK`; inventory over time → `INVENTORY_SNAPSHOTS`.
- Chargeback disputes by manufacturer → `V_CHARGEBACK_SUMMARY`; dispute reasons → `CHARGEBACKS` grouped by `DISPUTE_REASON`.
- Service cases, SLA, escalations → `SERVICE_CASES`; link to backorders via `RELATED_BACKORDER_ID`.
- DC performance comparison → `V_DC_SERVICE_PERFORMANCE`.
- Channel comparison (auto-replenish vs EDI vs portal) → `V_ORDER_LINE_DETAIL` grouped by `ORDER_CHANNEL`.
- Revenue by customer, class, manufacturer → `V_ORDER_LINE_DETAIL` `SUM(SHIPPED_REVENUE)`.
- Any "today" or "current" → anchor to 2026-09-25; latest inventory snapshot 2026-09-21; latest complete week ends 2026-09-20.
