# Supply Chain Product Taxonomy Standard v3.0

Letterhead: Pecos Ridge Energy LLC — Supply Chain Management
Owner: VP Supply Chain
Maintained by: Supply Chain Data Steward (Hector Brown)
Approved by: Category managers Jessica Whitaker, Clint Johnson and Hector Brown
Effective: 2025-07-01 (taxonomy version 3.0; applies to every OpenInvoice line from go-live on 2022-01-01)
Warehouse: PECOS_RIDGE_SCM_OPENINVOICE.OPENINVOICE (SCM_PRODUCT_TAXONOMY, SCM_ITEM_CLASSIFICATION)
Classification: Internal

## 1. Purpose

Accounting labels every invoice with a cost code and a supplier category. Those labels are right for the ledger and useless for sourcing: an invoice coded LOE-CHEM from a supplier categorised as "Chemicals" tells a category manager nothing about which chemical was bought, in what pack, at what price per gallon, or whether another qualified supplier sells the same product for less. This standard defines the generic product taxonomy that Supply Chain analyses by, the rule for naming a generic product, the standard unit of measure each product is compared in, how a supplier item is classified to a generic product, and who owns the result. Every spend, price and savings figure Supply Chain publishes must use these definitions. The warehouse implementation is the SCM_PRODUCT_TAXONOMY and SCM_ITEM_CLASSIFICATION tables in the OpenInvoice schema and the V_INVOICE_LINE_CLASSIFIED view that applies them to every invoice line.

## 2. Why the accounting labels are not enough

- OpenInvoice header cost codes are six values: LOE-CHEM (Chemicals - treating), CAP-PROP (Completion - proppant), CAP-OCTG (Drilling - casing and tubulars), CAP-RENT (Rental equipment), LOE-SWD (Water hauling and disposal) and CAP-WTR (Completion - water sourcing and transfer). They say where the cost lands, not what was bought.
- Supplier categories (OI_SUPPLIER.OI_SUPPLIER_CATEGORY and SPEND_INVOICE.SPEND_CATEGORY) are assigned to the vendor, not the line: Chemicals, Sand/Proppant, Tubulars / OCTG, Rental Equipment, Trucking/Water Hauling, Other. A chemical supplier's fuel surcharge and technician hours are "Chemicals" too.
- The supplier item description on the line is a marketing name plus a pack: "CorroShield CS-7000 Corrosion Inhibitor 330 gal tote" and "CorroGuard BC-220 CI 55 GAL DRUM" are the same generic product from two suppliers in two packs. Nothing in SPEND_INVOICE can tell you that.
- Units differ by supplier for the same product: casing is billed per joint by one distributor and per foot by the next; rentals are billed per day, per week or per month.

## 3. The three levels

The taxonomy has three levels. Every leaf carries a node id of the form SCM-FF-CC-NNN where FF is the family, CC the class within the family and NNN the generic product within the class (SCM_PRODUCT_TAXONOMY.TAXONOMY_NODE_ID).

| Level | Column | What it is | Example |
|---|---|---|---|
| 1 Family | LEVEL1_FAMILY | The sourcing category a category manager owns | Production & completion chemicals |
| 2 Class | LEVEL2_CLASS | The functional group inside the family | Corrosion control |
| 3 Generic product | GENERIC_PRODUCT_NAME | The supplier-neutral product or service whose unit price can be compared across suppliers | Corrosion inhibitor, water-soluble, filming amine |

Spend is analysed at level 3. Levels 1 and 2 are roll-ups and are never used to compare prices because they mix products with different standard units.

## 4. Naming rule for generic products

A generic product name is written as noun, qualifier, specification, separated by commas or by the trade convention for tubulars:

