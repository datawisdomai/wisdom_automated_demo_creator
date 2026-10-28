# Q2 2026 Close Memo: Contract Reconciliation Findings

Letterhead: Meridian Clinician Network, Inc. — Revenue Accounting
To: Chief Accounting Officer; Director of SOX and Automation; Controller
From: Revenue Accounting Manager
Date: 2026-07-14
Reference: CLOSE-2026Q2-RECON-04
Classification: Internal

## 1. Summary

The Q2 2026 contract reconciliation was completed on 2026-07-11, nine business days after quarter end. Three teams performed their own slice of the work: Sales Ops compared Salesforce bookings with signed agreements, Revenue Accounting compared revenue terms across Salesforce, NetSuite and the agreements, and Billing compared NetSuite billing schedules with Exhibit B of the agreements. Each team worked from its own extract (two spreadsheets and one Alteryx workflow). The combined effort was approximately 190 person-hours. Nineteen agreements were reviewed by more than one team.

Findings: 46 agreements (17.2 percent of the 268 agreements in scope) failed at least one check. Exposure as defined in the Reconciliation Metric Definitions Standard was 24.1 million USD, of which 15.6 million relates to contract billing milestones with no matching NetSuite bill. Amendments drive the result: 39 of the 46 agreements had at least one amendment.

## 2. Findings by owning team

| Owning team | Agreements | Finding units | Exposure (USD) | High severity |
|---|---|---|---|---|
| Sales Ops | 21 | 24 | 2.9M | 9 |
| Revenue Accounting | 18 | 22 | 5.6M | 14 |
| Billing | 22 | 31 | 15.6M | 38 |

## 3. Root causes

- **Boomi does not carry amendments reliably.** Eleven agreements had sales orders whose last Boomi sync preceded the latest amendment signature. The March 2026 Boomi upgrade (see bulletin BOOMI-2026-03) made this worse: before the upgrade Boomi restated the order but not the end date; after it, several amendments did not arrive at all.
- **Amendment opportunities are not always booked.** Four amendments existed in DocuSign only. Sales Ops attributes this to amendments negotiated by Deal Desk without a Salesforce opportunity being opened.
- **Rep entry habits.** One account owner accounts for a disproportionate share of TCV and product-count mismatches (amounts rounded to the nearest 25,000; one product line omitted). A coaching plan is in place.
- **Duplicate sales orders.** In three agreements Boomi created a second order from an amendment opportunity instead of updating the first.
- **Billing schedules.** Milestone-billed agreements whose NetSuite order was set up with a quarterly schedule, and schedules truncated by one or two bills, produced most missing milestones.

## 4. Control implications

The findings evidence exceptions under OTC-04 (order entry accuracy), OTC-05 (sales order uniqueness), OTC-07 (amendment processing), OTC-09 (revenue schedule accuracy), OTC-11 (billing terms accuracy) and OTC-12 (billing schedule completeness). None rose to a deficiency because every exception was identified and corrected before revenue was recognised; however the reliance on three manual processes is itself the risk the external auditors flagged in the FY2025 management letter.

## 5. Recommendation

Replace the three team reconciliations with one automated three-way match run against the warehouse replicas, using the control matrix as the single rulebook, with every finding carrying its owning team and SOX control reference. Reviewers disposition findings in one queue; nobody re-reviews another team's work. Target for Q3 2026: the match runs on the as-of date and the review is complete within three business days.

## 6. Example: Halvorsen Therapeutics (MCN-2025-0142)

The compound case. The original agreement (1.8 million, quarterly, Net 30, ending 2026-08-31) was amended three times: A1 added Sponsored Content (2.25 million), A2 extended the term to 2027-02-28 and converted billing to milestones (2.85 million), A3 reduced the campaign unit price and moved to Net 45 (2.73 million). Salesforce stops at A2. NetSuite stops at A1 and holds two sales orders because Boomi created a second order for the A1 increment. Every revenue and billing figure for this customer is wrong in at least one system. It is used in this memo because it exercises eight of the eleven checks.

Prepared by Revenue Accounting. Questions to #close-reconciliation.
