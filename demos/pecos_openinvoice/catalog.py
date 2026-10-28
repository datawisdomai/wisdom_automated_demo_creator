"""catalog.py — the supply-chain product taxonomy and the supplier item catalogs for the
Pecos Ridge OpenInvoice demo. Pure data (no Snowflake, no randomness): generator.py,
supplier_docs.py, checks.py and the authored context documents all read from here so
every marketing name, generic name, pack size and contract rate agrees everywhere.

Vocabulary
  generic product   what supply chain wants to analyse: "Corrosion inhibitor, water-soluble,
                    filming amine" — one row per leaf in TAXONOMY, keyed by a node id SCM-FF-CC-NNN
  supplier item     what the supplier prints on the invoice line: "CorroShield CS-7000 Corrosion
                    Inhibitor 55 gal drum" with its own code, UOM and pack size
  std UOM           the taxonomy's unit for price comparison (GAL, TON, FT, DAY, BBL, HR, EA);
                    pack_qty converts one invoiced unit into std units (a 55 gal drum -> 55 GAL)
"""
from __future__ import annotations

# --------------------------------------------------------------------------------------
# Generic product taxonomy (version 3.0, owned by Supply Chain; category manager per family)
# node_id, family, class, generic_product_name, primary_use, use_phase, std_uom, key_spec, unspsc, alt_supplier_eligible
# --------------------------------------------------------------------------------------
FAMILY_MANAGER = {
    "Production & completion chemicals": "Jessica Whitaker",
    "Proppant": "Clint Johnson",
    "OCTG & wellhead": "Clint Johnson",
    "Rental equipment": "Hector Brown",
    "Water logistics": "Jessica Whitaker",
    "Fees & surcharges": "Hector Brown",
    "Downhole & artificial lift": "Clint Johnson",
    "MRO & consumables": "Hector Brown",
}

