"""
generator.py (Nordmark Dagligvaror)
-----------------------------------
Deterministic synthetic data for the Nordmark Dagligvaror WisdomAI POC: a fictional
Swedish grocery group with three banners — Kronmat (discount), Torghallen (neighbourhood)
and Grosshallen (hypermarkets acquired 2025-01-01). No Snowflake dependency; every
builder is seeded so the same rows are produced on every run.

Demo "today" (AS_OF) = 2026-09-30. Data spans 2024-10-01 .. 2026-09-30.
Rolling-12-month windows: R12_CUR = 2025-10-01..2026-09-30, R12_PRIOR = 2024-10-01..2025-09-30.

Engineered control points (see ../DEMO_PLAN.md / demo.yaml):
  CP1  Grosshallen like-for-like lags the group (about -1.5% vs +1.5%); the gap is
       transactions (about -6%) not basket (about +5%); gross margin 2.5 pts below Kronmat;
       banner EBIT loss in Q3 2025, break-even in Q3 2026 after cost measures. Hero store
       Grosshallen Vasterhamn sells ~62% of its catchment potential vs ~0.90 for its peer cluster.
  CP2  Kronmat Fresh & Produce grows ~+8% while its margin falls ~2 pts; the campaign
       "Sommarpris 2026" has a top-3 uplift and a bottom-3 margin.
  CP3  Stores with Dairy/Bread availability below 94% run >= 3 pts weaker like-for-like;
       Vasterhamn has the worst availability in the banner (~91%).
  CP4  Families visits fall >10% at Grosshallen while other banners hold; the discount
       competitor "Billigmat" opened 1.1 km from Vasterhamn on 2026-03-12 (sales -9% after).
  CP5  Peer store Grosshallen Nordstaden (same cluster) runs at ~97% of potential with
       +7 pts private-label share, 97% availability and ~35% lower markdown rate.
  CP6  Grosshallen non-food lost sales concentrate in SKUs from the three import suppliers
       whose purchase orders run late in the Teradata purchasing platform (keys from inputs/ref).
"""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from demo_creator.rng import rng as _seeded_rng

SEED = 20261026
AS_OF = date(2026, 9, 30)
START = date(2024, 10, 1)
CAL_START = date(2024, 10, 1)
CAL_END = date(2026, 12, 31)
R12_CUR = (date(2025, 10, 1), date(2026, 9, 30))
R12_PRIOR = (date(2024, 10, 1), date(2025, 9, 30))
REF_DIR = Path(__file__).resolve().parent / "inputs" / "ref"

# Story constants (mirrored in demo.yaml generator.constants)
GROUP_NAME = "Nordmark Dagligvaror"
KRM, TRG, GRH = "Kronmat", "Torghallen", "Grosshallen"
HYPERMARKET_ACQUIRED = date(2025, 1, 1)
HERO_STORE = "Grosshallen Västerhamn"
PEER_STORE = "Grosshallen Nordstaden"
CONVERTED_STORE = "Grosshallen Sundsvik"
CONVERTED_ON = date(2026, 8, 15)
HERO_PROMOTION = "Sommarpris 2026"
HERO_CATEGORY = "Fresh & Produce"
COMPETITOR_NAME = "Billigmat"
COMPETITOR_OPENED = date(2026, 3, 12)
COMPETITOR_DISTANCE_KM = 1.1
HERO_SEGMENT = "Families"
VAT_CUT_DATE = date(2026, 4, 1)
LATE_SUPPLIER_COUNT = 3
NONFOOD_SKU_COUNT = 250
LATE_SUPPLIER_SKUS = 20          # SKUs per late supplier in the Grosshallen range

BANNERS = {
    KRM: dict(banner_id="KRM", store_format="Discount", stores=120, loyalty="Kronmat Plus", basket=355.0, price_index=0.915, gp=0.270,
              director="Johanna Lindqvist", positioning="Sweden's cheapest full-range grocery basket: large discount supermarkets with a wide private-label range."),
    TRG: dict(banner_id="TRG", store_format="Neighbourhood", stores=90, loyalty="Torghallen Klubb", basket=185.0, price_index=1.03, gp=0.305,
              director="Erik Sandström", positioning="Convenient neighbourhood supermarkets with fresh food ready meals and personal service."),
    GRH: dict(banner_id="GRH", store_format="Hypermarket", stores=38, loyalty="Grosshallen Kort", basket=520.0, price_index=0.96, gp=0.245,
              director="Maria Holm", positioning="Out-of-town hypermarkets for the big weekly shop: grocery plus imported non-food."),
}
REGIONS = ["Stockholm", "Vast", "Syd", "Ost", "Mitt", "Norr"]
REGION_W = {KRM: [0.26, 0.20, 0.18, 0.12, 0.14, 0.10], TRG: [0.36, 0.20, 0.16, 0.10, 0.12, 0.06], GRH: [0.24, 0.21, 0.21, 0.11, 0.13, 0.10]}
REGION_CITIES = {
    "Stockholm": [("Stockholm", "Stockholm"), ("Solna", "Solna"), ("Nacka", "Nacka"), ("Huddinge", "Huddinge"), ("Täby", "Täby"), ("Sollentuna", "Sollentuna"),
                  ("Botkyrka", "Tumba"), ("Haninge", "Handen"), ("Järfälla", "Jakobsberg"), ("Södertälje", "Södertälje"), ("Upplands Väsby", "Upplands Väsby"), ("Lidingö", "Lidingö")],
    "Vast": [("Göteborg", "Göteborg"), ("Mölndal", "Mölndal"), ("Borås", "Borås"), ("Partille", "Partille"), ("Kungsbacka", "Kungsbacka"), ("Trollhättan", "Trollhättan"),
             ("Uddevalla", "Uddevalla"), ("Skövde", "Skövde"), ("Varberg", "Varberg"), ("Halmstad", "Halmstad")],
    "Syd": [("Malmö", "Malmö"), ("Lund", "Lund"), ("Helsingborg", "Helsingborg"), ("Kristianstad", "Kristianstad"), ("Växjö", "Växjö"), ("Karlskrona", "Karlskrona"),
            ("Ystad", "Ystad"), ("Landskrona", "Landskrona"), ("Hässleholm", "Hässleholm"), ("Kalmar", "Kalmar")],
    "Ost": [("Linköping", "Linköping"), ("Norrköping", "Norrköping"), ("Jönköping", "Jönköping"), ("Nyköping", "Nyköping"), ("Västervik", "Västervik"),
            ("Motala", "Motala"), ("Eskilstuna", "Eskilstuna"), ("Katrineholm", "Katrineholm")],
    "Mitt": [("Uppsala", "Uppsala"), ("Västerås", "Västerås"), ("Örebro", "Örebro"), ("Gävle", "Gävle"), ("Karlstad", "Karlstad"), ("Falun", "Falun"),
             ("Borlänge", "Borlänge"), ("Enköping", "Enköping"), ("Sandviken", "Sandviken")],
    "Norr": [("Umeå", "Umeå"), ("Luleå", "Luleå"), ("Sundsvall", "Sundsvall"), ("Östersund", "Östersund"), ("Skellefteå", "Skellefteå"),
             ("Örnsköldsvik", "Örnsköldsvik"), ("Piteå", "Piteå"), ("Härnösand", "Härnösand")],
}
CATCHMENT_TYPES = ["Urban core", "Suburban family", "Small town", "Commuter belt", "Rural hub"]
CATCHMENT_W = {KRM: [0.10, 0.35, 0.22, 0.23, 0.10], TRG: [0.50, 0.25, 0.15, 0.10, 0.00], GRH: [0.00, 0.50, 0.22, 0.28, 0.00]}
NBH_PREFIX = ["Väster", "Öster", "Norr", "Söder", "Björk", "Ek", "Lind", "Sol", "Kvarn", "Strand", "Hag", "Berg", "Sjö", "Äng", "Tall", "Gran", "Ås", "Dal",
              "Mo", "Ny", "Kyrk", "Bro", "Fors", "Höj", "Lövs", "Ryd", "Hall", "Malm", "Rös", "Vall"]
NBH_SUFFIX = ["hamn", "staden", "vik", "ängen", "holmen", "hagen", "berga", "backen", "lund", "by", "torp", "näs", "bro", "dalen", "hult", "gården", "kulla", "sund", "viken", "höjden"]
SEGMENTS = ["Families", "Seniors", "Students", "Urban singles", "Value seekers", "Premium"]
SEGMENT_MIX = {  # by catchment type
    "Urban core": [0.14, 0.12, 0.18, 0.30, 0.14, 0.12],
    "Suburban family": [0.38, 0.14, 0.04, 0.10, 0.22, 0.12],
    "Small town": [0.28, 0.26, 0.04, 0.10, 0.24, 0.08],
    "Commuter belt": [0.34, 0.12, 0.04, 0.16, 0.22, 0.12],
    "Rural hub": [0.24, 0.32, 0.02, 0.06, 0.30, 0.06],
}
SEGMENT_FREQ = {"Families": 3.4, "Seniors": 4.2, "Students": 2.4, "Urban singles": 2.9, "Value seekers": 3.1, "Premium": 2.3}   # visits per member per month
SEGMENT_BASKET = {"Families": 1.35, "Seniors": 0.80, "Students": 0.55, "Urban singles": 0.70, "Value seekers": 0.95, "Premium": 1.25}

# category_name: (department, is_fresh, share_all_banners, gp_pct, waste_prone, teradata_department, nonfood)
CATEGORIES = [
    ("Fresh & Produce", "Fresh", True, 0.120, 0.300, True, None, False),
    ("Dairy", "Fresh", True, 0.110, 0.220, True, None, False),
    ("Bread & Bakery", "Fresh", True, 0.070, 0.320, True, None, False),
    ("Meat & Poultry", "Fresh", True, 0.110, 0.240, True, None, False),
    ("Fish & Seafood", "Fresh", True, 0.030, 0.260, True, None, False),
    ("Deli & Charcuterie", "Fresh", True, 0.060, 0.330, True, None, False),
    ("Ready Meals", "Fresh", True, 0.050, 0.350, True, None, False),
    ("Frozen", "Frozen", False, 0.060, 0.280, False, None, False),
    ("Beverages", "Ambient", False, 0.090, 0.240, False, None, False),
    ("Snacks & Confectionery", "Ambient", False, 0.080, 0.300, False, None, False),
    ("Pantry Staples", "Ambient", False, 0.100, 0.250, False, None, False),
    ("Health & Beauty", "Household", False, 0.040, 0.330, False, None, False),
    ("Household & Cleaning", "Household", False, 0.040, 0.270, False, None, False),
    ("Baby & Child", "Household", False, 0.015, 0.200, False, None, False),
    ("Pet", "Household", False, 0.015, 0.280, False, None, False),
    ("Beer & Cider", "Ambient", False, 0.020, 0.220, False, None, False),
    ("Flowers & Garden", "Fresh", True, 0.010, 0.400, True, None, False),
    ("Apparel & Footwear", "Non-food", False, 0.040, 0.420, False, "Apparel", True),
    ("Home & Kitchen", "Non-food", False, 0.040, 0.380, False, "Home", True),
    ("Electronics", "Non-food", False, 0.020, 0.180, False, "Electronics", True),
    ("Toys & Games", "Non-food", False, 0.015, 0.350, False, "Toys & Games", True),
    ("Sports & Outdoors", "Non-food", False, 0.015, 0.360, False, "Sports & Outdoors", True),
    ("Cosmetics & Fragrance", "Non-food", False, 0.010, 0.400, False, "Beauty", True),
]
TD_DEPT_TO_CATEGORY = {"Apparel": "Apparel & Footwear", "Footwear": "Apparel & Footwear", "Home": "Home & Kitchen", "Electronics": "Electronics",
                       "Toys & Games": "Toys & Games", "Sports & Outdoors": "Sports & Outdoors", "Beauty": "Cosmetics & Fragrance"}
CATEGORY_MANAGERS = ["Anna Bergström", "Oskar Nilsson", "Sara Ekholm", "Mikael Dahl", "Elin Åberg", "Jonas Petersson", "Karin Lund", "Fredrik Svensson"]
FIRST = ["Anna", "Erik", "Maria", "Johan", "Karin", "Lars", "Sofia", "Anders", "Eva", "Per", "Lena", "Mikael", "Emma", "Jonas", "Sara", "Daniel", "Ingrid", "Oskar", "Elin", "Fredrik",
         "Hanna", "Magnus", "Linnea", "Niklas", "Åsa", "Henrik", "Maja", "Mattias", "Camilla", "Patrik", "Amir", "Fatima", "Yusuf", "Leila", "Omar", "Noor"]
LAST = ["Andersson", "Johansson", "Karlsson", "Nilsson", "Eriksson", "Larsson", "Olsson", "Persson", "Svensson", "Gustafsson", "Pettersson", "Jonsson", "Jansson",
        "Hansson", "Bengtsson", "Jönsson", "Lindberg", "Jakobsson", "Magnusson", "Lindström", "Lindqvist", "Axelsson", "Berg", "Bergström", "Lundberg", "Holm", "Ali", "Hassan"]
COMPETITORS = [("Billigmat", "Discount"), ("Matpriset", "Discount"), ("Hemmaköp", "Supermarket"), ("Stora Maxi", "Hypermarket"), ("Nära Dig", "Convenience"),
               ("Matkassen Online", "Online"), ("Familjelivs", "Supermarket"), ("Lågpris Livs", "Discount")]


def rng(tag: str) -> np.random.Generator:
    return _seeded_rng(SEED, tag)


