# Business Glossary and Data Ownership Register

Owner: Finance Data Governance
Maintained by: Deal Desk (commercial terms) and Revenue Accounting (reconciliation terms)
Last review: 2026-09-12
Scope: order-to-cash data for the three-way contract reconciliation (MERIDIAN_POC.ANALYTICS)

## How to read this register

Each entry gives the business definition, the business owner accountable for the definition, the data steward who maintains it, the system of record and the warehouse table or view the term maps to. Synonyms are the words people actually use in Slack and in meetings.

## Parties and products

| Term | Definition | Synonyms | Business owner | Steward | System of record | Warehouse |
|---|---|---|---|---|---|---|
| Customer | A pharma brand or a health system that signs agreements with Meridian | account, client, brand (pharma), system (health system) | VP Commercial Operations | Deal Desk | Salesforce Account | CUSTOMERS |
| Customer type | Pharma (buys clinician marketing) or Health System (buys talent products) | vertical, segment group | VP Commercial Operations | Deal Desk | Salesforce | CUSTOMERS.customer_type |
| Account owner | The sales rep who owns the account and books its opportunities | rep, AE, owner, salesperson | VP Sales | Sales Ops | Salesforce | CUSTOMERS.account_owner, SALESFORCE_OPPORTUNITIES.owner |
| Sales pod | The team an account owner belongs to: Pharma East, Pharma West, Health Systems East, Health Systems West | team, pod, region team | VP Sales | Sales Ops | Salesforce | CUSTOMERS.sales_pod |
| Product | A sellable item: Specialty Targeted Campaign, Sponsored Content, Clinical Newsletter Placement, Peer Discussion Program, Recruiting Placement, Employer Branding, Residency Navigator Sponsorship, Physician Directory Enhanced Profile | SKU, item, campaign type, placement type | VP Product Marketing | Deal Desk | NetSuite item master | PRODUCTS |
| Specialty targeted | The clinician specialty a pharma campaign targets (Cardiology, Oncology ...) | specialty, audience, target specialty | VP Product Marketing | Deal Desk | DocuSign exhibit | CONTRACT_LINE_ITEMS.specialty_targeted |

## Agreements (DocuSign)

| Term | Definition | Synonyms | Business owner | Steward | System of record | Warehouse |
|---|---|---|---|---|---|---|
| Agreement | One original signed document plus all its amendments; the unit of reconciliation | contract, deal, chain, contract chain, MSA | Chief Accounting Officer | Revenue Accounting | DocuSign | V_CONTRACT_CHAIN (one row per agreement) |
| Document | One signed PDF: the original or an amendment | version, signed document, envelope | Deal Desk lead | Deal Desk | DocuSign | CONTRACTS (one row per document) |
| Contract number | The agreement number printed on the document; amendments append -A1, -A2 | agreement number, MCN number, contract ref | Deal Desk lead | Deal Desk | DocuSign | CONTRACTS.contract_number |
| Amendment | A signed change to an agreement that restates the full terms; numbered 1..n | change order, addendum, A1 A2 A3 | Deal Desk lead | Deal Desk | DocuSign | CONTRACTS where amendment_number > 0 |
| Latest version | The highest-numbered signed document of an agreement; carries the current terms | current terms, latest amendment, as signed | Revenue Accounting Manager | Revenue Accounting | DocuSign | V_CONTRACT_CHAIN.latest_* columns |
| Total contract value | The full value of the agreement as restated by the document | TCV, contract value, deal value | Revenue Accounting Manager | Revenue Accounting | DocuSign | CONTRACTS.total_contract_value, V_CONTRACT_CHAIN.current_tcv |
| Term | Effective date to end date of the agreement | contract period, service period, start and end | Revenue Accounting Manager | Revenue Accounting | DocuSign | CONTRACTS.effective_date, end_date, term_months |
| Payment terms | Days to pay an invoice: Net 30, Net 45, Net 60 | terms, net terms, payment days | Billing Lead | Billing | DocuSign | CONTRACTS.payment_terms |
| Billing frequency | How the agreement is invoiced: Upfront, Quarterly, Monthly, Milestone | billing schedule type, billing cadence, invoicing frequency | Billing Lead | Billing | DocuSign | CONTRACTS.billing_frequency |
| Billing milestone | One scheduled invoice in Exhibit B of a document (date, description, amount) | milestone, scheduled bill, instalment, Exhibit B line | Billing Lead | Billing | DocuSign | CONTRACT_BILLING_SCHEDULE |
| Exhibit A | The product lines of a document | line items, products on the contract | Deal Desk lead | Deal Desk | DocuSign | CONTRACT_LINE_ITEMS |
| Extraction confidence | Confidence of the automated term extraction from the signed PDF; below 0.90 Deal Desk reviews the extraction | OCR confidence, extraction score | Deal Desk lead | Deal Desk | Contract extraction service | CONTRACTS.extraction_confidence |
| Contract archive | The S3 bucket holding the signed PDFs by file name | PDF archive, DocuSign archive, signed copies | Deal Desk lead | Deal Desk | S3 | CONTRACTS.pdf_file_name |

## Salesforce

