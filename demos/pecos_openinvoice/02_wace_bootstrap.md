# Pecos Ridge Energy — OpenInvoice Supply Chain addition to the O&G domain — Domain Bootstrap (wACE)

Demo as-of date: **2026-09-30**. Data spans 2022-01-01 (OpenInvoice go-live) to 2026-09-30.
Warehouse: Snowflake `PECOS_RIDGE_SCM_OPENINVOICE.OPENINVOICE` (new connection "Pecos Ridge OpenInvoice (Snowflake)"). Dialect: Snowflake. Amounts are USD.
This schema is ADDED to the existing Pecos Ridge "O&G" domain (26 source databases: SAP, Quorum, WellView, ProdView, Icertis, planning, MDM …). Keys shared with those sources: LIFNR, CORP_WELL_ID, PAD_ID, AFE_NUMBER, PROPERTY_NUMBER, CLM_CONTRACT_ID, ERP_INVOICE_ID = SPEND_INVOICE.INVOICE_ID.

---

## 1. DOMAIN OVERVIEW

Pecos Ridge Energy LLC is a fictional operator in the Midland, Delaware, Anadarko (SCOOP) and Hugoton basins (business units Midland Basin, Delaware Basin, Midcon, Hugoton). Supply Chain manages five categories through Enverus OpenInvoice: Chemicals, Sand/Proppant, Tubulars / OCTG, Rental Equipment and Trucking/Water Hauling. Suppliers raise field tickets, the field approves them, the supplier invoices with line items, the invoice routes through Coupa and posts to SAP. Spend analytics (PECOS_RIDGE_PROCUREMENT_SCM.SCM.SPEND_INVOICE) holds one amount per invoice with an accounting cost code and a supplier category; it cannot say what was bought, in which pack, at what unit price, or whether another supplier sells the same product for less.

This addition brings the OpenInvoice line items (supplier item code and description, quantity, invoiced UOM, unit price, matched price book rate) and Supply Chain's generic product taxonomy v3.0 (SCM_PRODUCT_TAXONOMY: family > class > generic product with a standard UOM, primary use and use phase) plus the crosswalk SCM_ITEM_CLASSIFICATION that maps each supplier item to a generic product with a conversion factor into the standard UOM. The audience is the Supply Chain Category Manager (Jessica Whitaker for chemicals and water logistics, Clint Johnson for proppant and OCTG, Hector Brown for rentals, fees and MRO and as data steward), with the VP Supply Chain, a completions engineer and an AP analyst as secondary users. Questions are about spend by generic product or use, standard unit price by supplier and pack, price dispersion and savings at the best observed price, price book variance and disputed lines, the unclassified backlog, and completion cost per lateral foot. Answers report what the invoices show; they do not recommend suppliers.

---

## 2. TABLE CATALOG

### 2.1 `OI_SUPPLIER` (dimension)
Suppliers onboarded to OpenInvoice. `OI_SUPPLIER_ID` (OIS-nnnnn), `LIFNR` (SAP vendor number, 10 characters with leading zeros), `SUPPLIER_NAME` (registered name, title case), `SUPPLIER_CITY`, `SUPPLIER_STATE`, `DUNS_NUMBER`, `OI_SUPPLIER_CATEGORY` (Chemicals, Sand/Proppant, Tubulars / OCTG, Rental Equipment, Trucking/Water Hauling, Other), `ONBOARDED_DATE`, `EINVOICE_ENABLED`, `PRICEBOOK_LOADED` (TRUE only for the hero chemical, proppant and hauling suppliers), `PRIMARY_BASIN`, `PAYMENT_TERMS` (NT30/NT45/NT60), `SUPPLIER_STATUS`.

### 2.2 `SCM_PRODUCT_TAXONOMY` (dimension, 59 rows)
Taxonomy v3.0, one row per generic product. `TAXONOMY_NODE_ID` (SCM-FF-CC-NNN), `LEVEL1_FAMILY` (Production & completion chemicals, Proppant, OCTG & wellhead, Rental equipment, Water logistics, Fees & surcharges, Downhole & artificial lift, MRO & consumables), `LEVEL2_CLASS`, `GENERIC_PRODUCT_NAME` (e.g. "Corrosion inhibitor, water-soluble, filming amine"), `PRIMARY_USE`, `USE_PHASE` (Drilling, Completion, Production, Facilities), `STANDARD_UOM` (GAL, LB, TON, FT, EA, DAY, BBL, HR), `KEY_SPEC_ATTRIBUTES`, `UNSPSC_CODE`, `ALTERNATE_SUPPLIER_ELIGIBLE`, `CATEGORY_MANAGER`, `BENCHMARK_PRICE_USD_PER_STD_UOM` (2025 reference; NULL for fees), `TAXONOMY_VERSION`.

