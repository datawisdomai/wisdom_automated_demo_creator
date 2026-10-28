# Supplier Item Alias Glossary

Letterhead: Pecos Ridge Energy LLC — Supply Chain Management
Owner: Supply Chain Data Steward (Hector Brown)
Reviewed by: Jessica Whitaker (chemicals and water logistics), Clint Johnson (proppant and OCTG)
Last review: 2026-09-26
Scope: supplier item codes and descriptions on OpenInvoice lines (OI_INVOICE_LINE.SUPPLIER_ITEM_CODE and SUPPLIER_ITEM_DESCRIPTION) and their approved generic product in SCM_ITEM_CLASSIFICATION
Classification: Internal

## How to read this glossary

Suppliers print their own marketing names, part numbers and pack sizes on invoice lines. This glossary lists, for the suppliers Supply Chain manages most closely, what each item is as invoiced, the pack it comes in, how many standard units one invoiced unit represents (SCM_ITEM_CLASSIFICATION.CONVERSION_FACTOR_TO_STD_UOM) and the generic product it is approved to in taxonomy v3.0. Prices quoted in the notes are the supplier's 2025 standard-unit price level relative to the Supply Chain benchmark; 2026 prices run about 3 percent higher under the escalation clauses and 2022 prices were about 9 percent lower. Supplier names below are the OpenInvoice registered names (OI_SUPPLIER.SUPPLIER_NAME); the name typed on an invoice (OI_INVOICE.SUPPLIER_NAME_AS_SUBMITTED) varies in case and suffix and should never be used as a key. Use LIFNR.

## Corrosion Control Chem LLC (LIFNR 0000100039, Liberal KS, contract CLM-00040)

The lower-priced corrosion inhibitor supplier. Price book CCC-PB-2025A loaded; e-invoicing enabled since the 2022 go-live.

| Supplier | Item code | Description as invoiced | Pack / UOM | Conversion to std UOM | Generic product (node id) | Note |
|---|---|---|---|---|---|---|
| Corrosion Control Chem LLC | CS-7000-T | CorroShield CS-7000 Corrosion Inhibitor 330 gal tote | TOTE (330 GAL) | 330 | Corrosion inhibitor, water-soluble, filming amine (SCM-01-01-001) | About $16.40 per GAL in 2025 (at the 2025 benchmark of $16.40) |
| Corrosion Control Chem LLC | CS-7000-D | CorroShield CS-7000 Corrosion Inhibitor 55 gal drum | DRUM (55 GAL) | 55 | Corrosion inhibitor, water-soluble, filming amine (SCM-01-01-001) | About $17.55 per GAL in 2025 (about 7% above the 2025 benchmark of $16.40) |
| Corrosion Control Chem LLC | CS-7000-B | CorroShield CS-7000 bulk delivery (gal) | GAL | 1 | Corrosion inhibitor, water-soluble, filming amine (SCM-01-01-001) | About $15.91 per GAL in 2025 (about 3% below the 2025 benchmark of $16.40) |
| Corrosion Control Chem LLC | CS-7100-D | CorroShield CS-7100 Oil-Soluble Batch Inhibitor 55 gal drum | DRUM (55 GAL) | 55 | Corrosion inhibitor, oil-soluble, batch (SCM-01-01-002) | About $19.28 per GAL in 2025 (about 2% above the 2025 benchmark of $18.90) |
| Corrosion Control Chem LLC | SG-2200-T | ScaleGuard SG-2200 Phosphonate Scale Inhibitor tote | TOTE (330 GAL) | 330 | Scale inhibitor, phosphonate, continuous injection (SCM-01-02-001) | About $13.33 per GAL in 2025 (about 2% below the 2025 benchmark of $13.60) |
| Corrosion Control Chem LLC | PX-500-D | ParaClear PX-500 Aromatic Solvent 55 gal drum | DRUM (55 GAL) | 55 | Paraffin solvent, aromatic (SCM-01-03-001) | About $9.40 per GAL in 2025 (at the 2025 benchmark of $9.40) |
| Corrosion Control Chem LLC | HS-9000-T | SulfiStop HS-9000 Triazine Scavenger 330 gal tote | TOTE (330 GAL) | 330 | H2S scavenger, triazine (SCM-01-04-001) | About $11.02 per GAL in 2025 (about 3% above the 2025 benchmark of $10.70) |
| Corrosion Control Chem LLC | BG-25-D | BioGard 25% Glutaraldehyde 55 gal drum | DRUM (55 GAL) | 55 | Biocide, glutaraldehyde (SCM-01-05-001) | About $12.30 per GAL in 2025 (at the 2025 benchmark of $12.30) |
| Corrosion Control Chem LLC | DM-410-D | DemulsiMax DM-410 Oil Treater 55 gal drum | DRUM (55 GAL) | 55 | Demulsifier, oil-treating (SCM-01-06-001) | About $19.40 per GAL in 2025 (about 1% below the 2025 benchmark of $19.60) |
| Corrosion Control Chem LLC | FM-30-T | FoamLift FM-30 Surfactant tote | TOTE (330 GAL) | 330 | Foamer / surfactant, gas-well deliquification (SCM-01-07-001) | About $13.33 per GAL in 2025 (about 1% above the 2025 benchmark of $13.20) |
| Corrosion Control Chem LLC | MEOH-B | Methanol 99% bulk (gal) | GAL | 1 | Methanol, hydrate inhibitor (SCM-01-07-002) | About $2.95 per GAL in 2025 (at the 2025 benchmark of $2.95) |
| Corrosion Control Chem LLC | FR-77-B | FlowRite FR-77 Friction Reducer bulk (gal) | GAL | 1 | Friction reducer, slickwater (SCM-01-08-001) | About $7.25 per GAL in 2025 (about 2% below the 2025 benchmark of $7.40) |
| Corrosion Control Chem LLC | HCL15-B | 15% HCl Inhibited Acid bulk (gal) | GAL | 1 | Hydrochloric acid 15%, spearhead (SCM-01-08-002) | About $2.15 per GAL in 2025 (at the 2025 benchmark of $2.15) |
| Corrosion Control Chem LLC | SVC-TECH | Field technician service call (hr) | HR | 1 | Standby / waiting time (SCM-06-02-002) | Fee or service line; excluded from unit-price views |
| Corrosion Control Chem LLC | ENV-FEE | Environmental / container fee | EA | 1 | Environmental / disposal fee (SCM-06-02-001) | Fee or service line; excluded from unit-price views |
| Corrosion Control Chem LLC | FUEL-SC | Fuel surcharge | EA | 1 | Fuel surcharge (SCM-06-01-001) | Fee or service line; excluded from unit-price views |