TAXONOMY: list[tuple] = [
    # ---- 01 chemicals
    ("SCM-01-01-001", "Production & completion chemicals", "Corrosion control", "Corrosion inhibitor, water-soluble, filming amine", "Continuous or batch treatment of tubing and flowlines against CO2/H2S corrosion", "Production", "GAL", "water-soluble; imidazoline/quaternary amine; batch or continuous", "12161700", True),
    ("SCM-01-01-002", "Production & completion chemicals", "Corrosion control", "Corrosion inhibitor, oil-soluble, batch", "Batch treatment of oil wells and gathering lines", "Production", "GAL", "oil-soluble; batch; 7-14 day interval", "12161700", True),
    ("SCM-01-02-001", "Production & completion chemicals", "Scale control", "Scale inhibitor, phosphonate, continuous injection", "Prevents carbonate and sulfate scale in tubing and surface equipment", "Production", "GAL", "phosphonate; continuous injection 5-25 ppm", "12161700", True),
    ("SCM-01-02-002", "Production & completion chemicals", "Scale control", "Scale inhibitor, squeeze grade", "Downhole squeeze treatments", "Production", "GAL", "squeeze grade; 10-20% active", "12161700", True),
    ("SCM-01-03-001", "Production & completion chemicals", "Paraffin & asphaltene", "Paraffin solvent, aromatic", "Dissolves paraffin deposits in tubing and flowlines", "Production", "GAL", "aromatic solvent blend; hot-oil alternative", "12161700", True),
    ("SCM-01-03-002", "Production & completion chemicals", "Paraffin & asphaltene", "Paraffin dispersant / inhibitor, continuous", "Keeps paraffin in suspension; continuous injection", "Production", "GAL", "crystal modifier; continuous", "12161700", True),
    ("SCM-01-04-001", "Production & completion chemicals", "Gas treating", "H2S scavenger, triazine", "Removes H2S from produced gas and oil to meet pipeline spec", "Production", "GAL", "MEA triazine 50-70%", "12161700", True),
    ("SCM-01-04-002", "Production & completion chemicals", "Gas treating", "Oxygen scavenger, sulfite", "Removes dissolved oxygen in injection and frac water", "Production", "GAL", "ammonium bisulfite 65%", "12161700", True),
    ("SCM-01-05-001", "Production & completion chemicals", "Microbial control", "Biocide, glutaraldehyde", "Controls sulfate-reducing bacteria in produced and frac water", "Completion", "GAL", "glutaraldehyde 25-50%", "12161700", True),
    ("SCM-01-05-002", "Production & completion chemicals", "Microbial control", "Biocide, THPS", "Low-toxicity biocide for water systems", "Production", "GAL", "THPS 50-75%", "12161700", True),
    ("SCM-01-06-001", "Production & completion chemicals", "Separation", "Demulsifier, oil-treating", "Breaks water-in-oil emulsions at the tank battery", "Production", "GAL", "resin/oxyalkylate blend", "12161700", True),
    ("SCM-01-06-002", "Production & completion chemicals", "Separation", "Water clarifier, reverse demulsifier", "Removes oil from produced water before disposal", "Production", "GAL", "cationic polymer", "12161700", True),
    ("SCM-01-07-001", "Production & completion chemicals", "Flow assurance", "Foamer / surfactant, gas-well deliquification", "Unloads liquids from gas wells", "Production", "GAL", "foaming surfactant; capillary or batch", "12161700", True),
    ("SCM-01-07-002", "Production & completion chemicals", "Flow assurance", "Methanol, hydrate inhibitor", "Prevents hydrates in gas lines and wellheads in winter", "Production", "GAL", "99% methanol", "12352100", True),
    ("SCM-01-08-001", "Production & completion chemicals", "Completion fluids", "Friction reducer, slickwater", "Reduces friction pressure in slickwater fracs", "Completion", "GAL", "polyacrylamide emulsion; 0.5-1.0 gpt", "12161700", True),
    ("SCM-01-08-002", "Production & completion chemicals", "Completion fluids", "Hydrochloric acid 15%, spearhead", "Breaks down near-wellbore damage ahead of the frac", "Completion", "GAL", "15% HCl with inhibitor", "12352300", True),
    ("SCM-01-08-003", "Production & completion chemicals", "Completion fluids", "Clay stabilizer, KCl substitute", "Prevents clay swelling in the formation", "Completion", "GAL", "choline chloride 70%", "12161700", True),
    ("SCM-01-08-004", "Production & completion chemicals", "Completion fluids", "Gel breaker, oxidizer", "Breaks crosslinked gel after the frac", "Completion", "LB", "ammonium persulfate", "12161700", True),
    # ---- 02 proppant
    ("SCM-02-01-001", "Proppant", "Regional sand", "Regional sand, 100 mesh", "Primary proppant for slickwater stages", "Completion", "TON", "Permian regional; 100 mesh; crush 7-8K", "11111600", True),
    ("SCM-02-01-002", "Proppant", "Regional sand", "Regional sand, 40/70 mesh", "Tail-in proppant for slickwater stages", "Completion", "TON", "Permian regional; 40/70; crush 8K", "11111600", True),
    ("SCM-02-02-001", "Proppant", "Northern white sand", "Northern white sand, 30/50 mesh", "Higher-conductivity tail-in for deeper, higher-stress wells", "Completion", "TON", "Northern white; 30/50; crush 9-10K", "11111600", True),
    ("SCM-02-03-001", "Proppant", "Coated proppant", "Resin-coated sand, 20/40 mesh", "Flowback control in high-rate gas wells", "Completion", "TON", "curable resin coat; 20/40", "11111600", True),
    ("SCM-02-04-001", "Proppant", "Proppant logistics", "Proppant last-mile logistics, mine to pad", "Trucking and transloading from mine or transload to the frac pad", "Completion", "TON", "per ton delivered; boxes or pneumatic", "78101800", True),
    # ---- 03 OCTG
    ("SCM-03-01-001", "OCTG & wellhead", "Casing", "Surface casing 13-3/8 in 54.5 lb/ft J-55 BTC", "Surface hole casing string", "Drilling", "FT", "13.375 in; 54.5#; J-55; BTC; R3", "40171500", True),
    ("SCM-03-01-002", "OCTG & wellhead", "Casing", "Intermediate casing 9-5/8 in 40 lb/ft L-80 BTC", "Intermediate casing string", "Drilling", "FT", "9.625 in; 40#; L-80; BTC; R3", "40171500", True),
    ("SCM-03-01-003", "OCTG & wellhead", "Casing", "Production casing 5-1/2 in 20 lb/ft P-110 BTC", "Production casing / lateral string for horizontal wells", "Drilling", "FT", "5.5 in; 20#; P-110; BTC; R3", "40171500", True),
    ("SCM-03-01-004", "OCTG & wellhead", "Casing", "Production casing 5-1/2 in 17 lb/ft P-110 BTC", "Lighter production string for shallower laterals", "Drilling", "FT", "5.5 in; 17#; P-110; BTC; R3", "40171500", True),
    ("SCM-03-02-001", "OCTG & wellhead", "Tubing", "Production tubing 2-7/8 in 6.5 lb/ft L-80 EUE", "Production tubing string", "Completion", "FT", "2.875 in; 6.5#; L-80; EUE 8rd", "40171500", True),
    ("SCM-03-02-002", "OCTG & wellhead", "Tubing", "Production tubing 2-3/8 in 4.7 lb/ft J-55 EUE", "Tubing for shallow and Hugoton wells", "Production", "FT", "2.375 in; 4.7#; J-55; EUE", "40171500", True),
    ("SCM-03-03-001", "OCTG & wellhead", "Casing accessories", "Casing centralizer, bow-spring", "Centralises casing for cement placement", "Drilling", "EA", "bow spring; per casing size", "40171500", True),
    ("SCM-03-03-002", "OCTG & wellhead", "Casing accessories", "Float equipment, shoe and collar", "Float shoe and collar for cementing", "Drilling", "EA", "set; per casing size", "40171500", True),
    ("SCM-03-04-001", "OCTG & wellhead", "Wellhead", "Wellhead assembly, 5M, multibowl", "Casing head, spools and tubing head", "Drilling", "EA", "5,000 psi multibowl system", "40171600", True),
    # ---- 04 rentals
    ("SCM-04-01-001", "Rental equipment", "Tanks", "Frac tank rental, 500 bbl", "Temporary fluid storage on location", "Completion", "DAY", "500 bbl; open or closed top", "72141100", True),
    ("SCM-04-01-002", "Rental equipment", "Tanks", "Mud / cuttings tank rental", "Drilling fluid and cuttings containment", "Drilling", "DAY", "open-top; roll-off", "72141100", True),
    ("SCM-04-02-001", "Rental equipment", "Power & light", "Light tower rental", "Night lighting on location", "Drilling", "DAY", "4-lamp diesel", "72141100", True),
    ("SCM-04-02-002", "Rental equipment", "Power & light", "Generator rental, 100 kW", "Temporary power for pads and crew quarters", "Drilling", "DAY", "100 kW diesel", "72141100", True),
    ("SCM-04-03-001", "Rental equipment", "Pressure control", "Flowback iron and manifold package rental", "Choke manifold, iron and separators during flowback", "Completion", "DAY", "10K iron; 3-phase separator", "72141100", True),
    ("SCM-04-03-002", "Rental equipment", "Pressure control", "BOP stack rental, 5M", "Blowout preventer for workovers and completions", "Completion", "DAY", "5,000 psi double ram", "72141100", True),
    ("SCM-04-04-001", "Rental equipment", "Site & crew", "Office / crew trailer rental", "Company man and crew quarters", "Drilling", "DAY", "12x60 trailer", "72141100", True),
    ("SCM-04-04-002", "Rental equipment", "Site & crew", "Telehandler / forklift rental", "Material handling on location", "Drilling", "DAY", "10,000 lb telehandler", "72141100", True),
    ("SCM-04-05-001", "Rental equipment", "Surface lines", "Temporary surface line rental, lay-flat", "Water transfer and flowback lines", "Completion", "DAY", "per 1,000 ft-day; 10 or 12 in lay-flat", "72141100", True),
    # ---- 05 water logistics
    ("SCM-05-01-001", "Water logistics", "Produced water", "Produced water hauling, truck", "Trucking produced water from tank battery to disposal", "Production", "BBL", "per barrel hauled; 130 bbl loads", "78101800", True),
    ("SCM-05-01-002", "Water logistics", "Produced water", "Saltwater disposal fee, third-party SWD", "Disposal fee at third-party SWD well", "Production", "BBL", "per barrel disposed", "76121900", True),
    ("SCM-05-02-001", "Water logistics", "Frac water", "Fresh / brackish water sourcing, frac", "Water purchased for completions", "Completion", "BBL", "per barrel sourced", "70171700", True),
    ("SCM-05-02-002", "Water logistics", "Frac water", "Water transfer, pumping and lay-flat", "Moving frac water from source or pit to the pad", "Completion", "BBL", "per barrel transferred", "78101800", True),
    ("SCM-05-03-001", "Water logistics", "Field service trucks", "Vacuum truck service", "Pit, tank and spill cleanup by vac truck", "Production", "HR", "per hour; 130 bbl vac", "78101800", True),
    ("SCM-05-03-002", "Water logistics", "Field service trucks", "Hot oil truck service", "Hot oiling tubing and flowlines for paraffin", "Production", "HR", "per hour; hot oil unit", "78101800", True),
    # ---- 06 fees
    ("SCM-06-01-001", "Fees & surcharges", "Logistics fees", "Fuel surcharge", "Fuel index surcharge on trucking and delivered material", "Production", "EA", "percentage or flat per invoice", "78101800", False),
    ("SCM-06-01-002", "Fees & surcharges", "Logistics fees", "Delivery / freight charge", "Freight on delivered material", "Production", "EA", "flat per delivery", "78101800", False),
    ("SCM-06-02-001", "Fees & surcharges", "Service fees", "Environmental / disposal fee", "Container and residue handling fee", "Production", "EA", "flat per invoice", "76121900", False),
    ("SCM-06-02-002", "Fees & surcharges", "Service fees", "Standby / waiting time", "Crew or truck standby billed hourly", "Production", "HR", "per hour", "78101800", False),
    ("SCM-06-02-003", "Fees & surcharges", "Service fees", "Minimum charge / mobilization", "Minimum invoice or mobilization charge", "Production", "EA", "flat", "78101800", False),
    # ---- 07 downhole & artificial lift (distributor items)
    ("SCM-07-01-001", "Downhole & artificial lift", "Rod lift", "Sucker rod, 7/8 in grade D", "Rod string for beam-pumped wells", "Production", "EA", "7/8 in; grade D; 25 ft", "40171500", True),
    ("SCM-07-01-002", "Downhole & artificial lift", "Rod lift", "Rod pump insert, 2 in", "Downhole insert pump for rod lift", "Production", "EA", "RHAC 2 in", "40151500", True),
    ("SCM-07-02-001", "Downhole & artificial lift", "Valves", "Gate valve 2 in 2000 psi", "Wellhead and flowline isolation", "Production", "EA", "2 in; 2,000 psi; flanged", "40141600", True),
    ("SCM-07-02-002", "Downhole & artificial lift", "Valves", "Ball valve 2 in threaded", "Flowline and tank battery isolation", "Production", "EA", "2 in; NPT; 2,000 psi", "40141600", True),
    # ---- 08 MRO & consumables
    ("SCM-08-01-001", "MRO & consumables", "Shop & safety", "Shop supplies and consumables, misc", "Catch-all for distributor consumables (gloves, rags, hardware)", "Production", "EA", "misc", "31160000", False),
    ("SCM-08-01-002", "MRO & consumables", "Shop & safety", "PPE and safety supplies", "Gloves, glasses, FR clothing, gas-monitor consumables", "Production", "EA", "misc", "46180000", True),
    ("SCM-08-02-001", "MRO & consumables", "Pipe & fittings", "Line pipe and fittings, 2-4 in", "Flowline pipe, fittings and unions", "Facilities", "FT", "sch 40/80; 2-4 in", "40171500", True),
]
TAX_BY_ID = {t[0]: t for t in TAXONOMY}
TAX_BY_NAME = {t[3]: t[0] for t in TAXONOMY}