### 2.3 `OI_PRICEBOOK_ITEM` (dimension)
Contract rates loaded in OpenInvoice per supplier item and version. `PRICEBOOK_ITEM_ID` (PBI-nnnnnn), `OI_SUPPLIER_ID`, `LIFNR`, `CLM_CONTRACT_ID` (CLM-nnnnn), `PRICEBOOK_VERSION` (CCC-PB-2025A, BSN-PB-2025, KSC-2025H2, MPL-2026, RLS-2026 and their 2024 predecessors), `SUPPLIER_ITEM_CODE`, `SUPPLIER_ITEM_DESCRIPTION`, `UOM` (the pack: TOTE, DRUM, PAIL, GAL, TON, BBL, DAY, HR, EA), `CONTRACT_RATE_USD` (per invoiced UOM), `EFFECTIVE_FROM`, `EFFECTIVE_TO`, `ESCALATION_PCT`, `SOURCE_DOCUMENT` (MSA Exhibit B file name), `LOADED_DATE`.

### 2.4 `SCM_ITEM_CLASSIFICATION` (crosswalk)
One row per supplier item (`LIFNR` + `SUPPLIER_ITEM_CODE`). `CLASSIFICATION_ID` (CLS-nnnnnn), `OI_SUPPLIER_ID`, `SUPPLIER_ITEM_DESCRIPTION`, `INVOICED_UOM`, `TAXONOMY_NODE_ID` (NULL while unclassified), `CONVERSION_FACTOR_TO_STD_UOM` (tote 330, drum 55, pail 5, 50 lb bag 50, casing joint 42, tubing joint 31, week 7, month 30, else 1), `CLASSIFICATION_METHOD` (Rule, Spec sheet review, Steward, ML suggested), `CONFIDENCE`, `SOURCE_DOCUMENT` (spec sheet, pricing exhibit or OCTG mill sheet), `CLASSIFIED_BY`, `CLASSIFIED_DATE`, `REVIEW_STATUS` (Approved, Needs review, Unclassified), `STEWARD_NOTE`.

### 2.5 `OI_FIELD_TICKET` (fact)
`FIELD_TICKET_ID` (FT-nnnnnnn), `OI_SUPPLIER_ID`, `LIFNR`, `TICKET_NUMBER`, `TICKET_DATE`, `TICKET_TYPE` (Delivery, Service, Rental), `CORP_WELL_ID`, `PAD_ID`, `PROPERTY_NUMBER` (LOE), `AFE_NUMBER` (capital), `BASIN`, `APPROVED_BY`, `APPROVED_TS`, `APPROVAL_STATUS` (Approved, Rejected), `TICKET_TOTAL_USD`, `OI_INVOICE_ID` (NULL for rejected tickets).

### 2.6 `OI_INVOICE` (fact)
One row per supplier invoice. `OI_INVOICE_ID` (OI-YYYY-nnnnnn), `SUPPLIER_INVOICE_NUMBER`, `OI_SUPPLIER_ID`, `LIFNR`, `SUPPLIER_NAME_AS_SUBMITTED` (free text, varies), `INVOICE_DATE`, `SUBMITTED_TS`, `APPROVED_DATE`, `PAID_DATE`, `INVOICE_STATUS` (Paid, Approved, Submitted, Disputed, On hold - coding, Rejected), `SOURCE_LEDGER` (AFE actual (capex), LOE), `OI_SUPPLIER_CATEGORY`, `COST_CODE` (LOE-CHEM, CAP-PROP, CAP-OCTG, CAP-RENT, LOE-SWD, CAP-WTR), `PO_NUMBER`, `AFE_NUMBER`, `PROPERTY_NUMBER`, `CORP_WELL_ID` (derived), `PAD_ID`, `BASIN`, `BUSINESS_UNIT`, `SUBTOTAL_USD`, `SURCHARGES_USD`, `INVOICE_TOTAL_USD` (= sum of lines), `LINE_COUNT`, `COUPA_DOC_ID`, `ERP_INVOICE_ID` (= SPEND_INVOICE.INVOICE_ID, 2025 onward), `ERP_MATCH_STATUS` (Stamped, Legacy - Coupa id only), `APPROVER_NAME`, `DISPUTE_REASON`.

