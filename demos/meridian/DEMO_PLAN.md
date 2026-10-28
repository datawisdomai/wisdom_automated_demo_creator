# Demo Plan: Meridian Clinician Network — Three-Way Contract Reconciliation

**Prospect / vertical:** Doximity conversation (Technology — professional network for clinicians) · **Persona:** Chief Accounting Officer, with the Director of SOX and Automation, Revenue Accounting, Billing and Deal Desk alongside · **As-of date:** 2026-09-30 (Q3 2026 quarter end; the close starts tomorrow)

## The story in one paragraph
Meridian Clinician Network is a free professional network for US physicians, nurse practitioners,
physician assistants and pharmacists. Revenue is B2B: pharma brands buy specialty-targeted campaigns
and sponsored content; health systems buy recruiting placements and employer branding. Contracts are
multi-year, milestone- or schedule-billed, and amended constantly. Every closed deal exists in three
places that should agree and often do not: the signed agreement in DocuSign (the legal truth), the
closed-won opportunity in Salesforce (entered by the rep) and the NetSuite sales order (created by
Boomi; it drives billing and revenue recognition). Today Sales Ops, Revenue Accounting and Billing each
reconcile their own slice by hand in Alteryx, nobody does the full match, and amendments are the biggest
leak. The demo shows Wisdom doing the first complete three-way match live from the raw systems, using
the control matrix as its rulebook, with a review workflow the three teams share and an agent that
re-runs the checks on every new signature. Nothing here names the prospect.

## Story arcs (what the data will prove)
| # | Arc | Hero entity | Target numbers the data will contain |
|---|---|---|---|
| CP1 (hero) | **The three-way match at Q3 close.** About 270 live contract chains; 15–20% fail at least one of the eleven checks; the dollar exposure on open findings is over $5M; at least 15 findings are High severity. | the 2026-09-30 match | mismatch rate 0.15–0.22; exposure ≥ $5M; High ≥ 15 |
| CP2 | **A chain of amendments.** Halvorsen Therapeutics (pharma): MSA Feb 2025 at $1.80M → Amendment 1 Jun 2025 (+Sponsored Content, $2.25M; Boomi created a second NetSuite order) → Amendment 2 Nov 2025 (term +6 months, $2.85M, billing changed Quarterly → Milestone) → Amendment 3 Jul 2026 (campaign price reduced, $2.73M, Net 45). Salesforce reflects Amendment 2 only; NetSuite reflects Amendment 1 only (original end date, quarterly, Net 30, duplicate order). Across the book ≥ 20 amended chains where NetSuite still carries stale terms; amended chains fail checks ≥ 2.5× as often as unamended ones. | Halvorsen Therapeutics | 3 amendments; NetSuite 2 behind, Salesforce 1 behind; hero exposure ≥ $400k; stale amended chains ≥ 20; ratio ≥ 2.5 |
| CP3 | **Billing milestones missing from NetSuite.** ≥ 60 contract milestones (≥ $3M) have no NetSuite bill within 7 days for the same amount; concentrated in milestone-billed amended chains. | milestone-billed chains | missing ≥ 60; ≥ $3M |
| CP4 | **Who owns what.** Findings split across Revenue, Sales Ops and Billing per the control matrix (each between 20% and 45%); pharma brands carry ≥ 60% of the variance dollars; account owner Dana Whitfield (Pharma East) has a finding rate at least twice the average (rounds amounts, drops line items). | Dana Whitfield | team shares 0.20–0.45; pharma ≥ 0.6 of variance $; Whitfield ≥ 2× average |

Seeded discrepancy mix (~48 chains, some compound; four compound chains including the hero): Salesforce amount vs contract TCV ~10, NetSuite end date stale after an extension ~7, billing frequency or milestone amounts ~8, payment terms ~5, amendment never reached NetSuite ~8, amendment only in DocuSign ~3, missing links (order with no opportunity id, opportunity with no or wrong contract number) ~4, product line count ~5, duplicate sales orders ~3, truncated NetSuite billing schedules ~6.

## Data (Snowflake `MERIDIAN_POC.ANALYTICS`)
- Dimensions (3): `CUSTOMERS` (~140: 85 pharma brands, 55 health systems; type, segment, account owner, region), `PRODUCTS` (8 campaign and placement products), `RECONCILIATION_CONTROLS` (the rulebook: one row per check with the systems compared, tolerance, default severity, owning team, SOX control reference and a plain-English description).
- DocuSign extraction (3): `CONTRACTS` (400 agreements: ~270 originals and ~130 amendments; an amendment row restates the full agreement — TCV, dates, terms, exhibits), `CONTRACT_LINE_ITEMS` (~1,000), `CONTRACT_BILLING_SCHEDULE` (~1,400 milestones).
- Salesforce replica (2): `SALESFORCE_OPPORTUNITIES` (~380 closed-won; an amendment is its own opportunity booked for the incremental amount; the contract link is sometimes null or wrong), `SALESFORCE_OPPORTUNITY_PRODUCTS` (~950).
- NetSuite replica (3): `NETSUITE_SALES_ORDERS` (~300; one order per chain unless Boomi duplicated it; opportunity id sometimes missing; Boomi sync timestamp), `NETSUITE_SALES_ORDER_LINES` (~800), `NETSUITE_BILLING_SCHEDULE` (~1,300 bills).
- `DATA_DICTIONARY`.
- Views (4, join helpers only, **no status column**): `V_CONTRACT_CHAIN` (one row per original agreement with its latest version: current TCV, end date, payment terms, billing frequency, amendment count), `V_AMENDMENT_LINEAGE` (one row per version in a chain with the restated values and the change versus the previous version), `V_DEAL_CROSSWALK` (chain → Salesforce opportunity → NetSuite sales order, broken links kept as nulls), `V_CHAIN_SYSTEM_SUMMARY` (the three systems side by side per chain: contract, Salesforce and NetSuite values with nothing compared).
- There is **no precomputed results table**. The eleven checks live in one SQL module shared by the validation suite and the certified query library, so what the demo is validated against is exactly what Wisdom runs.
- Documents: *Q2 2026 Close Memo: Contract Reconciliation Findings* (Revenue Accounting), *Order-to-Cash Reconciliation Policy and Control Matrix* (SOX), *Boomi Sync Incident Bulletin 2026-03*.
- Context assets (through the context extractor, never as CSV): Reconciliation Metric Definitions Standard v1.4, Business Glossary and Ownership Register, Data Platform wiki onboarding notes for MERIDIAN_POC, a #close-reconciliation channel export, plus the three documents; the pipeline adds a dbt semantic-layer YAML, the certified query library and an analyst handbook rendered from the local definitions.
- Stretch, after everything else: the Halvorsen chain and about twenty other agreements rendered as PDFs, uploaded to the S3 bucket and attached to the domain; the 3-run eval; Domain Health analysis left running.

