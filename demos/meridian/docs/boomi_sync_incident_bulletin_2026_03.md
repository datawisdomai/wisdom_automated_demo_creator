# Boomi Sync Incident Bulletin: Salesforce to NetSuite amendment propagation

Letterhead: Meridian Clinician Network, Inc. — IT Integrations
Bulletin: BOOMI-2026-03
Date: 2026-03-27
Severity: Major (financial data)
Status: Mitigated; permanent fix scheduled
Distribution: Revenue Accounting, Billing, Sales Ops, SOX and Automation

## What happened

On 2026-03-01 the Salesforce to NetSuite integration (Boomi process "SFDC Opportunity to NS Sales Order v4") was upgraded to the new NetSuite REST connector. Two defects were introduced:

1. **Amendment opportunities not matched to the existing sales order.** When an opportunity of type Amendment closes, the process is supposed to look up the sales order created from the original opportunity (by customer and linked contract number) and restate it: order total, lines, service end date and billing schedule. After the upgrade the lookup failed intermittently when the linked contract number carried an amendment suffix (-A1, -A2). The process then either skipped the record (the amendment never reached NetSuite) or, when the duplicate-prevention flag was off, created a **second sales order** for the increment.
2. **Service end date not restated.** Even when the lookup succeeded, the end date field was mapped from the original opportunity rather than the amendment opportunity, so term extensions did not update NetSuite's service end. Billing schedule type and payment terms were likewise left unchanged.

The behaviour existed in a milder form before the upgrade: since mid-2025 a known race condition occasionally created a second order when an amendment closed within days of a scheduled sync (the Halvorsen Therapeutics A1 case of June 2025 is the reference example).

## Impact

- Amendments signed between 2025-06-01 and 2026-03-27 may not be reflected in NetSuite, or may be reflected as a duplicate order. Revenue Accounting identified eleven affected agreements at the Q2 2026 close.
- Term extensions in that window may show the original end date in NetSuite (revenue schedule too short).
- Billing schedules on affected orders do not match Exhibit B of the amended agreement.

## Detection

An amendment is not reflected in NetSuite when the sales order's last Boomi sync timestamp is earlier than the amendment's signature date. Duplicate orders are visible as more than one sales order per agreement. Both conditions are part of the quarterly three-way reconciliation (checks AMENDMENT_NOT_IN_NETSUITE and DUPLICATE_SALES_ORDERS under control OTC-07 and OTC-05).

## Interim procedure (in force)

1. Revenue Accounting raises a ticket per affected agreement referencing the control.
2. IT Integrations re-runs the amendment through the corrected mapping in a controlled batch every Thursday.
3. Billing re-generates the billing schedule from the amended Exhibit B once the order is restated.
4. Duplicate orders are closed, never deleted, and the surviving order is restated.

## Permanent fix

Process v5 (lookup by chain contract number without suffix; end date, payment terms and billing schedule mapped from the amendment opportunity; duplicate prevention mandatory) is in user acceptance testing with a target release of 2026-10-20. Until then the reconciliation remains the control.

Contact: IT Integrations on-call, or #close-reconciliation for finance questions.
