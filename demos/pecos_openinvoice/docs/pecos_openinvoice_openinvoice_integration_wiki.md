# OpenInvoice Integration — Data Platform Wiki

Space: Data Platform / Supply Chain Analytics
Page owner: Data Platform integration team, with the Supply Chain Data Steward (Hector Brown) for the SCM_* tables
Last edited: 2026-10-02
Audience: category managers, AP analysts, completions and drilling engineers, and anyone querying PECOS_RIDGE_SCM_OPENINVOICE

## What this schema is

PECOS_RIDGE_SCM_OPENINVOICE.OPENINVOICE is the warehouse copy of the Enverus OpenInvoice e-invoicing platform for the five supply-chain managed categories (Chemicals, Sand/Proppant, Tubulars / OCTG, Rental Equipment, Trucking/Water Hauling), plus the two Supply Chain master-data tables that give every line a generic product. It is the twenty-seventh source in the Pecos Ridge "O&G" domain and follows the same convention as the others: one database per source system, one system-named schema. OI_* tables mirror OpenInvoice objects; SCM_* tables are Supply Chain master data; V_* views are the curated layer.

Snapshot: invoices dated 2022-01-01 (OpenInvoice go-live) to 2026-09-30 (the as-of date). The line level is what makes this source different from PECOS_RIDGE_PROCUREMENT_SCM.SCM.SPEND_INVOICE: spend analytics holds one amount per invoice; OpenInvoice holds the supplier item, quantity, unit of measure and unit price on every line.

## The flow: field ticket to invoice to Coupa to SAP

- A supplier delivers material, performs a service or has equipment on rent and raises a field ticket in OpenInvoice (OI_FIELD_TICKET). The company man or foreman approves or rejects it in the field against a well (CORP_WELL_ID), a pad and either an AFE (capital work) or a Quorum property (lease operating expense).
- The supplier bills approved tickets on an invoice (OI_INVOICE with its OI_INVOICE_LINE rows). PO-backed material lines carry a PO_NUMBER and no ticket. Fees and surcharges are their own lines.
- Where the supplier has a loaded price book (OI_PRICEBOOK_ITEM), OpenInvoice matches each line to the contract rate in force on the service date and records the rate and the variance on the line. Lines above contract are Disputed or Short-paid by AP.
- The invoice routes to Coupa for company approval (COUPA_DOC_ID on every invoice since go-live) and posts to SAP S/4HANA. Payment date flows back from SAP.
- Spend analytics (SPEND_INVOICE) receives one row per posted invoice from SAP, not from OpenInvoice.

## The January 2025 ERP id stamping

Until the end of 2024 the only key shared between an OpenInvoice header and its SPEND_INVOICE row was the Coupa document id, and matching through Coupa is a two-hop lookup that AP maintained by hand. The January 2025 integration upgrade closed the loop: SAP returns the spend-analytics invoice id (SPEND_INVOICE.INVOICE_ID, format INV-nnnnnnn) and the integration writes it onto the OpenInvoice header as OI_INVOICE.ERP_INVOICE_ID.

| Invoice date | ERP_INVOICE_ID | ERP_MATCH_STATUS | How to join to SPEND_INVOICE |
|---|---|---|---|
| 2025-01-01 onward | Populated | Stamped | OI_INVOICE.ERP_INVOICE_ID = SPEND_INVOICE.INVOICE_ID; INVOICE_TOTAL_USD = AMOUNT_USD; INVOICE_DATE = INVOICE_DATE |
| Before 2025-01-01 | NULL | Legacy - Coupa id only | Through COUPA_DOC_ID in AP's Coupa extract; not a direct warehouse join |

For stamped invoices the totals tie exactly: INVOICE_TOTAL_USD equals the sum of its LINE_AMOUNT_USD rows and equals SPEND_INVOICE.AMOUNT_USD. That is the control the load validates every refresh.

## Tables