### 2.7 `OI_INVOICE_LINE` (fact)
One row per line. `OI_LINE_ID`, `OI_INVOICE_ID`, `LINE_NO`, `FIELD_TICKET_ID`, `SERVICE_DATE`, `SUPPLIER_ITEM_CODE`, `SUPPLIER_ITEM_DESCRIPTION` (marketing name and pack, as invoiced), `UOM` (GAL, TOTE, DRUM, PAIL, BAG, TON, JT, FT, EA, DAY, WEEK, MONTH, BBL, HR), `QUANTITY`, `UNIT_PRICE_USD` (per invoiced unit), `LINE_AMOUNT_USD`, `OI_COST_CODE`, `OI_COST_CODE_DESC`, `OI_SUPPLIER_CATEGORY`, `LIFNR`, `OI_SUPPLIER_ID`, `AFE_NUMBER`, `PROPERTY_NUMBER`, `CORP_WELL_ID`, `PAD_ID`, `BASIN`, `PRICEBOOK_ITEM_ID`, `PRICEBOOK_RATE_USD`, `PRICE_VARIANCE_USD` (positive = above contract), `LINE_STATUS` (Approved, Disputed, Short-paid), `APPROVER_NAME`, `DISPUTE_REASON`. The generic product is NOT on this table.

### 2.8 `DATA_DICTIONARY`
`TABLE_NAME`, `COLUMN_NAME`, `DESCRIPTION`, `EXAMPLE_VALUE`.

---

## 3. ANALYTICAL VIEWS (use these first)

| View | Grain | Use for |
|---|---|---|
| `V_INVOICE_LINE_CLASSIFIED` | invoice line | Every line with header, supplier, approved generic product (or "Unclassified"), `STD_QUANTITY`, `STD_UNIT_PRICE_USD`, `IS_CLASSIFIED`, benchmark, price book rate and variance. Start here for any product, price or pack-size question |
| `V_GENERIC_PRODUCT_PRICE_MONTHLY` | generic product × supplier × invoice month × basin | `SPEND_USD`, `STD_QUANTITY`, volume-weighted `AVG_STD_UNIT_PRICE_USD`, benchmark; classified lines only, fees excluded |
| `V_SUPPLIER_ALTERNATIVES` | generic product × year × supplier | `SUPPLIER_COUNT`, `VOLUME_SHARE`, `BEST_STD_UNIT_PRICE_USD`, `HIGHEST_STD_UNIT_PRICE_USD`, `SAVINGS_AT_BEST_PRICE_USD`, `PRICE_DISPERSION_PCT`; alternate-supplier-eligible products only |
| `V_PRICEBOOK_VARIANCE` | matched invoice line | `PRICEBOOK_RATE_USD`, `PRICE_VARIANCE_USD`, `PRICE_VARIANCE_PCT`, `IS_OVER_CONTRACT`, `LINE_STATUS`, `DISPUTE_REASON`, `PRICEBOOK_VERSION`, `CLM_CONTRACT_ID` |
| `V_UNCLASSIFIED_SPEND` | invoice line | The steward queue: lines with no approved generic product, with supplier, description, amount and `REVIEW_STATUS` |
| `V_AFE_PRODUCT_COST` | AFE × well × generic product | Capital spend, `STD_QUANTITY` and `AVG_STD_UNIT_PRICE_USD` per AFE and well; the hook to WellView, the AFE headers and the well master for cost per lateral foot |

---

## 4. ENTITY RELATIONSHIP MAP

