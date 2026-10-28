# Order-to-Cash Reconciliation Policy and Control Matrix

Letterhead: Meridian Clinician Network, Inc. — Internal Controls
Policy owner: Director of SOX and Automation
Approved by: Chief Accounting Officer
Version: 2026.3
Effective: 2026-09-01
Review cycle: Quarterly

## 1. Policy statement

Every customer agreement signed in DocuSign must be reflected accurately and completely in Salesforce (the commercial record) and in NetSuite (the financial record). Management performs a three-way reconciliation of the signed agreement, the closed-won opportunity and the sales order at each quarter end, and on every new signature during the quarter, using the checks in this matrix. Findings are reviewed by the owning team, dispositioned, and corrected in the system named in the matrix. The reconciliation is the evidence for the order-to-cash controls listed below.

## 2. Scope

All agreements with pharma brands and health systems: original agreements, renewals and amendments. The unit of reconciliation is the agreement (the original document plus its amendments). The current terms are those of the latest signed document.

## 3. Roles

- **Sales Ops** owns the commercial record: opportunity amounts, products and the link from opportunity to signed document.
- **Revenue Accounting** owns the financial record: sales order existence, uniqueness, service dates and the propagation of amendments into NetSuite.
- **Billing** owns the billing record: payment terms, billing schedule type and the completeness of scheduled bills against Exhibit B.
- **Deal Desk** owns the extraction of terms from signed documents and the resolution of low-confidence extractions.
- **SOX and Automation** owns this matrix, the tolerances and the evidence retention.

## 4. Control matrix

| Control | Check (rulebook id) | Objective | Systems | Tolerance | Severity rule | Owning team | Corrective system |
|---|---|---|---|---|---|---|---|
| OTC-02 Completeness of contract linkage | OPPORTUNITY_WITHOUT_CONTRACT_LINK (RC-03) | Every closed-won opportunity traces to a signed document of the same customer | Salesforce vs Contract | exact | Medium | Sales Ops | Salesforce |
| OTC-02 Completeness of contract linkage | SALES_ORDER_WITHOUT_OPPORTUNITY (RC-08) | Every sales order carries the opportunity it was created from | NetSuite vs Salesforce | exact | Medium | Revenue Accounting | NetSuite |
| OTC-04 Order entry accuracy | TCV_MISMATCH (RC-01) | Bookings equal the contract value | Contract vs Salesforce | 100 USD | Medium; High at 100,000 USD variance | Sales Ops | Salesforce |
| OTC-04 Order entry accuracy | PRODUCT_LINE_COUNT_MISMATCH (RC-02) | Products booked equal Exhibit A | Contract vs Salesforce | exact | Medium | Sales Ops | Salesforce |
| OTC-05 Sales order uniqueness | DUPLICATE_SALES_ORDERS (RC-07) | One sales order per agreement | NetSuite vs Contract | one order | High; dollars = over-booked amount | Revenue Accounting | NetSuite |
| OTC-07 Amendment processing | AMENDMENT_NOT_IN_SALESFORCE (RC-04) | Every amendment is booked | Contract vs Salesforce | exact | High | Sales Ops | Salesforce |
| OTC-07 Amendment processing | AMENDMENT_NOT_IN_NETSUITE (RC-06) | Every amendment reaches the sales order | Contract vs NetSuite | exact | High; dollars = contract minus NetSuite | Revenue Accounting | NetSuite |
| OTC-09 Revenue schedule accuracy | TERM_END_DATE_MISMATCH (RC-05) | Service end equals the contract end date | Contract vs NetSuite | exact | High | Revenue Accounting | NetSuite |
| OTC-11 Billing terms accuracy | PAYMENT_TERMS_MISMATCH (RC-09) | Payment terms equal the contract | Contract vs NetSuite | exact | Medium | Billing | NetSuite |
| OTC-11 Billing terms accuracy | BILLING_FREQUENCY_MISMATCH (RC-10) | Billing schedule type equals the contract billing frequency | Contract vs NetSuite | exact | Medium | Billing | NetSuite |
| OTC-12 Billing schedule completeness | MISSING_BILLING_MILESTONE (RC-11) | Every Exhibit B milestone has a NetSuite bill | Contract vs NetSuite | 7 days and 1 USD | Medium; High at 100,000 USD | Billing | NetSuite |

## 5. Review and disposition

1. The reconciliation produces one finding per failed check per agreement (per milestone, opportunity or order for the row-level checks). Each finding carries the three system values, the dollar variance, the severity, the owning team, the control reference and a plain-language reason.
2. The owning team reviews each finding against the evidence (the signed document, the opportunity, the sales order and billing schedule) and records a decision: **Confirmed** (a real exception; names the system to correct), **Rejected** (a false positive; the reason is recorded) or **Needs follow-up** (evidence outstanding; an owner and date are set).
3. High severity findings are dispositioned within three business days of the as-of date; all others within ten.
4. Decisions, notes and the reviewer are retained with the finding as audit evidence. A finding is closed when the correcting system shows the agreed value in the next reconciliation run.
5. No team re-reviews another team's findings. Disagreements escalate to the Controller.

## 6. Evidence retention

The reconciliation output (findings with decisions) is retained for seven years. The signed documents remain in the contract archive; the extracted terms, the Salesforce and NetSuite replicas and the rulebook are retained in the warehouse with their load dates.

## 7. Amendment handling (the known weak point)

Amendments are the main source of exceptions. The matrix therefore treats "amendment not reflected" in either system as High severity regardless of dollars. Boomi's propagation of amendments is monitored by IT Integrations; see bulletin BOOMI-2026-03 for the March 2026 incident and the interim manual re-sync procedure.
