# Live App prompt — Renewals and Installed Base Cockpit

Paste into Wisdom on the Keelstone Data Systems domain.

```
Create a live app called "Renewals and Installed Base Cockpit" for Keelstone Data Systems, a hybrid-cloud storage and data infrastructure vendor. It is an operational cockpit for the VP of Sales Operations, not a reporting dashboard. Every page answers "which renewals are slipping, why, and what do we do about it this quarter". Use three connected pages.

DATA RULES
Use V_RENEWAL_PERFORMANCE for renewal rate, V_ARR_MONTHLY for ARR and V_RENEWALS_AT_RISK_90D for the renewal pipeline. Use V_ARR_FINANCE_VS_SALESOPS for the Finance versus Sales Ops ARR comparison, V_INSTALLED_BASE_HEALTH for end-of-support and firmware exposure, V_SUPPORT_CASE_SUMMARY for P1 case trends and V_CLOUD_COMMIT_UTILIZATION for cloud commits. Aggregate each source before combining; never join fact tables as raw rows.
Anchor "today" to 2026-10-12. The current fiscal quarter is FY27-Q2 and the fiscal year ends 30 April; the latest complete month is September 2026. ARR is the certified Finance definition (V_ARR_MONTHLY); when the Sales Ops figure appears label it "Sales Ops ARR (not certified)". Renewal rate is SUM(ARR_RENEWED) / SUM(ARR_DUE); never average rate columns. Describe RISK_FLAG as the renewals team's assessment, never as a churn prediction.

PAGE 1: EXECUTIVE OVERVIEW
KPI tiles: Finance ARR for October 2026 with the change since April 2026; FY27 renewal rate to date versus FY26; ARR renewing in the next 90 days with the at-risk share; cloud commit utilisation for FY27 with the number of under-utilised enterprise accounts.
One chart that shows the core story: renewal rate by region for FY26 versus FY27 to date, with Americas East highlighted.
Breakdowns: ARR at risk in the next 90 days by region and by risk reason; FY27 renewal rate by product family inside the selected region; P1 cases per month since May 2026 by region for KeelOS 9.14.2; a small Finance ARR versus Sales Ops ARR panel for September 2026 with the gap explained in one sentence.
Preselect Americas East so the demo starts there. Clicking a region filters the breakdowns and carries into the Scenario Lab.

PAGE 2: RENEWAL RESCUE LAB
For the selected region show three scenarios side by side: Baseline, Custom, and System Recommended.
Baseline is the current state: no migration offers, no credits, pending renewals left to run their course.
Custom has four controls: share of at-risk KS-7000 renewals that receive a migration offer with the Extended Support bridge (0 to 100 percent); renewal credit on accounts with an open P1 case (0 to 10 percent of annual value); number of renewals specialists re-assigned to the region (0 to 4); cloud commit right-sizing on under-utilised accounts (on or off).
System Recommended uses a simple transparent rule: rank the at-risk contracts in V_RENEWALS_AT_RISK_90D by annual value times an editable save probability for each risk reason, assign migration offers and credits in that order until the budget and specialist capacity run out, and show the ranked list with the action, expected retained ARR, cost and a plain-language reason.
Assumptions panel, editable and clearly labelled as assumptions: save probability with a migration offer on an End of support product renewal 55 percent (baseline 30); save probability with a credit and a delivered RCA on an Open P1 case renewal 60 percent (baseline 35); each re-assigned specialist works 25 additional contracts; a right-sized cloud commit retains 85 percent of commit value instead of lapsing to pay-as-you-go; credit cost equals the credit percent times annual value.
Compare all three scenarios on: ARR retained from the next 90 days; ARR still at risk; projected FY27 renewal rate for the region; cost of credits; net ARR impact; confidence High, Medium or Low based on how much of the uplift depends on assumptions.
The user explicitly selects one scenario; the selection flows to the Implementation Plan.

PAGE 3: IMPLEMENTATION PLAN
Receive the selected scenario and prepopulate a rollout plan phased by confidence: quick wins (migration offers to the largest End of support product renewals), a controlled pilot (credits plus RCA follow-up on Open P1 case accounts), and segments to monitor and hold. Include a leadership summary written from the current assumptions, monitoring thresholds (regional renewal rate, pending ARR, new P1 cases on 9.14.2), the concrete queue of contracts to act on with customer, partner, rep, end date and annual value, owners, due dates and success metrics. Let the user edit any field and approve. On submit, save the plan to an action log inside the app and show a labelled mock payload for the Salesforce handoff; state plainly that no external system is connected.

DESIGN
Calm, operational, few KPI tiles. Top stepper Executive Overview -> Renewal Rescue Lab -> Implementation Plan. Preserve the selected region and scenario across pages. Tables where precision matters, tabular numerals for money, fiscal labels (FY27-Q2) on time axes.
```
