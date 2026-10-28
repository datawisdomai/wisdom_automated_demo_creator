# Meridian Clinician Network — Domain Bootstrap (wACE)

Demo as-of date: **2026-09-30** (last day of Q3 2026; the close starts 2026-10-01). Data spans 2024-01-01 to 2026-09-30.
Warehouse: Snowflake `MERIDIAN_POC.ANALYTICS`. Dialect: Snowflake.

---

## 1. DOMAIN OVERVIEW

Meridian Clinician Network is a fictional, free professional network for US physicians, nurse practitioners, physician assistants and pharmacists. Revenue is B2B from two customer types: **pharma brands** buy specialty-targeted campaigns, sponsored content, newsletter placements and peer discussion programs; **health systems** buy recruiting placements, employer branding, residency navigator sponsorships and directory profiles. Agreements are multi-year, billed upfront, quarterly, monthly or by milestone, and amended constantly.

Every closed deal exists in three systems that should agree: the signed agreement in **DocuSign** (legal truth; its extracted terms are the CONTRACTS tables), the closed-won **Salesforce** opportunity entered by the rep, and the **NetSuite** sales order that **Boomi** creates from the opportunity and that drives billing and revenue recognition. Until now Sales Ops, Revenue Accounting and Billing each reconciled their own slice by hand (two spreadsheets and an Alteryx workflow). This domain performs the full **three-way match** live: eleven checks derived from the raw tables using `RECONCILIATION_CONTROLS` as the rulebook. There is no precomputed results table.

Audience: the Chief Accounting Officer, the Director of SOX and Automation, Revenue Accounting, Billing and Deal Desk. They care about the integrity of the numbers, controls and audit trail, and removing duplicated manual review. Never frame answers as forecasts.

---

## 2. TABLE CATALOG

### 2.1 `CUSTOMERS` (dimension, 140 rows)
85 pharma brands and 55 health systems. Key `CUSTOMER_ID` (CUST-0017) shared by all three systems. `CUSTOMER_TYPE` (Pharma / Health System), `SEGMENT`, `ACCOUNT_OWNER` (the sales rep), `SALES_POD`, `REGION`.

### 2.2 `PRODUCTS` (dimension, 8 rows)
Product catalogue; `PRODUCT_NAME` is identical across contracts, Salesforce products and NetSuite items. `PRODUCT_FAMILY` Pharma Marketing or Health System Talent; `REVENUE_RECOGNITION`.

### 2.3 `RECONCILIATION_CONTROLS` (dimension, 11 rows) — the rulebook
One row per three-way check: `CHECK_TYPE` (TCV_MISMATCH, PRODUCT_LINE_COUNT_MISMATCH, OPPORTUNITY_WITHOUT_CONTRACT_LINK, AMENDMENT_NOT_IN_SALESFORCE, TERM_END_DATE_MISMATCH, AMENDMENT_NOT_IN_NETSUITE, DUPLICATE_SALES_ORDERS, SALES_ORDER_WITHOUT_OPPORTUNITY, PAYMENT_TERMS_MISMATCH, BILLING_FREQUENCY_MISMATCH, MISSING_BILLING_MILESTONE), `FIELD_NAME`, `SYSTEMS_COMPARED`, `TOLERANCE`, `DEFAULT_SEVERITY`, `HIGH_SEVERITY_USD`, `OWNING_TEAM` (Sales Ops / Revenue Accounting / Billing), `SOX_CONTROL_REF` (OTC-xx), `DESCRIPTION`, `CORRECTIVE_SYSTEM`.

