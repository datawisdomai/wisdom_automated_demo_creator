# Finance Metric Definitions Standard

Letterhead: Keelstone Data Systems — Finance, Financial Planning and Analysis
Document: FIN-STD-004 Metric Definitions Standard, version 3.2
Effective: 2026-05-01 (fiscal year FY27)
Owner: Director of FP&A (Helena Marsh)
Data steward: Finance Data Domain Steward (Priya Iyer)
Classification: Internal. Certified definitions for executive reporting.

## 1. Purpose

This standard defines the recurring revenue and renewal metrics used in executive reporting, board materials and the certified Power BI datasets. Any report, dashboard or AI-generated answer that uses one of these metric names must use the definition in this document. Where a team needs a variant, the variant must carry a different name (for example "Sales Ops pipeline ARR") and must not be labelled ARR.

## 2. Fiscal calendar

- Keelstone's fiscal year ends on 30 April and is named for the calendar year in which it ends. FY27 runs from 2026-05-01 to 2027-04-30.
- Fiscal quarters: Q1 May to July, Q2 August to October, Q3 November to January, Q4 February to April.
- "Fiscal year to date" means from 1 May of the current fiscal year to the reporting date.
- Physical mapping: FISCAL_CALENDAR.FISCAL_YEAR and FISCAL_CALENDAR.FISCAL_QUARTER in Snowflake KEELSTONE_POC.ANALYTICS.

## 3. Annual Recurring Revenue (ARR)

**Definition.** ARR on a date is the sum of the annualised value of every recurring contract in force on that date. A contract is in force while its start date is on or before the date and its end date is after the date (the end date is exclusive).

- Recurring contracts are support contracts, KeelOS software subscriptions and cloud commits. Hardware orders and professional services are never ARR.
- Multi-year contracts contribute their annual value, not their total contract value.
- A contract that renews contributes continuously: the successor starts on the predecessor's end date.
- A contract stops contributing on the day it lapses, whatever the state of the renewal conversation.
- Physical mapping: CONTRACTS.ANNUAL_VALUE where CONTRACTS.START_DATE <= date < CONTRACTS.END_DATE. The certified monthly series is the view V_ARR_MONTHLY (ARR column) measured at month end.

**Known variant (not certified).** Sales Operations publishes an ARR figure that continues to count a lapsed contract while its renewal opportunity remains open in Salesforce. Renewals Operations closes those opportunities as lost up to a year after the lapse. The difference between the two figures is reported in V_ARR_FINANCE_VS_SALESOPS as LAPSED_OPEN_ARR. The Finance figure is the number of record.

## 4. Net Revenue Retention (NRR)

**Definition.** ARR today from the customers who had ARR twelve months ago, divided by their ARR twelve months ago. Includes expansion, contraction and churn from that cohort; excludes customers acquired in the last twelve months.

## 5. Renewal rate (gross ARR renewal rate)

**Definition.** For contracts whose end date falls in the period: ARR renewed divided by ARR due.

- ARR due is the annual value of every contract that reached its end date in the period.
- ARR renewed is the annual value of those contracts for which a successor contract has been signed.
- A lapsed contract whose renewal is still open (pending) counts as not yet renewed. It is reported separately as ARR pending.
- A lapsed contract whose opportunity was closed lost is churned ARR.
- Rates are computed in dollars. Rolling up across regions, quarters or product families means dividing the sum of ARR renewed by the sum of ARR due, never averaging rates.
- Physical mapping: V_RENEWAL_PERFORMANCE (ARR_DUE, ARR_RENEWED, ARR_CHURNED, ARR_PENDING, RENEWAL_RATE).

| Term | Status in CONTRACTS | Counts as |
|---|---|---|
| Renewed | RENEWED | ARR renewed |
| Closed lost | CHURNED | ARR churned |
| Renewal open after lapse | PENDING_RENEWAL | ARR pending (not yet renewed) |
| Still in force | ACTIVE | Not yet due |

## 6. ARR up for renewal and ARR at risk

- ARR up for renewal in the next 90 days is the annual value of active contracts whose end date falls in the next 90 days from the reporting date.
- ARR at risk is the subset the Renewals team has flagged AT_RISK on the Salesforce opportunity, with the reason recorded (End of support product, Open P1 case, Budget, Competitive, Consolidation). The flag is the team's assessment and is not a prediction.
- Physical mapping: V_RENEWALS_AT_RISK_90D (ANNUAL_VALUE, RISK_FLAG, RISK_REASON).

## 7. Bookings

**Definition.** The net amount of orders accepted in the period from SAP S/4HANA, including one-time hardware and the total contract value of multi-year recurring contracts. Bookings are a sales measure and are never a substitute for ARR.

- Physical mapping: ORDERS.NET_AMOUNT by ORDERS.ORDER_DATE.

## 8. Support attach rate

**Definition.** Among systems installed in the period, the share with a support contract whose start date is within 60 days of the install date. Reported by partner and fiscal quarter.

- Physical mapping: V_PARTNER_ATTACH_RATE (SYSTEMS_INSTALLED, SYSTEMS_WITH_SUPPORT, ATTACH_RATE). Roll up by dividing the sums.

## 9. Cloud commit utilisation

**Definition.** Metered cloud consumption in the fiscal year to date divided by the committed amount for the same months. An account below 60 percent with at least three months of data is under-utilised.

- Physical mapping: V_CLOUD_COMMIT_UTILIZATION (COMMIT_AMOUNT, CONSUMED_AMOUNT, UTILIZATION_PCT, IS_UNDER_UTILIZED). Monthly detail in CLOUD_CONSUMPTION_MONTHLY.

## 10. Governance

- Change control: changes to a definition require approval by the Director of FP&A and the Finance Data Domain Steward and a new version of this standard.
- Certification: a dataset or report is certified only if every metric it exposes is computed exactly as defined here from the views named above.
- Questions about a definition go to the #data-help channel; the steward answers within one business day.
- Related documents: Business Glossary and Data Ownership Register (GOV-GLS-001), Sales Operations Renewal Playbook FY27.
