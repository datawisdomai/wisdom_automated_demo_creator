# Sales Operations Renewal Playbook FY27

Letterhead: Keelstone Data Systems — Sales Operations
Document: SOPS-PB-FY27, version 1.2
Effective: 2026-05-01, updated 2026-08-24 after the Q1 installed base review
Owner: Grace Osei, VP Sales Operations
Applies to: Account executives, renewals specialists, cloud specialists and partner managers

## 1. The renewal window

- A renewal opportunity is created in Salesforce 120 days before the contract end date for every recurring contract: support, KeelOS subscriptions and cloud commits. The expected close date is the contract end date.
- Stages: Qualification (more than 90 days out), Quote Sent (90 to 45 days), Negotiation (inside 45 days), Closed Won, Closed Lost.
- A contract that lapses with the opportunity still open is a pending renewal. Finance stops counting its ARR on the lapse date. Renewals Ops reviews pending opportunities monthly and closes them lost no later than twelve months after the lapse. The Sales Ops pipeline figure continues to include them until then; it is not the certified ARR.

## 2. Risk flags

Every opportunity carries a risk flag set by the renewals specialist and reviewed weekly:

| Flag | Meaning | Reasons |
|---|---|---|
| ON_TRACK | Customer has confirmed intent or there is no known obstacle | none |
| AT_RISK | A known obstacle could prevent the renewal | End of support product, Open P1 case, Budget, Competitive, Consolidation |

- End of support product: the covered array reaches end of support within twelve months of the contract end date (currently the KS-7000 family, 2027-01-31).
- Open P1 case: the customer has had a priority 1 case in the last 90 days or has one open now.
- Competitive: the customer has named another vendor; record the competitor on the opportunity.
- The flag is the team's assessment. Do not describe it as a forecast or a churn probability in customer-facing or executive material.

## 3. Weekly cadence

- Monday: the at-risk list is pulled from V_RENEWALS_AT_RISK_90D (contracts ending in the next 90 days) using the Finance definitions, by region and renewals specialist.
- Tuesday: regional review. Every AT_RISK contract above 100 thousand dollars of annual value needs a documented next step and an owner.
- Thursday: executive sponsor assignment for any account with more than 500 thousand dollars at risk or an open P1 case inside 60 days of renewal.
- Monthly: pending renewals older than 90 days are reviewed with Finance and either re-forecast or closed lost.

## 4. Plays

### 4.1 End-of-support play (KS-7000)

- Lead with the migration path from bulletin PLB-2026-014: KS-9300 or KS-9500 with the trade-in credit, and the Extended Support bridge (SUP-EXT7K) for customers that need more than the remaining term.
- Quote the KeelOS Core subscription transfer at no charge; it removes the objection that software is paid twice.
- Never quote a standard support term that extends past 2027-01-31 on a KS-7000 system.

### 4.2 Open P1 play

- Confirm the case status with Support Engineering and that the written root cause analysis has been delivered. For the KeelOS 9.14.2 defect (KB-2026-0917) confirm the 9.14.3 upgrade is scheduled.
- Offer a health review of the customer's fleet from V_INSTALLED_BASE_HEALTH before the renewal conversation.
- Credits against the renewal require VP approval and must be recorded on the opportunity.

### 4.3 Cloud commit play

- For accounts under 60 percent of their commit (V_CLOUD_COMMIT_UTILIZATION, IS_UNDER_UTILIZED = 1), propose a right-sized commit with a growth ramp rather than a flat renewal. A lapsed cloud commit converts to list-price pay-as-you-go which customers resent.
- For accounts with overage, propose a larger commit with the overage credited.

### 4.4 Partner attach play

- Partners below 70 percent attach rate on new systems (V_PARTNER_ATTACH_RATE) are reviewed in the partner QBR. Unattached systems are contacted by the renewals team directly at 60 days after install with a first-year support offer.

## 5. Definitions used in this playbook

- ARR, renewal rate, ARR at risk and attach rate follow the Finance Metric Definitions Standard v3.2. When a number in this playbook differs from the Finance pack, the Finance pack is right and the playbook example is stale.
- Fiscal year FY27 runs 2026-05-01 to 2027-04-30; Q2 is August to October.

## 6. Current focus (updated 2026-08-24)

- Americas East: about 28 million dollars renewing in the next 90 days with roughly 13 million flagged at risk; the pending backlog is about 10 million. Priority accounts are the KS-7000 estates with 9.14.2 P1 cases, starting with Brightwater Mutual Insurance, Tidewater Health Alliance and Pinecrest Regional Health.
- Altura Technology Partners attach rate review scheduled for the October partner QBR.
- 27 enterprise cloud accounts under 60 percent of commit assigned to the cloud specialists for right-sizing conversations before their commits renew.
