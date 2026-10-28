# Demo Plan: Pecos Ridge OpenInvoice Supply Chain (addition to the digitz "O&G" domain)

**Prospect / vertical:** Jeff's partner request (digitz), upstream oil & gas · **Persona:** Supply Chain Category Manager · **As-of date:** 2026-09-30

## The story in one paragraph
Pecos Ridge Energy already has a 26-database Wisdom domain. Its supply chain team has several years of Enverus OpenInvoice
invoices, but the accounting cost codes and supplier categories on them cannot tell a category manager what was bought,
how much, or at what unit price across suppliers. The demo adds the OpenInvoice line items plus Supply Chain's generic
product taxonomy and item classification. It shows a 20%+ per-gallon gap on the same corrosion inhibitor that spend
analytics shows as one "Chemicals" bucket, catches a sand supplier invoicing above its price book, normalises six
descriptions of the same casing to $/ft, sizes the classification backlog, and ties product spend to lateral feet and
the Q3 reforecast. Nothing in the domain that existed before is changed.

## Story arcs (what the data will prove)
| # | Arc | Hero entity | Target numbers the data will contain |
|---|---|---|---|
| CP1 | Hidden price dispersion on water-soluble corrosion inhibitor | Corrosion Control Chem (CorroShield CS-7000) vs Basin Chemical (CorroGuard BC-220) | supplier gap >= 18% per gallon; pail premium over tote >= 8%; 2025 savings at best observed price >= $500k |
| CP2 | Price-book enforcement | Redline Sand RL100 | >= 30 lines over contract in 2026 (every Redline 2026 invoice), >= $150k variance, >= 50% of them Disputed; Kermit / Monahans within 2% |
| CP3 | Same casing, six descriptions, two UOMs | Production casing 5-1/2 in 20 lb/ft P-110 BTC | >= 5 descriptions, 2 UOMs, >= 12% $/ft spread across distributors |
| CP4 | Classification backlog | Hector Brown's steward queue | 6-10% of 2026 line spend unclassified, >= 50% of it rentals; 2025 share lower |
| CP5 | Operational hook | 2025-26 completion AFEs | >= 40 wells with proppant AFE lines; every stamped invoice equals SPEND_INVOICE to the cent |

## Data (Snowflake `PECOS_RIDGE_SCM_OPENINVOICE.OPENINVOICE`, our account; new connection on digitz)
- Master data: OI_SUPPLIER (real LIFNRs), SCM_PRODUCT_TAXONOMY (59 generic products, v3.0), SCM_ITEM_CLASSIFICATION (~6.3k items), OI_PRICEBOOK_ITEM (~150 rated items, 10 suppliers, real CLM contracts)
- Facts: OI_INVOICE (50,693, 2022-01 → 2026-09; 23,556 stamped with real SPEND_INVOICE ids), OI_INVOICE_LINE (126,980), OI_FIELD_TICKET (49,386)
- Synced reference copies (OpenInvoice's own cost-object lists, verbatim from the partner tables): OI_REF_WELL (1,494), OI_REF_AFE (1,614), OI_REF_VENDOR (316), OI_ERP_INTEGRATION_LOG (23,556). Needed because our database and the partner's 26 live on different Snowflake accounts and one SQL query runs on one connection; Wisdom chat can still join across connections in Python, which is how the WellView and reforecast questions are asked
- Views: V_INVOICE_LINE_CLASSIFIED, V_GENERIC_PRODUCT_PRICE_MONTHLY, V_SUPPLIER_ALTERNATIVES, V_PRICEBOOK_VARIANCE, V_UNCLASSIFIED_SPEND, V_AFE_PRODUCT_COST
- Reference extracts (read-only, paged from the partner's Snowflake through the Wisdom SQL playground): vendors, wells, pads, AFEs, properties, contracts, sourcing events, WellView jobs, proposed AFEs, capex plan, the exact SPEND_INVOICE slice and the 2022-24 calibration aggregates
- Documents in S3 (stretch): supplier technical data sheets, OCTG mill sheets, MSA Exhibit B pricing schedules — cited by SOURCE_DOCUMENT columns
- Context assets (extractor only): taxonomy standard v3, supplier item alias glossary, OpenInvoice integration wiki, supply-chain channel export, chemicals category review memo; plus the generated dbt semantic YAML, certified query library and analyst handbook
- Final step: Domain Health analysis queued on the shared domain and left running for the SE

## What the audience sees
1. **Live App "Pecos Ridge Supply Chain Spend Cube"** — Category Overview → Price Dispersion → Pricebook Variance & Disputes → Classification Queue → Cost per Lateral Foot
2. **Follow-up question**: price per gallon for water-soluble corrosion inhibitor by supplier and pack in 2025 and the saving at the best observed price → two suppliers, Corrosion Control Chem cheaper, small-pack premium, savings > $500k
3. **Agent "Price Variance Watch"** (created disabled): weekly lines > 5% over price book by supplier plus new unclassified spend > $25k
4. **5-minute script** in the Shipping Cockpit format

## Guard rails for the shared domain
Existing-domain mode: the O&G domain is never created, renamed, deleted or re-instructed; a connection this demo did not
create is never updated; extractor files it did not upload are never deleted; suggestions pending before its first upload
are never accepted; teardown keeps the domain.

Approved by Chick on 2026-10-19 (plan file); build runs end to end without further questions.
