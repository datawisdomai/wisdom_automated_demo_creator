# Data Platform wiki: MERIDIAN_POC onboarding notes

Space: Finance Data Platform
Page owner: Analytics Engineering (order-to-cash)
Last edited: 2026-09-18 by the data engineering team
Audience: anyone writing SQL or asking questions against MERIDIAN_POC.ANALYTICS

## What this database is

MERIDIAN_POC.ANALYTICS holds the three replicas the contract reconciliation needs, side by side and on the same customer key:

- **DocuSign extraction** (CONTRACTS, CONTRACT_LINE_ITEMS, CONTRACT_BILLING_SCHEDULE): the terms pulled from every signed PDF. The legal truth.
- **Salesforce replica** (SALESFORCE_OPPORTUNITIES, SALESFORCE_OPPORTUNITY_PRODUCTS): closed-won opportunities as the reps entered them. Refreshed nightly.
- **NetSuite replica** (NETSUITE_SALES_ORDERS, NETSUITE_SALES_ORDER_LINES, NETSUITE_BILLING_SCHEDULE): sales orders Boomi created from Salesforce, with the billing schedules NetSuite will actually invoice. Refreshed nightly.
- **Rulebook** (RECONCILIATION_CONTROLS): one row per three-way check. Join findings to it on check_type.
- **Dimensions** (CUSTOMERS, PRODUCTS) and DATA_DICTIONARY.

Nothing in here is a result table. The checks are queries. If you want "the findings", run the certified query library (the eleven check queries and the roll-ups) or the Wisdom domain that wraps them.

## The one thing to understand: chains and versions

A deal is an **agreement** (we also say chain). The original document is version 0; each amendment is version 1, 2, 3 and is its own row in CONTRACTS with parent_contract_id pointing at the ORIGINAL (not at the previous amendment) and amendment_number = n. Contract numbers carry the version as a suffix: MCN-2025-0142, MCN-2025-0142-A1, MCN-2025-0142-A2.

**An amendment row restates the whole agreement.** total_contract_value on an amendment is the full value after the amendment, end_date is the restated end, and the amendment carries the complete Exhibit A (CONTRACT_LINE_ITEMS) and Exhibit B (CONTRACT_BILLING_SCHEDULE). So "current terms" = the latest version, nothing to add up. Use V_CONTRACT_CHAIN; do not sum TOTAL_CONTRACT_VALUE across versions.

**Salesforce is the opposite.** The original opportunity carries the original value; an amendment opportunity carries only the increment (can be negative). So the Salesforce value of a chain is SUM(amount) over its opportunities. V_CHAIN_SYSTEM_SUMMARY.SF_AMOUNT does that for you.

**NetSuite is one order per chain** that Boomi is supposed to restate when an amendment arrives (order_total, end_date, lines, billing schedule). When Boomi misses the amendment the order simply stays on the old terms: boomi_sync_timestamp earlier than the amendment's signed_date is the tell. Sometimes Boomi creates a second order from the amendment opportunity instead of updating the first; that is a duplicate.

## Join paths

| From | To | How |
|---|---|---|
| CONTRACTS (any version) | its chain | COALESCE(parent_contract_id, contract_id) = chain_id |
| chain | SALESFORCE_OPPORTUNITIES | SPLIT_PART(linked_contract_number, '-A', 1) = chain contract_number AND same customer_id (V_DEAL_CROSSWALK does this) |
| SALESFORCE_OPPORTUNITIES | NETSUITE_SALES_ORDERS | sales order opportunity_id = opportunity_id; when it is blank, or the chain has no linked opportunity, fall back to customer_id + start_date = chain effective_date |
| NETSUITE_SALES_ORDERS | NETSUITE_BILLING_SCHEDULE | sales_order_id |
| CONTRACT_BILLING_SCHEDULE (latest version) | NETSUITE_BILLING_SCHEDULE | no key: match on the chain, bill_date within 7 days of scheduled_date, bill_amount within 1 USD |
| anything | RECONCILIATION_CONTROLS | check_type |