- `OI_SUPPLIER 1 — n OI_INVOICE`, `OI_INVOICE_LINE`, `OI_FIELD_TICKET`, `OI_PRICEBOOK_ITEM`, `SCM_ITEM_CLASSIFICATION` (OI_SUPPLIER_ID; LIFNR carried on every row).
- `OI_INVOICE 1 — n OI_INVOICE_LINE` (OI_INVOICE_ID); `INVOICE_TOTAL_USD` = SUM(`LINE_AMOUNT_USD`).
- `OI_FIELD_TICKET 1 — n OI_INVOICE_LINE` (FIELD_TICKET_ID); `OI_FIELD_TICKET.OI_INVOICE_ID` points back to the invoice it was billed on.
- `OI_INVOICE_LINE n — 1 SCM_ITEM_CLASSIFICATION` on (`LIFNR`, `SUPPLIER_ITEM_CODE`); `SCM_ITEM_CLASSIFICATION n — 1 SCM_PRODUCT_TAXONOMY` (TAXONOMY_NODE_ID). This two-hop join is what gives a line its generic product.
- `OI_INVOICE_LINE n — 1 OI_PRICEBOOK_ITEM` (PRICEBOOK_ITEM_ID; the rate in force on SERVICE_DATE); `OI_PRICEBOOK_ITEM n — 1 CLM_CONTRACT` in PECOS_RIDGE_PROCUREMENT_SCM.SCM (CLM_CONTRACT_ID).
- Cross-database: `LIFNR` → PECOS_RIDGE_MAINT_SAP.S4_PM.S4_VENDOR_LFA1 and PECOS_RIDGE_PROCUREMENT_SCM.SCM.SPEND_INVOICE; `ERP_INVOICE_ID` → SPEND_INVOICE.INVOICE_ID (2025 onward); `CORP_WELL_ID` → PECOS_RIDGE_CORP_MDM.MASTER.WELL_MASTER (LATERAL_LENGTH_FT); `PAD_ID` → PECOS_RIDGE_CORP_MDM.MASTER.PAD; `AFE_NUMBER` → PECOS_RIDGE_REV_ACCOUNTING.QUORUM_FIN.OD_AFE_HEADER, PECOS_RIDGE_DRILLING_WELLVIEW.WV.WVJOB and PECOS_RIDGE_DEV_PLANNING.PLAN.AFE_PROPOSED_LINE; `PROPERTY_NUMBER` → PECOS_RIDGE_FIN_SAP.ZFI_SYSTEM_XWALK.QUORUM_PROPERTY_NUMBER; plan versions in PECOS_RIDGE_DEV_PLANNING.PLAN.PLAN_PRODUCTION_CAPEX.

---

## 5. METRICS DICTIONARY

Certified definitions live in `metrics.csv`. The ones used most (all over `V_INVOICE_LINE_CLASSIFIED` unless stated):
- **total_line_spend_usd** = SUM(LINE_AMOUNT_USD); **invoice_count** = COUNT(DISTINCT OI_INVOICE_ID); **line_count** = COUNT(*).
- **classified_spend_usd** = SUM(LINE_AMOUNT_USD) WHERE IS_CLASSIFIED = 1; **unclassified_spend_usd** = SUM(LINE_AMOUNT_USD) WHERE IS_CLASSIFIED = 0 (`V_UNCLASSIFIED_SPEND`); **unclassified_spend_share_pct** = 100 × unclassified / total.
- **std_quantity** = SUM(STD_QUANTITY); **avg_std_unit_price_usd** = SUM(LINE_AMOUNT_USD) / SUM(STD_QUANTITY) — volume weighted, never AVG of line prices.
- **best_std_unit_price_usd**, **highest_std_unit_price_usd**, **price_dispersion_pct** = (highest / best − 1) × 100, **savings_at_best_price_usd** = Σ (supplier price − best price) × supplier std quantity, **supplier_count**, **volume_share_pct** — from `V_SUPPLIER_ALTERNATIVES` by generic product and year.
- **benchmark_variance_pct** = (avg_std_unit_price_usd / BENCHMARK_PRICE_USD_PER_STD_UOM − 1) × 100.
- **pack_premium_pct** = (std unit price of DRUM or PAIL lines / std unit price of TOTE or GAL lines of the same supplier and product − 1) × 100.
- **pricebook_variance_usd** = SUM(PRICE_VARIANCE_USD), **pricebook_variance_pct** = (UNIT_PRICE_USD / PRICEBOOK_RATE_USD − 1) × 100, **over_contract_line_count** = SUM(IS_OVER_CONTRACT), **over_contract_share_pct**, **disputed_line_count** = COUNT(*) WHERE LINE_STATUS = 'Disputed', **disputed_spend_usd** — from `V_PRICEBOOK_VARIANCE`.
- **stamped_invoice_share_pct** = share of OI_INVOICE rows with ERP_MATCH_STATUS = 'Stamped'; **avg_days_to_approve** = AVG(APPROVED_DATE − INVOICE_DATE); **field_ticket_count** = COUNT(*) over `OI_FIELD_TICKET`.
- **cost_per_lateral_foot_usd** = SUM(V_AFE_PRODUCT_COST.SPEND_USD) / SUM(WELL_MASTER.LATERAL_LENGTH_FT) per well; **proppant_tons_per_lateral_foot** = SUM(STD_QUANTITY for Proppant family) / LATERAL_LENGTH_FT.