| Table | Grain | Key columns | Notes |
|---|---|---|---|
| OI_SUPPLIER | one row per supplier onboarded to OpenInvoice | OI_SUPPLIER_ID (OIS-nnnnn), LIFNR, SUPPLIER_NAME, OI_SUPPLIER_CATEGORY, ONBOARDED_DATE, EINVOICE_ENABLED, PRICEBOOK_LOADED, PRIMARY_BASIN, PAYMENT_TERMS, SUPPLIER_STATUS | LIFNR is the SAP vendor number with leading zeros; SUPPLIER_NAME is the registered name in title case; PRICEBOOK_LOADED is TRUE only for the hero chemical, proppant and hauling suppliers |
| SCM_PRODUCT_TAXONOMY | one row per generic product (leaf) | TAXONOMY_NODE_ID (SCM-FF-CC-NNN), LEVEL1_FAMILY, LEVEL2_CLASS, GENERIC_PRODUCT_NAME, PRIMARY_USE, USE_PHASE, STANDARD_UOM, KEY_SPEC_ATTRIBUTES, UNSPSC_CODE, ALTERNATE_SUPPLIER_ELIGIBLE, CATEGORY_MANAGER, BENCHMARK_PRICE_USD_PER_STD_UOM, TAXONOMY_VERSION | Taxonomy v3.0: 8 families, 59 generic products; see the Supply Chain Product Taxonomy Standard |
| OI_PRICEBOOK_ITEM | one row per supplier item per price book version | PRICEBOOK_ITEM_ID (PBI-nnnnnn), OI_SUPPLIER_ID, LIFNR, CLM_CONTRACT_ID, PRICEBOOK_VERSION, SUPPLIER_ITEM_CODE, UOM, CONTRACT_RATE_USD, EFFECTIVE_FROM, EFFECTIVE_TO, ESCALATION_PCT, SOURCE_DOCUMENT, LOADED_DATE | The rate is per invoiced UOM (per tote, per drum, per ton), not per standard UOM; SOURCE_DOCUMENT names the MSA Exhibit B pricing schedule in the supplier document archive |
| SCM_ITEM_CLASSIFICATION | one row per supplier item (LIFNR + SUPPLIER_ITEM_CODE) | CLASSIFICATION_ID (CLS-nnnnnn), LIFNR, SUPPLIER_ITEM_CODE, SUPPLIER_ITEM_DESCRIPTION, INVOICED_UOM, TAXONOMY_NODE_ID, CONVERSION_FACTOR_TO_STD_UOM, CLASSIFICATION_METHOD, CONFIDENCE, SOURCE_DOCUMENT, CLASSIFIED_BY, CLASSIFIED_DATE, REVIEW_STATUS, STEWARD_NOTE | The crosswalk from marketing name to generic product; only REVIEW_STATUS = Approved counts as classified; TAXONOMY_NODE_ID is NULL while Unclassified |
| OI_FIELD_TICKET | one row per field ticket | FIELD_TICKET_ID (FT-nnnnnnn), OI_SUPPLIER_ID, LIFNR, TICKET_NUMBER, TICKET_DATE, TICKET_TYPE, CORP_WELL_ID, PAD_ID, PROPERTY_NUMBER, AFE_NUMBER, BASIN, APPROVED_BY, APPROVED_TS, APPROVAL_STATUS, TICKET_TOTAL_USD, OI_INVOICE_ID | TICKET_TYPE is Delivery, Service or Rental; OI_INVOICE_ID is NULL for Rejected tickets |
| OI_INVOICE | one row per supplier invoice | OI_INVOICE_ID (OI-YYYY-nnnnnn), SUPPLIER_INVOICE_NUMBER, OI_SUPPLIER_ID, LIFNR, SUPPLIER_NAME_AS_SUBMITTED, INVOICE_DATE, SUBMITTED_TS, APPROVED_DATE, PAID_DATE, INVOICE_STATUS, SOURCE_LEDGER, OI_SUPPLIER_CATEGORY, COST_CODE, PO_NUMBER, AFE_NUMBER, PROPERTY_NUMBER, CORP_WELL_ID, PAD_ID, BASIN, BUSINESS_UNIT, SUBTOTAL_USD, SURCHARGES_USD, INVOICE_TOTAL_USD, LINE_COUNT, COUPA_DOC_ID, ERP_INVOICE_ID, ERP_MATCH_STATUS, APPROVER_NAME, DISPUTE_REASON | INVOICE_TOTAL_USD = SUBTOTAL_USD + SURCHARGES_USD = sum of the lines; INVOICE_STATUS is Paid, Approved, Submitted, Disputed, On hold - coding or Rejected; COST_CODE is one of LOE-CHEM, CAP-PROP, CAP-OCTG, CAP-RENT, LOE-SWD, CAP-WTR |
| OI_INVOICE_LINE | one row per invoice line | OI_LINE_ID, OI_INVOICE_ID, LINE_NO, FIELD_TICKET_ID, SERVICE_DATE, SUPPLIER_ITEM_CODE, SUPPLIER_ITEM_DESCRIPTION, UOM, QUANTITY, UNIT_PRICE_USD, LINE_AMOUNT_USD, OI_COST_CODE, OI_COST_CODE_DESC, OI_SUPPLIER_CATEGORY, LIFNR, OI_SUPPLIER_ID, AFE_NUMBER, PROPERTY_NUMBER, CORP_WELL_ID, PAD_ID, BASIN, PRICEBOOK_ITEM_ID, PRICEBOOK_RATE_USD, PRICE_VARIANCE_USD, LINE_STATUS, APPROVER_NAME, DISPUTE_REASON | The generic product is NOT on this table; LINE_AMOUNT_USD = QUANTITY x UNIT_PRICE_USD; LINE_STATUS is Approved, Disputed or Short-paid |
| DATA_DICTIONARY | one row per column | TABLE_NAME, COLUMN_NAME, DESCRIPTION, EXAMPLE_VALUE | Business meaning, units and join hints for every column |