# Standard-UOM reference price (USD per std unit) in 2025 dollars; yearly index applied by the generator
BASE_PRICE = {
    "SCM-01-01-001": 16.40, "SCM-01-01-002": 18.90, "SCM-01-02-001": 13.60, "SCM-01-02-002": 15.20, "SCM-01-03-001": 9.40,
    "SCM-01-03-002": 11.80, "SCM-01-04-001": 10.70, "SCM-01-04-002": 6.90, "SCM-01-05-001": 12.30, "SCM-01-05-002": 14.10,
    "SCM-01-06-001": 19.60, "SCM-01-06-002": 15.90, "SCM-01-07-001": 13.20, "SCM-01-07-002": 2.95, "SCM-01-08-001": 7.40,
    "SCM-01-08-002": 2.15, "SCM-01-08-003": 9.80, "SCM-01-08-004": 3.10,
    "SCM-02-01-001": 64.00, "SCM-02-01-002": 71.00, "SCM-02-02-001": 88.00, "SCM-02-03-001": 162.00, "SCM-02-04-001": 21.00,
    "SCM-03-01-001": 52.50, "SCM-03-01-002": 57.80, "SCM-03-01-003": 42.60, "SCM-03-01-004": 38.90, "SCM-03-02-001": 15.80,
    "SCM-03-02-002": 9.90, "SCM-03-03-001": 68.00, "SCM-03-03-002": 1450.00, "SCM-03-04-001": 38500.00,
    "SCM-04-01-001": 58.00, "SCM-04-01-002": 85.00, "SCM-04-02-001": 44.00, "SCM-04-02-002": 215.00, "SCM-04-03-001": 1180.00,
    "SCM-04-03-002": 740.00, "SCM-04-04-001": 72.00, "SCM-04-04-002": 365.00, "SCM-04-05-001": 29.00,
    "SCM-05-01-001": 1.34, "SCM-05-01-002": 0.58, "SCM-05-02-001": 0.46, "SCM-05-02-002": 0.39, "SCM-05-03-001": 138.00, "SCM-05-03-002": 172.00,
    "SCM-06-01-001": 1.0, "SCM-06-01-002": 1.0, "SCM-06-02-001": 1.0, "SCM-06-02-002": 95.00, "SCM-06-02-003": 1.0,
    "SCM-07-01-001": 78.40, "SCM-07-01-002": 1850.00, "SCM-07-02-001": 640.00, "SCM-07-02-002": 185.00,
    "SCM-08-01-001": 1.0, "SCM-08-01-002": 1.0, "SCM-08-02-001": 6.80,
}
# Yearly price index relative to 2025 (what the pricebooks and invoices actually moved by)
PRICE_INDEX = {2022: 0.91, 2023: 0.97, 2024: 1.00, 2025: 1.00, 2026: 1.03}

