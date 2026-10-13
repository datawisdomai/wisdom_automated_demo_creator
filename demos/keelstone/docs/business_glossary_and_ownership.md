# Business Glossary and Data Ownership Register

Letterhead: Keelstone Data Systems — Data Governance Office
Document: GOV-GLS-001 Business Glossary and Data Ownership Register
Version: 2026.10 (reviewed 2026-10-05)
Owner: Head of Data Governance (Marcus Whitfield)
Scope: Revenue operations, installed base, support and cloud consumption data in Snowflake KEELSTONE_POC.ANALYTICS

## 1. How to use this register

Each business term has one definition, one business owner who approves changes, one data steward who maintains the physical mapping, and the source system of record. The physical asset column names the Snowflake table or view and column that implements the term. Teams building reports or asking the AI assistant should use the terms exactly as defined; synonyms are listed so that different teams' vocabulary resolves to the same asset.

## 2. Core business entities

| Term | Definition | Business owner | Data steward | Source system | Physical asset |
|---|---|---|---|---|---|
| Customer | A legal entity that has purchased from Keelstone. Identified by the Salesforce account. | VP Sales Operations | Sales Ops data steward (Daniel Okafor) | Salesforce | CUSTOMERS (CUSTOMER_ID, CRM_ACCOUNT_ID) |
| Segment | ENTERPRISE, COMMERCIAL or PUBLIC_SECTOR as assigned by Sales Ops territory planning. | VP Sales Operations | Daniel Okafor | Salesforce | CUSTOMERS.SEGMENT |
| Region | Keelstone sales region: Americas East, Americas West, EMEA, APAC. | VP Sales Operations | Daniel Okafor | Salesforce | CUSTOMERS.REGION and SALES_REPS.REGION |
| Partner | Channel partner of record for an account (VAR, distributor or MSP). PTR-000 denotes direct sales. | VP Channel Sales | Partner Ops steward (Elena Ramirez) | Salesforce partner master | PARTNERS and CUSTOMERS.PARTNER_ID |
| Installed system | An array that Keelstone has shipped, identified by serial number, registered in AutoPulse. | VP Customer Success | Support Engineering steward (Jonas Lindqvist) | AutoPulse registry | INSTALLED_SYSTEMS.SYSTEM_ID |
| Product family | The array or service family: KS-5000, KS-7000, KS-9000, HD-3000, KeelOS, Keelstone Cloud Volumes, Keelstone Object Store, Support. For a support contract or a KeelOS Core subscription it means the family of the covered array. | VP Product Management | Product data steward (Aisha Haddad) | SAP material master | PRODUCTS.PRODUCT_FAMILY |
| Contract | A recurring agreement (support, software subscription or cloud commit) with a start date, an exclusive end date and an annual value. | Director of FP&A | Finance data steward (Priya Iyer) | SAP S/4HANA | CONTRACTS |
| Renewal opportunity | The Salesforce opportunity created 120 days before a contract ends to track its renewal. | VP Sales Operations | Daniel Okafor | Salesforce | RENEWAL_OPPORTUNITIES |
| Support case | A customer issue logged in ServiceNow with priority P1 to P4. P1 means production down. | VP Customer Success | Jonas Lindqvist | ServiceNow | SUPPORT_CASES |
| Cloud commit | An annual committed spend on Keelstone Cloud Volumes or Object Store against which monthly consumption is metered. | VP Cloud Services | Cloud billing steward (Mateo Delgado) | Cloud billing platform | CONTRACTS (CLOUD_COMMIT) and CLOUD_CONSUMPTION_MONTHLY |
| Booking | An accepted order line in SAP with its net amount. | Director of Revenue Accounting | Priya Iyer | SAP S/4HANA | ORDERS |
| Fiscal year | Twelve months ending 30 April, named for the calendar year in which it ends. | Director of FP&A | Priya Iyer | Derived | FISCAL_CALENDAR.FISCAL_YEAR |

## 3. Certified metrics