| Term | Definition | Synonyms | Business owner | Steward | System of record | Warehouse |
|---|---|---|---|---|---|---|
| Opportunity | A closed-won deal entered by the rep; one per signed document when booked correctly | opp, booking, closed won | VP Sales | Sales Ops | Salesforce | SALESFORCE_OPPORTUNITIES |
| Amendment opportunity | The opportunity booked for an amendment; its amount is the increment, not the restated total | amendment booking, upsell opp, change opp | VP Sales | Sales Ops | Salesforce | SALESFORCE_OPPORTUNITIES where opportunity_type = Amendment |
| Bookings | Sum of closed-won opportunity amounts | booked amount, Salesforce amount, Salesforce value | VP Sales | Sales Ops | Salesforce | V_CHAIN_SYSTEM_SUMMARY.sf_amount |
| Linked contract number | The contract number the rep typed on the opportunity; the only link from Salesforce to the signed document | contract link, contract ref on the opp | Sales Ops lead | Sales Ops | Salesforce | SALESFORCE_OPPORTUNITIES.linked_contract_number |
| Opportunity products | The products the rep added to the opportunity | opp lines, products on the opp | Sales Ops lead | Sales Ops | Salesforce | SALESFORCE_OPPORTUNITY_PRODUCTS |

## NetSuite

| Term | Definition | Synonyms | Business owner | Steward | System of record | Warehouse |
|---|---|---|---|---|---|---|
| Sales order | The NetSuite order Boomi creates from the opportunity; drives billing and revenue recognition | SO, order, NetSuite order | Controller | Revenue Accounting | NetSuite | NETSUITE_SALES_ORDERS |
| Order total | The sum of the order lines; Boomi should restate it on amendments | NetSuite amount, NetSuite value, ordered amount | Controller | Revenue Accounting | NetSuite | NETSUITE_SALES_ORDERS.order_total |
| Service end | The end date NetSuite uses to schedule revenue | revenue end date, NetSuite end date | Controller | Revenue Accounting | NetSuite | NETSUITE_SALES_ORDERS.end_date |
| Billing schedule type | NetSuite's billing schedule on the order: Upfront, Quarterly, Monthly, Milestone | NetSuite billing frequency | Billing Lead | Billing | NetSuite | NETSUITE_SALES_ORDERS.billing_schedule_type |
| NetSuite bill | One scheduled invoice on a sales order | bill, scheduled invoice, billing line | Billing Lead | Billing | NetSuite | NETSUITE_BILLING_SCHEDULE |
| Boomi sync | The last time Boomi created or updated the sales order from Salesforce | sync timestamp, last sync, Boomi run | IT Integrations | Revenue Accounting | Boomi | NETSUITE_SALES_ORDERS.boomi_sync_timestamp |
| Duplicate order | More than one sales order for one agreement, usually created by Boomi from an amendment opportunity | dup SO, second order | Controller | Revenue Accounting | NetSuite | V_CHAIN_SYSTEM_SUMMARY.ns_sales_order_count > 1 |

## Reconciliation

| Term | Definition | Synonyms | Business owner | Steward | System of record | Warehouse |
|---|---|---|---|---|---|---|
| Three-way match | Comparing the current terms of each agreement with Salesforce and NetSuite using the eleven checks | three-way reconciliation, contract recon, the recon | Chief Accounting Officer | Revenue Accounting | Rulebook + warehouse | RECONCILIATION_CONTROLS + the certified check queries |
| Check | One comparison rule with its tolerance, severity rule, owning team and SOX control | control, rule, test | Director of SOX and Automation | Revenue Accounting | Rulebook | RECONCILIATION_CONTROLS |
| Finding | One failed check on one agreement (or one milestone, opportunity or order for the row-level checks) | discrepancy, mismatch, exception, break | Chief Accounting Officer | Owning team | Derived | output of the check queries |
| Owning team | The team that reviews and resolves a finding: Sales Ops, Revenue Accounting, Billing | owner team, responsible team | Chief Accounting Officer | Revenue Accounting | Rulebook | RECONCILIATION_CONTROLS.owning_team |
| Severity | High, Medium or Low per the rulebook with dollar escalation | priority, risk level | Director of SOX and Automation | Revenue Accounting | Rulebook | RECONCILIATION_CONTROLS.default_severity, high_severity_usd |
| Exposure | Sum of the absolute dollar variance across open findings | dollar exposure, open exposure, dollars at risk | Chief Accounting Officer | Revenue Accounting | Derived | SUM(ABS(variance_usd)) |
| Stale system | A system that still carries the terms of an earlier version of the agreement | behind, not updated, lagging, out of date | Revenue Accounting Manager | Revenue Accounting | Derived | sf_version_reflected or ns_version_reflected < latest_version |
| SOX control reference | The order-to-cash control the check evidences (OTC-02 ... OTC-12) | control ref, OTC control, key control | Director of SOX and Automation | SOX and Automation | Control matrix | RECONCILIATION_CONTROLS.sox_control_ref |
| Decision | The reviewer's disposition of a finding: Confirmed, Rejected (false positive), Needs follow-up | disposition, outcome, resolution | Owning team lead | Owning team | Review workflow | not stored in the warehouse |