## Basin Chemical LLC (LIFNR 0000100040, Liberal KS, contract CLM-00041)

Premium-priced supplier with a heavy share of small packs. Price book BSN-PB-2025 loaded. Note the inconsistent capitalisation of its descriptions ("CorroGuard BC-220 CI 55 GAL DRUM" and "CORROGUARD BC-220 5 GAL PAIL" are the same product family).

| Supplier | Item code | Description as invoiced | Pack / UOM | Conversion to std UOM | Generic product (node id) | Note |
|---|---|---|---|---|---|---|
| Basin Chemical LLC | BC-220-T | CorroGuard BC-220 CI 330 GAL TOTE | TOTE (330 GAL) | 330 | Corrosion inhibitor, water-soluble, filming amine (SCM-01-01-001) | About $19.84 per GAL in 2025 (about 21% above the 2025 benchmark of $16.40) |
| Basin Chemical LLC | BC-220-D | CorroGuard BC-220 CI 55 GAL DRUM | DRUM (55 GAL) | 55 | Corrosion inhibitor, water-soluble, filming amine (SCM-01-01-001) | About $21.16 per GAL in 2025 (about 29% above the 2025 benchmark of $16.40) |
| Basin Chemical LLC | BC-220-P | CORROGUARD BC-220 5 GAL PAIL | PAIL (5 GAL) | 5 | Corrosion inhibitor, water-soluble, filming amine (SCM-01-01-001) | About $23.29 per GAL in 2025 (about 42% above the 2025 benchmark of $16.40) |
| Basin Chemical LLC | BC-240-D | CorroGuard BC-240 OS Batch 55 GAL DRUM | DRUM (55 GAL) | 55 | Corrosion inhibitor, oil-soluble, batch (SCM-01-01-002) | About $21.17 per GAL in 2025 (about 12% above the 2025 benchmark of $18.90) |
| Basin Chemical LLC | BS-310-T | BasinScale BS-310 Inhibitor TOTE | TOTE (330 GAL) | 330 | Scale inhibitor, phosphonate, continuous injection (SCM-01-02-001) | About $14.82 per GAL in 2025 (about 9% above the 2025 benchmark of $13.60) |
| Basin Chemical LLC | BS-320-D | BasinScale BS-320 Squeeze 55 GAL DRUM | DRUM (55 GAL) | 55 | Scale inhibitor, squeeze grade (SCM-01-02-002) | About $15.81 per GAL in 2025 (about 4% above the 2025 benchmark of $15.20) |
| Basin Chemical LLC | BP-150-D | Basin ParaSolv BP-150 55 GAL DRUM | DRUM (55 GAL) | 55 | Paraffin solvent, aromatic (SCM-01-03-001) | About $10.15 per GAL in 2025 (about 8% above the 2025 benchmark of $9.40) |
| Basin Chemical LLC | BP-160-T | Basin ParaFlow BP-160 Dispersant TOTE | TOTE (330 GAL) | 330 | Paraffin dispersant / inhibitor, continuous (SCM-01-03-002) | About $11.80 per GAL in 2025 (at the 2025 benchmark of $11.80) |
| Basin Chemical LLC | BH-700-T | Basin H2S-Trap BH-700 TOTE | TOTE (330 GAL) | 330 | H2S scavenger, triazine (SCM-01-04-001) | About $11.34 per GAL in 2025 (about 6% above the 2025 benchmark of $10.70) |
| Basin Chemical LLC | BO-65-T | Basin O2-Scav 65% Bisulfite TOTE | TOTE (330 GAL) | 330 | Oxygen scavenger, sulfite (SCM-01-04-002) | About $6.90 per GAL in 2025 (at the 2025 benchmark of $6.90) |
| Basin Chemical LLC | BB-50-D | BasinCide BB-50 THPS 55 GAL DRUM | DRUM (55 GAL) | 55 | Biocide, THPS (SCM-01-05-002) | About $14.38 per GAL in 2025 (about 2% above the 2025 benchmark of $14.10) |
| Basin Chemical LLC | BW-90-T | Basin WaterClear BW-90 TOTE | TOTE (330 GAL) | 330 | Water clarifier, reverse demulsifier (SCM-01-06-002) | About $16.38 per GAL in 2025 (about 3% above the 2025 benchmark of $15.90) |
| Basin Chemical LLC | BF-20-T | Basin FoamUp BF-20 TOTE | TOTE (330 GAL) | 330 | Foamer / surfactant, gas-well deliquification (SCM-01-07-001) | About $13.86 per GAL in 2025 (about 5% above the 2025 benchmark of $13.20) |
| Basin Chemical LLC | BC-CLAY-B | Basin ClayLock 70 bulk (gal) | GAL | 1 | Clay stabilizer, KCl substitute (SCM-01-08-003) | About $9.80 per GAL in 2025 (at the 2025 benchmark of $9.80) |
| Basin Chemical LLC | BC-BRK-50 | Basin BreakOut AP Oxidizer 50 lb bag | BAG (50 LB) | 50 | Gel breaker, oxidizer (SCM-01-08-004) | About $3.10 per LB in 2025 (at the 2025 benchmark of $3.10) |
| Basin Chemical LLC | SVC-TECH | Chemical technician field service (hr) | HR | 1 | Standby / waiting time (SCM-06-02-002) | Fee or service line; excluded from unit-price views |
| Basin Chemical LLC | DELIV | Delivery charge | EA | 1 | Delivery / freight charge (SCM-06-01-002) | Fee or service line; excluded from unit-price views |
| Basin Chemical LLC | FUEL-SC | Fuel surcharge | EA | 1 | Fuel surcharge (SCM-06-01-001) | Fee or service line; excluded from unit-price views |

