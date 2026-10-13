# Keelstone Data Systems — Domain Bootstrap (wACE)

Domain: **Keelstone Data Systems**, a fictional hybrid-cloud storage and data infrastructure vendor.
Warehouse: Snowflake `KEELSTONE_POC.ANALYTICS`.
Demo as-of date: **2026-10-12** (Monday), which is Q2 of fiscal year FY27. Keelstone's fiscal year ends 30 April.
Data spans 2025-05-01 to 2026-10-12; installed systems and contracts reach back to 2020.

---

## 1. DOMAIN OVERVIEW

Keelstone sells four things: storage arrays (the KS-5000, KS-7000, KS-9000 all-flash families and the HD-3000
hybrid family), the KeelOS storage operating system sold as a subscription, Keelstone Cloud Volumes and
Keelstone Object Store running on Azure, AWS and Google Cloud and billed against an annual commit, and support
contracts (Standard, Premium, Mission Critical) on every installed array. Most business goes through channel
partners (VARs, distributors and MSPs); large enterprises are sometimes sold direct ("Keelstone Direct").

The primary user is the **VP of Sales Operations**, measured on renewal rate, ARR and ARR at risk in the next
90 days. Finance (FP&A) owns the certified definitions of ARR, NRR and renewal rate. Executives, renewals
specialists and data stewards use the same domain.

Core mechanics represented:

- **Bookings** (SAP S/4HANA): hardware is a one-time booking; subscriptions, cloud commits and support book at
  total contract value. Bookings are never ARR.
- **Installed base** (AutoPulse telemetry registry): every array shipped, its model, install date, firmware and
  monthly health telemetry. The KS-7000 family left the price list on 2025-10-31 and reaches end of support on
  2027-01-31 (bulletin PLB-2026-014, 2026-06-15).
- **Contracts** (SAP): support contracts per system, KeelOS Core subscriptions per array, customer-level KeelOS
  add-ons, and cloud commits. A contract is in force while `START_DATE <= date < END_DATE`. When it lapses it
  is RENEWED (a successor contract starts the same day), CHURNED (closed lost) or PENDING_RENEWAL (renewal still
  open in Salesforce).
- **Renewal opportunities** (Salesforce): one per contract end, with stage, quote, risk flag and reason.
- **Cloud consumption**: metered monthly usage against the commit.
- **Support cases** (ServiceNow): priority P1-P4, category, firmware version and free-text engineer notes.

Scale: about $500M Finance ARR, 400 customers, 2,300 installed arrays, 10.7K contracts including history, 5.2K
renewal opportunities, 5.3K support cases.

---

## 2. TABLE CATALOG

### 2.1 `FISCAL_CALENDAR` (dimension, 1,095 rows)
One row per day 2024-05-01 to 2027-04-30. `FISCAL_YEAR` (FY27 = 2026-05-01 to 2027-04-30), `FISCAL_QUARTER`
(FY27-Q2 = Aug-Oct 2026), `FISCAL_MONTH_NUM` (May = 1), `MONTH_START_DATE`, `MONTH_END_DATE`,
`IS_COMPLETE_MONTH` (TRUE for months fully before 2026-10-12).

### 2.2 `PARTNERS` (dimension, 25 rows)
Channel partners with `PARTNER_TYPE` (VAR, DISTRIBUTOR, MSP, DIRECT), `PARTNER_TIER` (PLATINUM, GOLD, SILVER,
NA) and `PRIMARY_REGION`. `PTR-000` is Keelstone Direct. **Altura Technology Partners** (PTR-003) is the largest
Americas East partner.

### 2.3 `SALES_REPS` (dimension, 60 rows)
Account Executives, Renewals Specialists and Cloud Specialists by `REGION` (Americas East, Americas West, EMEA,
APAC) and `THEATER` (Americas, International).

### 2.4 `CUSTOMERS` (dimension, 400 rows)
`SEGMENT` (ENTERPRISE, COMMERCIAL, PUBLIC_SECTOR), `INDUSTRY`, `REGION`, `COUNTRY`, partner of record
(`PARTNER_ID`), owning rep (`REP_ID`), `CRM_ACCOUNT_ID` (Salesforce), `CUSTOMER_SINCE`.