---

## 6. SYNONYMS MASTER LIST

- CI, corrosion inhibitor, CorroShield, CS-7000, CorroGuard, BC-220, filming amine → GENERIC_PRODUCT_NAME = 'Corrosion inhibitor, water-soluble, filming amine' (SCM-01-01-001)
- SI, scale inhibitor, ScaleGuard, SG-2200, BasinScale, BS-310 → 'Scale inhibitor, phosphonate, continuous injection' (SCM-01-02-001)
- H2S scavenger, scavenger, triazine, SulfiStop, HS-9000, H2S-Trap, BH-700 → 'H2S scavenger, triazine' (SCM-01-04-001)
- FR, friction reducer → 'Friction reducer, slickwater'; acid, HCl, spearhead → 'Hydrochloric acid 15%, spearhead'; biocide, glut, THPS → the two Biocide nodes
- 100M, 100 mesh, in-basin sand, regional sand, FracMax 100, MP-100, RL100 → 'Regional sand, 100 mesh' (SCM-02-01-001); 40/70, MP-4070, RL4070 → 'Regional sand, 40/70 mesh'; NWS, northern white → 'Northern white sand, 30/50 mesh'; RCS, resin coated → 'Resin-coated sand, 20/40 mesh'
- last mile, LM-PAD, transload, sand trucking → 'Proppant last-mile logistics, mine to pad' (SCM-02-04-001)
- csg, CSG, prod csg, production casing, 5-1/2 20#, 20 ppf P110 → 'Production casing 5-1/2 in 20 lb/ft P-110 BTC' (SCM-03-01-003); tbg, TBG, tubing → the Production tubing nodes; OCTG, tubulars → LEVEL1_FAMILY = 'OCTG & wellhead'
- frac tank → 'Frac tank rental, 500 bbl'; light plant, light tower → 'Light tower rental'; genset, generator → 'Generator rental, 100 kW'; BOP → 'BOP stack rental, 5M'; trailer → 'Office / crew trailer rental'; lay-flat → 'Temporary surface line rental, lay-flat'
- SWD, disposal → 'Saltwater disposal fee, third-party SWD'; water haul, PW haul → 'Produced water hauling, truck'; vac truck → 'Vacuum truck service'; hot oiler → 'Hot oil truck service'
- fuel surcharge, FSC, demurrage, standby, delivery charge, environmental fee, minimum load → LEVEL1_FAMILY = 'Fees & surcharges'
- tote, IBC → INVOICED_UOM = 'TOTE' (330 gal); drum → 'DRUM' (55 gal); pail, bucket → 'PAIL' (5 gal); bulk, transport → 'GAL'; joint, jt → 'JT'
- vendor, supplier, SAP vendor → OI_SUPPLIER by LIFNR; supplier name on the invoice → SUPPLIER_NAME_AS_SUBMITTED (never a key)
- category manager, owner → CATEGORY_MANAGER; steward, Hector → the classification queue (V_UNCLASSIFIED_SPEND)
- generic product, generic name, product family, use, what we bought → GENERIC_PRODUCT_NAME / LEVEL1_FAMILY / PRIMARY_USE / USE_PHASE; marketing name, item description, part number → SUPPLIER_ITEM_DESCRIPTION / SUPPLIER_ITEM_CODE
- cost code, accounting category → OI_COST_CODE / OI_SUPPLIER_CATEGORY (the accounting view)
- standard price, normalised price, price per gallon / ton / foot / day → STD_UNIT_PRICE_USD or AVG_STD_UNIT_PRICE_USD; invoiced price, line price → UNIT_PRICE_USD
- contract rate, book rate, price book, exhibit B → PRICEBOOK_RATE_USD / OI_PRICEBOOK_ITEM; over contract, overbilled, above book → IS_OVER_CONTRACT = 1; disputed → LINE_STATUS = 'Disputed'
- classified, approved mapping → IS_CLASSIFIED = 1; unclassified, backlog, queue, needs review → IS_CLASSIFIED = 0
- stamped, ERP id, INV number → ERP_INVOICE_ID / ERP_MATCH_STATUS = 'Stamped'; legacy → 'Legacy - Coupa id only'; Coupa id → COUPA_DOC_ID
- capex, AFE spend, capital → SOURCE_LEDGER = 'AFE actual (capex)' / AFE_NUMBER; LOE, lease operating, opex → SOURCE_LEDGER = 'LOE' / PROPERTY_NUMBER
- lateral foot, per foot of lateral, $/ft lateral → V_AFE_PRODUCT_COST joined to WELL_MASTER.LATERAL_LENGTH_FT
- Q3 reforecast, reforecast → PLAN_PRODUCTION_CAPEX.PLAN_VERSION = '2026 Q3 Reforecast'; budget → '2026 Budget'
- this year, YTD → INVOICE_YEAR = 2026 (through 2026-09-30); last year → 2025
- Midcon, SCOOP, Anadarko → BASIN = 'Anadarko' / BUSINESS_UNIT = 'Midcon'; Permian → Midland and Delaware