## Proppant: Kermit Sand Co LLC (0000100041, CLM-00042), Monahans Proppant LLC (0000100042, CLM-00043), Redline Sand LLC (0000100043, CLM-00044)

Three mines sell 100 mesh regional sand on three pricing bases: Kermit delivered to pad, Monahans FOB mine with a separate last-mile trucking line, Redline delivered at a premium. Price books KSC-2025H2, MPL-2026 and RLS-2026 are loaded.

| Supplier | Item code | Description as invoiced | Pack / UOM | Conversion to std UOM | Generic product (node id) | Note |
|---|---|---|---|---|---|---|
| Kermit Sand Co LLC | FM100-DLV | FracMax 100 mesh, delivered to pad (ton) | TON | 1 | Regional sand, 100 mesh (SCM-02-01-001) | About $64.00 per TON in 2025 (at the 2025 benchmark of $64.00) |
| Kermit Sand Co LLC | FM4070-DLV | FracMax 40/70, delivered to pad (ton) | TON | 1 | Regional sand, 40/70 mesh (SCM-02-01-002) | About $71.00 per TON in 2025 (at the 2025 benchmark of $71.00) |
| Kermit Sand Co LLC | NW3050-DLV | Northern White 30/50 delivered (ton) | TON | 1 | Northern white sand, 30/50 mesh (SCM-02-02-001) | About $88.00 per TON in 2025 (at the 2025 benchmark of $88.00) |
| Kermit Sand Co LLC | DEMUR | Truck demurrage / standby (hr) | HR | 1 | Standby / waiting time (SCM-06-02-002) | Fee or service line; excluded from unit-price views |
| Kermit Sand Co LLC | FUEL-SC | Fuel surcharge | EA | 1 | Fuel surcharge (SCM-06-01-001) | Fee or service line; excluded from unit-price views |
| Monahans Proppant LLC | MP-100 | MP-100 Permian Regional Sand FOB Monahans (ton) | TON | 1 | Regional sand, 100 mesh (SCM-02-01-001) | About $55.04 per TON in 2025 (about 14% below the 2025 benchmark of $64.00); FOB mine: add the LM-PAD last-mile line before comparing with delivered prices |
| Monahans Proppant LLC | MP-4070 | MP-4070 Permian Regional Sand FOB Monahans (ton) | TON | 1 | Regional sand, 40/70 mesh (SCM-02-01-002) | About $62.48 per TON in 2025 (about 12% below the 2025 benchmark of $71.00); FOB mine: add the LM-PAD last-mile line before comparing with delivered prices |
| Monahans Proppant LLC | LM-PAD | Last-mile trucking mine to pad (ton) | TON | 1 | Proppant last-mile logistics, mine to pad (SCM-02-04-001) | About $21.00 per TON in 2025 (at the 2025 benchmark of $21.00) |
| Monahans Proppant LLC | TRANSLOAD | Transload handling (ton) | TON | 1 | Proppant last-mile logistics, mine to pad (SCM-02-04-001) | Transload handling; about $7.35 per TON (a fraction of the last-mile benchmark of $21.00) |
| Monahans Proppant LLC | FUEL-SC | Fuel surcharge | EA | 1 | Fuel surcharge (SCM-06-01-001) | Fee or service line; excluded from unit-price views |
| Redline Sand LLC | RL100 | Redline RL100 In-Basin Sand 100M delivered (ton) | TON | 1 | Regional sand, 100 mesh (SCM-02-01-001) | About $71.04 per TON in 2025 (about 11% above the 2025 benchmark of $64.00); from February 2026 invoiced about 8.5% above the RLS-2026 price book rate and mostly Disputed |
| Redline Sand LLC | RL4070 | Redline RL4070 In-Basin Sand delivered (ton) | TON | 1 | Regional sand, 40/70 mesh (SCM-02-01-002) | About $76.68 per TON in 2025 (about 8% above the 2025 benchmark of $71.00) |
| Redline Sand LLC | RLRC2040 | Redline RCS 20/40 resin-coated delivered (ton) | TON | 1 | Resin-coated sand, 20/40 mesh (SCM-02-03-001) | About $162.00 per TON in 2025 (at the 2025 benchmark of $162.00) |
| Redline Sand LLC | DEMUR | Standby time (hr) | HR | 1 | Standby / waiting time (SCM-06-02-002) | Fee or service line; excluded from unit-price views |
| Redline Sand LLC | FUEL-SC | Fuel surcharge | EA | 1 | Fuel surcharge (SCM-06-01-001) | Fee or service line; excluded from unit-price views |

