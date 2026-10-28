# Meridian Clinician Network — demo story guide

As-of 2026-09-30 (Q3 2026 quarter end). Expected answers come from the certified check queries (recon_sql.py) and are asserted by checks.py.

## Opening (warm-up) questions
1. "What reconciliation checks do we run and which team owns each one?" → the 11-row control matrix with SOX refs (RC-01..RC-11).
2. "How many agreements fail the three-way match and what is the total dollar exposure?" → ~52 of 270 agreements (≈19%), ≈ $31M exposure, ≈ 90 High findings.
3. "Which discrepancies belong to the Revenue team versus Billing versus Sales Ops?" → three rows; Billing carries most exposure dollars (missing milestones), Revenue Accounting the amendment and duplicate-order findings, Sales Ops the TCV and product-count findings.

## Hero arc (CP2): Halvorsen Therapeutics
- "Show me the full amendment lineage for Halvorsen Therapeutics and where each system is relative to the latest amendment." → versions 0..3; Salesforce Yes/Yes/Yes/No; NetSuite Yes/Yes/No/No; TCV 1.80M → 2.25M → 2.85M → 2.73M; end date extended to 2027-02-28 at A2; Net 45 at A3.
- "What findings does the Halvorsen Therapeutics agreement have and what is the dollar exposure?" → TCV_MISMATCH (−120k), AMENDMENT_NOT_IN_SALESFORCE, TERM_END_DATE_MISMATCH, AMENDMENT_NOT_IN_NETSUITE (+480k), DUPLICATE_SALES_ORDERS, PAYMENT_TERMS_MISMATCH, BILLING_FREQUENCY_MISMATCH, 4 × MISSING_BILLING_MILESTONE (500k, 600k, 400k, 217.5k).
- "Compare the billing schedule in the latest Halvorsen amendment with what NetSuite will actually bill." → milestones 1–4 matched (quarterly bills carried forward), milestones 5–8 unmatched.

## Other arcs
- CP1: "Which closed won deals do not reconcile across all three systems?" → ~52 agreements ranked by exposure.
- CP2 (book-wide): "Show me every contract with amendments where NetSuite still reflects the original terms." → ≥ 20 amended agreements with what is stale.
- CP3: "Which billing milestones in the contract are missing from the NetSuite billing schedule?" → ≥ 60 milestones, ≥ $3M.
- CP4: "Which account owners have the most mismatches?" → Dana Whitfield first (≈ 40% of her agreements, ≈ 2× the overall rate). "Show total contract value by customer type where Salesforce and the contract disagree and by how much." → pharma dominates.
- Trend: "How does the mismatch rate trend by the month the latest document was signed and do amendments drive it?" → amended agreements drive almost all findings; signings after the 2026-03-01 Boomi upgrade are worse.

## Follow-up (chat) question
"Show me the full amendment lineage for Halvorsen Therapeutics and where Salesforce and NetSuite each stand relative to the latest amendment and what the dollar exposure is" → see demo.yaml `chat.expected_points`.

## Agent
"Which agreements signed or amended in the last 7 days have findings and which team owns each one?" → findings on agreements with latest_signed_date ≥ 2026-09-23, grouped by owning team.