## Views and when to use which

| View | Grain | Use it for | Do not use it for |
|---|---|---|---|
| V_INVOICE_LINE_CLASSIFIED | invoice line | Any product, price, pack-size or supplier question: every line with its header, supplier, approved generic product (or "Unclassified"), STD_QUANTITY, STD_UNIT_PRICE_USD, IS_CLASSIFIED and the benchmark. Start here. | Nothing; it is the base for the other five |
| V_GENERIC_PRODUCT_PRICE_MONTHLY | generic product x supplier x invoice month x basin | Price trends and spend by generic product and supplier over time; volume-weighted AVG_STD_UNIT_PRICE_USD | Fees (excluded) and unclassified lines (excluded) |
| V_SUPPLIER_ALTERNATIVES | generic product x year x supplier | "Who else sells this and what would we save": SUPPLIER_COUNT, VOLUME_SHARE, BEST_STD_UNIT_PRICE_USD, HIGHEST_STD_UNIT_PRICE_USD, SAVINGS_AT_BEST_PRICE_USD, PRICE_DISPERSION_PCT | Products with ALTERNATE_SUPPLIER_ELIGIBLE = FALSE (fees, catch-all nodes); pack-size comparisons within one supplier (use the line view) |
| V_PRICEBOOK_VARIANCE | invoice line matched to a price book | Invoiced price versus contract rate, PRICE_VARIANCE_USD, PRICE_VARIANCE_PCT, IS_OVER_CONTRACT, LINE_STATUS, DISPUTE_REASON, PRICEBOOK_VERSION, CLM_CONTRACT_ID | Suppliers without a loaded price book (they are simply absent) |
| V_UNCLASSIFIED_SPEND | invoice line | The steward queue: lines with no approved generic product, their supplier, description, amount and REVIEW_STATUS | Anything about classified spend |
| V_AFE_PRODUCT_COST | AFE x well x generic product | Capital spend by generic product per AFE and well with STD_QUANTITY and the average standard unit price; the hook for cost per lateral foot and plan comparisons | LOE spend (AFE_NUMBER is NULL on LOE lines, so they are not in this view) |

## Join map to the rest of the Pecos Ridge data

