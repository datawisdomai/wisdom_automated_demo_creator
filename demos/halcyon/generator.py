"""
generator.py (Halcyon Specialty Distribution)
--------------------------------------------
Deterministic synthetic data builders for the Halcyon Specialty Distribution
WisdomAI POC. No Snowflake dependency. Every builder is seeded so the same
rows are produced on every run.

Demo "today" (AS_OF) = 2026-09-25. Data spans 2025-01-01 .. 2026-09-25.

Engineered control points (see ../00_DESIGN.md):
  1. Vanterra (GLP-1) allocation cut June 2026 squeezes Bayview / Cascade / Northgate
  2. DC-MEM GEL_PACK_STD cold chain excursion cluster from June 2026
  3. Oncaryl short-dated inventory build-up at DC-DAL
  4. Keldon Pharma chargeback dispute spike after 2026-04 price file
  5. Backorders > 14 days drive HIGH severity service cases
  6. AUTO_REPLENISH sites fill better and raise fewer STAT orders
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from demo_creator.rng import rng as _seeded_rng

SEED = 20260925
AS_OF = date(2026, 9, 25)
START = date(2025, 1, 1)

# Story dates
VANTERRA_CUT_MONTH = date(2026, 6, 1)      # first allocation cut effective
VANTERRA_CUT2_MONTH = date(2026, 8, 1)     # second, deeper cut
MEM_GELPACK_START = date(2026, 6, 1)       # Memphis packaging change
KELDON_PRICE_FILE_DATE = date(2026, 4, 15)  # Keldon price file 2026-04A
BAYVIEW_LEAKAGE_START = date(2026, 7, 27)  # Bayview shifts non-GLP-1 volume
ONCARYL_DEMAND_DROP_START = date(2026, 5, 1)

HERO_CUSTOMER = "CUST-0001"    # Bayview Regional Health
SQUEEZED_CUSTOMERS = ["CUST-0001", "CUST-0007", "CUST-0003"]  # Bayview, Cascade, Northgate

VANTERRA_NDC = "61234-0101-04"
ONCARYL_NDC = "58771-0410-01"
VELTRIX = "MFR-001"
KELDON = "MFR-002"
AMBERLINE = "MFR-005"


def rng(tag: str) -> np.random.Generator:
    """Independent generator per builder so adding rows to one table never
    reshuffles another (shared implementation in demo_creator.rng)."""
    return _seeded_rng(SEED, tag)


def _d(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


# ---------------------------------------------------------------------------
# CALENDAR
# ---------------------------------------------------------------------------
US_HOLIDAYS = {
    "2025-01-01": "New Year's Day", "2025-05-26": "Memorial Day", "2025-07-04": "Independence Day",
    "2025-09-01": "Labor Day", "2025-11-27": "Thanksgiving", "2025-12-25": "Christmas Day",
    "2026-01-01": "New Year's Day", "2026-05-25": "Memorial Day", "2026-07-03": "Independence Day (observed)",
    "2026-09-07": "Labor Day", "2026-11-26": "Thanksgiving", "2026-12-25": "Christmas Day",
}


def build_calendar() -> pd.DataFrame:
    days = pd.date_range("2025-01-01", "2026-12-31", freq="D")
    last_complete_monday = _monday(AS_OF) - timedelta(days=7)  # week of 2026-09-14 is last complete
    rows = []
    for ts in days:
        d = ts.date()
        ws = _monday(d)
        q = (d.month - 1) // 3 + 1
        hol = US_HOLIDAYS.get(d.isoformat())
        rows.append({
            "CALENDAR_DATE": d,
            "WEEK_START_DATE": ws,
            "MONTH_START_DATE": d.replace(day=1),
            "FISCAL_QUARTER": f"{d.year}-Q{q}",
            "DAY_OF_WEEK": d.strftime("%A"),
            "IS_WEEKEND": d.weekday() >= 5,
            "IS_US_HOLIDAY": hol is not None,
            "HOLIDAY_NAME": hol,
            "IS_COMPLETE_WEEK": ws <= last_complete_monday,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# DISTRIBUTION CENTERS
# ---------------------------------------------------------------------------
DCS = [
    ("DC-MEM", "Halcyon Memphis National Hub", "Memphis", "TN", "SOUTH", True, True, 14000, 35.0456, -89.9767),
    ("DC-DAL", "Halcyon Dallas", "Dallas", "TX", "CENTRAL", True, False, 9000, 32.8998, -97.0403),
    ("DC-ATL", "Halcyon Atlanta", "Atlanta", "GA", "SOUTHEAST", True, False, 9500, 33.6407, -84.4277),
    ("DC-CHI", "Halcyon Chicago", "Chicago", "IL", "MIDWEST", True, True, 10000, 41.9742, -87.9073),
    ("DC-PHX", "Halcyon Phoenix", "Phoenix", "AZ", "WEST", True, False, 7000, 33.4373, -112.0078),
    ("DC-EWR", "Halcyon Newark", "Newark", "NJ", "NORTHEAST", True, False, 8500, 40.6895, -74.1745),
]
REGION_TO_DC = {r[4]: r[0] for r in DCS}


def build_distribution_centers() -> pd.DataFrame:
    return pd.DataFrame(DCS, columns=[
        "DC_ID", "DC_NAME", "CITY", "STATE", "REGION", "COLD_CHAIN_CAPABLE", "ULTRA_COLD_CAPABLE",
        "DAILY_LINE_CAPACITY", "LATITUDE", "LONGITUDE"])


# ---------------------------------------------------------------------------
# MANUFACTURERS / GPOS
# ---------------------------------------------------------------------------
MANUFACTURERS = [
    ("MFR-001", "Veltrix Biopharma", "Denmark", "STRATEGIC", True, 45),
    ("MFR-002", "Keldon Pharma", "United States", "STRATEGIC", False, 30),
    ("MFR-003", "Aurelian Therapeutics", "Switzerland", "STRATEGIC", True, 45),
    ("MFR-004", "Corvane Biologics", "United States", "PREFERRED", False, 30),
    ("MFR-005", "Amberline Oncology", "United States", "STRATEGIC", False, 30),
    ("MFR-006", "Solvane Life Sciences", "Germany", "PREFERRED", True, 60),
    ("MFR-007", "Meridex Pharmaceuticals", "United States", "PREFERRED", False, 30),
    ("MFR-008", "Halvorsen Biotech", "Norway", "STANDARD", False, 45),
    ("MFR-009", "Tessaro Immunology", "United States", "PREFERRED", True, 30),
    ("MFR-010", "Brightwater Generics", "India", "STANDARD", False, 60),
    ("MFR-011", "Nordveil Rare Disease", "Sweden", "PREFERRED", True, 45),
    ("MFR-012", "Calder Vaccines", "United Kingdom", "PREFERRED", False, 30),
    ("MFR-013", "Pemberly Neuro", "United States", "STANDARD", False, 45),
    ("MFR-014", "Ostrava Hematology", "Czech Republic", "STANDARD", False, 60),
    ("MFR-015", "Lumenis Ophthalmics", "United States", "STANDARD", False, 30),
    ("MFR-016", "Quillon Infectious Disease", "United States", "STANDARD", False, 45),
    ("MFR-017", "Wexford Generics", "United States", "STANDARD", False, 60),
    ("MFR-018", "Arbor Peak Biologics", "Canada", "PREFERRED", False, 30),
    ("MFR-019", "Sarnia Metabolic", "United States", "PREFERRED", True, 45),
    ("MFR-020", "Elmhurst Specialty", "United States", "STANDARD", False, 30),
    ("MFR-021", "Ravenna Therapeutics", "Italy", "STANDARD", False, 45),
    ("MFR-022", "Kestwick Pharma", "Ireland", "STANDARD", False, 60),
]

GPOS = [
    ("GPO-01", "Meridian Health Purchasing Alliance", "NATIONAL"),
    ("GPO-02", "Summit Care Collective", "NATIONAL"),
    ("GPO-03", "Oncology Practice Network", "SPECIALTY"),
    ("GPO-04", "Great Lakes Health Consortium", "REGIONAL"),
    ("GPO-05", "Pacific Rim Provider Group", "REGIONAL"),
    ("GPO-06", "Southern States Hospital Alliance", "REGIONAL"),
    ("GPO-07", "Independent Pharmacy Cooperative", "SPECIALTY"),
    ("GPO-08", "Atlantic Academic Medical Consortium", "REGIONAL"),
]


def build_manufacturers() -> pd.DataFrame:
    return pd.DataFrame(MANUFACTURERS, columns=[
        "MANUFACTURER_ID", "MANUFACTURER_NAME", "HQ_COUNTRY", "SUPPLIER_TIER",
        "RUNS_ALLOCATION_PROGRAM", "CHARGEBACK_TERMS_DAYS"])


def build_gpos() -> pd.DataFrame:
    return pd.DataFrame(GPOS, columns=["GPO_ID", "GPO_NAME", "GPO_TYPE"])


# ---------------------------------------------------------------------------
# PRODUCTS
# ---------------------------------------------------------------------------
CLASS_SPECS = {
    # class: (manufacturers, forms, storage classes with weights, wac range, qty typical, count)
    "ONCOLOGY":           (["MFR-002", "MFR-005", "MFR-003", "MFR-021"], ["VIAL", "INFUSION_BAG", "TABLET"], [("REFRIGERATED_2_8C", .6), ("AMBIENT", .4)], (900, 6500), (2, 12), 34),
    "IMMUNOLOGY":         (["MFR-002", "MFR-009", "MFR-004", "MFR-018"], ["PREFILLED_PEN", "PREFILLED_SYRINGE", "VIAL"], [("REFRIGERATED_2_8C", .9), ("AMBIENT", .1)], (1200, 7800), (2, 10), 28),
    "GLP1_METABOLIC":     (["MFR-001", "MFR-019"], ["PREFILLED_PEN"], [("REFRIGERATED_2_8C", 1.0)], (650, 1400), (6, 40), 12),
    "RARE_DISEASE":       (["MFR-011", "MFR-006", "MFR-003"], ["VIAL", "KIT"], [("REFRIGERATED_2_8C", .5), ("FROZEN_MINUS20", .3), ("ULTRA_COLD_MINUS70", .2)], (4000, 38000), (1, 4), 16),
    "HEMATOLOGY":         (["MFR-014", "MFR-004", "MFR-008"], ["VIAL", "PREFILLED_SYRINGE"], [("REFRIGERATED_2_8C", .7), ("AMBIENT", .3)], (700, 5200), (2, 10), 18),
    "NEUROLOGY":          (["MFR-013", "MFR-007", "MFR-020"], ["TABLET", "PREFILLED_SYRINGE", "VIAL"], [("AMBIENT", .6), ("REFRIGERATED_2_8C", .4)], (300, 4200), (4, 24), 20),
    "INFECTIOUS_DISEASE": (["MFR-016", "MFR-010", "MFR-017", "MFR-022"], ["TABLET", "VIAL"], [("AMBIENT", .8), ("REFRIGERATED_2_8C", .2)], (40, 1800), (10, 80), 22),
    "VACCINES":           (["MFR-012", "MFR-006"], ["PREFILLED_SYRINGE", "VIAL"], [("REFRIGERATED_2_8C", .8), ("FROZEN_MINUS20", .2)], (25, 260), (20, 200), 16),
    "OPHTHALMOLOGY":      (["MFR-015", "MFR-018"], ["VIAL", "PREFILLED_SYRINGE"], [("REFRIGERATED_2_8C", .8), ("AMBIENT", .2)], (500, 2400), (2, 12), 14),
}
BRAND_STEMS = ["Vel", "Onc", "Imm", "Neur", "Hem", "Cal", "Sol", "Tess", "Nord", "Mer", "Ath", "Bri", "Cor", "Dax", "Elu", "Fen", "Gal", "Hal", "Ivo", "Jur",
               "Kel", "Lum", "Myr", "Nex", "Ora", "Pri", "Quo", "Rav", "Ser", "Tal", "Ula", "Vor", "Wen", "Xan", "Yel", "Zor", "Ard", "Bel", "Cyr", "Dor"]
BRAND_ENDS = ["tera", "aryl", "ivax", "umab", "enza", "oxin", "ivir", "adex", "olin", "ecta", "imra", "ovant", "ixen", "aleq", "ustra"]
GENERIC_ENDS = ["mab", "nib", "tide", "vir", "zumab", "ciclib", "lisib", "parin", "statin", "gliptin", "setron", "prazole", "olol", "sartan", "cept"]


def build_products() -> pd.DataFrame:
    r = rng("products")
    rows = []
    used = set()
    n = 0
    for cls, (mfrs, forms, storages, wac_rng, qty_rng, count) in CLASS_SPECS.items():
        for i in range(count):
            n += 1
            while True:
                name = BRAND_STEMS[r.integers(len(BRAND_STEMS))] + BRAND_ENDS[r.integers(len(BRAND_ENDS))]
                if name not in used and name not in ("Vanterra", "Oncaryl"):
                    used.add(name)
                    break
            generic = (name[:3].lower() + GENERIC_ENDS[r.integers(len(GENERIC_ENDS))])
            mfr = mfrs[r.integers(len(mfrs))]
            st = r.choice([s for s, _ in storages], p=[w for _, w in storages])
            wac = float(np.round(np.exp(r.uniform(np.log(wac_rng[0]), np.log(wac_rng[1]))), 2))
            brand = "GENERIC" if mfr in ("MFR-010", "MFR-017") or (cls == "INFECTIOUS_DISEASE" and r.random() < .5) else "BRAND"
            if brand == "GENERIC":
                wac = round(wac * 0.25, 2)
            labeler = 10000 + int(mfr[-3:]) * 137 % 89999
            ndc = f"{labeler:05d}-{(1000 + n * 7) % 10000:04d}-{r.integers(1, 5):02d}"
            rows.append({
                "NDC": ndc, "PRODUCT_NAME": name, "GENERIC_NAME": generic, "MANUFACTURER_ID": mfr,
                "THERAPEUTIC_CLASS": cls, "DOSAGE_FORM": forms[r.integers(len(forms))], "STORAGE_CLASS": st,
                "IS_SPECIALTY": cls not in ("INFECTIOUS_DISEASE", "VACCINES") or wac > 400,
                "IS_LIMITED_DISTRIBUTION": cls == "RARE_DISEASE" and r.random() < .6,
                "IS_ALLOCATED": False, "BRAND_GENERIC": brand, "WAC_UNIT_PRICE": wac,
                "UNIT_OF_SALE": "1 vial" if "VIAL" in forms[0] else ("carton of 4 pens" if forms[0] == "PREFILLED_PEN" else "1 unit"),
                "SHELF_LIFE_DAYS": int(r.choice([365, 540, 730, 1095])),
                "LAUNCH_DATE": _d("2019-01-01") + timedelta(days=int(r.integers(0, 2200))),
                "X_QTY_MIN": qty_rng[0], "X_QTY_MAX": qty_rng[1],
            })
    df = pd.DataFrame(rows)
    # Named story products override two generated rows.
    v = df.index[df.THERAPEUTIC_CLASS == "GLP1_METABOLIC"][0]
    df.loc[v, ["NDC", "PRODUCT_NAME", "GENERIC_NAME", "MANUFACTURER_ID", "DOSAGE_FORM", "STORAGE_CLASS", "IS_SPECIALTY",
               "IS_ALLOCATED", "BRAND_GENERIC", "WAC_UNIT_PRICE", "UNIT_OF_SALE", "SHELF_LIFE_DAYS", "LAUNCH_DATE", "X_QTY_MIN", "X_QTY_MAX"]] = \
        [VANTERRA_NDC, "Vanterra", "velmaglutide", VELTRIX, "PREFILLED_PEN", "REFRIGERATED_2_8C", True,
         True, "BRAND", 985.00, "carton of 4 pens", 730, _d("2023-03-01"), 8, 48]
    o = df.index[(df.THERAPEUTIC_CLASS == "ONCOLOGY") & (df.MANUFACTURER_ID == AMBERLINE)][0]
    df.loc[o, ["NDC", "PRODUCT_NAME", "GENERIC_NAME", "DOSAGE_FORM", "STORAGE_CLASS", "IS_SPECIALTY",
               "BRAND_GENERIC", "WAC_UNIT_PRICE", "UNIT_OF_SALE", "SHELF_LIFE_DAYS", "LAUNCH_DATE", "X_QTY_MIN", "X_QTY_MAX"]] = \
        [ONCARYL_NDC, "Oncaryl", "ambertuzumab", "VIAL", "REFRIGERATED_2_8C", True,
         "BRAND", 2850.00, "1 vial", 540, _d("2021-06-15"), 2, 10]
    # Other allocated products: a handful from allocation-program manufacturers
    alloc_mfrs = {m[0] for m in MANUFACTURERS if m[4]}
    cand = df.index[df.MANUFACTURER_ID.isin(alloc_mfrs) & (df.NDC != VANTERRA_NDC)]
    picks = rng("alloc_products").choice(cand, size=7, replace=False)
    df.loc[picks, "IS_ALLOCATED"] = True
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# CUSTOMERS / SITES
# ---------------------------------------------------------------------------
REGION_CITIES = {
    "SOUTH":     [("Memphis", "TN", 35.15, -90.05), ("Nashville", "TN", 36.16, -86.78), ("Little Rock", "AR", 34.75, -92.29), ("Jackson", "MS", 32.30, -90.18), ("Louisville", "KY", 38.25, -85.76), ("Birmingham", "AL", 33.52, -86.81)],
    "CENTRAL":   [("Dallas", "TX", 32.78, -96.80), ("Houston", "TX", 29.76, -95.37), ("Austin", "TX", 30.27, -97.74), ("San Antonio", "TX", 29.42, -98.49), ("Oklahoma City", "OK", 35.47, -97.52), ("New Orleans", "LA", 29.95, -90.07)],
    "SOUTHEAST": [("Atlanta", "GA", 33.75, -84.39), ("Charlotte", "NC", 35.23, -80.84), ("Tampa", "FL", 27.95, -82.46), ("Orlando", "FL", 28.54, -81.38), ("Jacksonville", "FL", 30.33, -81.66), ("Savannah", "GA", 32.08, -81.09), ("Raleigh", "NC", 35.78, -78.64)],
    "MIDWEST":   [("Chicago", "IL", 41.88, -87.63), ("Indianapolis", "IN", 39.77, -86.16), ("Columbus", "OH", 39.96, -83.00), ("Detroit", "MI", 42.33, -83.05), ("Milwaukee", "WI", 43.04, -87.91), ("Minneapolis", "MN", 44.98, -93.27), ("St. Louis", "MO", 38.63, -90.20)],
    "WEST":      [("Phoenix", "AZ", 33.45, -112.07), ("Denver", "CO", 39.74, -104.99), ("Las Vegas", "NV", 36.17, -115.14), ("Salt Lake City", "UT", 40.76, -111.89), ("Sacramento", "CA", 38.58, -121.49), ("Portland", "OR", 45.52, -122.68), ("Seattle", "WA", 47.61, -122.33), ("Los Angeles", "CA", 34.05, -118.24)],
    "NORTHEAST": [("Newark", "NJ", 40.74, -74.17), ("Philadelphia", "PA", 39.95, -75.17), ("Boston", "MA", 42.36, -71.06), ("Hartford", "CT", 41.76, -72.69), ("Baltimore", "MD", 39.29, -76.61), ("Pittsburgh", "PA", 40.44, -79.99), ("Albany", "NY", 42.65, -73.76)],
}
NAME_PREFIXES = ["Bayview", "Northgate", "Cascade", "Riverstone", "Summit Ridge", "Harborlight", "Prairie Rose", "Silver Lake", "Oakhaven", "Pinecrest", "Bluewater",
                 "Ironwood", "Cedar Point", "Stonebridge", "Willow Creek", "Redrock", "Clearwater", "Highland", "Lakeshore", "Meadowbrook", "Granite Falls",
                 "Sunridge", "Copper Canyon", "Fox Hollow", "Maple Grove", "Eastfield", "Westbrook", "Southgate", "Kingsport", "Ashford", "Brookline",
                 "Coral Bay", "Dunmore", "Elkhorn", "Fairhaven", "Glenmoor", "Hollowell", "Innsbrook", "Juniper", "Kingswood", "Larkspur", "Millbrook",
                 "Norwood", "Oceanside", "Parkview", "Quarry Hill", "Rosemont", "Sagebrush", "Timberline", "Upland", "Valley Forge", "Whitmore",
                 "Yardley", "Zephyr Cove", "Amberfield", "Beacon Hill", "Crestline", "Driftwood", "Evergreen", "Foxglove", "Goldcrest", "Heron Bay",
                 "Ivy Ridge", "Jasper", "Kestrel", "Lantern Hill", "Marlow", "Nightingale", "Orchard Park", "Pelican Point", "Quail Run", "Ridgefield",
                 "Saltmarsh", "Tidewater", "Union Square", "Vista Del Sol", "Wolf Creek", "Aspen Hollow", "Birchwood", "Cobalt", "Dawson", "Emberly",
                 "Falcon Ridge", "Greyhaven", "Hawthorne", "Ironbridge", "Kingfisher", "Lockwood", "Mariner", "Northwind", "Oakmont", "Prospect",
                 "Redwood", "Seabrook", "Thornfield", "Underhill", "Verdant", "Waverly", "Wildrose", "Yellowstone", "Alder", "Boulder Creek", "Canyon Rim",
                 "Deer Valley", "Edgewater", "Fernwood", "Goldenrod", "Harbor Point", "Indigo", "Kettle Falls", "Linden", "Mesa Verde", "Newport", "Overlook"]
TYPE_SUFFIX = {
    "HEALTH_SYSTEM": ["Regional Health", "Health Alliance", "Health System", "Medical Group", "Health Network"],
    "ACADEMIC_MEDICAL_CENTER": ["University Medical Center", "Academic Health", "University Hospitals"],
    "ONCOLOGY_PRACTICE": ["Oncology Partners", "Cancer Care", "Hematology Oncology Associates", "Oncology Group"],
    "INFUSION_CENTER": ["Infusion Services", "Infusion Centers", "Specialty Infusion"],
    "SPECIALTY_PHARMACY": ["Specialty Pharmacy", "Specialty Rx", "Health Pharmacy Services"],
    "RETAIL_PHARMACY_CHAIN": ["Pharmacy", "Drug Stores", "Family Pharmacy"],
}
ACCOUNT_MANAGERS = ["Dana Whitfield", "Marcus Oyelaran", "Priya Raman", "Tom Castellano", "Elena Vasquez", "Jordan Blake", "Renee Hollis", "Sam Okafor"]

# Type mix and scale (ACV in $M range, site count range)
CUSTOMER_TYPES = [
    ("HEALTH_SYSTEM", 30, (6, 60), (6, 14)),
    ("ACADEMIC_MEDICAL_CENTER", 10, (12, 55), (4, 8)),
    ("ONCOLOGY_PRACTICE", 28, (2, 18), (1, 4)),
    ("INFUSION_CENTER", 14, (1.5, 9), (1, 3)),
    ("SPECIALTY_PHARMACY", 18, (3, 22), (1, 3)),
    ("RETAIL_PHARMACY_CHAIN", 20, (4, 30), (8, 18)),
]
CLASS_MIX_BY_TYPE = {
    "HEALTH_SYSTEM":           {"ONCOLOGY": .22, "IMMUNOLOGY": .16, "GLP1_METABOLIC": .12, "RARE_DISEASE": .05, "HEMATOLOGY": .10, "NEUROLOGY": .08, "INFECTIOUS_DISEASE": .15, "VACCINES": .08, "OPHTHALMOLOGY": .04},
    "ACADEMIC_MEDICAL_CENTER": {"ONCOLOGY": .26, "IMMUNOLOGY": .14, "GLP1_METABOLIC": .06, "RARE_DISEASE": .14, "HEMATOLOGY": .12, "NEUROLOGY": .08, "INFECTIOUS_DISEASE": .10, "VACCINES": .05, "OPHTHALMOLOGY": .05},
    "ONCOLOGY_PRACTICE":       {"ONCOLOGY": .62, "IMMUNOLOGY": .06, "GLP1_METABOLIC": .0, "RARE_DISEASE": .03, "HEMATOLOGY": .22, "NEUROLOGY": .0, "INFECTIOUS_DISEASE": .05, "VACCINES": .02, "OPHTHALMOLOGY": .0},
    "INFUSION_CENTER":         {"ONCOLOGY": .30, "IMMUNOLOGY": .36, "GLP1_METABOLIC": .0, "RARE_DISEASE": .08, "HEMATOLOGY": .10, "NEUROLOGY": .12, "INFECTIOUS_DISEASE": .04, "VACCINES": .0, "OPHTHALMOLOGY": .0},
    "SPECIALTY_PHARMACY":      {"ONCOLOGY": .18, "IMMUNOLOGY": .26, "GLP1_METABOLIC": .18, "RARE_DISEASE": .10, "HEMATOLOGY": .08, "NEUROLOGY": .12, "INFECTIOUS_DISEASE": .06, "VACCINES": .0, "OPHTHALMOLOGY": .02},
    "RETAIL_PHARMACY_CHAIN":   {"ONCOLOGY": .02, "IMMUNOLOGY": .16, "GLP1_METABOLIC": .34, "RARE_DISEASE": .0, "HEMATOLOGY": .02, "NEUROLOGY": .10, "INFECTIOUS_DISEASE": .18, "VACCINES": .16, "OPHTHALMOLOGY": .02},
}


def build_customers() -> pd.DataFrame:
    r = rng("customers")
    rows = []
    prefixes = list(NAME_PREFIXES)
    r.shuffle(prefixes)
    extra = ["Blue Heron", "Cinder Ridge", "Dove Hollow", "Elm Street", "Fallbrook", "Glacier Bay", "Hidden Valley", "Iron Gate", "Kite Hill", "Loon Lake",
             "Moss Landing", "North Fork", "Otter Creek", "Pinewood", "Rockport", "Sandpiper", "Twin Oaks", "Vine Hill", "Whitecap", "Windmill"]
    prefixes += [p for p in extra if p not in prefixes]
    pi = 0
    regions = list(REGION_CITIES.keys())
    cid = 0
    for ctype, count, acv_rng, _ in CUSTOMER_TYPES:
        for _ in range(count):
            cid += 1
            region = regions[r.integers(len(regions))]
            city = REGION_CITIES[region][r.integers(len(REGION_CITIES[region]))]
            name = f"{prefixes[pi]} {TYPE_SUFFIX[ctype][r.integers(len(TYPE_SUFFIX[ctype]))]}"
            pi += 1
            acv = float(np.round(np.exp(r.uniform(np.log(acv_rng[0]), np.log(acv_rng[1]))) * 1_000_000, -3))
            onboard = _d("2014-01-01") + timedelta(days=int(r.integers(0, 3800)))
            cstart = _d("2023-01-01") + timedelta(days=int(r.integers(0, 900)))
            renewal = cstart + timedelta(days=int(r.choice([730, 1095])))
            while renewal < _d("2026-10-01"):
                renewal += timedelta(days=365)
            gpo = None if r.random() < .12 else ("GPO-03" if ctype == "ONCOLOGY_PRACTICE" and r.random() < .7 else
                                                 "GPO-07" if ctype in ("SPECIALTY_PHARMACY", "RETAIL_PHARMACY_CHAIN") and r.random() < .5 else
                                                 GPOS[r.integers(len(GPOS))][0])
            rows.append({
                "CUSTOMER_ID": f"CUST-{cid:04d}", "CUSTOMER_NAME": name, "CUSTOMER_TYPE": ctype, "CUSTOMER_TIER": "CORE",
                "GPO_ID": gpo, "REGION": region, "HQ_STATE": city[1], "HQ_CITY": city[0], "PRIMARY_DC_ID": REGION_TO_DC[region],
                "ACCOUNT_MANAGER": ACCOUNT_MANAGERS[r.integers(len(ACCOUNT_MANAGERS))], "ONBOARDED_DATE": onboard,
                "CONTRACT_START_DATE": cstart, "CONTRACT_RENEWAL_DATE": renewal, "ANNUAL_CONTRACT_VALUE": acv,
                "PAYMENT_TERMS_DAYS": int(r.choice([30, 45, 60])), "IS_ACTIVE": True,
            })
    df = pd.DataFrame(rows)

    # Named story customers
    def set_row(i, **kw):
        for k, v in kw.items():
            df.loc[i, k] = v
    set_row(0, CUSTOMER_ID="CUST-0001", CUSTOMER_NAME="Bayview Regional Health", CUSTOMER_TYPE="HEALTH_SYSTEM", REGION="SOUTHEAST", HQ_STATE="FL", HQ_CITY="Tampa",
            PRIMARY_DC_ID="DC-ATL", GPO_ID="GPO-01", ACCOUNT_MANAGER="Dana Whitfield", ONBOARDED_DATE=_d("2016-04-11"), CONTRACT_START_DATE=_d("2023-12-15"),
            CONTRACT_RENEWAL_DATE=_d("2026-12-15"), ANNUAL_CONTRACT_VALUE=48_200_000.0, PAYMENT_TERMS_DAYS=45)
    set_row(2, CUSTOMER_ID="CUST-0003", CUSTOMER_NAME="Northgate Health Alliance", CUSTOMER_TYPE="HEALTH_SYSTEM", REGION="MIDWEST", HQ_STATE="OH", HQ_CITY="Columbus",
            PRIMARY_DC_ID="DC-CHI", GPO_ID="GPO-04", ACCOUNT_MANAGER="Marcus Oyelaran", CONTRACT_START_DATE=_d("2024-11-30"),
            CONTRACT_RENEWAL_DATE=_d("2026-11-30"), ANNUAL_CONTRACT_VALUE=31_500_000.0)
    # Cascade Oncology Partners: an oncology practice that also runs a metabolic clinic (buys Vanterra)
    onc_first = df.index[df.CUSTOMER_TYPE == "ONCOLOGY_PRACTICE"][0]
    set_row(onc_first, CUSTOMER_ID="CUST-0007", CUSTOMER_NAME="Cascade Oncology Partners", REGION="WEST", HQ_STATE="OR", HQ_CITY="Portland",
            PRIMARY_DC_ID="DC-PHX", GPO_ID="GPO-03", ACCOUNT_MANAGER="Priya Raman", CONTRACT_START_DATE=_d("2025-01-20"),
            CONTRACT_RENEWAL_DATE=_d("2027-01-20"), ANNUAL_CONTRACT_VALUE=14_800_000.0)
    # move CUST-0007 id: swap with whichever row currently has CUST-0007
    dup = df.index[(df.CUSTOMER_ID == "CUST-0007") & (df.index != onc_first)]
    if len(dup):
        df.loc[dup[0], "CUSTOMER_ID"] = f"CUST-{onc_first + 1:04d}"
    # Houston oncology practices for the Oncaryl transfer story (served by DC-DAL)
    onc_idx = list(df.index[(df.CUSTOMER_TYPE == "ONCOLOGY_PRACTICE") & (df.index != onc_first)][:3])
    for i, nm in zip(onc_idx, ["Gulfstream Cancer Care", "Bayou City Oncology Group", "Lone Star Hematology Oncology Associates"]):
        set_row(i, CUSTOMER_NAME=nm, REGION="CENTRAL", HQ_STATE="TX", HQ_CITY="Houston", PRIMARY_DC_ID="DC-DAL", GPO_ID="GPO-03")

    # Ensure a healthy set of renewals inside the next 120 days (Oct 2026 .. late Jan 2027)
    window_targets = [_d("2026-10-18"), _d("2026-10-31"), _d("2026-11-15"), _d("2026-12-01"), _d("2026-12-31"), _d("2027-01-10"), _d("2027-01-22")]
    healthy = [i for i in df.index if df.loc[i, "CUSTOMER_ID"] not in SQUEEZED_CUSTOMERS][5:5 + len(window_targets)]
    for i, d in zip(healthy, window_targets):
        df.loc[i, "CONTRACT_RENEWAL_DATE"] = d
        df.loc[i, "CONTRACT_START_DATE"] = d - timedelta(days=1095)

    # Tiers by ACV rank
    df = df.sort_values("ANNUAL_CONTRACT_VALUE", ascending=False).reset_index(drop=True)
    df.loc[:11, "CUSTOMER_TIER"] = "STRATEGIC"
    df.loc[12:41, "CUSTOMER_TIER"] = "KEY"
    df.loc[df.CUSTOMER_ID.isin(["CUST-0001", "CUST-0003"]), "CUSTOMER_TIER"] = "STRATEGIC"
    df.loc[df.CUSTOMER_ID == "CUST-0007", "CUSTOMER_TIER"] = "KEY"
    df = df.sort_values("CUSTOMER_ID").reset_index(drop=True)
    return df


def build_customer_sites(customers: pd.DataFrame) -> pd.DataFrame:
    r = rng("sites")
    site_rng = {t[0]: t[3] for t in CUSTOMER_TYPES}
    site_types = {
        "HEALTH_SYSTEM": ["HOSPITAL_PHARMACY", "OUTPATIENT_INFUSION", "CLINIC"],
        "ACADEMIC_MEDICAL_CENTER": ["HOSPITAL_PHARMACY", "OUTPATIENT_INFUSION"],
        "ONCOLOGY_PRACTICE": ["CLINIC", "OUTPATIENT_INFUSION"],
        "INFUSION_CENTER": ["OUTPATIENT_INFUSION"],
        "SPECIALTY_PHARMACY": ["CENTRAL_FILL", "MAIL_ORDER"],
        "RETAIL_PHARMACY_CHAIN": ["RETAIL_STORE", "CENTRAL_FILL"],
    }
    rows = []
    n = 0
    for c in customers.itertuples(index=False):
        lo, hi = site_rng[c.CUSTOMER_TYPE]
        k = int(r.integers(lo, hi + 1))
        if c.CUSTOMER_ID == HERO_CUSTOMER:
            k = 11
        cities = REGION_CITIES[c.REGION]
        for j in range(k):
            n += 1
            city = cities[0] if j == 0 else cities[r.integers(len(cities))]
            if c.CUSTOMER_ID == HERO_CUSTOMER:
                city = [x for x in cities if x[1] == "FL"][j % 3]
            st = site_types[c.CUSTOMER_TYPE][0] if j == 0 else site_types[c.CUSTOMER_TYPE][r.integers(len(site_types[c.CUSTOMER_TYPE]))]
            label = {"HOSPITAL_PHARMACY": "Main Campus Pharmacy" if j == 0 else f"{city[0]} Hospital Pharmacy",
                     "OUTPATIENT_INFUSION": f"{city[0]} Infusion Center", "CLINIC": f"{city[0]} Clinic",
                     "RETAIL_STORE": f"Store {100 + n}", "CENTRAL_FILL": "Central Fill", "MAIL_ORDER": "Mail Order Facility"}[st]
            channel = r.choice(["EDI", "PORTAL", "PHONE", "AUTO_REPLENISH"], p=[.42, .30, .10, .18])
            if c.CUSTOMER_TYPE == "RETAIL_PHARMACY_CHAIN":
                channel = r.choice(["EDI", "AUTO_REPLENISH"], p=[.5, .5])
            rows.append({
                "SITE_ID": f"SITE-{n:05d}", "CUSTOMER_ID": c.CUSTOMER_ID, "SITE_NAME": f"{c.CUSTOMER_NAME} - {label}",
                "SITE_TYPE": st, "CITY": city[0], "STATE": city[1], "SERVING_DC_ID": c.PRIMARY_DC_ID,
                "COLD_CHAIN_RECEIVING": True if st != "RETAIL_STORE" else bool(r.random() < .85),
                "ORDERING_CHANNEL": channel,
                "LATITUDE": round(city[2] + r.normal(0, .08), 6), "LONGITUDE": round(city[3] + r.normal(0, .08), 6),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# CONTRACT PRICES
# ---------------------------------------------------------------------------
def build_contract_prices(products: pd.DataFrame) -> pd.DataFrame:
    r = rng("contracts")
    rows = []
    n = 0
    for g in GPOS:
        gid = g[0]
        for p in products.itertuples(index=False):
            # each GPO contracts ~65% of the catalog; oncology GPO covers oncology fully
            cover = .65 if not (gid == "GPO-03" and p.THERAPEUTIC_CLASS in ("ONCOLOGY", "HEMATOLOGY")) else .97
            if r.random() > cover:
                continue
            n += 1
            disc = r.uniform(.06, .22)
            eff = _d("2025-01-01")
            ver = "2025-01A"
            if p.MANUFACTURER_ID == KELDON:
                eff = KELDON_PRICE_FILE_DATE
                ver = "2026-04A"
            rows.append({
                "CONTRACT_PRICE_ID": f"CP-{n:06d}", "GPO_ID": gid, "NDC": p.NDC, "MANUFACTURER_ID": p.MANUFACTURER_ID,
                "CONTRACT_PRICE": round(p.WAC_UNIT_PRICE * (1 - disc), 2), "WAC_AT_CONTRACT": p.WAC_UNIT_PRICE,
                "EFFECTIVE_DATE": eff, "EXPIRATION_DATE": _d("2027-12-31"), "PRICE_FILE_VERSION": ver,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# ORDERS + ORDER LINES  (the core generator)
# ---------------------------------------------------------------------------
def build_orders_and_lines(customers, sites, products, contract_prices):
    r = rng("orders")
    prod_by_class = {c: products[products.THERAPEUTIC_CLASS == c].reset_index(drop=True) for c in CLASS_SPECS}
    cp_lookup = {(row.GPO_ID, row.NDC): row.CONTRACT_PRICE for row in contract_prices.itertuples(index=False)}
    cust = customers.set_index("CUSTOMER_ID")
    weeks = pd.date_range(START, AS_OF, freq="W-MON").date
    days_all = [START + timedelta(days=i) for i in range((AS_OF - START).days + 60)]
    holidays = {_d(k) for k in US_HOLIDAYS}
    biz_days = [d for d in days_all if d.weekday() < 5 and d not in holidays]
    biz_set = set(biz_days)

    def next_biz(d, n):
        while n > 0:
            d += timedelta(days=1)
            if d in biz_set:
                n -= 1
        return d

    # weekly order lines per customer scale with ACV: ~ $1.0M ACV -> 0.55 lines/week (approx 150K lines total)
    lines_per_week = (cust.ANNUAL_CONTRACT_VALUE / 1_000_000 * 0.95).clip(lower=0.8)
    sites_by_cust = {cid: g for cid, g in sites.groupby("CUSTOMER_ID")}

    order_rows, line_rows = [], []
    oid = 0
    lid = 0
    for cid, c in cust.iterrows():
        mix = dict(CLASS_MIX_BY_TYPE[c.CUSTOMER_TYPE])
        if cid in SQUEEZED_CUSTOMERS:
            mix["GLP1_METABOLIC"] = 0.30  # these customers run large GLP-1 programs
        classes = [k for k, v in mix.items() if v > 0]
        probs = np.array([mix[k] for k in classes]); probs = probs / probs.sum()
        csites = sites_by_cust[cid]
        site_weights = np.where(csites.SITE_TYPE.isin(["HOSPITAL_PHARMACY", "CENTRAL_FILL", "MAIL_ORDER"]), 3.0, 1.0)
        site_weights = site_weights / site_weights.sum()
        buys_vanterra = mix["GLP1_METABOLIC"] > 0 or cid in SQUEEZED_CUSTOMERS
        houston_onc = c.CUSTOMER_NAME in ("Gulfstream Cancer Care", "Bayou City Oncology Group", "Lone Star Hematology Oncology Associates")
        growth = 1.0 + (0.35 if cid in SQUEEZED_CUSTOMERS else r.uniform(-.05, .12))  # squeezed customers were growing

        for wk in weeks:
            # weekly line budget with growth over time and seasonality
            t = (wk - START).days / 365.0
            base = lines_per_week[cid] * (1 + (growth - 1) * t)
            if cid == HERO_CUSTOMER and wk >= BAYVIEW_LEAKAGE_START:
                base *= 1.0  # total kept; the non-GLP-1 reduction is applied per line below
            n_lines = r.poisson(base)
            if n_lines == 0:
                continue
            # group lines into orders of 2-6 lines
            remaining = n_lines
            while remaining > 0:
                k = int(min(remaining, r.integers(2, 7)))
                remaining -= k
                oid += 1
                site = csites.iloc[r.choice(len(csites), p=site_weights)]
                channel = site.ORDERING_CHANNEL
                # order day within the week
                od = wk + timedelta(days=int(r.integers(0, 5)))
                if od not in biz_set:
                    od = next_biz(od, 1)
                if od > AS_OF:
                    continue
                if channel == "AUTO_REPLENISH":
                    prio = "STANDARD" if r.random() < .985 else "URGENT"
                else:
                    prio = r.choice(["STANDARD", "URGENT", "STAT"], p=[.90, .07, .03])
                promised_ship = od  # Halcyon ships same business day for next-day delivery
                req_deliv = od if prio == "STAT" else next_biz(od, 1)
                lines_this = []
                for _ in range(k):
                    cls = classes[r.choice(len(classes), p=probs)]
                    # Bayview leakage: drop non-GLP-1 lines ~20% after July 13 2026
                    if cid == HERO_CUSTOMER and od >= BAYVIEW_LEAKAGE_START and cls != "GLP1_METABOLIC" and r.random() < .26:
                        continue
                    pool = prod_by_class[cls]
                    if cls == "GLP1_METABOLIC" and buys_vanterra and r.random() < (.85 if cid in SQUEEZED_CUSTOMERS else .45):
                        p = products[products.NDC == VANTERRA_NDC].iloc[0]
                    elif cid in SQUEEZED_CUSTOMERS and cls != "GLP1_METABOLIC" and r.random() < .06:
                        p = products[products.NDC == VANTERRA_NDC].iloc[0]  # metabolic clinics inside these customers
                    else:
                        p = pool.iloc[r.integers(len(pool))]
                    # Oncaryl demand at Dallas-served sites drops from May 2026 (except Houston oncology)
                    if p.NDC == ONCARYL_NDC and c.PRIMARY_DC_ID == "DC-DAL" and od >= ONCARYL_DEMAND_DROP_START and not houston_onc and r.random() < .55:
                        p = pool.iloc[r.integers(len(pool))]
                    # boost Oncaryl for Dallas sites before the drop and for Houston practices always
                    if cls == "ONCOLOGY" and c.PRIMARY_DC_ID == "DC-DAL" and (houston_onc or od < ONCARYL_DEMAND_DROP_START) and r.random() < .18:
                        p = products[products.NDC == ONCARYL_NDC].iloc[0]
                    qty = int(r.integers(int(p.X_QTY_MIN), int(p.X_QTY_MAX) + 1))
                    if p.NDC == VANTERRA_NDC:
                        qty = int(qty * (1 + 0.5 * t)) if cid in SQUEEZED_CUSTOMERS else qty
                    wac = float(p.WAC_UNIT_PRICE)
                    cprice = cp_lookup.get((c.GPO_ID, p.NDC)) if pd.notna(c.GPO_ID) else None
                    is_contract = cprice is not None
                    unit_price = cprice if is_contract else round(wac * 1.02, 2)

                    # --- fill logic ---
                    short_p = 0.025 if channel != "AUTO_REPLENISH" else 0.012
                    reason_pool = (["STOCKOUT", "MFR_SHORTAGE", "QUALITY_HOLD", "CREDIT_HOLD"], [.55, .25, .12, .08])
                    if p.IS_ALLOCATED:
                        short_p = 0.05
                        reason_pool = (["ALLOCATION_LIMIT", "MFR_SHORTAGE", "STOCKOUT"], [.6, .25, .15])
                    if p.NDC == VANTERRA_NDC and od >= VANTERRA_CUT_MONTH:
                        if od >= VANTERRA_CUT2_MONTH:
                            short_p = 0.56 if cid in SQUEEZED_CUSTOMERS else 0.28
                        else:
                            short_p = 0.22 if cid in SQUEEZED_CUSTOMERS else 0.10
                        reason_pool = (["ALLOCATION_LIMIT", "MFR_SHORTAGE"], [.92, .08])
                    if p.NDC == VANTERRA_NDC and od < VANTERRA_CUT_MONTH:
                        short_p = 0.03
                    shipped, bo, canc, reason = qty, 0, 0, None
                    if r.random() < short_p:
                        reason = reason_pool[0][r.choice(len(reason_pool[0]), p=reason_pool[1])]
                        if reason == "CREDIT_HOLD":
                            shipped, bo = 0, 0
                            canc = qty if r.random() < .5 else 0
                            bo = qty - canc
                        else:
                            frac = r.choice([0.0, 0.25, 0.5, 0.75], p=[.35, .2, .3, .15])
                            shipped = int(np.floor(qty * frac))
                            bo = qty - shipped
                            if r.random() < .12:
                                canc, bo = bo, 0
                    status = "FILLED" if shipped >= qty else ("CANCELLED" if shipped == 0 and canc == qty else ("BACKORDERED" if shipped == 0 else "PARTIAL"))
                    actual_ship = None
                    if shipped > 0:
                        late = r.random() < (0.06 if channel != "AUTO_REPLENISH" else 0.03)
                        actual_ship = promised_ship if not late else next_biz(promised_ship, int(r.integers(1, 4)))
                        if actual_ship > AS_OF:
                            actual_ship = AS_OF
                    lid += 1
                    lines_this.append({
                        "ORDER_LINE_ID": f"OL-{lid:09d}", "ORDER_ID": f"ORD-{oid:08d}", "CUSTOMER_ID": cid, "SITE_ID": site.SITE_ID,
                        "DC_ID": site.SERVING_DC_ID, "NDC": p.NDC, "ORDER_DATE": od, "QTY_ORDERED": qty, "QTY_SHIPPED": shipped,
                        "QTY_BACKORDERED": bo, "QTY_CANCELLED": canc, "UNIT_PRICE": unit_price, "WAC_AT_ORDER": wac,
                        "IS_CONTRACT_PRICED": is_contract, "LINE_STATUS": status, "SHORT_REASON_CODE": reason,
                        "PROMISED_SHIP_DATE": promised_ship, "ACTUAL_SHIP_DATE": actual_ship,
                        "X_STORAGE_CLASS": p.STORAGE_CLASS, "X_MFR": p.MANUFACTURER_ID, "X_CHANNEL": channel, "X_PRIO": prio,
                    })
                if not lines_this:
                    oid -= 1
                    continue
                statuses = {l["LINE_STATUS"] for l in lines_this}
                ostatus = "COMPLETE" if statuses == {"FILLED"} else ("CANCELLED" if statuses == {"CANCELLED"} else ("OPEN" if statuses <= {"BACKORDERED", "CANCELLED"} else "PARTIAL"))
                order_rows.append({
                    "ORDER_ID": f"ORD-{oid:08d}", "CUSTOMER_ID": cid, "SITE_ID": site.SITE_ID, "DC_ID": site.SERVING_DC_ID,
                    "ORDER_DATE": od, "ORDER_CHANNEL": channel, "ORDER_PRIORITY": prio, "REQUESTED_DELIVERY_DATE": req_deliv,
                    "ORDER_STATUS": ostatus, "LINE_COUNT": len(lines_this),
                    "ORDER_VALUE_WAC": round(sum(l["QTY_ORDERED"] * l["WAC_AT_ORDER"] for l in lines_this), 2),
                })
                line_rows.extend(lines_this)
    orders = pd.DataFrame(order_rows)
    lines = pd.DataFrame(line_rows)
    return orders, lines


# ---------------------------------------------------------------------------
# SHIPMENTS + COLD CHAIN EVENTS
# ---------------------------------------------------------------------------
STORAGE_RANGE = {"REFRIGERATED_2_8C": (2.0, 8.0), "FROZEN_MINUS20": (-25.0, -15.0), "ULTRA_COLD_MINUS70": (-90.0, -60.0), "AMBIENT": (15.0, 25.0)}


def build_shipments_and_cold_chain(orders, lines):
    r = rng("shipments")
    holidays = {_d(k) for k in US_HOLIDAYS}
    val = (lines.QTY_SHIPPED * lines.WAC_AT_ORDER).groupby(lines.ORDER_ID).sum()
    rank = {"AMBIENT": 0, "REFRIGERATED_2_8C": 1, "FROZEN_MINUS20": 2, "ULTRA_COLD_MINUS70": 3}
    inv_rank = {v: k for k, v in rank.items()}
    cold = lines["X_STORAGE_CLASS"].map(rank).groupby(lines.ORDER_ID).max().map(inv_rank)
    first_ship = lines.dropna(subset=["ACTUAL_SHIP_DATE"]).groupby("ORDER_ID")["ACTUAL_SHIP_DATE"].min()
    ship_rows, cce_rows = [], []
    sid = 0
    eid = 0
    units_by_order = lines.groupby("ORDER_ID")["QTY_SHIPPED"].sum()
    for o in orders.itertuples(index=False):
        units = int(units_by_order.get(o.ORDER_ID, 0))
        if units <= 0:
            continue
        sid += 1
        coldest = cold[o.ORDER_ID]
        cc_req = coldest != "AMBIENT"
        ship_date = first_ship[o.ORDER_ID]
        if o.ORDER_PRIORITY == "STAT":
            carrier, svc = "COURIER", "STAT_COURIER"
        elif o.ORDER_PRIORITY == "URGENT":
            carrier, svc = ("HALCYON_FLEET", "SAME_DAY") if r.random() < .6 else ("FEDEX", "NEXT_DAY")
        else:
            carrier, svc = (["HALCYON_FLEET", "UPS", "FEDEX"][r.choice(3, p=[.55, .25, .20])], "NEXT_DAY")
        transit = 0 if svc in ("STAT_COURIER", "SAME_DAY") else 1
        promised = ship_date + timedelta(days=transit)
        while promised.weekday() >= 5 or promised in holidays:
            promised += timedelta(days=1)
        # packaging
        if coldest == "AMBIENT":
            pkg = "AMBIENT_BOX"
        elif coldest == "REFRIGERATED_2_8C":
            pkg = "PHASE_CHANGE_48H"
            if o.DC_ID == "DC-MEM" and ship_date >= MEM_GELPACK_START and r.random() < .60:
                pkg = "GEL_PACK_STD"
            elif o.DC_ID != "DC-MEM" and r.random() < .04:
                pkg = "GEL_PACK_STD"
        elif coldest == "FROZEN_MINUS20":
            pkg = "DRY_ICE"
        else:
            pkg = "LN2_DEWAR"
        # delivery
        late_p = 0.05 if carrier != "COURIER" else 0.02
        if o.DC_ID == "DC-PHX" and ship_date.month in (7, 8):
            late_p += 0.03
        delivered = promised
        status = "DELIVERED"
        if r.random() < late_p:
            delivered = promised + timedelta(days=int(r.integers(1, 4)))
            status = "DELIVERED" if r.random() < .9 else "EXCEPTION"
        if delivered > AS_OF:
            delivered, status = None, ("IN_TRANSIT" if promised >= AS_OF else "DELAYED")
        value = round(float(val[o.ORDER_ID]), 2)
        ship_rows.append({
            "SHIPMENT_ID": f"SHP-{sid:08d}", "ORDER_ID": o.ORDER_ID, "CUSTOMER_ID": o.CUSTOMER_ID, "SITE_ID": o.SITE_ID, "DC_ID": o.DC_ID,
            "CARRIER": carrier, "SERVICE_LEVEL": svc, "SHIP_DATE": ship_date, "PROMISED_DELIVERY_DATE": promised,
            "ACTUAL_DELIVERY_DATE": delivered, "DELIVERY_STATUS": status, "COLD_CHAIN_REQUIRED": cc_req, "PACKAGING_TYPE": pkg,
            "TOTAL_UNITS": units, "SHIPMENT_VALUE_WAC": value,
        })
        # cold chain readings
        if cc_req:
            lo, hi = STORAGE_RANGE[coldest]
            stages = ["DC_STORAGE", "PACKOUT", "IN_TRANSIT", "DELIVERY"]
            n_read = int(r.integers(2, 5))
            for st in r.choice(stages, size=n_read, replace=False):
                eid += 1
                base_p = 0.006
                sev_p = [.7, .25, .05]
                if st == "PACKOUT" and pkg == "GEL_PACK_STD":
                    base_p = 0.02
                    if o.DC_ID == "DC-MEM" and ship_date >= MEM_GELPACK_START:
                        base_p = 0.21 if ship_date.month in (7, 8) else 0.12
                        sev_p = [.30, .45, .25]
                if st == "IN_TRANSIT" and ship_date.month in (7, 8):
                    base_p *= 1.3
                exc = r.random() < base_p
                ts = datetime.combine(ship_date, datetime.min.time()) + timedelta(hours=int(r.integers(5, 22)), minutes=int(r.integers(0, 60)))
                if st == "DELIVERY":
                    ts += timedelta(days=transit)
                if not exc:
                    temp = round(float(r.uniform(lo + .3, hi - .3)), 1)
                    cce_rows.append({"EVENT_ID": f"CCE-{eid:08d}", "SHIPMENT_ID": f"SHP-{sid:08d}", "DC_ID": o.DC_ID, "CUSTOMER_ID": o.CUSTOMER_ID,
                                     "EVENT_TIMESTAMP": ts, "EVENT_DATE": ts.date(), "STAGE": st, "STORAGE_CLASS": coldest, "PACKAGING_TYPE": pkg,
                                     "TEMP_READING_C": temp, "IS_EXCURSION": False, "EXCURSION_MINUTES": None, "EXCURSION_SEVERITY": None,
                                     "DISPOSITION": None, "UNITS_AFFECTED": None, "VALUE_AFFECTED_WAC": None})
                    continue
                sev = ["MINOR", "MAJOR", "CRITICAL"][r.choice(3, p=sev_p)]
                minutes = int({"MINOR": r.integers(5, 30), "MAJOR": r.integers(30, 121), "CRITICAL": r.integers(121, 600)}[sev])
                temp = round(float(hi + {"MINOR": r.uniform(.5, 3), "MAJOR": r.uniform(2, 8), "CRITICAL": r.uniform(6, 18)}[sev]), 1)
                disp = {"MINOR": ["RELEASED", "QUARANTINED"], "MAJOR": ["QUARANTINED", "RETURNED", "RELEASED"], "CRITICAL": ["DESTROYED", "QUARANTINED", "RETURNED"]}[sev]
                dp = {"MINOR": [.85, .15], "MAJOR": [.45, .40, .15], "CRITICAL": [.50, .25, .25]}[sev]
                disposition = disp[r.choice(len(disp), p=dp)]
                frac = {"MINOR": .15, "MAJOR": .55, "CRITICAL": .9}[sev]
                ua = max(1, int(units * frac))
                cce_rows.append({"EVENT_ID": f"CCE-{eid:08d}", "SHIPMENT_ID": f"SHP-{sid:08d}", "DC_ID": o.DC_ID, "CUSTOMER_ID": o.CUSTOMER_ID,
                                 "EVENT_TIMESTAMP": ts, "EVENT_DATE": ts.date(), "STAGE": st, "STORAGE_CLASS": coldest, "PACKAGING_TYPE": pkg,
                                 "TEMP_READING_C": temp, "IS_EXCURSION": True, "EXCURSION_MINUTES": minutes, "EXCURSION_SEVERITY": sev,
                                 "DISPOSITION": disposition, "UNITS_AFFECTED": ua, "VALUE_AFFECTED_WAC": round(value * frac, 2)})
    return pd.DataFrame(ship_rows), pd.DataFrame(cce_rows)


# ---------------------------------------------------------------------------
# BACKORDERS
# ---------------------------------------------------------------------------
def build_backorders(lines):
    r = rng("backorders")
    src = lines[lines.QTY_BACKORDERED > 0]
    rows = []
    for i, l in enumerate(src.itertuples(index=False), start=1):
        reason = l.SHORT_REASON_CODE if l.SHORT_REASON_CODE in ("ALLOCATION_LIMIT", "STOCKOUT", "MFR_SHORTAGE", "QUALITY_HOLD") else "STOCKOUT"
        if reason == "ALLOCATION_LIMIT":
            if l.ORDER_DATE >= VANTERRA_CUT2_MONTH and l.CUSTOMER_ID in SQUEEZED_CUSTOMERS:
                dur = int(r.integers(21, 70))
            elif l.ORDER_DATE >= VANTERRA_CUT_MONTH and l.CUSTOMER_ID in SQUEEZED_CUSTOMERS:
                dur = int(r.integers(12, 40))
            else:
                dur = int(r.integers(5, 22))
        elif reason == "MFR_SHORTAGE":
            dur = int(r.integers(7, 30))
        elif reason == "QUALITY_HOLD":
            dur = int(r.integers(3, 12))
        else:
            dur = int(r.integers(2, 10))
        expected = l.ORDER_DATE + timedelta(days=max(2, dur - int(r.integers(0, 4))))
        released = l.ORDER_DATE + timedelta(days=dur)
        cancelled = r.random() < .06
        if released > AS_OF:
            status, released_date, days_open = "OPEN", None, (AS_OF - l.ORDER_DATE).days
        elif cancelled:
            status, released_date, days_open = "CANCELLED", None, dur
        else:
            status, released_date, days_open = "RELEASED", released, dur
        rows.append({"BACKORDER_ID": f"BO-{i:08d}", "ORDER_LINE_ID": l.ORDER_LINE_ID, "CUSTOMER_ID": l.CUSTOMER_ID, "SITE_ID": l.SITE_ID,
                     "DC_ID": l.DC_ID, "NDC": l.NDC, "BACKORDER_DATE": l.ORDER_DATE, "QTY_BACKORDERED": int(l.QTY_BACKORDERED),
                     "REASON_CODE": reason, "EXPECTED_RELEASE_DATE": expected, "RELEASED_DATE": released_date, "STATUS": status,
                     "DAYS_OPEN": days_open, "BACKORDER_VALUE_WAC": round(l.QTY_BACKORDERED * l.WAC_AT_ORDER, 2)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# INVENTORY SNAPSHOTS
# ---------------------------------------------------------------------------
def build_inventory_snapshots(lines, products, dcs):
    r = rng("inventory")
    snaps = pd.date_range("2025-01-06", "2026-09-21", freq="W-MON").date
    lines = lines.copy()
    lines["WEEK"] = pd.to_datetime(lines.ORDER_DATE).dt.to_period("W-SUN").dt.start_time.dt.date
    demand = lines.groupby(["DC_ID", "NDC", "WEEK"])["QTY_ORDERED"].sum()
    dem_by_dc_ndc = {k: v for k, v in demand.groupby(level=[0, 1])}
    prod = products.set_index("NDC")
    rows = []
    n = 0
    for dc in dcs.DC_ID:
        for ndc in products.NDC:
            key = (dc, ndc)
            if key not in dem_by_dc_ndc and r.random() < .7:
                continue  # DC does not stock this SKU
            series = dem_by_dc_ndc.get(key)
            wk_dem = series.droplevel([0, 1]) if series is not None else pd.Series(dtype=float)
            wac = float(prod.loc[ndc, "WAC_UNIT_PRICE"])
            shelf = int(prod.loc[ndc, "SHELF_LIFE_DAYS"])
            for sd in snaps:
                n += 1
                window = [sd - timedelta(days=7 * k) for k in range(1, 9)]
                avg_dem = float(np.mean([wk_dem.get(w, 0) for w in window])) if len(wk_dem) else 0.0
                target_weeks = r.uniform(3.5, 6.5)
                on_hand = max(0, int(avg_dem * target_weeks + r.normal(0, max(1, avg_dem * .4))))
                allocated = int(min(on_hand, max(0, r.normal(avg_dem * .6, max(1, avg_dem * .2)))))
                on_order = int(max(0, avg_dem * r.uniform(1, 3))) if on_hand < avg_dem * 5 else int(max(0, avg_dem * r.uniform(0, 1)))
                exp90 = int(on_hand * r.uniform(0.0, 0.08))
                exp30 = int(exp90 * r.uniform(0.1, 0.5))
                # Vanterra: allocation-constrained, thin stock after June 2026
                if ndc == VANTERRA_NDC and sd >= VANTERRA_CUT_MONTH:
                    on_hand = int(on_hand * .45)
                    allocated = min(on_hand, int(avg_dem * .9))
                    on_order = int(avg_dem * .7)
                # Oncaryl at Dallas: stock keeps arriving while demand falls; short-dated pile-up
                if ndc == ONCARYL_NDC and dc == "DC-DAL" and sd >= ONCARYL_DEMAND_DROP_START:
                    months_in = (sd - ONCARYL_DEMAND_DROP_START).days / 30.0
                    on_hand = int(420 + 95 * months_in + r.normal(0, 12))
                    allocated = int(min(on_hand, avg_dem * .7))
                    on_order = int(max(120, 300 - 20 * months_in))
                    exp90 = int(min(on_hand, 120 + 150 * months_in))
                    exp30 = int(exp90 * (0.15 + 0.06 * months_in))
                available = max(0, on_hand - allocated)
                dos = round(available / (avg_dem / 7.0), 1) if avg_dem > 0 else None
                rows.append({"SNAPSHOT_ID": f"INV-{n:08d}", "SNAPSHOT_DATE": sd, "DC_ID": dc, "NDC": ndc, "ON_HAND_UNITS": on_hand,
                             "ALLOCATED_UNITS": allocated, "AVAILABLE_UNITS": available, "ON_ORDER_UNITS": on_order,
                             "AVG_WEEKLY_DEMAND_UNITS": round(avg_dem, 1), "DAYS_OF_SUPPLY": dos, "EXPIRING_30D_UNITS": exp30,
                             "EXPIRING_90D_UNITS": exp90, "INVENTORY_VALUE_WAC": round(on_hand * wac, 2),
                             "EXPIRING_90D_VALUE_WAC": round(exp90 * wac, 2), "REORDER_POINT_UNITS": int(avg_dem * 2.5)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# CUSTOMER ALLOCATIONS
# ---------------------------------------------------------------------------
def build_customer_allocations(lines, products):
    r = rng("allocations")
    alloc_ndcs = products[products.IS_ALLOCATED].set_index("NDC")
    l = lines[lines.NDC.isin(alloc_ndcs.index)].copy()
    l["MONTH"] = pd.to_datetime(l.ORDER_DATE).dt.to_period("M").dt.start_time.dt.date
    g = l.groupby(["NDC", "MONTH", "CUSTOMER_ID"]).agg(req=("QTY_ORDERED", "sum"), cons=("QTY_SHIPPED", "sum")).reset_index()
    tot = g.groupby(["NDC", "MONTH"]).agg(req=("req", "sum"), cons=("cons", "sum")).reset_index()
    # Vanterra donors: 8 non-squeezed customers with modest, steady demand that keep a legacy historical-share
    # allocation well above what they use. They are the reallocation pool in the Scenario Lab.
    vcust = g[(g.NDC == VANTERRA_NDC) & (g.MONTH >= VANTERRA_CUT_MONTH)].groupby("CUSTOMER_ID")["req"].mean()
    vcust = vcust[~vcust.index.isin(SQUEEZED_CUSTOMERS)].sort_values()
    mid = vcust.iloc[len(vcust) // 3: len(vcust) // 3 + 8]
    donors = set(mid.index)
    rows = []
    n = 0
    for t in tot.itertuples(index=False):
        sub = g[(g.NDC == t.NDC) & (g.MONTH == t.MONTH)]
        allocs = []
        for row in sub.itertuples(index=False):
            short = row.cons < row.req
            if t.NDC == VANTERRA_NDC and row.CUSTOMER_ID in donors:
                # Historical-share donors: demand has fallen but their allocation has not. 40-55% utilization.
                allocated = int(max(row.cons, row.req) / r.uniform(0.40, 0.55))
                basis = "HISTORICAL_SHARE"
            elif t.NDC == VANTERRA_NDC and t.MONTH >= VANTERRA_CUT_MONTH:
                allocated = int(row.cons) if short else int(row.req * r.uniform(1.0, 1.04))
                basis = "HISTORICAL_SHARE"
            else:
                allocated = int(row.cons) if short else int(row.req * r.uniform(1.03, 1.15))
                basis = "HISTORICAL_SHARE" if r.random() < .8 else "CONTRACT_MINIMUM"
            allocs.append((row, max(allocated, 1), basis))
        halcyon_total = int(sum(a for _, a, _ in allocs) * (1.005 if (t.NDC == VANTERRA_NDC and t.MONTH >= VANTERRA_CUT_MONTH) else r.uniform(1.02, 1.10)))
        for row, allocated, basis in allocs:
            n += 1
            rows.append({"ALLOCATION_ID": f"ALC-{n:07d}", "PERIOD_MONTH": t.MONTH, "NDC": t.NDC, "MANUFACTURER_ID": alloc_ndcs.loc[t.NDC, "MANUFACTURER_ID"],
                         "CUSTOMER_ID": row.CUSTOMER_ID, "HALCYON_TOTAL_ALLOCATION_UNITS": halcyon_total, "ALLOCATION_BASIS": basis,
                         "CUSTOMER_ALLOCATED_UNITS": allocated, "CUSTOMER_REQUESTED_UNITS": int(row.req), "CUSTOMER_CONSUMED_UNITS": int(row.cons),
                         "UTILIZATION_PCT": round(100.0 * row.cons / allocated, 2), "SHORTFALL_UNITS": int(max(row.req - allocated, 0))})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# RETURNS
# ---------------------------------------------------------------------------
def build_returns(lines, shipments, cce):
    r = rng("returns")
    shipped = lines[lines.QTY_SHIPPED > 0]
    pick = shipped.sample(frac=0.02, random_state=SEED)
    rows = []
    n = 0
    for l in pick.itertuples(index=False):
        n += 1
        reason = ["DAMAGED", "SHORT_DATED", "WRONG_ITEM", "OVERSTOCK", "RECALL"][r.choice(5, p=[.32, .22, .18, .24, .04])]
        qty = max(1, int(l.QTY_SHIPPED * r.uniform(.2, 1.0)))
        disp = {"DAMAGED": "DESTROY", "SHORT_DATED": "RETURN_TO_MFR", "WRONG_ITEM": "RESTOCK", "OVERSTOCK": "RESTOCK", "RECALL": "RETURN_TO_MFR"}[reason]
        rows.append({"RETURN_ID": f"RET-{n:08d}", "ORDER_LINE_ID": l.ORDER_LINE_ID, "CUSTOMER_ID": l.CUSTOMER_ID, "DC_ID": l.DC_ID, "NDC": l.NDC,
                     "RETURN_DATE": min(AS_OF, l.ORDER_DATE + timedelta(days=int(r.integers(3, 30)))), "QTY_RETURNED": qty, "RETURN_REASON": reason,
                     "DISPOSITION": disp, "CREDIT_AMOUNT": round(qty * l.UNIT_PRICE, 2), "IS_SALEABLE": disp == "RESTOCK"})
    # temperature excursion returns tied to RETURNED dispositions
    ret_events = cce[(cce.IS_EXCURSION) & (cce.DISPOSITION == "RETURNED")]
    ship_to_order = shipments.set_index("SHIPMENT_ID")["ORDER_ID"]
    cold_lines = lines[lines.X_STORAGE_CLASS != "AMBIENT"].groupby("ORDER_ID").first()
    for e in ret_events.itertuples(index=False):
        oid = ship_to_order[e.SHIPMENT_ID]
        if oid not in cold_lines.index:
            continue
        l = cold_lines.loc[oid]
        n += 1
        qty = max(1, min(int(l.QTY_SHIPPED), int(e.UNITS_AFFECTED)))
        rows.append({"RETURN_ID": f"RET-{n:08d}", "ORDER_LINE_ID": l.ORDER_LINE_ID, "CUSTOMER_ID": e.CUSTOMER_ID, "DC_ID": e.DC_ID, "NDC": l.NDC,
                     "RETURN_DATE": min(AS_OF, e.EVENT_DATE + timedelta(days=int(r.integers(1, 6)))), "QTY_RETURNED": qty, "RETURN_REASON": "TEMP_EXCURSION",
                     "DISPOSITION": "DESTROY", "CREDIT_AMOUNT": round(qty * l.UNIT_PRICE, 2), "IS_SALEABLE": False})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# CHARGEBACKS
# ---------------------------------------------------------------------------
def build_chargebacks(lines, customers, manufacturers):
    r = rng("chargebacks")
    gpo = customers.set_index("CUSTOMER_ID")["GPO_ID"]
    terms = manufacturers.set_index("MANUFACTURER_ID")["CHARGEBACK_TERMS_DAYS"]
    src = lines[(lines.IS_CONTRACT_PRICED) & (lines.QTY_SHIPPED > 0)]
    rows = []
    for i, l in enumerate(src.itertuples(index=False), start=1):
        submitted = l.ORDER_DATE + timedelta(days=int(r.integers(1, 6)))
        keldon_new = (l.X_MFR == KELDON) and (l.ORDER_DATE >= KELDON_PRICE_FILE_DATE)
        dispute_p = 0.22 if keldon_new else 0.04
        wac_amt = round(l.QTY_SHIPPED * l.WAC_AT_ORDER, 2)
        con_amt = round(l.QTY_SHIPPED * l.UNIT_PRICE, 2)
        cb_amt = round(wac_amt - con_amt, 2)
        t = int(terms[l.X_MFR])
        reason = None
        if r.random() < dispute_p:
            if keldon_new:
                reason = ["PRICE_MISMATCH", "INELIGIBLE_CUSTOMER", "EXPIRED_CONTRACT"][r.choice(3, p=[.55, .35, .10])]
            else:
                reason = ["PRICE_MISMATCH", "INELIGIBLE_CUSTOMER", "EXPIRED_CONTRACT", "DUPLICATE_CLAIM", "MISSING_DEA"][r.choice(5, p=[.3, .25, .15, .2, .1])]
            age = (AS_OF - submitted).days
            if age < 20:
                status, settled = "DISPUTED", None
            else:
                status = "REJECTED" if r.random() < .35 else "DISPUTED"
                settled = submitted + timedelta(days=int(r.integers(15, 45))) if status == "REJECTED" else None
        else:
            age = (AS_OF - submitted).days
            settle_days = int(r.integers(int(t * .6), int(t * 1.3)))
            if age < 5:
                status, settled = "SUBMITTED", None
            elif age < settle_days:
                status, settled = ("APPROVED" if age > settle_days * .5 else "SUBMITTED"), None
            else:
                status, settled = "PAID", submitted + timedelta(days=settle_days)
        rows.append({"CHARGEBACK_ID": f"CB-{i:08d}", "ORDER_LINE_ID": l.ORDER_LINE_ID, "MANUFACTURER_ID": l.X_MFR, "NDC": l.NDC,
                     "CUSTOMER_ID": l.CUSTOMER_ID, "GPO_ID": gpo[l.CUSTOMER_ID], "SUBMITTED_DATE": submitted, "SETTLED_DATE": settled,
                     "UNITS": int(l.QTY_SHIPPED), "WAC_AMOUNT": wac_amt, "CONTRACT_AMOUNT": con_amt, "CHARGEBACK_AMOUNT": cb_amt,
                     "STATUS": status, "DISPUTE_REASON": reason, "PRICE_FILE_VERSION": "2026-04A" if keldon_new else "2025-01A"})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# SERVICE CASES
# ---------------------------------------------------------------------------
SLA = {"LOW": 120, "MEDIUM": 72, "HIGH": 24, "CRITICAL": 8}


def build_service_cases(customers, backorders, shipments, cce, lines):
    r = rng("cases")
    tier = customers.set_index("CUSTOMER_ID")["CUSTOMER_TIER"]
    cname = customers.set_index("CUSTOMER_ID")["CUSTOMER_NAME"]
    prod_name = None
    rows = []
    n = 0

    def add(cid, opened, ctype, sev, site=None, dc=None, bo=None, shp=None, summary="", force_open=False, escalate=None):
        nonlocal n
        n += 1
        sla = SLA[sev]
        if force_open or opened > AS_OF - timedelta(days=int(r.integers(1, 6))):
            status, closed, hrs, met = ("OPEN" if r.random() < .5 else "IN_PROGRESS"), None, None, None
        else:
            hrs = round(float(sla * r.lognormal(-0.2, 0.6)), 1)
            closed = opened + timedelta(days=max(0, int(hrs // 24)))
            status, met = "CLOSED", hrs <= sla
        esc = escalate if escalate is not None else (sev in ("HIGH", "CRITICAL") and r.random() < .12)
        rows.append({"CASE_ID": f"CASE-{n:08d}", "CUSTOMER_ID": cid, "SITE_ID": site, "DC_ID": dc, "RELATED_BACKORDER_ID": bo, "RELATED_SHIPMENT_ID": shp,
                     "OPENED_DATE": opened, "CLOSED_DATE": closed, "CASE_TYPE": ctype, "SEVERITY": sev, "STATUS": status, "SLA_HOURS": sla,
                     "RESOLUTION_HOURS": hrs, "SLA_MET": met, "ESCALATED_TO_EXEC": bool(esc), "CASE_SUMMARY": summary[:300]})

    # (a) backorders over 14 days raise PRODUCT_AVAILABILITY cases
    aged = backorders[backorders.DAYS_OPEN > 14]
    pn = None
    for b in aged.itertuples(index=False):
        p = 0.30 if tier[b.CUSTOMER_ID] == "STRATEGIC" else (0.30 if tier[b.CUSTOMER_ID] == "KEY" else 0.22)
        if r.random() >= p:
            continue
        sev = "HIGH" if tier[b.CUSTOMER_ID] == "STRATEGIC" else ("HIGH" if r.random() < .5 else "MEDIUM")
        opened = b.BACKORDER_DATE + timedelta(days=int(r.integers(10, 16)))
        if opened > AS_OF:
            continue
        force_open = b.STATUS == "OPEN"
        add(b.CUSTOMER_ID, opened, "PRODUCT_AVAILABILITY", sev, site=b.SITE_ID, dc=b.DC_ID, bo=b.BACKORDER_ID,
            summary=f"{cname[b.CUSTOMER_ID]} escalated a backorder open {b.DAYS_OPEN} days for {b.NDC} ({b.REASON_CODE}); patient scheduling impacted.",
            force_open=force_open, escalate=(force_open and b.CUSTOMER_ID in SQUEEZED_CUSTOMERS and r.random() < .2))
    # (b) some quick PRODUCT_AVAILABILITY cases for younger backorders (lower rate)
    young = backorders[(backorders.DAYS_OPEN <= 14)].sample(frac=0.03, random_state=SEED)
    for b in young.itertuples(index=False):
        add(b.CUSTOMER_ID, b.BACKORDER_DATE + timedelta(days=int(r.integers(1, 6))), "PRODUCT_AVAILABILITY", "MEDIUM" if r.random() < .7 else "LOW",
            site=b.SITE_ID, dc=b.DC_ID, bo=b.BACKORDER_ID, summary=f"Customer asked for an ETA on backordered {b.NDC}.")
    # (c) late deliveries
    late = shipments[(shipments.ACTUAL_DELIVERY_DATE.notna()) & (shipments.ACTUAL_DELIVERY_DATE > shipments.PROMISED_DELIVERY_DATE)].sample(frac=0.18, random_state=SEED)
    for s in late.itertuples(index=False):
        sev = "MEDIUM" if r.random() < .75 else "HIGH"
        add(s.CUSTOMER_ID, s.ACTUAL_DELIVERY_DATE, "DELIVERY_DELAY", sev, site=s.SITE_ID, dc=s.DC_ID, shp=s.SHIPMENT_ID,
            summary=f"Shipment {s.SHIPMENT_ID} delivered {(s.ACTUAL_DELIVERY_DATE - s.PROMISED_DELIVERY_DATE).days} day(s) late via {s.CARRIER}.")
    # (d) temperature excursions with MAJOR/CRITICAL severity
    exc = cce[(cce.IS_EXCURSION) & (cce.EXCURSION_SEVERITY.isin(["MAJOR", "CRITICAL"])) & (cce.STAGE.isin(["IN_TRANSIT", "DELIVERY", "PACKOUT"]))]
    for e in exc.itertuples(index=False):
        if r.random() < .55:
            sev = "CRITICAL" if e.EXCURSION_SEVERITY == "CRITICAL" and r.random() < .5 else "HIGH"
            add(e.CUSTOMER_ID, e.EVENT_DATE + timedelta(days=int(r.integers(0, 3))), "TEMP_EXCURSION", sev, dc=e.DC_ID, shp=e.SHIPMENT_ID,
                summary=f"Temperature excursion ({e.EXCURSION_SEVERITY.lower()}, {e.EXCURSION_MINUTES} min) on {e.STORAGE_CLASS} product packed in {e.PACKAGING_TYPE}; product {e.DISPOSITION.lower()}.")
    # (e) background cases
    bg_types = ["BILLING_DISPUTE", "ORDER_ERROR", "DAMAGED_PRODUCT", "SHORT_SHIP"]
    for cid in customers.CUSTOMER_ID:
        k = int(r.poisson(4.5))
        for _ in range(k):
            opened = START + timedelta(days=int(r.integers(0, (AS_OF - START).days)))
            ctype = bg_types[r.choice(4, p=[.35, .3, .2, .15])]
            sev = ["LOW", "MEDIUM", "HIGH"][r.choice(3, p=[.45, .45, .10])]
            add(cid, opened, ctype, sev, summary=f"{ctype.replace('_', ' ').title()} reported by {cname[cid]}.")
    # Hero: make sure Bayview has visible open high-severity cases and two exec escalations in the last 90 days
    hero_sites = list(lines[lines.CUSTOMER_ID == HERO_CUSTOMER].SITE_ID.unique())[:3]
    hero_bos = backorders[(backorders.CUSTOMER_ID == HERO_CUSTOMER) & (backorders.STATUS == "OPEN")].sort_values("DAYS_OPEN", ascending=False)
    for k, d in enumerate([_d("2026-08-14"), _d("2026-08-28"), _d("2026-09-09"), _d("2026-09-18")]):
        bo = hero_bos.iloc[k].BACKORDER_ID if k < len(hero_bos) else None
        add(HERO_CUSTOMER, d, "PRODUCT_AVAILABILITY", "CRITICAL" if k in (1, 3) else "HIGH", site=hero_sites[k % len(hero_sites)], dc="DC-ATL", bo=bo,
            summary="Bayview pharmacy director reports repeated Vanterra shortfalls; clinics rescheduling GLP-1 starts and asking whether Halcyon can guarantee supply through renewal.",
            force_open=True, escalate=(k in (1, 3)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# DATA DICTIONARY
# ---------------------------------------------------------------------------
DATA_DICTIONARY_ROWS = [
    ("ORDER_LINES", "QTY_SHIPPED", "NUMBER", "Units shipped on first release; compare to QTY_ORDERED for line fill", "24", None),
    ("ORDER_LINES", "SHORT_REASON_CODE", "VARCHAR", "Why units were not shipped: ALLOCATION_LIMIT, STOCKOUT, MFR_SHORTAGE, QUALITY_HOLD, CREDIT_HOLD", "ALLOCATION_LIMIT", None),
    ("ORDER_LINES", "IS_CONTRACT_PRICED", "BOOLEAN", "TRUE when a GPO contract price applied; every such shipped line generates a chargeback", "TRUE", None),
    ("V_ORDER_LINE_DETAIL", "IS_LINE_FILLED_COMPLETE", "NUMBER", "1 when qty_shipped >= qty_ordered", "1", "CASE WHEN QTY_SHIPPED >= QTY_ORDERED THEN 1 ELSE 0 END"),
    ("V_FILL_RATE_CUSTOMER_MONTH", "LINE_FILL_RATE", "NUMBER", "Share of lines shipped complete on first release", "0.9634", "SUM(IS_LINE_FILLED_COMPLETE) / COUNT(*)"),
    ("V_FILL_RATE_CUSTOMER_MONTH", "UNIT_FILL_RATE", "NUMBER", "Units shipped as a share of units ordered", "0.9812", "SUM(QTY_SHIPPED) / SUM(QTY_ORDERED)"),
    ("V_FILL_RATE_CUSTOMER_MONTH", "BACKORDER_RATE", "NUMBER", "Units backordered as a share of units ordered", "0.0150", "SUM(QTY_BACKORDERED) / SUM(QTY_ORDERED)"),
    ("V_CUSTOMER_HEALTH", "OPERATIONAL_RISK_SCORE", "NUMBER", "0-100 transparent triage score: 35 fill rate deterioration, 25 backorder aging, 25 service cases, 15 volume decline. Not a churn prediction.", "62.4", "LEAST(35,-FILL_RATE_CHANGE*175)+LEAST(25,OPEN_BACKORDERS_OVER_14D*5)+LEAST(25,OPEN_HIGH_SEVERITY_CASES*8+EXEC_ESCALATIONS_90D*5)+LEAST(15,-DISCRETIONARY_VALUE_CHANGE_PCT*75)"),
    ("V_CUSTOMER_HEALTH", "DISCRETIONARY_VALUE_CHANGE_PCT", "NUMBER", "Change in ordered WAC value of non-allocated products, recent 8 weeks vs prior 8 weeks. Allocated products are excluded because their demand is supply-constrained.", "-0.24", "(RECENT_DISCRETIONARY_VALUE_WAC - PRIOR_DISCRETIONARY_VALUE_WAC) / PRIOR_DISCRETIONARY_VALUE_WAC"),
    ("V_CUSTOMER_HEALTH", "FILL_RATE_CHANGE", "NUMBER", "Recent 8-week line fill rate minus prior 8-week line fill rate (negative = deteriorating)", "-0.18", "RECENT_LINE_FILL_RATE - PRIOR_LINE_FILL_RATE"),
    ("V_CUSTOMER_HEALTH", "DAYS_TO_RENEWAL", "NUMBER", "Days from 2026-09-25 to the contract renewal date", "81", "DATEDIFF('day', DATE '2026-09-25', CONTRACT_RENEWAL_DATE)"),
    ("BACKORDERS", "DAYS_OPEN", "NUMBER", "Days a backorder has been open; over 14 is the escalation threshold", "23", None),
    ("CUSTOMER_ALLOCATIONS", "SHORTFALL_UNITS", "NUMBER", "Units requested above what Halcyon could allocate", "180", "GREATEST(CUSTOMER_REQUESTED_UNITS - CUSTOMER_ALLOCATED_UNITS, 0)"),
    ("CUSTOMER_ALLOCATIONS", "HALCYON_TOTAL_ALLOCATION_UNITS", "NUMBER", "Manufacturer allocation to Halcyon for the NDC and month; repeated on every customer row, take MAX not SUM", "8400", None),
    ("COLD_CHAIN_EVENTS", "IS_EXCURSION", "BOOLEAN", "TRUE when a reading was outside the storage class range", "TRUE", None),
    ("V_COLD_CHAIN_EXCURSIONS", "EXCURSION_RATE", "NUMBER", "Excursions as a share of monitored readings", "0.0071", "SUM(IS_EXCURSION) / COUNT(*)"),
    ("INVENTORY_SNAPSHOTS", "DAYS_OF_SUPPLY", "NUMBER", "Available units divided by average daily demand", "34.5", "AVAILABLE_UNITS / (AVG_WEEKLY_DEMAND_UNITS / 7)"),
    ("V_INVENTORY_RISK", "IS_EXPIRY_WRITE_OFF_RISK", "NUMBER", "1 when 12 weeks of demand cannot consume the units expiring in 90 days", "1", "CASE WHEN AVG_WEEKLY_DEMAND_UNITS * 12 < EXPIRING_90D_UNITS THEN 1 ELSE 0 END"),
    ("CHARGEBACKS", "CHARGEBACK_AMOUNT", "NUMBER", "WAC amount minus contract amount; what the manufacturer owes Halcyon", "1840.00", "WAC_AMOUNT - CONTRACT_AMOUNT"),
    ("V_CHARGEBACK_SUMMARY", "DISPUTE_RATE", "NUMBER", "Disputed or rejected claims as a share of claims submitted", "0.22", "SUM(STATUS IN ('DISPUTED','REJECTED')) / COUNT(*)"),
    ("SERVICE_CASES", "SLA_MET", "BOOLEAN", "TRUE when resolution_hours is within the severity SLA (LOW 120h, MEDIUM 72h, HIGH 24h, CRITICAL 8h)", "FALSE", "RESOLUTION_HOURS <= SLA_HOURS"),
    ("V_DC_SERVICE_PERFORMANCE", "ON_TIME_DELIVERY_RATE", "NUMBER", "Delivered shipments on or before the promised date", "0.9412", "SUM(ACTUAL_DELIVERY_DATE <= PROMISED_DELIVERY_DATE) / COUNT(delivered)"),
]


def build_data_dictionary() -> pd.DataFrame:
    return pd.DataFrame(DATA_DICTIONARY_ROWS, columns=["TABLE_NAME", "COLUMN_NAME", "DATA_TYPE", "DESCRIPTION", "SAMPLE_VALUE", "METRIC_FORMULA"])


# ---------------------------------------------------------------------------
# ORCHESTRATION + CACHE
# ---------------------------------------------------------------------------
LOAD_ORDER = ["CALENDAR", "DISTRIBUTION_CENTERS", "MANUFACTURERS", "GPOS", "PRODUCTS", "CUSTOMERS", "CUSTOMER_SITES", "CONTRACT_PRICES",
              "ORDERS", "ORDER_LINES", "SHIPMENTS", "COLD_CHAIN_EVENTS", "BACKORDERS", "INVENTORY_SNAPSHOTS", "CUSTOMER_ALLOCATIONS",
              "RETURNS", "CHARGEBACKS", "SERVICE_CASES", "DATA_DICTIONARY"]


def generate_all(verbose=True) -> dict:
    def log(msg):
        if verbose:
            print(msg, flush=True)
    log("Building dimensions...")
    cal = build_calendar()
    dcs = build_distribution_centers()
    mfrs = build_manufacturers()
    gpos = build_gpos()
    products = build_products()
    customers = build_customers()
    sites = build_customer_sites(customers)
    cps = build_contract_prices(products)
    log("Building orders and lines (this is the slow step, ~1-2 min)...")
    orders, lines = build_orders_and_lines(customers, sites, products, cps)
    log(f"  orders={len(orders):,} lines={len(lines):,}")
    log("Building shipments and cold chain events...")
    shipments, cce = build_shipments_and_cold_chain(orders, lines)
    log("Building backorders, inventory, allocations...")
    backorders = build_backorders(lines)
    inventory = build_inventory_snapshots(lines, products, dcs)
    allocations = build_customer_allocations(lines, products)
    log("Building returns, chargebacks, service cases...")
    returns = build_returns(lines, shipments, cce)
    chargebacks = build_chargebacks(lines, customers, mfrs)
    cases = build_service_cases(customers, backorders, shipments, cce, lines)
    dd = build_data_dictionary()

    products_out = products.drop(columns=[c for c in products.columns if c.startswith("X_")])
    lines_out = lines.drop(columns=[c for c in lines.columns if c.startswith("X_")])
    frames = {
        "CALENDAR": cal, "DISTRIBUTION_CENTERS": dcs, "MANUFACTURERS": mfrs, "GPOS": gpos, "PRODUCTS": products_out,
        "CUSTOMERS": customers, "CUSTOMER_SITES": sites, "CONTRACT_PRICES": cps, "ORDERS": orders, "ORDER_LINES": lines_out,
        "SHIPMENTS": shipments, "COLD_CHAIN_EVENTS": cce, "BACKORDERS": backorders, "INVENTORY_SNAPSHOTS": inventory,
        "CUSTOMER_ALLOCATIONS": allocations, "RETURNS": returns, "CHARGEBACKS": chargebacks, "SERVICE_CASES": cases,
        "DATA_DICTIONARY": dd,
    }
    return frames