def _dates(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


# ---------------------------------------------------------------- calendar
def _easter(year: int) -> date:
    a = year % 19; b = year // 100; c = year % 100; d = b // 4; e = b % 4; f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30; i = c // 4; k = c % 4; l = (32 + 2 * e + 2 * i - h - k) % 7; m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31; day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _midsummer_eve(year: int) -> date:
    d = date(year, 6, 19)
    while d.weekday() != 4:
        d += timedelta(days=1)
    return d


def _all_saints(year: int) -> date:
    d = date(year, 10, 31)
    while d.weekday() != 5:
        d += timedelta(days=1)
    return d


def swedish_holidays(year: int) -> dict[date, str]:
    e = _easter(year)
    ms = _midsummer_eve(year)
    return {
        date(year, 1, 1): "New Year's Day", date(year, 1, 6): "Epiphany", e - timedelta(days=2): "Good Friday", e: "Easter Sunday",
        e + timedelta(days=1): "Easter Monday", date(year, 5, 1): "May Day", e + timedelta(days=39): "Ascension Day", date(year, 6, 6): "National Day",
        ms: "Midsummer Eve", ms + timedelta(days=1): "Midsummer Day", _all_saints(year): "All Saints' Day", date(year, 12, 24): "Christmas Eve",
        date(year, 12, 25): "Christmas Day", date(year, 12, 26): "Boxing Day", date(year, 12, 31): "New Year's Eve",
    }


def build_calendar() -> pd.DataFrame:
    hol = {}
    for y in (2024, 2025, 2026):
        hol.update(swedish_holidays(y))
    rows = []
    for d in _dates(CAL_START, CAL_END):
        iso = d.isocalendar()
        e = _easter(d.year); ms = _midsummer_eve(d.year)
        if date(d.year, 12, 1) <= d <= date(d.year, 12, 31):
            season = "Christmas"
        elif e - timedelta(days=10) <= d <= e + timedelta(days=1):
            season = "Easter"
        elif ms - timedelta(days=6) <= d <= ms + timedelta(days=1):
            season = "Midsummer"
        elif d.month in (1, 2):
            season = "Winter"
        elif d.month in (3, 4, 5):
            season = "Spring"
        elif d.month in (6, 7, 8):
            season = "Summer"
        else:
            season = "Autumn"
        bucket = "R12_CUR" if R12_CUR[0] <= d <= R12_CUR[1] else ("R12_PRIOR" if R12_PRIOR[0] <= d <= R12_PRIOR[1] else None)
        rows.append(dict(
            calendar_date=d, year_num=d.year, month_num=d.month, month_start_date=date(d.year, d.month, 1), month_name=d.strftime("%B"),
            quarter_label=f"{d.year}-Q{(d.month - 1) // 3 + 1}", iso_year=iso[0], iso_week=iso[1], week_start_date=d - timedelta(days=d.weekday()),
            week_label=f"{iso[0]}-W{iso[1]:02d}", day_of_week=d.isoweekday(), day_name=d.strftime("%A"), is_weekend=d.isoweekday() >= 6,
            is_holiday=d in hol, holiday_name=hol.get(d), season=season, rolling_12m_bucket=bucket, is_in_data_window=START <= d <= AS_OF,
        ))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- banners / categories
def build_banners() -> pd.DataFrame:
    rows = []
    for name, b in BANNERS.items():
        rows.append(dict(banner_id=b["banner_id"], banner_name=name, store_format=b["store_format"], positioning=b["positioning"], loyalty_program=b["loyalty"],
                         acquired_date=HYPERMARKET_ACQUIRED if name == GRH else None, typical_basket_sek=b["basket"], price_index=b["price_index"],
                         target_gp_pct=b["gp"], banner_director=b["director"]))
    return pd.DataFrame(rows)


def build_product_categories() -> pd.DataFrame:
    rows = []
    for i, (name, dept, fresh, share, gp, waste_prone, td_dept, nonfood) in enumerate(CATEGORIES, 1):
        rows.append(dict(category_id=f"CAT-{i:02d}", category_name=name, department=dept, is_fresh=fresh, is_nonfood=nonfood,
                         sold_in_banners=GRH if nonfood else f"{KRM},{TRG},{GRH}", target_gp_pct=gp, waste_prone=waste_prone,
                         category_manager=CATEGORY_MANAGERS[i % len(CATEGORY_MANAGERS)], teradata_department=td_dept))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- stores + neighbourhoods
def build_stores_and_neighborhoods() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Returns (STORES, NEIGHBORHOODS, params) where params holds the per-store story parameters
    (annual sales base, growth, basket, availability quality, pl share, markdown factor...)."""
    r = rng("stores")
    stores, nbhs, params = [], [], {}
    used_names: set[str] = set()
    sid = 0

    def nbh_name(force: str | None = None) -> str:
        if force:
            used_names.add(force); return force
        while True:
            n = r.choice(NBH_PREFIX) + r.choice(NBH_SUFFIX)
            if n not in used_names:
                used_names.add(n); return n

    def add_store(banner: str, *, force_name: str | None = None, region: str | None = None, city: tuple | None = None, catchment: str | None = None,
                  opened: date | None = None, closed: date | None = None, converted_to: str | None = None, franchise: bool = False, p_over: dict | None = None):
        nonlocal sid
        sid += 1
        b = BANNERS[banner]
        region = region or str(r.choice(REGIONS, p=REGION_W[banner]))
        muni, cty = city or REGION_CITIES[region][int(r.integers(len(REGION_CITIES[region])))]
        catchment = catchment or str(r.choice(CATCHMENT_TYPES, p=CATCHMENT_W[banner]))
        nb = nbh_name(force_name)
        if opened is None:
            if banner == GRH:
                opened = date(int(r.integers(2004, 2020)), int(r.integers(1, 13)), 1)
            else:
                opened = date(int(r.integers(1996, 2024)), int(r.integers(1, 13)), 1)
        sqm = {KRM: int(r.integers(1500, 2900)), TRG: int(r.integers(450, 1250)), GRH: int(r.integers(5000, 9200))}[banner]
        # annual sales base (R12_PRIOR level, MSEK)
        base = {KRM: r.normal(85, 11), TRG: r.normal(36, 7), GRH: r.normal(180, 28)}[banner]
        base *= {"Urban core": 1.05, "Suburban family": 1.05, "Small town": 0.92, "Commuter belt": 1.0, "Rural hub": 0.85}[catchment]
        base = float(np.clip(base, {KRM: 55, TRG: 20, GRH: 120}[banner], {KRM: 125, TRG: 60, GRH: 240}[banner]))
        growth = {KRM: r.normal(0.021, 0.022), TRG: r.normal(0.053, 0.022), GRH: r.normal(-0.018, 0.025)}[banner]
        basket_growth = {KRM: r.normal(0.015, 0.008), TRG: r.normal(0.020, 0.008), GRH: r.normal(0.055, 0.010)}[banner]
        p = dict(banner=banner, base_msek=base, growth=float(growth), basket_growth=float(basket_growth),
                 basket=float(b["basket"] * r.normal(1.0, 0.05)), gp_adj=float(r.normal(0, 0.006)),
                 osa_q=float(r.normal(0, 0.008)), low_osa=False, pl_share={KRM: 0.30, TRG: 0.24, GRH: 0.19}[banner] + float(r.normal(0, 0.02)),
                 markdown_f=float(np.clip(r.normal(1.0, 0.12), 0.7, 1.4)), waste_f=float(np.clip(r.normal(1.0, 0.12), 0.7, 1.4)),
                 potential_index=float(np.clip(r.normal(0.92, 0.07), 0.78, 1.12)), step_date=None, step=0.0, families_trend=0.0, catchment=catchment)
        if p_over:
            p.update(p_over)
        store_id = f"ST-{sid:04d}"
        params[store_id] = p
        status = "OPEN" if closed is None else ("CONVERTED" if converted_to else "CLOSED")
        lat = {"Stockholm": 59.33, "Vast": 57.71, "Syd": 55.9, "Ost": 58.4, "Mitt": 59.75, "Norr": 63.6}[region] + float(r.normal(0, 0.35))
        lon = {"Stockholm": 18.07, "Vast": 12.3, "Syd": 13.5, "Ost": 15.8, "Mitt": 16.2, "Norr": 18.5}[region] + float(r.normal(0, 0.6))
        stores.append(dict(store_id=store_id, store_name=f"{banner} {nb}", banner_id=b["banner_id"], banner=banner, store_format=b["store_format"], region=region,
                           municipality=muni, city=cty, neighborhood_id=f"NBH-{sid:03d}", catchment_type=catchment, peer_cluster=f"{banner} / {catchment}",
                           sales_area_sqm=sqm, opened_date=opened, acquired_date=HYPERMARKET_ACQUIRED if banner == GRH else None, closed_date=closed,
                           converted_to_banner=converted_to, store_status=status, is_franchise=franchise,
                           is_lfl_comparable=(opened < START and closed is None), store_manager=f"{r.choice(FIRST)} {r.choice(LAST)}",
                           parking_spaces={KRM: int(r.integers(80, 260)), TRG: int(r.integers(0, 40)), GRH: int(r.integers(400, 1100))}[banner],
                           online_pickup=bool(r.random() < {KRM: 0.6, TRG: 0.25, GRH: 0.9}[banner]), latitude=round(lat, 6), longitude=round(lon, 6)))
        pop = {"Urban core": r.integers(28000, 60000), "Suburban family": r.integers(14000, 32000), "Small town": r.integers(6000, 16000),
               "Commuter belt": r.integers(9000, 22000), "Rural hub": r.integers(3000, 9000)}[catchment]
        hh = int(pop / r.uniform(1.9, 2.5))
        inc = {"Urban core": r.normal(430, 40), "Suburban family": r.normal(520, 45), "Small town": r.normal(400, 35), "Commuter belt": r.normal(470, 40), "Rural hub": r.normal(380, 30)}[catchment]
        mix = SEGMENT_MIX[catchment]
        comp = int(r.integers({"Urban core": 3, "Suburban family": 1, "Small town": 1, "Commuter belt": 1, "Rural hub": 0}[catchment],
                              {"Urban core": 8, "Suburban family": 5, "Small town": 4, "Commuter belt": 4, "Rural hub": 2}[catchment] + 1))
        disc = bool(r.random() < 0.45) if comp > 0 else False
        nearest = float(np.clip(r.normal(1.4, 0.7), 0.2, 6.0)) if comp > 0 else float(r.uniform(4, 15))
        nbhs.append(dict(neighborhood_id=f"NBH-{sid:03d}", neighborhood_name=f"{nb} ({cty})", municipality=muni, region=region, catchment_type=catchment,
                         population_2km=int(pop), households_2km=hh, median_income_ksek=round(float(inc), 1),
                         share_families=round(mix[0] + float(r.normal(0, 0.03)), 3), share_students=round(mix[2] + float(r.normal(0, 0.015)), 3),
                         share_seniors=round(mix[1] + float(r.normal(0, 0.03)), 3),
                         car_access_share=round({"Urban core": 0.45, "Suburban family": 0.82, "Small town": 0.78, "Commuter belt": 0.86, "Rural hub": 0.92}[catchment] + float(r.normal(0, 0.04)), 3),
                         competitor_count_2km=comp, discount_competitor_flag=disc, nearest_competitor_km=round(nearest, 2),
                         grocery_spend_potential_msek=0.0, fair_share_pct=0.0, catchment_potential_msek=0.0))   # filled after sales are known
        return store_id

    # --- Grosshallen (38 incl. hero, peer and the converted store) ---
    hero_id = add_store(GRH, force_name="Västerhamn", region="Vast", city=("Göteborg", "Göteborg"), catchment="Suburban family", opened=date(2009, 3, 1),
                        p_over=dict(base_msek=172.0, growth=-0.030, basket_growth=0.050, gp_adj=-0.004, osa_q=-0.055, low_osa=True, pl_share=0.15,
                                    markdown_f=1.45, waste_f=1.3, potential_index=0.62, step_date=COMPETITOR_OPENED, step=-0.09, families_trend=-0.20))
    peer_id = add_store(GRH, force_name="Nordstaden", region="Mitt", city=("Uppsala", "Uppsala"), catchment="Suburban family", opened=date(2011, 9, 1),
                        p_over=dict(base_msek=168.0, growth=0.030, basket_growth=0.040, gp_adj=0.006, osa_q=0.014, pl_share=0.22, markdown_f=0.88, waste_f=0.85,
                                    potential_index=0.97, families_trend=-0.02))
    conv_id = add_store(GRH, force_name="Sundsvik", region="Syd", city=("Helsingborg", "Helsingborg"), catchment="Commuter belt", opened=date(2007, 5, 1),
                        closed=CONVERTED_ON, converted_to=KRM, p_over=dict(base_msek=128.0, growth=-0.060, potential_index=0.70))
    for _ in range(35):
        add_store(GRH)
    # --- Kronmat (120; 8 opened inside the window) ---
    for i in range(120):
        opened = None
        if i >= 112:
            opened = date(2025, 1, 1) + timedelta(days=int(r.integers(0, 600)))
        add_store(KRM, opened=opened)
    add_store(KRM, force_name="Sundsvik", region="Syd", city=("Helsingborg", "Helsingborg"), catchment="Commuter belt", opened=date(2026, 9, 5),
              p_over=dict(base_msek=95.0, growth=0.0))
    # --- Torghallen (90; 30 franchise; 4 opened inside the window) ---
    for i in range(90):
        opened = date(2025, 3, 1) + timedelta(days=int(r.integers(0, 500))) if i >= 86 else None
        add_store(TRG, opened=opened, franchise=(i % 3 == 0))

    stores_df = pd.DataFrame(stores)
    nbh_df = pd.DataFrame(nbhs)
    # low-availability stores (CP3): ~22 comparable stores across banners with weak availability AND weaker growth
    comparable = [s for s in stores_df[stores_df.is_lfl_comparable].store_id if s not in (hero_id, peer_id)]
    low = r.choice(comparable, size=22, replace=False)
    for s in low:
        params[s]["osa_q"] = float(r.normal(-0.040, 0.006))
        params[s]["low_osa"] = True
        params[s]["growth"] -= 0.050
    # Grosshallen Families trend (CP4): the banner loses family shoppers; other banners hold
    for s, p in params.items():
        if p["banner"] == GRH and s not in (hero_id, peer_id):
            p["families_trend"] = float(r.normal(-0.11, 0.03))
        elif p["banner"] != GRH:
            p["families_trend"] = float(r.normal(0.0, 0.015))
    params["_ids"] = dict(hero=hero_id, peer=peer_id, converted=conv_id)
    return stores_df, nbh_df, params


# ---------------------------------------------------------------- daily sales
def _day_factor(cal: pd.DataFrame, catchment: str, banner: str) -> np.ndarray:
    dow = cal.day_of_week.to_numpy()
    wk = np.array([0.0, 0.86, 0.86, 0.92, 1.02, 1.36, 1.28, 0.70])[dow]
    if banner == TRG:
        wk = 1 + (wk - 1) * 0.55
    f = wk.copy()
    hol = cal.holiday_name.fillna("").to_numpy()
    season = cal.season.to_numpy()
    month = cal.month_num.to_numpy()
    day = cal.calendar_date.map(lambda d: d.day).to_numpy()
    hmap = {"New Year's Day": 0.25, "Epiphany": 0.65, "Good Friday": 0.55, "Easter Sunday": 0.35, "Easter Monday": 0.6, "May Day": 0.6, "Ascension Day": 0.7,
            "National Day": 0.7, "Midsummer Eve": 0.45, "Midsummer Day": 0.3, "All Saints' Day": 0.7, "Christmas Eve": 0.5, "Christmas Day": 0.1, "Boxing Day": 0.6,
            "New Year's Eve": 1.15}
    for i, h in enumerate(hol):
        if h:
            f[i] *= hmap.get(h, 0.7)
    # pre-holiday peaks
    f = np.where((month == 12) & (day >= 15) & (day <= 23), f * 1.45, f)
    f = np.where(season == "Midsummer", f * 1.22, f)
    f = np.where(season == "Easter", f * 1.10, f)
    summer = {"Urban core": 0.86, "Suburban family": 0.95, "Small town": 1.08, "Commuter belt": 0.95, "Rural hub": 1.18}[catchment]
    f = np.where(month == 7, f * summer, f)
    f = np.where(month == 1, f * 0.93, f)
    return f


def _price_factor(dates: np.ndarray) -> np.ndarray:
    """Shelf price level ex VAT: mild inflation to spring 2025, flat, then deflation through 2026 (about -2% y/y by Q3 2026)."""
    t = np.array([(d - START).days for d in dates], dtype=float)
    f = np.ones_like(t)
    f += np.clip(t, 0, 180) / 180 * 0.012                       # +1.2% by end of March 2025
    f -= np.clip(t - 455, 0, 275) / 275 * 0.032                  # -3.2% from 2026-01 to 2026-09-30
    return f


def build_store_daily_sales(cal: pd.DataFrame, stores: pd.DataFrame, params: dict) -> pd.DataFrame:
    cal_w = cal[cal.is_in_data_window].reset_index(drop=True)
    dates = cal_w.calendar_date.to_numpy()
    t = np.array([(d - date(2025, 4, 1)).days for d in dates], dtype=float) / 365.0   # 0 at the middle of the prior window
    price = _price_factor(dates)
    vat_vol = np.array([1.025 if d >= VAT_CUT_DATE else 1.0 for d in dates])          # VAT cut lifts volume
    frames = []
    for s in stores.itertuples(index=False):
        p = params[s.store_id]
        r = rng(f"daily:{s.store_id}")
        f = _day_factor(cal_w, s.catchment_type, s.banner)
        open_mask = np.array([(d >= s.opened_date) and (s.closed_date is None or d < s.closed_date) for d in dates])
        if not open_mask.any():
            continue
        level = p["base_msek"] * 1e6 / 365.0 / f.mean()
        growth = (1 + p["growth"]) ** t
        step = np.ones_like(t)
        if p["step_date"] is not None:
            step = np.where(dates >= p["step_date"], 1 + p["step"], 1.0)
        # ramp-up for new stores (first 90 days)
        age = np.array([(d - s.opened_date).days for d in dates], dtype=float)
        ramp = np.clip(0.55 + age / 90 * 0.45, 0.55, 1.0)
        noise = r.normal(1.0, 0.045, size=len(dates))
        sales = level * f * growth * step * ramp * noise * vat_vol * price
        basket = p["basket"] * price * (1 + p["basket_growth"]) ** t * r.normal(1.0, 0.02, size=len(dates))
        basket *= np.where(cal_w.day_of_week.to_numpy() >= 5, 1.12, 0.96)   # bigger weekend baskets
        tx = np.maximum(1, np.round(sales / basket)).astype(int)
        items = np.round(tx * {KRM: 14.5, TRG: 7.5, GRH: 22.0}[s.banner] * r.normal(1.0, 0.03, size=len(dates))).astype(int)
        loy_share = {KRM: 0.62, TRG: 0.55, GRH: 0.50}[s.banner] + r.normal(0, 0.02)
        loy_tx = np.round(tx * loy_share * r.normal(1.0, 0.03, size=len(dates))).astype(int)
        loy_sales = sales * loy_share * 1.08 * r.normal(1.0, 0.03, size=len(dates))
        online_share = (0.06 if s.online_pickup else 0.0) * {KRM: 1.0, TRG: 0.5, GRH: 1.3}[s.banner]
        online_orders = np.round(tx * online_share * r.normal(1.0, 0.1, size=len(dates))).astype(int)
        online_sales = online_orders * basket * 1.9
        df = pd.DataFrame(dict(store_id=s.store_id, calendar_date=dates, net_sales_sek=np.round(sales, 2), gross_profit_sek=0.0, transactions=tx,
                               items_sold=items, loyalty_transactions=np.minimum(loy_tx, tx), loyalty_sales_sek=np.round(np.minimum(loy_sales, sales * 0.95), 2),
                               online_orders=np.minimum(online_orders, tx), online_sales_sek=np.round(np.minimum(online_sales, sales * 0.4), 2)))
        frames.append(df[open_mask])
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------- weekly store x category
def build_weekly(cal: pd.DataFrame, stores: pd.DataFrame, params: dict, daily: pd.DataFrame, cats: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Weekly store x category facts split from the daily totals; also returns daily with gross_profit filled in."""
    week_of = dict(zip(cal.calendar_date, cal.week_start_date))
    d = daily.copy()
    d["week_start_date"] = d.calendar_date.map(week_of)
    wk_tot = d.groupby(["store_id", "week_start_date"], as_index=False).net_sales_sek.sum()
    banner_of = dict(zip(stores.store_id, stores.banner))
    cat_names = [c[0] for c in CATEGORIES]
    cat_id = dict(zip(cats.category_name, cats.category_id))
    base_share = np.array([c[3] for c in CATEGORIES])
    base_gp = np.array([c[4] for c in CATEGORIES])
    fresh = np.array([c[2] for c in CATEGORIES])
    nonfood = np.array([c[7] for c in CATEGORIES])
    hero_cat_i = cat_names.index(HERO_CATEGORY)
    dairy_i, bread_i = cat_names.index("Dairy"), cat_names.index("Bread & Bakery")
    ready_i, pantry_i, bev_i = cat_names.index("Ready Meals"), cat_names.index("Pantry Staples"), cat_names.index("Beverages")
    sku_per_cat = np.array([420, 260, 180, 240, 90, 220, 160, 300, 380, 520, 700, 420, 300, 140, 120, 90, 60, 60, 50, 25, 30, 30, 25], dtype=float)
    frames = []
    ids = params["_ids"]
    for store_id, grp in wk_tot.groupby("store_id"):
        p = params[store_id]
        banner = banner_of[store_id]
        r = rng(f"weekly:{store_id}")
        share = base_share.copy()
        if banner != GRH:
            share[nonfood] = 0
        if banner == TRG:
            share[ready_i] *= 1.9; share[cat_names.index("Beer & Cider")] *= 0.6
        if banner == KRM:
            share[pantry_i] *= 1.15; share[bev_i] *= 1.1; share[ready_i] *= 0.7
        share = share * r.normal(1.0, 0.06, size=len(share))
        share /= share.sum()
        # banner margin calibration: scale category margins so the sales-weighted mix hits the banner target
        gp = base_gp.copy()
        if banner == KRM:
            gp[hero_cat_i] = 0.282
        scale = (BANNERS[banner]["gp"] + p["gp_adj"]) / float((gp * share).sum())
        gp = gp * scale
        weeks = grp.week_start_date.to_numpy()
        tot = grp.net_sales_sek.to_numpy()
        tt = np.array([(w - date(2025, 4, 1)).days for w in weeks], dtype=float) / 365.0
        n_w = len(weeks)
        osa_base = 0.965 + p["osa_q"]
        rows = []
        for ci, cname in enumerate(cat_names):
            if share[ci] <= 0:
                continue
            sh = share[ci] * r.normal(1.0, 0.05, size=n_w)
            gpc = np.full(n_w, gp[ci]) + r.normal(0, 0.006, size=n_w)
            promo_share = np.clip(r.normal(0.18 if banner == KRM else 0.14, 0.03, size=n_w), 0.05, 0.4)
            if banner == KRM and ci == hero_cat_i:
                # CP2: Fresh & Produce share grows ~8% faster than the store, margin erodes ~2.2 pts over the current window
                sh = sh * (1 + 0.065 * np.clip(tt, 0, 1.5))
                gpc = gpc - 0.022 * np.clip((tt - 0.5) / 1.0, 0, 1)
                summer = np.array([(date(2026, 6, 15) <= w <= date(2026, 8, 9)) for w in weeks])
                sh = np.where(summer, sh * 1.30, sh)
                gpc = np.where(summer, gpc - 0.045, gpc)
                promo_share = np.where(summer, 0.55, promo_share)
            sales = tot * sh
            cogs = sales * (1 - gpc)
            units_price = {KRM: 28.0, TRG: 34.0, GRH: 31.0}[banner] * (3.5 if nonfood[ci] else 1.0) * (0.6 if ci in (dairy_i, bread_i) else 1.0)
            units = np.maximum(1, np.round(sales / units_price * r.normal(1.0, 0.04, size=n_w))).astype(int)
            waste_rate = (np.clip(r.normal(0.032, 0.005, size=n_w), 0.015, 0.06) if fresh[ci] else np.clip(r.normal(0.005, 0.0015, size=n_w), 0.001, 0.012)) * p["waste_f"]
            md_rate = np.clip(r.normal(0.018 if fresh[ci] else 0.009, 0.003, size=n_w), 0.002, 0.05) * p["markdown_f"]
            osa = osa_base + r.normal(0, 0.005, size=n_w) + (-0.008 if ci in (dairy_i, bread_i) else 0) + (0.008 if not fresh[ci] else 0)
            if p["low_osa"] and ci in (dairy_i, bread_i):
                osa = osa - 0.015
            if store_id == ids["hero"] and nonfood[ci]:
                osa = osa - 0.03
            osa = np.clip(osa, 0.80, 0.995)
            stockout_h = (1 - osa) * sku_per_cat[ci] * 98.0 * r.normal(1.0, 0.1, size=n_w)
            inv_days = np.clip(r.normal(6 if fresh[ci] else (45 if nonfood[ci] else 18), 1.5, size=n_w), 2, 90)
            rows.append(pd.DataFrame(dict(store_id=store_id, week_start_date=weeks, category_id=cat_id[cname], net_sales_sek=np.round(sales, 2),
                                          cogs_sek=np.round(cogs, 2), gross_profit_sek=np.round(sales - cogs, 2), units_sold=units,
                                          promo_sales_sek=np.round(sales * promo_share, 2), markdown_sek=np.round(sales * md_rate, 2),
                                          waste_sek=np.round(cogs * waste_rate, 2), waste_units=np.round(units * waste_rate * 1.1).astype(int),
                                          on_shelf_availability_pct=np.round(osa, 4), stockout_hours=np.round(stockout_h, 1), inventory_days=np.round(inv_days, 1))))
        frames.append(pd.concat(rows, ignore_index=True))
    weekly = pd.concat(frames, ignore_index=True)
    # daily gross profit from the week's category mix
    wk_gp = weekly.groupby(["store_id", "week_start_date"], as_index=False).agg(gp=("gross_profit_sek", "sum"), ns=("net_sales_sek", "sum"))
    wk_gp["gp_pct"] = wk_gp.gp / wk_gp.ns
    d = d.merge(wk_gp[["store_id", "week_start_date", "gp_pct"]], on=["store_id", "week_start_date"], how="left")
    r = rng("daily_gp")
    d["gross_profit_sek"] = np.round(d.net_sales_sek * d.gp_pct * r.normal(1.0, 0.01, size=len(d)), 2)
    daily_out = d.drop(columns=["week_start_date", "gp_pct"])
    return weekly, daily_out


# ---------------------------------------------------------------- costs
def build_costs(cal: pd.DataFrame, stores: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    month_of = dict(zip(cal.calendar_date, cal.month_start_date))
    d = daily.assign(month_start_date=daily.calendar_date.map(month_of))
    m = d.groupby(["store_id", "month_start_date"], as_index=False).agg(ns=("net_sales_sek", "sum"), days=("calendar_date", "count"))
    m = m.merge(stores[["store_id", "banner", "sales_area_sqm"]], on="store_id")
    r = rng("costs")
    rows = []
    for x in m.itertuples(index=False):
        prog = np.clip(((x.month_start_date - date(2026, 1, 1)).days) / 200.0, 0, 1)   # Grosshallen structural measures Jan-Jul 2026
        if x.banner == GRH:
            labour = 0.135 - 0.023 * prog
            other = 0.025 - 0.005 * prog
            occ_sqm = 118.0
            logistics, marketing, dep = 0.021, 0.010, 0.016
        elif x.banner == KRM:
            labour, other, occ_sqm, logistics, marketing, dep = 0.097, 0.018, 95.0, 0.020, 0.009, 0.013
        else:
            labour, other, occ_sqm, logistics, marketing, dep = 0.122, 0.020, 160.0, 0.024, 0.011, 0.012
        n = r.normal(1.0, 0.02)
        lab = x.ns * labour * n
        rows.append(dict(store_id=x.store_id, month_start_date=x.month_start_date, labour_cost_sek=round(lab, 2),
                         occupancy_cost_sek=round(x.sales_area_sqm * occ_sqm * (x.days / 30.0) * r.normal(1.0, 0.03), 2),
                         logistics_cost_sek=round(x.ns * logistics * r.normal(1.0, 0.03), 2), marketing_cost_sek=round(x.ns * marketing * r.normal(1.0, 0.08), 2),
                         other_opex_sek=round(x.ns * other * r.normal(1.0, 0.05), 2), depreciation_sek=round(x.ns * dep, 2),
                         fte=round(lab / 48000.0, 1), labour_hours=round(lab / 48000.0 * 150.0, 1)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- promotions
def build_promotions(cats: pd.DataFrame) -> pd.DataFrame:
    r = rng("promotions")
    cat_id = dict(zip(cats.category_name, cats.category_id))
    food = [c[0] for c in CATEGORIES if not c[7]]
    mech = ["Price cut", "Multibuy", "Loyalty price", "Bundle", "Clearance"]
    names = {"Price cut": ["Veckans pris", "Lågpris", "Storpack"], "Multibuy": ["3 för 2", "Ta 2 betala 1", "Flerpack"], "Loyalty price": ["Medlemspris", "Klubbpris", "Kortpris"],
             "Bundle": ["Helgpaket", "Fredagsmys", "Grillpaket"], "Clearance": ["Utförsäljning", "Rensning", "Kort datum"]}
    rows = []
    pid = 0
    for banner in (KRM, TRG, GRH):
        for _ in range({KRM: 26, TRG: 18, GRH: 15}[banner]):
            pid += 1
            m = str(r.choice(mech, p=[0.32, 0.22, 0.2, 0.16, 0.10]))
            cat = str(r.choice(food))
            start = START + timedelta(days=int(r.integers(14, 690)))
            weeks = int(r.integers(2, 7))
            rows.append(dict(promotion_id=f"PRM-{pid:03d}", promotion_name=f"{r.choice(names[m])} {cat} {start.strftime('%b %Y')}", banner=banner, category_name=cat,
                             mechanic=m, discount_pct=round(float({"Price cut": r.uniform(0.15, 0.3), "Multibuy": r.uniform(0.25, 0.4), "Loyalty price": r.uniform(0.1, 0.2),
                                                                  "Bundle": r.uniform(0.1, 0.2), "Clearance": r.uniform(0.3, 0.5)}[m]), 3),
                             start_date=start, end_date=start + timedelta(days=weeks * 7 - 1), weeks=weeks,
                             funding_source=str(r.choice(["Supplier", "Retailer", "Shared"], p=[0.4, 0.3, 0.3])), is_loyalty_only=(m == "Loyalty price"),
                             objective=str(r.choice(["Traffic", "Basket", "Clearance", "Margin", "Loyalty acquisition"])), owner=str(r.choice(CATEGORY_MANAGERS))))
    pid += 1
    rows.append(dict(promotion_id=f"PRM-{pid:03d}", promotion_name=HERO_PROMOTION, banner=KRM, category_name=HERO_CATEGORY, mechanic="Price cut", discount_pct=0.30,
                     start_date=date(2026, 6, 15), end_date=date(2026, 8, 9), weeks=8, funding_source="Retailer", is_loyalty_only=False, objective="Traffic", owner="Anna Bergström"))
    df = pd.DataFrame(rows)
    df["banner_id"] = df.banner.map({b: v["banner_id"] for b, v in BANNERS.items()})
    df["category_id"] = df.category_name.map(cat_id)
    df["supplier_funding_pct"] = df.funding_source.map({"Supplier": 0.8, "Shared": 0.45, "Retailer": 0.0})
    return df[["promotion_id", "promotion_name", "banner_id", "banner", "category_id", "category_name", "mechanic", "discount_pct", "start_date", "end_date", "weeks",
               "funding_source", "supplier_funding_pct", "is_loyalty_only", "objective", "owner"]]


def build_promotion_results(promos: pd.DataFrame, stores: pd.DataFrame, weekly: pd.DataFrame) -> pd.DataFrame:
    r = rng("promo_results")
    wk_avg = weekly.groupby(["store_id", "category_id"], as_index=False).agg(ns=("net_sales_sek", "mean"), gp=("gross_profit_sek", "mean"))
    wk_avg["gp_pct"] = wk_avg.gp / wk_avg.ns
    avg = {(a, b): (c, d) for a, b, c, d in wk_avg[["store_id", "category_id", "ns", "gp_pct"]].itertuples(index=False)}
    rows = []
    for p in promos.itertuples(index=False):
        is_hero = p.promotion_name == HERO_PROMOTION
        if is_hero:
            uplift_c, dil_c = 0.52, 0.075
        else:
            uplift_c = {"Price cut": r.uniform(0.18, 0.34), "Multibuy": r.uniform(0.22, 0.45), "Loyalty price": r.uniform(0.08, 0.2), "Bundle": r.uniform(0.12, 0.26), "Clearance": r.uniform(0.3, 0.48)}[p.mechanic]
            dil_c = {"Price cut": r.uniform(0.02, 0.055), "Multibuy": r.uniform(0.03, 0.06), "Loyalty price": r.uniform(0.005, 0.025), "Bundle": r.uniform(0.01, 0.03), "Clearance": r.uniform(0.04, 0.065)}[p.mechanic]
            if p.funding_source == "Supplier":
                dil_c *= 0.5
        for s in stores[(stores.banner == p.banner) & (stores.opened_date <= p.start_date) & (stores.closed_date.isna() | (stores.closed_date > p.end_date))].itertuples(index=False):
            base_ns, base_gp = avg.get((s.store_id, p.category_id), (50000.0, 0.27))
            baseline = base_ns * p.weeks * r.normal(1.0, 0.05)
            uplift = max(-0.1, uplift_c + r.normal(0, 0.05))
            promo_sales = baseline * (1 + uplift)
            dil = max(0.0, dil_c + r.normal(0, 0.008))
            promo_gp = base_gp - dil
            rows.append(dict(promotion_id=p.promotion_id, store_id=s.store_id, promo_sales_sek=round(promo_sales, 2), baseline_sales_sek=round(baseline, 2),
                             uplift_pct=round(uplift, 3), promo_gp_pct=round(promo_gp, 3), baseline_gp_pct=round(base_gp, 3), margin_dilution_pts=round(dil, 3),
                             markdown_cost_sek=round(promo_sales * p.discount_pct * (1 - p.supplier_funding_pct) * 0.6, 2),
                             incremental_gp_sek=round(promo_sales * promo_gp - baseline * base_gp, 2), promo_units=int(promo_sales / 26.0)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- loyalty
def build_loyalty(cal: pd.DataFrame, stores: pd.DataFrame, params: dict, daily: pd.DataFrame) -> pd.DataFrame:
    month_of = dict(zip(cal.calendar_date, cal.month_start_date))
    d = daily.assign(month_start_date=daily.calendar_date.map(month_of))
    m = d.groupby(["store_id", "month_start_date"], as_index=False).agg(tx=("transactions", "sum"), ns=("net_sales_sek", "sum"))
    m = m.merge(stores[["store_id", "banner", "catchment_type"]], on="store_id")
    rows = []
    ids = params["_ids"]
    for store_id, grp in m.groupby("store_id"):
        p = params[store_id]
        r = rng(f"loyalty:{store_id}")
        mix = np.array(SEGMENT_MIX[grp.catchment_type.iloc[0]]) * r.normal(1.0, 0.08, size=len(SEGMENTS))
        mix /= mix.sum()
        loy_share = {KRM: 0.62, TRG: 0.55, GRH: 0.50}[p["banner"]]
        for x in grp.itertuples(index=False):
            tt = (x.month_start_date - date(2025, 4, 1)).days / 365.0
            basket = x.ns / max(x.tx, 1)
            for si, seg in enumerate(SEGMENTS):
                trend = 1.0
                if seg == HERO_SEGMENT:
                    trend = (1 + p["families_trend"]) ** tt if store_id != ids["hero"] else (1 + (-0.04)) ** tt
                    if store_id == ids["hero"] and x.month_start_date >= date(2026, 3, 1):
                        trend *= 0.80
                visits = x.tx * loy_share * mix[si] * trend * r.normal(1.0, 0.03)
                members = visits / SEGMENT_FREQ[seg] * r.normal(1.0, 0.03)
                spend = visits * basket * SEGMENT_BASKET[seg] * r.normal(1.0, 0.03)
                rows.append(dict(store_id=store_id, month_start_date=x.month_start_date, segment=seg, active_members=int(members), visits=int(visits),
                                 spend_sek=round(spend, 2), new_members=int(members * r.uniform(0.015, 0.035)),
                                 lapsed_members=int(members * (r.uniform(0.02, 0.04) + (0.03 if trend < 0.95 else 0))),
                                 avg_visits_per_member=round(visits / max(members, 1), 2)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- assortment
def build_assortment(cal: pd.DataFrame, stores: pd.DataFrame, params: dict, cats: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    months = sorted(cal[cal.is_in_data_window].month_start_date.unique())
    month_of = dict(zip(cal.calendar_date, cal.month_start_date))
    open_months = daily.assign(m=daily.calendar_date.map(month_of)).groupby("store_id").m.unique().to_dict()
    cat_names = [c[0] for c in CATEGORIES]
    cat_id = dict(zip(cats.category_name, cats.category_id))
    base_skus = dict(zip(cat_names, [420, 260, 180, 240, 90, 220, 160, 300, 380, 520, 700, 420, 300, 140, 120, 90, 60, 60, 50, 25, 30, 30, 25]))
    fmt_f = {KRM: 0.75, TRG: 0.95, GRH: 1.6}
    rows = []
    for s in stores.itertuples(index=False):
        p = params[s.store_id]
        r = rng(f"assort:{s.store_id}")
        for cname in cat_names:
            nonfood = dict((c[0], c[7]) for c in CATEGORIES)[cname]
            if nonfood and s.banner != GRH:
                continue
            listed = int(base_skus[cname] * fmt_f[s.banner] * r.normal(1.0, 0.08))
            pl = float(np.clip(p["pl_share"] + r.normal(0, 0.03) + (-0.08 if nonfood else 0), 0.02, 0.6))
            for mth in months:
                if mth not in open_months.get(s.store_id, []):
                    continue
                drift = r.integers(-3, 4)
                rows.append(dict(store_id=s.store_id, month_start_date=mth, category_id=cat_id[cname], listed_skus=listed + int(drift),
                                 private_label_skus=int((listed + drift) * pl * 0.9), pl_sales_share=round(float(np.clip(pl + r.normal(0, 0.008), 0.01, 0.7)), 4),
                                 new_skus=int(r.integers(0, 6)), delisted_skus=int(r.integers(0, 5)), range_depth_index=round(float(r.normal(1.0, 0.08)), 3)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- competitor events
def build_competitor_events(stores: pd.DataFrame, params: dict) -> pd.DataFrame:
    r = rng("competitors")
    ids = params["_ids"]
    rows = [dict(event_id="CEV-001", store_id=ids["hero"], event_date=COMPETITOR_OPENED, competitor_name=COMPETITOR_NAME, competitor_format="Discount", event_type="Opening",
                 distance_km=COMPETITOR_DISTANCE_KM, estimated_sales_impact_pct=-0.09,
                 notes="New Billigmat discount store opened 1.1 km from Grosshallen Vasterhamn with an aggressive opening campaign on fresh and dairy. Family shoppers switching their weekly shop.")]
    comparable = [s for s in stores[stores.is_lfl_comparable].store_id if s != ids["hero"]]
    for i, s in enumerate(r.choice(comparable, size=72, replace=False), 2):
        comp, fmt = COMPETITORS[int(r.integers(len(COMPETITORS)))]
        et = str(r.choice(["Opening", "Closure", "Price campaign", "Refurbishment"], p=[0.4, 0.15, 0.3, 0.15]))
        impact = {"Opening": -r.uniform(0.02, 0.06), "Closure": r.uniform(0.02, 0.05), "Price campaign": -r.uniform(0.005, 0.02), "Refurbishment": -r.uniform(0.005, 0.015)}[et]
        rows.append(dict(event_id=f"CEV-{i:03d}", store_id=s, event_date=START + timedelta(days=int(r.integers(0, 700))), competitor_name=comp, competitor_format=fmt,
                         event_type=et, distance_km=round(float(r.uniform(0.3, 3.5)), 2), estimated_sales_impact_pct=round(float(impact), 3),
                         notes=f"{comp} {et.lower()} reported by the regional manager."))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- non-food (Teradata-keyed)
def _ref(name: str) -> pd.DataFrame:
    p = REF_DIR / f"{name}.csv"
    if not p.exists():
        raise FileNotFoundError(f"{p} missing — run demos/nordmark/ref_extract.py first (reads Ali's Teradata through Wisdom)")
    return pd.read_csv(p)


def late_suppliers() -> list[int]:
    """The LATE_SUPPLIER_COUNT suppliers with the highest average days late in the Teradata purchase-order lines."""
    po = _ref("rtl_supplier_po_summary")
    po = po[po.po_lines >= 500].sort_values("avg_days_late", ascending=False)
    return [int(k) for k in po.supplier_key.head(LATE_SUPPLIER_COUNT)]


def build_nonfood_assortment(cats: pd.DataFrame) -> pd.DataFrame:
    r = rng("nonfood_assortment")
    prod = _ref("rtl_dim_product")
    prod = prod[prod.department.isin(TD_DEPT_TO_CATEGORY)].copy()
    late = late_suppliers()
    picked = []
    for sk in late:
        pool = prod[prod.supplier_key == sk]
        picked.append(pool.sample(n=min(LATE_SUPPLIER_SKUS, len(pool)), random_state=int(r.integers(1 << 30))))
    chosen = pd.concat(picked)
    rest = prod[~prod.product_key.isin(chosen.product_key)]
    need = NONFOOD_SKU_COUNT - len(chosen)
    per_dept = pd.concat([g.sample(n=max(1, int(round(need * len(g) / len(rest)))), random_state=int(r.integers(1 << 30)))
                          for _, g in rest.groupby("department")])
    chosen = pd.concat([chosen, per_dept]).drop_duplicates("product_key").head(NONFOOD_SKU_COUNT)
    cat_id = dict(zip(cats.category_name, cats.category_id))
    rows = []
    for x in chosen.sort_values("product_key").itertuples(index=False):
        cname = TD_DEPT_TO_CATEGORY[x.department]
        rows.append(dict(product_key=int(x.product_key), sku=x.sku, product_name=x.product_name, teradata_department=x.department, category_id=cat_id[cname], category_name=cname,
                         subcategory=x.subcategory, brand=x.brand, is_private_label=bool(int(x.is_private_label)), supplier_key=int(x.supplier_key), price_tier=x.price_tier,
                         list_price_sek=round(float(x.list_price) * 10.5, 2), unit_cost_sek=round(float(x.unit_cost) * 10.5, 2),
                         listed_since=HYPERMARKET_ACQUIRED if r.random() < 0.8 else date(2025, 9, 1), range_role="Seasonal" if int(x.is_seasonal) else "Core", stores_listed=38))
    return pd.DataFrame(rows)


def build_nonfood_availability(cal: pd.DataFrame, stores: pd.DataFrame, params: dict, nonfood: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    month_of = dict(zip(cal.calendar_date, cal.month_start_date))
    open_months = daily.assign(m=daily.calendar_date.map(month_of)).groupby("store_id").m.unique().to_dict()
    late = set(late_suppliers())
    ids = params["_ids"]
    gh = stores[stores.banner == GRH]
    months = sorted(cal[cal.is_in_data_window].month_start_date.unique())
    frames = []
    for s in gh.itertuples(index=False):
        r = rng(f"nonfood:{s.store_id}")
        size_f = s.sales_area_sqm / 7000.0
        for mth in months:
            if mth not in open_months.get(s.store_id, []) or mth < HYPERMARKET_ACQUIRED:
                continue
            season = 1.6 if mth.month in (11, 12) else (0.85 if mth.month in (1, 2) else 1.0)
            late_mask = nonfood.supplier_key.isin(late).to_numpy()
            tier_f = nonfood.price_tier.map({"Value": 1.4, "Mid": 1.0, "Premium": 0.6}).to_numpy()
            demand = 9.0 * size_f * season * tier_f * r.normal(1.0, 0.25, size=len(nonfood))
            osa = np.where(late_mask, r.normal(0.85 if mth >= date(2026, 1, 1) else 0.88, 0.04, size=len(nonfood)), r.normal(0.97, 0.015, size=len(nonfood)))
            if s.store_id == ids["hero"]:
                osa = osa - 0.03
            if s.store_id == ids["peer"]:
                osa = osa + 0.01
            osa = np.clip(osa, 0.55, 0.995)
            units = np.maximum(0, np.round(demand * osa)).astype(int)
            sales = units * nonfood.list_price_sek.to_numpy()
            lost = demand * (1 - osa) * nonfood.list_price_sek.to_numpy() * 0.7
            days = 26
            frames.append(pd.DataFrame(dict(store_id=s.store_id, month_start_date=mth, product_key=nonfood.product_key.to_numpy(), units_sold=units,
                                            net_sales_sek=np.round(sales, 2), on_shelf_availability_pct=np.round(osa, 4),
                                            stockout_days=np.round(days * (1 - osa)).astype(int), lost_sales_sek=np.round(lost, 2))))
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------- neighbourhood potential (needs sales)
def fill_potential(nbhs: pd.DataFrame, stores: pd.DataFrame, params: dict, cal: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    bucket = dict(zip(cal.calendar_date, cal.rolling_12m_bucket))
    d = daily.assign(b=daily.calendar_date.map(bucket))
    cur = d[d.b == "R12_CUR"].groupby("store_id").net_sales_sek.sum()
    r = rng("potential")
    out = nbhs.set_index("neighborhood_id")
    for s in stores.itertuples(index=False):
        p = params[s.store_id]
        sales = float(cur.get(s.store_id, p["base_msek"] * 1e6))
        if not s.is_lfl_comparable:
            sales = p["base_msek"] * 1e6
        potential = sales / p["potential_index"]
        comp = int(out.at[s.neighborhood_id, "competitor_count_2km"])
        fair = float(np.clip(0.42 - 0.035 * comp + r.normal(0, 0.02), 0.15, 0.5)) * {KRM: 1.0, TRG: 0.7, GRH: 1.15}[s.banner]
        out.at[s.neighborhood_id, "fair_share_pct"] = round(fair, 3)
        out.at[s.neighborhood_id, "catchment_potential_msek"] = round(potential / 1e6, 2)
        out.at[s.neighborhood_id, "grocery_spend_potential_msek"] = round(potential / 1e6 / fair, 2)
    hero = stores[stores.store_name == HERO_STORE].iloc[0]
    out.at[hero.neighborhood_id, "discount_competitor_flag"] = True
    out.at[hero.neighborhood_id, "competitor_count_2km"] = max(int(out.at[hero.neighborhood_id, "competitor_count_2km"]), 3)
    out.at[hero.neighborhood_id, "nearest_competitor_km"] = COMPETITOR_DISTANCE_KM
    return out.reset_index()


# ---------------------------------------------------------------- campaigns and forecasts (Revision 2: the Kampanjrapport)
# CP7  Kronmat week 2026-W36 (four campaigns, 28 article rows): the chain's own purchase forecast (Köpt prognos)
#      lands +18% over actual sales, the CatBoost sold forecast +6%.
# CP8  The chain plan over-forecasts Multiköp 3 för 2 on perishables (bias >= +25%) while other tactics stay
#      <= +10%; perishables carry >= 60% of the absolute error; Grosshallen Vasterhamn is the worst store
#      (>= +35% over-forecast after the Billigmat opening) and Nordstaden sits in the best quartile.
# CP9  Over-forecast costs margin: Q3 2026 between SEK 9m and 15m on the ILLUSTRATIVE cost table, >= 55% of it
#      perishable waste; Kronmat Multiköp is the largest chain x tactic share.
# CP10 Upcoming perishable Multiköp campaigns (weeks 2026-W41..W44) have a chain forecast > 15% above CatBoost.
# CP11 Torghallen "Äpplen & Päron" week 2026-W42: proposed purchase cut 15-22% in whole cases rounded to layers.
HERO_CAMPAIGN_WEEK = "2026-W36"
HERO_CAMPAIGN = "Höstskörd 3 för 2"
HERO_TACTIC = "Multiköp 3 för 2"
DRAFT_CAMPAIGN = "Äpplen & Päron"
DRAFT_WEEK = "2026-W42"
ARTICLE_COUNT = 1200
COST_SOURCE_LABEL = "ILLUSTRATIV - finanssystem ej migrerat"
PERISHABLE_CATS = {c[0] for c in CATEGORIES if c[2]}
CAMPAIGN_CATS = [c[0] for c in CATEGORIES if not c[7]]
TACTICS = {"PN": "Prisnedsättning", "MK": "Multiköp 3 för 2", "MP": "Medlemspris", "HP": "Halva priset", "KU": "Kupong"}
TACTIC_SUFFIX = {"PN": "Veckans pris", "MK": "3 för 2", "MP": "Medlemspris", "HP": "Halva priset", "KU": "Kupong"}
TACTIC_DISCOUNT = {"PN": 0.20, "MK": 1 / 3, "MP": 0.15, "HP": 0.50, "KU": 0.25}
TACTIC_UPLIFT = {"PN": 1.6, "MK": 2.2, "MP": 1.3, "HP": 2.6, "KU": 1.2}
TACTIC_P = [0.35, 0.25, 0.17, 0.13, 0.10]
# chain-plan (Köpt prognos) bias versus actual by tactic: (perishable (mean, sd), dry (mean, sd))
KOPT_BIAS = {"PN": ((0.08, 0.06), (0.05, 0.06)), "MK": ((0.31, 0.08), (0.11, 0.06)), "MP": ((0.05, 0.05), (0.03, 0.05)),
             "HP": ((0.09, 0.06), (0.06, 0.06)), "KU": ((0.04, 0.05), (0.02, 0.05))}
CATBOOST_BIAS = (0.05, 0.07)
PER_STORE_UNITS = {"Fresh & Produce": 180, "Dairy": 220, "Bread & Bakery": 150, "Meat & Poultry": 90, "Fish & Seafood": 40, "Deli & Charcuterie": 70,
                   "Ready Meals": 80, "Frozen": 60, "Beverages": 120, "Snacks & Confectionery": 110, "Pantry Staples": 90, "Health & Beauty": 30,
                   "Household & Cleaning": 40, "Baby & Child": 20, "Pet": 25, "Beer & Cider": 70, "Flowers & Garden": 25}
BANNER_VOLUME = {KRM: 1.0, TRG: 0.45, GRH: 1.6}
VOLUME_SCALE = 0.55                      # tunes CP9 (Q3 2026 margin cost between SEK 9m and 15m)
KRM_MK_Q3_WEEKS = {date(2026, 8, 10): ("Skolstart", ["Dairy", "Bread & Bakery"])}   # CP9: Kronmat Multiköp is the largest cost share in Q3 2026
PL_BRANDS = ["Nordmark", "Nordmark", "Nordmark", "Nordmark Eko"]
CATALOGUE = {  # category: (national brand, bases, sizes, (price min, price max), unit, shelf life range, kolli range)
    "Fresh & Produce": ("Gröna Gården", ["Äpplen Royal Gala", "Päron Conference", "Bananer", "Gurka", "Tomater kvist", "Potatis fast", "Morötter", "Gul lök", "Röd paprika",
                                         "Avokado", "Citroner", "Apelsiner", "Vindruvor gröna", "Blåbär", "Jordgubbar", "Isbergssallad", "Broccoli", "Blomkål", "Champinjoner",
                                         "Purjolök", "Rödbetor", "Palsternacka", "Kålrot", "Vitkål", "Plommon", "Clementiner", "Kiwi", "Mango", "Ingefära", "Vitlök"],
                        ["1 kg", "500 g", "2 kg", "250 g", "lösvikt", "3-pack"], (12, 60), "kg", (5, 12), (8, 12)),
    "Dairy": ("Fjällmejeriet", ["Mellanmjölk 1,5%", "Standardmjölk 3%", "Lättmjölk 0,5%", "Filmjölk 3%", "Yoghurt naturell", "Grekisk yoghurt 10%", "Smör normalsaltat",
                                "Bordsmargarin", "Crème fraiche 34%", "Vispgrädde 40%", "Matlagningsgrädde 15%", "Kvarg vanilj", "Hushållsost 26%", "Prästost lagrad",
                                "Keso 4%", "Ägg frigående", "Havredryck", "Laktosfri mellanmjölk", "Kefir", "Riven ost"],
              ["1 l", "1,5 l", "500 g", "1 kg", "250 g", "12-pack", "200 g", "3 dl"], (10, 95), "st", (10, 30), (6, 12)),
    "Bread & Bakery": ("Gårdsbageriet", ["Rågbröd", "Formfranska", "Grovt lantbröd", "Kanelbullar", "Tunnbröd", "Knäckebröd råg", "Baguette", "Hamburgerbröd", "Korvbröd",
                                         "Sirapslimpa", "Fullkornsbröd", "Pitabröd", "Croissanter", "Wienerbröd", "Kardemummabullar", "Surdegsbröd", "Tekakor", "Pepparkakor",
                                         "Skorpor", "Muffins"], ["500 g", "750 g", "6-pack", "8-pack", "10-pack", "4-pack", "400 g"], (15, 65), "st", (3, 7), (6, 10)),
    "Meat & Poultry": ("Svea Kött", ["Kycklingfilé", "Kycklinglårfilé", "Nötfärs 10%", "Blandfärs", "Fläskkarré", "Fläskfilé", "Högrev", "Entrecôte", "Bacon", "Falukorv",
                                     "Prinskorv", "Grillkorv", "Kycklingvingar", "Lammstek", "Kalkonbröst", "Köttbullar", "Hamburgare", "Fläskkotlett", "Rostbiff", "Kassler"],
                       ["1 kg", "500 g", "800 g", "300 g", "2 kg", "400 g", "10-pack"], (35, 220), "st", (5, 10), (6, 10)),
    "Fish & Seafood": ("Västkustens Fisk", ["Laxfilé", "Torskrygg", "Räkor skalade", "Sillinläggning", "Kallrökt lax", "Fiskpinnar", "Sejfilé", "Gravad lax", "Musslor",
                                            "Fiskbullar", "Tonfisk i vatten", "Makrill i tomatsås", "Kräftstjärtar", "Rödingfilé", "Laxburgare"],
                       ["400 g", "500 g", "250 g", "1 kg", "200 g", "3-pack"], (25, 190), "st", (3, 8), (6, 12)),
    "Deli & Charcuterie": ("Skärgårdsdeli", ["Skinka skivad", "Salami", "Leverpastej", "Rökt kalkon", "Prosciutto", "Potatissallad", "Hummus", "Oliver", "Fetaost", "Mozzarella",
                                             "Brieost", "Chorizo", "Pastrami", "Rostbiff skivad", "Tzatziki"], ["120 g", "150 g", "200 g", "300 g", "400 g", "100 g"], (18, 85), "st", (14, 35), (8, 16)),
    "Ready Meals": ("Hemlagat", ["Lasagne", "Pytt i panna", "Kycklinggryta", "Pastasallad", "Köttbullar med mos", "Chili con carne", "Pad thai", "Pizza margherita", "Tomatsoppa",
                                 "Sushi 8 bitar", "Wrap kyckling", "Falafelbox", "Dumplings", "Risotto svamp", "Fiskgratäng"], ["400 g", "350 g", "450 g", "1 port", "2 port", "500 g"], (32, 89), "st", (7, 14), (6, 12)),
    "Frozen": ("Frysta Favoriter", ["Gröna ärtor", "Pommes frites", "Fiskgratäng", "Jordgubbar frysta", "Glass vanilj", "Pizza kebab", "Kycklingnuggets", "Broccoli fryst",
                                    "Hallon frysta", "Isglass", "Wokgrönsaker", "Blåbär frysta", "Köttfärssås", "Vårrullar", "Ugnspannkaka"], ["500 g", "1 kg", "750 g", "2 l", "6-pack", "400 g"], (20, 75), "st", (180, 540), (6, 12)),
    "Beverages": ("Nordisk Dryck", ["Läsk cola", "Mineralvatten citron", "Apelsinjuice", "Äppeljuice", "Kaffe mellanrost", "Te Earl Grey", "Energidryck", "Saft hallon",
                                    "Kaffe mörkrost", "Kakao", "Lingondryck", "Iste persika", "Kolsyrat vatten", "Smoothie mango", "Havredryck barista"],
                  ["1,5 l", "33 cl 6-pack", "1 l", "450 g", "20-pack", "50 cl", "2 l"], (12, 95), "l", (120, 540), (6, 24)),
    "Snacks & Confectionery": ("Godisgruvan", ["Chips sourcream", "Ostbågar", "Mjölkchoklad", "Lösgodis", "Salta pinnar", "Popcorn", "Nötmix", "Lakrits", "Chokladkaka hasselnöt",
                                               "Kex digestive", "Tortillachips", "Geléhallon", "Marsipan", "Kolapåse", "Mintpastiller"], ["200 g", "275 g", "100 g", "150 g", "300 g", "400 g"], (12, 55), "st", (150, 540), (12, 24)),
    "Pantry Staples": ("Skafferiet", ["Pasta spaghetti", "Ris jasmin", "Vetemjöl", "Strösocker", "Havregryn", "Krossade tomater", "Olivolja", "Ketchup", "Senap", "Majonnäs",
                                      "Müsli", "Röda linser", "Kokosmjölk", "Tacoskal", "Buljongtärningar", "Honung", "Jordnötssmör", "Jordgubbssylt", "Svarta bönor", "Couscous"],
                       ["1 kg", "500 g", "2 kg", "400 g", "750 ml", "1 l", "350 g", "5 kg"], (10, 110), "st", (240, 720), (6, 16)),
    "Health & Beauty": ("Hälsohuset", ["Schampo", "Balsam", "Duschkräm", "Tandkräm", "Deodorant", "Handtvål", "Ansiktskräm", "Tandborste", "Rakhyvlar", "Solkräm SPF 30",
                                       "Plåster", "Bomullspads", "Munskölj", "Hårspray", "Läppbalsam"], ["250 ml", "400 ml", "75 ml", "50 ml", "2-pack", "100 st"], (20, 120), "st", (360, 720), (6, 12)),
    "Household & Cleaning": ("Rent Hem", ["Diskmedel", "Tvättmedel", "Allrengöring", "Hushållspapper", "Toalettpapper", "Soppåsar", "Diskborste", "Fönsterputs", "Sköljmedel",
                                          "Disktabletter", "Ugnsrengöring", "Mikrofiberduk", "Fryspåsar", "Aluminiumfolie", "Bakplåtspapper"], ["500 ml", "1 l", "4-pack", "8-pack", "16-pack", "50 st", "30 m"], (15, 130), "st", (360, 720), (4, 12)),
    "Baby & Child": ("Lillen", ["Blöjor stl 4", "Våtservetter", "Välling", "Barnmat burk", "Napp", "Blöjor stl 5", "Barnschampo", "Fruktpuré klämmis", "Barngröt", "Nappflaska"],
                     ["40-pack", "64-pack", "3-pack", "190 g", "600 g", "120 g"], (15, 180), "st", (240, 720), (2, 6)),
    "Pet": ("Tassen", ["Kattmat torr", "Hundmat torr", "Kattsand", "Hundgodis", "Kattmat våt", "Fågelfrö", "Tuggben", "Kattgodis"], ["2 kg", "10 kg", "400 g", "12-pack", "1 kg", "5 kg"], (25, 350), "st", (240, 720), (2, 8)),
    "Beer & Cider": ("Bryggeriet Söder", ["Lager 3,5%", "Folköl ljus", "Cider päron 2,2%", "Alkoholfri IPA", "Veteöl 3,5%", "Cider äpple 2,2%", "Pilsner 3,5%", "Alkoholfri lager"],
                     ["33 cl 6-pack", "50 cl", "33 cl 24-pack"], (12, 150), "st", (120, 360), (4, 6)),
    "Flowers & Garden": ("Blomsterhallen", ["Tulpaner", "Rosor", "Grön krukväxt", "Orkidé", "Hyacint", "Julstjärna", "Kryddväxt basilika", "Pelargon", "Amaryllis", "Snittblommor bukett"],
                         ["10-pack", "7-pack", "12 cm kruka", "1 st", "3-pack"], (25, 199), "st", (4, 8), (5, 10)),
}
THEMES = [  # (theme, categories, allowed months or None)
    ("Fredagsmys", ["Snacks & Confectionery", "Beverages", "Frozen"], None), ("Grillpremiär", ["Meat & Poultry", "Beverages", "Fresh & Produce"], [5, 6, 7, 8]),
    ("Midsommarbord", ["Fish & Seafood", "Dairy", "Fresh & Produce", "Beer & Cider"], [6]), ("Julbord", ["Meat & Poultry", "Fish & Seafood", "Deli & Charcuterie"], [12]),
    ("Påskbord", ["Dairy", "Fish & Seafood", "Snacks & Confectionery"], [3, 4]), ("Skolstart", ["Bread & Bakery", "Dairy", "Pantry Staples"], [8]),
    ("Kräftskiva", ["Fish & Seafood", "Beer & Cider", "Bread & Bakery"], [8]), ("Sportlov", ["Ready Meals", "Snacks & Confectionery", "Frozen"], [2]),
    ("Halloween", ["Snacks & Confectionery", "Beverages"], [10]), ("Lucia", ["Bread & Bakery", "Beverages"], [12]), ("Nyårsfest", ["Deli & Charcuterie", "Beverages", "Snacks & Confectionery"], [12, 1]),
    ("Semmeldagen", ["Bread & Bakery", "Dairy"], [2, 3]), ("Våffeldagen", ["Dairy", "Frozen"], [3]), ("Kanelbullens dag", ["Bread & Bakery"], [10]),
    ("Vinterförråd", ["Pantry Staples", "Frozen", "Household & Cleaning"], [1, 2, 11]), ("Storkok", ["Meat & Poultry", "Pantry Staples", "Fresh & Produce"], [1, 2, 3, 9, 10, 11]),
    ("Mejerivecka", ["Dairy"], None), ("Fruktfest", ["Fresh & Produce"], None), ("Grönsaksvecka", ["Fresh & Produce"], None), ("Brödfest", ["Bread & Bakery"], None),
    ("Köttvecka", ["Meat & Poultry"], None), ("Fiskvecka", ["Fish & Seafood"], None), ("Hemmakväll", ["Ready Meals", "Snacks & Confectionery"], None),
    ("Rent & Fint", ["Household & Cleaning", "Health & Beauty"], None), ("Barnens vecka", ["Baby & Child", "Snacks & Confectionery"], None), ("Husdjursvecka", ["Pet"], None),
]
PLANNERS = ["Linnea Åkerman", "Oskar Lindgren", "Maja Sjöberg", "Hugo Bergman", "Elsa Nyström", "Viktor Holmgren"]
CAMPAIGN_START_WEEK = date(2024, 10, 7)       # first Monday in the data window
LAST_COMPLETE_WEEK = date(2026, 9, 21)        # last ISO week fully before the as-of date (2026-W39)
ONGOING_WEEK = date(2026, 9, 28)              # 2026-W40, running at the as-of date
PLANNED_WEEKS = [date(2026, 10, 5), date(2026, 10, 12), date(2026, 10, 19), date(2026, 10, 26)]   # 2026-W41..W44
# forced perishable Multiköp campaigns in the planned weeks (CP10/CP11): (banner, week, name, category, articles, forecast gap)
PLANNED_MK = [(KRM, PLANNED_WEEKS[0], "Mejerivecka 3 för 2", "Dairy", 24, 0.19), (TRG, PLANNED_WEEKS[1], DRAFT_CAMPAIGN, "Fresh & Produce", 20, 0.21),
              (GRH, PLANNED_WEEKS[2], "Brödfest 3 för 2", "Bread & Bakery", 22, 0.23), (KRM, PLANNED_WEEKS[3], "Köttvecka 3 för 2", "Meat & Poultry", 26, 0.18)]


def _week_label(d: date) -> str:
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _week_id(d: date) -> int:
    iso = d.isocalendar()
    return iso[0] * 100 + iso[1]


def build_artikel(cats: pd.DataFrame) -> pd.DataFrame:
    r = rng("artikel")
    cat_id = dict(zip(cats.category_name, cats.category_id))
    shares = {c[0]: c[3] for c in CATEGORIES if c[0] in CAMPAIGN_CATS}
    tot = sum(shares.values())
    counts = {c: max(8, int(round(ARTICLE_COUNT * s / tot))) for c, s in shares.items()}
    diff = ARTICLE_COUNT - sum(counts.values())
    counts["Pantry Staples"] += diff
    rows, aid = [], 0
    for cat in CAMPAIGN_CATS:
        brand, bases, sizes, (pmin, pmax), unit, shelf, kolli_rng = CATALOGUE[cat]
        seen: set[str] = set()
        made = 0
        while made < counts[cat]:
            name = None
            for _ in range(12):                       # unique brand + product + size without numeric suffixes
                base = str(r.choice(bases)); size = str(r.choice(sizes))
                pl = r.random() < 0.26
                b = str(r.choice(PL_BRANDS)) if pl else brand
                cand = f"{b} {base} {size}"
                if cand not in seen:
                    name = cand
                    break
            if name is None:
                name = f"{cand} {made + 1}"
            seen.add(name)
            aid += 1
            made += 1
            kolli = int(r.integers(kolli_rng[0], kolli_rng[1] + 1))
            lav = int(r.integers(4, 13))
            price = round(float(r.uniform(pmin, pmax)) * (0.85 if pl else 1.0), 2)
            rows.append(dict(artikel_id=f"A-{aid:05d}", artikel_namn=name, category_id=cat_id[cat], kategori=cat, varumarke=b, egna_markesvaror=bool(pl),
                             farskvara=cat in PERISHABLE_CATS, hallbarhet_dagar=int(r.integers(shelf[0], shelf[1] + 1)), enhet=unit, kolli=kolli, lav=lav,
                             pall=lav * int(r.integers(4, 9)), ordinarie_pris_sek=price, status="Utgaende" if r.random() < 0.04 else "Aktiv"))
    return pd.DataFrame(rows)


def _campaign_schedule(r, promos: pd.DataFrame) -> list[dict]:
    """One slot per banner and ISO week; a 2-week campaign occupies two slots. Hero week, the Sommarpris link, the
    ongoing week and the four planned weeks are forced."""
    weeks = []
    d = CAMPAIGN_START_WEEK
    while d <= LAST_COMPLETE_WEEK:
        weeks.append(d); d += timedelta(days=7)
    hero_week = date(2026, 8, 31)
    sommar = promos[promos.promotion_name == HERO_PROMOTION].iloc[0]
    camps = []
    p_start = {KRM: 0.62, TRG: 0.52, GRH: 0.44}
    for banner in (KRM, TRG, GRH):
        busy_until = None
        for w in weeks:
            if busy_until is not None and w <= busy_until:
                continue
            if banner == KRM and w == hero_week:
                for code, n in (("PN", 8), ("MK", 7), ("MP", 7), ("HP", 6)):
                    camps.append(dict(banner=banner, week=w, weeks=1, tactic=code, theme="Höstskörd", cats=["Fresh & Produce", "Dairy", "Bread & Bakery"] if code != "MK" else ["Fresh & Produce"],
                                      n_articles=n, name=HERO_CAMPAIGN if code == "MK" else f"Höstskörd {TACTIC_SUFFIX[code]}", status="Avslutad", promotion_id=None))
                busy_until = w
                continue
            if banner == KRM and w == date(2026, 6, 22):
                camps.append(dict(banner=banner, week=w, weeks=1, tactic="PN", theme="Sommarpris", cats=["Fresh & Produce"], n_articles=36, name="Sommarpris Veckans pris",
                                  status="Avslutad", promotion_id=sommar.promotion_id))
                busy_until = w
                continue
            if banner == KRM and w in KRM_MK_Q3_WEEKS:
                theme, tcats = KRM_MK_Q3_WEEKS[w]
                camps.append(dict(banner=banner, week=w, weeks=1, tactic="MK", theme=theme, cats=list(tcats), n_articles=16,
                                  name=f"{theme} {TACTIC_SUFFIX['MK']}", status="Avslutad", promotion_id=None))
                busy_until = w
                continue
            if r.random() > p_start[banner]:
                continue
            n_weeks = 1 if (w >= hero_week - timedelta(days=7) and banner == KRM) or w == LAST_COMPLETE_WEEK else int(r.choice([1, 2], p=[0.6, 0.4]))
            tactic = str(r.choice(list(TACTICS), p=TACTIC_P))
            month = w.month
            pool = [t for t in THEMES if t[2] is None or month in t[2]]
            theme, tcats, _ = pool[int(r.integers(len(pool)))]
            camps.append(dict(banner=banner, week=w, weeks=n_weeks, tactic=tactic, theme=theme, cats=list(tcats), n_articles=int(r.integers(24, 57)),
                              name=f"{theme} {TACTIC_SUFFIX[tactic]}", status="Avslutad", promotion_id=None))
            busy_until = w + timedelta(days=7 * (n_weeks - 1))
    # ongoing week (W40) and the planned weeks (W41..W44): one campaign per banner and week
    forced = {(b, w): (nm, cat, n, gap) for b, w, nm, cat, n, gap in PLANNED_MK}
    for banner in (KRM, TRG, GRH):
        for w in [ONGOING_WEEK] + PLANNED_WEEKS:
            if (banner, w) in forced:
                nm_, cat, n, gap = forced[(banner, w)]
                camps.append(dict(banner=banner, week=w, weeks=1, tactic="MK", theme=nm_, cats=[cat], n_articles=n, name=nm_, status="Planerad", promotion_id=None, gap=gap))
                continue
            tactic = str(r.choice(["PN", "MP", "HP", "KU"], p=[0.45, 0.25, 0.15, 0.15]))
            pool = [t for t in THEMES if t[2] is None or w.month in t[2]]
            theme, tcats, _ = pool[int(r.integers(len(pool)))]
            camps.append(dict(banner=banner, week=w, weeks=1, tactic=tactic, theme=theme, cats=list(tcats), n_articles=int(r.integers(20, 41)),
                              name=f"{theme} {TACTIC_SUFFIX[tactic]}", status="Pagaende" if w == ONGOING_WEEK else "Planerad", promotion_id=None))
    camps.sort(key=lambda c: (c["week"], c["banner"], c["tactic"]))
    return camps


def _link_promotions(c: dict, promos: pd.DataFrame) -> str | None:
    if c["promotion_id"]:
        return c["promotion_id"]
    start, end = c["week"], c["week"] + timedelta(days=7 * c["weeks"] - 1)
    hit = promos[(promos.banner == c["banner"]) & (promos.category_name == c["cats"][0]) & (promos.start_date <= start) & (promos.end_date >= end)]
    return str(hit.iloc[0].promotion_id) if len(hit) else None


def build_kampanj_and_rows(artikel: pd.DataFrame, stores: pd.DataFrame, promos: pd.DataFrame, cal: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    r = rng("kampanj")
    camps = _campaign_schedule(r, promos)
    week_label = dict(zip(cal.calendar_date, cal.week_label))
    by_cat = {c: artikel[(artikel.kategori == c) & (artikel.status == "Aktiv")].artikel_id.tolist() for c in CAMPAIGN_CATS}
    art = artikel.set_index("artikel_id")
    fruit = artikel[artikel.artikel_namn.str.contains("Äpplen|Päron|Plommon|Clementiner|Apelsiner|Vindruvor|Kiwi|Mango|Bananer", regex=True) & (artikel.kategori == "Fresh & Produce")].artikel_id.tolist()
    used: dict[date, set] = {}
    krows, arows = [], []
    counter: dict[tuple, int] = {}
    for c in camps:
        w = c["week"]
        wk_dates = [w + timedelta(days=7 * i) for i in range(c["weeks"])]
        for d in wk_dates:
            used.setdefault(d, set())
        taken = set().union(*[used[d] for d in wk_dates])
        pool = fruit if c["name"] == DRAFT_CAMPAIGN else [a for cat in c["cats"] for a in by_cat[cat]]
        pool = [a for a in pool if a not in taken]
        if c["name"] == DRAFT_CAMPAIGN:
            pool = [a for a in fruit if a not in taken]
        n = min(c["n_articles"], len(pool))
        chosen = list(r.choice(pool, size=n, replace=False))
        for d in wk_dates:
            used[d].update(chosen)
        key = (w.isocalendar()[0], w.isocalendar()[1], BANNERS[c["banner"]]["banner_id"])
        counter[key] = counter.get(key, 0) + 1
        kid = f"K-{key[0]}-{key[1]:03d}-{key[2]}" + (f"-{counter[key]}" if counter[key] > 1 else "")
        n_stores = int(((stores.banner == c["banner"]) & (stores.opened_date <= w) & (stores.closed_date.isna() | (stores.closed_date > w + timedelta(days=6)))).sum())
        slut = w + timedelta(days=7 * c["weeks"] - 1)
        krows.append(dict(kampanj_id=kid, kampanj_namn=c["name"], kedja=c["banner"], banner_id=BANNERS[c["banner"]]["banner_id"], koncept_kod=f"{BANNERS[c['banner']]['banner_id']}-{c['tactic']}",
                          taktik_typ_kod=c["tactic"], taktik_typ=TACTICS[c["tactic"]], kalender_vecka_id=_week_id(w), vecka_label=_week_label(w),
                          leverans_fran=w, leverans_till=w + timedelta(days=1 if c["weeks"] == 1 else 8), kampanj_start=w, kampanj_slut=slut, antal_veckor=c["weeks"],
                          antal_artiklar=n, promotion_id=_link_promotions(c, promos), tema=c["theme"], ansvarig_planerare=str(r.choice(PLANNERS)), status=c["status"]))
        is_future = w > LAST_COMPLETE_WEEK
        per_art = {}
        for a in chosen:
            row = art.loc[a]
            per = VOLUME_SCALE * PER_STORE_UNITS[row.kategori] * BANNER_VOLUME[c["banner"]] * TACTIC_UPLIFT[c["tactic"]] * (30.0 / max(row.ordinarie_pris_sek, 8.0)) ** 0.35
            per_art[a] = per * float(r.lognormal(0, 0.35))
        bias_draw = {}
        for a in chosen:
            m, sd = KOPT_BIAS[c["tactic"]][0 if art.loc[a].farskvara else 1]
            bias_draw[a] = (float(r.normal(m, sd)), float(r.normal(*CATBOOST_BIAS)))
        for i, d in enumerate(wk_dates):
            for a in chosen:
                row = art.loc[a]
                actual = per_art[a] * n_stores * (1.0 if i == 0 else 0.85) * float(r.normal(1.0, 0.06))
                bk, bc = bias_draw[a]
                if is_future:
                    cb = actual * (1 + bc)
                    if c.get("gap") is not None:
                        kopt = cb * (1 + c["gap"] + float(r.normal(0, 0.02)))
                    elif row.farskvara:
                        kopt = cb * (1 + float(np.clip(r.normal(0.06, 0.04), -0.05, 0.14)))
                    else:
                        kopt = cb * (1 + float(np.clip(r.normal(0.04, 0.04), -0.05, 0.14)))
                    faktisk = None
                else:
                    cb = actual * (1 + bc)
                    kopt = actual * (1 + bk)
                    faktisk = int(round(actual))
                kolli = int(row.kolli)
                kopt_i = int(round(kopt)); cb_i = int(round(cb))
                planerad = int(np.ceil(kopt_i / kolli) * kolli)
                pris = round(float(row.ordinarie_pris_sek) * (1 - TACTIC_DISCOUNT[c["tactic"]]), 2)
                arows.append(dict(nyckel=f"{_week_label(d)}-{a}", kampanj_id=kid, kedja=c["banner"], kalender_vecka_id=_week_id(d), vecka_label=_week_label(d), vecka_start=d,
                                  artikel_id=a, planerad_kvantitet=planerad, sald_prognos_catboost=cb_i, kopt_prognos_kedjan=kopt_i,
                                  levererad_kvantitet=None if faktisk is None else int(round(planerad * float(r.uniform(0.96, 1.0)))),
                                  faktisk_sald=faktisk, kampanjpris_sek=pris, ordinarie_pris_sek=float(row.ordinarie_pris_sek),
                                  kampanjforsaljning_sek=None if faktisk is None else round(faktisk * pris, 2)))
    kampanj = pd.DataFrame(krows)
    rows = pd.DataFrame(arows)
    # CP7: pin the hero week totals — chain plan +18%, CatBoost +6% over actual
    hero = (rows.kedja == KRM) & (rows.vecka_label == HERO_CAMPAIGN_WEEK)
    act = rows.loc[hero, "faktisk_sald"].sum()
    rows.loc[hero, "kopt_prognos_kedjan"] = np.round(rows.loc[hero, "kopt_prognos_kedjan"] * (1.18 * act / rows.loc[hero, "kopt_prognos_kedjan"].sum())).astype(int)
    rows.loc[hero, "sald_prognos_catboost"] = np.round(rows.loc[hero, "sald_prognos_catboost"] * (1.06 * act / rows.loc[hero, "sald_prognos_catboost"].sum())).astype(int)
    kolli = rows.artikel_id.map(art.kolli)
    rows.loc[hero, "planerad_kvantitet"] = (np.ceil(rows.loc[hero, "kopt_prognos_kedjan"] / kolli[hero]) * kolli[hero]).astype(int)
    rows.loc[hero, "levererad_kvantitet"] = np.minimum(rows.loc[hero, "levererad_kvantitet"].astype(float), rows.loc[hero, "planerad_kvantitet"]).astype(int)
    for col in ("levererad_kvantitet", "faktisk_sald"):
        rows[col] = rows[col].astype("Int64")
    rows["kampanjforsaljning_sek"] = rows["kampanjforsaljning_sek"].astype(float)
    return kampanj, rows


def build_kampanj_butik(rows: pd.DataFrame, kampanj: pd.DataFrame, stores: pd.DataFrame, params: dict) -> pd.DataFrame:
    r = rng("kampanj_butik")
    ids = params["_ids"]
    base = {s: params[s]["base_msek"] for s in stores.store_id}
    f_store = {s: float(np.clip(r.normal(0, 0.05), -0.11, 0.11)) for s in stores.store_id}
    f_store[ids["peer"]] = -0.10
    done = rows[rows.faktisk_sald.notna()]
    tot = done.groupby(["kampanj_id", "kalender_vecka_id", "vecka_label", "vecka_start", "kedja"], as_index=False).agg(kopt=("kopt_prognos_kedjan", "sum"), actual=("faktisk_sald", "sum"))
    out = []
    for t in tot.itertuples(index=False):
        w = t.vecka_start
        st = stores[(stores.banner == t.kedja) & (stores.opened_date <= w) & (stores.closed_date.isna() | (stores.closed_date > w + timedelta(days=6)))]
        if st.empty:
            continue
        wts = np.array([base[s] for s in st.store_id], dtype=float); wts /= wts.sum()
        prog = np.round(float(t.kopt) * wts).astype(int)
        g = np.array([1.0 / (1.0 + (0.42 if (s == ids["hero"] and w >= date(2026, 3, 16)) else (0.15 if s == ids["hero"] else f_store[s]))) for s in st.store_id])
        g *= r.normal(1.0, 0.08, size=len(g))
        share = wts * g; share /= share.sum()
        fakt = np.maximum(1, np.round(float(t.actual) * share)).astype(int)
        out.append(pd.DataFrame(dict(kampanj_id=t.kampanj_id, kedja=t.kedja, store_id=st.store_id.to_numpy(), kalender_vecka_id=t.kalender_vecka_id, vecka_label=t.vecka_label,
                                     vecka_start=w, prognos_kvantitet=prog, faktisk_sald=fakt, avvikelse_pct=np.round((prog - fakt) / fakt, 4))))
    return pd.concat(out, ignore_index=True)


def build_artikel_kostnad(artikel: pd.DataFrame, cats: pd.DataFrame) -> pd.DataFrame:
    r = rng("artikel_kostnad")
    gp = dict(zip(cats.category_name, cats.target_gp_pct))
    months = [date(2024, 10, 1)]
    while months[-1] < date(2026, 11, 1):
        y, m = months[-1].year, months[-1].month
        months.append(date(y + (m == 12), 1 if m == 12 else m + 1, 1))
    mi = np.arange(len(months))
    drift = 1 + 0.03 * np.sin(mi / 12 * 2 * np.pi) - 0.012 * np.where(np.array(months) >= date(2026, 1, 1), 1, 0)   # mild seasonality, deflation in 2026
    frames = []
    for a in artikel.itertuples(index=False):
        inkop = a.ordinarie_pris_sek * (1 - gp[a.kategori]) * drift * r.normal(1.0, 0.02, size=len(months))
        lista = a.ordinarie_pris_sek * (1 + 0.01 * np.sin(mi / 12 * 2 * np.pi))
        svinn = 0.0
        if a.farskvara:
            svinn = 0.70 if a.hallbarhet_dagar <= 7 else (0.55 if a.hallbarhet_dagar <= 14 else 0.40)
        frames.append(pd.DataFrame(dict(artikel_id=a.artikel_id, manad=months, inkopspris_sek=np.round(inkop, 2), listpris_sek=np.round(lista, 2),
                                        marginal_pct=np.round(1 - inkop / lista, 4), svinnandel_pct=svinn, kalla=COST_SOURCE_LABEL)))
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------- data dictionary
DICTIONARY = [
    ("V_KPI_STORE_MONTHLY", "net_sales_sek", "NUMBER", "Net sales excluding VAT after discounts and markdowns", "4 812 330.50", "SUM(STORE_DAILY_SALES.net_sales_sek)", "Store Operations", "POS"),
    ("V_KPI_STORE_MONTHLY", "lfl_growth_pct", "NUMBER", "Like-for-like sales growth versus the same month last year for comparable stores only", "-0.0152", "net_sales / ly_net_sales - 1 where is_lfl_comparable", "FP&A", "POS"),
    ("V_KPI_STORE_MONTHLY", "gp_pct", "NUMBER", "Gross margin percent", "0.247", "gross_profit_sek / net_sales_sek", "FP&A", "POS"),
    ("V_KPI_STORE_MONTHLY", "avg_basket_sek", "NUMBER", "Average basket (net sales per transaction)", "518.40", "net_sales_sek / transactions", "Store Operations", "POS"),
    ("V_KPI_STORE_MONTHLY", "transactions", "NUMBER", "Customer receipts in the month", "61 220", "SUM(STORE_DAILY_SALES.transactions)", "Store Operations", "POS"),
    ("V_BANNER_KPI_MONTHLY", "ebit_sek", "NUMBER", "Banner operating result = gross profit minus store operating costs", "-8 120 000", "gross_profit_sek - operating_costs_sek", "FP&A", "SAP"),
    ("V_BANNER_KPI_MONTHLY", "lfl_growth_pct", "NUMBER", "Banner like-for-like growth from comparable stores", "0.015", "SUM comparable net sales / SUM comparable LY net sales - 1", "FP&A", "POS"),
    ("V_STORE_GAP_DECOMPOSITION", "transactions_effect_sek", "NUMBER", "Part of the rolling-12-month sales change explained by the change in transactions at the prior basket", "-9 300 000", "(tx_cur - tx_prior) x basket_prior", "FP&A", "POS"),
    ("V_STORE_GAP_DECOMPOSITION", "basket_effect_sek", "NUMBER", "Part of the sales change explained by the change in average basket at current transactions", "6 100 000", "(basket_cur - basket_prior) x tx_cur", "FP&A", "POS"),
    ("V_PEER_COMPARISON", "cluster_gp_pct", "NUMBER", "Median gross margin percent of the store peer cluster (banner x catchment type)", "0.246", "MEDIAN(gp_pct) over the cluster", "FP&A", "POS"),
    ("V_PEER_COMPARISON", "osa_pct", "NUMBER", "Sales-weighted on-shelf availability over the rolling 12 months", "0.958", "SUM(osa x sales) / SUM(sales)", "Supply Chain", "Relex"),
    ("V_PEER_COMPARISON", "markdown_rate", "NUMBER", "Markdown value as a share of net sales", "0.019", "SUM(markdown_sek) / SUM(net_sales_sek)", "Category Management", "POS"),
    ("V_CATCHMENT_POTENTIAL", "potential_index", "NUMBER", "Rolling-12-month net sales divided by the catchment potential; 1.0 = capturing the expected fair share", "0.62", "sales_r12_sek / (catchment_potential_msek x 1e6)", "Store Development", "Market data provider"),
    ("V_CATCHMENT_POTENTIAL", "potential_gap_sek", "NUMBER", "Catchment potential minus rolling-12-month sales (the SEK opportunity)", "104 000 000", "catchment_potential_msek x 1e6 - sales_r12_sek", "Store Development", "Market data provider"),
    ("V_PROMO_EFFECTIVENESS", "uplift_pct", "NUMBER", "Promotion sales uplift versus the pre-period baseline", "0.52", "promo_sales / baseline_sales - 1", "Category Management", "POS"),
    ("V_PROMO_EFFECTIVENESS", "margin_dilution_pts", "NUMBER", "Gross margin points lost during the campaign versus baseline", "0.075", "baseline_gp_pct - promo_gp_pct", "Category Management", "POS"),
    ("V_AVAILABILITY_VS_SALES", "osa_pct", "NUMBER", "On-shelf availability over the last 13 weeks (target 0.96; alert below 0.94)", "0.905", "SUM(osa x sales) / SUM(sales)", "Supply Chain", "Relex"),
    ("V_LOYALTY_SEGMENT_TRENDS", "visits_change_pct", "NUMBER", "Change in identified loyalty visits rolling 12 months versus prior 12 months", "-0.12", "visits_r12 / visits_prior_r12 - 1", "Loyalty & CRM", "Loyalty CRM"),
    ("V_NONFOOD_AVAILABILITY_BY_SUPPLIER", "lost_sales_sek", "NUMBER", "Estimated non-food sales lost to stockouts", "212 400", "SUM(NONFOOD_AVAILABILITY_MONTHLY.lost_sales_sek)", "Grosshallen Non-food", "Relex"),
    ("V_NONFOOD_AVAILABILITY_BY_SUPPLIER", "supplier_key", "NUMBER", "Supplier key of the import-purchasing platform; join to Teradata wisdomai.RTL_DIM_SUPPLIER and RTL_FACT_PURCHASE_ORDER_LINE", "26", "", "Grosshallen Non-food", "Teradata purchasing"),
    ("STORES", "peer_cluster", "VARCHAR", "Banner x catchment type; the comparison set for every store", "Grosshallen / Suburban family", "", "Store Development", "Store master"),
    ("STORES", "is_lfl_comparable", "BOOLEAN", "Store traded through both rolling-12-month windows", "TRUE", "opened_date < 2024-10-01 AND closed_date IS NULL", "FP&A", "Store master"),
    ("NEIGHBORHOODS", "catchment_potential_msek", "NUMBER", "Expected annual net sales for a store of this format in this catchment", "277.4", "grocery_spend_potential_msek x fair_share_pct", "Store Development", "Market data provider"),
    ("SALES_WEEKLY_STORE_CATEGORY", "on_shelf_availability_pct", "NUMBER", "Share of audited SKU-hours the item was on the shelf", "0.962", "", "Supply Chain", "Relex"),
    ("SALES_WEEKLY_STORE_CATEGORY", "waste_sek", "NUMBER", "Cost value of goods written off", "18 240.00", "", "Store Operations", "Relex"),
    ("LOYALTY_ACTIVITY_MONTHLY", "segment", "VARCHAR", "Customer segment from the loyalty CRM", "Families", "", "Loyalty & CRM", "Loyalty CRM"),
    ("NONFOOD_ASSORTMENT", "product_key", "NUMBER", "Same key as Teradata wisdomai.RTL_DIM_PRODUCT.product_key", "1457", "", "Grosshallen Non-food", "Teradata purchasing"),
    ("COMPETITOR_EVENTS", "estimated_sales_impact_pct", "NUMBER", "Regional manager estimate of the annual sales impact", "-0.09", "", "Store Operations", "Regional manager log"),
    ("STORE_MONTHLY_COSTS", "labour_cost_sek", "NUMBER", "Store labour cost including social charges", "2 310 000", "", "FP&A", "SAP"),
    ("CALENDAR", "rolling_12m_bucket", "VARCHAR", "R12_CUR = 2025-10-01..2026-09-30; R12_PRIOR = 2024-10-01..2025-09-30", "R12_CUR", "", "FP&A", "Calendar"),
    ("V_KAMPANJRAPPORT", "nyckel", "VARCHAR", "Report key (Nyckel) = campaign week label concatenated with the article id; one row per week and article", "2026-W36-A-00012", "vecka_label || '-' || artikel_id", "Campaign Planning", "Campaign mart"),
    ("V_KAMPANJRAPPORT", "sald_prognos_catboost", "NUMBER", "Sold forecast (Såld prognos) from the group's CatBoost demand model for the campaign week", "18 420", "", "Demand Planning", "Forecast feed"),
    ("V_KAMPANJRAPPORT", "kopt_prognos_kedjan", "NUMBER", "Purchase forecast (Köpt prognos, Kedjans prognos) from the chain's own campaign plan; the quantity bought", "21 700", "", "Campaign Planning", "Campaign mart"),
    ("V_KAMPANJRAPPORT", "prognosfel_kedjan_pct", "NUMBER", "Forecast error of the chain plan = (purchase forecast - actual sold) / actual sold; positive = over-forecast", "0.18", "(kopt_prognos_kedjan - faktisk_sald) / faktisk_sald", "Demand Planning", "Campaign mart"),
    ("V_KAMPANJRAPPORT", "prognosfel_catboost_pct", "NUMBER", "Forecast error of the CatBoost sold forecast = (sold forecast - actual sold) / actual sold", "0.06", "(sald_prognos_catboost - faktisk_sald) / faktisk_sald", "Demand Planning", "Forecast feed"),
    ("V_PROGNOSFEL_TAKTIK", "bias_kedjan_pct", "NUMBER", "Chain-plan bias by tactic type = SUM(purchase forecast) / SUM(actual sold) - 1; the tactic grouping is TAKTIK_TYP", "0.31", "SUM(kopt_prognos_kedjan) / SUM(faktisk_sald) - 1", "Demand Planning", "Campaign mart"),
    ("V_KAMPANJ_MARGINALEFFEKT", "marginaleffekt_sek", "NUMBER", "Margin cost of over-forecasting = perishable waste cost + clearance markdown of the remainder. ILLUSTRATIVE: cost prices come from a finance extract that is not yet migrated", "412 300", "svinnkostnad_sek + nedsattningskostnad_sek", "FP&A", "Illustrative cost extract"),
    ("V_KAMPANJ_KOMMANDE", "foreslagen_minskning_kolli", "NUMBER", "Proposed purchase reduction in whole cases (kolli) rounded down to full layers (lav) when the chain forecast exceeds CatBoost by more than 15 percent on a perishable", "96", "FLOOR((kopt - catboost) / kolli / lav) * lav", "Campaign Planning", "Campaign mart"),
    ("ARTIKEL", "kolli", "NUMBER", "Units per case (kolli); lav = cases per layer; pall = cases per pallet", "12", "", "Supply Chain", "Article master"),
    ("ARTIKEL_KOSTNAD_MANAD", "kalla", "VARCHAR", "Source label; always 'ILLUSTRATIV - finanssystem ej migrerat' because purchase cost and margin live in a finance system not yet migrated to the warehouse", "ILLUSTRATIV - finanssystem ej migrerat", "", "FP&A", "Illustrative cost extract"),
    ("KAMPANJ", "kalender_vecka_id", "NUMBER", "Campaign week key (Calendar_Week_Id, YYYYWW) = the ISO week of the first delivery day (leverans_fran)", "202636", "", "Campaign Planning", "Campaign mart"),
]


def build_data_dictionary() -> pd.DataFrame:
    return pd.DataFrame(DICTIONARY, columns=["table_name", "column_name", "data_type", "description", "sample_value", "metric_formula", "business_owner", "source_system"])


# ---------------------------------------------------------------- orchestration
def generate_all() -> dict[str, pd.DataFrame]:
    cal = build_calendar()
    banners = build_banners()
    cats = build_product_categories()
    stores, nbhs, params = build_stores_and_neighborhoods()
    daily = build_store_daily_sales(cal, stores, params)
    weekly, daily = build_weekly(cal, stores, params, daily, cats)
    nbhs = fill_potential(nbhs, stores, params, cal, daily)
    costs = build_costs(cal, stores, daily)
    promos = build_promotions(cats)
    promo_results = build_promotion_results(promos, stores, weekly)
    loyalty = build_loyalty(cal, stores, params, daily)
    assortment = build_assortment(cal, stores, params, cats, daily)
    competitors = build_competitor_events(stores, params)
    nonfood = build_nonfood_assortment(cats)
    nonfood_avail = build_nonfood_availability(cal, stores, params, nonfood, daily)
    # Revision 2: campaigns and forecasts (new rng tags; the builders above are untouched)
    artikel = build_artikel(cats)
    kampanj, kampanj_rows = build_kampanj_and_rows(artikel, stores, promos, cal)
    kampanj_butik = build_kampanj_butik(kampanj_rows, kampanj, stores, params)
    artikel_kostnad = build_artikel_kostnad(artikel, cats)
    return {
        "CALENDAR": cal, "BANNERS": banners, "NEIGHBORHOODS": nbhs, "STORES": stores, "PRODUCT_CATEGORIES": cats, "NONFOOD_ASSORTMENT": nonfood,
        "PROMOTIONS": promos, "STORE_DAILY_SALES": daily, "SALES_WEEKLY_STORE_CATEGORY": weekly, "STORE_MONTHLY_COSTS": costs,
        "PROMOTION_RESULTS": promo_results, "LOYALTY_ACTIVITY_MONTHLY": loyalty, "STORE_ASSORTMENT_MONTHLY": assortment,
        "COMPETITOR_EVENTS": competitors, "NONFOOD_AVAILABILITY_MONTHLY": nonfood_avail,
        "ARTIKEL": artikel, "KAMPANJ": kampanj, "ARTIKEL_KOSTNAD_MANAD": artikel_kostnad, "KAMPANJ_ARTIKEL_VECKA": kampanj_rows, "KAMPANJ_BUTIK_VECKA": kampanj_butik,
        "DATA_DICTIONARY": build_data_dictionary(),
    }


if __name__ == "__main__":
    for name, df in generate_all().items():
        print(f"{name:32s} {len(df):>9,} rows  {list(df.columns)[:6]}")