# --------------------------------------------------------------------------------------
# Supplier item catalogs for the hero suppliers (real LIFNRs from S4_VENDOR_LFA1)
# dict(code, desc, uom, pack_qty, node, mult) — invoiced unit price = BASE_PRICE[node] * mult * pack_qty * index * noise
# `mult` is the supplier's standard-UOM price relative to BASE_PRICE (the dispersion the demo exposes)
# --------------------------------------------------------------------------------------
CORROSION_CONTROL = "0000100039"   # Corrosion Control Chem LLC, Liberal KS — the lower-priced inhibitor supplier
BASIN_CHEMICAL = "0000100040"      # Basin Chemical LLC, Liberal KS — premium-priced, heavy on small packs
KERMIT = "0000100041"              # Kermit Sand Co LLC — delivered pricing
MONAHANS = "0000100042"            # Monahans Proppant LLC — FOB mine + separate last-mile line
REDLINE = "0000100043"             # Redline Sand LLC — invoiced above pricebook in 2026 (disputes)
HAULERS = ["0000100018", "0000100019", "0000100020", "0000100021", "0000100022"]

CHEM_PACKS = [  # (uom, gallons per unit, price premium per gallon vs bulk)
    ("GAL", 1, 1.00), ("TOTE", 330, 1.00), ("DRUM", 55, 1.07), ("PAIL", 5, 1.18),
]