- Noun first: what it is (Corrosion inhibitor; Scale inhibitor; Regional sand; Production casing; Frac tank rental; Produced water hauling).
- Qualifier second: the attribute that changes its use or price class (water-soluble; phosphonate; squeeze grade; delivered; 500 bbl).
- Specification last: the attribute that makes two supplier items interchangeable (filming amine; continuous injection; 100 mesh; 5-1/2 in 20 lb/ft P-110 BTC).
- Tubulars follow the mill convention instead: type, OD, weight per foot, grade, connection (Production casing 5-1/2 in 20 lb/ft P-110 BTC).
- No supplier names, trade marks or part numbers ever appear in a generic product name. CorroShield, CorroGuard, FracMax, MP-100 and RL100 are supplier items, not generic products.
- The KEY_SPEC_ATTRIBUTES column records the attributes a steward must confirm from the spec sheet before mapping an item (mesh size and crush rating for sand; OD, weight, grade and connection for OCTG; active content and solubility for chemicals).
- The PRIMARY_USE and USE_PHASE columns (Drilling, Completion, Production, Facilities) state what the product is for; questions phrased by use ("what do we spend on corrosion treatment" or "completion-phase consumables") resolve through them.

## 5. Standard unit of measure and conversions

Every generic product has one standard UOM (SCM_PRODUCT_TAXONOMY.STANDARD_UOM). Supplier items are invoiced in their own pack or unit; SCM_ITEM_CLASSIFICATION.CONVERSION_FACTOR_TO_STD_UOM holds the number of standard units in one invoiced unit. Standard quantity = QUANTITY x conversion factor; standard unit price = LINE_AMOUNT_USD / standard quantity. All supplier comparisons, benchmarks and savings use the standard unit price.

| Standard UOM | Used for | Invoiced unit | Conversion factor | Note |
|---|---|---|---|---|
| GAL | Liquid chemicals | GAL (bulk delivery) | 1 | Bulk tanker or transport delivery |
| GAL | Liquid chemicals | TOTE | 330 | 330 gal IBC tote |
| GAL | Liquid chemicals | DRUM | 55 | 55 gal drum |
| GAL | Liquid chemicals | PAIL | 5 | 5 gal pail |
| LB | Dry chemicals (gel breaker) | BAG | 50 | 50 lb bag |
| TON | Proppant and proppant logistics | TON | 1 | Short ton delivered or FOB |
| FT | Casing, tubing and line pipe | FT | 1 | Per foot |
| FT | Casing | JT | 42 | Range 3 casing joint (42 ft average) |
| FT | Tubing | JT | 31 | Range 2 tubing joint (31 ft average) |
| EA | Accessories, wellheads, valves, fees | EA | 1 | Each |
| DAY | Rental equipment | DAY | 1 | Per day |
| DAY | Rental equipment | WEEK | 7 | Weekly rate |
| DAY | Rental equipment | MONTH | 30 | Monthly rate |
| BBL | Water hauling, disposal, sourcing, transfer | BBL | 1 | Per barrel |
| HR | Vac truck, hot oil, standby, technician time | HR | 1 | Per hour |

Fees and surcharges (family 06) have a nominal EA or HR unit and are never expressed as a unit price of the product they ride on; they are reported as a separate family and excluded from the unit-price views.

## 6. Classification methods and review statuses

A classification is one row of SCM_ITEM_CLASSIFICATION keyed by supplier (LIFNR) and SUPPLIER_ITEM_CODE. It records the generic product (TAXONOMY_NODE_ID), the conversion factor, how the mapping was made, the evidence and the review status.

| CLASSIFICATION_METHOD | Meaning | Typical confidence |
|---|---|---|
| Rule | The item code matches a pattern from a loaded price book or a supplier catalogue (for example every CS-7000-x code of Corrosion Control Chem LLC) | 1.00 |
| Spec sheet review | A steward read the supplier technical data sheet or mill data sheet and confirmed the key spec attributes | 1.00 |
| Steward | Manual mapping by the data steward or a category manager from the description and the field ticket | 0.85 to 1.00 |
| ML suggested | A model proposed the mapping from the description; it waits in the queue until a steward approves it | 0.50 to 0.90 |