### 2.5 `PRODUCTS` (dimension, 23 rows)
`PRODUCT_FAMILY` (KS-5000, KS-7000, KS-9000, HD-3000, KeelOS, Keelstone Cloud Volumes, Keelstone Object Store,
Support), `PRODUCT_LINE` (HARDWARE, SOFTWARE_SUBSCRIPTION, CLOUD_SERVICE, SUPPORT), `SUPPORT_TIER`,
`LIST_PRICE`, `UNIT_OF_MEASURE`, `END_OF_SALE_DATE`, `END_OF_SUPPORT_DATE`, `IS_RECURRING`.

### 2.6 `ORDERS` (fact, 5.7K rows, grain = order line)
Bookings from 2025-05-01: `ORDER_DATE`, customer, product, partner, rep, `BOOKING_TYPE` (NEW, EXPANSION,
RENEWAL), `QUANTITY`, `LIST_AMOUNT`, `DISCOUNT_PCT`, `NET_AMOUNT`. Source SAP S/4HANA.

### 2.7 `INSTALLED_SYSTEMS` (fact, 2.3K rows, grain = array)
`SYSTEM_ID` (serial), customer, `PRODUCT_ID` (array model), partner, `INSTALL_DATE`, site, `RAW_CAPACITY_TB`,
`WORKLOAD_TYPE`, `CURRENT_FIRMWARE` (KeelOS version on 2026-10-12), `SYSTEM_STATUS` (ACTIVE, DECOMMISSIONED).

### 2.8 `SYSTEM_TELEMETRY_MONTHLY` (fact, 32K rows, grain = system x month)
AutoPulse call-home: `SNAPSHOT_MONTH` (2025-05 to 2026-09), `FIRMWARE_VERSION`, `CAPACITY_USED_PCT`,
`HEALTH_SCORE` (0-100), `CRITICAL_ALERTS`, `UPTIME_PCT`, `AVG_LATENCY_MS`.

### 2.9 `CONTRACTS` (fact, 10.7K rows, grain = contract)
`CONTRACT_TYPE` (SUPPORT, SOFTWARE_SUBSCRIPTION, CLOUD_COMMIT), `SYSTEM_ID` (for support and per-array KeelOS
Core), `START_DATE`, `END_DATE` (exclusive), `TERM_MONTHS`, `ANNUAL_VALUE` (the ARR contribution),
`TOTAL_CONTRACT_VALUE`, `CONTRACT_STATUS` (ACTIVE, RENEWED, CHURNED, PENDING_RENEWAL), `OUTCOME_DATE`,
`SUCCESSOR_CONTRACT_ID`, `PREDECESSOR_CONTRACT_ID`.

### 2.10 `RENEWAL_OPPORTUNITIES` (fact, 5.2K rows, grain = opportunity)
One per contract ending 2025-05-01 to 2027-04-10: `STAGE` (Qualification, Quote Sent, Negotiation, Closed Won,
Closed Lost), `QUOTE_AMOUNT`, `RISK_FLAG` (ON_TRACK, AT_RISK), `RISK_REASON`, `COMPETITOR`. Source Salesforce.

### 2.11 `CLOUD_CONSUMPTION_MONTHLY` (fact, 2.1K rows, grain = customer x month)
`USAGE_MONTH`, `CLOUD_PROVIDER`, `MONTHLY_COMMIT_AMOUNT`, `CONSUMED_AMOUNT`, `CONSUMED_TB`, `OVERAGE_AMOUNT`.

### 2.12 `SUPPORT_CASES` (fact, 5.3K rows, grain = case)
`OPENED_DATE`, `CLOSED_DATE`, `PRIORITY` (P1-P4), `CASE_STATUS`, `CATEGORY`, `SUBCATEGORY`,
`FIRMWARE_VERSION`, `ROOT_CAUSE`, `RESOLUTION_HOURS`, `CSAT_SCORE`, `CASE_NOTES` (free text). Source ServiceNow.

