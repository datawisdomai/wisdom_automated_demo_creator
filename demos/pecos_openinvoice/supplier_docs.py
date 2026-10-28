"""supplier_docs.py — render the supplier document archive (stretch goal of the Pecos Ridge
OpenInvoice demo): the unstructured evidence behind SCM_ITEM_CLASSIFICATION.SOURCE_DOCUMENT and
OI_PRICEBOOK_ITEM.SOURCE_DOCUMENT.

`demo docs pecos_openinvoice` calls `render(spec, out_dir)` through the `generated_documents` hook
in demo.yaml. Three document types are rendered into out_dir (build/supplier_docs):

  a. one supplier technical data sheet per hero supplier item family (CS-7000, BC-220, FM100-DLV ...)
     — the sheet the steward read to map the marketing name to a generic product;
  b. one OCTG mill data sheet per casing / tubing / accessory node, with the alias table of every
     description variant the long-tail vendors print on invoices and its conversion to feet;
  c. one MSA Exhibit B rate schedule per supplier price book version, every rate taken from the
     OI_PRICEBOOK_ITEM frame (nothing on a pricing exhibit is invented).

Inputs are the parquet frames `demo generate` caches (OI_SUPPLIER, OI_PRICEBOOK_ITEM,
SCM_ITEM_CLASSIFICATION, SCM_PRODUCT_TAXONOMY) plus catalog.py. File names come from the frames
when they cite one (SOURCE_DOCUMENT) and from catalog's file-name helpers otherwise, so the names
on the PDFs always equal the names in the tables.
"""
from __future__ import annotations

import re
import zlib
from pathlib import Path

import pandas as pd

import catalog
from demo_creator.documents import render_pdf

COMPANY = "Pecos Ridge Energy LLC"
COMPANY_ADDRESS = "600 N. Marienfeld Street, Suite 900, Midland, TX 79701"
FEES_FAMILY = "Fees & surcharges"
LOGISTICS_NODE = "SCM-02-04-001"

# Used only when the OI_SUPPLIER frame is not cached: S4_VENDOR_LFA1 NAME1 / ORT01 / REGIO in title case
S4_FALLBACK = {
    catalog.CORROSION_CONTROL: ("Corrosion Control Chem LLC", "Liberal", "KS"),
    catalog.BASIN_CHEMICAL: ("Basin Chemical LLC", "Liberal", "KS"),
    catalog.KERMIT: ("Kermit Sand Co LLC", "Liberal", "KS"),
    catalog.MONAHANS: ("Monahans Proppant LLC", "Oklahoma City", "OK"),
    catalog.REDLINE: ("Redline Sand LLC", "Midland", "TX"),
    "0000100018": ("Hackberry Hauling LLC", "Hobbs", "NM"),
    "0000100019": ("Two Dogs Trucking LLC", "Pecos", "TX"),
    "0000100020": ("Sandhills Water Transfer LLC", "Monahans", "TX"),
    "0000100021": ("Pecos Valley Vac Trucks LLC", "Carlsbad", "NM"),
    "0000100022": ("Rattlesnake Hauling LLC", "Odessa", "TX"),
}

# Fictional supplier signatories for the Exhibit B signature block (deterministic per vendor)
SIGNATORIES = {
    catalog.CORROSION_CONTROL: ("Dale Pruitt", "Vice President, Sales"),
    catalog.BASIN_CHEMICAL: ("Marcy Holloway", "Director, Permian and Midcon Accounts"),
    catalog.KERMIT: ("Travis Keel", "Vice President, Commercial"),
    catalog.MONAHANS: ("Renee Castillo", "Chief Commercial Officer"),
    catalog.REDLINE: ("Boyd Lattimer", "President"),
}
_SIGNATORY_POOL = [("Carla Jennings", "General Manager"), ("Wade Nolan", "Owner"), ("Priya Natarajan", "Vice President, Operations"),
                   ("Hank Delgado", "Managing Member"), ("Lorraine Pike", "Director of Sales")]
_STREETS = ["Industrial Boulevard", "W. Pancake Boulevard", "Commerce Drive", "E. Highway 80", "N. Garfield Street",
            "S. County Road 1140", "Rankin Highway", "W. 8th Street", "Loop 250 Frontage Road", "Refinery Road"]
_AREA_CODE = {"KS": "620", "OK": "405", "TX": "432", "NM": "575"}


# --------------------------------------------------------------------------------------
# Small deterministic helpers
# --------------------------------------------------------------------------------------
def _h(text: str) -> int:
    return zlib.crc32(text.encode("utf-8"))


def _money(x) -> str:
    return f"${float(x):,.2f}"


def _date(d) -> str:
    return pd.Timestamp(d).strftime("%B %-d, %Y")


def _qty(x) -> str:
    x = float(x)
    return f"{int(x):,}" if x.is_integer() else f"{x:,.2f}"


def _title_case(name: str) -> str:
    keep = {"LLC", "LP", "LLP", "INC", "CO", "USA"}
    return " ".join(w if w.upper() in keep else w.capitalize() for w in name.split())


def family_code(item_code: str) -> str:
    """Product family = the supplier item code without its pack suffix (CS-7000-T -> CS-7000,
    BC-CLAY-B -> BC-CLAY, FM100-DLV stays FM100-DLV). Used only when the classification frame does
    not already cite a spec-sheet file for the item."""
    return re.sub(r"-(T|D|B|P)$", "", item_code)


_PAREN_UNIT = re.compile(r"\s*\((gal|ton|hr|bbl)\)\s*$", re.I)
_PACK_WORDS = re.compile(r",?\s*(\d+\s*(gal|lb)\s*)?\b(tote|drum|pail|bulk( delivery)?|bag)\b.*$", re.I)
_PROP_WORDS = re.compile(r",?\s*\b(delivered( to pad)?|FOB \w+)\b.*$", re.I)


def product_name(descriptions: list[str]) -> str:
    """Marketing product name = the longest invoice description once the pack and delivery words are
    removed (CorroShield CS-7000 Corrosion Inhibitor 55 gal drum -> CorroShield CS-7000 Corrosion Inhibitor)."""
    cands = []
    for d in descriptions:
        n = _PAREN_UNIT.sub("", d)
        n = _PACK_WORDS.sub("", n)
        n = _PROP_WORDS.sub("", n)
        cands.append(_PAREN_UNIT.sub("", n).strip(" ,-"))
    return max(cands, key=len)


def pack_label(uom: str, pack_qty) -> str:
    q = _qty(pack_qty)
    u = (uom or "").upper()
    return {"TOTE": f"{q} gal IBC tote", "DRUM": f"{q} gal poly drum", "PAIL": f"{q} gal pail",
            "GAL": "Bulk, per gallon (transport delivery)", "BAG": f"{q} lb bag", "TON": "Per short ton (2,000 lb)",
            "HR": "Per hour", "EA": "Each", "BBL": "Per barrel"}.get(u, u)