## What the audience sees
1. **Live App "Contract Reconciliation Review"** — Findings Queue (Wisdom runs the eleven checks against the raw tables; one row per finding with the three system values, the variance, severity, owning team, SOX control and the reason; filters by team, severity, customer type, account owner, check type; a summary strip with total findings, exposure and the team split) → Case Review (evidence side by side: contract terms and amendment chain, the Salesforce opportunity, the NetSuite order and billing schedule, the differing field highlighted; a decision per finding — Confirmed, Rejected, Needs follow-up — with a note and the system to correct; decisions persist within the session; Halvorsen is the obvious first case) → Export (a JSON blob of the reviewed findings, shown and copyable, framed as what would be written back to Snowflake, NetSuite or a ticketing system; nothing is written).
2. **Follow-up question**: "Show me the full amendment lineage for Halvorsen Therapeutics and where Salesforce and NetSuite each stand relative to the latest amendment and what the dollar exposure is" → expected answer: three amendments, latest TCV about $2.73M; Salesforce at Amendment 2 (about $2.85M booked, Amendment 3 missing); NetSuite at Amendment 1 (about $2.25M, original end date, quarterly, Net 30, two orders); exposure roughly $480k against NetSuite plus about $120k overstated in Salesforce.
3. **Agent "Amendment Sync Watch"** (created disabled): every weekday morning runs the same checks restricted to agreements signed or amended in the last 7 days and posts new findings grouped by owning team.
4. **5-minute script** in the Shipping Cockpit format, with a controls beat: from any finding, show the SOX control it maps to and the definition behind the check.

## Build differences for this demo
- Published to proddemo **Default Organization**, reusing the **"Snowflake Demo"** connection; `MERIDIAN_POC` is added to its database filter by hand in the browser so the shared connection's credentials are never touched by the pipeline.
- Scope order at the user's request: structured path first (DDL → data → load → context → reviewed queries → publish → Live App → chat → agent → script → report); PDFs in S3, the 3-run eval and Domain Health only once everything else is done.

## Built outcome (2026-10-16)
- Snowflake `MERIDIAN_POC.ANALYTICS`: 12 tables (428 signed documents on 270 agreements) and 4 helper views; CP1–CP4 pass in DuckDB and Snowflake; the compact roll-up union agrees with the full union on every check.
- The three-way match at 2026-09-30: 149 findings on 54 of 270 agreements (20.0%), $30.4M exposure, 85 High; Sales Ops 35 / Revenue Accounting 23 / Billing 91 findings; Halvorsen Therapeutics 11 findings and $2.32M exposure; Dana Whitfield 16 of 35 agreements (46%, 2.3× the overall rate).
- Domain `ET_DOMAIN_97f519e3d9f943179957fd72ebbbf0ec` in Default Organization on the "Snowflake Demo" connection (filter extended in the browser). Context extraction (batched, max 3 files per run, concurrent): 27/27 metrics, 40/41 library queries, 188 knowledge entries; 357 suggestions accepted, 197 left pending for the steward-review beat. The certified query library was slimmed from 308 KB to 113 KB after the first full run stalled.
- Live App "Contract Reconciliation Review" (`app_99d32a563228427a884b41a537fe5d13`): Findings Queue → Case Review → Export, numbers identical to the data.
- Follow-up chat `dd7f4372-9f1a-49a2-a63f-7c7d14172863` (and `8a662247-489b-4c7d-919e-85674ef54183`): four versions, Salesforce one amendment behind, NetSuite two behind, 11 findings and the exposure, from the live match.
- Agent "Amendment Sync Watch" (`AGENT_9ca79491-0366-4e7b-965e-1b030c1461ab`), draft, 5 nodes.
- Stretch done: 78 contract PDFs (Halvorsen chain + 20 agreements) rendered from the data and uploaded to s3://wisdom-proddemo/meridian_contracts/contracts/; Wisdom S3 connection "Meridian Clinician Network Contract Archive" (`et-connection-6dc77f2c90d7487ebe8ebb896d97f28e`) and dataset `ET_DATASET_7ecd633c5c2c4150b0bfa35076153235` attached to the domain, 78 files crawled.

## Questions for you
- None — approved 2026-10-15; the build runs end to end without further questions.
