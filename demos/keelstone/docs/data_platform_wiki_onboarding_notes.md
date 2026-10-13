# Data Platform Wiki: KEELSTONE_POC.ANALYTICS onboarding notes

Letterhead: Keelstone Data Systems — Data Platform Engineering (internal wiki page)
Page: Analytics / Snowflake / KEELSTONE_POC.ANALYTICS
Last edited: 2026-10-06 by Sofia Brennan (Data Platform Engineering)
Page owner: Data Platform Engineering on-call (#data-platform)
Status: Current

## Why this page exists

This is the single schema behind the revenue operations, installed base, support and cloud consumption reporting. It feeds the certified Power BI datasets in Fabric and the AI assistant. If you are onboarding a report or a new source against it, read this page first. Most support tickets we get about this schema are answered in the Gotchas section.

## Sources and refresh

| Source system | What we take | Loader | Refresh | Lands in |
|---|---|---|---|---|
| SAP S/4HANA | Sales order lines, recurring contracts, material master | Fivetran SAP connector to RAW, dbt models to ANALYTICS | Nightly 02:00 UTC | ORDERS, CONTRACTS, PRODUCTS |
| Salesforce | Accounts, users, renewal opportunities, partner master | Fivetran Salesforce connector | Hourly | CUSTOMERS, SALES_REPS, PARTNERS, RENEWAL_OPPORTUNITIES |
| ServiceNow | Cases with notes | Fivetran ServiceNow connector | Every 4 hours | SUPPORT_CASES |
| AutoPulse (call-home telemetry) | System registry and monthly rollups | Snowpipe from the AutoPulse S3 export | Daily registry, monthly rollup on the 3rd | INSTALLED_SYSTEMS, SYSTEM_TELEMETRY_MONTHLY |
| Cloud billing platform | Monthly metered consumption against commit | Scheduled task from the billing API | Monthly on the 5th | CLOUD_CONSUMPTION_MONTHLY |
| Derived | Fiscal calendar and data dictionary | dbt seed | On deploy | FISCAL_CALENDAR, DATA_DICTIONARY |

## Lineage of the certified views

| View | Reads | Ultimately from | Used by |
|---|---|---|---|
| V_ARR_MONTHLY | CONTRACTS, CUSTOMERS, PRODUCTS, INSTALLED_SYSTEMS, FISCAL_CALENDAR | SAP, Salesforce, AutoPulse | Finance ARR dataset (Power BI), board pack |
| V_ARR_FINANCE_VS_SALESOPS | CONTRACTS, CUSTOMERS, FISCAL_CALENDAR | SAP, Salesforce | ARR reconciliation report |
| V_RENEWAL_PERFORMANCE | CONTRACTS, CUSTOMERS, PRODUCTS, INSTALLED_SYSTEMS, FISCAL_CALENDAR | SAP, Salesforce, AutoPulse | Renewals dashboard |
| V_RENEWALS_AT_RISK_90D | CONTRACTS, RENEWAL_OPPORTUNITIES, SUPPORT_CASES, INSTALLED_SYSTEMS, CUSTOMERS, PARTNERS, SALES_REPS, PRODUCTS | SAP, Salesforce, ServiceNow, AutoPulse | Renewals at risk list, weekly forecast call |
| V_INSTALLED_BASE_HEALTH | INSTALLED_SYSTEMS, SYSTEM_TELEMETRY_MONTHLY, CONTRACTS, SUPPORT_CASES, CUSTOMERS, PRODUCTS, PARTNERS | AutoPulse, SAP, ServiceNow | Customer Success install base review |
| V_CLOUD_COMMIT_UTILIZATION | CLOUD_CONSUMPTION_MONTHLY, CUSTOMERS, PRODUCTS, FISCAL_CALENDAR | Cloud billing | Cloud revenue review |
| V_SUPPORT_CASE_SUMMARY | SUPPORT_CASES, CUSTOMERS, PRODUCTS, FISCAL_CALENDAR | ServiceNow | Support operations dashboard |
| V_PARTNER_ATTACH_RATE | INSTALLED_SYSTEMS, CONTRACTS, PARTNERS, FISCAL_CALENDAR | AutoPulse, SAP | Partner operations QBR |

## Join paths

- CUSTOMERS is the hub. Everything joins to it on CUSTOMER_ID. CUSTOMERS.PARTNER_ID joins PARTNERS; CUSTOMERS.REP_ID joins SALES_REPS.
- INSTALLED_SYSTEMS.SYSTEM_ID joins SYSTEM_TELEMETRY_MONTHLY, SUPPORT_CASES (nullable) and CONTRACTS (support and per-array KeelOS Core only).
- CONTRACTS.CONTRACT_ID joins RENEWAL_OPPORTUNITIES (one opportunity per contract end) and CLOUD_CONSUMPTION_MONTHLY (cloud commits).
- CONTRACTS.SUCCESSOR_CONTRACT_ID and PREDECESSOR_CONTRACT_ID chain renewals.
- Dates join FISCAL_CALENDAR on CALENDAR_DATE for fiscal labels.

## Gotchas (read these)

- CONTRACTS is a history table. Every renewal in a chain is its own row. A plain SUM of ANNUAL_VALUE over the table is meaningless; always restrict to contracts in force on a date (START_DATE <= date < END_DATE) or to a CONTRACT_STATUS.
- END_DATE is exclusive. A contract ending 2026-12-01 is in force through 2026-11-30. Its renewal starts 2026-12-01. Do not add a day.
- CONTRACT_STATUS is evaluated as of the as-of date: ACTIVE means END_DATE is in the future; RENEWED, CHURNED and PENDING_RENEWAL apply to lapsed contracts.
- The product on a support contract is the support tier (Standard, Premium, Mission Critical, Extended). To report by array family join through SYSTEM_ID to INSTALLED_SYSTEMS and PRODUCTS. The certified views already do this; PRODUCT_FAMILY in those views means the covered array's family.
- RENEWAL_OPPORTUNITIES.QUOTE_AMOUNT carries the quoted uplift and is not the contract value. ARR figures must come from CONTRACTS.ANNUAL_VALUE.
- Opportunities stay open after a contract lapses until Renewals Ops closes them, which can take up to a year. This is why the Sales Ops ARR extract differs from Finance ARR. Do not "fix" this in the data; it is the business process.
- SYSTEM_TELEMETRY_MONTHLY and CLOUD_CONSUMPTION_MONTHLY end at the last complete month (September 2026). There is no October telemetry until the rollup lands on 3 November.
- SUPPORT_CASES.CASE_NOTES is free text written by support engineers and can be several paragraphs. It contains customer sentiment that is not coded anywhere else.
- Firmware strings are "KeelOS 9.14.2" style. Filter with equality, not LIKE '9.14%' unless you mean the whole 9.14 line.
- Americas East upgraded to KeelOS 9.14.2 first (July and August 2026). Comparing P1 case counts across regions without the firmware version will mislead.
- Rates in the views (RENEWAL_RATE, ATTACH_RATE, UTILIZATION_PCT) are precomputed per row. Never average them; roll up numerator and denominator.

## Source onboarding checklist (what it took for ServiceNow)

- Catalogue: register the source in the glossary register (GOV-GLS-001) with owner and steward. (2 days of back and forth to find an owner.)
- Classify: tag CASE_NOTES as containing customer-identifiable free text; mask contact names in lower environments.
- Document: write column comments in the DDL; they are the descriptions the AI assistant and the catalog pick up.
- Quality rules: closed cases need a closed date; priority must be P1 to P4; firmware strings validated against the KeelOS release list.
- Lineage: add the new tables to the lineage table above and to the dbt exposures so the Power BI datasets show their upstream.
- Review: steward sign-off before the dataset is certified.

## Known issues

- KI-412: 14 ServiceNow cases from 2025-06 have CLOSED_DATE before OPENED_DATE in RAW; corrected in the ANALYTICS model, open with the ServiceNow admin team.
- KI-437: AutoPulse registry occasionally reports a decommissioned serial as active for one cycle; the ANALYTICS model keeps the first decommission date.
- KI-441: Sales Ops Power BI "ARR" measure still uses the open-opportunity logic; renamed to "Pipeline ARR" in the October release.

## Contacts

- Data Platform Engineering on-call: #data-platform (Sofia Brennan, Noah Fischer).
- Finance data steward: Priya Iyer. Sales Ops data steward: Daniel Okafor. Support Engineering steward: Jonas Lindqvist.
- Governance questions: Marcus Whitfield, Head of Data Governance.
