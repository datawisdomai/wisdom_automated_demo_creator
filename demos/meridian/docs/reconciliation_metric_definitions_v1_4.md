# Reconciliation Metric Definitions Standard v1.4

Owner: Revenue Accounting (Controller's office)
Approved by: Chief Accounting Officer
Effective: 2026-09-01
Applies to: MERIDIAN_POC.ANALYTICS and any report or answer that cites a reconciliation figure
Supersedes: v1.3 (2026-03-15)

## 1. Purpose

This standard defines the terms used in the three-way contract reconciliation between the signed agreement (DocuSign), the closed-won opportunity (Salesforce) and the sales order (NetSuite). Every figure reported to the CAO, to the audit committee or to the external auditors must use these definitions. Where a system shows a different number the definition in this standard prevails and the system is corrected.

## 2. Grain

- **Agreement (contract chain).** One original signed document plus all of its signed amendments. Identified by the original contract number (MCN-2025-0142). The agreement is the unit of reconciliation: one agreement = one closed deal. In the warehouse `V_CONTRACT_CHAIN` has one row per agreement.
- **Document (version).** One signed PDF: the original (version 0) or an amendment (version 1..n). Amendment documents carry the suffix -A1 -A2 and so on. In the warehouse each document is one row of `CONTRACTS`.
- **Current terms.** The terms of the latest signed document of an agreement. An amendment restates the entire agreement (value, dates, payment terms, billing frequency, Exhibit A products and Exhibit B billing schedule) so the latest document is always the complete current truth.

## 3. System values

| Term | Definition | Warehouse column |
|---|---|---|
| Contract value (TCV) | Total contract value stated in the latest signed document | `V_CONTRACT_CHAIN.CURRENT_TCV` |
| Salesforce value | Sum of the closed-won opportunity amounts linked to any document of the agreement. The original opportunity carries the original value; an amendment opportunity carries the increment (positive or negative). | `V_CHAIN_SYSTEM_SUMMARY.SF_AMOUNT` |
| NetSuite value | Sum of the order totals of the sales orders linked to the agreement | `V_CHAIN_SYSTEM_SUMMARY.NS_AMOUNT` |
| Version reflected in Salesforce | Highest amendment number referenced by any opportunity of the agreement | `SF_VERSION_REFLECTED` |
| Version reflected in NetSuite | Highest amendment number signed on or before the last Boomi sync of the agreement's sales orders | `NS_VERSION_REFLECTED` |

An agreement is linked to its opportunities through the opportunity's linked contract number (any version of the agreement, same customer) and to its sales orders through the opportunity id Boomi wrote on the order, or, when that id is blank or the agreement has no linked opportunity, by customer and service start date. `V_DEAL_CROSSWALK` holds the row-level map including the broken links.

## 4. The eleven checks

Each check compares one field of the current terms with one or two systems and produces a finding when the difference exceeds the tolerance. The rulebook is the `RECONCILIATION_CONTROLS` table; this section states the business meaning.

| Check | Compares | Tolerance | Finding when |
|---|---|---|---|
| TCV_MISMATCH | Contract value vs Salesforce value | 100 USD | the two differ by more than 100 USD (including when no opportunity is linked) |
| PRODUCT_LINE_COUNT_MISMATCH | Distinct products in Exhibit A vs distinct products across the agreement's opportunities | exact | counts differ |
| OPPORTUNITY_WITHOUT_CONTRACT_LINK | Opportunity's linked contract number vs signed documents of the same customer | exact | the number is blank or resolves to another customer's agreement |
| AMENDMENT_NOT_IN_SALESFORCE | Latest amendment number vs version reflected in Salesforce | exact | Salesforce is behind |
| TERM_END_DATE_MISMATCH | Contract end date vs NetSuite service end date | exact | dates differ |
| AMENDMENT_NOT_IN_NETSUITE | Latest amendment number vs version reflected in NetSuite | exact | NetSuite is behind (last Boomi sync precedes the amendment signature) |
| DUPLICATE_SALES_ORDERS | Number of sales orders per agreement | one | more than one |
| SALES_ORDER_WITHOUT_OPPORTUNITY | Sales order opportunity id | present | blank |
| PAYMENT_TERMS_MISMATCH | Contract payment terms vs NetSuite payment terms | exact | differ |
| BILLING_FREQUENCY_MISMATCH | Contract billing frequency vs NetSuite billing schedule type | exact | differ |
| MISSING_BILLING_MILESTONE | Each Exhibit B milestone of the latest document vs NetSuite bills on the agreement's orders | 7 days and 1 USD | no bill for the same amount within 7 days of the scheduled date |

## 5. Severity

Each check has a default severity in the rulebook. A finding escalates to **High** when its absolute dollar variance is at or above the check's high-severity threshold (100,000 USD for TCV_MISMATCH, AMENDMENT_NOT_IN_NETSUITE, DUPLICATE_SALES_ORDERS and MISSING_BILLING_MILESTONE). Checks with no dollar variance keep their default severity.

## 6. Dollar variance and exposure

- **Variance** per finding: TCV_MISMATCH = Salesforce value minus contract value; AMENDMENT_NOT_IN_NETSUITE = contract value minus NetSuite value; DUPLICATE_SALES_ORDERS = the amount by which the orders exceed the contract value (never negative); MISSING_BILLING_MILESTONE = the scheduled amount of the milestone; OPPORTUNITY_WITHOUT_CONTRACT_LINK = the opportunity amount. Every other check carries a variance of zero.
- **Exposure (open exposure, dollar exposure)** = the sum of the absolute variance across open findings. An agreement contributes once per check it fails. Exposure is a review-priority measure, not an accounting adjustment: it tells the reviewer how many dollars are affected by findings that have not yet been dispositioned.
- **Exposure this quarter** = exposure on findings as of the quarter-end as-of date. Where a narrower figure is needed, "exposure on Q3 signings" restricts to agreements whose latest document was signed in the quarter.

## 7. Rates and shares

- **Mismatch rate** = agreements with at least one finding / agreements checked.
- **Amended mismatch rate** = the same ratio restricted to agreements with at least one amendment; **unamended mismatch rate** likewise.
- **Team share** = findings owned by a team / all findings. A finding unit is one agreement x one check (milestone findings are counted per milestone in the queue but per agreement x check for team shares).
- **Account owner mismatch rate** = agreements with findings owned by the rep / agreements owned by the rep.

## 8. Ownership

| Owning team | Checks | SOX control |
|---|---|---|
| Sales Ops | TCV_MISMATCH, PRODUCT_LINE_COUNT_MISMATCH, OPPORTUNITY_WITHOUT_CONTRACT_LINK, AMENDMENT_NOT_IN_SALESFORCE | OTC-02, OTC-04, OTC-07 |
| Revenue Accounting | TERM_END_DATE_MISMATCH, AMENDMENT_NOT_IN_NETSUITE, DUPLICATE_SALES_ORDERS, SALES_ORDER_WITHOUT_OPPORTUNITY | OTC-02, OTC-05, OTC-07, OTC-09 |
| Billing | PAYMENT_TERMS_MISMATCH, BILLING_FREQUENCY_MISMATCH, MISSING_BILLING_MILESTONE | OTC-11, OTC-12 |

## 9. As-of date and periods

The reconciliation is run at quarter end. For the current cycle the as-of date is 2026-09-30 (last day of Q3 2026). "This quarter" means Q3 2026 (2026-07-01 to 2026-09-30). Dates in the warehouse are calendar dates; Meridian's fiscal year is the calendar year.

## 10. Change log

- v1.4 (2026-09-01): added AMENDMENT_NOT_IN_SALESFORCE and SALES_ORDER_WITHOUT_OPPORTUNITY; defined exposure per check; milestone tolerance set to 7 days.
- v1.3 (2026-03-15): severity escalation thresholds; owning team per check.
- v1.2 (2025-11-01): first version used for the Q3 2025 close.