---

## 7. DOMAIN KNOWLEDGE

- The OpenInvoice extract covers invoices dated 2022-01-01 through the as-of date 2026-09-30 for the five supply-chain managed categories: Chemicals; Sand/Proppant; Tubulars / OCTG; Rental Equipment and Trucking/Water Hauling.
- OpenInvoice went live on 2022-01-01 and every invoice since then routes through Coupa (COUPA_DOC_ID) and posts to SAP.
- Since the January 2025 integration upgrade the spend-analytics invoice id (SPEND_INVOICE.INVOICE_ID in the format INV-nnnnnnn) is stamped back onto the OpenInvoice header as ERP_INVOICE_ID and ERP_MATCH_STATUS reads Stamped.
- Invoices dated before 2025-01-01 have no ERP_INVOICE_ID and carry ERP_MATCH_STATUS "Legacy - Coupa id only"; they link to spend analytics only through COUPA_DOC_ID.
- INVOICE_TOTAL_USD always equals the sum of LINE_AMOUNT_USD on the invoice and equals SPEND_INVOICE.AMOUNT_USD for stamped invoices.
- Taxonomy v3.0 (effective 2025-07-01) has 8 families and 59 generic products keyed SCM-FF-CC-NNN; the generic product is the level at which spend and unit prices are compared.
- The water-soluble filming-amine corrosion inhibitor (SCM-01-01-001; standard UOM GAL; 2025 benchmark $16.40 per gallon) is bought from Corrosion Control Chem LLC (LIFNR 0000100039) as CorroShield CS-7000 and from Basin Chemical LLC (LIFNR 0000100040) as CorroGuard BC-220.
- CorroShield CS-7000 sold in 2025 at about $16.40 per gallon in 330 gal totes and about $17.55 in 55 gal drums and about $15.91 as bulk delivery.
- CorroGuard BC-220 sold in 2025 at about $19.84 per gallon in totes and about $21.16 in drums and about $23.29 in 5 gal pails; tote to tote Basin Chemical is about 21 percent above Corrosion Control Chem.
- Savings at the best observed price for the water-soluble corrosion inhibitor in 2025 are well over half a million dollars (V_SUPPLIER_ALTERNATIVES.SAVINGS_AT_BEST_PRICE_USD).
- 100 mesh regional sand (SCM-02-01-001; TON; 2025 benchmark $64 per ton) comes from Kermit Sand Co LLC (FracMax 100 delivered to pad at benchmark) and Monahans Proppant LLC (MP-100 FOB mine about 14 percent below benchmark plus a separate last-mile trucking line) and Redline Sand LLC (RL100 delivered about 11 percent above benchmark).
- From February 2026 Redline Sand LLC (LIFNR 0000100043) invoiced RL100 about 8.5 percent above its RLS-2026 price-book rate and most of those lines are Disputed with reason "Unit price above contract rate".
- Production casing 5-1/2 in 20 lb/ft P-110 BTC (SCM-03-01-003; FT; 2025 benchmark $42.60 per foot) is bought from a long tail of distributors who describe it six different ways and bill per 42 ft joint or per foot; normalised to dollars per foot the spread between distributors is above 12 percent.
- About 8 percent of 2026 line spend has no approved generic product; more than half of it is rental equipment and the rest is distributor items with descriptions such as MISC SUPPLIES or PART# 44-1093 or RENTAL EQUIP PER TICKET.
- Hector Brown is the Supply Chain data steward and owns the classification queue; Jessica Whitaker is category manager for chemicals and water logistics; Clint Johnson owns proppant and OCTG and downhole; Hector Brown also owns rentals and fees and MRO.
- Price books are loaded for the five hero suppliers only and the versions in force at the as-of date are CCC-PB-2025A and BSN-PB-2025 and KSC-2025H2 and MPL-2026 and RLS-2026.