| From (this schema) | To | On | Gives |
|---|---|---|---|
| OI_SUPPLIER.LIFNR, OI_INVOICE.LIFNR | PECOS_RIDGE_MAINT_SAP.S4_PM.S4_VENDOR_LFA1.LIFNR | LIFNR | Vendor master (NAME1, city, state, account group, vendor category, ISN id, blocked flag) |
| OI_INVOICE.ERP_INVOICE_ID | PECOS_RIDGE_PROCUREMENT_SCM.SCM.SPEND_INVOICE.INVOICE_ID | ERP_INVOICE_ID = INVOICE_ID (2025 onward only) | The spend-analytics row: PLATFORM, GL_ACCOUNT, COST_CATEGORY, APPROVAL_STATUS |
| OI_PRICEBOOK_ITEM.CLM_CONTRACT_ID | PECOS_RIDGE_PROCUREMENT_SCM.SCM.CLM_CONTRACT.CLM_CONTRACT_ID | CLM_CONTRACT_ID (CLM-nnnnn) | The Icertis contract: title, type, term, auto-renew, annual value, owner, status |
| OI_INVOICE.CORP_WELL_ID, OI_INVOICE_LINE.CORP_WELL_ID, OI_FIELD_TICKET.CORP_WELL_ID | PECOS_RIDGE_CORP_MDM.MASTER.WELL_MASTER.CORP_WELL_ID | CORP_WELL_ID (PRW-nnnnnn) | Well name, basin, play, county, trajectory, LATERAL_LENGTH_FT, spud and first-production dates, status |
| PAD_ID | PECOS_RIDGE_CORP_MDM.MASTER.PAD.PAD_ID | PAD_ID | Pad name, DSU, county, gathering system |
| AFE_NUMBER (capital invoices and lines) | PECOS_RIDGE_REV_ACCOUNTING.QUORUM_FIN.OD_AFE_HEADER.AFE_NUMBER | AFE_NUMBER (STYY-NNNNNT; suffix D drilling, C completion) | AFE type, date, gross amount, company working interest, status |
| AFE_NUMBER | PECOS_RIDGE_DRILLING_WELLVIEW.WV.WVJOB.AFE_NUMBER | AFE_NUMBER | The WellView job: JOB_TYPE (Drilling or Completion), start and end dates, rig, target and actual days |
| AFE_NUMBER | PECOS_RIDGE_DEV_PLANNING.PLAN.AFE_PROPOSED_LINE.AFE_NUMBER | AFE_NUMBER | Planned estimate by COST_CATEGORY (Proppant, Chemicals, Casing & tubulars, Rentals, Water sourcing/transfer and others) |
| BASIN or BUSINESS_UNIT | PECOS_RIDGE_DEV_PLANNING.PLAN.PLAN_PRODUCTION_CAPEX.BASIN | BASIN and PLAN_MONTH | Plan versions (2026 Budget, 2026 Q2 Reforecast, 2026 Q3 Reforecast) with wells turned in line and D&C capex by month |
| PROPERTY_NUMBER (LOE invoices and lines) | PECOS_RIDGE_FIN_SAP.ZFI_SYSTEM_XWALK.QUORUM_PROPERTY_NUMBER (XWALK_TYPE = WELL) | PROPERTY_NUMBER (NN-NNNNN) | The well behind a property, cost centre and profit centre |
| OI_SUPPLIER.DUNS_NUMBER | PECOS_RIDGE_CORP_MDM.MASTER.COUNTERPARTY_MASTER.DUNS_NUMBER | DUNS_NUMBER | Counterparty legal name, type, HQ state, credit rating (only where the supplier is also a counterparty) |

## Known data quality wrinkles

