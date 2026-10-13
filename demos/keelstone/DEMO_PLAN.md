# Demo Plan: Keelstone Data Systems

**Prospect / vertical:** NetApp (Technology — hybrid-cloud storage and data infrastructure vendor) · **Persona:** VP of Sales Operations, with Finance (FP&A) and the executive staff alongside · **As-of date:** 2026-10-12 (Q2 FY27; Keelstone's fiscal year ends 30 April)

## The story in one paragraph
Keelstone Data Systems sells storage arrays, a storage operating system sold by subscription
(KeelOS), cloud volume services on the hyperscalers, and support contracts, mostly through channel
partners. The VP of Sales Operations is measured on renewal rate, ARR and at-risk ARR; Finance is
measured on certified ARR and NRR. Today the two teams argue about whose ARR is right and find out
about renewal problems from the quarterly report. The demo shows governed self-service on the data
already in Snowflake: certified metric definitions the answers always use, a glossary and semantic
context extracted from the documents the stewards actually own, free-text support notes read
alongside the numbers, and an agent that watches renewal risk so nobody has to. Nothing names NetApp.

## Story arcs (what the data will prove) — kept deliberately simple
| # | Arc | Hero entity | Target numbers the data will contain |
|---|---|---|---|
| CP1 (hero) | **Renewals are slipping in one region.** Americas East renewal rate fell from ~90% of ARR due in FY26 to ~79% in Q1–Q2 FY27 (most of the shortfall is pending, not lost). Two visible causes: the KS-7000 array family reaches end of support on 31 Jan 2027 and customers are holding off, and a cluster of P1 cases after the KeelOS 9.14 upgrade (controller failover). | Americas East region; KS-7000 family; KeelOS 9.14 | renewal rate drop ≥ 6 pts vs FY26; ≥ $15M ARR renewing in the next 90 days in the region, ≥ $5M of it flagged at risk; KeelOS 9.14 P1 cases in Americas East ≥ 3× any other region |
| CP2 | **Two ARRs.** Sales Ops reports ARR about 5% higher than Finance because its number keeps counting lapsed contracts whose renewal opportunity is still open in Salesforce (closed lost up to a year later). The certified definition (Finance) is the one the answers use; the gap is explainable on demand. | ARR metric | Sales Ops ARR exceeds Finance ARR by 5–8% as of September 2026 (built: 5.4% overall, 7.0% in Americas East) |
| CP3 | **Cloud grows, commits go unused.** Keelstone Cloud Volumes consumption is up ~40% year over year, but ~25 enterprise accounts are running below 60% of their annual commit (built: 27; consumption +78% YoY) — a renewal conversation waiting to happen. | Keelstone Cloud Volumes | YoY consumption growth ≥ 35%; ≥ 20 accounts under 60% commit utilisation |
| CP4 | **A top partner stopped attaching support.** Altura Technology Partners' support-contract attach rate on new systems fell from ~78% to ~62% this fiscal year while the other top partners held steady. | Altura Technology Partners | attach rate drop ≥ 12 pts (built: 77% → 61%); peers within ±3 pts |

## Data (Snowflake `KEELSTONE_POC.ANALYTICS`)
- Dimensions (5): `FISCAL_CALENDAR` (FY ends 30 Apr), `CUSTOMERS` (~400; segment, industry, region, owning partner), `PRODUCTS` (~40 array families, KeelOS subscriptions, cloud services and support tiers, with end-of-sale / end-of-support dates), `PARTNERS` (~25), `SALES_REPS` (~60, mapped to regions).
- Facts (7): `ORDERS` (~12k bookings lines from SAP), `INSTALLED_SYSTEMS` (~2,500 systems), `SYSTEM_TELEMETRY_MONTHLY` (~40k rows: capacity used, firmware version, health score — the AutoPulse feed), `CONTRACTS` (~3,500 support/subscription contracts with renewal dates), `RENEWAL_OPPORTUNITIES` (~1,200 from Salesforce; stage, quote amount, risk flag), `CLOUD_CONSUMPTION_MONTHLY` (~2,500 rows: commit vs consumed), `SUPPORT_CASES` (~6,000 from ServiceNow; priority, product, firmware, **free-text engineer notes**).
- Views (8): `V_ARR_MONTHLY` (certified Finance ARR), `V_ARR_FINANCE_VS_SALESOPS`, `V_RENEWAL_PERFORMANCE`, `V_RENEWALS_AT_RISK_90D`, `V_INSTALLED_BASE_HEALTH`, `V_CLOUD_COMMIT_UTILIZATION`, `V_SUPPORT_CASE_SUMMARY`, `V_PARTNER_ATTACH_RATE`; plus `DATA_DICTIONARY`.
- Unstructured, two layers:
  1. The `CASE_NOTES` column in `SUPPORT_CASES`: realistic engineer notes (the hero cluster reads like "controller failover during KeelOS 9.14.2 upgrade…"), so "what are customers complaining about before renewal" has to read text.
  2. Documents in the domain (PDFs the chat can reason over): *Q1 FY27 Installed Base Review* memo, *Product Lifecycle Bulletin: KS-7000 End of Support*, *Sales Ops Renewal Playbook FY27*.

## Context, built as real assets rather than one bootstrap document
The pipeline normally teaches the domain from a single bootstrap document plus two CSVs. For this
demo the fact-like content is split into assets a steward would actually own and pushed through
Wisdom's **context extraction**, so the glossary and semantic context visibly come *from documents*:
1. **Finance Metric Definitions Standard v3.2** — ARR, NRR, renewal rate, attach rate, bookings vs revenue, fiscal calendar (the "certified definitions").
2. **Business Glossary and Data Ownership Register** — entity definitions, business owner, steward, source system (SAP S/4HANA, Salesforce, ServiceNow, AutoPulse telemetry) and the Snowflake table each maps to.
3. **Data Platform wiki: KEELSTONE_POC onboarding notes** — table semantics, join paths, gotchas and tribal knowledge written by the data engineering team.
4. **#data-help channel export** — a short Slack thread of "which ARR do I use" style questions answered by the stewards.
5. The three PDFs above (memo, bulletin, playbook) are also fed to extraction.
A slim bootstrap keeps only the routing/instruction sections the pipeline needs; `knowledge.csv` holds the as-of date and hero entities; `metrics.csv` carries the certified metrics as expressions over the views. This is the one piece of new pipeline work (an extraction step in `publish`), done during the build.

**Built outcome (2026-10-13):** the seven assets were uploaded to the domain's context extractor (`publish --only extraction`) and the run produced 198 suggestions: 71 knowledge entries and 22 synonym sets were accepted (additive, de-duplicated), while 97 table and column description rewrites were deliberately left **pending** so the demo can show a steward reviewing extracted context in the Context Extractor screen. The same PDFs are also attached as domain documents for chat.

## What the audience sees
1. **Live App "Renewals and Installed Base Cockpit"** — Executive Overview (ARR, renewal rate trend, at-risk ARR by region, cloud commit utilisation) → Scenario Lab (recover a share of Americas East at-risk renewals; migration offer for KS-7000 customers; true-up on under-utilised cloud commits) → Implementation Plan.
2. **Follow-up question**: "Which region's renewal rate has dropped the most this fiscal year and what is driving it and how much ARR is up for renewal there in the next 90 days?" → expected answer: Americas East; roughly 7 points below FY26; KS-7000 end of support and KeelOS 9.14 P1 cases; about $18M renewing in 90 days with about $6M flagged at risk.
3. **Agent "Renewal Risk Watch"** (created disabled): weekly, lists contracts renewing within 90 days that have an open P1 case or an end-of-support product, grouped by region and rep, and posts the summary.
4. **5-minute script** in the Shipping Cockpit format, plus a governance beat: ask for ARR, show the certified definition behind the answer, ask why Sales Ops' number differs.

## Build differences for this demo
- Published to proddemo **Default Organization** (`ET_WORKSPACE_01dc4f2105194dc286b9d69df2a89024`), not Certified Demos.
- Reuses the existing **"Snowflake Demo"** connection (user `WISDOMAI_PROD`, role `WISDOMAI_READ_ONLY`). `KEELSTONE_POC` is added to that connection's database filter **by hand in the browser** (Claude-in-Chrome) rather than by the pipeline, so the shared connection's credentials are never touched.
- Snowflake writes stay inside `KEELSTONE_POC`; grants to `WISDOMAI_READ_ONLY` are generated per the standard pattern.

## Questions for you
- None — reply "go" and the build runs end to end without further questions.