---

## 8. BUSINESS NUANCES

- Only classification rows with REVIEW_STATUS Approved count as classified; Needs review and Unclassified and lines with no classification row all show as Unclassified in V_INVOICE_LINE_CLASSIFIED.
- Never compare UNIT_PRICE_USD across suppliers; compare STD_UNIT_PRICE_USD because packs and units differ (tote 330 gal; drum 55 gal; pail 5 gal; casing joint 42 ft; tubing joint 31 ft; week 7 days; month 30 days).
- A standard unit price over a period is volume weighted: SUM(LINE_AMOUNT_USD) / SUM(STD_QUANTITY); never average line prices.
- Fees and surcharges (LEVEL1_FAMILY = 'Fees & surcharges') are separate lines and are excluded from V_GENERIC_PRODUCT_PRICE_MONTHLY and V_SUPPLIER_ALTERNATIVES; include them only when the question is total invoice spend.
- Monahans Proppant LLC prices MP-100 FOB mine; add its last-mile trucking lines (SCM-02-04-001 Proppant last-mile logistics) before calling it the cheapest 100 mesh supplier.
- Pricebook variance exists only where PRICEBOOK_ITEM_ID is not null; the haulers and the OCTG distributors and the rental vendors have no loaded price book and never appear in V_PRICEBOOK_VARIANCE.
- Positive PRICE_VARIANCE_USD means invoiced above contract; IS_OVER_CONTRACT = 1 marks those lines and LINE_STATUS says whether AP disputed or short-paid them.
- LOE invoices carry PROPERTY_NUMBER and a NULL AFE_NUMBER; capital invoices carry AFE_NUMBER and a NULL PROPERTY_NUMBER; CORP_WELL_ID on an invoice is derived from the AFE or the property and is never typed by the supplier.
- SUPPLIER_NAME_AS_SUBMITTED varies in case and suffix from one invoice to the next; group suppliers by LIFNR or OI_SUPPLIER.SUPPLIER_NAME and never by the submitted name.
- SOURCE_LEDGER values 'AFE actual (capex)' and 'LOE' and the INVOICE_STATUS values Paid / Approved / Submitted / Disputed / On hold - coding / Rejected use the same vocabulary as SPEND_INVOICE.
- Year and month questions use INVOICE_DATE (INVOICE_YEAR and INVOICE_MONTH in the views) and not SERVICE_DATE unless the question is about when the work was done.
- Benchmark prices on the taxonomy are 2025 reference prices; 2026 invoices run about 3 percent higher and 2022 invoices about 9 percent lower through contract escalation so compare suppliers within one year.
- Savings at best observed price is an opportunity figure and not a realised saving; it assumes every supplier's volume could have been bought at the lowest supplier's price that year.
- V_AFE_PRODUCT_COST holds capital lines only because LOE lines have no AFE_NUMBER; cost per lateral foot is a completion-phase capital measure.

---

## 9. TRIBAL KNOWLEDGE

- "CI" in a supply chain question means corrosion inhibitor; "CS-7000" and "BC-220" are the two water-soluble corrosion inhibitors and "the pail problem" is the Basin Chemical 5 gal pail premium.
- "100M" and "100 mesh" and "in-basin sand" and "FracMax 100" and "MP-100" and "RL100" all mean 100 mesh regional sand (SCM-02-01-001).
- "The Redline disputes" means the RL100 lines invoiced above the RLS-2026 price book since February 2026.
- "Prod csg" and "5-1/2 20#" and "20 ppf P110" all mean the 5-1/2 in 20 lb/ft P-110 BTC production casing; a 17 in the weight position means the 17 lb/ft product instead.
- "The queue" or "Hector's backlog" means V_UNCLASSIFIED_SPEND; Hector Brown works it by line amount descending with a ten business day service level on Needs review items.
- "Cost per lateral foot" means V_AFE_PRODUCT_COST spend divided by WELL_MASTER.LATERAL_LENGTH_FT for the well on the AFE; it is asked for completion-phase products on the 2025-26 wells.
- "The Q3 reforecast" means PLAN_VERSION = '2026 Q3 Reforecast' (version date 2026-08-20) in PECOS_RIDGE_DEV_PLANNING.PLAN.PLAN_PRODUCTION_CAPEX; "the plus 10 percent proppant sensitivity" is the Delaware program scenario planning asked for against it.
- "Stamped" means an invoice whose ERP_INVOICE_ID is populated; "legacy" means a pre-2025 invoice with only a Coupa id.
- Supply chain says "supplier" and AP says "vendor"; both mean OI_SUPPLIER by LIFNR.
- Business units are Midland Basin and Delaware Basin and Midcon and Hugoton; the Anadarko basin (SCOOP) belongs to the Midcon business unit.
- The field approves tickets and AP approves invoices; a ticket that was Rejected has no OI_INVOICE_ID.
- The Chemicals category total in spend analytics was flat year over year which is why Finance never saw the corrosion inhibitor gap; the gap only exists at the line and generic product level.
- AFE numbers end in D for drilling AFEs and C for completion AFEs (for example TX24-01057D); completion-phase product cost sits on the C AFE.