SUPPLIER_ITEMS: dict[str, list[dict]] = {
    CORROSION_CONTROL: [
        dict(code="CS-7000-T", desc="CorroShield CS-7000 Corrosion Inhibitor 330 gal tote", uom="TOTE", pack_qty=330, node="SCM-01-01-001", mult=1.00),
        dict(code="CS-7000-D", desc="CorroShield CS-7000 Corrosion Inhibitor 55 gal drum", uom="DRUM", pack_qty=55, node="SCM-01-01-001", mult=1.07),
        dict(code="CS-7000-B", desc="CorroShield CS-7000 bulk delivery (gal)", uom="GAL", pack_qty=1, node="SCM-01-01-001", mult=0.97),
        dict(code="CS-7100-D", desc="CorroShield CS-7100 Oil-Soluble Batch Inhibitor 55 gal drum", uom="DRUM", pack_qty=55, node="SCM-01-01-002", mult=1.02),
        dict(code="SG-2200-T", desc="ScaleGuard SG-2200 Phosphonate Scale Inhibitor tote", uom="TOTE", pack_qty=330, node="SCM-01-02-001", mult=0.98),
        dict(code="PX-500-D", desc="ParaClear PX-500 Aromatic Solvent 55 gal drum", uom="DRUM", pack_qty=55, node="SCM-01-03-001", mult=1.00),
        dict(code="HS-9000-T", desc="SulfiStop HS-9000 Triazine Scavenger 330 gal tote", uom="TOTE", pack_qty=330, node="SCM-01-04-001", mult=1.03),
        dict(code="BG-25-D", desc="BioGard 25% Glutaraldehyde 55 gal drum", uom="DRUM", pack_qty=55, node="SCM-01-05-001", mult=1.00),
        dict(code="DM-410-D", desc="DemulsiMax DM-410 Oil Treater 55 gal drum", uom="DRUM", pack_qty=55, node="SCM-01-06-001", mult=0.99),
        dict(code="FM-30-T", desc="FoamLift FM-30 Surfactant tote", uom="TOTE", pack_qty=330, node="SCM-01-07-001", mult=1.01),
        dict(code="MEOH-B", desc="Methanol 99% bulk (gal)", uom="GAL", pack_qty=1, node="SCM-01-07-002", mult=1.00),
        dict(code="FR-77-B", desc="FlowRite FR-77 Friction Reducer bulk (gal)", uom="GAL", pack_qty=1, node="SCM-01-08-001", mult=0.98),
        dict(code="HCL15-B", desc="15% HCl Inhibited Acid bulk (gal)", uom="GAL", pack_qty=1, node="SCM-01-08-002", mult=1.00),
        dict(code="SVC-TECH", desc="Field technician service call (hr)", uom="HR", pack_qty=1, node="SCM-06-02-002", mult=1.00),
        dict(code="ENV-FEE", desc="Environmental / container fee", uom="EA", pack_qty=1, node="SCM-06-02-001", mult=1.00),
        dict(code="FUEL-SC", desc="Fuel surcharge", uom="EA", pack_qty=1, node="SCM-06-01-001", mult=1.00),
    ],
    BASIN_CHEMICAL: [
        dict(code="BC-220-T", desc="CorroGuard BC-220 CI 330 GAL TOTE", uom="TOTE", pack_qty=330, node="SCM-01-01-001", mult=1.21),
        dict(code="BC-220-D", desc="CorroGuard BC-220 CI 55 GAL DRUM", uom="DRUM", pack_qty=55, node="SCM-01-01-001", mult=1.29),
        dict(code="BC-220-P", desc="CORROGUARD BC-220 5 GAL PAIL", uom="PAIL", pack_qty=5, node="SCM-01-01-001", mult=1.42),
        dict(code="BC-240-D", desc="CorroGuard BC-240 OS Batch 55 GAL DRUM", uom="DRUM", pack_qty=55, node="SCM-01-01-002", mult=1.12),
        dict(code="BS-310-T", desc="BasinScale BS-310 Inhibitor TOTE", uom="TOTE", pack_qty=330, node="SCM-01-02-001", mult=1.09),
        dict(code="BS-320-D", desc="BasinScale BS-320 Squeeze 55 GAL DRUM", uom="DRUM", pack_qty=55, node="SCM-01-02-002", mult=1.04),
        dict(code="BP-150-D", desc="Basin ParaSolv BP-150 55 GAL DRUM", uom="DRUM", pack_qty=55, node="SCM-01-03-001", mult=1.08),
        dict(code="BP-160-T", desc="Basin ParaFlow BP-160 Dispersant TOTE", uom="TOTE", pack_qty=330, node="SCM-01-03-002", mult=1.00),
        dict(code="BH-700-T", desc="Basin H2S-Trap BH-700 TOTE", uom="TOTE", pack_qty=330, node="SCM-01-04-001", mult=1.06),
        dict(code="BO-65-T", desc="Basin O2-Scav 65% Bisulfite TOTE", uom="TOTE", pack_qty=330, node="SCM-01-04-002", mult=1.00),
        dict(code="BB-50-D", desc="BasinCide BB-50 THPS 55 GAL DRUM", uom="DRUM", pack_qty=55, node="SCM-01-05-002", mult=1.02),
        dict(code="BW-90-T", desc="Basin WaterClear BW-90 TOTE", uom="TOTE", pack_qty=330, node="SCM-01-06-002", mult=1.03),
        dict(code="BF-20-T", desc="Basin FoamUp BF-20 TOTE", uom="TOTE", pack_qty=330, node="SCM-01-07-001", mult=1.05),
        dict(code="BC-CLAY-B", desc="Basin ClayLock 70 bulk (gal)", uom="GAL", pack_qty=1, node="SCM-01-08-003", mult=1.00),
        dict(code="BC-BRK-50", desc="Basin BreakOut AP Oxidizer 50 lb bag", uom="BAG", pack_qty=50, node="SCM-01-08-004", mult=1.00),
        dict(code="SVC-TECH", desc="Chemical technician field service (hr)", uom="HR", pack_qty=1, node="SCM-06-02-002", mult=1.05),
        dict(code="DELIV", desc="Delivery charge", uom="EA", pack_qty=1, node="SCM-06-01-002", mult=1.00),
        dict(code="FUEL-SC", desc="Fuel surcharge", uom="EA", pack_qty=1, node="SCM-06-01-001", mult=1.00),
    ],
    KERMIT: [
        dict(code="FM100-DLV", desc="FracMax 100 mesh, delivered to pad (ton)", uom="TON", pack_qty=1, node="SCM-02-01-001", mult=1.00),
        dict(code="FM4070-DLV", desc="FracMax 40/70, delivered to pad (ton)", uom="TON", pack_qty=1, node="SCM-02-01-002", mult=1.00),
        dict(code="NW3050-DLV", desc="Northern White 30/50 delivered (ton)", uom="TON", pack_qty=1, node="SCM-02-02-001", mult=1.00),
        dict(code="DEMUR", desc="Truck demurrage / standby (hr)", uom="HR", pack_qty=1, node="SCM-06-02-002", mult=1.00),
        dict(code="FUEL-SC", desc="Fuel surcharge", uom="EA", pack_qty=1, node="SCM-06-01-001", mult=1.00),
    ],
    MONAHANS: [
        dict(code="MP-100", desc="MP-100 Permian Regional Sand FOB Monahans (ton)", uom="TON", pack_qty=1, node="SCM-02-01-001", mult=0.86),
        dict(code="MP-4070", desc="MP-4070 Permian Regional Sand FOB Monahans (ton)", uom="TON", pack_qty=1, node="SCM-02-01-002", mult=0.88),
        dict(code="LM-PAD", desc="Last-mile trucking mine to pad (ton)", uom="TON", pack_qty=1, node="SCM-02-04-001", mult=1.00),
        dict(code="TRANSLOAD", desc="Transload handling (ton)", uom="TON", pack_qty=1, node="SCM-02-04-001", mult=0.35),
        dict(code="FUEL-SC", desc="Fuel surcharge", uom="EA", pack_qty=1, node="SCM-06-01-001", mult=1.00),
    ],
    REDLINE: [
        dict(code="RL100", desc="Redline RL100 In-Basin Sand 100M delivered (ton)", uom="TON", pack_qty=1, node="SCM-02-01-001", mult=1.11),
        dict(code="RL4070", desc="Redline RL4070 In-Basin Sand delivered (ton)", uom="TON", pack_qty=1, node="SCM-02-01-002", mult=1.08),
        dict(code="RLRC2040", desc="Redline RCS 20/40 resin-coated delivered (ton)", uom="TON", pack_qty=1, node="SCM-02-03-001", mult=1.00),
        dict(code="DEMUR", desc="Standby time (hr)", uom="HR", pack_qty=1, node="SCM-06-02-002", mult=1.00),
        dict(code="FUEL-SC", desc="Fuel surcharge", uom="EA", pack_qty=1, node="SCM-06-01-001", mult=1.00),
    ],
}
# The five water haulers share a template; each gets its own wording and price level
HAULER_TEMPLATE = [
    dict(code="PW-HAUL", desc="Produced water haul (per bbl)", uom="BBL", pack_qty=1, node="SCM-05-01-001", mult=1.00),
    dict(code="SWD-FEE", desc="SWD disposal fee (per bbl)", uom="BBL", pack_qty=1, node="SCM-05-01-002", mult=1.00),
    dict(code="FW-SRC", desc="Fresh water sourcing (per bbl)", uom="BBL", pack_qty=1, node="SCM-05-02-001", mult=1.00),
    dict(code="WT-XFER", desc="Water transfer (per bbl)", uom="BBL", pack_qty=1, node="SCM-05-02-002", mult=1.00),
    dict(code="VAC-HR", desc="Vac truck (per hr)", uom="HR", pack_qty=1, node="SCM-05-03-001", mult=1.00),
    dict(code="HOTOIL-HR", desc="Hot oil unit (per hr)", uom="HR", pack_qty=1, node="SCM-05-03-002", mult=1.00),
    dict(code="LOAD-MIN", desc="Minimum load charge", uom="EA", pack_qty=1, node="SCM-06-02-003", mult=1.00),
    dict(code="FUEL-SC", desc="Fuel surcharge", uom="EA", pack_qty=1, node="SCM-06-01-001", mult=1.00),
]
HAULER_STYLE = {   # LIFNR -> (price multiplier, description style)
    "0000100018": (1.04, "upper"),   # Hackberry Hauling
    "0000100019": (0.97, "title"),   # Two Dogs Trucking
    "0000100020": (1.00, "code"),    # Sandhills Water Transfer
    "0000100021": (1.09, "upper"),   # Pecos Valley Vac Trucks
    "0000100022": (0.95, "title"),   # Rattlesnake Hauling
}