## Water logistics: the five haulers

Hackberry Hauling LLC (0000100018), Two Dogs Trucking LLC (0000100019), Sandhills Water Transfer LLC (0000100020), Pecos Valley Vac Trucks LLC (0000100021) and Rattlesnake Hauling LLC (0000100022) all invoice the same eight item codes but with their own wording and price level. The template below is the canonical description; each hauler's wording and price level follow.

| Item code | Canonical description | UOM | Conversion | Generic product (node id) | Note |
|---|---|---|---|---|---|
| PW-HAUL | Produced water haul (per bbl) | BBL | 1 | Produced water hauling, truck (SCM-05-01-001) | 2025 benchmark $1.34 per BBL |
| SWD-FEE | SWD disposal fee (per bbl) | BBL | 1 | Saltwater disposal fee, third-party SWD (SCM-05-01-002) | 2025 benchmark $0.58 per BBL |
| FW-SRC | Fresh water sourcing (per bbl) | BBL | 1 | Fresh / brackish water sourcing, frac (SCM-05-02-001) | 2025 benchmark $0.46 per BBL |
| WT-XFER | Water transfer (per bbl) | BBL | 1 | Water transfer, pumping and lay-flat (SCM-05-02-002) | 2025 benchmark $0.39 per BBL |
| VAC-HR | Vac truck (per hr) | HR | 1 | Vacuum truck service (SCM-05-03-001) | 2025 benchmark $138.00 per HR |
| HOTOIL-HR | Hot oil unit (per hr) | HR | 1 | Hot oil truck service (SCM-05-03-002) | 2025 benchmark $172.00 per HR |
| LOAD-MIN | Minimum load charge | EA | 1 | Minimum charge / mobilization (SCM-06-02-003) | Fee line; excluded from unit-price views |
| FUEL-SC | Fuel surcharge | EA | 1 | Fuel surcharge (SCM-06-01-001) | Fee line; excluded from unit-price views |

| Hauler | LIFNR | Contract | Description style | 2025 price level |
|---|---|---|---|---|
| Hackberry Hauling LLC | 0000100018 | CLM-00019 | upper-case wording | about 4% above benchmark |
| Two Dogs Trucking LLC | 0000100019 | CLM-00020 | title-case wording | about 3% below benchmark |
| Sandhills Water Transfer LLC | 0000100020 | CLM-00021 | item code printed ahead of the description | at benchmark |
| Pecos Valley Vac Trucks LLC | 0000100021 | CLM-00022 | upper-case wording | about 9% above benchmark |
| Rattlesnake Hauling LLC | 0000100022 | CLM-00023 | title-case wording | about 5% below benchmark |

## OCTG long-tail descriptions

Casing and tubing come from a long tail of distributors in the "Other" supplier category. Each describes the same pipe its own way and bills per joint (JT) or per foot (FT). All variants below are approved by Spec sheet review against the OCTG mill data sheet for the generic product; the conversion turns joints into feet (42 ft per Range 3 casing joint, 31 ft per Range 2 tubing joint). The six descriptions of 5-1/2 in 20 lb/ft P-110 BTC production casing are the reference example of why the taxonomy exists.