| Term | Definition | Business owner | Data steward | Physical asset |
|---|---|---|---|---|
| ARR | Sum of annual value of recurring contracts in force on the measurement date (Finance Metric Definitions Standard v3.2 section 3). | Director of FP&A | Priya Iyer | V_ARR_MONTHLY.ARR |
| Sales Ops ARR | Finance ARR plus lapsed contracts whose renewal opportunity is still open. Not certified; used by Sales Ops for pipeline management. | VP Sales Operations | Daniel Okafor | V_ARR_FINANCE_VS_SALESOPS.SALESOPS_ARR |
| Renewal rate | ARR renewed divided by ARR due for contracts ending in the period. Pending renewals count as not yet renewed. | Director of FP&A | Priya Iyer | V_RENEWAL_PERFORMANCE |
| ARR at risk | ARR renewing in the next 90 days flagged AT_RISK by the Renewals team. | VP Sales Operations | Daniel Okafor | V_RENEWALS_AT_RISK_90D |
| Support attach rate | Systems with a support contract starting within 60 days of install divided by systems installed. | VP Channel Sales | Elena Ramirez | V_PARTNER_ATTACH_RATE |
| Commit utilisation | Cloud consumption divided by commit, fiscal year to date. | VP Cloud Services | Mateo Delgado | V_CLOUD_COMMIT_UTILIZATION |
| Installed base health | AutoPulse health score (0 to 100) for the latest telemetry month; below 70 is poor. | VP Customer Success | Jonas Lindqvist | V_INSTALLED_BASE_HEALTH.LATEST_HEALTH_SCORE |
| End-of-support exposure | Active systems whose product reaches end of support within 12 months. | VP Product Management | Aisha Haddad | V_INSTALLED_BASE_HEALTH.IS_END_OF_SUPPORT_WITHIN_12M |

## 4. Lifecycle terms

| Term | Definition | Owner | Physical asset |
|---|---|---|---|
| End of sale | Last date a product can be ordered. KS-7000 family: 2025-10-31. HD-3000 family: 2026-12-31. | VP Product Management | PRODUCTS.END_OF_SALE_DATE |
| End of support | Date Keelstone stops providing support and firmware for a product. KS-7000 family: 2027-01-31 (bulletin PLB-2026-014). | VP Product Management | PRODUCTS.END_OF_SUPPORT_DATE |
| Extended support | Limited post-end-of-support coverage. KS-7000 Extended Support (SUP-EXT7K) runs to 2028-01-31. | VP Customer Success | PRODUCTS.SUPPORT_TIER = EXTENDED |
| Firmware | The KeelOS release an array runs. 9.14.2 (2026-07-01) carries defect KB-2026-0917; 9.14.3 (2026-09-15) is the fix. | VP Engineering | INSTALLED_SYSTEMS.CURRENT_FIRMWARE |
| AutoPulse | Keelstone's call-home telemetry service; source of the installed base registry and monthly health data. | VP Customer Success | SYSTEM_TELEMETRY_MONTHLY |

## 5. Synonyms

- ARR: annual recurring revenue, recurring revenue, run rate, the Finance number.
- Sales Ops ARR: the Salesforce number, pipeline ARR, bookings ARR.
- Renewal rate: gross retention, GRR, renewal percentage.
- Pending renewal: stalled renewal, open renewal, lapsed, in the grace window.
- Installed system: array, box, system, node, estate, fleet, install base.
- End of support: EOS, EOL, end of life, sunset.
- End of sale: EOSL, off the price list, no longer orderable.
- P1: sev 1, severity 1, outage, production down.
- Partner: channel, reseller, VAR, distributor, MSP.
- Region: theater, geo. Americas East is sometimes called AMER East or East.
- Cloud commit: committed spend, annual commit, cloud contract.
- Under-utilised: under-consumed, burn-down shortfall, unconsumed commit.

## 6. Data quality rules enforced on the certified views

- Every contract has a start date before its end date and an annual value above zero.
- A RENEWED contract has a successor whose start date equals its end date.
- No ACTIVE contract has an end date in the past; no lapsed status appears on a contract still in force.
- Every support case flagged CLOSED has a closed date.
- Customer names are unique.
- Renewal opportunity stages agree with contract status (Closed Won only for RENEWED, Closed Lost only for CHURNED).

## 7. Change log

- 2026.10: added lifecycle terms for the KS-7000 end of support and the KeelOS 9.14.2 defect; clarified that product family on support and KeelOS Core contracts means the covered array's family.
- 2026.07: added Sales Ops ARR as a named, non-certified variant after the FY26 close reconciliation.
- 2026.05: aligned with Finance Metric Definitions Standard v3.2.