# OCTG and rentals come from the long tail of "Other" vendors: each vendor gets a slice of these
# templates with one of several wordings (that is CP3: five ways to say the same casing).
OCTG_DESCRIPTIONS = {
    "SCM-03-01-003": [("CSG 5.500 20.00 P110 BTC R3", "JT", 42.0), ("5-1/2in 20# P-110 BTC casing, per ft", "FT", 1.0),
                      ("CASING 5 1/2\" 20.00# P-110 BTC RANGE 3 (jt)", "JT", 42.0), ("Prod csg 5.5 x 20 P110 BTC-M, ft", "FT", 1.0),
                      ("OCTG 5.5 20PPF P110 BUTTRESS R3 PE", "JT", 42.0), ("5.500 OD 20# P110 BTC SMLS casing / ft", "FT", 1.0)],
    "SCM-03-01-004": [("CSG 5.500 17.00 P110 BTC R3", "JT", 42.0), ("5-1/2in 17# P-110 BTC casing, per ft", "FT", 1.0), ("CASING 5 1/2\" 17# P110 BTC R3", "JT", 42.0)],
    "SCM-03-01-002": [("CSG 9.625 40.00 L80 BTC R3", "JT", 42.0), ("9-5/8in 40# L-80 BTC casing, per ft", "FT", 1.0), ("INTERMEDIATE CASING 9 5/8 40# L80 BTC (jt)", "JT", 42.0)],
    "SCM-03-01-001": [("CSG 13.375 54.50 J55 BTC R3", "JT", 42.0), ("13-3/8in 54.5# J-55 BTC surface casing, per ft", "FT", 1.0), ("SURF CSG 13 3/8 54.5# J55 BTC", "JT", 42.0)],
    "SCM-03-02-001": [("TBG 2.875 6.50 L80 EUE 8RD R2", "JT", 31.0), ("2-7/8in 6.5# L-80 EUE tubing, per ft", "FT", 1.0), ("TUBING 2 7/8\" 6.5# L80 EUE 8RD (jt)", "JT", 31.0)],
    "SCM-03-02-002": [("TBG 2.375 4.70 J55 EUE R2", "JT", 31.0), ("2-3/8in 4.7# J-55 EUE tubing, per ft", "FT", 1.0)],
    "SCM-03-03-001": [("Bow spring centralizer 5-1/2 x 8-1/2", "EA", 1.0), ("CENTRALIZER BOW 5.5X8.5", "EA", 1.0)],
    "SCM-03-03-002": [("Float shoe & collar set 5-1/2 BTC", "EA", 1.0), ("FLOAT EQUIP 5.5 BTC SHOE+COLLAR", "EA", 1.0)],
    "SCM-03-04-001": [("Wellhead system 5M multibowl 13-3/8 x 9-5/8 x 5-1/2", "EA", 1.0), ("WELLHEAD ASSY 5000PSI MULTIBOWL", "EA", 1.0)],
}
RENTAL_DESCRIPTIONS = {
    "SCM-04-01-001": [("Frac tank 500 bbl rental (day)", "DAY", 1.0), ("500BBL FRAC TANK DAILY", "DAY", 1.0), ("Frac tank rental, 500 bbl, monthly", "MONTH", 30.0)],
    "SCM-04-01-002": [("Mud tank / roll-off rental (day)", "DAY", 1.0), ("CUTTINGS BOX RENTAL DAILY", "DAY", 1.0)],
    "SCM-04-02-001": [("Light tower rental (day)", "DAY", 1.0), ("LIGHT PLANT 4-LAMP DAILY", "DAY", 1.0), ("Light tower, monthly rate", "MONTH", 30.0)],
    "SCM-04-02-002": [("100kW generator rental (day)", "DAY", 1.0), ("GENSET 100KW DAILY", "DAY", 1.0), ("Generator 100 kW, weekly", "WEEK", 7.0)],
    "SCM-04-03-001": [("Flowback iron & manifold package (day)", "DAY", 1.0), ("FLOWBACK EQUIP PKG 10K DAILY", "DAY", 1.0)],
    "SCM-04-03-002": [("BOP stack 5M double ram rental (day)", "DAY", 1.0), ("BOP 5000PSI DAILY", "DAY", 1.0)],
    "SCM-04-04-001": [("Office trailer 12x60 rental (day)", "DAY", 1.0), ("CREW TRAILER MONTHLY", "MONTH", 30.0)],
    "SCM-04-04-002": [("Telehandler 10K rental (day)", "DAY", 1.0), ("FORKLIFT TELEHANDLER WEEKLY", "WEEK", 7.0)],
    "SCM-04-05-001": [("Lay-flat line 10in rental per 1000 ft-day", "DAY", 1.0), ("LAYFLAT HOSE RENTAL DAILY", "DAY", 1.0)],
}
# Distributor / misc items that stay unclassified (CP4) — vague descriptions, no spec
UNCLASSIFIED_DESCRIPTIONS = [
    ("MISC SUPPLIES", "EA"), ("SHOP SUPPLIES", "EA"), ("PART# 44-1093", "EA"), ("MATERIAL PER TICKET", "EA"), ("RENTAL EQUIP PER TICKET", "EA"),
    ("EQUIPMENT RENTAL - SEE ATTACHED", "EA"), ("FIELD TICKET 7731 CHARGES", "EA"), ("HARDWARE", "EA"), ("VALVE 2IN", "EA"), ("SUPPLIES - LOCATION", "EA"),
    ("RENTAL - MONTHLY", "MONTH"), ("SERVICE CALL", "EA"), ("CONSUMABLES", "EA"), ("MISC RENTAL", "DAY"),
]