| Description as invoiced | UOM | Conversion to FT or EA | Generic product (node id) | Note |
|---|---|---|---|---|
| CSG 5.500 20.00 P110 BTC R3 | JT | 42 | Production casing 5-1/2 in 20 lb/ft P-110 BTC (SCM-03-01-003) | 2025 benchmark $42.60 per FT |
| 5-1/2in 20# P-110 BTC casing, per ft | FT | 1 | Production casing 5-1/2 in 20 lb/ft P-110 BTC (SCM-03-01-003) | 2025 benchmark $42.60 per FT |
| CASING 5 1/2" 20.00# P-110 BTC RANGE 3 (jt) | JT | 42 | Production casing 5-1/2 in 20 lb/ft P-110 BTC (SCM-03-01-003) | 2025 benchmark $42.60 per FT |
| Prod csg 5.5 x 20 P110 BTC-M, ft | FT | 1 | Production casing 5-1/2 in 20 lb/ft P-110 BTC (SCM-03-01-003) | 2025 benchmark $42.60 per FT |
| OCTG 5.5 20PPF P110 BUTTRESS R3 PE | JT | 42 | Production casing 5-1/2 in 20 lb/ft P-110 BTC (SCM-03-01-003) | 2025 benchmark $42.60 per FT |
| 5.500 OD 20# P110 BTC SMLS casing / ft | FT | 1 | Production casing 5-1/2 in 20 lb/ft P-110 BTC (SCM-03-01-003) | 2025 benchmark $42.60 per FT |
| CSG 5.500 17.00 P110 BTC R3 | JT | 42 | Production casing 5-1/2 in 17 lb/ft P-110 BTC (SCM-03-01-004) | 2025 benchmark $38.90 per FT |
| 5-1/2in 17# P-110 BTC casing, per ft | FT | 1 | Production casing 5-1/2 in 17 lb/ft P-110 BTC (SCM-03-01-004) | 2025 benchmark $38.90 per FT |
| CASING 5 1/2" 17# P110 BTC R3 | JT | 42 | Production casing 5-1/2 in 17 lb/ft P-110 BTC (SCM-03-01-004) | 2025 benchmark $38.90 per FT |
| CSG 9.625 40.00 L80 BTC R3 | JT | 42 | Intermediate casing 9-5/8 in 40 lb/ft L-80 BTC (SCM-03-01-002) | 2025 benchmark $57.80 per FT |
| 9-5/8in 40# L-80 BTC casing, per ft | FT | 1 | Intermediate casing 9-5/8 in 40 lb/ft L-80 BTC (SCM-03-01-002) | 2025 benchmark $57.80 per FT |
| INTERMEDIATE CASING 9 5/8 40# L80 BTC (jt) | JT | 42 | Intermediate casing 9-5/8 in 40 lb/ft L-80 BTC (SCM-03-01-002) | 2025 benchmark $57.80 per FT |
| CSG 13.375 54.50 J55 BTC R3 | JT | 42 | Surface casing 13-3/8 in 54.5 lb/ft J-55 BTC (SCM-03-01-001) | 2025 benchmark $52.50 per FT |
| 13-3/8in 54.5# J-55 BTC surface casing, per ft | FT | 1 | Surface casing 13-3/8 in 54.5 lb/ft J-55 BTC (SCM-03-01-001) | 2025 benchmark $52.50 per FT |
| SURF CSG 13 3/8 54.5# J55 BTC | JT | 42 | Surface casing 13-3/8 in 54.5 lb/ft J-55 BTC (SCM-03-01-001) | 2025 benchmark $52.50 per FT |
| TBG 2.875 6.50 L80 EUE 8RD R2 | JT | 31 | Production tubing 2-7/8 in 6.5 lb/ft L-80 EUE (SCM-03-02-001) | 2025 benchmark $15.80 per FT |
| 2-7/8in 6.5# L-80 EUE tubing, per ft | FT | 1 | Production tubing 2-7/8 in 6.5 lb/ft L-80 EUE (SCM-03-02-001) | 2025 benchmark $15.80 per FT |
| TUBING 2 7/8" 6.5# L80 EUE 8RD (jt) | JT | 31 | Production tubing 2-7/8 in 6.5 lb/ft L-80 EUE (SCM-03-02-001) | 2025 benchmark $15.80 per FT |
| TBG 2.375 4.70 J55 EUE R2 | JT | 31 | Production tubing 2-3/8 in 4.7 lb/ft J-55 EUE (SCM-03-02-002) | 2025 benchmark $9.90 per FT |
| 2-3/8in 4.7# J-55 EUE tubing, per ft | FT | 1 | Production tubing 2-3/8 in 4.7 lb/ft J-55 EUE (SCM-03-02-002) | 2025 benchmark $9.90 per FT |
| Bow spring centralizer 5-1/2 x 8-1/2 | EA | 1 | Casing centralizer, bow-spring (SCM-03-03-001) | 2025 benchmark $68.00 per EA |
| CENTRALIZER BOW 5.5X8.5 | EA | 1 | Casing centralizer, bow-spring (SCM-03-03-001) | 2025 benchmark $68.00 per EA |
| Float shoe & collar set 5-1/2 BTC | EA | 1 | Float equipment, shoe and collar (SCM-03-03-002) | 2025 benchmark $1,450.00 per EA |
| FLOAT EQUIP 5.5 BTC SHOE+COLLAR | EA | 1 | Float equipment, shoe and collar (SCM-03-03-002) | 2025 benchmark $1,450.00 per EA |
| Wellhead system 5M multibowl 13-3/8 x 9-5/8 x 5-1/2 | EA | 1 | Wellhead assembly, 5M, multibowl (SCM-03-04-001) | 2025 benchmark $38,500.00 per EA |
| WELLHEAD ASSY 5000PSI MULTIBOWL | EA | 1 | Wellhead assembly, 5M, multibowl (SCM-03-04-001) | 2025 benchmark $38,500.00 per EA |

## Rental equipment long-tail descriptions

Rental vendors bill the same equipment per day, per week or per month. The standard UOM is DAY; a weekly line converts at 7 and a monthly line at 30.