| REVIEW_STATUS | Meaning | Counts as classified |
|---|---|---|
| Approved | A steward or category manager approved the mapping | Yes |
| Needs review | An ML suggestion or a low-confidence steward mapping awaiting approval | No |
| Unclassified | No generic product could be assigned (vague description, no spec, no price book) | No |

Only Approved rows count as classified spend. An invoice line with no classification row at all is treated exactly like Unclassified. V_INVOICE_LINE_CLASSIFIED carries IS_CLASSIFIED = 1 only for Approved rows and shows "Unclassified" in the family, class and generic product columns otherwise.

## 7. Governance

| Family | Category manager | Steward |
|---|---|---|
| Production & completion chemicals | Jessica Whitaker | Hector Brown |
| Water logistics | Jessica Whitaker | Hector Brown |
| Proppant | Clint Johnson | Hector Brown |
| OCTG & wellhead | Clint Johnson | Hector Brown |
| Downhole & artificial lift | Clint Johnson | Hector Brown |
| Rental equipment | Hector Brown | Hector Brown |
| Fees & surcharges | Hector Brown | Hector Brown |
| MRO & consumables | Hector Brown | Hector Brown |

- The steward queue is V_UNCLASSIFIED_SPEND: every invoice line without an approved generic product, with its supplier, description, amount and the current review status. The steward works it by line amount descending.
- Service level: a Needs review item is dispositioned within ten business days of its first invoice; a new supplier item with more than 25,000 USD of spend in the current year must be classified before the next monthly category review.
- Target: no more than 5 percent of current-year line spend unclassified. At the end of Q3 2026 the backlog stands at about 8 percent of 2026 line spend, concentrated in rental equipment and distributor items whose descriptions carry no specification (MISC SUPPLIES, PART# 44-1093, RENTAL EQUIP PER TICKET).
- Evidence: every Rule and Spec sheet review mapping cites the supplier technical data sheet, MSA Exhibit B pricing schedule or OCTG mill data sheet in SOURCE_DOCUMENT; the documents live in the supplier document archive.
- Change control: new generic products are added by the owning category manager and published in a numbered taxonomy version; mappings are never deleted, they are superseded with a new CLASSIFIED_DATE.

## 8. Families and classes

| Family code | Family | Category manager | Classes (generic products) | Leaves |
|---|---|---|---|---|
| 01 | Production & completion chemicals | Jessica Whitaker | Corrosion control (2); Scale control (2); Paraffin & asphaltene (2); Gas treating (2); Microbial control (2); Separation (2); Flow assurance (2); Completion fluids (4) | 18 |
| 02 | Proppant | Clint Johnson | Regional sand (2); Northern white sand (1); Coated proppant (1); Proppant logistics (1) | 5 |
| 03 | OCTG & wellhead | Clint Johnson | Casing (4); Tubing (2); Casing accessories (2); Wellhead (1) | 9 |
| 04 | Rental equipment | Hector Brown | Tanks (2); Power & light (2); Pressure control (2); Site & crew (2); Surface lines (1) | 9 |
| 05 | Water logistics | Jessica Whitaker | Produced water (2); Frac water (2); Field service trucks (2) | 6 |
| 06 | Fees & surcharges | Hector Brown | Logistics fees (2); Service fees (3) | 5 |
| 07 | Downhole & artificial lift | Clint Johnson | Rod lift (2); Valves (2) | 4 |
| 08 | MRO & consumables | Hector Brown | Shop & safety (2); Pipe & fittings (1) | 3 |

## 9. Generic product catalogue (taxonomy v3.0)

Benchmark prices are the Supply Chain 2025 reference price per standard UOM used in category reviews (SCM_PRODUCT_TAXONOMY.BENCHMARK_PRICE_USD_PER_STD_UOM); fees carry no benchmark. "Alt." marks products Supply Chain considers substitutable across qualified suppliers (ALTERNATE_SUPPLIER_ELIGIBLE).

| Node id | Generic product | Std UOM | Use phase | Primary use | 2025 benchmark per std UOM | Alt. |
|---|---|---|---|---|---|---|
| SCM-01-01-001 | Corrosion inhibitor, water-soluble, filming amine | GAL | Production | Continuous or batch treatment of tubing and flowlines against CO2/H2S corrosion | $16.40 | Yes |
| SCM-01-01-002 | Corrosion inhibitor, oil-soluble, batch | GAL | Production | Batch treatment of oil wells and gathering lines | $18.90 | Yes |
| SCM-01-02-001 | Scale inhibitor, phosphonate, continuous injection | GAL | Production | Prevents carbonate and sulfate scale in tubing and surface equipment | $13.60 | Yes |
| SCM-01-02-002 | Scale inhibitor, squeeze grade | GAL | Production | Downhole squeeze treatments | $15.20 | Yes |
| SCM-01-03-001 | Paraffin solvent, aromatic | GAL | Production | Dissolves paraffin deposits in tubing and flowlines | $9.40 | Yes |
| SCM-01-03-002 | Paraffin dispersant / inhibitor, continuous | GAL | Production | Keeps paraffin in suspension; continuous injection | $11.80 | Yes |
| SCM-01-04-001 | H2S scavenger, triazine | GAL | Production | Removes H2S from produced gas and oil to meet pipeline spec | $10.70 | Yes |
| SCM-01-04-002 | Oxygen scavenger, sulfite | GAL | Production | Removes dissolved oxygen in injection and frac water | $6.90 | Yes |
| SCM-01-05-001 | Biocide, glutaraldehyde | GAL | Completion | Controls sulfate-reducing bacteria in produced and frac water | $12.30 | Yes |
| SCM-01-05-002 | Biocide, THPS | GAL | Production | Low-toxicity biocide for water systems | $14.10 | Yes |
| SCM-01-06-001 | Demulsifier, oil-treating | GAL | Production | Breaks water-in-oil emulsions at the tank battery | $19.60 | Yes |
| SCM-01-06-002 | Water clarifier, reverse demulsifier | GAL | Production | Removes oil from produced water before disposal | $15.90 | Yes |
| SCM-01-07-001 | Foamer / surfactant, gas-well deliquification | GAL | Production | Unloads liquids from gas wells | $13.20 | Yes |
| SCM-01-07-002 | Methanol, hydrate inhibitor | GAL | Production | Prevents hydrates in gas lines and wellheads in winter | $2.95 | Yes |
| SCM-01-08-001 | Friction reducer, slickwater | GAL | Completion | Reduces friction pressure in slickwater fracs | $7.40 | Yes |
| SCM-01-08-002 | Hydrochloric acid 15%, spearhead | GAL | Completion | Breaks down near-wellbore damage ahead of the frac | $2.15 | Yes |
| SCM-01-08-003 | Clay stabilizer, KCl substitute | GAL | Completion | Prevents clay swelling in the formation | $9.80 | Yes |
| SCM-01-08-004 | Gel breaker, oxidizer | LB | Completion | Breaks crosslinked gel after the frac | $3.10 | Yes |
| SCM-02-01-001 | Regional sand, 100 mesh | TON | Completion | Primary proppant for slickwater stages | $64.00 | Yes |
| SCM-02-01-002 | Regional sand, 40/70 mesh | TON | Completion | Tail-in proppant for slickwater stages | $71.00 | Yes |
| SCM-02-02-001 | Northern white sand, 30/50 mesh | TON | Completion | Higher-conductivity tail-in for deeper, higher-stress wells | $88.00 | Yes |
| SCM-02-03-001 | Resin-coated sand, 20/40 mesh | TON | Completion | Flowback control in high-rate gas wells | $162.00 | Yes |
| SCM-02-04-001 | Proppant last-mile logistics, mine to pad | TON | Completion | Trucking and transloading from mine or transload to the frac pad | $21.00 | Yes |
| SCM-03-01-001 | Surface casing 13-3/8 in 54.5 lb/ft J-55 BTC | FT | Drilling | Surface hole casing string | $52.50 | Yes |
| SCM-03-01-002 | Intermediate casing 9-5/8 in 40 lb/ft L-80 BTC | FT | Drilling | Intermediate casing string | $57.80 | Yes |
| SCM-03-01-003 | Production casing 5-1/2 in 20 lb/ft P-110 BTC | FT | Drilling | Production casing / lateral string for horizontal wells | $42.60 | Yes |
| SCM-03-01-004 | Production casing 5-1/2 in 17 lb/ft P-110 BTC | FT | Drilling | Lighter production string for shallower laterals | $38.90 | Yes |
| SCM-03-02-001 | Production tubing 2-7/8 in 6.5 lb/ft L-80 EUE | FT | Completion | Production tubing string | $15.80 | Yes |
| SCM-03-02-002 | Production tubing 2-3/8 in 4.7 lb/ft J-55 EUE | FT | Production | Tubing for shallow and Hugoton wells | $9.90 | Yes |
| SCM-03-03-001 | Casing centralizer, bow-spring | EA | Drilling | Centralises casing for cement placement | $68.00 | Yes |
| SCM-03-03-002 | Float equipment, shoe and collar | EA | Drilling | Float shoe and collar for cementing | $1,450.00 | Yes |
| SCM-03-04-001 | Wellhead assembly, 5M, multibowl | EA | Drilling | Casing head, spools and tubing head | $38,500.00 | Yes |
| SCM-04-01-001 | Frac tank rental, 500 bbl | DAY | Completion | Temporary fluid storage on location | $58.00 | Yes |
| SCM-04-01-002 | Mud / cuttings tank rental | DAY | Drilling | Drilling fluid and cuttings containment | $85.00 | Yes |
| SCM-04-02-001 | Light tower rental | DAY | Drilling | Night lighting on location | $44.00 | Yes |
| SCM-04-02-002 | Generator rental, 100 kW | DAY | Drilling | Temporary power for pads and crew quarters | $215.00 | Yes |
| SCM-04-03-001 | Flowback iron and manifold package rental | DAY | Completion | Choke manifold, iron and separators during flowback | $1,180.00 | Yes |
| SCM-04-03-002 | BOP stack rental, 5M | DAY | Completion | Blowout preventer for workovers and completions | $740.00 | Yes |
| SCM-04-04-001 | Office / crew trailer rental | DAY | Drilling | Company man and crew quarters | $72.00 | Yes |
| SCM-04-04-002 | Telehandler / forklift rental | DAY | Drilling | Material handling on location | $365.00 | Yes |
| SCM-04-05-001 | Temporary surface line rental, lay-flat | DAY | Completion | Water transfer and flowback lines | $29.00 | Yes |
| SCM-05-01-001 | Produced water hauling, truck | BBL | Production | Trucking produced water from tank battery to disposal | $1.34 | Yes |
| SCM-05-01-002 | Saltwater disposal fee, third-party SWD | BBL | Production | Disposal fee at third-party SWD well | $0.58 | Yes |
| SCM-05-02-001 | Fresh / brackish water sourcing, frac | BBL | Completion | Water purchased for completions | $0.46 | Yes |
| SCM-05-02-002 | Water transfer, pumping and lay-flat | BBL | Completion | Moving frac water from source or pit to the pad | $0.39 | Yes |
| SCM-05-03-001 | Vacuum truck service | HR | Production | Pit, tank and spill cleanup by vac truck | $138.00 | Yes |
| SCM-05-03-002 | Hot oil truck service | HR | Production | Hot oiling tubing and flowlines for paraffin | $172.00 | Yes |
| SCM-06-01-001 | Fuel surcharge | EA | Production | Fuel index surcharge on trucking and delivered material | n/a | No |
| SCM-06-01-002 | Delivery / freight charge | EA | Production | Freight on delivered material | n/a | No |
| SCM-06-02-001 | Environmental / disposal fee | EA | Production | Container and residue handling fee | n/a | No |
| SCM-06-02-002 | Standby / waiting time | HR | Production | Crew or truck standby billed hourly | n/a | No |
| SCM-06-02-003 | Minimum charge / mobilization | EA | Production | Minimum invoice or mobilization charge | n/a | No |
| SCM-07-01-001 | Sucker rod, 7/8 in grade D | EA | Production | Rod string for beam-pumped wells | $78.40 | Yes |
| SCM-07-01-002 | Rod pump insert, 2 in | EA | Production | Downhole insert pump for rod lift | $1,850.00 | Yes |
| SCM-07-02-001 | Gate valve 2 in 2000 psi | EA | Production | Wellhead and flowline isolation | $640.00 | Yes |
| SCM-07-02-002 | Ball valve 2 in threaded | EA | Production | Flowline and tank battery isolation | $185.00 | Yes |
| SCM-08-01-001 | Shop supplies and consumables, misc | EA | Production | Catch-all for distributor consumables (gloves, rags, hardware) | n/a | No |
| SCM-08-01-002 | PPE and safety supplies | EA | Production | Gloves, glasses, FR clothing, gas-monitor consumables | n/a | Yes |
| SCM-08-02-001 | Line pipe and fittings, 2-4 in | FT | Facilities | Flowline pipe, fittings and unions | $6.80 | Yes |

## 10. Applying the standard to OpenInvoice lines

- The generic product is not stored on OI_INVOICE_LINE. It is reached by joining SCM_ITEM_CLASSIFICATION on LIFNR and SUPPLIER_ITEM_CODE and then SCM_PRODUCT_TAXONOMY on TAXONOMY_NODE_ID. V_INVOICE_LINE_CLASSIFIED does this for every line and adds STD_QUANTITY, STD_UNIT_PRICE_USD, IS_CLASSIFIED and the benchmark; it is the starting point for any product or price question.
- Classified spend = SUM(LINE_AMOUNT_USD) where IS_CLASSIFIED = 1. Unclassified spend = SUM(LINE_AMOUNT_USD) where IS_CLASSIFIED = 0 (V_UNCLASSIFIED_SPEND). Unclassified share = unclassified spend / total line spend for the period.
- Standard unit price for a supplier and product over a period is volume weighted: SUM(LINE_AMOUNT_USD) / SUM(STD_QUANTITY), never an average of line unit prices. V_GENERIC_PRODUCT_PRICE_MONTHLY publishes it by generic product, supplier and invoice month.
- Price dispersion for a generic product and year = (highest supplier standard unit price / lowest supplier standard unit price - 1) x 100. Savings at best observed price = SUM over suppliers of (supplier standard unit price - lowest supplier standard unit price) x supplier standard quantity. Both are published in V_SUPPLIER_ALTERNATIVES for alternate-supplier-eligible products only.
- Pack premium = standard unit price of a small pack (drum or pail) / standard unit price of the tote or bulk delivery of the same supplier item family - 1.
- Pricebook variance applies only to lines matched to a loaded price book (PRICEBOOK_ITEM_ID not null): PRICE_VARIANCE_USD = (UNIT_PRICE_USD - PRICEBOOK_RATE_USD) x QUANTITY, positive when invoiced above contract (V_PRICEBOOK_VARIANCE).
- Fees and surcharges (family 06) are excluded from every unit-price, dispersion and savings figure and reported as their own family.
- Delivered versus FOB: a proppant generic product is priced delivered to pad. Where a supplier invoices FOB mine and bills last-mile trucking as a separate line, the trucking line is classified to Proppant last-mile logistics, mine to pad (SCM-02-04-001) and must be added back before the supplier is compared with delivered pricing.

## 11. Change log

- v3.0 (2025-07-01): generic product names rewritten to the noun, qualifier, specification rule; standard UOM and conversion factors made mandatory on every classification; Fees & surcharges split out as family 06; benchmark prices added for the 2025 category reviews.
- v2.1 (2024-01-15): Water logistics separated from Rental equipment; casing and tubing joints given fixed conversion factors (42 ft and 31 ft).
- v2.0 (2023-01-01): classes introduced under each family; review statuses Approved, Needs review and Unclassified adopted.
- v1.0 (2022-01-01): first family-level taxonomy published with the OpenInvoice go-live.