# OpenInvoice cost codes (what accounting sees) by SPEND_INVOICE cost category
OI_COST_CODES = {
    "Chemicals": ("LOE-CHEM", "Chemicals - treating"),
    "Proppant": ("CAP-PROP", "Completion - proppant"),
    "Casing & tubulars": ("CAP-OCTG", "Drilling - casing and tubulars"),
    "Rentals": ("CAP-RENT", "Rental equipment"),
    "Water Disposal": ("LOE-SWD", "Water hauling and disposal"),
    "Water sourcing/transfer": ("CAP-WTR", "Completion - water sourcing and transfer"),
}

# Supplier price books loaded in OpenInvoice: (LIFNR -> pricebook version, effective date, escalation %)
PRICEBOOK_VERSIONS = {
    CORROSION_CONTROL: [("CCC-PB-2024A", "2024-01-01", "2024-12-31", 0.0), ("CCC-PB-2025A", "2025-01-01", "2026-12-31", 2.5)],
    BASIN_CHEMICAL: [("BSN-PB-2024", "2024-01-01", "2024-12-31", 0.0), ("BSN-PB-2025", "2025-01-01", "2026-12-31", 3.0)],
    KERMIT: [("KSC-2024", "2024-01-01", "2025-06-30", 0.0), ("KSC-2025H2", "2025-07-01", "2026-12-31", 3.0)],
    MONAHANS: [("MPL-2024", "2024-01-01", "2025-12-31", 0.0), ("MPL-2026", "2026-01-01", "2026-12-31", 2.0)],
    REDLINE: [("RLS-2024", "2024-01-01", "2025-12-31", 0.0), ("RLS-2026", "2026-01-01", "2026-12-31", 2.0)],
}
# Redline invoices RL100 at this premium over its 2026 pricebook rate from February 2026 (CP2)
REDLINE_OVERBILL_FROM = "2026-02-01"
REDLINE_OVERBILL_PCT = 0.085