| Description as invoiced | UOM | Conversion to DAY | Generic product (node id) | Note |
|---|---|---|---|---|
| Frac tank 500 bbl rental (day) | DAY | 1 | Frac tank rental, 500 bbl (SCM-04-01-001) | 2025 benchmark $58.00 per DAY |
| 500BBL FRAC TANK DAILY | DAY | 1 | Frac tank rental, 500 bbl (SCM-04-01-001) | 2025 benchmark $58.00 per DAY |
| Frac tank rental, 500 bbl, monthly | MONTH | 30 | Frac tank rental, 500 bbl (SCM-04-01-001) | 2025 benchmark $58.00 per DAY |
| Mud tank / roll-off rental (day) | DAY | 1 | Mud / cuttings tank rental (SCM-04-01-002) | 2025 benchmark $85.00 per DAY |
| CUTTINGS BOX RENTAL DAILY | DAY | 1 | Mud / cuttings tank rental (SCM-04-01-002) | 2025 benchmark $85.00 per DAY |
| Light tower rental (day) | DAY | 1 | Light tower rental (SCM-04-02-001) | 2025 benchmark $44.00 per DAY |
| LIGHT PLANT 4-LAMP DAILY | DAY | 1 | Light tower rental (SCM-04-02-001) | 2025 benchmark $44.00 per DAY |
| Light tower, monthly rate | MONTH | 30 | Light tower rental (SCM-04-02-001) | 2025 benchmark $44.00 per DAY |
| 100kW generator rental (day) | DAY | 1 | Generator rental, 100 kW (SCM-04-02-002) | 2025 benchmark $215.00 per DAY |
| GENSET 100KW DAILY | DAY | 1 | Generator rental, 100 kW (SCM-04-02-002) | 2025 benchmark $215.00 per DAY |
| Generator 100 kW, weekly | WEEK | 7 | Generator rental, 100 kW (SCM-04-02-002) | 2025 benchmark $215.00 per DAY |
| Flowback iron & manifold package (day) | DAY | 1 | Flowback iron and manifold package rental (SCM-04-03-001) | 2025 benchmark $1,180.00 per DAY |
| FLOWBACK EQUIP PKG 10K DAILY | DAY | 1 | Flowback iron and manifold package rental (SCM-04-03-001) | 2025 benchmark $1,180.00 per DAY |
| BOP stack 5M double ram rental (day) | DAY | 1 | BOP stack rental, 5M (SCM-04-03-002) | 2025 benchmark $740.00 per DAY |
| BOP 5000PSI DAILY | DAY | 1 | BOP stack rental, 5M (SCM-04-03-002) | 2025 benchmark $740.00 per DAY |
| Office trailer 12x60 rental (day) | DAY | 1 | Office / crew trailer rental (SCM-04-04-001) | 2025 benchmark $72.00 per DAY |
| CREW TRAILER MONTHLY | MONTH | 30 | Office / crew trailer rental (SCM-04-04-001) | 2025 benchmark $72.00 per DAY |
| Telehandler 10K rental (day) | DAY | 1 | Telehandler / forklift rental (SCM-04-04-002) | 2025 benchmark $365.00 per DAY |
| FORKLIFT TELEHANDLER WEEKLY | WEEK | 7 | Telehandler / forklift rental (SCM-04-04-002) | 2025 benchmark $365.00 per DAY |
| Lay-flat line 10in rental per 1000 ft-day | DAY | 1 | Temporary surface line rental, lay-flat (SCM-04-05-001) | 2025 benchmark $29.00 per DAY |
| LAYFLAT HOSE RENTAL DAILY | DAY | 1 | Temporary surface line rental, lay-flat (SCM-04-05-001) | 2025 benchmark $29.00 per DAY |

## Descriptions that stay in the steward queue

These wordings appear on distributor and rental invoices and carry no specification; they are Unclassified or Needs review in SCM_ITEM_CLASSIFICATION and make up most of the unclassified backlog (about 8 percent of 2026 line spend, mostly rentals and distributor items).

| Description as invoiced | UOM | Status |
|---|---|---|
| MISC SUPPLIES | EA | Unclassified or Needs review; no specification in the description |
| SHOP SUPPLIES | EA | Unclassified or Needs review; no specification in the description |
| PART# 44-1093 | EA | Unclassified or Needs review; no specification in the description |
| MATERIAL PER TICKET | EA | Unclassified or Needs review; no specification in the description |
| RENTAL EQUIP PER TICKET | EA | Unclassified or Needs review; no specification in the description |
| EQUIPMENT RENTAL - SEE ATTACHED | EA | Unclassified or Needs review; no specification in the description |
| FIELD TICKET 7731 CHARGES | EA | Unclassified or Needs review; no specification in the description |
| HARDWARE | EA | Unclassified or Needs review; no specification in the description |
| VALVE 2IN | EA | Unclassified or Needs review; no specification in the description |
| SUPPLIES - LOCATION | EA | Unclassified or Needs review; no specification in the description |
| RENTAL - MONTHLY | MONTH | Unclassified or Needs review; no specification in the description |
| SERVICE CALL | EA | Unclassified or Needs review; no specification in the description |
| CONSUMABLES | EA | Unclassified or Needs review; no specification in the description |
| MISC RENTAL | DAY | Unclassified or Needs review; no specification in the description |

## Price books loaded in OpenInvoice

| Supplier | LIFNR | Contract | PRICEBOOK_VERSION | Effective from | Effective to | Escalation | Source document (MSA Exhibit B) |
|---|---|---|---|---|---|---|---|
| Corrosion Control Chem LLC | 0000100039 | CLM-00040 | CCC-PB-2024A | 2024-01-01 | 2024-12-31 | 0% | Corrosion_Control_Chem_LLC_CCC_PB_2024A_MSA_Exhibit_B_Pricing.pdf |
| Corrosion Control Chem LLC | 0000100039 | CLM-00040 | CCC-PB-2025A | 2025-01-01 | 2026-12-31 | 2.5% | Corrosion_Control_Chem_LLC_CCC_PB_2025A_MSA_Exhibit_B_Pricing.pdf |
| Basin Chemical LLC | 0000100040 | CLM-00041 | BSN-PB-2024 | 2024-01-01 | 2024-12-31 | 0% | Basin_Chemical_LLC_BSN_PB_2024_MSA_Exhibit_B_Pricing.pdf |
| Basin Chemical LLC | 0000100040 | CLM-00041 | BSN-PB-2025 | 2025-01-01 | 2026-12-31 | 3% | Basin_Chemical_LLC_BSN_PB_2025_MSA_Exhibit_B_Pricing.pdf |
| Kermit Sand Co LLC | 0000100041 | CLM-00042 | KSC-2024 | 2024-01-01 | 2025-06-30 | 0% | Kermit_Sand_Co_LLC_KSC_2024_MSA_Exhibit_B_Pricing.pdf |
| Kermit Sand Co LLC | 0000100041 | CLM-00042 | KSC-2025H2 | 2025-07-01 | 2026-12-31 | 3% | Kermit_Sand_Co_LLC_KSC_2025H2_MSA_Exhibit_B_Pricing.pdf |
| Monahans Proppant LLC | 0000100042 | CLM-00043 | MPL-2024 | 2024-01-01 | 2025-12-31 | 0% | Monahans_Proppant_LLC_MPL_2024_MSA_Exhibit_B_Pricing.pdf |
| Monahans Proppant LLC | 0000100042 | CLM-00043 | MPL-2026 | 2026-01-01 | 2026-12-31 | 2% | Monahans_Proppant_LLC_MPL_2026_MSA_Exhibit_B_Pricing.pdf |
| Redline Sand LLC | 0000100043 | CLM-00044 | RLS-2024 | 2024-01-01 | 2025-12-31 | 0% | Redline_Sand_LLC_RLS_2024_MSA_Exhibit_B_Pricing.pdf |
| Redline Sand LLC | 0000100043 | CLM-00044 | RLS-2026 | 2026-01-01 | 2026-12-31 | 2% | Redline_Sand_LLC_RLS_2026_MSA_Exhibit_B_Pricing.pdf |

