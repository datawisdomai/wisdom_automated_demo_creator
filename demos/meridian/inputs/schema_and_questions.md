# Suggested schema and must-answer questions (internal input)

Tables:

CUSTOMERS
customer_id, customer_name, customer_type (Pharma, Health System), segment, account_owner, region

CONTRACTS (represents the extracted terms from the DocuSign PDF)
contract_id, customer_id, contract_number, docusign_envelope_id, contract_type (New, Renewal, Amendment), parent_contract_id (null for originals, points to the original for amendments), amendment_number, signed_date, effective_date, end_date, term_months, total_contract_value, currency, payment_terms (Net 30, Net 45, Net 60), billing_frequency (Upfront, Quarterly, Milestone, Monthly), auto_renew (bool), cancellation_notice_days, signatory_name, product_summary (text), extracted_at, extraction_confidence

CONTRACT_LINE_ITEMS
contract_id, line_id, product_name (e.g. Specialty Targeted Campaign, Sponsored Content, Recruiting Placement, Employer Branding, Residency Navigator Sponsorship), specialty_targeted, quantity, unit_price, line_amount, start_date, end_date

CONTRACT_BILLING_SCHEDULE (from the PDF)
contract_id, milestone_number, milestone_description, scheduled_date, scheduled_amount

SALESFORCE_OPPORTUNITIES
opportunity_id, customer_id, opportunity_name, stage (all Closed Won), amount, close_date, contract_start_date, contract_end_date, term_months, owner, linked_contract_number (sometimes null or wrong), last_modified_date

SALESFORCE_OPPORTUNITY_PRODUCTS
opportunity_id, product_name, quantity, unit_price, total_price

NETSUITE_SALES_ORDERS
sales_order_id, customer_id, opportunity_id (populated by Boomi, sometimes missing), order_date, order_total, start_date, end_date, payment_terms, status, boomi_sync_timestamp

NETSUITE_SALES_ORDER_LINES
sales_order_id, line_id, item_name, quantity, rate, amount

NETSUITE_BILLING_SCHEDULE
sales_order_id, bill_number, bill_date, bill_amount, billed (bool)

RECONCILIATION_RESULTS (the output WisdomAI would produce) — DROPPED in the revision: Wisdom derives findings live.

## Discrepancies to seed deliberately
Most records should reconcile cleanly. Seed roughly 15 to 20 percent of contracts with realistic problems:
- Amount mismatch: Salesforce amount differs from contract TCV (rep rounded, or excluded a line item).
- Term mismatch: end date in NetSuite is the original contract end, amendment extended it.
- Billing schedule mismatch: contract says milestone based, NetSuite shows quarterly, or milestone amounts differ.
- Payment terms mismatch: contract Net 45, NetSuite Net 30.
- Amendment never reached NetSuite: amendment signed, Salesforce updated, NetSuite still on original.
- Amendment never reached Salesforce either: only exists in DocuSign.
- Missing link: NetSuite order with no opportunity_id, or opportunity with no matching contract_number.
- Product mismatch: contract has 3 line items, Salesforce has 2.
- Duplicate: two NetSuite sales orders for one contract after an amendment.
Make a few of these compound, where one contract with multiple amendments has drifted across both systems.

## Questions the demo must answer well
- Which closed won deals do not reconcile across all three systems?
- Show me every contract with amendments where NetSuite still reflects the original terms.
- Which billing milestones in the contract are missing from the NetSuite billing schedule?
- Total contract value by customer type where Salesforce and the contract disagree, and by how much.
- Which discrepancies belong to the Revenue team vs Billing vs Sales Ops?
- Show me the full amendment lineage for [customer] and where each system is relative to the latest amendment.
- What is the dollar exposure of unreconciled items this quarter?
- Which account owners have the most mismatches?
- Trend of mismatch rate by month, and whether amendments drive it.