# --------------------------------------------------------------------------------------
# Supplier document archive (S3): file names cited by SCM_ITEM_CLASSIFICATION.SOURCE_DOCUMENT and
# OI_PRICEBOOK_ITEM.SOURCE_DOCUMENT and rendered by supplier_docs.py. Keep both sides in sync here.
# --------------------------------------------------------------------------------------
def _slug(text: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")


def spec_sheet_filename(supplier_name: str, item_code: str) -> str:
    """Technical data sheet / catalog page for one supplier item family, e.g.
    Corrosion_Control_Chem_LLC_CS-7000_Technical_Data_Sheet.pdf"""
    return f"{_slug(supplier_name)}_{_slug(item_code)}_Technical_Data_Sheet.pdf"


def pricing_exhibit_filename(supplier_name: str, pricebook_version: str) -> str:
    """MSA Exhibit B rate schedule a price book version was loaded from, e.g.
    Basin_Chemical_LLC_BSN-PB-2025_MSA_Exhibit_B_Pricing.pdf"""
    return f"{_slug(supplier_name)}_{_slug(pricebook_version)}_MSA_Exhibit_B_Pricing.pdf"


def octg_mill_sheet_filename(node_id: str) -> str:
    """Generic OCTG mill data sheet used to classify the long-tail casing descriptions."""
    return f"OCTG_Mill_Data_Sheet_{_slug(TAX_BY_ID[node_id][3])}.pdf"