Invoice lines are matched to the price book line in force on the service date (OI_INVOICE_LINE.PRICEBOOK_ITEM_ID and PRICEBOOK_RATE_USD). Suppliers without a loaded price book (the haulers, the OCTG distributors, the rental vendors) have NULL in both columns and do not appear in V_PRICEBOOK_VARIANCE.

## Synonyms

| People say | They mean | Warehouse |
|---|---|---|
| CI, corrosion inhibitor, CorroShield, CS-7000, CorroGuard, BC-220, filming amine | Corrosion inhibitor, water-soluble, filming amine | SCM-01-01-001 |
| OS batch inhibitor, oil-soluble CI, CS-7100, BC-240 | Corrosion inhibitor, oil-soluble, batch | SCM-01-01-002 |
| SI, scale inhibitor, ScaleGuard, SG-2200, BasinScale, BS-310 | Scale inhibitor, phosphonate, continuous injection | SCM-01-02-001 |
| squeeze, BS-320 | Scale inhibitor, squeeze grade | SCM-01-02-002 |
| paraffin solvent, ParaClear, PX-500, ParaSolv, BP-150 | Paraffin solvent, aromatic | SCM-01-03-001 |
| H2S scavenger, scavenger, triazine, SulfiStop, HS-9000, H2S-Trap, BH-700 | H2S scavenger, triazine | SCM-01-04-001 |
| O2 scavenger, bisulfite, O2-Scav | Oxygen scavenger, sulfite | SCM-01-04-002 |
| biocide, glut, BioGard, THPS, BasinCide | Biocide, glutaraldehyde (SCM-01-05-001) or Biocide, THPS (SCM-01-05-002) | SCM-01-05-001 and SCM-01-05-002 |
| demulsifier, oil treater, DemulsiMax, DM-410 | Demulsifier, oil-treating | SCM-01-06-001 |
| water clarifier, reverse breaker, WaterClear, BW-90 | Water clarifier, reverse demulsifier | SCM-01-06-002 |
| foamer, surfactant, FoamLift, FM-30, FoamUp, BF-20 | Foamer / surfactant, gas-well deliquification | SCM-01-07-001 |
| methanol, MeOH, hydrate inhibitor | Methanol, hydrate inhibitor | SCM-01-07-002 |
| FR, friction reducer, slickwater FR, FlowRite, FR-77 | Friction reducer, slickwater | SCM-01-08-001 |
| acid, HCl, 15% acid, spearhead | Hydrochloric acid 15%, spearhead | SCM-01-08-002 |
| clay stab, KCl sub, ClayLock | Clay stabilizer, KCl substitute | SCM-01-08-003 |
| breaker, AP breaker, BreakOut | Gel breaker, oxidizer | SCM-01-08-004 |
| 100M, 100 mesh, 100-mesh, in-basin sand, regional sand, Permian sand, FracMax 100, FM100, MP-100, RL100 | Regional sand, 100 mesh | SCM-02-01-001 |
| 40/70, 40-70, FracMax 40/70, MP-4070, RL4070 | Regional sand, 40/70 mesh | SCM-02-01-002 |
| NWS, northern white, 30/50 | Northern white sand, 30/50 mesh | SCM-02-02-001 |
| RCS, resin coated, 20/40 RCS, RLRC2040 | Resin-coated sand, 20/40 mesh | SCM-02-03-001 |
| last mile, LM-PAD, transload, sand trucking, mine to pad | Proppant last-mile logistics, mine to pad | SCM-02-04-001 |
| csg, CSG, prod csg, production casing, 5-1/2 casing, 5.5 20# P110, 20 ppf P-110 | Production casing 5-1/2 in 20 lb/ft P-110 BTC (or 17 lb/ft when the weight says 17) | SCM-03-01-003 and SCM-03-01-004 |
| intermediate, 9-5/8, 9.625 | Intermediate casing 9-5/8 in 40 lb/ft L-80 BTC | SCM-03-01-002 |
| surface casing, surf csg, 13-3/8 | Surface casing 13-3/8 in 54.5 lb/ft J-55 BTC | SCM-03-01-001 |
| tbg, TBG, tubing, 2-7/8, 2-3/8 | Production tubing 2-7/8 in 6.5 lb/ft L-80 EUE or 2-3/8 in 4.7 lb/ft J-55 EUE | SCM-03-02-001 and SCM-03-02-002 |
| OCTG, tubulars, pipe (when casing or tubing is meant) | OCTG & wellhead family | LEVEL1_FAMILY = OCTG & wellhead |
| frac tank, 500 bbl tank, frac tank rental | Frac tank rental, 500 bbl | SCM-04-01-001 |
| light plant, light tower, light tower rental | Light tower rental | SCM-04-02-001 |
| genset, generator, 100 kW gen | Generator rental, 100 kW | SCM-04-02-002 |
| flowback iron, flowback package, choke manifold | Flowback iron and manifold package rental | SCM-04-03-001 |
| BOP, BOP stack, 5M stack | BOP stack rental, 5M | SCM-04-03-002 |
| trailer, crew trailer, office trailer | Office / crew trailer rental | SCM-04-04-001 |
| telehandler, forklift | Telehandler / forklift rental | SCM-04-04-002 |
| lay-flat, layflat, lay flat hose | Temporary surface line rental, lay-flat | SCM-04-05-001 |
| SWD, saltwater disposal, disposal fee | Saltwater disposal fee, third-party SWD | SCM-05-01-002 |
| water haul, produced water haul, PW haul | Produced water hauling, truck | SCM-05-01-001 |
| fresh water, brackish water, source water | Fresh / brackish water sourcing, frac | SCM-05-02-001 |
| water transfer, transfer | Water transfer, pumping and lay-flat | SCM-05-02-002 |
| vac truck, vacuum truck | Vacuum truck service | SCM-05-03-001 |
| hot oiler, hot oil truck | Hot oil truck service | SCM-05-03-002 |
| fuel surcharge, FSC | Fuel surcharge | SCM-06-01-001 |
| demurrage, standby, waiting time | Standby / waiting time | SCM-06-02-002 |
| tote, IBC, 330 | TOTE pack = 330 GAL | INVOICED_UOM = TOTE |
| drum, 55 | DRUM pack = 55 GAL | INVOICED_UOM = DRUM |
| pail, bucket, 5 gal | PAIL pack = 5 GAL | INVOICED_UOM = PAIL |
| bulk, transport, tanker | GAL bulk delivery | INVOICED_UOM = GAL |
| joint, jt, JT | Casing or tubing joint (42 ft or 31 ft) | INVOICED_UOM = JT |
| vendor, supplier, LIFNR, SAP vendor | OI_SUPPLIER by LIFNR | OI_SUPPLIER.LIFNR |
| category manager, owner | CATEGORY_MANAGER on the taxonomy family | SCM_PRODUCT_TAXONOMY.CATEGORY_MANAGER |
| steward queue, backlog, unclassified | Lines without an approved generic product | V_UNCLASSIFIED_SPEND |