### 2.4 `CONTRACTS` (fact, 423 rows, grain = signed document)
Terms extracted from every signed PDF: ~270 originals (New / Renewal) and ~150 amendments. `CONTRACT_NUMBER` (MCN-2025-0142; amendments MCN-2025-0142-A2), `PARENT_CONTRACT_ID` (amendment → the ORIGINAL's `CONTRACT_ID`), `AMENDMENT_NUMBER` (0..n), `SIGNED_DATE`, `EFFECTIVE_DATE`, `END_DATE`, `TOTAL_CONTRACT_VALUE` (**restated full value**, not the increment), `PAYMENT_TERMS`, `BILLING_FREQUENCY`, `PRODUCT_SUMMARY`, `SPECIAL_TERMS`, `EXTRACTION_CONFIDENCE`, `PDF_FILE_NAME`.

### 2.5 `CONTRACT_LINE_ITEMS` (fact, ~1,000 rows, grain = Exhibit A line)
Product lines of each document; an amendment carries the FULL restated set. `SPECIALTY_TARGETED` for pharma campaigns. Sum of `LINE_AMOUNT` = document TCV.

### 2.6 `CONTRACT_BILLING_SCHEDULE` (fact, ~2,700 rows, grain = Exhibit B milestone)
Billing schedule of each document (full restated schedule on amendments). `MILESTONE_NUMBER`, `MILESTONE_DESCRIPTION`, `SCHEDULED_DATE`, `SCHEDULED_AMOUNT`. Sum = document TCV.

### 2.7 `SALESFORCE_OPPORTUNITIES` (fact, 419 rows, grain = opportunity)
Closed-won opportunities. `OPPORTUNITY_TYPE` New Business / Renewal / Amendment. `AMOUNT` is the **increment** for an amendment opportunity. `LINKED_CONTRACT_NUMBER` is the only link to the signed document and is sometimes NULL or wrong. `OWNER` = rep.

### 2.8 `SALESFORCE_OPPORTUNITY_PRODUCTS` (fact, ~740 rows)
Products on each opportunity. Sum of `TOTAL_PRICE` = opportunity amount.

### 2.9 `NETSUITE_SALES_ORDERS` (fact, 273 rows, grain = sales order)
One order per agreement unless Boomi duplicated it. `OPPORTUNITY_ID` (sometimes NULL), `ORDER_TOTAL`, `START_DATE`, `END_DATE` (service end for revenue), `PAYMENT_TERMS`, `BILLING_SCHEDULE_TYPE`, `STATUS`, `BOOMI_SYNC_TIMESTAMP` (last create/update by Boomi).

### 2.10 `NETSUITE_SALES_ORDER_LINES` (fact, ~650 rows)
Order lines; sum of `AMOUNT` = order total.

### 2.11 `NETSUITE_BILLING_SCHEDULE` (fact, ~1,700 rows, grain = scheduled bill)
What NetSuite will actually invoice: `BILL_DATE`, `BILL_AMOUNT`, `BILLED` (TRUE when bill_date <= 2026-09-30), `INVOICE_NUMBER`.

### 2.12 `DATA_DICTIONARY` (metadata, 39 rows)
Column and metric definitions with business owner and source system.

---

## 3. HELPER VIEWS (join helpers only — no status column anywhere)

### `V_CONTRACT_CHAIN`
One row per **agreement** (chain = original + amendments). `CHAIN_ID` (the original's contract_id), `CONTRACT_NUMBER`, customer and owner columns, `AMENDMENT_COUNT`, `LATEST_VERSION`, `LATEST_CONTRACT_NUMBER`, `LATEST_SIGNED_DATE`, and the **current terms** from the latest document: `CURRENT_TCV`, `CURRENT_END_DATE`, `CURRENT_PAYMENT_TERMS`, `CURRENT_BILLING_FREQUENCY`, `CURRENT_PRODUCT_COUNT`, `CURRENT_MILESTONE_COUNT`, plus `ORIGINAL_TCV`, `ORIGINAL_END_DATE`, `IS_ACTIVE_TODAY`. The grain for every reconciliation question.

### `V_AMENDMENT_LINEAGE`
One row per document in each chain: `VERSION`, `DOCUMENT_NUMBER`, `SIGNED_DATE`, `TCV`, `TCV_CHANGE`, `END_DATE`, `END_DATE_CHANGE_DAYS`, payment terms and billing frequency before/after, `PRODUCT_SUMMARY`, `SPECIAL_TERMS`, `PDF_FILE_NAME`, `IS_LATEST_VERSION`. Neutral lineage; it does not say which system reflects a version.

### `V_DEAL_CROSSWALK`
Row-level map chain → opportunity → sales order with broken links kept as NULLs and orphan opportunities with NULL chain columns (`LINK_KIND`). `SO_LINK_METHOD` says whether the order was linked by opportunity id or by customer and start date. Grain chain x opportunity x order: COUNT(DISTINCT ...).

### `V_CHAIN_SYSTEM_SUMMARY`
One row per chain with the three systems side by side: contract current values; Salesforce `SF_OPPORTUNITY_COUNT`, `SF_AMOUNT` (sum of opportunities), `SF_END_DATE`, `SF_PRODUCT_COUNT`, `SF_VERSION_REFLECTED`; NetSuite `NS_SALES_ORDER_COUNT`, `NS_AMOUNT`, `NS_END_DATE`, `NS_PAYMENT_TERMS`, `NS_BILLING_SCHEDULE_TYPE`, `NS_LAST_SYNC`, `NS_VERSION_REFLECTED` (highest amendment signed on or before the last Boomi sync), `NS_BILL_COUNT`, `NS_BILL_TOTAL`, `NS_BILLED_TO_DATE`. Nothing is compared here.

---

## 4. ENTITY RELATIONSHIP MAP

- `CUSTOMERS` 1—n `CONTRACTS` (customer_id); `CONTRACTS` 1—n `CONTRACT_LINE_ITEMS`, `CONTRACT_BILLING_SCHEDULE` (contract_id); `CONTRACTS.parent_contract_id` → `CONTRACTS.contract_id` (amendment → original).
- `CUSTOMERS` 1—n `SALESFORCE_OPPORTUNITIES` (customer_id); `SALESFORCE_OPPORTUNITIES` 1—n `SALESFORCE_OPPORTUNITY_PRODUCTS`; `SALESFORCE_OPPORTUNITIES.linked_contract_number` → `CONTRACTS.contract_number` (soft link, same customer).
- `CUSTOMERS` 1—n `NETSUITE_SALES_ORDERS`; `NETSUITE_SALES_ORDERS.opportunity_id` → `SALESFORCE_OPPORTUNITIES` (nullable); `NETSUITE_SALES_ORDERS` 1—n `NETSUITE_SALES_ORDER_LINES`, `NETSUITE_BILLING_SCHEDULE`.
- `PRODUCTS.product_name` = `CONTRACT_LINE_ITEMS.product_name` = `SALESFORCE_OPPORTUNITY_PRODUCTS.product_name` = `NETSUITE_SALES_ORDER_LINES.item_name`.
- Findings join `RECONCILIATION_CONTROLS` on `CHECK_TYPE`.

---

## 5. METRICS DICTIONARY

- **Contract value (TCV)** = `V_CONTRACT_CHAIN.CURRENT_TCV` (latest document). Never SUM `CONTRACTS.TOTAL_CONTRACT_VALUE` across a chain.
- **Salesforce value** = `V_CHAIN_SYSTEM_SUMMARY.SF_AMOUNT` (sum of the chain's opportunity amounts).
- **NetSuite value** = `V_CHAIN_SYSTEM_SUMMARY.NS_AMOUNT` (sum of the chain's order totals).
- **Finding** = one failed check on one agreement (per milestone / opportunity / order for row-level checks).
- **Variance (USD)** per finding: TCV_MISMATCH = Salesforce − contract; AMENDMENT_NOT_IN_NETSUITE = contract − NetSuite; DUPLICATE_SALES_ORDERS = orders − contract (floor 0); MISSING_BILLING_MILESTONE = milestone amount; OPPORTUNITY_WITHOUT_CONTRACT_LINK = opportunity amount; others 0.
- **Exposure** = SUM(ABS(variance)) over open findings; an agreement contributes once per check. A review-priority measure, not an accounting adjustment.
- **Mismatch rate** = agreements with ≥ 1 finding / agreements checked.
- **Severity** = control default, escalated to High when ABS(variance) ≥ `HIGH_SEVERITY_USD`.
- **Team share** = finding units (agreement x check) per owning team / all units.

---

## 6. SYNONYMS MASTER LIST

- agreement = contract = deal = chain = contract chain = MSA = closed-won deal
- document = version = signed document = envelope; amendment = change order = addendum = A1/A2/A3
- current terms = latest version = as signed = latest amendment
- TCV = total contract value = contract value = deal value
- bookings = Salesforce amount = Salesforce value = booked amount = opportunity amount
- NetSuite value = order total = ordered amount; sales order = SO = order
- service end = NetSuite end date = revenue end date
- billing frequency = billing schedule type = billing cadence; milestone = scheduled bill = instalment = Exhibit B line
- payment terms = net terms = terms
- finding = discrepancy = mismatch = exception = break = issue
- exposure = dollar exposure = open exposure = dollars at risk = unreconciled dollars
- stale = behind = not reflected = not updated = lagging = out of date
- owning team = responsible team; Sales Ops = Deal Desk (Sales Ops reviews; Deal Desk extracts)
- rep = account owner = AE = owner = salesperson
- pharma = pharma brand = brand; health system = hospital = provider
- Boomi sync = integration run = last sync; duplicate order = dup SO = second order
- SOX control = control ref = OTC control = key control
- three-way match = three-way reconciliation = contract recon = the recon = reconciliation

---

## 7. DOMAIN KNOWLEDGE

- The demo as-of date is 2026-09-30, the last day of Q3 2026. "Today", "now", "this quarter" and "the close" refer to that date and to Q3 2026 (2026-07-01 to 2026-09-30). Meridian's fiscal year is the calendar year.
- An agreement is one original signed document plus all its amendments, identified by the original contract number. An amendment document restates the entire agreement, so the latest document carries the current terms. `V_CONTRACT_CHAIN` has one row per agreement.
- In Salesforce an amendment is its own opportunity booked for the increment; the Salesforce value of an agreement is the sum of its opportunities. In NetSuite there should be one order per agreement that Boomi restates on amendments; `BOOMI_SYNC_TIMESTAMP` earlier than an amendment's signature means the amendment is not reflected.
- The three-way match at the 2026-09-30 close: about 52 of 270 agreements (roughly 19 percent) fail at least one of the eleven checks, with about 31 million dollars of exposure and about 90 High severity findings. Missing billing milestones carry most of the exposure dollars. Amended agreements fail far more often (about 43 percent) than unamended ones (about 4 percent).
- Halvorsen Therapeutics (CUST-0017, owner Dana Whitfield) is the compound case: MSA MCN-2025-0142 signed 2025-02-10 for 1.8M; A1 2025-06-16 adds Sponsored Content (2.25M); A2 2025-11-03 extends the term to 2027-02-28 and converts billing to milestones (2.85M); A3 2026-07-20 reduces the campaign unit price and moves to Net 45 (2.73M). Salesforce reflects A2 only (2.85M booked). NetSuite reflects A1 only: orders SO-10017 and SO-10018 totalling 2.25M, end date 2026-08-31, quarterly, Net 30, last Boomi sync 2025-06-18. Exposure about 480k against NetSuite plus a 120k Salesforce overstatement plus four milestones NetSuite will never bill.
- Dana Whitfield (Pharma East) has the highest account-owner mismatch rate (about 40 percent of her agreements, roughly twice the overall rate): rounded opportunity amounts and omitted line items.
- The Boomi upgrade of 2026-03-01 (bulletin BOOMI-2026-03) broke amendment propagation: amendments skipped or duplicated as a second order, and service end dates not restated. The permanent fix is scheduled for 2026-10-20; the reconciliation is the control until then.
- Owning teams per the control matrix: Sales Ops (TCV_MISMATCH, PRODUCT_LINE_COUNT_MISMATCH, OPPORTUNITY_WITHOUT_CONTRACT_LINK, AMENDMENT_NOT_IN_SALESFORCE); Revenue Accounting (TERM_END_DATE_MISMATCH, AMENDMENT_NOT_IN_NETSUITE, DUPLICATE_SALES_ORDERS, SALES_ORDER_WITHOUT_OPPORTUNITY); Billing (PAYMENT_TERMS_MISMATCH, BILLING_FREQUENCY_MISMATCH, MISSING_BILLING_MILESTONE).

---

## 8. BUSINESS NUANCES

- "Which deals do not reconcile" means: run all eleven checks (the certified query "Which closed won deals do not reconcile across all three systems?") and list agreements with at least one finding. Always carry owning team and SOX control on findings.
- Exposure is a review-priority number, not money lost. Say so when asked whether it is a loss.
- A missing milestone is counted per milestone in the queue; team shares and mismatch rates count per agreement x check. Both are correct; say which one you used.
- TCV_MISMATCH already carries the dollar effect of an amendment missing from Salesforce; AMENDMENT_NOT_IN_SALESFORCE is reported with zero variance to avoid double counting. AMENDMENT_NOT_IN_NETSUITE carries the contract-minus-NetSuite dollars.
- A chain with no linked opportunity (blank or wrong contract number) shows Salesforce value 0 and fails TCV_MISMATCH; the orphan opportunity itself appears under OPPORTUNITY_WITHOUT_CONTRACT_LINK. The crosswalk still finds the NetSuite order by customer and start date.
- "This quarter" exposure = exposure on findings as of 2026-09-30; "exposure on Q3 signings" restricts to agreements whose latest document was signed in Q3 2026.
- "Trend" questions: there is no run history. Trend the mismatch rate by the month the latest document was signed and show the amended share.
- Severity High on amendment-not-reflected and duplicate orders regardless of dollars; TCV and milestone findings escalate to High at 100,000 USD.
- Decisions (Confirmed / Rejected / Needs follow-up) are recorded in the review workflow, not in the warehouse.

---

## 9. TRIBAL KNOWLEDGE

- Never SUM `CONTRACTS.TOTAL_CONTRACT_VALUE` or `CONTRACT_BILLING_SCHEDULE.SCHEDULED_AMOUNT` across versions of one chain; take the latest document (`V_CONTRACT_CHAIN.LATEST_CONTRACT_ID`).
- Always add the customer condition when joining opportunities to contracts by number; a wrong `LINKED_CONTRACT_NUMBER` otherwise joins to another customer's agreement.
- `V_DEAL_CROSSWALK` can repeat a sales order across opportunity rows; aggregate with DISTINCT or use `V_CHAIN_SYSTEM_SUMMARY`.
- Milestones that pre-date an amendment are carried forward unchanged into the restated Exhibit B, so only the restated part of a schedule goes missing in NetSuite.
- `BOOMI_SYNC_TIMESTAMP` and `EXTRACTED_AT` are timestamps; cast to DATE before comparing with signed dates.
- `IS_ACTIVE_TODAY` and `BILLED` are anchored to 2026-09-30.
- Product names match exactly across the three systems; join on name when comparing products.

---

## 10. QUERY ROUTING HINTS

- Which deals do not reconcile / all findings / exposure / by team / by owner / by customer type → the certified check queries over `V_CHAIN_SYSTEM_SUMMARY`, `V_CONTRACT_CHAIN`, `V_DEAL_CROSSWALK` and the raw tables, joined to `RECONCILIATION_CONTROLS` on CHECK_TYPE. Reuse the reviewed query SQL for each check.
- Current terms of an agreement, amendments count, active today → `V_CONTRACT_CHAIN`.
- Lineage / history of an agreement, what each amendment changed → `V_AMENDMENT_LINEAGE`; where each system stands → join `V_CHAIN_SYSTEM_SUMMARY` (SF_VERSION_REFLECTED, NS_VERSION_REFLECTED).
- Contract vs Salesforce vs NetSuite values side by side → `V_CHAIN_SYSTEM_SUMMARY`.
- Which opportunity / which order belongs to an agreement, broken links → `V_DEAL_CROSSWALK`.
- Missing milestones → latest document's `CONTRACT_BILLING_SCHEDULE` vs `NETSUITE_BILLING_SCHEDULE` on the chain's orders, 7 days and 1 USD tolerance.
- What a check means, who owns it, the SOX control → `RECONCILIATION_CONTROLS`.
- Recent signings (agent) → `V_CHAIN_SYSTEM_SUMMARY.LATEST_SIGNED_DATE >= 2026-09-23` then the checks.
- Any "today" / "this quarter" → 2026-09-30 / Q3 2026.