### 2.13 `DATA_DICTIONARY` (metadata, 24 rows)
Column and metric definitions with `BUSINESS_OWNER` and `SOURCE_SYSTEM`: the physical half of the glossary.

---

## 3. ANALYTICAL VIEWS

Prefer these views for aggregate questions. They encode the certified definitions.

### `V_ARR_MONTHLY`
Certified Finance ARR by `ARR_MONTH` x `REGION` x `SEGMENT` x `CONTRACT_TYPE` x `PRODUCT_FAMILY` (for support
and KeelOS Core contracts the family is the covered array's family). `ARR` is the sum of `ANNUAL_VALUE` of
contracts in force on `ARR_AS_OF_DATE` (month end, or 2026-10-12 for October). Sum across slices within a
month; never sum across months. Current ARR = the 2026-10-01 row set.

### `V_ARR_FINANCE_VS_SALESOPS`
By month and region: `FINANCE_ARR`, `LAPSED_OPEN_ARR` (lapsed contracts whose Salesforce opportunity is still
open, within a year of the lapse), `SALESOPS_ARR` = Finance + lapsed open, `GAP_PCT`.

### `V_RENEWAL_PERFORMANCE`
Contracts that ended 2025-05-01 to 2026-10-12 by `FISCAL_YEAR` x `FISCAL_QUARTER` x `REGION` x `SEGMENT` x
`CONTRACT_TYPE` x `PRODUCT_FAMILY`: `ARR_DUE`, `ARR_RENEWED`, `ARR_CHURNED`, `ARR_PENDING`, contract counts,
`RENEWAL_RATE`, `CHURN_RATE`. Roll up with SUM(ARR_RENEWED)/SUM(ARR_DUE).

### `V_RENEWALS_AT_RISK_90D`
One row per active contract ending 2026-10-13 to 2027-01-10 with customer, region, partner, rep, product,
`SYSTEM_MODEL`, `ANNUAL_VALUE`, `DAYS_TO_RENEWAL`, opportunity `OPPORTUNITY_STAGE`, `RISK_FLAG`, `RISK_REASON`,
`IS_END_OF_SUPPORT_WITHIN_12M`, `OPEN_P1_CASES`, `P1_CASES_90D`.

### `V_INSTALLED_BASE_HEALTH`
One row per active array: model, family, age, capacity, `CURRENT_FIRMWARE`, September 2026 telemetry,
`CRITICAL_ALERTS_3M`, `END_OF_SUPPORT_DATE`, `IS_END_OF_SUPPORT_WITHIN_12M`, `HAS_ACTIVE_SUPPORT`,
`SUPPORT_END_DATE`, `OPEN_P1_CASES`, `CASES_90D`.

### `V_CLOUD_COMMIT_UTILIZATION`
Customer x fiscal year: `COMMIT_AMOUNT`, `CONSUMED_AMOUNT`, `OVERAGE_AMOUNT`, `UTILIZATION_PCT`,
`IS_UNDER_UTILIZED` (below 60 percent with 3+ months).

### `V_SUPPORT_CASE_SUMMARY`
Opened month x region x segment x product family x priority x category x firmware version: `CASES`,
`OPEN_CASES`, `P1_CASES`, `AVG_RESOLUTION_HOURS`, `AVG_CSAT`, `CUSTOMERS_AFFECTED`.

### `V_PARTNER_ATTACH_RATE`
Partner x fiscal quarter for systems installed since 2024-05-01: `SYSTEMS_INSTALLED`, `SYSTEMS_WITH_SUPPORT`,
`ATTACH_RATE`. Roll up with SUM(SYSTEMS_WITH_SUPPORT)/SUM(SYSTEMS_INSTALLED).

---

## 4. ENTITY RELATIONSHIP MAP

```
PARTNERS 1--* CUSTOMERS *--1 SALES_REPS
              |
              +--* INSTALLED_SYSTEMS *--1 PRODUCTS (array model)
              |        +--* SYSTEM_TELEMETRY_MONTHLY
              |        +--* CONTRACTS (support, KeelOS Core)   *--1 PRODUCTS (support tier / subscription)
              |        +--* SUPPORT_CASES
              +--* CONTRACTS (add-ons, cloud commits) 1--1 RENEWAL_OPPORTUNITIES
              |        +--* CLOUD_CONSUMPTION_MONTHLY (cloud commits)
              +--* ORDERS *--1 PRODUCTS
FISCAL_CALENDAR 1--* any date column (join on CALENDAR_DATE)
```

Join keys: `CUSTOMER_ID`, `PARTNER_ID`, `REP_ID`, `PRODUCT_ID`, `SYSTEM_ID`, `CONTRACT_ID`, `ORDER_LINE_ID`.

**Grain warning.** CONTRACTS includes history: filter on dates or `CONTRACT_STATUS` before summing
`ANNUAL_VALUE`. Never join CONTRACTS, SUPPORT_CASES and SYSTEM_TELEMETRY_MONTHLY as raw rows in one query;
aggregate each to the customer or system first. The views already do this.

---

## 5. METRICS DICTIONARY

| Metric | Formula | Notes |
|---|---|---|
| **ARR (Finance, certified)** | `SUM(ANNUAL_VALUE)` of contracts with `START_DATE <= d < END_DATE` | Finance Metric Definitions Standard v3.2. Use `V_ARR_MONTHLY`. |
| **Sales Ops ARR** | Finance ARR + lapsed contracts with an open renewal opportunity | Not certified. `V_ARR_FINANCE_VS_SALESOPS.SALESOPS_ARR`. |
| **ARR gap** | `LAPSED_OPEN_ARR / FINANCE_ARR` | Explains the difference between the two numbers. |
| **Renewal rate** | `SUM(ARR_RENEWED) / SUM(ARR_DUE)` | Renewed only when a successor contract is signed; pending counts as not yet renewed. |
| **Churn rate** | `SUM(ARR_CHURNED) / SUM(ARR_DUE)` | Closed lost. |
| **ARR up for renewal (90 days)** | `SUM(ANNUAL_VALUE)` from `V_RENEWALS_AT_RISK_90D` | Active contracts ending 2026-10-13 to 2027-01-10. |
| **ARR at risk** | same, `RISK_FLAG = 'AT_RISK'` | Flag set by the renewals team in Salesforce. |
| **Support attach rate** | `SUM(SYSTEMS_WITH_SUPPORT) / SUM(SYSTEMS_INSTALLED)` | Support contract starting within 60 days of install. |
| **Commit utilisation** | `SUM(CONSUMED_AMOUNT) / SUM(MONTHLY_COMMIT_AMOUNT)` | Fiscal year to date. Under 60 percent is under-utilised. |
| **Cloud consumption growth** | consumed this period / consumed same period last year - 1 | Use `CLOUD_CONSUMPTION_MONTHLY`. |
| **P1 cases** | `COUNT(*) WHERE PRIORITY = 'P1'` | Production down. |
| **Installed base health** | `HEALTH_SCORE` from the latest telemetry month | Below 70 is poor. |
| **End-of-support exposure** | systems where `END_OF_SUPPORT_DATE` is within 12 months | KS-7000 family: 2027-01-31. |
| **Bookings** | `SUM(NET_AMOUNT)` from `ORDERS` | Total contract value, not ARR. |

---

## 6. SYNONYMS MASTER LIST

**Revenue**
- "ARR", "annual recurring revenue", "recurring revenue", "run rate" → `V_ARR_MONTHLY.ARR` (Finance definition)
- "Sales Ops ARR", "the Salesforce number", "bookings ARR" → `V_ARR_FINANCE_VS_SALESOPS.SALESOPS_ARR`
- "bookings", "orders", "TCV" → `ORDERS.NET_AMOUNT`
- "contract value", "annual value", "ACV" → `CONTRACTS.ANNUAL_VALUE`

**Renewals**
- "renewal rate", "gross retention", "GRR" → `V_RENEWAL_PERFORMANCE.RENEWAL_RATE`
- "churn", "lost", "non-renewal" → `CONTRACT_STATUS = 'CHURNED'`
- "pending", "stalled", "open renewal", "lapsed" → `CONTRACT_STATUS = 'PENDING_RENEWAL'`
- "up for renewal", "renewing", "coming due", "expiring" → `V_RENEWALS_AT_RISK_90D` or `CONTRACTS.END_DATE`
- "at risk", "red accounts", "flagged" → `RISK_FLAG = 'AT_RISK'`

**Installed base and support**
- "install base", "fleet", "estate", "arrays", "systems", "boxes" → `INSTALLED_SYSTEMS` / `V_INSTALLED_BASE_HEALTH`
- "EOS", "end of support", "end of life", "EOL", "sunset" → `END_OF_SUPPORT_DATE`
- "end of sale", "EOSL", "off the price list" → `END_OF_SALE_DATE`
- "firmware", "OS version", "KeelOS release", "9.14" → `CURRENT_FIRMWARE` / `FIRMWARE_VERSION`
- "attach", "attach rate", "support coverage" → `V_PARTNER_ATTACH_RATE` / `HAS_ACTIVE_SUPPORT`
- "P1", "sev 1", "outage", "production down" → `PRIORITY = 'P1'`
- "ticket", "case", "incident" → `SUPPORT_CASES`
- "health", "AutoPulse score" → `HEALTH_SCORE`

**Cloud**
- "cloud", "Cloud Volumes", "KCV", "consumption", "usage" → `CLOUD_CONSUMPTION_MONTHLY`
- "commit", "committed spend", "annual commit" → `MONTHLY_COMMIT_AMOUNT` x 12 or `CONTRACTS` type CLOUD_COMMIT
- "under-utilised", "under-consumed", "shortfall", "burn down" → `IS_UNDER_UTILIZED`

**Organisation**
- "region", "theater", "geo" → `CUSTOMERS.REGION` (Americas East, Americas West, EMEA, APAC)
- "AMER East", "East", "Northeast" → `Americas East`
- "partner", "channel", "VAR", "reseller" → `PARTNERS`
- "rep", "AE", "account manager", "renewals specialist" → `SALES_REPS`
- "fiscal year", "FY27", "this year" → `FISCAL_CALENDAR.FISCAL_YEAR`; FY27 started 2026-05-01

---

## 7. DOMAIN KNOWLEDGE

- Keelstone's fiscal year ends 30 April and is named for the calendar year it ends in. FY27 runs 2026-05-01 to 2027-04-30 and the demo date 2026-10-12 is in FY27-Q2. "This fiscal year" means FY27 to date (May through 12 October 2026).
- ARR is the sum of ANNUAL_VALUE of contracts in force on the measurement date (START_DATE <= date < END_DATE). This is the certified Finance definition from the Finance Metric Definitions Standard v3.2 and is what V_ARR_MONTHLY computes. Hardware bookings are never ARR.
- Renewal rate is ARR renewed divided by ARR due in the period. A contract counts as renewed only when its successor contract is signed. A lapsed contract whose renewal is still open is PENDING_RENEWAL and counts as not yet renewed.
- The KS-7000 array family (KS-7200, KS-7400, KS-7600) left the price list on 2025-10-31 and reaches end of support on 2027-01-31 under product lifecycle bulletin PLB-2026-014 issued 2026-06-15. The migration targets are the KS-9300 and KS-9500. KS-7000 Extended Support (SUP-EXT7K) covers systems to 2028-01-31.
- KeelOS 9.14.2 was released 2026-07-01 and carries defect KB-2026-0917 which causes controller failover loops during takeover and giveback. The fix is KeelOS 9.14.3 released 2026-09-15. Americas East received the AutoPulse managed upgrade to 9.14.2 in July and August 2026; the other regions started upgrading in September.
- Altura Technology Partners (PTR-003) is the largest Americas East partner. Its support attach rate on new systems fell from about 77 percent in FY26 to about 61 percent in FY27 while the other large partners stayed near 76 percent.

---

## 8. BUSINESS NUANCES

- Finance and Sales Ops report different ARR figures. Finance stops counting a contract on the day it lapses. Sales Ops keeps counting a lapsed contract while its renewal opportunity is still open in Salesforce, which renewals ops closes as lost up to a year after the lapse. When asked for ARR give the Finance figure and explain the gap with V_ARR_FINANCE_VS_SALESOPS when the two numbers are compared.
- Renewal rate questions should be answered in ARR dollars (SUM of ARR_RENEWED over SUM of ARR_DUE) not by averaging RENEWAL_RATE rows. The same applies to ATTACH_RATE and UTILIZATION_PCT.
- Product family for a support contract or a KeelOS Core subscription means the family of the covered array (KS-7000 for example) and that is how the views report it. The product on the contract itself is the support tier or the subscription SKU.
- Contracts ending in the next 90 days are the renewal pipeline. The renewals team sets RISK_FLAG on the Salesforce opportunity; End of support product and Open P1 case are the reasons that matter in Americas East right now.
- A P1 support case is production down. P1 cases on KeelOS 9.14.2 since July 2026 are concentrated in Americas East because that region upgraded first.
- Cloud commit utilisation under 60 percent in a fiscal year means the customer is paying for capacity it is not using; those accounts are the ones to talk to before the commit renews.
- Describe RISK_FLAG and the at-risk list as the renewals team's assessment, never as a churn prediction.

---

## 9. TRIBAL KNOWLEDGE

- CONTRACTS includes every historical contract; when summing ANNUAL_VALUE always restrict to contracts in force on a date or to a CONTRACT_STATUS. A plain SUM over the table counts the same renewal chain several times.
- END_DATE is exclusive. A contract ending 2026-12-01 is in force through 2026-11-30 and its renewal starts on 2026-12-01.
- SYSTEM_TELEMETRY_MONTHLY runs to September 2026 (SNAPSHOT_MONTH 2026-09-01). Current telemetry means that month. The October partial month has no telemetry.
- CLOUD_CONSUMPTION_MONTHLY runs to September 2026. Year over year cloud growth compares the same months of 2026 and 2025.
- CASE_NOTES is free text. To find what customers are saying about a renewal or an outage read the notes on P1 cases rather than relying on CATEGORY alone.
- The at-risk and renewal figures for a region should be taken from V_RENEWALS_AT_RISK_90D and V_RENEWAL_PERFORMANCE which already apply the certified definitions; do not recompute them from RENEWAL_OPPORTUNITIES alone because opportunities carry quote amounts not contract values.

---

## 10. QUERY ROUTING HINTS

- "What is our ARR" or ARR by region, segment, family, month → `V_ARR_MONTHLY`; current ARR is the 2026-10-01 rows.
- "Why do Finance and Sales Ops disagree" or Sales Ops ARR → `V_ARR_FINANCE_VS_SALESOPS`.
- Renewal rate, churn, pending renewals by quarter, region, family → `V_RENEWAL_PERFORMANCE`; roll up with SUM(ARR_RENEWED)/SUM(ARR_DUE).
- Renewals coming up, at-risk ARR, who to call → `V_RENEWALS_AT_RISK_90D`; filter `RISK_FLAG = 'AT_RISK'` for the at-risk list.
- Which systems reach end of support, firmware spread, support coverage, health → `V_INSTALLED_BASE_HEALTH`.
- Cloud utilisation, under-used commits → `V_CLOUD_COMMIT_UTILIZATION` (fiscal year FY27); monthly trend and growth → `CLOUD_CONSUMPTION_MONTHLY`.
- Case volumes, P1 trends, firmware-related cases → `V_SUPPORT_CASE_SUMMARY`; what customers said → `SUPPORT_CASES.CASE_NOTES`.
- Partner attach rate → `V_PARTNER_ATTACH_RATE`; roll up with SUM(SYSTEMS_WITH_SUPPORT)/SUM(SYSTEMS_INSTALLED).
- Bookings by month, product line, partner → `ORDERS` joined to PRODUCTS and FISCAL_CALENDAR.
- Any "today" or "current" → anchor to 2026-10-12; latest telemetry and consumption month is 2026-09; the current fiscal quarter is FY27-Q2.