- Supplier name varies per row. SUPPLIER_NAME_AS_SUBMITTED is whatever the supplier typed ("BASIN CHEMICAL", "Basin Chemical LLC", "Basin Chemical, L.L.C."). Group and filter by LIFNR or by OI_SUPPLIER.SUPPLIER_NAME, never by the submitted name.
- Pre-2025 invoices have no ERP id. ERP_INVOICE_ID is NULL and ERP_MATCH_STATUS is "Legacy - Coupa id only" for every invoice dated before 2025-01-01. A question that ties OpenInvoice to SPEND_INVOICE is answerable in the warehouse for 2025 and 2026 only.
- The generic product is not on the line. OI_INVOICE_LINE carries the supplier item code and description only; the generic product arrives through SCM_ITEM_CLASSIFICATION (LIFNR + SUPPLIER_ITEM_CODE) and only when REVIEW_STATUS is Approved. Use V_INVOICE_LINE_CLASSIFIED.
- Packs and units differ by supplier. A tote is 330 gallons, a drum 55, a pail 5; a Range 3 casing joint is 42 feet and a Range 2 tubing joint 31 feet; rental vendors bill per day, per week (7) or per month (30). UNIT_PRICE_USD is per invoiced unit and is not comparable across suppliers; STD_UNIT_PRICE_USD is.
- Monthly rental lines. "Frac tank rental, 500 bbl, monthly" and "CREW TRAILER MONTHLY" carry QUANTITY in months; the standard quantity is days (x30). Daily rates for the same equipment appear on other vendors' lines, so always compare per day.
- Fees and surcharges are separate lines. Fuel surcharge, delivery, environmental fee, standby and minimum charge are their own lines classified to the Fees & surcharges family; they are summed in OI_INVOICE.SURCHARGES_USD and excluded from V_GENERIC_PRODUCT_PRICE_MONTHLY and V_SUPPLIER_ALTERNATIVES so they do not distort unit prices.
- FOB versus delivered. Monahans Proppant LLC invoices MP-100 FOB mine and bills last-mile trucking (LM-PAD) and transload (TRANSLOAD) as separate lines classified to Proppant last-mile logistics; Kermit Sand Co LLC and Redline Sand LLC invoice delivered. Add the logistics lines back before comparing suppliers.
- LOE versus capital. LOE invoices carry PROPERTY_NUMBER and NULL AFE_NUMBER; capital invoices carry AFE_NUMBER and NULL PROPERTY_NUMBER. SOURCE_LEDGER says which ("LOE" or "AFE actual (capex)").
- The well on an invoice is derived. CORP_WELL_ID, PAD_ID and BASIN on OI_INVOICE and OI_INVOICE_LINE are looked up from the AFE (OD_AFE_HEADER) or the property (ZFI_SYSTEM_XWALK); the supplier never types them. Field tickets carry the well the company man approved against, which is the same well in almost every case.
- Price book coverage is partial. Only the hero chemical, proppant and hauling suppliers have a loaded price book (OI_SUPPLIER.PRICEBOOK_LOADED). Lines for the OCTG distributors and the rental vendors have NULL PRICEBOOK_ITEM_ID and never appear in V_PRICEBOOK_VARIANCE.
- Redline Sand RL100 since February 2026. The RLS-2026 price book loaded on 2026-01-01 with a 2 percent escalation; from February the invoiced unit price for RL100 runs about 8.5 percent above the book rate and most of those lines are Disputed with reason "Unit price above contract rate". This is real supplier behaviour, not a load error.
- Descriptions with no specification. MISC SUPPLIES, PART# 44-1093, RENTAL EQUIP PER TICKET, EQUIPMENT RENTAL - SEE ATTACHED, MATERIAL PER TICKET and the like cannot be classified from the line alone; they sit in V_UNCLASSIFIED_SPEND (about 8 percent of 2026 line spend, more than half of it rental equipment).
- Benchmark prices are 2025 dollars. Contract escalation moved 2026 prices about 3 percent higher and 2022 prices sat about 9 percent lower; compare suppliers within the same year and treat the benchmark as a 2025 reference.
- tablePreview row counts in tools are approximate; count rows with a query.

## Query routing hints

- "What did we pay per gallon / per ton / per foot for X by supplier" → V_INVOICE_LINE_CLASSIFIED filtered on GENERIC_PRODUCT_NAME, grouped by SUPPLIER_NAME (and INVOICED_UOM for pack size), SUM(LINE_AMOUNT_USD) / SUM(STD_QUANTITY).
- "Who else sells X and what would we save" → V_SUPPLIER_ALTERNATIVES by GENERIC_PRODUCT_NAME and INVOICE_YEAR.
- "Price trend for X" → V_GENERIC_PRODUCT_PRICE_MONTHLY by INVOICE_MONTH and SUPPLIER_NAME.
- "Invoiced above contract / disputed / pricebook variance" → V_PRICEBOOK_VARIANCE by SUPPLIER_NAME, INVOICE_YEAR, LINE_STATUS.
- "Unclassified / backlog / steward queue" → V_UNCLASSIFIED_SPEND; share of spend = its SUM(LINE_AMOUNT_USD) over the same period's total in V_INVOICE_LINE_CLASSIFIED.
- "Cost per well / per AFE / per lateral foot" → V_AFE_PRODUCT_COST joined to WELL_MASTER on CORP_WELL_ID (LATERAL_LENGTH_FT) and to WVJOB or OD_AFE_HEADER on AFE_NUMBER.
- "Spend by cost code / by supplier category" (the accounting view) → OI_INVOICE by COST_CODE or OI_SUPPLIER_CATEGORY; it reconciles to SPEND_INVOICE for 2025 onward.
- "Field tickets / who approved" → OI_FIELD_TICKET; "invoice status / days to approve / paid" → OI_INVOICE.

## Refresh and ownership

Nightly extract from OpenInvoice at 02:00 Central; SCM_PRODUCT_TAXONOMY and SCM_ITEM_CLASSIFICATION are published by the Supply Chain Data Steward after each steward queue session. The load validates that every invoice total equals the sum of its lines and that every stamped invoice equals its SPEND_INVOICE amount. Questions about the integration go to the Data Platform team; questions about classifications go to #supply-chain-category. Schema changes come with a DATA_DICTIONARY update in the same change.