The helper views encode all of this:

- **V_CONTRACT_CHAIN** one row per chain, current terms from the latest version plus original values and amendment_count. Start here for anything per agreement.
- **V_AMENDMENT_LINEAGE** one row per version with tcv_change and end_date_change_days versus the previous version. Use it to tell the story of an agreement. It does not say which system reflects a version.
- **V_DEAL_CROSSWALK** row-level chain -> opportunity -> sales order map. Grain is chain x opportunity x order, so COUNT(DISTINCT ...). Orphan opportunities (no agreement) appear with NULL chain columns and link_kind = orphan_opportunity.
- **V_CHAIN_SYSTEM_SUMMARY** one row per chain with contract, Salesforce and NetSuite values side by side (sf_amount, ns_amount, sf_version_reflected, ns_version_reflected, ns_end_date, ns_payment_terms, ns_billing_schedule_type, ns_sales_order_count, ns_last_sync). Nothing is compared in the view; comparing is what the check queries do.

## Gotchas we have all hit

- Summing CONTRACTS.total_contract_value across a chain triples the value. Use V_CONTRACT_CHAIN.current_tcv.
- Summing SALESFORCE_OPPORTUNITIES.amount is correct (increments), summing CONTRACTS is not. Yes, it is confusing. Yes, we have asked Sales Ops to change the booking model.
- An opportunity with a wrong linked_contract_number will join to ANOTHER customer's agreement if you forget the customer_id condition. Always add it.
- A chain can legitimately have NetSuite orders without opportunity_id (Boomi left it blank). The crosswalk falls back to customer + start date; so_link_method tells you which path was used.
- ns_version_reflected is derived from boomi_sync_timestamp, not from anything NetSuite stores. If Boomi re-syncs an order without actually applying the amendment the derivation will say the amendment is reflected; in practice it has not happened since the March 2026 incident fix.
- Billing milestones in the contract that fall before an amendment are carried forward unchanged into the amended Exhibit B, so NetSuite bills from the earlier version still match them. Only the restated part of the schedule goes missing.
- Dates are DATE, Boomi sync and extraction timestamps are TIMESTAMP_NTZ. Cast before comparing.
- The as-of date 2026-09-30 is hard-coded in V_CONTRACT_CHAIN.is_active_today and in the billed flag of NETSUITE_BILLING_SCHEDULE.

## Worked example: Halvorsen Therapeutics (MCN-2025-0142)

Four versions. Latest is Amendment 3 (2026-07-20, TCV 2,730,000, end 2027-02-28, Net 45, Milestone). Salesforce has three opportunities (original 1,800,000 + A1 450,000 + A2 600,000 = 2,850,000) and nothing for A3. NetSuite has two orders (SO-10017 for the original and SO-10018 which Boomi created for the A1 increment) with the last sync on 2025-06-18, so ns_version_reflected = 1: original end date 2026-08-31, quarterly, Net 30. Running the eleven checks on this one chain gives TCV_MISMATCH, AMENDMENT_NOT_IN_SALESFORCE, TERM_END_DATE_MISMATCH, AMENDMENT_NOT_IN_NETSUITE (480,000), DUPLICATE_SALES_ORDERS, PAYMENT_TERMS_MISMATCH, BILLING_FREQUENCY_MISMATCH and four MISSING_BILLING_MILESTONE findings. It is the example in every training session for a reason.

## Who to ask

- Chain / version semantics, extraction confidence: Deal Desk (#deal-desk)
- Salesforce booking model, linked contract numbers: Sales Ops (#sales-ops-help)
- Boomi sync, duplicate orders, revenue schedules: Revenue Accounting (#close-reconciliation)
- Billing schedules and milestones: Billing (#billing-ops)
- This page, the views, the certified queries: Analytics Engineering (#data-help)