def letterhead(name: str, city: str | None, state: str | None) -> str:
    h = _h(name)
    city = city or "Midland"
    state = (state or "TX").upper()
    street = f"{1000 + h % 8000} {_STREETS[h % len(_STREETS)]}"
    phone = f"({_AREA_CODE.get(state, '432')}) 555-{100 + (h // 7) % 900:04d}"
    domain = re.sub(r"[^a-z0-9]", "", name.lower().replace(" llc", "").replace(" lp", ""))
    return f"{name}, {street}, {city}, {state} {10000 + (h // 13) % 89999:05d}  ·  {phone}  ·  sales@{domain}.example"


def revision_date(key: str) -> str:
    h = _h("rev:" + key)
    year = 2024 + h % 2
    month = 1 + (h // 2) % 12
    day = 1 + (h // 24) % 28
    return pd.Timestamp(year=year, month=month, day=day).strftime("%B %-d, %Y")


# --------------------------------------------------------------------------------------
# Chemical technical content (plausible, generic; keyed by taxonomy node)
# --------------------------------------------------------------------------------------
DOSAGE = {
    "SCM-01-01-001": "Continuous injection at 10-25 ppm of total produced fluids through the wellhead injection quill or a capillary string, or batch treatment at 1-2 gal per 1,000 ft of tubing every 7-14 days followed by a 2-5 bbl flush. Residual film inhibitor should be verified at the flowline sample point monthly.",
    "SCM-01-01-002": "Batch treat 2-5 gal per well down the annulus with a 2-5 bbl flush of produced oil or diesel every 7-14 days. Film persistence is typically 10-14 days under Permian and Anadarko producing conditions.",
    "SCM-01-02-001": "Continuous injection at 5-25 ppm of produced water downstream of the pump. Raise to 50 ppm for 48 hours after a workover or any change in water cut. Verify residual phosphonate at 2-5 ppm.",
    "SCM-01-02-002": "Squeeze treatment: 10-20 percent active solution placed into the near-wellbore formation with a 5-10 bbl overflush and 12-24 hours shut-in. Squeeze life 6-12 months depending on water rate.",
    "SCM-01-03-001": "Batch treat 10-55 gal down the tubing or annulus with a hot-oil or produced-fluid flush; allow 2-4 hours contact before returning the well to production. Suitable as a hot-oil alternative on flowlines.",
    "SCM-01-03-002": "Continuous injection at 100-500 ppm of produced oil upstream of the cloud-point location, typically at the wellhead or downhole through a capillary string.",
    "SCM-01-04-001": "Continuous injection into the gas stream at 1-3 gal per pound of H2S removed, by direct injection ahead of the separator or in a contact tower. Confirm sales-gas H2S below 4 ppm by Draeger or lead-acetate test.",
    "SCM-01-04-002": "Inject at 2-10 ppm per ppm of dissolved oxygen into frac or injection water ahead of the pumps. Verify with a dissolved-oxygen meter at the discharge.",
    "SCM-01-05-001": "Frac water: 100-500 ppm per stage on the fly. Produced-water and injection systems: slug treat at 500-1,000 ppm for 4-6 hours weekly. Rotate with a THPS biocide quarterly to prevent resistance.",
    "SCM-01-05-002": "Slug treat at 200-500 ppm for 4-6 hours weekly in produced-water and injection systems; continuous at 25-50 ppm for high-activity systems.",
    "SCM-01-06-001": "Inject 20-100 ppm of total fluid ahead of the heater-treater or FWKO. Optimise by bottle test at the tank battery; reduce dosage in steps of 5 ppm until BS&W rises.",
    "SCM-01-06-002": "Inject 5-50 ppm of produced water ahead of the skim tank, gun barrel or flotation unit. Overtreatment causes re-emulsification; confirm by jar test.",
    "SCM-01-07-001": "Capillary injection at 0.5-2 gal per day or batch down the annulus; adjust rate to maintain liquid unloading on the gas well. Compatible with methanol co-injection.",
    "SCM-01-07-002": "Inject at 0.1-2 gal per MMscf depending on line temperature and water content; winter operations on gathering lines and wellhead chokes. Rates above 2 gal per MMscf indicate free water that should be removed upstream.",
    "SCM-01-08-001": "0.5-1.0 gallon per thousand gallons (gpt) in slickwater stages, added on the fly at the blender; hydrates in under 60 seconds in fresh and brackish water.",
    "SCM-01-08-002": "Spearhead 1,000-3,000 gal per stage ahead of the pad to break down near-wellbore damage and perforation tunnels. Inhibitor loading is matched to bottom-hole temperature.",
    "SCM-01-08-003": "1-2 gpt in fresh and brackish frac water as a permanent clay stabiliser; replaces 2 percent KCl.",
    "SCM-01-08-004": "0.25-2 lb per thousand gallons of fluid according to the breaker schedule; stage the loading with temperature and desired break time.",
}
PHYSICAL = {
    "SCM-01-01-001": [("Appearance", "Clear amber liquid"), ("Specific gravity at 60 F", "1.02 - 1.06"), ("pH (neat)", "7.5 - 9.0"), ("Flash point (PMCC)", "> 140 F"), ("Active content", "35 - 40 percent imidazoline and quaternary amine"), ("Pour point", "< -20 F"), ("Solubility", "Water-soluble; dispersible in oil")],
    "SCM-01-01-002": [("Appearance", "Dark amber liquid"), ("Specific gravity at 60 F", "0.90 - 0.94"), ("pH (10 percent in water)", "6.5 - 8.0"), ("Flash point (PMCC)", "> 105 F"), ("Active content", "25 - 30 percent oil-soluble amide / imidazoline"), ("Pour point", "< -10 F"), ("Solubility", "Oil-soluble; water-dispersible")],
    "SCM-01-02-001": [("Appearance", "Clear to pale yellow liquid"), ("Specific gravity at 60 F", "1.12 - 1.18"), ("pH (neat)", "3.0 - 5.0"), ("Flash point (PMCC)", "> 200 F"), ("Active content", "20 - 25 percent phosphonate"), ("Freeze point", "< 0 F"), ("Solubility", "Completely water-soluble")],
    "SCM-01-02-002": [("Appearance", "Clear liquid"), ("Specific gravity at 60 F", "1.08 - 1.14"), ("pH (neat)", "2.5 - 4.0"), ("Flash point (PMCC)", "> 200 F"), ("Active content", "10 - 20 percent phosphonate, squeeze grade"), ("Solubility", "Completely water-soluble")],
    "SCM-01-03-001": [("Appearance", "Clear, colourless to light yellow liquid"), ("Specific gravity at 60 F", "0.86 - 0.89"), ("Flash point (PMCC)", "> 105 F"), ("Active content", "90 - 95 percent aromatic hydrocarbon blend"), ("Pour point", "< -40 F"), ("Solubility", "Oil-soluble; insoluble in water")],
    "SCM-01-03-002": [("Appearance", "Amber liquid"), ("Specific gravity at 60 F", "0.88 - 0.92"), ("Flash point (PMCC)", "> 120 F"), ("Active content", "30 - 35 percent crystal modifier polymer"), ("Pour point", "< 0 F"), ("Solubility", "Oil-soluble; dispersible in water")],
    "SCM-01-04-001": [("Appearance", "Clear, colourless to pale yellow liquid"), ("Specific gravity at 60 F", "1.10 - 1.16"), ("pH (neat)", "10.5 - 12.0"), ("Flash point (PMCC)", "> 200 F"), ("Active content", "55 - 65 percent MEA triazine"), ("Freeze point", "< -20 F"), ("Solubility", "Completely water-soluble")],
    "SCM-01-04-002": [("Appearance", "Clear, colourless liquid"), ("Specific gravity at 60 F", "1.36 - 1.40"), ("pH (neat)", "4.5 - 5.5"), ("Flash point (PMCC)", "None"), ("Active content", "65 percent ammonium bisulfite"), ("Freeze point", "< 15 F"), ("Solubility", "Completely water-soluble")],
    "SCM-01-05-001": [("Appearance", "Clear, colourless liquid"), ("Specific gravity at 60 F", "1.05 - 1.08"), ("pH (neat)", "3.0 - 4.5"), ("Flash point (PMCC)", "None"), ("Active content", "25 percent glutaraldehyde"), ("Freeze point", "< 0 F"), ("Solubility", "Completely water-soluble")],
    "SCM-01-05-002": [("Appearance", "Clear, colourless liquid"), ("Specific gravity at 60 F", "1.30 - 1.36"), ("pH (neat)", "3.0 - 5.0"), ("Flash point (PMCC)", "None"), ("Active content", "50 percent THPS"), ("Freeze point", "< -20 F"), ("Solubility", "Completely water-soluble")],
    "SCM-01-06-001": [("Appearance", "Dark amber liquid"), ("Specific gravity at 60 F", "0.92 - 0.96"), ("Flash point (PMCC)", "> 100 F"), ("Active content", "40 - 45 percent resin and oxyalkylate blend"), ("Pour point", "< -25 F"), ("Solubility", "Oil-soluble; dispersible in water")],
    "SCM-01-06-002": [("Appearance", "Clear to hazy liquid"), ("Specific gravity at 60 F", "1.02 - 1.06"), ("pH (neat)", "4.0 - 6.0"), ("Flash point (PMCC)", "> 200 F"), ("Active content", "20 - 30 percent cationic polymer"), ("Freeze point", "< 10 F"), ("Solubility", "Completely water-soluble")],
    "SCM-01-07-001": [("Appearance", "Clear amber liquid"), ("Specific gravity at 60 F", "1.00 - 1.04"), ("pH (neat)", "6.5 - 8.5"), ("Flash point (PMCC)", "> 140 F"), ("Active content", "30 - 40 percent foaming surfactant"), ("Freeze point", "< -20 F"), ("Solubility", "Completely water-soluble")],
    "SCM-01-07-002": [("Appearance", "Clear, colourless liquid"), ("Specific gravity at 60 F", "0.79 - 0.80"), ("Flash point (closed cup)", "52 F"), ("Active content", "99 percent methanol minimum"), ("Freeze point", "-144 F"), ("Solubility", "Miscible with water")],
    "SCM-01-08-001": [("Appearance", "White to off-white emulsion"), ("Specific gravity at 60 F", "1.01 - 1.05"), ("pH (neat)", "6.0 - 8.0"), ("Flash point (PMCC)", "> 200 F"), ("Active content", "28 - 32 percent polyacrylamide"), ("Viscosity at 77 F", "600 - 1,200 cP"), ("Solubility", "Inverts in fresh and brackish water")],
    "SCM-01-08-002": [("Appearance", "Clear to pale yellow liquid"), ("Specific gravity at 60 F", "1.07 - 1.08"), ("Concentration", "15 percent hydrochloric acid, inhibited"), ("Flash point (PMCC)", "None"), ("Iron control", "Included to 2,000 ppm Fe"), ("Solubility", "Completely water-soluble")],
    "SCM-01-08-003": [("Appearance", "Clear, colourless liquid"), ("Specific gravity at 60 F", "1.09 - 1.11"), ("pH (neat)", "7.0 - 9.0"), ("Flash point (PMCC)", "None"), ("Active content", "70 percent choline chloride"), ("Freeze point", "< -10 F"), ("Solubility", "Completely water-soluble")],
    "SCM-01-08-004": [("Appearance", "White crystalline solid"), ("Bulk density", "63 lb/ft3"), ("pH (1 percent solution)", "3.0 - 4.5"), ("Active content", "98 percent ammonium persulfate minimum"), ("Decomposition temperature", "> 248 F"), ("Solubility", "Readily water-soluble")],
}
_PHYSICAL_DEFAULT = [("Appearance", "Clear liquid"), ("Specific gravity at 60 F", "1.00 - 1.05"), ("pH (neat)", "6.0 - 8.0"), ("Flash point (PMCC)", "> 140 F"), ("Active content", "As specified")]
HANDLING = {
    "SCM-01-07-002": "Flammable liquid (NFPA 3). Store in grounded, bonded containers away from ignition sources; use explosion-proof pumps. Tote and bulk tank vents must be flame-arrested. Toxic by ingestion and inhalation; wear nitrile gloves and splash goggles. Shelf life unlimited in sealed containers.",
    "SCM-01-08-002": "Corrosive. Store in HDPE or rubber-lined vessels; never in carbon steel. Wear acid-resistant gloves, face shield and apron; have an eye-wash station within 25 ft of the transfer point. Keep away from oxidisers and bases. Inhibitor is effective for 72 hours after mixing at temperatures above 150 F.",
    "SCM-01-08-004": "Oxidiser. Keep bags dry and sealed; store away from combustibles, reducing agents and heat. Do not return spilled product to the bag. Wear dust mask and gloves when handling. Shelf life 12 months in original packaging.",
    "SCM-01-04-002": "Store below 100 F out of direct sunlight; product releases sulfur dioxide on contact with acids. Keep away from oxidisers. Wear gloves and goggles. Shelf life 6 months; retest active content before use after that.",
}
_HANDLING_DEFAULT = ("Store in original containers between 20 F and 120 F out of direct sunlight; product may thicken below the pour point and should be warmed before pumping. Keep containers closed to prevent water pick-up. Wear nitrile gloves and splash goggles; see the SDS for first-aid measures. Compatible with carbon steel, stainless steel, HDPE and fibreglass tanks. Shelf life 24 months in sealed containers. Empty drums and totes are returned on the next delivery or disposed of under the environmental fee on the invoice.")

# --------------------------------------------------------------------------------------
# Proppant technical content (per node; supplier-specific jitter applied deterministically)
# --------------------------------------------------------------------------------------
PROPPANT = {
    "SCM-02-01-001": dict(label="100 mesh", sieves=[("50", 0.4), ("70", 7.9), ("100", 46.2), ("140", 38.1), ("200", 6.4), ("Pan", 1.0)],
                          crush=[("7,000 psi", 7.6), ("8,000 psi", 9.8)], kvalue="7K", sph=0.7, rnd=0.7, turb=160, bulk=93.5, sg=2.65, acid=1.8),
    "SCM-02-01-002": dict(label="40/70 mesh", sieves=[("30", 0.2), ("40", 9.6), ("50", 42.3), ("70", 43.9), ("100", 3.6), ("Pan", 0.4)],
                          crush=[("7,000 psi", 6.1), ("8,000 psi", 8.9)], kvalue="8K", sph=0.7, rnd=0.7, turb=140, bulk=95.0, sg=2.65, acid=1.6),
    "SCM-02-02-001": dict(label="30/50 mesh", sieves=[("20", 0.1), ("30", 8.7), ("40", 50.6), ("50", 37.8), ("70", 2.5), ("Pan", 0.3)],
                          crush=[("9,000 psi", 7.2), ("10,000 psi", 9.5)], kvalue="9K", sph=0.8, rnd=0.8, turb=90, bulk=97.0, sg=2.65, acid=0.9),
    "SCM-02-03-001": dict(label="20/40 mesh resin-coated", sieves=[("16", 0.1), ("20", 7.8), ("30", 55.2), ("40", 34.6), ("50", 2.0), ("Pan", 0.3)],
                          crush=[("10,000 psi", 4.9), ("12,000 psi", 7.4)], kvalue="10K", sph=0.8, rnd=0.8, turb=40, bulk=92.0, sg=2.58, acid=0.7),
}

# --------------------------------------------------------------------------------------
# OCTG mill data (plausible API 5CT / 10D / 6A values; one entry per node in catalog.OCTG_DESCRIPTIONS)
# --------------------------------------------------------------------------------------
OCTG_SPECS = {
    "SCM-03-01-003": dict(kind="tubular", rows=[("Nominal OD", "5.500 in (5-1/2 in)"), ("Nominal weight", "20.00 lb/ft"), ("Grade", "P-110"), ("Connection", "BTC (API buttress thread)"), ("Range", "R3"), ("Wall thickness", "0.361 in"), ("Inside diameter", "4.778 in"), ("Drift diameter", "4.653 in (API)"), ("Collapse resistance", "11,100 psi"), ("Internal yield (burst)", "12,640 psi"), ("Pipe body yield strength", "641,000 lbf"), ("Joint strength (BTC)", "607,000 lbf"), ("Joint length", "42 ft nominal (R3, 38-45 ft)")]),
    "SCM-03-01-004": dict(kind="tubular", rows=[("Nominal OD", "5.500 in (5-1/2 in)"), ("Nominal weight", "17.00 lb/ft"), ("Grade", "P-110"), ("Connection", "BTC (API buttress thread)"), ("Range", "R3"), ("Wall thickness", "0.304 in"), ("Inside diameter", "4.892 in"), ("Drift diameter", "4.767 in (API)"), ("Collapse resistance", "7,480 psi"), ("Internal yield (burst)", "10,640 psi"), ("Pipe body yield strength", "546,000 lbf"), ("Joint strength (BTC)", "519,000 lbf"), ("Joint length", "42 ft nominal (R3, 38-45 ft)")]),
    "SCM-03-01-002": dict(kind="tubular", rows=[("Nominal OD", "9.625 in (9-5/8 in)"), ("Nominal weight", "40.00 lb/ft"), ("Grade", "L-80"), ("Connection", "BTC (API buttress thread)"), ("Range", "R3"), ("Wall thickness", "0.395 in"), ("Inside diameter", "8.835 in"), ("Drift diameter", "8.679 in (API)"), ("Collapse resistance", "3,090 psi"), ("Internal yield (burst)", "5,750 psi"), ("Pipe body yield strength", "916,000 lbf"), ("Joint strength (BTC)", "1,002,000 lbf"), ("Joint length", "42 ft nominal (R3, 38-45 ft)")]),
    "SCM-03-01-001": dict(kind="tubular", rows=[("Nominal OD", "13.375 in (13-3/8 in)"), ("Nominal weight", "54.50 lb/ft"), ("Grade", "J-55"), ("Connection", "BTC (API buttress thread)"), ("Range", "R3"), ("Wall thickness", "0.380 in"), ("Inside diameter", "12.615 in"), ("Drift diameter", "12.459 in (API)"), ("Collapse resistance", "1,130 psi"), ("Internal yield (burst)", "2,730 psi"), ("Pipe body yield strength", "853,000 lbf"), ("Joint strength (BTC)", "909,000 lbf"), ("Joint length", "42 ft nominal (R3, 38-45 ft)")]),
    "SCM-03-02-001": dict(kind="tubular", rows=[("Nominal OD", "2.875 in (2-7/8 in)"), ("Nominal weight", "6.50 lb/ft"), ("Grade", "L-80"), ("Connection", "EUE 8rd (external upset)"), ("Range", "R2"), ("Wall thickness", "0.217 in"), ("Inside diameter", "2.441 in"), ("Drift diameter", "2.347 in (API)"), ("Collapse resistance", "11,160 psi"), ("Internal yield (burst)", "10,570 psi"), ("Pipe body yield strength", "145,000 lbf"), ("Joint strength (EUE)", "145,000 lbf"), ("Joint length", "31 ft nominal (R2, 28-32 ft)")]),
    "SCM-03-02-002": dict(kind="tubular", rows=[("Nominal OD", "2.375 in (2-3/8 in)"), ("Nominal weight", "4.70 lb/ft"), ("Grade", "J-55"), ("Connection", "EUE 8rd (external upset)"), ("Range", "R2"), ("Wall thickness", "0.190 in"), ("Inside diameter", "1.995 in"), ("Drift diameter", "1.901 in (API)"), ("Collapse resistance", "7,680 psi"), ("Internal yield (burst)", "7,700 psi"), ("Pipe body yield strength", "71,700 lbf"), ("Joint strength (EUE)", "71,700 lbf"), ("Joint length", "31 ft nominal (R2, 28-32 ft)")]),
    "SCM-03-03-001": dict(kind="accessory", rows=[("Product", "Bow-spring casing centralizer, hinged, non-welded"), ("Casing size", "5-1/2 in"), ("Hole size", "8-1/2 in"), ("Bows", "6, spring steel, zinc-phosphate coated"), ("Starting force (API 10D)", "< 400 lbf"), ("Restoring force (API 10D)", "> 1,200 lbf at 67 percent standoff"), ("Stop collar", "Set-screw, 5-1/2 in, supplied separately"), ("Standard", "API 10D / ISO 10427-1")]),
    "SCM-03-03-002": dict(kind="accessory", rows=[("Product", "Float shoe and float collar set, non-rotating, PDC-drillable"), ("Casing size and connection", "5-1/2 in BTC box up"), ("Pressure rating", "5,000 psi differential"), ("Temperature rating", "350 F"), ("Valve", "Spring-loaded poppet, double valve in collar"), ("Nose", "Concrete, down-jet"), ("Standard", "API 10F category IIIC")]),
    "SCM-03-04-001": dict(kind="accessory", rows=[("Product", "Multibowl wellhead system, 5,000 psi WP"), ("Casing program", "13-3/8 in surface x 9-5/8 in intermediate x 5-1/2 in production"), ("Casing head", "13-5/8 in 5M, slip-on-weld bottom"), ("Tubing head", "11 in 5M x 7-1/16 in 5M"), ("Tubing hanger", "2-7/8 in EUE, extended neck"), ("Material class", "API 6A DD-NL, PSL 2, temperature class P-U"), ("Standard", "API 6A 21st edition")]),
}


# --------------------------------------------------------------------------------------
# Frame access
# --------------------------------------------------------------------------------------
def _frame(spec, table: str, *, required: bool) -> pd.DataFrame | None:
    path = spec.paths.parquet(table)
    if not path.exists():
        if required:
            raise FileNotFoundError(
                f"{table} is not in the parquet cache ({path}). Run `demo generate pecos_openinvoice` first; "
                "supplier_docs.py renders from the generated frames so every value on a PDF equals the table it came from.")
        return None
    return pd.read_parquet(path)


def _suppliers(frame: pd.DataFrame | None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if frame is not None:
        for _, r in frame.drop_duplicates("LIFNR").iterrows():
            out[str(r.LIFNR)] = dict(name=str(r.SUPPLIER_NAME), city=r.get("SUPPLIER_CITY"), state=r.get("SUPPLIER_STATE"),
                                    terms=r.get("PAYMENT_TERMS"), basin=r.get("PRIMARY_BASIN"))
    for lifnr, (name, city, state) in S4_FALLBACK.items():
        out.setdefault(lifnr, dict(name=_title_case(name), city=city, state=state, terms=None, basin=None))
    return out


def _taxonomy(frame: pd.DataFrame | None) -> dict[str, dict]:
    tax = {}
    for t in catalog.TAXONOMY:
        tax[t[0]] = dict(family=t[1], klass=t[2], name=t[3], use=t[4], phase=t[5], uom=t[6], spec=t[7], unspsc=t[8])
    if frame is not None:
        for _, r in frame.iterrows():
            tax[str(r.TAXONOMY_NODE_ID)] = dict(family=r.LEVEL1_FAMILY, klass=r.LEVEL2_CLASS, name=r.GENERIC_PRODUCT_NAME, use=r.PRIMARY_USE,
                                                phase=r.USE_PHASE, uom=r.STANDARD_UOM, spec=r.KEY_SPEC_ATTRIBUTES, unspsc=r.UNSPSC_CODE)
    return tax


def _items_for(lifnr: str) -> list[dict]:
    if lifnr in catalog.SUPPLIER_ITEMS:
        return catalog.SUPPLIER_ITEMS[lifnr]
    if lifnr in catalog.HAULERS:
        return catalog.HAULER_TEMPLATE
    return []


def _dominant_family(lifnr: str, codes: list[str] | None = None) -> str:
    counts: dict[str, int] = {}
    for it in _items_for(lifnr):
        if codes and it["code"] not in codes:
            continue
        fam = catalog.TAX_BY_ID[it["node"]][1]
        if fam != FEES_FAMILY:
            counts[fam] = counts.get(fam, 0) + 1
    if not counts:
        for it in _items_for(lifnr):
            counts[catalog.TAX_BY_ID[it["node"]][1]] = counts.get(catalog.TAX_BY_ID[it["node"]][1], 0) + 1
    return max(counts, key=counts.get) if counts else "Production & completion chemicals"


# --------------------------------------------------------------------------------------
# a. Supplier technical data sheets
# --------------------------------------------------------------------------------------
def _spec_sheet_groups(suppliers: dict[str, dict], classification: pd.DataFrame | None) -> list[dict]:
    """One group per (supplier, product family): file name from the classification frame when it cites a
    technical data sheet for the item, else catalog.spec_sheet_filename(supplier name, family code)."""
    cited: dict[tuple[str, str], str] = {}
    if classification is not None and "SOURCE_DOCUMENT" in classification.columns:
        for _, r in classification.dropna(subset=["SOURCE_DOCUMENT"]).iterrows():
            doc = str(r.SOURCE_DOCUMENT)
            if doc.endswith("_Technical_Data_Sheet.pdf"):
                cited[(str(r.LIFNR), str(r.SUPPLIER_ITEM_CODE))] = doc
    groups: dict[str, dict] = {}
    for lifnr, items in catalog.SUPPLIER_ITEMS.items():
        sup = suppliers[lifnr]
        for it in items:
            if catalog.TAX_BY_ID[it["node"]][1] == FEES_FAMILY:
                continue
            fam = family_code(it["code"])
            file = cited.get((lifnr, it["code"])) or catalog.spec_sheet_filename(sup["name"], fam)
            g = groups.setdefault(file, dict(file=file, lifnr=lifnr, supplier=sup, family=fam, items=[]))
            g["items"].append(it)
    return list(groups.values())


def _chemical_sheet(g: dict, tax: dict) -> str:
    sup, items = g["supplier"], g["items"]
    node = max((it["node"] for it in items), key=[it["node"] for it in items].count)
    t = tax[node]
    name = product_name([it["desc"] for it in items])
    out = [f"# {name} — Technical Data Sheet",
           f"Letterhead: {letterhead(sup['name'], sup['city'], sup['state'])}",
           f"Document: Technical Data Sheet {g['family']}",
           f"Revision: {revision_date(g['file'])}",
           "",
           "## Product description",
           f"{name} is a {t['name'].lower()} manufactured by {sup['name']} for {t['use'][0].lower() + t['use'][1:]}. "
           f"Chemistry and specification: {t['spec']}. The product is supplied under the {sup['name']} product code family {g['family']} in the packs listed below; all packs contain the same formulation and concentration.",
           "",
           "## Typical application and dosage",
           DOSAGE.get(node, f"Apply as directed by the {sup['name']} field technician for {t['use'][0].lower() + t['use'][1:]}; dosage is set by the well's fluid rate and confirmed by residual testing."),
           "",
           "## Physical properties",
           "| Property | Typical value |", "|---|---|"]
    out += [f"| {p} | {v} |" for p, v in PHYSICAL.get(node, _PHYSICAL_DEFAULT)]
    out += ["", "## Packaging",
            "| Pack | Net contents | Supplier item code | Invoice description |", "|---|---|---|---|"]
    for it in items:
        std = tax[it["node"]]["uom"]
        out.append(f"| {pack_label(it['uom'], it['pack_qty'])} | {_qty(it['pack_qty'])} {std} | {it['code']} | {it['desc']} |")
    out += ["", "## Handling and storage", HANDLING.get(node, _HANDLING_DEFAULT),
            "", "## Generic classification",
            f"**Pecos Ridge Supply Chain generic product: {node} — {t['name']}** (taxonomy v3.0, family {t['family']}, class {t['klass']}, standard UOM {t['uom']}). "
            f"Supplier item codes {', '.join(it['code'] for it in items)} map to this node; invoiced packs convert to {t['uom']} at the net contents above. UNSPSC {t['unspsc']}.",
            "", f"Revision {revision_date(g['file'])}. This data sheet supersedes all earlier revisions. Values are typical and not specifications unless stated in the Master Service Agreement."]
    return "\n".join(out)


def _proppant_sheet(g: dict, tax: dict) -> str:
    sup, items = g["supplier"], g["items"]
    node = items[0]["node"]
    t = tax[node]
    p = PROPPANT.get(node, PROPPANT["SCM-02-01-001"])
    name = product_name([it["desc"] for it in items])
    j = (_h(sup["name"] + node) % 7 - 3) / 10.0        # -0.3 .. +0.3 points moved between the two main sieves
    sieves = list(p["sieves"])
    sieves[2] = (sieves[2][0], round(sieves[2][1] + j, 1))
    sieves[3] = (sieves[3][0], round(sieves[3][1] - j, 1))
    fines_adj = (_h(node + sup["name"]) % 5 - 2) / 10.0
    delivered = any("deliver" in it["desc"].lower() for it in items)
    fob = any("fob" in it["desc"].lower() for it in items)
    out = [f"# {name} — Technical Data Sheet",
           f"Letterhead: {letterhead(sup['name'], sup['city'], sup['state'])}",
           f"Document: Technical Data Sheet {g['family']}",
           f"Revision: {revision_date(g['file'])}",
           "",
           "## Product description",
           f"{name} is a {t['name'].lower()} produced by {sup['name']} for {t['use'][0].lower() + t['use'][1:]}. "
           f"Specification: {t['spec']}. Tested to API RP 19C / ISO 13503-2 at the plant laboratory on every 5,000-ton lot; certificates of analysis are available by lot number.",
           "",
           "## Typical application",
           f"{t['use']}. Pumped at 0.25-2.0 lb per gallon in slickwater stages; {p['label']} is run {'as the primary proppant across the stage' if 'ton' in t['uom'].lower() and '100' in p['label'] else 'as the tail-in proppant'} at concentrations set by the completion design.",
           "",
           "## Sieve analysis (API RP 19C)",
           "| US sieve | Percent retained |", "|---|---|"]
    out += [f"| {s} | {v:.1f} |" for s, v in sieves]
    out += [f"| In-size (within {p['label'].split()[0]}) | {sum(v for s, v in sieves[1:4]):.1f} percent (specification minimum 90) |",
            "", "## Physical and mechanical properties",
            "| Property | Typical value |", "|---|---|",
            f"| Crush resistance (API 19C K-value) | {p['kvalue']} |"]
    out += [f"| Fines generated at {stress} | {fines + fines_adj:.1f} percent |" for stress, fines in p["crush"]]
    out += [f"| Sphericity (Krumbein) | {p['sph']:.1f} |", f"| Roundness (Krumbein) | {p['rnd']:.1f} |",
            f"| Turbidity | {p['turb']} NTU maximum |", f"| Bulk density | {p['bulk']:.1f} lb/ft3 |",
            f"| Specific gravity | {p['sg']:.2f} |", f"| Acid solubility (12:3 HCl:HF) | {p['acid']:.1f} percent |",
            "| Moisture at shipment | 0.1 percent maximum |",
            "", "## Delivery and units",
            "| Supplier item code | Invoice description | Invoiced UOM | Delivery basis |", "|---|---|---|---|"]
    for it in items:
        basis = ("Delivered to the frac pad (DDP); freight, last mile and transload included in the per-ton rate" if "deliver" in it["desc"].lower()
                 else "FOB mine or transload; last-mile trucking and transload handling invoiced on separate lines" if "fob" in it["desc"].lower()
                 else "Per short ton as invoiced")
        out.append(f"| {it['code']} | {it['desc']} | {it['uom']} | {basis} |")
    out += ["", "## Terms: FOB versus delivered",
            ("Delivered pricing: the per-ton rate includes trucking from the mine or transload to the pad and the pneumatic or box offload; demurrage applies after two hours on location. "
             if delivered else "") +
            ("FOB pricing: title transfers at the mine load-out; last-mile trucking and transload handling are separate per-ton lines on the same invoice and the delivered cost is the sum of the three. "
             if fob else "") +
            "Tonnage is measured at the certified mine scale; the scale ticket number is the field ticket reference in OpenInvoice.",
            "", "## Handling and storage",
            "Store in silos or boxes under cover; moisture above 0.5 percent causes bridging at the blender. Respirable crystalline silica hazard: follow OSHA 29 CFR 1926.1153 engineering controls and dust monitoring on the pad.",
            "", "## Generic classification",
            f"**Pecos Ridge Supply Chain generic product: {node} — {t['name']}** (taxonomy v3.0, family {t['family']}, class {t['klass']}, standard UOM {t['uom']}). "
            f"Supplier item codes {', '.join(it['code'] for it in items)} map to this node at 1 ton per invoiced ton. UNSPSC {t['unspsc']}.",
            "", f"Revision {revision_date(g['file'])}. Values are lot-typical results from the plant laboratory."]
    return "\n".join(out)


def _service_sheet(g: dict, tax: dict) -> str:
    sup, items = g["supplier"], g["items"]
    node = items[0]["node"]
    t = tax[node]
    name = product_name([it["desc"] for it in items])
    out = [f"# {name} — Service Data Sheet",
           f"Letterhead: {letterhead(sup['name'], sup['city'], sup['state'])}",
           f"Document: Service Data Sheet {g['family']}",
           f"Revision: {revision_date(g['file'])}",
           "",
           "## Service description",
           f"{name}: {t['use'][0].lower() + t['use'][1:]}. Specification: {t['spec']}. Provided by {sup['name']} as a separately invoiced service line alongside FOB proppant sales so the delivered cost per ton is transparent.",
           "",
           "## Equipment and basis",
           "| Item | Detail |", "|---|---|",
           "| Trucks | Pneumatic trailers (25 ton) and 24-ton containerised boxes, 110-150 mile radius of the mine |",
           "| Transload | Rail-to-truck transload silo storage with certified scale |",
           "| Rate basis | Per short ton handled; tonnage from the mine or transload scale ticket |",
           "| Standby | Demurrage after two hours on location at the standby rate on the invoice |",
           "", "## Service lines",
           "| Supplier item code | Invoice description | Invoiced UOM |", "|---|---|---|"]
    out += [f"| {it['code']} | {it['desc']} | {it['uom']} |" for it in items]
    out += ["", "## Generic classification",
            f"**Pecos Ridge Supply Chain generic product: {node} — {t['name']}** (taxonomy v3.0, family {t['family']}, class {t['klass']}, standard UOM {t['uom']}). "
            f"Supplier item codes {', '.join(it['code'] for it in items)} map to this node. UNSPSC {t['unspsc']}.",
            "", f"Revision {revision_date(g['file'])}."]
    return "\n".join(out)


def _spec_sheet_markdown(g: dict, tax: dict) -> str:
    node = g["items"][0]["node"]
    fam = catalog.TAX_BY_ID[node][1]
    if node == LOGISTICS_NODE:
        return _service_sheet(g, tax)
    if fam == "Proppant":
        return _proppant_sheet(g, tax)
    return _chemical_sheet(g, tax)


# --------------------------------------------------------------------------------------
# b. OCTG mill data sheets
# --------------------------------------------------------------------------------------
def _octg_markdown(node: str, tax: dict) -> str:
    t = tax[node]
    spec = OCTG_SPECS.get(node) or dict(kind="accessory", rows=[("Product", t["name"]), ("Specification", t["spec"])])
    tubular = spec["kind"] == "tubular"
    out = [f"# {'Mill Data Sheet' if tubular else 'Product Data Sheet'} — {t['name']}",
           f"Letterhead: {COMPANY} Supply Chain — OCTG reference sheet compiled from mill certificates and vendor catalog pages",
           f"Document: OCTG reference {node}",
           f"Revision: {revision_date(node)}",
           "",
           "## Product description",
           f"{t['name']}: {t['use'][0].lower() + t['use'][1:]}. Specification: {t['spec']}. "
           + ("Seamless or ERW per API 5CT; mill test certificates (MTC) are supplied per heat with chemical and mechanical results." if tubular
              else "Supplied by distributors and the long-tail OCTG vendors; the reference values below are what the steward used to match vendor descriptions to the generic product."),
           "",
           "## Specification",
           "| Property | Value |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in spec["rows"]]
    if tubular:
        out += ["", "## Mechanical properties (API 5CT)",
                "| Property | Value |", "|---|---|",
                "| Minimum yield strength | " + {"P-110": "110,000 psi", "L-80": "80,000 psi", "J-55": "55,000 psi"}.get(next(v for k, v in spec["rows"] if k == "Grade"), "n/a") + " |",
                "| Maximum yield strength | " + {"P-110": "140,000 psi", "L-80": "95,000 psi", "J-55": "80,000 psi"}.get(next(v for k, v in spec["rows"] if k == "Grade"), "n/a") + " |",
                "| Minimum tensile strength | " + {"P-110": "125,000 psi", "L-80": "95,000 psi", "J-55": "75,000 psi"}.get(next(v for k, v in spec["rows"] if k == "Grade"), "n/a") + " |",
                "| Hardness | " + {"P-110": "Not specified", "L-80": "23 HRC maximum", "J-55": "Not specified"}.get(next(v for k, v in spec["rows"] if k == "Grade"), "n/a") + " |",
                "| Coating | Mill varnish, thread protectors both ends |"]
    out += ["", "## Aliases seen on supplier invoices",
            "Every description below is the same generic product. Joints convert to feet at the nominal joint length for the range; per-foot lines convert 1:1.",
            "| Invoice description | Invoiced UOM | Conversion to standard UOM |", "|---|---|---|"]
    for desc, uom, conv in catalog.OCTG_DESCRIPTIONS[node]:
        if uom == "JT":
            conv_txt = f"{_qty(conv)} ft per joint (Range {'3' if conv >= 40 else '2'})"
        elif uom == "FT":
            conv_txt = "1 ft per ft"
        else:
            conv_txt = f"{_qty(conv)} {t['uom']} per {uom}"
        out.append(f"| {desc} | {uom} | {conv_txt} |")
    out += ["", "## Generic classification",
            f"**Pecos Ridge Supply Chain generic product: {node} — {t['name']}** (taxonomy v3.0, family {t['family']}, class {t['klass']}, standard UOM {t['uom']}). "
            f"Compare suppliers on price per {t['uom']} after conversion; never on price per invoiced unit. UNSPSC {t['unspsc']}.",
            "", f"Revision {revision_date(node)}. Compiled by Pecos Ridge Supply Chain for item classification; not a mill certificate."]
    return "\n".join(out)


# --------------------------------------------------------------------------------------
# c. MSA Exhibit B pricing schedules
# --------------------------------------------------------------------------------------
def _terms(lifnr: str, rows: pd.DataFrame) -> list[str]:
    family = _dominant_family(lifnr, list(rows.SUPPLIER_ITEM_CODE.astype(str)))
    descs = " ".join(rows.SUPPLIER_ITEM_DESCRIPTION.fillna("").astype(str)).lower()
    if family == "Proppant":
        if "fob" in descs:
            basis = "Proppant rates are FOB the mine load-out or transload. Last-mile trucking and transload handling are invoiced as the separate per-ton lines in this Exhibit; title transfers at the load-out scale."
        else:
            basis = "Proppant rates are delivered to the Pecos Ridge frac pad (DDP) and include trucking from the mine or transload and the pneumatic or box offload. Tonnage is measured at the certified mine scale."
    elif family == "Water logistics":
        basis = "Rates are per barrel hauled, transferred or disposed and per hour on location as stated; the minimum load charge applies to loads under 100 bbl."
    else:
        basis = "Chemical rates are delivered (DDP) to Pecos Ridge well sites and chemical storage in the Hugoton, Anadarko, Midland and Delaware basins. Bulk per-gallon rates assume transport deliveries; drum, pail and tote rates are per pack with net contents as stated on the technical data sheet."
    return [
        f"- {basis}",
        "- Fuel surcharge: a fuel surcharge may be invoiced as a separate line item only when the published diesel index exceeds the base index stated in Exhibit C; it is never embedded in a unit rate.",
        "- Invoicing: Supplier submits invoices through Enverus OpenInvoice. Every service, delivery or rental line references the approved OpenInvoice field ticket number; material lines under a purchase order reference the PO.",
        "- Price book enforcement: the rates in this Exhibit are loaded in OpenInvoice as the Supplier price book for the version period. A line invoiced at a unit price above the rate in force on the service date is disputed and short-paid to the contract rate until a corrected invoice is received.",
        "- Rates are in US dollars, exclusive of sales and use tax. Items not listed in this Exhibit require a written rate quotation approved by the Pecos Ridge category manager before service.",
    ]


def _exhibit_markdown(lifnr: str, version: str, rows: pd.DataFrame, sup: dict) -> str:
    rows = rows.sort_values(["SUPPLIER_ITEM_CODE", "EFFECTIVE_FROM"])
    contract = next((str(c) for c in rows.CLM_CONTRACT_ID.dropna().astype(str).unique()), "(contract id not loaded)")
    eff_from, eff_to = rows.EFFECTIVE_FROM.min(), rows.EFFECTIVE_TO.max()
    esc = rows.ESCALATION_PCT.dropna()
    esc = float(esc.iloc[0]) if len(esc) else 0.0
    loaded = rows.LOADED_DATE.dropna()
    family = _dominant_family(lifnr, list(rows.SUPPLIER_ITEM_CODE.astype(str)))
    manager = catalog.FAMILY_MANAGER.get(family, catalog.FAMILY_MANAGER["Production & completion chemicals"])
    signatory = SIGNATORIES.get(lifnr) or _SIGNATORY_POOL[_h(lifnr) % len(_SIGNATORY_POOL)]
    out = [f"# Exhibit B — Rate Schedule ({version})",
           f"Letterhead: {COMPANY}, {COMPANY_ADDRESS}",
           f"Agreement: Master Service Agreement {contract} between {COMPANY} and {sup['name']}",
           f"Version: {version}",
           f"Effective: {_date(eff_from)} through {_date(eff_to)}",
           "",
           "## 1. Scope",
           f"This Exhibit B (the \"Rate Schedule\") forms part of Master Service Agreement {contract} (the \"Agreement\") between {COMPANY} (\"Company\") and {sup['name']} (\"Supplier\"). "
           f"It states the rates Supplier may invoice for the products and services listed below for work performed between {_date(eff_from)} and {_date(eff_to)}. "
           "It replaces every earlier rate schedule for the same items from its effective date. Capitalised terms have the meaning given in the Agreement.",
           "",
           "## 2. Escalation",
           (f"Rates in this Exhibit escalate by {esc:g} percent on each anniversary of the effective date, applied to the rate then in force and rounded to the cent; the escalated rate is loaded as a new price book version before it is invoiced."
            if esc > 0 else "Rates in this Exhibit are firm for the version period; no escalation applies."),
           "",
           "## 3. Rate table",
           "| Supplier item code | Description | UOM | Contract rate (USD) | Effective from | Effective to |",
           "|---|---|---|---|---|---|"]
    for _, r in rows.iterrows():
        desc = r.SUPPLIER_ITEM_DESCRIPTION if isinstance(r.SUPPLIER_ITEM_DESCRIPTION, str) else ""
        out.append(f"| {r.SUPPLIER_ITEM_CODE} | {desc} | {r.UOM} | {_money(r.CONTRACT_RATE_USD)} | {_date(r.EFFECTIVE_FROM)} | {_date(r.EFFECTIVE_TO)} |")
    out += ["", f"{len(rows)} rate line(s). Price book item ids {rows.PRICEBOOK_ITEM_ID.min()} through {rows.PRICEBOOK_ITEM_ID.max()} in OpenInvoice.",
            "", "## 4. Standard terms"]
    out += _terms(lifnr, rows)
    if sup.get("terms"):
        out.append(f"- Payment terms: {sup['terms']} from receipt of a correct invoice in OpenInvoice, as stated in the Agreement.")
    out += ["", "## 5. Price book load",
            (f"Loaded in Enverus OpenInvoice as price book version {version} on {_date(loaded.iloc[0])}." if len(loaded)
             else f"Loaded in Enverus OpenInvoice as price book version {version}.")
            + " Invoice lines are matched to the rate in force on the service date.",
            "", "## Signatures",
            f"| For {COMPANY} | For {sup['name']} |", "|---|---|",
            f"| {manager}, Category Manager — {family} | {signatory[0]}, {signatory[1]} |",
            f"| Date: {_date(eff_from)} | Date: {_date(eff_from)} |"]
    return "\n".join(out)


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------
def render(spec, out_dir: Path, *, echo: bool = True) -> list[dict]:
    pricebook = _frame(spec, "OI_PRICEBOOK_ITEM", required=True)
    supplier_frame = _frame(spec, "OI_SUPPLIER", required=False)
    classification = _frame(spec, "SCM_ITEM_CLASSIFICATION", required=False)
    taxonomy_frame = _frame(spec, "SCM_PRODUCT_TAXONOMY", required=False)
    if echo and supplier_frame is None:
        print("  OI_SUPPLIER is not cached; supplier names and cities fall back to the S4 vendor master (title case)")
    suppliers = _suppliers(supplier_frame)
    tax = _taxonomy(taxonomy_frame)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / "_md"
    tmp.mkdir(exist_ok=True)
    results: list[dict] = []

    def emit(file: str, kind: str, md: str, **extra) -> None:
        try:
            md_path = tmp / (Path(file).stem + ".md")
            md_path.write_text(md)
            pdf = out_dir / file
            render_pdf(md_path, pdf, title=Path(file).stem)
            results.append({"file": file, "kind": kind, "ok": True, **extra})
            if echo:
                print(f"  {kind:<17} {file} ({pdf.stat().st_size:,} bytes)")
        except Exception as exc:  # noqa: BLE001
            results.append({"file": file, "kind": kind, "ok": False, "error": f"{type(exc).__name__}: {str(exc)[:300]}", **extra})
            if echo:
                print(f"  FAILED {kind} {file}: {results[-1]['error']}")

    # a. supplier technical data sheets
    for g in _spec_sheet_groups(suppliers, classification):
        emit(g["file"], "spec_sheet", _spec_sheet_markdown(g, tax), supplier=g["supplier"]["name"], family=g["family"])

    # b. OCTG mill data sheets
    for node in catalog.OCTG_DESCRIPTIONS:
        emit(catalog.octg_mill_sheet_filename(node), "octg_mill_sheet", _octg_markdown(node, tax), node=node)

    # c. MSA Exhibit B pricing schedules, one per supplier price book version, every number from the frame
    for (lifnr, version), rows in pricebook.groupby(["LIFNR", "PRICEBOOK_VERSION"], sort=True):
        lifnr, version = str(lifnr), str(version)
        sup = suppliers.get(lifnr) or dict(name=f"Supplier {lifnr}", city=None, state=None, terms=None)
        docs = rows.SOURCE_DOCUMENT.dropna().astype(str).unique()
        file = docs[0] if len(docs) else catalog.pricing_exhibit_filename(sup["name"], version)
        if len(docs) > 1 and echo:
            print(f"  WARNING {lifnr} {version} cites {len(docs)} SOURCE_DOCUMENT values; rendering {file}")
        emit(file, "pricing_exhibit", _exhibit_markdown(lifnr, version, rows, sup), supplier=sup["name"], version=version, rate_lines=int(len(rows)))

    # cross-check: every file the tables cite should now exist in the archive
    rendered = {r["file"] for r in results if r["ok"]}
    cited: set[str] = set(pricebook.SOURCE_DOCUMENT.dropna().astype(str))
    if classification is not None and "SOURCE_DOCUMENT" in classification.columns:
        cited |= set(classification.SOURCE_DOCUMENT.dropna().astype(str))
    missing = sorted(cited - rendered)
    if echo:
        kinds = {k: sum(1 for r in results if r["ok"] and r["kind"] == k) for k in ("spec_sheet", "octg_mill_sheet", "pricing_exhibit")}
        print(f"  rendered {sum(kinds.values())} supplier documents ({kinds['spec_sheet']} spec sheets, {kinds['octg_mill_sheet']} OCTG sheets, "
              f"{kinds['pricing_exhibit']} pricing exhibits) -> {out_dir}")
        if missing:
            print(f"  WARNING {len(missing)} SOURCE_DOCUMENT value(s) cited in the tables have no rendered PDF: {', '.join(missing[:6])}{' ...' if len(missing) > 6 else ''}")
    return results
