# Prospect brief (internal input — never rendered, uploaded or named in the demo)

Build a WisdomAI demo domain for Doximity, using synthetic data loaded into Snowflake.

## Who the prospect is
Doximity is a professional network for US physicians, NPs, PAs and pharmacists. Members use it for free. Revenue comes from two customer types: pharma brands that buy targeted marketing campaigns aimed at specific physician specialties, and health systems that buy recruiting and branding placements. Contracts are B2B, often multi year, with scheduled billing milestones, and they get amended frequently (adding campaigns, changing dates, changing price, extending term).

## Who we are demoing to
Sid Sitaram, Chief Accounting Officer. Owns accounting, tax, treasury, SOX, and commercial operations (sales ops, deal desk, financial systems).
Jonathan Giammarco, Director of SOX and Automation. Internal controls and transformation projects.
This is an accounting audience, not FP&A. They care about accuracy, controls, audit trail, and removing duplicated manual review. Keep the framing around integrity of the numbers and efficiency, not forecasting.

## Their systems
Salesforce (CRM, closed won opportunities), NetSuite (ERP, sales orders, billing, revenue), DocuSign (signed contract PDFs), Boomi (syncs Salesforce opportunities into NetSuite sales orders), Alteryx (ad hoc reconciliation work today), Airbase (procurement, not relevant here).

## The use case: three way contract reconciliation
Every closed deal exists in three places that should agree but often don't:
1. The signed contract PDF in DocuSign. This is the legal truth: customer, products or campaigns, total contract value, start and end dates, billing schedule and milestones, payment terms, renewal and cancellation terms, special clauses. It is unstructured.
2. The closed won opportunity in Salesforce. Entered by a sales rep. Amount, close date, products, term.
3. The sales order in NetSuite. Created from Salesforce via Boomi. Drives billing and revenue recognition.

Today three teams each manually reconcile their own slice against the PDF:
- Sales ops checks Salesforce against the contract.
- Revenue accounting checks revenue terms across Salesforce, NetSuite and the contract.
- Billing checks billing schedules and milestones in NetSuite against the contract.
Nobody does the full picture, the work is duplicated, and things still slip through. Amendments are the biggest cause: NetSuite handles them badly, Boomi does not always carry changes across, and the lineage from original contract to latest amendment gets lost.

Sid wants one comprehensive, automated reconciliation that becomes the single source of truth all three teams rely on, so nobody has to re-review.
