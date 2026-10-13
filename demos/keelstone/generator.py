"""
generator.py (Keelstone Data Systems)
------------------------------------
Deterministic synthetic data for the Keelstone Data Systems WisdomAI POC.
No Snowflake dependency. Every builder is seeded so the same rows are produced
on every run.

Demo "today" (AS_OF) = 2026-10-12 (Q2 FY27; fiscal year ends 30 April).
Data spans 2025-05-01 .. 2026-10-12; installs and contracts reach back earlier.

Engineered control points (see ../DEMO_PLAN.md):
  CP1  Americas East renewal rate slips in FY27: KS-7000 end of support (bulletin
       2026-06-15, EOS 2027-01-31) plus P1 cases after the KeelOS 9.14.2 upgrade
       wave that started in Americas East in July 2026.
  CP2  Sales Ops ARR exceeds Finance ARR: Sales Ops keeps counting a lapsed contract
       while its renewal opportunity is still open in Salesforce (renewals ops closes
       lost 90-365 days after the lapse); Finance stops at end_date.
  CP3  Keelstone Cloud Volumes consumption grows ~40% YoY while ~25 enterprise
       accounts run below 60% of commit.
  CP4  Altura Technology Partners' support attach rate falls in FY27 while peers hold.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from demo_creator.rng import rng as _seeded_rng

SEED = 20261012
AS_OF = date(2026, 10, 12)
START = date(2025, 5, 1)
CAL_START = date(2024, 5, 1)
CAL_END = date(2027, 4, 30)

# Story constants (mirrored in demo.yaml generator.constants)
HERO_REGION = "Americas East"
EOS_FAMILY = "KS-7000"
EOS_DATE = date(2027, 1, 31)
EOS_ANNOUNCED = date(2026, 6, 15)
KS7_END_OF_SALE = date(2025, 10, 31)
BAD_FW = "KeelOS 9.14.2"
BAD_FW_RELEASE = date(2026, 7, 1)
FIX_FW = "KeelOS 9.14.3"
FIX_FW_RELEASE = date(2026, 9, 15)
FY27_START = date(2026, 5, 1)
HERO_PARTNER = "PTR-003"          # Altura Technology Partners
CLOUD_FAMILY = "Keelstone Cloud Volumes"

REGIONS = ["Americas East", "Americas West", "EMEA", "APAC"]
REGION_W = [0.32, 0.23, 0.28, 0.17]
THEATER = {"Americas East": "Americas", "Americas West": "Americas", "EMEA": "International", "APAC": "International"}
REGION_COUNTRIES = {
    "Americas East": ["United States"] * 8 + ["Canada", "Brazil"],
    "Americas West": ["United States"] * 8 + ["Canada", "Mexico"],
    "EMEA": ["United Kingdom", "Germany", "France", "Netherlands", "Sweden", "Switzerland", "Spain", "Italy", "United Arab Emirates", "South Africa"],
    "APAC": ["Japan", "Australia", "Singapore", "India", "South Korea", "Hong Kong", "New Zealand"],
}
REGION_CITIES = {
    "Americas East": ["New York", "Boston", "Atlanta", "Charlotte", "Toronto", "Miami", "Philadelphia", "Washington", "Chicago", "Sao Paulo"],
    "Americas West": ["San Jose", "Seattle", "Denver", "Phoenix", "Los Angeles", "Dallas", "Vancouver", "Austin", "Portland", "Mexico City"],
    "EMEA": ["London", "Frankfurt", "Paris", "Amsterdam", "Stockholm", "Zurich", "Madrid", "Milan", "Dubai", "Johannesburg"],
    "APAC": ["Tokyo", "Sydney", "Singapore", "Bengaluru", "Seoul", "Hong Kong", "Auckland", "Melbourne", "Osaka", "Mumbai"],
}
INDUSTRIES = ["Financial Services", "Healthcare", "Manufacturing", "Retail", "Technology", "Public Sector", "Education", "Media", "Energy", "Life Sciences"]


def rng(tag: str) -> np.random.Generator:
    """Independent generator per builder so adding rows to one table never reshuffles another."""
    return _seeded_rng(SEED, tag)


def _d(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _month_start(d: date) -> date:
    return d.replace(day=1)


def _add_months(d: date, n: int) -> date:
    y, m = d.year, d.month + n
    while m > 12:
        y += 1
        m -= 12
    while m < 1:
        y -= 1
        m += 12
    return date(y, m, min(d.day, 28))


def _month_end(d: date) -> date:
    return _add_months(_month_start(d), 1) - timedelta(days=1)


def fiscal_year(d: date) -> str:
    fy = d.year + 1 if d.month >= 5 else d.year
    return f"FY{fy % 100:02d}"


def fiscal_quarter(d: date) -> str:
    fm = (d.month - 5) % 12 + 1
    return f"{fiscal_year(d)}-Q{(fm - 1) // 3 + 1}"


def _rdate(g: np.random.Generator, a: date, b: date) -> date:
    span = (b - a).days
    return a + timedelta(days=int(g.integers(0, max(span, 0) + 1)))


# ---------------------------------------------------------------------------
# FISCAL_CALENDAR
# ---------------------------------------------------------------------------
def build_fiscal_calendar() -> pd.DataFrame:
    rows = []
    for ts in pd.date_range(CAL_START, CAL_END, freq="D"):
        d = ts.date()
        fy_start = date(d.year if d.month >= 5 else d.year - 1, 5, 1)
        rows.append({
            "CALENDAR_DATE": d,
            "MONTH_START_DATE": _month_start(d),
            "MONTH_END_DATE": _month_end(d),
            "FISCAL_YEAR": fiscal_year(d),
            "FISCAL_QUARTER": fiscal_quarter(d),
            "FISCAL_MONTH_NUM": (d.month - 5) % 12 + 1,
            "FISCAL_YEAR_START_DATE": fy_start,
            "CALENDAR_QUARTER": f"{d.year}-Q{(d.month - 1) // 3 + 1}",
            "IS_COMPLETE_MONTH": _month_end(d) < AS_OF,
            "IS_WEEKEND": d.weekday() >= 5,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# PARTNERS
# ---------------------------------------------------------------------------
PARTNERS = [
    ("PTR-000", "Keelstone Direct", "DIRECT", "NA", "Global", "United States", "2015-01-01"),
    ("PTR-001", "Northwind Integrators", "VAR", "PLATINUM", "Americas East", "United States", "2016-03-14"),
    ("PTR-002", "Stonebridge Systems", "VAR", "GOLD", "Americas East", "United States", "2018-07-02"),
    ("PTR-003", "Altura Technology Partners", "VAR", "PLATINUM", "Americas East", "United States", "2015-09-21"),
    ("PTR-004", "Fairhaven Technology Partners", "VAR", "SILVER", "Americas East", "Canada", "2020-02-10"),
    ("PTR-005", "Ironbridge Managed Services", "MSP", "GOLD", "Americas East", "United States", "2019-05-06"),
    ("PTR-006", "Caldera Data Solutions", "VAR", "PLATINUM", "Americas West", "United States", "2016-11-28"),
    ("PTR-007", "Brightline Systems", "VAR", "GOLD", "Americas West", "United States", "2017-08-15"),
    ("PTR-008", "Vectorpoint Technologies", "VAR", "SILVER", "Americas West", "United States", "2021-01-19"),
    ("PTR-009", "Copperfield IT Group", "VAR", "GOLD", "Americas West", "Mexico", "2019-10-07"),
    ("PTR-010", "Lumen Arc Managed Cloud", "MSP", "GOLD", "Americas West", "United States", "2020-06-22"),
    ("PTR-011", "Harbourline Technology", "VAR", "PLATINUM", "EMEA", "United Kingdom", "2016-04-04"),
    ("PTR-012", "Oakfield Solutions", "VAR", "GOLD", "EMEA", "Germany", "2017-02-13"),
    ("PTR-013", "Tessera Networks", "VAR", "GOLD", "EMEA", "France", "2018-09-24"),
    ("PTR-014", "Marlowe and Vance Technology", "VAR", "SILVER", "EMEA", "Netherlands", "2020-11-30"),
    ("PTR-015", "Elmridge Solutions", "VAR", "SILVER", "EMEA", "Sweden", "2021-05-17"),
    ("PTR-016", "Kestrel Infrastructure Partners", "VAR", "PLATINUM", "APAC", "Australia", "2016-08-08"),
    ("PTR-017", "Pacific Crest Systems", "VAR", "GOLD", "APAC", "Singapore", "2018-03-26"),
    ("PTR-018", "Sakura Digital Partners", "VAR", "GOLD", "APAC", "Japan", "2017-06-12"),
    ("PTR-019", "Redgum Technology", "VAR", "SILVER", "APAC", "Australia", "2021-09-01"),
    ("PTR-020", "Tarn Hill Technology", "MSP", "SILVER", "APAC", "India", "2022-01-10"),
    ("PTR-021", "Silverleaf Distribution", "DISTRIBUTOR", "PLATINUM", "Global", "United States", "2015-06-15"),
    ("PTR-022", "Granite Peak Distribution", "DISTRIBUTOR", "GOLD", "Global", "United Kingdom", "2016-10-03"),
    ("PTR-023", "Bluewater Technologies", "VAR", "GOLD", "Americas West", "Canada", "2019-04-29"),
    ("PTR-024", "Summit Ridge IT", "VAR", "SILVER", "Americas East", "United States", "2022-03-07"),
]


def build_partners() -> pd.DataFrame:
    df = pd.DataFrame(PARTNERS, columns=["PARTNER_ID", "PARTNER_NAME", "PARTNER_TYPE", "PARTNER_TIER", "PRIMARY_REGION", "HQ_COUNTRY", "PARTNER_SINCE"])
    df["PARTNER_SINCE"] = df["PARTNER_SINCE"].map(_d)
    return df


# ---------------------------------------------------------------------------
# SALES_REPS
# ---------------------------------------------------------------------------
FIRST = ["Maya", "Daniel", "Priya", "Marcus", "Elena", "Jonas", "Aisha", "Liam", "Sofia", "Noah", "Hannah", "Mateo", "Grace", "Omar", "Chloe",
         "Ravi", "Isabel", "Ethan", "Nora", "Tomas", "Leila", "Felix", "Amara", "Lucas", "Ingrid", "Kenji", "Zara", "Hugo", "Mei", "Samuel",
         "Yuki", "Diego", "Freya", "Arjun", "Clara", "Idris", "Tessa", "Rafael", "Anika", "Caleb"]
LAST = ["Okafor", "Lindqvist", "Ramirez", "Chen", "Whitfield", "Nakamura", "Haddad", "Fischer", "Osei", "Brennan", "Kowalski", "Moreau",
        "Delgado", "Iyer", "Sorensen", "Blackwood", "Tanaka", "Varga", "Mbeki", "Hartley", "Novak", "Castillo", "Reyes", "Dubois",
        "Ferreira", "Olsen", "Pham", "Sato", "Eriksson", "Gallagher", "Mensah", "Petrov", "Alvarez", "Kaur", "Lund", "Rossi", "Yamada", "Weber"]
MANAGERS = {"Americas East": "Victoria Lang", "Americas West": "Andre Castellanos", "EMEA": "Margaret Hollis", "APAC": "Kenneth Wu"}


def build_sales_reps() -> pd.DataFrame:
    g = rng("reps")
    rows = []
    i = 0
    for region in REGIONS:
        roles = ["Account Executive"] * 11 + ["Renewals Specialist"] * 3 + ["Cloud Specialist"]
        for role in roles:
            i += 1
            name = f"{FIRST[int(g.integers(len(FIRST)))]} {LAST[int(g.integers(len(LAST)))]}"
            rows.append({
                "REP_ID": f"REP-{i:03d}", "REP_NAME": name, "REP_ROLE": role, "REGION": region, "THEATER": THEATER[region],
                "MANAGER_NAME": MANAGERS[region], "HIRE_DATE": _rdate(g, date(2015, 1, 1), date(2025, 6, 30)), "IS_ACTIVE": True,
            })
    df = pd.DataFrame(rows)
    # make names unique
    seen = {}
    for idx, n in enumerate(df["REP_NAME"]):
        if n in seen:
            seen[n] += 1
            df.at[idx, "REP_NAME"] = f"{n} {'Jr' if seen[n] == 1 else 'II'}"
        else:
            seen[n] = 0
    return df


# ---------------------------------------------------------------------------
# CUSTOMERS
# ---------------------------------------------------------------------------
HERO_CUSTOMERS = [  # Americas East enterprise accounts that carry the story
    ("Brightwater Mutual Insurance", "Financial Services", "PTR-003"),
    ("Tidewater Health Alliance", "Healthcare", "PTR-001"),
    ("Carrow and Finch Capital", "Financial Services", "PTR-000"),
    ("Pinecrest Regional Health", "Healthcare", "PTR-003"),
    ("Harrowgate Logistics", "Manufacturing", "PTR-002"),
    ("Atlantic Meridian Bank", "Financial Services", "PTR-000"),
    ("Greystone Media Group", "Media", "PTR-001"),
    ("Northfield Grocers", "Retail", "PTR-003"),
    ("Beacon Hill University Health", "Healthcare", "PTR-005"),
    ("Sterling Oak Life Sciences", "Life Sciences", "PTR-000"),
    ("Commonwealth Transit Authority", "Public Sector", "PTR-002"),
    ("Delmarva Energy Cooperative", "Energy", "PTR-003"),
]
NAME_A = ["Brightwater", "Tidewater", "Harrowgate", "Pinecrest", "Greystone", "Northfield", "Sterling Oak", "Beacon Hill", "Delmarva", "Silverline",
          "Oakhurst", "Riverbend", "Ashford", "Cedar Point", "Highland", "Lakeshore", "Maplewood", "Ironwood", "Westbrook", "Summitview",
          "Clearwater", "Redfern", "Stonehaven", "Goldcrest", "Blue Ridge", "Evergreen", "Falcon Rock", "Granite Bay", "Hawthorne", "Juniper",
          "Kingsbridge", "Larkspur", "Mariner", "Nightingale", "Orchard", "Prospect", "Quarry Hill", "Rosewood", "Saltmarsh", "Thornfield",
          "Umber", "Valewood", "Wexford", "Yarrow", "Zephyr", "Alder", "Bramble", "Coldspring", "Dunmore", "Elkhorn", "Foxglove", "Glenmoor",
          "Holloway", "Ivory Coast", "Kestrel", "Linden", "Moorland", "Netherby", "Oldcastle", "Pembrook", "Quayside", "Ravenswood", "Seabright",
          "Tamarind", "Underhill", "Vantage", "Willowmere", "Amberly", "Birchwood", "Crestline", "Dovetail", "Eastgate", "Fernhill", "Greenway"]
NAME_B = {
    "Financial Services": ["Mutual Insurance", "Capital", "Bank", "Financial Group", "Credit Union", "Asset Management", "Trust", "Insurance Group"],
    "Healthcare": ["Health Alliance", "Regional Health", "Medical Center", "Health System", "Hospitals", "Care Network", "Clinics"],
    "Manufacturing": ["Logistics", "Industries", "Manufacturing", "Automotive", "Components", "Fabrication", "Precision"],
    "Retail": ["Grocers", "Retail Group", "Stores", "Outfitters", "Home and Garden", "Marketplace"],
    "Technology": ["Software", "Digital", "Cloud Services", "Labs", "Analytics", "Systems", "Networks"],
    "Public Sector": ["Transit Authority", "County", "City Services", "Water Authority", "Department of Revenue", "Port Authority"],
    "Education": ["University", "College", "School District", "Institute of Technology", "Polytechnic"],
    "Media": ["Media Group", "Broadcasting", "Studios", "Publishing", "Entertainment"],
    "Energy": ["Energy Cooperative", "Power", "Utilities", "Renewables", "Gas and Electric", "Pipeline"],
    "Life Sciences": ["Life Sciences", "Biotherapeutics", "Pharma", "Diagnostics", "Genomics", "Clinical Research"],
}


def build_customers(partners: pd.DataFrame) -> pd.DataFrame:
    g = rng("customers")
    partner_by_region = {r: partners[(partners.PRIMARY_REGION == r) & (partners.PARTNER_TYPE != "DIRECT")].PARTNER_ID.tolist() for r in REGIONS}
    global_partners = partners[partners.PRIMARY_REGION == "Global"].PARTNER_ID.tolist()
    rows, used = [], set()
    n_total = 400
    for i in range(1, n_total + 1):
        if i <= len(HERO_CUSTOMERS):
            name, industry, partner = HERO_CUSTOMERS[i - 1]
            region, segment = HERO_REGION, "ENTERPRISE"
        else:
            region = REGIONS[int(g.choice(len(REGIONS), p=REGION_W))]
            segment = ["ENTERPRISE", "COMMERCIAL", "PUBLIC_SECTOR"][int(g.choice(3, p=[0.28, 0.59, 0.13]))]
            industry = "Public Sector" if segment == "PUBLIC_SECTOR" and g.random() < 0.6 else INDUSTRIES[int(g.integers(len(INDUSTRIES)))]
            if segment == "PUBLIC_SECTOR" and industry not in ("Public Sector", "Education", "Healthcare"):
                industry = "Public Sector"
            while True:
                name = f"{NAME_A[int(g.integers(len(NAME_A)))]} {NAME_B[industry][int(g.integers(len(NAME_B[industry])))]}"
                if name not in used:
                    break
            if segment == "ENTERPRISE" and g.random() < 0.25:
                partner = "PTR-000"
            elif g.random() < 0.15:
                partner = global_partners[int(g.integers(len(global_partners)))]
            else:
                pool = partner_by_region[region]
                if region == HERO_REGION:
                    pool = pool + [HERO_PARTNER] * 2  # Altura is the largest Americas East partner
                partner = pool[int(g.integers(len(pool)))]
        used.add(name)
        crm = "001" + "".join(str(int(g.integers(10))) for _ in range(12)) + "AAA"
        rows.append({
            "CUSTOMER_ID": f"CUST-{i:04d}", "CUSTOMER_NAME": name, "CRM_ACCOUNT_ID": crm, "SEGMENT": segment, "INDUSTRY": industry,
            "REGION": region, "COUNTRY": REGION_COUNTRIES[region][int(g.integers(len(REGION_COUNTRIES[region])))],
            "PARTNER_ID": partner, "REP_ID": None, "CUSTOMER_SINCE": None, "IS_ACTIVE": True,
        })
    df = pd.DataFrame(rows)
    return df


def assign_reps(customers: pd.DataFrame, reps: pd.DataFrame) -> pd.DataFrame:
    g = rng("customer_reps")
    aes = {r: reps[(reps.REGION == r) & (reps.REP_ROLE == "Account Executive")].REP_ID.tolist() for r in REGIONS}
    customers = customers.copy()
    customers["REP_ID"] = [aes[r][int(g.integers(len(aes[r])))] for r in customers.REGION]
    return customers


# ---------------------------------------------------------------------------
# PRODUCTS
# ---------------------------------------------------------------------------
PRODUCTS = [
    # id, name, family, line, tier, list, uom, ga, eosale, eos, recurring, desc
    ("KS-5200", "KS-5200 All-Flash Array", "KS-5000", "HARDWARE", None, 95000, "SYSTEM", "2022-03-01", None, None, False, "Entry all-flash array for departmental workloads, up to 400 TB raw"),
    ("KS-5400", "KS-5400 All-Flash Array", "KS-5000", "HARDWARE", None, 140000, "SYSTEM", "2022-03-01", None, None, False, "Mid-range all-flash array, up to 800 TB raw"),
    ("KS-7200", "KS-7200 All-Flash Array", "KS-7000", "HARDWARE", None, 180000, "SYSTEM", "2019-06-01", "2025-10-31", "2027-01-31", False, "Previous-generation enterprise all-flash array. End of sale 2025-10-31; end of support 2027-01-31."),
    ("KS-7400", "KS-7400 All-Flash Array", "KS-7000", "HARDWARE", None, 260000, "SYSTEM", "2019-06-01", "2025-10-31", "2027-01-31", False, "Previous-generation enterprise all-flash array. End of sale 2025-10-31; end of support 2027-01-31."),
    ("KS-7600", "KS-7600 All-Flash Array", "KS-7000", "HARDWARE", None, 340000, "SYSTEM", "2020-02-01", "2025-10-31", "2027-01-31", False, "Previous-generation high-end all-flash array. End of sale 2025-10-31; end of support 2027-01-31."),
    ("KS-9300", "KS-9300 NVMe Array", "KS-9000", "HARDWARE", None, 420000, "SYSTEM", "2024-05-01", None, None, False, "Current-generation enterprise NVMe array, the migration target for KS-7200 and KS-7400"),
    ("KS-9500", "KS-9500 NVMe Array", "KS-9000", "HARDWARE", None, 620000, "SYSTEM", "2024-05-01", None, None, False, "Current-generation enterprise NVMe array, the migration target for KS-7600"),
    ("KS-9700", "KS-9700 NVMe Array", "KS-9000", "HARDWARE", None, 880000, "SYSTEM", "2025-02-01", None, None, False, "Flagship NVMe array for mission-critical databases and AI pipelines"),
    ("HD-3200", "HD-3200 Hybrid Array", "HD-3000", "HARDWARE", None, 70000, "SYSTEM", "2021-01-01", "2026-12-31", "2028-06-30", False, "Hybrid flash and disk array for backup and file archives. End of sale 2026-12-31."),
    ("HD-3400", "HD-3400 Hybrid Array", "HD-3000", "HARDWARE", None, 110000, "SYSTEM", "2021-01-01", "2026-12-31", "2028-06-30", False, "Larger hybrid array for backup targets. End of sale 2026-12-31."),
    ("KOS-CORE", "KeelOS Core Subscription", "KeelOS", "SOFTWARE_SUBSCRIPTION", None, 480, "TB_PER_YEAR", "2019-01-01", None, None, True, "Base KeelOS storage operating system subscription, licensed per array on its raw TB per year"),
    ("KOS-ADS", "KeelOS Advanced Data Services", "KeelOS", "SOFTWARE_SUBSCRIPTION", None, 160, "TB_PER_YEAR", "2021-01-01", None, None, True, "Snapshots, replication and tiering add-on, per TB per year"),
    ("KOS-SHIELD", "KeelOS Ransomware Shield", "KeelOS", "SOFTWARE_SUBSCRIPTION", None, 120, "TB_PER_YEAR", "2023-03-01", None, None, True, "Immutable snapshot and anomaly detection add-on, per TB per year"),
    ("KOS-INSIGHT", "Keelstone Insight", "KeelOS", "SOFTWARE_SUBSCRIPTION", None, 45000, "SYSTEM_PER_YEAR", "2022-06-01", None, None, True, "SaaS fleet management and capacity planning console, per fleet per year"),
    ("KOS-BACKUP", "Keelstone Backup Suite", "KeelOS", "SOFTWARE_SUBSCRIPTION", None, 90, "TB_PER_YEAR", "2022-01-01", None, None, True, "Backup orchestration and cloud archive add-on, per TB per year"),
    ("KCV-AZURE", "Keelstone Cloud Volumes for Azure", "Keelstone Cloud Volumes", "CLOUD_SERVICE", None, 1, "COMMIT_USD_PER_YEAR", "2022-09-01", None, None, True, "Managed KeelOS file and block volumes in Azure, billed against an annual commit"),
    ("KCV-AWS", "Keelstone Cloud Volumes for AWS", "Keelstone Cloud Volumes", "CLOUD_SERVICE", None, 1, "COMMIT_USD_PER_YEAR", "2023-02-01", None, None, True, "Managed KeelOS volumes in AWS, billed against an annual commit"),
    ("KCV-GCP", "Keelstone Cloud Volumes for Google Cloud", "Keelstone Cloud Volumes", "CLOUD_SERVICE", None, 1, "COMMIT_USD_PER_YEAR", "2024-01-01", None, None, True, "Managed KeelOS volumes in Google Cloud, billed against an annual commit"),
    ("KOS-OBJECT", "Keelstone Object Store", "Keelstone Object Store", "CLOUD_SERVICE", None, 1, "COMMIT_USD_PER_YEAR", "2024-06-01", None, None, True, "S3-compatible object storage service, billed against an annual commit"),
    ("SUP-STD", "Standard Support", "Support", "SUPPORT", "STANDARD", 24000, "SYSTEM_PER_YEAR", "2015-01-01", None, None, True, "Next-business-day parts and 8x5 engineering support, priced per system per year at about 14 percent of hardware list"),
    ("SUP-PREM", "Premium Support", "Support", "SUPPORT", "PREMIUM", 38000, "SYSTEM_PER_YEAR", "2015-01-01", None, None, True, "4-hour parts and 24x7 engineering support, about 18 percent of hardware list"),
    ("SUP-MC", "Mission Critical Support", "Support", "SUPPORT", "MISSION_CRITICAL", 56000, "SYSTEM_PER_YEAR", "2018-01-01", None, None, True, "2-hour onsite, named engineer and proactive AutoPulse monitoring, about 24 percent of hardware list"),
    ("SUP-EXT7K", "KS-7000 Extended Support", "Support", "SUPPORT", "EXTENDED", 30000, "SYSTEM_PER_YEAR", "2026-06-15", None, "2028-01-31", True, "Limited post-end-of-support coverage for KS-7000 systems through 2028-01-31, offered with bulletin PLB-2026-014"),
]
HW_LIST = {p[0]: p[5] for p in PRODUCTS if p[3] == "HARDWARE"}
FAMILY_OF = {p[0]: p[2] for p in PRODUCTS}
TIER_PCT = {"SUP-STD": 0.14, "SUP-PREM": 0.18, "SUP-MC": 0.24, "SUP-EXT7K": 0.12}


def build_products() -> pd.DataFrame:
    df = pd.DataFrame(PRODUCTS, columns=["PRODUCT_ID", "PRODUCT_NAME", "PRODUCT_FAMILY", "PRODUCT_LINE", "SUPPORT_TIER", "LIST_PRICE", "UNIT_OF_MEASURE",
                                         "GENERAL_AVAILABILITY_DATE", "END_OF_SALE_DATE", "END_OF_SUPPORT_DATE", "IS_RECURRING", "DESCRIPTION"])
    for c in ("GENERAL_AVAILABILITY_DATE", "END_OF_SALE_DATE", "END_OF_SUPPORT_DATE"):
        df[c] = df[c].map(lambda s: _d(s) if s else None)
    return df


# ---------------------------------------------------------------------------
# INSTALLED_SYSTEMS
# ---------------------------------------------------------------------------
WORKLOADS = ["Virtualization", "Databases", "File Services", "Backup Target", "Analytics", "EHR"]
FW_BY_DATE = [  # (available from, version)
    (date(2020, 1, 1), "KeelOS 9.11.4"), (date(2023, 6, 1), "KeelOS 9.12.1"), (date(2024, 4, 1), "KeelOS 9.13.0"),
    (date(2025, 3, 1), "KeelOS 9.13.2"), (date(2026, 3, 1), "KeelOS 9.14.1"), (BAD_FW_RELEASE, BAD_FW), (FIX_FW_RELEASE, FIX_FW),
]


def _fw_at(d: date) -> str:
    v = FW_BY_DATE[0][1]
    for start, ver in FW_BY_DATE:
        if d >= start:
            v = ver
    return v


def _pick_model(g, install: date, region: str) -> str:
    if install < date(2024, 5, 1):
        fam_w = {"KS-7000": 0.45, "KS-5000": 0.25, "HD-3000": 0.22, "KS-9000": 0.08}
    elif install <= KS7_END_OF_SALE:
        fam_w = {"KS-7000": 0.30, "KS-5000": 0.25, "HD-3000": 0.15, "KS-9000": 0.30}
    else:
        fam_w = {"KS-7000": 0.0, "KS-5000": 0.35, "HD-3000": 0.15, "KS-9000": 0.50}
    if region == HERO_REGION and install <= KS7_END_OF_SALE:
        fam_w["KS-7000"] *= 1.45  # Americas East was the KS-7000 launch market
    fams = list(fam_w)
    w = np.array([fam_w[f] for f in fams])
    w = w / w.sum()
    fam = fams[int(g.choice(len(fams), p=w))]
    models = [p for p, f in FAMILY_OF.items() if f == fam and p in HW_LIST]
    return models[int(g.integers(len(models)))]


def build_installed_systems(customers: pd.DataFrame) -> pd.DataFrame:
    g = rng("systems")
    rows = []
    n = 0
    for c in customers.itertuples(index=False):
        if c.SEGMENT == "ENTERPRISE":
            k = int(g.integers(6, 18))
        elif c.SEGMENT == "PUBLIC_SECTOR":
            k = int(g.integers(3, 9))
        else:
            k = int(g.integers(1, 5))
        if c.CUSTOMER_ID in ("CUST-0001", "CUST-0002", "CUST-0004", "CUST-0008"):
            k = int(g.integers(14, 22))
        for _ in range(k):
            # install year weights: growing fleet
            yr = int(g.choice([2020, 2021, 2022, 2023, 2024, 2025, 2026], p=[0.04, 0.07, 0.10, 0.14, 0.18, 0.27, 0.20]))
            lo = date(yr, 1, 1) if yr > 2020 else date(2020, 6, 1)
            hi = date(yr, 12, 31) if yr < 2026 else date(2026, 10, 5)
            install = _rdate(g, lo, hi)
            model = _pick_model(g, install, c.REGION)
            fam = FAMILY_OF[model]
            cap = {"KS-5000": (60, 400), "KS-7000": (120, 900), "KS-9000": (200, 1600), "HD-3000": (150, 1200)}[fam]
            raw_tb = float(np.round(g.uniform(*cap) / 10) * 10)
            n += 1
            prefix = {"KS-5000": "KS5", "KS-7000": "KS7", "KS-9000": "KS9", "HD-3000": "HD3"}[fam]
            sid = f"{prefix}-{install.year}-{n:05d}"
            status, decom = "ACTIVE", None
            if install < date(2022, 1, 1) and g.random() < 0.10:
                status = "DECOMMISSIONED"
                decom = _rdate(g, max(install + timedelta(days=1200), START), AS_OF - timedelta(days=30))
            rows.append({
                "SYSTEM_ID": sid, "CUSTOMER_ID": c.CUSTOMER_ID, "PRODUCT_ID": model, "PARTNER_ID": c.PARTNER_ID, "ORDER_LINE_ID": None,
                "INSTALL_DATE": install, "SITE_CITY": REGION_CITIES[c.REGION][int(g.integers(len(REGION_CITIES[c.REGION])))], "SITE_COUNTRY": c.COUNTRY,
                "RAW_CAPACITY_TB": raw_tb, "WORKLOAD_TYPE": WORKLOADS[int(g.choice(len(WORKLOADS), p=[0.30, 0.22, 0.18, 0.14, 0.10, 0.06]))],
                "CURRENT_FIRMWARE": None, "SYSTEM_STATUS": status, "DECOMMISSION_DATE": decom,
                "X_REGION": c.REGION, "X_UPG_914_2": None, "X_UPG_914_3": None,
            })
    df = pd.DataFrame(rows)
    # Firmware story: Americas East got the KeelOS 9.14.2 upgrade wave in Jul-Aug 2026;
    # other regions started in September. 9.14.3 (the fix) from mid-September.
    g2 = rng("firmware")
    upg2, upg3, cur = [], [], []
    for r in df.itertuples(index=False):
        u2 = u3 = None
        if r.SYSTEM_STATUS == "ACTIVE":
            if r.X_REGION == HERO_REGION:
                if g2.random() < 0.72:
                    u2 = _rdate(g2, date(2026, 7, 6), date(2026, 8, 28))
                    if g2.random() < 0.25:
                        u3 = _rdate(g2, FIX_FW_RELEASE, AS_OF)
            else:
                if g2.random() < 0.22:
                    u2 = _rdate(g2, date(2026, 9, 1), date(2026, 10, 5))
                elif g2.random() < 0.08:
                    u3 = _rdate(g2, FIX_FW_RELEASE, AS_OF)
        if u2 and r.INSTALL_DATE > u2:
            u2 = None
        if u3 and r.INSTALL_DATE > u3:
            u3 = None
        if u3:
            fw = FIX_FW
        elif u2:
            fw = BAD_FW
        else:
            fw = _fw_at(min(r.INSTALL_DATE, date(2026, 6, 30))) if r.INSTALL_DATE < BAD_FW_RELEASE else "KeelOS 9.14.1"
            if r.INSTALL_DATE >= FIX_FW_RELEASE:
                fw = FIX_FW
        upg2.append(u2)
        upg3.append(u3)
        cur.append(fw)
    df["X_UPG_914_2"] = upg2
    df["X_UPG_914_3"] = upg3
    df["CURRENT_FIRMWARE"] = cur
    return df


def firmware_on(sys_row, d: date) -> str:
    """Firmware a system ran on date d (uses the X_ helper columns)."""
    if sys_row.X_UPG_914_3 is not None and d >= sys_row.X_UPG_914_3:
        return FIX_FW
    if sys_row.X_UPG_914_2 is not None and d >= sys_row.X_UPG_914_2:
        return BAD_FW
    base = _fw_at(min(sys_row.INSTALL_DATE, date(2026, 6, 30)))
    if sys_row.INSTALL_DATE >= FIX_FW_RELEASE:
        return FIX_FW
    if sys_row.INSTALL_DATE >= BAD_FW_RELEASE:
        return "KeelOS 9.14.1"
    return base


# ---------------------------------------------------------------------------
# SUPPORT CASES (built before contracts so renewal outcomes can react to P1s)
# ---------------------------------------------------------------------------
CASE_CATEGORIES = {
    "HARDWARE": [("Hardware", "Drive failure"), ("Hardware", "Controller fault"), ("Hardware", "Power supply"), ("Performance", "Latency"),
                 ("Capacity", "Volume full"), ("Configuration", "Replication setup"), ("Firmware", "Upgrade"), ("Configuration", "Host connectivity")],
    "CLOUD": [("Cloud", "Volume provisioning"), ("Cloud", "Performance tier"), ("Cloud", "Billing question"), ("Cloud", "Replication to cloud")],
    "SOFTWARE": [("Licensing", "License key"), ("Configuration", "Insight onboarding"), ("Performance", "Backup window")],
}
NOTE_OPEN = [
    "Customer reports {sym} on {sysref}. Engineer {eng} engaged via phone and collected AutoPulse bundle.",
    "Case opened by {contact} ({cust}). Symptom: {sym} on {sysref}. Initial triage by {eng}.",
    "{contact} from {cust} called in: {sym}. {eng} picked up the case and reviewed recent AutoPulse alerts for {sysref}.",
]
SYMPTOMS = {
    "Drive failure": "a failed SSD in shelf 1 with a second drive showing predictive failure",
    "Controller fault": "controller B rebooted unexpectedly and the node is running degraded",
    "Power supply": "a PSU fault LED and a redundancy warning",
    "Latency": "read latency above 5 ms during the morning batch window",
    "Volume full": "an aggregate at 96 percent with snapshot reserve exhausted",
    "Replication setup": "SnapMirror style replication relationship failing to initialise",
    "Upgrade": "questions about the recommended upgrade path and maintenance window",
    "Host connectivity": "intermittent path loss on two VMware hosts after a switch change",
    "Volume provisioning": "a cloud volume stuck in creating state for over an hour",
    "Performance tier": "throughput lower than the selected performance tier",
    "Billing question": "a consumption invoice that does not match the portal usage report",
    "Replication to cloud": "replication to Keelstone Cloud Volumes falling behind its schedule",
    "License key": "a KeelOS add-on license showing as expired in the console",
    "Insight onboarding": "systems not appearing in the Keelstone Insight console",
    "Backup window": "backup jobs overrunning their window since the last change",
}
NOTE_ACTION = [
    "Replaced the component under contract and confirmed the system is back to a healthy state. Customer confirmed.",
    "Walked the customer through the fix on a screen share. Verified with a follow-up AutoPulse snapshot.",
    "Applied the recommended configuration change and monitored for 24 hours with no recurrence.",
    "Dispatched a field engineer; parts arrived within SLA. Post-replacement health check passed.",
    "Provided the KB article and a maintenance plan. Customer will schedule the change in their next window.",
]
NOTE_CLOSE = [
    "Customer satisfied with the resolution. Closing.",
    "No further action. Case closed with customer agreement.",
    "Closing per customer confirmation; recommended a proactive health check at the next quarterly review.",
    "Customer thanked the team for the quick turnaround. Closed.",
]
HERO_OPEN = [
    "P1 raised by {contact} ({cust}): production down on {sysref} after the KeelOS 9.14.2 upgrade. Controller A failed over to B during the post-upgrade giveback and both nodes went into a takeover loop. All volumes offline for the VMware cluster.",
    "{cust} escalated a P1: {sysref} lost access to all LUNs roughly 40 minutes after completing the 9.14.2 upgrade. Symptoms match a controller failover storm. {eng} engaged the backline team immediately.",
    "Production outage at {cust}. {sysref} entered repeated controller failover after the AutoPulse managed upgrade to 9.14.2 completed. Database tier unavailable. Executive bridge opened with {contact}.",
]
HERO_ACTION = [
    "Backline identified the issue as the 9.14.2 giveback timing defect (KB-2026-0917). Applied the interim workaround (disabled auto-giveback, manual giveback after cache flush) and stabilised the system after {hrs} hours.",
    "Engineering confirmed defect KB-2026-0917 in 9.14.2. Workaround applied and the cluster stabilised at hour {hrs}. Customer asked why the upgrade was pushed before the fix was available.",
    "Root cause: 9.14.2 defect KB-2026-0917 affecting takeover and giveback on KS-7000 and KS-9000 controllers. Workaround applied at hour {hrs}; permanent fix is 9.14.3 (released 2026-09-15).",
]
HERO_SENTIMENT = [
    "{contact} stated that leadership is 'reconsidering the January support renewal' and asked for a written RCA before any further upgrades.",
    "Customer sentiment is poor. {contact} mentioned they are already in conversations with another vendor about replacing the KS-7000 estate rather than renewing support.",
    "Customer frustrated: second outage this quarter on an end-of-support platform. {contact} asked for the extended support pricing and a migration quote to KS-9000.",
    "Account team notified. Customer wants a credit against the support renewal and a commitment that no further upgrades are pushed without approval.",
    "Customer calm but firm: they expect a migration plan for the KS-7000 systems before the renewal conversation. CSM to follow up within the week.",
]
HERO_CLOSE = [
    "Upgraded to 9.14.3 and verified takeover and giveback under load. RCA document delivered. Closing with customer agreement; account team owns the renewal follow-up.",
    "System stable on the workaround for 14 days; 9.14.3 scheduled. Closing the P1; a P3 tracks the upgrade. Renewal risk noted in Salesforce.",
]
CONTACTS = ["J. Alvarez (Storage Lead)", "M. Chen (Infrastructure Manager)", "R. Patel (VP Infrastructure)", "S. Okoro (Systems Engineer)",
            "L. Berg (IT Director)", "T. Nguyen (Platform Lead)", "K. Fischer (Data Center Manager)", "A. Romano (CIO office)"]
ENGINEERS = ["D. Kowalski", "P. Iyer", "H. Sorensen", "N. Okafor", "E. Vargas", "Y. Tanaka", "C. Dubois", "M. Hartley"]


def build_support_cases(customers: pd.DataFrame, systems: pd.DataFrame, cloud_customers: set, has_subscription: set) -> pd.DataFrame:
    g = rng("cases")
    cust = customers.set_index("CUSTOMER_ID")
    rows = []
    n = 0
    months = [START + timedelta(days=0)]
    while _add_months(months[-1], 1) <= AS_OF:
        months.append(_add_months(months[-1], 1))

    def mk_id():
        nonlocal n
        n += 1
        return f"CS{400000 + n:07d}"

    def generic_case(cid, sid, pid, opened, cat, sub, fw, prio_p=(0.03, 0.15, 0.52, 0.30)):
        prio = ["P1", "P2", "P3", "P4"][int(g.choice(4, p=prio_p))]
        c = cust.loc[cid]
        contact = CONTACTS[int(g.integers(len(CONTACTS)))]
        eng = ENGINEERS[int(g.integers(len(ENGINEERS)))]
        sysref = sid if sid else pid
        notes = [NOTE_OPEN[int(g.integers(len(NOTE_OPEN)))].format(sym=SYMPTOMS[sub], sysref=sysref, eng=eng, contact=contact, cust=c.CUSTOMER_NAME)]
        hrs_target = {"P1": (4, 36), "P2": (8, 72), "P3": (24, 240), "P4": (24, 400)}[prio]
        hrs = float(np.round(g.uniform(*hrs_target), 1))
        closed = opened + timedelta(days=int(np.ceil(hrs / 24)))
        if closed > AS_OF:
            status, closed, hrs_out, csat, rc = "OPEN", None, None, None, None
            notes.append(f"{eng}: investigation in progress; next update scheduled.")
        else:
            status, hrs_out = "CLOSED", hrs
            notes.append(NOTE_ACTION[int(g.integers(len(NOTE_ACTION)))])
            notes.append(NOTE_CLOSE[int(g.integers(len(NOTE_CLOSE)))])
            csat = int(g.choice([3, 4, 5], p=[0.15, 0.40, 0.45])) if g.random() < 0.6 else None
            rc = {"Drive failure": "Media wear-out", "Controller fault": "Transient controller panic", "Power supply": "PSU component failure",
                  "Latency": "Workload contention", "Volume full": "Snapshot retention policy", "Replication setup": "Configuration error",
                  "Upgrade": "Guidance provided", "Host connectivity": "Switch zoning change", "Volume provisioning": "Cloud API throttling",
                  "Performance tier": "Tier misconfiguration", "Billing question": "Usage report timing", "Replication to cloud": "Bandwidth limit",
                  "License key": "License not applied", "Insight onboarding": "Firewall rule", "Backup window": "Job scheduling"}.get(sub)
        rows.append({
            "CASE_ID": mk_id(), "CUSTOMER_ID": cid, "SYSTEM_ID": sid, "PRODUCT_ID": pid, "OPENED_DATE": opened, "CLOSED_DATE": closed,
            "PRIORITY": prio, "CASE_STATUS": status, "CATEGORY": cat, "SUBCATEGORY": sub, "FIRMWARE_VERSION": fw, "ROOT_CAUSE": rc,
            "RESOLUTION_HOURS": hrs_out, "CSAT_SCORE": csat, "CASE_NOTES": " ".join(notes), "SOURCE_SYSTEM": "ServiceNow",
        })

    # 1. background hardware cases: ~0.055 per active system-month
    active = systems[systems.SYSTEM_STATUS == "ACTIVE"]
    for s in active.itertuples(index=False):
        for m in months:
            if m < _month_start(s.INSTALL_DATE):
                continue
            if g.random() < 0.12:
                opened = _rdate(g, max(m, s.INSTALL_DATE), min(_month_end(m), AS_OF))
                cat, sub = CASE_CATEGORIES["HARDWARE"][int(g.integers(len(CASE_CATEGORIES["HARDWARE"])))]
                generic_case(s.CUSTOMER_ID, s.SYSTEM_ID, s.PRODUCT_ID, opened, cat, sub, firmware_on(s, opened))
    # 2. cloud and software cases per customer-month
    for c in customers.itertuples(index=False):
        for m in months:
            if c.CUSTOMER_ID in cloud_customers and g.random() < 0.15:
                opened = _rdate(g, m, min(_month_end(m), AS_OF))
                cat, sub = CASE_CATEGORIES["CLOUD"][int(g.integers(len(CASE_CATEGORIES["CLOUD"])))]
                pid = cloud_customers[c.CUSTOMER_ID]
                generic_case(c.CUSTOMER_ID, None, pid, opened, cat, sub, None, prio_p=(0.02, 0.12, 0.50, 0.36))
            if c.CUSTOMER_ID in has_subscription and g.random() < 0.08:
                opened = _rdate(g, m, min(_month_end(m), AS_OF))
                cat, sub = CASE_CATEGORIES["SOFTWARE"][int(g.integers(len(CASE_CATEGORIES["SOFTWARE"])))]
                generic_case(c.CUSTOMER_ID, None, "KOS-CORE", opened, cat, sub, None, prio_p=(0.01, 0.09, 0.50, 0.40))
    # 3. STORY (CP1): P1 controller failover cases after the 9.14.2 upgrade.
    #    Americas East systems upgraded Jul-Aug 2026 -> 13% raise a P1 within 30 days.
    #    Other regions upgraded from September -> 4%.
    gh = rng("hero_cases")
    hero_systems = []
    for s in active.itertuples(index=False):
        if s.X_UPG_914_2 is None:
            continue
        p = 0.13 if s.X_REGION == HERO_REGION else 0.04
        if FAMILY_OF[s.PRODUCT_ID] == "HD-3000":
            p *= 0.3
        if gh.random() < p:
            hero_systems.append(s)
    g = gh  # every draw below comes from the hero stream so both passes agree
    for s in hero_systems:
        opened = s.X_UPG_914_2 + timedelta(days=int(g.integers(0, 31)))
        if opened > AS_OF:
            opened = AS_OF - timedelta(days=int(g.integers(0, 5)))
        c = cust.loc[s.CUSTOMER_ID]
        contact = CONTACTS[int(g.integers(len(CONTACTS)))]
        eng = ENGINEERS[int(g.integers(len(ENGINEERS)))]
        hrs = float(np.round(g.uniform(6, 30), 1))
        fmt = dict(contact=contact, cust=c.CUSTOMER_NAME, sysref=s.SYSTEM_ID, eng=eng, hrs=int(hrs))
        notes = [HERO_OPEN[int(g.integers(len(HERO_OPEN)))].format(**fmt), HERO_ACTION[int(g.integers(len(HERO_ACTION)))].format(**fmt)]
        if s.X_REGION == HERO_REGION and g.random() < 0.7:
            notes.append(HERO_SENTIMENT[int(g.integers(len(HERO_SENTIMENT)))].format(**fmt))
        total_hrs = hrs + float(g.uniform(48, 400))  # P1 stays open for RCA and follow-up
        closed = opened + timedelta(days=int(np.ceil(total_hrs / 24)))
        if closed > AS_OF or (opened >= date(2026, 8, 20) and g.random() < 0.45):  # recent ones wait on 9.14.3 and the RCA
            status, closed, hrs_out, csat = "OPEN", None, None, None
            notes.append("Case remains open pending the 9.14.3 upgrade and the written RCA.")
        else:
            status, hrs_out = "CLOSED", float(np.round(total_hrs, 1))
            notes.append(HERO_CLOSE[int(g.integers(len(HERO_CLOSE)))])
            csat = int(g.choice([1, 2, 3], p=[0.25, 0.45, 0.30]))
        rows.append({
            "CASE_ID": mk_id(), "CUSTOMER_ID": s.CUSTOMER_ID, "SYSTEM_ID": s.SYSTEM_ID, "PRODUCT_ID": s.PRODUCT_ID, "OPENED_DATE": opened, "CLOSED_DATE": closed,
            "PRIORITY": "P1", "CASE_STATUS": status, "CATEGORY": "Firmware", "SUBCATEGORY": "Controller failover", "FIRMWARE_VERSION": BAD_FW,
            "ROOT_CAUSE": "KeelOS 9.14.2 defect KB-2026-0917", "RESOLUTION_HOURS": hrs_out, "CSAT_SCORE": csat,
            "CASE_NOTES": " ".join(notes), "SOURCE_SYSTEM": "ServiceNow",
        })
        # a P2 follow-up on about half of them
        if g.random() < 0.5:
            o2 = opened + timedelta(days=int(g.integers(2, 12)))
            if o2 <= AS_OF:
                rows.append({
                    "CASE_ID": mk_id(), "CUSTOMER_ID": s.CUSTOMER_ID, "SYSTEM_ID": s.SYSTEM_ID, "PRODUCT_ID": s.PRODUCT_ID, "OPENED_DATE": o2,
                    "CLOSED_DATE": None if o2 + timedelta(days=6) > AS_OF else o2 + timedelta(days=6),
                    "PRIORITY": "P2", "CASE_STATUS": "OPEN" if o2 + timedelta(days=6) > AS_OF else "CLOSED", "CATEGORY": "Firmware",
                    "SUBCATEGORY": "Takeover delay", "FIRMWARE_VERSION": BAD_FW, "ROOT_CAUSE": "KeelOS 9.14.2 defect KB-2026-0917",
                    "RESOLUTION_HOURS": None if o2 + timedelta(days=6) > AS_OF else 144.0, "CSAT_SCORE": None,
                    "CASE_NOTES": f"Follow-up to the 9.14.2 failover P1 on {s.SYSTEM_ID}: takeover now completes but giveback is slow (over 8 minutes) with the interim workaround in place. {eng} tracking until 9.14.3 is applied. Customer ({c.CUSTOMER_NAME}) asked for weekly status until closure.",
                    "SOURCE_SYSTEM": "ServiceNow",
                })
    df = pd.DataFrame(rows).sort_values("OPENED_DATE", kind="stable").reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# CONTRACTS (support, subscriptions, cloud commits)
# ---------------------------------------------------------------------------
class _ContractBook:
    def __init__(self):
        self.rows = []
        self.n = 0

    def new_id(self):
        self.n += 1
        return f"CTR-{self.n:07d}"


_GROUP_STATE: dict = {}
# (hero region?, period, category) -> (renew share, churn share); the rest is pending
_OUTCOME_TABLE = {
    (True, "FY27", "EOS"): (0.63, 0.27), (True, "FY27", "P1"): (0.76, 0.16), (True, "FY27", "SUP"): (0.88, 0.09), (True, "FY27", "OTH"): (0.86, 0.10),
    (False, "FY27", "EOS"): (0.84, 0.12), (False, "FY27", "P1"): (0.84, 0.12), (False, "FY27", "SUP"): (0.875, 0.10), (False, "FY27", "OTH"): (0.875, 0.10),
}


def _outcome(g, region: str, end: date, kind: str, family: str, p1_hit: bool, value: float):
    """(status, outcome_date) for a contract that ended on `end` (<= AS_OF).

    Outcomes are assigned so that each (region, period, category) group tracks its
    target renewed share of ARR as contracts stream through (a dollar-weighted
    low-discrepancy draw), which keeps the story stable instead of hostage to a few
    large contracts. Not-renewed contracts are Closed Lost by renewals ops 90-365 days
    after the lapse; until then they are PENDING_RENEWAL (the Sales Ops ARR gap)."""
    if end < START:  # history: clean
        return ("RENEWED", end) if g.random() < 0.91 else ("CHURNED", end + timedelta(days=int(g.integers(90, 366))))
    period = "FY27" if end >= FY27_START else "PRE"
    if family == EOS_FAMILY and end >= FY27_START:   # KS-7000 left the price list 2025-10-31; EOS bulletin 2026-06-15
        cat = "EOS"
    elif p1_hit and end >= date(2026, 7, 15):
        cat = "P1"
    elif kind == "SUPPORT":
        cat = "SUP"
    else:
        cat = "OTH"
    if period == "PRE":
        renew, churn = 0.905, 0.075
    else:
        renew, churn = _OUTCOME_TABLE[(region == HERO_REGION, period, cat)]
    st = _GROUP_STATE.setdefault((region, period, cat, kind, family), [0.0, 0.0])  # [due, renewed]; per kind and family so each slice tracks its target
    due, ren = st
    target = renew + g.uniform(-0.01, 0.01)
    renewed = ren <= target * (due + value)  # renew while the group's renewed share is at or below target
    st[0] += value
    if renewed:
        st[1] += value
        return "RENEWED", end
    if g.random() < churn / max(1e-9, 1 - renew):
        close = end + timedelta(days=int(g.integers(90, 366)))
    else:
        close = end + timedelta(days=365)
    if close <= AS_OF:
        return "CHURNED", close
    return "PENDING_RENEWAL", None


def _chain(book: _ContractBook, g, *, customer, product, system_id, partner, rep, kind, first_start: date, annual: float,
           term_p=(0.85, 0.10, 0.05), region: str, family: str, p1_hit: bool, stop_at: date | None = None):
    """Create a chain of contracts starting at first_start; returns list of row dicts appended."""
    start = first_start
    prev = None
    out = []
    while True:
        term = [12, 24, 36][int(g.choice(3, p=term_p))]
        end = _add_months(start, term)
        cid = book.new_id()
        if stop_at is not None and end > stop_at:
            end = stop_at  # decommissioned mid-term: contract ends with the system
        row = {
            "CONTRACT_ID": cid, "CUSTOMER_ID": customer, "PRODUCT_ID": product, "SYSTEM_ID": system_id, "PARTNER_ID": partner, "REP_ID": rep,
            "ORDER_LINE_ID": None, "CONTRACT_TYPE": kind, "START_DATE": start, "END_DATE": end, "TERM_MONTHS": term,
            "ANNUAL_VALUE": round(annual, 2), "TOTAL_CONTRACT_VALUE": round(annual * term / 12, 2),
            "CONTRACT_STATUS": "ACTIVE", "OUTCOME_DATE": None, "SUCCESSOR_CONTRACT_ID": None, "PREDECESSOR_CONTRACT_ID": prev, "SOURCE_SYSTEM": "SAP S/4HANA",
            "X_REGION": region, "X_FAMILY": family,
        }
        out.append(row)
        if end > AS_OF:
            break
        if stop_at is not None and end >= stop_at:
            row["CONTRACT_STATUS"], row["OUTCOME_DATE"] = "CHURNED", end
            break
        status, odate = _outcome(g, region, end, kind, family, p1_hit, annual)
        row["CONTRACT_STATUS"], row["OUTCOME_DATE"] = status, odate
        if status != "RENEWED":
            break
        # successor
        annual = annual * (1 + g.uniform(0.02, 0.07))
        prev = cid
        start = end
    for i in range(len(out) - 1):
        out[i]["SUCCESSOR_CONTRACT_ID"] = out[i + 1]["CONTRACT_ID"]
    book.rows.extend(out)
    return out


def build_contracts(customers: pd.DataFrame, systems: pd.DataFrame, reps: pd.DataFrame, cases: pd.DataFrame):
    g = rng("contracts")
    _GROUP_STATE.clear()
    book = _ContractBook()
    cust = customers.set_index("CUSTOMER_ID")
    renewals = {r: reps[(reps.REGION == r) & (reps.REP_ROLE == "Renewals Specialist")].REP_ID.tolist() for r in REGIONS}
    cloud_reps = {r: reps[(reps.REGION == r) & (reps.REP_ROLE == "Cloud Specialist")].REP_ID.tolist() for r in REGIONS}
    p1_customers = set(cases[(cases.PRIORITY == "P1") & (cases.FIRMWARE_VERSION == BAD_FW)].CUSTOMER_ID)

    # ---- support contracts per system (CP4: Altura attach falls in FY27)
    # Attach is decided per (partner, fiscal year of install) so each partner lands on its
    # target rate exactly: Altura 78% in FY26 -> 62% in FY27, direct 88%, other partners 76%.
    g_att = rng("attach")
    attached = set()
    groups = {}
    for s in systems.itertuples(index=False):
        groups.setdefault((s.PARTNER_ID, fiscal_year(s.INSTALL_DATE)), []).append(s.SYSTEM_ID)
    for (pid, fy), ids in groups.items():
        if pid == HERO_PARTNER:
            rate = 0.62 if fy >= "FY27" else 0.78
        elif pid == "PTR-000":
            rate = 0.88
        else:
            rate = 0.76
        k = int(round(len(ids) * rate))
        pick = g_att.choice(len(ids), size=k, replace=False) if k else []
        attached.update(ids[i] for i in pick)
    for s in systems.itertuples(index=False):
        c = cust.loc[s.CUSTOMER_ID]
        # KeelOS Core is licensed per array: one subscription chain per system
        core_start = s.INSTALL_DATE + timedelta(days=int(g.integers(0, 31)))
        stop = s.DECOMMISSION_DATE if s.SYSTEM_STATUS == "DECOMMISSIONED" else None
        _chain(book, g, customer=s.CUSTOMER_ID, product="KOS-CORE", system_id=s.SYSTEM_ID, partner=s.PARTNER_ID, rep=c.REP_ID, kind="SOFTWARE_SUBSCRIPTION",
               first_start=core_start, annual=(min(float(s.RAW_CAPACITY_TB), 400.0) * 480 + max(float(s.RAW_CAPACITY_TB) - 400.0, 0.0) * 240) * (1 - g.uniform(0.15, 0.40)), term_p=(0.80, 0.12, 0.08),
               region=c.REGION, family=FAMILY_OF[s.PRODUCT_ID], p1_hit=s.CUSTOMER_ID in p1_customers, stop_at=stop)
        if s.SYSTEM_ID not in attached:
            continue
        tier = {"ENTERPRISE": ["SUP-PREM", "SUP-MC", "SUP-STD"], "PUBLIC_SECTOR": ["SUP-STD", "SUP-PREM", "SUP-MC"], "COMMERCIAL": ["SUP-STD", "SUP-PREM", "SUP-MC"]}[c.SEGMENT]
        tier_p = {"ENTERPRISE": [0.50, 0.30, 0.20], "PUBLIC_SECTOR": [0.55, 0.35, 0.10], "COMMERCIAL": [0.65, 0.30, 0.05]}[c.SEGMENT]
        product = tier[int(g.choice(3, p=tier_p))]
        annual = HW_LIST[s.PRODUCT_ID] * TIER_PCT[product] * (1 - g.uniform(0.05, 0.22))
        first_start = s.INSTALL_DATE + timedelta(days=int(g.integers(0, 21)))
        rep = renewals[c.REGION][int(g.integers(len(renewals[c.REGION])))]
        stop = s.DECOMMISSION_DATE if s.SYSTEM_STATUS == "DECOMMISSIONED" else None
        _chain(book, g, customer=s.CUSTOMER_ID, product=product, system_id=s.SYSTEM_ID, partner=s.PARTNER_ID, rep=rep, kind="SUPPORT",
               first_start=first_start, annual=annual, region=c.REGION, family=FAMILY_OF[s.PRODUCT_ID],
               p1_hit=s.CUSTOMER_ID in p1_customers, stop_at=stop)

    # ---- software subscriptions per customer
    tb_by_cust = systems[systems.SYSTEM_STATUS == "ACTIVE"].groupby("CUSTOMER_ID").RAW_CAPACITY_TB.sum()
    first_install = systems.groupby("CUSTOMER_ID").INSTALL_DATE.min()
    has_sub = set()
    for c in customers.itertuples(index=False):
        tb = float(tb_by_cust.get(c.CUSTOMER_ID, 0))
        if tb <= 0:
            continue
        has_sub.add(c.CUSTOMER_ID)
        tb = min(tb, 1200.0)  # add-ons are priced on a capped footprint
        base_start = first_install[c.CUSTOMER_ID] + timedelta(days=int(g.integers(0, 45)))
        if base_start < date(2021, 1, 1):
            base_start = _rdate(g, date(2021, 1, 1), date(2021, 12, 31))
        rep = c.REP_ID
        disc = 1 - g.uniform(0.15, 0.40)
        for pid, prob, rate in (("KOS-ADS", 0.5, 160), ("KOS-SHIELD", 0.35, 120), ("KOS-BACKUP", 0.25, 90)):
            if g.random() < prob:
                st = _rdate(g, max(base_start, date(2023, 3, 1) if pid == "KOS-SHIELD" else base_start), date(2026, 3, 31))
                _chain(book, g, customer=c.CUSTOMER_ID, product=pid, system_id=None, partner=c.PARTNER_ID, rep=rep, kind="SOFTWARE_SUBSCRIPTION",
                       first_start=st, annual=tb * rate * disc, term_p=(0.85, 0.10, 0.05), region=c.REGION, family="KeelOS", p1_hit=c.CUSTOMER_ID in p1_customers)
        if g.random() < 0.4:
            st = _rdate(g, max(base_start, date(2022, 6, 1)), date(2026, 3, 31))
            _chain(book, g, customer=c.CUSTOMER_ID, product="KOS-INSIGHT", system_id=None, partner=c.PARTNER_ID, rep=rep, kind="SOFTWARE_SUBSCRIPTION",
                   first_start=st, annual=45000 * (1 - g.uniform(0.0, 0.3)), term_p=(0.8, 0.1, 0.1), region=c.REGION, family="KeelOS", p1_hit=False)

    # ---- cloud commits (CP3)
    cloud = {}
    under = set()
    ent_cloud = []
    for c in customers.itertuples(index=False):
        p = {"ENTERPRISE": 0.62, "COMMERCIAL": 0.30, "PUBLIC_SECTOR": 0.22}[c.SEGMENT]
        if g.random() >= p:
            continue
        pid = ["KCV-AZURE", "KCV-AWS", "KCV-GCP", "KOS-OBJECT"][int(g.choice(4, p=[0.50, 0.30, 0.12, 0.08]))]
        if pid == "KCV-GCP":
            lo = date(2024, 1, 1)
        elif pid == "KOS-OBJECT":
            lo = date(2024, 6, 1)
        elif pid == "KCV-AWS":
            lo = date(2023, 2, 1)
        else:
            lo = date(2022, 9, 1)
        # 40% of cloud customers started in FY26 or later (drives YoY growth)
        st = _rdate(g, date(2025, 5, 1), date(2026, 7, 31)) if g.random() < 0.40 else _rdate(g, lo, date(2025, 4, 30))
        annual = {"ENTERPRISE": g.uniform(150000, 900000), "COMMERCIAL": g.uniform(60000, 300000), "PUBLIC_SECTOR": g.uniform(80000, 400000)}[c.SEGMENT]
        rep = cloud_reps[c.REGION][0]
        rows = _chain(book, g, customer=c.CUSTOMER_ID, product=pid, system_id=None, partner=c.PARTNER_ID, rep=rep, kind="CLOUD_COMMIT",
                      first_start=st, annual=annual, term_p=(0.90, 0.10, 0.0), region=c.REGION, family=FAMILY_OF[pid], p1_hit=False)
        cloud[c.CUSTOMER_ID] = pid
        if c.SEGMENT == "ENTERPRISE":
            ent_cloud.append(c.CUSTOMER_ID)
    # ~25 under-utilised enterprise accounts
    g_u = rng("cloud_under")
    pick = g_u.choice(len(ent_cloud), size=min(27, len(ent_cloud)), replace=False)
    under = {ent_cloud[i] for i in pick}

    df = pd.DataFrame(book.rows)
    return df, cloud, under, has_sub


# ---------------------------------------------------------------------------
# CLOUD_CONSUMPTION_MONTHLY
# ---------------------------------------------------------------------------
PROVIDER = {"KCV-AZURE": "Azure", "KCV-AWS": "AWS", "KCV-GCP": "GCP", "KOS-OBJECT": "AWS"}


def build_cloud_consumption(contracts: pd.DataFrame, under: set) -> pd.DataFrame:
    g = rng("cloud_usage")
    cc = contracts[contracts.CONTRACT_TYPE == "CLOUD_COMMIT"]
    rows = []
    months = []
    m = START
    while m <= date(2026, 9, 1):
        months.append(m)
        m = _add_months(m, 1)
    # per-customer utilisation profile
    profile = {}
    for cid in cc.CUSTOMER_ID.unique():
        if cid in under:
            profile[cid] = (g.uniform(0.30, 0.58), g.uniform(-0.002, 0.004))  # flat, low
        else:
            profile[cid] = (g.uniform(0.70, 1.10), g.uniform(0.010, 0.030))   # growing
    for m in months:
        inforce = cc[(cc.START_DATE <= m) & (cc.END_DATE > m)]
        for c in inforce.itertuples(index=False):
            base, slope = profile[c.CUSTOMER_ID]
            months_since_start = max(0, (m.year - START.year) * 12 + (m.month - START.month))
            util = base + slope * months_since_start + g.normal(0, 0.05)
            util = max(0.05, util)
            commit_m = c.ANNUAL_VALUE / 12
            consumed = commit_m * util
            price_per_tb = 55.0
            rows.append({
                "CONSUMPTION_ID": f"{c.CUSTOMER_ID}-{m.strftime('%Y%m')}", "CUSTOMER_ID": c.CUSTOMER_ID, "PRODUCT_ID": c.PRODUCT_ID, "CONTRACT_ID": c.CONTRACT_ID,
                "USAGE_MONTH": m, "CLOUD_PROVIDER": PROVIDER[c.PRODUCT_ID], "MONTHLY_COMMIT_AMOUNT": round(commit_m, 2),
                "CONSUMED_AMOUNT": round(consumed, 2), "CONSUMED_TB": round(consumed / price_per_tb, 2),
                "OVERAGE_AMOUNT": round(max(0.0, consumed - commit_m), 2),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# SYSTEM_TELEMETRY_MONTHLY
# ---------------------------------------------------------------------------
def build_telemetry(systems: pd.DataFrame, cases: pd.DataFrame) -> pd.DataFrame:
    g = rng("telemetry")
    p1_months = {}
    for r in cases[(cases.PRIORITY == "P1") & (cases.SYSTEM_ID.notna())].itertuples(index=False):
        p1_months.setdefault(r.SYSTEM_ID, set()).add(_month_start(r.OPENED_DATE))
    months = []
    m = START
    while m <= date(2026, 9, 1):
        months.append(m)
        m = _add_months(m, 1)
    rows = []
    for s in systems.itertuples(index=False):
        base_used = g.uniform(30, 62)
        base_lat = g.uniform(0.4, 1.6)
        for i, m in enumerate(months):
            if m < _month_start(s.INSTALL_DATE):
                continue
            if s.SYSTEM_STATUS == "DECOMMISSIONED" and s.DECOMMISSION_DATE is not None and m > s.DECOMMISSION_DATE:
                continue
            used = min(97.0, base_used + 0.9 * i + g.normal(0, 1.2))
            fw = firmware_on(s, _month_end(m))
            hit = m in p1_months.get(s.SYSTEM_ID, set())
            health = g.uniform(55, 70) if hit else g.uniform(84, 97)
            alerts = int(g.integers(2, 7)) if hit else int(g.choice([0, 0, 0, 0, 1, 1, 2], p=[0.55, 0.15, 0.1, 0.05, 0.08, 0.04, 0.03]))
            uptime = 99.2 + g.uniform(0, 0.3) if hit else 99.95 + g.uniform(0, 0.05)
            lat = base_lat * (2.2 if hit else 1.0) + g.normal(0, 0.08)
            rows.append({
                "TELEMETRY_ID": f"{s.SYSTEM_ID}-{m.strftime('%Y%m')}", "SYSTEM_ID": s.SYSTEM_ID, "SNAPSHOT_MONTH": m, "FIRMWARE_VERSION": fw,
                "CAPACITY_USED_PCT": round(used, 2), "HEALTH_SCORE": round(health, 1), "CRITICAL_ALERTS": alerts, "UPTIME_PCT": round(min(uptime, 100.0), 3),
                "AVG_LATENCY_MS": round(max(0.2, lat), 2), "SOURCE_SYSTEM": "AutoPulse",
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# RENEWAL_OPPORTUNITIES
# ---------------------------------------------------------------------------
RISK_REASONS = ["Budget", "Competitive", "Consolidation"]
COMPETITORS = ["Vaultline Storage", "Orbis Data", "Pellucid Systems", "Greyhaven Cloud"]


def build_renewal_opps(contracts: pd.DataFrame, customers: pd.DataFrame, cases: pd.DataFrame) -> pd.DataFrame:
    g = rng("opps")
    cust = customers.set_index("CUSTOMER_ID")
    p1_customers = set(cases[(cases.PRIORITY == "P1") & (cases.FIRMWARE_VERSION == BAD_FW)].CUSTOMER_ID)
    rows = []
    n = 0
    window_end = AS_OF + timedelta(days=180)
    for c in contracts.itertuples(index=False):
        if c.END_DATE < START or c.END_DATE > window_end:
            continue
        n += 1
        oid = "006" + f"{n:012d}" + "QAA"
        created = c.END_DATE - timedelta(days=120)
        uplift = 1 + g.uniform(0.02, 0.08)
        quote = round(c.ANNUAL_VALUE * uplift, 2)
        comp = None
        eos = c.X_FAMILY == EOS_FAMILY and c.END_DATE >= EOS_ANNOUNCED
        p1 = c.CUSTOMER_ID in p1_customers and c.END_DATE >= date(2026, 7, 15)
        if c.CONTRACT_STATUS == "RENEWED":
            stage, close, risk, reason = "Closed Won", c.OUTCOME_DATE, "ON_TRACK", None
            if g.random() < 0.12:
                risk, reason = "AT_RISK", RISK_REASONS[int(g.integers(3))]
        elif c.CONTRACT_STATUS == "CHURNED":
            stage, close, risk = "Closed Lost", c.OUTCOME_DATE, "AT_RISK"
            reason = "End of support product" if eos else ("Open P1 case" if p1 else RISK_REASONS[int(g.integers(3))])
            if reason == "Competitive" or (eos and g.random() < 0.5):
                comp = COMPETITORS[int(g.integers(len(COMPETITORS)))]
        elif c.CONTRACT_STATUS == "PENDING_RENEWAL":
            stage, close = ("Negotiation" if g.random() < 0.6 else "Quote Sent"), None
            risk = "AT_RISK" if (eos or p1 or g.random() < 0.5) else "ON_TRACK"
            reason = ("End of support product" if eos else "Open P1 case" if p1 else RISK_REASONS[int(g.integers(3))]) if risk == "AT_RISK" else None
        else:  # ACTIVE, ending in the future
            days = (c.END_DATE - AS_OF).days
            stage = "Qualification" if days > 90 else ("Quote Sent" if days > 45 else "Negotiation")
            close = None
            if eos:
                at = g.random() < 0.72
            elif p1:
                at = g.random() < 0.55
            else:
                at = g.random() < 0.07
            risk = "AT_RISK" if at else "ON_TRACK"
            reason = None
            if at:
                reason = "End of support product" if eos else ("Open P1 case" if p1 else RISK_REASONS[int(g.integers(3))])
                if reason == "Competitive" or (eos and g.random() < 0.35):
                    comp = COMPETITORS[int(g.integers(len(COMPETITORS)))]
        rows.append({
            "OPPORTUNITY_ID": oid, "CONTRACT_ID": c.CONTRACT_ID, "CUSTOMER_ID": c.CUSTOMER_ID, "REP_ID": c.REP_ID, "CREATED_DATE": created,
            "EXPECTED_CLOSE_DATE": c.END_DATE, "ACTUAL_CLOSE_DATE": close, "STAGE": stage, "QUOTE_AMOUNT": quote, "RISK_FLAG": risk,
            "RISK_REASON": reason, "COMPETITOR": comp, "SOURCE_SYSTEM": "Salesforce",
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# ORDERS (bookings derived from systems and contracts)
# ---------------------------------------------------------------------------
def build_orders(systems: pd.DataFrame, contracts: pd.DataFrame, customers: pd.DataFrame, products: pd.DataFrame):
    g = rng("orders")
    cust = customers.set_index("CUSTOMER_ID")
    price = products.set_index("PRODUCT_ID").LIST_PRICE.to_dict()
    lines = []
    sys_ol, ctr_ol = {}, {}
    n = 0

    def new_line():
        nonlocal n
        n += 1
        return f"OL-{n:08d}"

    for s in systems.itertuples(index=False):
        if s.INSTALL_DATE < date(2025, 6, 10):
            continue
        od = s.INSTALL_DATE - timedelta(days=int(g.integers(14, 46)))
        if od < START:
            continue
        lst = HW_LIST[s.PRODUCT_ID]
        disc = round(float(g.uniform(18, 42)), 2)
        ol = new_line()
        sys_ol[s.SYSTEM_ID] = ol
        lines.append({"ORDER_LINE_ID": ol, "ORDER_DATE": od, "CUSTOMER_ID": s.CUSTOMER_ID, "PRODUCT_ID": s.PRODUCT_ID, "PARTNER_ID": s.PARTNER_ID,
                      "REP_ID": cust.loc[s.CUSTOMER_ID].REP_ID, "BOOKING_TYPE": "EXPANSION" if g.random() < 0.7 else "NEW", "QUANTITY": 1.0,
                      "LIST_AMOUNT": float(lst), "DISCOUNT_PCT": disc, "NET_AMOUNT": round(lst * (1 - disc / 100), 2)})
    for c in contracts.itertuples(index=False):
        if c.START_DATE < START:
            continue
        od = c.START_DATE - timedelta(days=int(g.integers(0, 25)))
        if od < START:
            od = START
        if od > AS_OF:
            continue
        years = c.TERM_MONTHS / 12
        if c.CONTRACT_TYPE == "SUPPORT":
            qty = years
            lst = float(price[c.PRODUCT_ID]) * years
        elif c.CONTRACT_TYPE == "CLOUD_COMMIT":
            qty = c.ANNUAL_VALUE * years
            lst = c.TOTAL_CONTRACT_VALUE
        else:
            unit = float(price[c.PRODUCT_ID])
            qty = round(c.TOTAL_CONTRACT_VALUE / (unit * 0.72), 2)
            lst = round(qty * unit, 2)
        net = c.TOTAL_CONTRACT_VALUE
        lst = max(lst, net)
        disc = round(100 * (1 - net / lst), 2) if lst else 0.0
        ol = new_line()
        ctr_ol[c.CONTRACT_ID] = ol
        lines.append({"ORDER_LINE_ID": ol, "ORDER_DATE": od, "CUSTOMER_ID": c.CUSTOMER_ID, "PRODUCT_ID": c.PRODUCT_ID, "PARTNER_ID": c.PARTNER_ID,
                      "REP_ID": c.REP_ID, "BOOKING_TYPE": "RENEWAL" if c.PREDECESSOR_CONTRACT_ID else "NEW", "QUANTITY": round(float(qty), 2),
                      "LIST_AMOUNT": round(float(lst), 2), "DISCOUNT_PCT": disc, "NET_AMOUNT": round(float(net), 2)})
    df = pd.DataFrame(lines).sort_values(["ORDER_DATE", "CUSTOMER_ID", "ORDER_LINE_ID"], kind="stable").reset_index(drop=True)
    # group into orders per customer and date
    keys = {}
    order_ids, saps = [], []
    for r in df.itertuples(index=False):
        k = (r.CUSTOMER_ID, r.ORDER_DATE)
        if k not in keys:
            keys[k] = (f"ORD-{len(keys) + 1:07d}", f"{4500000000 + len(keys) + 1}")
        order_ids.append(keys[k][0])
        saps.append(keys[k][1])
    df.insert(1, "ORDER_ID", order_ids)
    df.insert(2, "SAP_SALES_ORDER", saps)
    df["SOURCE_SYSTEM"] = "SAP S/4HANA"
    return df, sys_ol, ctr_ol


# ---------------------------------------------------------------------------
# DATA DICTIONARY
# ---------------------------------------------------------------------------
DATA_DICTIONARY_ROWS = [
    ("V_ARR_MONTHLY", "ARR", "NUMBER", "Annual recurring revenue: sum of annual_value of contracts in force on the measurement date. Certified Finance definition (Metric Standard v3.2).", "412500000", "SUM(CONTRACTS.ANNUAL_VALUE) WHERE START_DATE <= date < END_DATE", "Finance - FP&A", "SAP S/4HANA"),
    ("V_ARR_FINANCE_VS_SALESOPS", "SALESOPS_ARR", "NUMBER", "Finance ARR plus lapsed contracts whose renewal opportunity is still open in Salesforce (opportunities are closed lost up to a year after the lapse). Not certified; shown to explain the gap.", "436000000", "FINANCE_ARR + LAPSED_OPEN_ARR", "Sales Operations", "SAP S/4HANA + Salesforce"),
    ("V_ARR_FINANCE_VS_SALESOPS", "GAP_PCT", "NUMBER", "Sales Ops ARR minus Finance ARR as a share of Finance ARR", "0.058", "LAPSED_OPEN_ARR / FINANCE_ARR", "Finance - FP&A", "Derived"),
    ("V_RENEWAL_PERFORMANCE", "RENEWAL_RATE", "NUMBER", "ARR renewed divided by ARR due in the period. A contract is renewed only when a successor contract is signed; pending renewals count as not yet renewed.", "0.84", "SUM(ARR_RENEWED) / SUM(ARR_DUE)", "Finance - FP&A", "SAP S/4HANA"),
    ("V_RENEWAL_PERFORMANCE", "ARR_PENDING", "NUMBER", "ARR of lapsed contracts whose renewal is still open", "6100000", "SUM(ANNUAL_VALUE) WHERE CONTRACT_STATUS = PENDING_RENEWAL", "Sales Operations", "SAP S/4HANA"),
    ("V_RENEWALS_AT_RISK_90D", "ANNUAL_VALUE", "NUMBER", "ARR of an active contract ending in the next 90 days", "184000", "CONTRACTS.ANNUAL_VALUE", "Sales Operations", "SAP S/4HANA"),
    ("V_RENEWALS_AT_RISK_90D", "RISK_FLAG", "VARCHAR", "AT_RISK or ON_TRACK as set by the renewals team on the Salesforce opportunity", "AT_RISK", None, "Sales Operations", "Salesforce"),
    ("V_RENEWALS_AT_RISK_90D", "IS_END_OF_SUPPORT_WITHIN_12M", "NUMBER", "1 when the product reaches end of support within 12 months of the contract end date", "1", "END_OF_SUPPORT_DATE <= END_DATE + 365", "Product Management", "SAP material master"),
    ("V_INSTALLED_BASE_HEALTH", "HAS_ACTIVE_SUPPORT", "NUMBER", "1 when a support contract covers the system on 2026-10-12", "1", "EXISTS SUPPORT contract in force", "Customer Success", "SAP S/4HANA"),
    ("V_INSTALLED_BASE_HEALTH", "LATEST_HEALTH_SCORE", "NUMBER", "AutoPulse health score for September 2026 (0-100; below 70 is poor)", "91.4", "SYSTEM_TELEMETRY_MONTHLY.HEALTH_SCORE at 2026-09-01", "Support Engineering", "AutoPulse"),
    ("V_CLOUD_COMMIT_UTILIZATION", "UTILIZATION_PCT", "NUMBER", "Consumed dollars divided by committed dollars for the fiscal year to date", "0.54", "SUM(CONSUMED_AMOUNT) / SUM(MONTHLY_COMMIT_AMOUNT)", "Finance - Cloud Revenue", "Cloud billing"),
    ("V_CLOUD_COMMIT_UTILIZATION", "IS_UNDER_UTILIZED", "NUMBER", "1 when utilisation is below 60 percent with at least 3 months reported", "1", "UTILIZATION_PCT < 0.60 AND MONTHS_REPORTED >= 3", "Sales Operations", "Derived"),
    ("V_PARTNER_ATTACH_RATE", "ATTACH_RATE", "NUMBER", "Systems with a support contract starting within 60 days of install divided by systems installed", "0.62", "SUM(SYSTEMS_WITH_SUPPORT) / SUM(SYSTEMS_INSTALLED)", "Partner Operations", "SAP S/4HANA + AutoPulse"),
    ("V_SUPPORT_CASE_SUMMARY", "P1_CASES", "NUMBER", "Count of priority 1 (production down) cases opened", "38", "SUM(PRIORITY = P1)", "Support Engineering", "ServiceNow"),
    ("CONTRACTS", "CONTRACT_STATUS", "VARCHAR", "ACTIVE, RENEWED, CHURNED, or PENDING_RENEWAL as of 2026-10-12", "PENDING_RENEWAL", None, "Finance - FP&A", "SAP S/4HANA"),
    ("CONTRACTS", "END_DATE", "DATE", "Exclusive end date: the contract is in force while start_date <= date < end_date", "2026-12-01", None, "Finance - FP&A", "SAP S/4HANA"),
    ("ORDERS", "NET_AMOUNT", "NUMBER", "Booked amount after discount. Multi-year contracts book total contract value; bookings are never ARR.", "312000", "LIST_AMOUNT * (1 - DISCOUNT_PCT / 100)", "Finance - Revenue Accounting", "SAP S/4HANA"),
    ("PRODUCTS", "END_OF_SUPPORT_DATE", "DATE", "Date support ends for the product. KS-7000 family: 2027-01-31 (bulletin PLB-2026-014).", "2027-01-31", None, "Product Management", "SAP material master"),
    ("SUPPORT_CASES", "CASE_NOTES", "VARCHAR", "Free-text engineer notes with symptoms, actions and customer sentiment", "P1 raised by ... after the KeelOS 9.14.2 upgrade", None, "Support Engineering", "ServiceNow"),
    ("SUPPORT_CASES", "PRIORITY", "VARCHAR", "P1 production down, P2 severely degraded, P3 minor impact, P4 question", "P1", None, "Support Engineering", "ServiceNow"),
    ("FISCAL_CALENDAR", "FISCAL_YEAR", "VARCHAR", "Keelstone fiscal year ends 30 April and is named for the calendar year it ends in", "FY27", None, "Finance - FP&A", "Derived"),
    ("CLOUD_CONSUMPTION_MONTHLY", "CONSUMED_AMOUNT", "NUMBER", "Metered cloud consumption in USD for the month", "48210.55", None, "Finance - Cloud Revenue", "Cloud billing"),
    ("INSTALLED_SYSTEMS", "CURRENT_FIRMWARE", "VARCHAR", "KeelOS version running on 2026-10-12. 9.14.2 carries defect KB-2026-0917; 9.14.3 is the fix.", "KeelOS 9.14.2", None, "Support Engineering", "AutoPulse"),
    ("RENEWAL_OPPORTUNITIES", "STAGE", "VARCHAR", "Salesforce stage. A renewal opportunity stays open after the contract lapses until renewals ops closes it lost, up to a year later.", "Negotiation", None, "Sales Operations", "Salesforce"),
]


def build_data_dictionary() -> pd.DataFrame:
    return pd.DataFrame(DATA_DICTIONARY_ROWS, columns=["TABLE_NAME", "COLUMN_NAME", "DATA_TYPE", "DESCRIPTION", "SAMPLE_VALUE", "METRIC_FORMULA", "BUSINESS_OWNER", "SOURCE_SYSTEM"])


# ---------------------------------------------------------------------------
# ORCHESTRATION
# ---------------------------------------------------------------------------
LOAD_ORDER = ["FISCAL_CALENDAR", "PARTNERS", "SALES_REPS", "CUSTOMERS", "PRODUCTS", "ORDERS", "INSTALLED_SYSTEMS", "SYSTEM_TELEMETRY_MONTHLY",
              "CONTRACTS", "RENEWAL_OPPORTUNITIES", "CLOUD_CONSUMPTION_MONTHLY", "SUPPORT_CASES", "DATA_DICTIONARY"]


def generate_all(verbose=True) -> dict:
    def log(msg):
        if verbose:
            print(msg, flush=True)
    log("Building dimensions...")
    cal = build_fiscal_calendar()
    partners = build_partners()
    reps = build_sales_reps()
    customers = assign_reps(build_customers(partners), reps)
    products = build_products()
    log("Building installed base...")
    systems = build_installed_systems(customers)
    first_install = systems.groupby("CUSTOMER_ID").INSTALL_DATE.min()
    g = rng("customer_since")
    customers["CUSTOMER_SINCE"] = [first_install.get(c, START) - timedelta(days=int(g.integers(10, 180))) for c in customers.CUSTOMER_ID]
    # cloud membership is decided inside build_contracts; cases need it, contracts need cases -> two-pass:
    log("Building support cases (pass 1) and contracts...")
    cases_seed = build_support_cases(customers, systems, {}, set())
    contracts, cloud, under, has_sub = build_contracts(customers, systems, reps, cases_seed)
    log("Building support cases (final)...")
    cases = build_support_cases(customers, systems, cloud, has_sub)
    log("Building telemetry, cloud consumption, renewal opportunities, orders...")
    telemetry = build_telemetry(systems, cases)
    consumption = build_cloud_consumption(contracts, under)
    opps = build_renewal_opps(contracts, customers, cases)
    orders, sys_ol, ctr_ol = build_orders(systems, contracts, customers, products)
    systems["ORDER_LINE_ID"] = systems.SYSTEM_ID.map(sys_ol)
    contracts["ORDER_LINE_ID"] = contracts.CONTRACT_ID.map(ctr_ol)
    dd = build_data_dictionary()

    systems_out = systems.drop(columns=[c for c in systems.columns if c.startswith("X_")])
    contracts_out = contracts.drop(columns=[c for c in contracts.columns if c.startswith("X_")])
    frames = {
        "FISCAL_CALENDAR": cal, "PARTNERS": partners, "SALES_REPS": reps, "CUSTOMERS": customers, "PRODUCTS": products, "ORDERS": orders,
        "INSTALLED_SYSTEMS": systems_out, "SYSTEM_TELEMETRY_MONTHLY": telemetry, "CONTRACTS": contracts_out, "RENEWAL_OPPORTUNITIES": opps,
        "CLOUD_CONSUMPTION_MONTHLY": consumption, "SUPPORT_CASES": cases, "DATA_DICTIONARY": dd,
    }
    for k, v in frames.items():
        log(f"  {k}: {len(v):,}")
    return frames