---

## 10. QUERY ROUTING HINTS

- Spend or price by generic product or family or use → V_INVOICE_LINE_CLASSIFIED (line grain) or V_GENERIC_PRODUCT_PRICE_MONTHLY (product x supplier x month).
- Which suppliers sell the same product and what would we save → V_SUPPLIER_ALTERNATIVES filtered by GENERIC_PRODUCT_NAME and INVOICE_YEAR; the savings column is SAVINGS_AT_BEST_PRICE_USD and dispersion is PRICE_DISPERSION_PCT.
- Price by pack size → V_INVOICE_LINE_CLASSIFIED grouped by SUPPLIER_NAME and INVOICED_UOM (or SUPPLIER_ITEM_DESCRIPTION) with SUM(LINE_AMOUNT_USD) / SUM(STD_QUANTITY).
- Invoiced above contract or disputed lines or pricebook variance → V_PRICEBOOK_VARIANCE filtered by SUPPLIER_NAME and INVOICE_YEAR; count IS_OVER_CONTRACT and sum PRICE_VARIANCE_USD and group by LINE_STATUS.
- Unclassified spend or steward queue or backlog → V_UNCLASSIFIED_SPEND; the share is its spend over total spend from V_INVOICE_LINE_CLASSIFIED for the same period.
- Casing described different ways → V_INVOICE_LINE_CLASSIFIED where GENERIC_PRODUCT_NAME is the casing name grouped by SUPPLIER_NAME and SUPPLIER_ITEM_DESCRIPTION and INVOICED_UOM with STD_UNIT_PRICE_USD per foot.
- Cost per well or per AFE or per lateral foot → V_AFE_PRODUCT_COST joined to PECOS_RIDGE_CORP_MDM.MASTER.WELL_MASTER on CORP_WELL_ID (LATERAL_LENGTH_FT) and to PECOS_RIDGE_DRILLING_WELLVIEW.WV.WVJOB or PECOS_RIDGE_REV_ACCOUNTING.QUORUM_FIN.OD_AFE_HEADER on AFE_NUMBER.
- Price sensitivity against the plan → V_AFE_PRODUCT_COST for the actual product cost plus PECOS_RIDGE_DEV_PLANNING.PLAN.AFE_PROPOSED_LINE (COST_CATEGORY = 'Proppant') and PLAN_PRODUCTION_CAPEX (PLAN_VERSION = '2026 Q3 Reforecast').
- Supplier attributes or contracts → OI_SUPPLIER joined to PECOS_RIDGE_PROCUREMENT_SCM.SCM.CLM_CONTRACT on LIFNR; vendor master detail from PECOS_RIDGE_MAINT_SAP.S4_PM.S4_VENDOR_LFA1 on LIFNR.
- Does OpenInvoice tie to spend analytics → OI_INVOICE joined to PECOS_RIDGE_PROCUREMENT_SCM.SCM.SPEND_INVOICE on ERP_INVOICE_ID = INVOICE_ID for 2025 onward; before 2025 only COUPA_DOC_ID links them.
- Spend by cost code or supplier category (the accounting view) → OI_INVOICE by COST_CODE or OI_SUPPLIER_CATEGORY; it reconciles to SPEND_INVOICE for 2025 onward.
- Field tickets or approvals or who approved → OI_FIELD_TICKET by TICKET_DATE and APPROVED_BY; join OI_INVOICE_LINE on FIELD_TICKET_ID.
- Invoice status or days to approve or payment → OI_INVOICE (INVOICE_DATE; APPROVED_DATE; PAID_DATE; INVOICE_STATUS).
- Column meanings → DATA_DICTIONARY.