## Business terms

| Term | Definition |
|---|---|
| Generic product | The supplier-neutral product or service name in taxonomy v3.0 that spend and unit prices are compared by (SCM_PRODUCT_TAXONOMY.GENERIC_PRODUCT_NAME). Never a marketing name. |
| Supplier item | What the supplier prints on the line: item code plus description plus pack (OI_INVOICE_LINE.SUPPLIER_ITEM_CODE and SUPPLIER_ITEM_DESCRIPTION). |
| Standard unit price | LINE_AMOUNT_USD divided by standard quantity (QUANTITY x CONVERSION_FACTOR_TO_STD_UOM); over a period it is volume weighted: SUM(amount) / SUM(standard quantity). The only price used to compare suppliers. |
| Price dispersion | For one generic product and year: highest supplier standard unit price divided by lowest, minus one, in percent (V_SUPPLIER_ALTERNATIVES.PRICE_DISPERSION_PCT). |
| Savings at best observed price | What would have been saved had every supplier's volume been bought at the lowest supplier standard unit price observed that year (V_SUPPLIER_ALTERNATIVES.SAVINGS_AT_BEST_PRICE_USD). An opportunity figure, not a realised saving. |
| Pack premium | Standard unit price of a drum or pail relative to the tote or bulk price of the same product from the same supplier, minus one, in percent. |
| Benchmark variance | Supplier standard unit price relative to BENCHMARK_PRICE_USD_PER_STD_UOM, minus one, in percent. |
| Pricebook variance | (UNIT_PRICE_USD - PRICEBOOK_RATE_USD) x QUANTITY on lines matched to a loaded price book; positive means invoiced above contract (V_PRICEBOOK_VARIANCE). |
| Over-contract line | A matched line with PRICE_VARIANCE_USD greater than zero (IS_OVER_CONTRACT = 1). Many are Disputed with reason "Unit price above contract rate". |
| Classified spend | SUM(LINE_AMOUNT_USD) of lines whose classification REVIEW_STATUS is Approved (IS_CLASSIFIED = 1). |
| Unclassified spend | SUM(LINE_AMOUNT_USD) of lines with no classification row, Needs review or Unclassified (IS_CLASSIFIED = 0; V_UNCLASSIFIED_SPEND). |
| Field ticket | The field-approved record of a delivery, service or rental (OI_FIELD_TICKET) that precedes the invoice line; approved by the company man or foreman against a well and an AFE or property. |
| Stamped invoice | An OpenInvoice header dated 2025-01-01 or later whose ERP_INVOICE_ID carries the spend-analytics invoice id (SPEND_INVOICE.INVOICE_ID) and whose INVOICE_TOTAL_USD equals SPEND_INVOICE.AMOUNT_USD (ERP_MATCH_STATUS = Stamped). |
| Legacy invoice | A pre-2025 header with no ERP_INVOICE_ID; it links to spend analytics only through COUPA_DOC_ID (ERP_MATCH_STATUS = Legacy - Coupa id only). |
| Delivered vs FOB | A delivered price includes trucking to the pad; an FOB mine price does not and needs the last-mile logistics line added before comparison. |
