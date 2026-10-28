# Pecos Ridge OpenInvoice — demo story guide (five beats)

Persona: Jessica Whitaker, Supply Chain Category Manager (chemicals and water logistics), with Clint Johnson (proppant and OCTG), Hector Brown (data steward), a completions engineer and an AP analyst in the room. As-of 2026-09-30. The thread through all five beats: accounting's cost codes say where the money landed; the generic product taxonomy says what was bought, in what pack, at what unit price, from whom — and that is the context that did not exist in the O&G domain until this addition.

## Beat 1 — CP1: the hidden corrosion inhibitor gap

- Opening question: "What did we pay per gallon for water-soluble corrosion inhibitor by supplier and pack size in 2025, and how much would we have saved at the best observed price?"
- What the answer shows: two suppliers for one generic product (SCM-01-01-001). Corrosion Control Chem LLC (CorroShield CS-7000) at about $16.40 per gallon in totes, about $15.91 in bulk; Basin Chemical LLC (CorroGuard BC-220) at about $19.84 in totes, $21.16 in drums and $23.29 in 5 gal pails. A 20-percent-plus supplier gap and a small-pack premium stacked on top. Savings at the best observed price for 2025 are well over half a million dollars.
- The follow-up: "Why didn't we see this before?" — in SPEND_INVOICE both suppliers are "Chemicals", cost code LOE-CHEM, one amount per invoice. The marketing names and packs only exist on the OpenInvoice line, and the generic product only exists because of SCM_ITEM_CLASSIFICATION. Show the line view, then the Chemicals category review memo and the alias glossary the answer drew on.
- Who cares: Jessica (consolidation and the Q4 RFP), the VP Supply Chain (the number), Finance (why the category total looked flat).

## Beat 2 — CP2: proppant on three pricing bases and a supplier above its price book

- Opening question: "Compare what we paid per ton for 100 mesh regional sand by supplier in 2025 and 2026, and show me Redline's lines against its price book this year."
- What the answer shows: Kermit Sand Co (FracMax 100, delivered to pad, at benchmark), Monahans Proppant (MP-100 FOB mine, looks about 14 percent cheaper until the last-mile trucking lines are added back) and Redline Sand (RL100 delivered, about 11 percent above benchmark). From February 2026 Redline invoiced RL100 about 8.5 percent above its RLS-2026 book rate; most of those lines are Disputed with "Unit price above contract rate".
- The follow-up: "How many of Redline's 2026 lines are over contract and what is the variance in dollars?" — V_PRICEBOOK_VARIANCE by supplier, status and month; link to contract CLM-00044 and the RLS-2026 MSA Exhibit B in the document archive.
- Who cares: Clint (supplier escalation), AP (what to dispute or short-pay), the completions engineer (delivered versus FOB when choosing a mine for a pad).

## Beat 3 — CP3: six ways to say the same casing

- Opening question: "Show every description we've been invoiced for 5-1/2 in 20 lb/ft P-110 BTC production casing, the unit it was billed in, and the price per foot by distributor."
- What the answer shows: six distributor wordings (CSG 5.500 20.00 P110 BTC R3; 5-1/2in 20# P-110 BTC casing, per ft; CASING 5 1/2" 20.00# P-110 BTC RANGE 3 (jt); Prod csg 5.5 x 20 P110 BTC-M, ft; OCTG 5.5 20PPF P110 BUTTRESS R3 PE; 5.500 OD 20# P110 BTC SMLS casing / ft), half billed per 42 ft joint and half per foot. Normalised to dollars per foot against the $42.60 benchmark the spread across distributors is above 12 percent.
- The follow-up: "Which distributors should be in the Q4 OCTG RFQ?" — the per-foot ranking plus volume share; the OCTG mill data sheet is the classification evidence.
- Who cares: Clint and Drilling (the RFQ), Hector (the Spec sheet review method that made this possible).

## Beat 4 — CP4: the classification backlog

- Opening question: "How much of this year's spend has no approved generic product, and where is it concentrated?"
- What the answer shows: about 8 percent of 2026 line spend is unclassified, more than half of it rental equipment, the rest distributor items with no specification in the description (MISC SUPPLIES, PART# 44-1093, RENTAL EQUIP PER TICKET, EQUIPMENT RENTAL - SEE ATTACHED). Needs review items (ML suggestions) sit alongside Unclassified ones; only Approved counts.
- The follow-up: "Which suppliers and descriptions should Hector work first?" — V_UNCLASSIFIED_SPEND by supplier and description, amount descending; the steward SLA and the field-ticket-attachment fix from the channel export.
- Who cares: Hector (the queue), the VP (data quality behind every number in beats 1-3), AP (supplier onboarding requirements).

## Beat 5 — CP5: from invoices to wells, lateral feet and the reforecast

- Opening question: "For the 2025-26 completions, what did we spend per lateral foot by generic product, and what does a 10 percent proppant price increase do against the Q3 reforecast?"
- What the answer shows: V_AFE_PRODUCT_COST rolled up by AFE and well, joined to WellView (WVJOB on AFE_NUMBER), the AFE headers (OD_AFE_HEADER) and the well master (LATERAL_LENGTH_FT) for dollars and tons per lateral foot; the 100 mesh line is the one that moves; the planned side comes from AFE_PROPOSED_LINE (Proppant) and PLAN_PRODUCTION_CAPEX (PLAN_VERSION '2026 Q3 Reforecast'). This beat is the "future step" in the original request: the same keys already in the domain (AFE_NUMBER, CORP_WELL_ID) carry the new line-level spend into operations and planning.
- The follow-up: "Are any of those wells sitting in the steward queue?" — closing the loop to beat 4: unclassified rental lines would understate per-foot cost.
- Who cares: the completions engineer and Planning (the sensitivity), the VP (why line-level spend belongs in the operational domain), Clint (proppant strategy by pad).

## Closing

Show the Domain Health analysis running on the enlarged domain and the agent "Price Variance Watch" (disabled) that would flag new over-contract lines. Leave with the three artefacts the answers cited: the taxonomy standard, the alias glossary and the Q3 chemicals memo.
