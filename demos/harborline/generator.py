"""
generator.py (Harborline Private Capital)
-----------------------------------------
Deterministic synthetic private-capital dataset for the Harborline WisdomAI demo.
No Snowflake dependency. Every builder is seeded so the same rows are produced
on every run (pattern: demos/halcyon/generator.py).

Demo "today" (AS_OF) = 2026-10-15. Latest reported quarter = 2026-06-30 (Q2 2026).
Vintages 2012-2024; quarterly series from each fund's first capital call.

Engineered control points (see DEMO_PLAN.md):
  CP1  North American buyout funds, vintages 2015-2020, beat the Harborline Broad
       Private Equity Index; mid-market (1-5B) beats mega (5B+).
  CP2  Subscription credit lines flatter early IRR (gap >= 3 pts at 8 quarters for
       2019-2022 vintages) and the gap closes for mature vintages (2014-2017).
       Hero fund Calder Ridge Capital Partners IV matches its Q2 2026 LP report.
  CP3  Distribution drought: 2021-2022 vintages return capital far more slowly than
       2014-2016 vintages did at the same age; H1 2026 distributions well below H1 2021.
  CP4  Westbrook State Retirement System's 2018 vintage sleeve lags its matching
       benchmarks because of two venture funds; other vintages at or above benchmark.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from demo_creator.rng import rng as _seeded_rng

SEED = 20261015
AS_OF = date(2026, 10, 15)
LATEST_Q = date(2026, 6, 30)
FIRST_VINTAGE, LAST_VINTAGE = 2012, 2024

# Hero entities
HERO_FUND_ID = "FND-0117"
HERO_FUND_NAME = "Calder Ridge Capital Partners IV"
HERO_MANAGER_ID = "MGR-007"
HERO_MANAGER_NAME = "Calder Ridge Capital"
HERO_VINTAGE = 2018
HERO_SIZE = 3200.0
HERO_LINE_LIMIT = 400.0
# Q2 2026 figures that the quarterly report PDF states (and FUND_REPORT_EXTRACTS reads back)
HERO_Q1_2026 = dict(nav=2560.0, called=2816.0, dist=1056.0, line=232.0)
HERO_Q2_2026 = dict(nav=2614.0, called=2880.0, dist=1152.0, line=210.0, irr=18.4)
HERO_Q2_CALLS = [(date(2026, 4, 14), 40.0, "Investment"), (date(2026, 6, 2), 24.0, "Investment")]
HERO_Q2_DISTS = [(date(2026, 5, 20), 96.0, "Realization")]
HERO_REPORT_FILE = "Calder_Ridge_Capital_Partners_IV_Q2_2026_Quarterly_Report.pdf"

HERO_ALLOCATOR_ID = "ALC-001"
HERO_ALLOCATOR_NAME = "Westbrook State Retirement System"
LAGGARD_VENTURE_FUNDS = {  # name -> (target IRR, fund size): the two 2018 NA venture funds that drag Westbrook's 2018 sleeve
    "Bramblewood Ventures III": (-4.0, 350.0),
    "Sable Point Ventures II": (-3.0, 280.0),
}

BROAD_PE = "HPCI-BROAD-PE"

STRATEGIES = ["Buyout", "Growth", "Venture", "Private Credit", "Real Estate", "Infrastructure"]
REGIONS = ["North America", "Europe", "Asia-Pacific", "Global"]


def rng(tag: str) -> np.random.Generator:
    return _seeded_rng(SEED, tag)


# ---------------------------------------------------------------------------
# Calendar helpers
# ---------------------------------------------------------------------------
def quarter_end(d: date) -> date:
    q = (d.month - 1) // 3
    m = 3 * (q + 1)
    last = {3: 31, 6: 30, 9: 30, 12: 31}[m]
    return date(d.year, m, last)


def next_quarter_end(qe: date) -> date:
    return quarter_end(qe + timedelta(days=1))


QUARTERS: list[date] = []
_q = date(2012, 3, 31)
while _q <= LATEST_Q:
    QUARTERS.append(_q)
    _q = next_quarter_end(_q)


def roman(n: int) -> str:
    vals = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


# ---------------------------------------------------------------------------
# MANAGERS
# ---------------------------------------------------------------------------
_PREFIX = [
    "Ashgrove", "Northquay", "Halden", "Marlow", "Stonebridge", "Verity", "Oakhaven", "Kestrel", "Brightwater",
    "Lindqvist", "Tamarind", "Silverthorn", "Redcliffe", "Pemberton", "Wexley", "Corvid", "Aldergate", "Beaumont",
    "Thornfield", "Greywell", "Harlow", "Ironbark", "Juniper Hill", "Lakeshore", "Meridian Row", "Nightingale",
    "Orchard Gate", "Pinecrest", "Quarry Lane", "Ravensworth", "Saltmarsh", "Tidewater", "Umberline", "Vantage Point",
    "Westmoor", "Yarrow", "Blackford", "Clearwater", "Dunmore", "Eastbrook", "Fairhaven", "Glenmere", "Hollowbrook",
    "Ivybridge", "Kingsmill", "Larkspur", "Mossbank", "Nordvik", "Oldfield", "Palisade", "Rosslyn", "Sandrock",
    "Tollgate", "Upton Cross", "Valmont", "Whitlock", "Zephyr Bay", "Amberlea", "Birchwood", "Caldwell Park",
    "Dovecote", "Elmsworth", "Foxhollow", "Granite Bay", "Hawkridge", "Ingleside", "Kelsey Point", "Lomond",
    "Maplecroft", "Newhaven", "Overlook", "Parkstone", "Quayside", "Riverbend", "Seabright", "Thistlewood",
    "Vesper", "Wrenfield", "Ardent Bay", "Bellrock", "Copperline", "Driftwood", "Evergreen Row", "Falconer",
    "Goldcrest", "Harborview", "Inverness", "Kingfisher", "Longmeadow", "Millbrook", "Northgate", "Osprey",
    "Prospect Hill", "Ridgeway", "Summerfield", "Trellis", "Waverly", "Bramblewood", "Sable Point", "Cobalt Reach",
    "Ferncliff", "Highwater", "Lanternhill", "Marigold", "Oakum", "Peregrine", "Stillwater", "Tern Harbour",
    "Windward", "Aster Lane", "Brookline Park", "Cedarholm", "Deepwater", "Eider", "Frostline", "Gull Rock",
]
_CITIES = {
    "North America": [("New York", "United States"), ("Boston", "United States"), ("San Francisco", "United States"),
                      ("Chicago", "United States"), ("Toronto", "Canada"), ("Menlo Park", "United States"),
                      ("Dallas", "United States"), ("Los Angeles", "United States"), ("Greenwich", "United States")],
    "Europe": [("London", "United Kingdom"), ("Paris", "France"), ("Stockholm", "Sweden"), ("Munich", "Germany"),
               ("Amsterdam", "Netherlands"), ("Zurich", "Switzerland"), ("Madrid", "Spain")],
    "Asia-Pacific": [("Singapore", "Singapore"), ("Hong Kong", "Hong Kong"), ("Sydney", "Australia"), ("Tokyo", "Japan"), ("Mumbai", "India")],
    "Global": [("London", "United Kingdom"), ("New York", "United States"), ("Singapore", "Singapore")],
}
_STRATEGY_SHARE = {"Buyout": 0.36, "Growth": 0.14, "Venture": 0.20, "Private Credit": 0.11, "Real Estate": 0.10, "Infrastructure": 0.09}
_REGION_SHARE = {"North America": 0.55, "Europe": 0.25, "Asia-Pacific": 0.12, "Global": 0.08}
N_MANAGERS = len(_PREFIX)


def build_managers() -> pd.DataFrame:
    r = rng("managers")
    prefixes = list(_PREFIX)
    r.shuffle(prefixes)
    rows = []
    strategies = r.choice(STRATEGIES, size=N_MANAGERS, p=[_STRATEGY_SHARE[s] for s in STRATEGIES])
    regions = r.choice(REGIONS, size=N_MANAGERS, p=[_REGION_SHARE[x] for x in REGIONS])
    for i in range(N_MANAGERS):
        mid = f"MGR-{i + 1:03d}"
        strat, reg = str(strategies[i]), str(regions[i])
        base = prefixes[i]
        if mid == HERO_MANAGER_ID:
            base, strat, reg = "Calder Ridge", "Buyout", "North America"
        suffix = {"Buyout": "Capital", "Growth": "Growth Partners", "Venture": "Ventures", "Private Credit": "Credit Partners",
                  "Real Estate": "Real Estate Advisors", "Infrastructure": "Infrastructure Partners"}[strat]
        if strat == "Buyout" and r.random() < 0.4:
            suffix = r.choice(["Partners", "Equity Partners", "Capital Management"])
        city, country = _CITIES[reg][int(r.integers(len(_CITIES[reg])))]
        rows.append({
            "MANAGER_ID": mid,
            "MANAGER_NAME": f"{base} {suffix}",
            "HEADQUARTERS_CITY": city,
            "HEADQUARTERS_COUNTRY": country,
            "FOUNDED_YEAR": int(r.integers(1978, 2016)),
            "PRIMARY_STRATEGY": strat,
            "FIRM_AUM_USD_B": float(np.round(np.exp(r.normal(np.log(12), 1.0)), 1)),
            "IS_HPCI_CONTRIBUTOR": bool(r.random() < 0.62),
            "_base": base, "_region": reg,
        })
    df = pd.DataFrame(rows)
    df.loc[df.MANAGER_ID == HERO_MANAGER_ID, ["FOUNDED_YEAR", "FIRM_AUM_USD_B", "IS_HPCI_CONTRIBUTOR"]] = [1996, 21.4, True]
    df.loc[df.MANAGER_ID == HERO_MANAGER_ID, ["HEADQUARTERS_CITY", "HEADQUARTERS_COUNTRY"]] = ["Boston", "United States"]
    return df


# ---------------------------------------------------------------------------
# BENCHMARKS
# ---------------------------------------------------------------------------
BENCHMARK_DEFS = [
    ("HPCI-BROAD-PE", "Harborline Broad Private Equity Index", "All Private Equity", "Global",
     "All buyout, growth and venture funds in the Harborline universe, every region and vintage", True),
    ("HPCI-ALL-PC", "Harborline Private Capital Composite", "All Private Capital", "Global",
     "Every fund in the Harborline universe across all six strategies", True),
    ("HPCI-BUYOUT-NA", "Harborline North America Buyout Index", "Buyout", "North America", "Buyout funds investing primarily in North America", False),
    ("HPCI-BUYOUT-EU", "Harborline Europe Buyout Index", "Buyout", "Europe", "Buyout funds investing primarily in Europe", False),
    ("HPCI-BUYOUT-APAC", "Harborline Asia-Pacific Buyout Index", "Buyout", "Asia-Pacific", "Buyout funds investing primarily in Asia-Pacific", False),
    ("HPCI-BUYOUT-GLOBAL", "Harborline Global Buyout Index", "Buyout", "Global", "All buyout funds regardless of region", False),
    ("HPCI-GROWTH-GLOBAL", "Harborline Global Growth Equity Index", "Growth", "Global", "All growth equity funds regardless of region", False),
    ("HPCI-VENTURE-NA", "Harborline North America Venture Index", "Venture", "North America", "Venture capital funds investing primarily in North America", False),
    ("HPCI-VENTURE-GLOBAL", "Harborline Global Venture Index", "Venture", "Global", "All venture capital funds regardless of region", False),
    ("HPCI-CREDIT-GLOBAL", "Harborline Global Private Credit Index", "Private Credit", "Global", "All private credit funds regardless of region", False),
    ("HPCI-RE-GLOBAL", "Harborline Global Private Real Estate Index", "Real Estate", "Global", "All private real estate funds regardless of region", False),
    ("HPCI-INFRA-GLOBAL", "Harborline Global Infrastructure Index", "Infrastructure", "Global", "All infrastructure funds regardless of region", False),
]


def build_benchmarks() -> pd.DataFrame:
    rows = [{"BENCHMARK_ID": b[0], "BENCHMARK_NAME": b[1], "STRATEGY": b[2], "REGION": b[3], "CONSTITUENT_RULE": b[4],
             "INCEPTION_DATE": date(2012, 3, 31), "IS_BROAD_INDEX": b[5]} for b in BENCHMARK_DEFS]
    return pd.DataFrame(rows)


def matching_benchmark(strategy: str, region: str) -> str:
    if strategy == "Buyout":
        return {"North America": "HPCI-BUYOUT-NA", "Europe": "HPCI-BUYOUT-EU", "Asia-Pacific": "HPCI-BUYOUT-APAC"}.get(region, "HPCI-BUYOUT-GLOBAL")
    if strategy == "Growth":
        return "HPCI-GROWTH-GLOBAL"
    if strategy == "Venture":
        return "HPCI-VENTURE-NA" if region == "North America" else "HPCI-VENTURE-GLOBAL"
    return {"Private Credit": "HPCI-CREDIT-GLOBAL", "Real Estate": "HPCI-RE-GLOBAL", "Infrastructure": "HPCI-INFRA-GLOBAL"}[strategy]


def benchmark_constituents(benchmark_id: str, funds: pd.DataFrame) -> pd.Series:
    """Boolean mask of FUNDS rows that are constituents of the index."""
    if benchmark_id == "HPCI-BROAD-PE":
        return funds.STRATEGY.isin(["Buyout", "Growth", "Venture"])
    if benchmark_id == "HPCI-ALL-PC":
        return pd.Series(True, index=funds.index)
    return funds.BENCHMARK_ID == benchmark_id


# ---------------------------------------------------------------------------
# FUNDS
# ---------------------------------------------------------------------------
# per-vintage quotas (strategy, region) -> count; sum 30
_QUOTA = [
    ("Buyout", "North America", 8), ("Buyout", "Europe", 3), ("Buyout", "Asia-Pacific", 1),
    ("Growth", "North America", 3), ("Growth", "Europe", 1),
    ("Venture", "North America", 4), ("Venture", "Europe", 1), ("Venture", "Asia-Pacific", 1),
    ("Private Credit", "North America", 2), ("Private Credit", "Europe", 1),
    ("Real Estate", "North America", 2), ("Real Estate", "Global", 1),
    ("Infrastructure", "Global", 1), ("Infrastructure", "Europe", 1),
]
_SIZE_BUCKET_P = {  # SMALL (<1B), MID_MARKET (1-5B), MEGA (>5B)
    "Buyout": [0.30, 0.45, 0.25], "Growth": [0.55, 0.40, 0.05], "Venture": [0.80, 0.19, 0.01],
    "Private Credit": [0.35, 0.50, 0.15], "Real Estate": [0.40, 0.50, 0.10], "Infrastructure": [0.25, 0.50, 0.25],
}
_IRR_BASE = {"Buyout": (14.0, 5.0), "Growth": (13.0, 6.0), "Venture": (11.0, 10.0), "Private Credit": (9.0, 2.5),
             "Real Estate": (8.5, 4.0), "Infrastructure": (9.5, 3.0)}
_REGION_ADJ = {"North America": 0.8, "Europe": -0.3, "Asia-Pacific": -1.0, "Global": 0.0}
_VINTAGE_ADJ = {2012: 1.5, 2013: 1.5, 2014: 1.5, 2015: 1.0, 2016: 1.0, 2017: 1.0, 2018: 0.3, 2019: 0.3,
                2020: 1.5, 2021: -2.5, 2022: -1.5, 2023: 0.0, 2024: 0.0}
_CURRENCY = {"North America": "USD", "Europe": "EUR", "Asia-Pacific": "USD", "Global": "USD"}


def size_bucket(size: float) -> str:
    return "SMALL" if size < 1000 else ("MID_MARKET" if size <= 5000 else "MEGA")


def build_funds(managers: pd.DataFrame) -> pd.DataFrame:
    r = rng("funds")
    specs: list[dict] = []
    for v in range(FIRST_VINTAGE, LAST_VINTAGE + 1):
        scale = 0.8 if v <= 2013 else (0.7 if v == 2024 else 1.0)
        for strat, reg, n in _QUOTA:
            k = int(round(n * scale))
            if strat == "Venture" and reg == "North America" and v == 2018:
                k += 3  # extra NA venture funds in 2018 so the two laggards do not dominate the venture index
            for _ in range(k):
                specs.append({"STRATEGY": strat, "REGION": reg, "VINTAGE_YEAR": v})
    order = r.permutation(len(specs))
    specs = [specs[i] for i in order]
    hero_pos = int(HERO_FUND_ID.split("-")[1]) - 1
    specs.insert(hero_pos, {"STRATEGY": "Buyout", "REGION": "North America", "VINTAGE_YEAR": HERO_VINTAGE, "_hero": True})

    laggards = list(LAGGARD_VENTURE_FUNDS.items())
    mgr_by_strat = {s: managers[managers.PRIMARY_STRATEGY == s].MANAGER_ID.tolist() for s in STRATEGIES}
    series_counter: dict[str, int] = {}
    rows = []
    for i, s in enumerate(specs):
        fid = f"FND-{i + 1:04d}"
        strat, reg, v = s["STRATEGY"], s["REGION"], s["VINTAGE_YEAR"]
        hero = s.get("_hero", False)
        # size
        p = _SIZE_BUCKET_P[strat]
        b = int(r.choice(3, p=p))
        lo, hi = [(150, 1000), (1000, 5000), (5000, 22000)][b]
        size = float(np.round(np.exp(r.uniform(np.log(lo), np.log(hi))) / 10) * 10)
        # target IRR at maturity
        mu, sd = _IRR_BASE[strat]
        target = mu + _REGION_ADJ[reg] + _VINTAGE_ADJ[v] + r.normal(0, sd)
        if strat == "Venture" and v in (2019, 2020, 2021):
            target -= 5.0  # post-2022 markdowns
        if strat == "Buyout" and reg == "North America" and 2015 <= v <= 2020:
            target += 2.5                                        # CP1: the custom-index cohort outperforms
            target += {0: -1.0, 1: 0.8, 2: -4.0}[b]              # CP1: mid-market beats mega
        # subscription line usage grows with vintage
        p_line = {2012: 0.15, 2013: 0.2, 2014: 0.28, 2015: 0.35, 2016: 0.42, 2017: 0.48, 2018: 0.52, 2019: 0.58,
                  2020: 0.6, 2021: 0.64, 2022: 0.66, 2023: 0.68, 2024: 0.7}[v]
        if strat in ("Venture",):
            p_line *= 0.5
        uses_line = bool(r.random() < p_line)
        line_limit = float(np.round(size * r.uniform(0.08, 0.18) / 5) * 5) if uses_line else None
        # manager
        pool = mgr_by_strat[strat] if r.random() < 0.85 else managers.MANAGER_ID.tolist()
        pool = [m for m in pool if m != HERO_MANAGER_ID]      # Calder Ridge funds I-III predate the data window
        mid = str(r.choice(pool))
        name_override = None
        if hero:
            fid, mid, size, target, uses_line, line_limit = HERO_FUND_ID, HERO_MANAGER_ID, HERO_SIZE, 18.4, True, HERO_LINE_LIMIT
            name_override = HERO_FUND_NAME
        elif strat == "Venture" and reg == "North America" and v == 2018 and laggards:
            name_override, (target, size) = laggards.pop(0)
            uses_line, line_limit = False, None
        # name
        mrow = managers[managers.MANAGER_ID == mid].iloc[0]
        series_counter[mid] = series_counter.get(mid, 0) + 1
        series = {"Buyout": "Capital Partners", "Growth": "Growth Equity", "Venture": "Ventures", "Private Credit": "Credit Opportunities",
                  "Real Estate": "Real Estate Partners", "Infrastructure": "Infrastructure Fund"}[strat]
        name = name_override or f"{mrow._base} {series}"
        # dates
        first_call = date(v, int(r.integers(1, 13)), int(r.integers(1, 28)))
        first_close = first_call - timedelta(days=int(r.integers(20, 120)))
        if hero:
            first_call, first_close = date(2018, 4, 9), date(2018, 1, 25)
        rows.append({
            "FUND_ID": fid, "FUND_NAME": name, "MANAGER_ID": mid, "STRATEGY": strat, "REGION": reg, "VINTAGE_YEAR": v,
            "FIRST_CLOSE_DATE": first_close, "FIRST_CALL_DATE": first_call, "FUND_SIZE_USD_M": size,
            "SIZE_BUCKET": size_bucket(size), "BASE_CURRENCY": _CURRENCY[reg], "USES_SUBSCRIPTION_LINE": uses_line,
            "SUBSCRIPTION_LINE_LIMIT_USD_M": line_limit, "FUND_STATUS": None, "BENCHMARK_ID": matching_benchmark(strat, reg),
            "DATA_SOURCE": str(r.choice(["LP contribution", "GP contribution", "Report extraction"], p=[0.5, 0.35, 0.15])),
            "_target_irr": float(target), "_hero": hero,
        })
    df = pd.DataFrame(rows)
    # fund numerals: per manager and series, in vintage order, starting at a per-manager offset
    offsets = {mid: int(r.integers(0, 3)) for mid in managers.MANAGER_ID}
    df.loc[df._hero, "FUND_NAME"] = f"{HERO_MANAGER_NAME.replace(' Capital', '')} Capital Partners"
    df["_rank"] = df.sort_values("FIRST_CALL_DATE").groupby(["MANAGER_ID", "FUND_NAME"]).cumcount()
    hero_rank = int(df.loc[df._hero, "_rank"].iloc[0])
    offsets[HERO_MANAGER_ID] = max(0, 3 - hero_rank)        # the hero is Calder Ridge Capital Partners IV
    df["FUND_NAME"] = [n if n in LAGGARD_VENTURE_FUNDS else f"{n} {roman(offsets[m] + k + 1)}"
                       for n, m, k in zip(df.FUND_NAME, df.MANAGER_ID, df._rank)]
    assert df.loc[df._hero, "FUND_NAME"].iloc[0] == HERO_FUND_NAME, df.loc[df._hero, "FUND_NAME"].iloc[0]
    df = df.drop(columns=["_rank"])
    assert df.FUND_NAME.is_unique, df.FUND_NAME[df.FUND_NAME.duplicated()].tolist()
    return df


# ---------------------------------------------------------------------------
# QUARTERLY SERIES: NAV, cash flows, IRR
# ---------------------------------------------------------------------------
_DIST_VINTAGE_FACTOR = {2020: 0.75, 2021: 0.42, 2022: 0.40, 2023: 0.5, 2024: 0.5}          # CP3 drought
_DIST_ENV = {2021: 1.30, 2022: 0.85, 2023: 0.70, 2024: 0.75, 2025: 0.80, 2026: 0.78}        # calendar-year exit environment
_MARKET_SHOCK = {date(2020, 3, 31): -2.5, date(2020, 6, 30): -1.0, date(2022, 6, 30): -0.8, date(2022, 9, 30): -0.6}
_DURATION = {"Buyout": 4.6, "Growth": 4.8, "Venture": 5.5, "Private Credit": 3.2, "Real Estate": 4.0, "Infrastructure": 5.0}


def _fund_series(f: pd.Series, r: np.random.Generator) -> tuple[list[dict], list[dict]]:
    """Return (nav_rows, flow_rows) for one fund."""
    size = float(f.FUND_SIZE_USD_M)
    target = float(f._target_irr)
    uses_line = bool(f.USES_SUBSCRIPTION_LINE)
    limit = float(f.SUBSCRIPTION_LINE_LIMIT_USD_M) if uses_line else 0.0
    q0 = quarter_end(f.FIRST_CALL_DATE)
    quarters = [q for q in QUARTERS if q >= q0]
    n = len(quarters)
    ages = np.arange(1, n + 1)
    # liquidation
    liq_age = int(52 + r.integers(0, 5))
    if n > liq_age:
        quarters, ages, n = quarters[:liq_age], ages[:liq_age], liq_age
        liquidated = True
    else:
        liquidated = False
    # ---- capital calls (fraction of commitment)
    total_called_pct = r.uniform(0.86, 0.97)
    inv_w = np.where(ages <= 22, np.exp(-(ages - 1) / 9.0), 0.0)
    if uses_line:                                   # the line bridges the first quarters: LP calls come later
        inv_w = inv_w * np.where(ages <= 3, 0.15, np.where(ages <= 12, 1.25, 1.0))
    inv_w = inv_w * r.lognormal(0, 0.35, size=n)
    fee_pct = 0.0025 * np.where(ages <= 40, 1.0, 0.0)
    inv_pct = inv_w / inv_w.sum() * (total_called_pct - fee_pct.sum())
    call_inc = np.round((inv_pct + fee_pct) * size, 1)
    fee_inc = np.round(fee_pct * size, 1)
    cum_called = np.cumsum(call_inc)
    # ---- credit line balance
    line_bal = np.zeros(n)
    if uses_line:
        persistent = r.random() < 0.25 or bool(f._hero)
        u = np.where(ages <= 3, 0.25 * ages, np.where(ages <= 8, 0.75, np.maximum(0.75 - 0.045 * (ages - 8), 0.0)))
        if persistent:
            u = np.maximum(u, r.uniform(0.35, 0.55))
        line_bal = np.round(limit * u * r.uniform(0.9, 1.1, size=n), 1)
    # ---- total value multiple path and IRR path
    tvpi_final = max(0.45, 1 + target / 100 * _DURATION[f.STRATEGY] * r.uniform(0.9, 1.1))
    tv = 1 + (tvpi_final - 1) * (1 - np.exp(-(ages - 1) / 14.0)) - 0.07 * np.exp(-(ages - 1) / 5.0)
    tv = tv * (1 + np.cumsum(r.normal(0, 0.012, size=n)))
    dip = -6.0 if uses_line else -12.0
    irr = target + (dip - target) * np.exp(-(ages - 1) / 7.0)
    if uses_line:
        irr = irr + 3.5 * np.exp(-np.maximum(ages - 6, 0) / 10.0)      # CP2: subscription line flatters early IRR
    eps = np.zeros(n)
    for i in range(1, n):
        eps[i] = 0.7 * eps[i - 1] + r.normal(0, 0.8)
    irr = irr + eps + np.array([_MARKET_SHOCK.get(q, 0.0) for q in quarters])
    # ---- distributions
    vf = _DIST_VINTAGE_FACTOR.get(int(f.VINTAGE_YEAR), 1.0)
    base_cum = cum_called * tvpi_final * np.clip((ages - 4) / 44.0, 0, 1) ** 0.85
    base_inc = np.maximum(np.diff(base_cum, prepend=0.0), 0.0)
    env = np.array([_DIST_ENV.get(q.year, 1.0) for q in quarters])
    dist_inc = base_inc * env * vf * r.lognormal(0, 0.45, size=n)
    cum_dist = np.cumsum(dist_inc)
    cap = cum_called * tv * 0.985
    cum_dist = np.minimum(cum_dist, cap)
    cum_dist = np.maximum.accumulate(cum_dist)
    if liquidated:
        cum_dist[-1] = cum_called[-1] * tv[-1]
    cum_dist = np.round(cum_dist, 1)
    dist_inc = np.round(np.maximum(np.diff(cum_dist, prepend=0.0), 0.0), 1)
    cum_dist = np.cumsum(dist_inc)
    nav = cum_called * tv - cum_dist + line_bal * (tv - 1)
    nav = np.maximum(nav, 0.0)
    if liquidated:
        nav[-1] = 0.0
        line_bal[-1] = 0.0
    # ---- hero override: match the Q2 2026 LP report exactly
    if bool(f._hero):
        iq1 = quarters.index(date(2026, 3, 31))
        iq2 = quarters.index(date(2026, 6, 30))
        call_inc[: iq1 + 1] = np.round(call_inc[: iq1 + 1] * HERO_Q1_2026["called"] / cum_called[iq1], 1)
        call_inc[iq1] += HERO_Q1_2026["called"] - np.round(call_inc[: iq1 + 1].sum(), 1)
        call_inc[iq2] = sum(a for _, a, _ in HERO_Q2_CALLS)
        fee_inc[iq2] = 0.0
        cum_called = np.cumsum(call_inc)
        dist_inc[: iq1 + 1] = np.round(dist_inc[: iq1 + 1] * HERO_Q1_2026["dist"] / cum_dist[iq1], 1)
        dist_inc[iq1] += HERO_Q1_2026["dist"] - np.round(dist_inc[: iq1 + 1].sum(), 1)
        dist_inc[iq2] = sum(a for _, a, _ in HERO_Q2_DISTS)
        cum_dist = np.cumsum(dist_inc)
        nav[: iq1 + 1] = nav[: iq1 + 1] * HERO_Q1_2026["nav"] / nav[iq1]
        nav[iq2] = HERO_Q2_2026["nav"]
        line_bal[iq1] = HERO_Q1_2026["line"]
        line_bal[iq2] = HERO_Q2_2026["line"]
        irr = irr + (HERO_Q2_2026["irr"] - irr[iq2])
    nav = np.round(nav, 1)
    cum_called = np.round(cum_called, 1)
    cum_dist = np.round(cum_dist, 1)
    # ---- rows
    nav_rows, flow_rows = [], []
    prev_nav = None
    for i, q in enumerate(quarters):
        called, dist, lb = float(cum_called[i]), float(cum_dist[i]), float(line_bal[i])
        has_capital = called >= 0.02 * size
        qret = None
        if prev_nav is not None and prev_nav >= 1.0:
            qret = float(np.clip((nav[i] - prev_nav + dist_inc[i] - call_inc[i]) / prev_nav * 100, -40, 60))
        nav_rows.append({
            "FUND_ID": f.FUND_ID, "QUARTER_END": q, "FUND_AGE_QUARTERS": int(ages[i]), "NAV_USD_M": float(nav[i]),
            "CUMULATIVE_CALLED_USD_M": called, "CUMULATIVE_DISTRIBUTED_USD_M": dist,
            "PAID_IN_PCT": round(100 * called / size, 2), "CREDIT_LINE_BALANCE_USD_M": lb,
            "IRR_SINCE_INCEPTION_PCT": round(float(irr[i]), 2) if has_capital else None,
            "TVPI": round((nav[i] + dist) / called, 3) if has_capital else None,
            "DPI": round(dist / called, 3) if has_capital else None,
            "RVPI": round(nav[i] / called, 3) if has_capital else None,
            "QUARTERLY_RETURN_PCT": round(qret, 2) if qret is not None else None,
            "REPORT_RECEIVED_DATE": q + timedelta(days=int(r.integers(45, 91))),
        })
        prev_nav = float(nav[i])
        # cash flows for the quarter
        qstart = quarter_end(q - timedelta(days=95)) + timedelta(days=1)
        if i == 0:
            qstart = max(f.FIRST_CALL_DATE, qstart)
        span = (q - qstart).days

        def rand_date():
            return qstart + timedelta(days=int(r.integers(0, max(span, 1))))

        if bool(f._hero) and q == date(2026, 6, 30):
            for d, a, purpose in HERO_Q2_CALLS:
                flow_rows.append({"FUND_ID": f.FUND_ID, "FLOW_DATE": d, "QUARTER_END": q, "FLOW_TYPE": "CAPITAL_CALL", "FLOW_PURPOSE": purpose, "AMOUNT_USD_M": a, "IS_RECALLABLE": None})
            for d, a, purpose in HERO_Q2_DISTS:
                flow_rows.append({"FUND_ID": f.FUND_ID, "FLOW_DATE": d, "QUARTER_END": q, "FLOW_TYPE": "DISTRIBUTION", "FLOW_PURPOSE": purpose, "AMOUNT_USD_M": a, "IS_RECALLABLE": False})
            continue
        ci, fi = float(call_inc[i]), float(fee_inc[i])
        inv = round(ci - fi, 2)
        if fi > 0 and inv > 0:
            flow_rows.append({"FUND_ID": f.FUND_ID, "FLOW_DATE": rand_date(), "QUARTER_END": q, "FLOW_TYPE": "CAPITAL_CALL", "FLOW_PURPOSE": "Management fee", "AMOUNT_USD_M": fi, "IS_RECALLABLE": None})
        else:
            inv = round(ci, 2)
        if inv > 0:
            purpose = "Line repayment" if (uses_line and i > 0 and line_bal[i] < line_bal[i - 1] - 1) else "Investment"
            if inv > 0.1 * size and r.random() < 0.4:
                a1 = round(inv * r.uniform(0.4, 0.6), 2)
                flow_rows.append({"FUND_ID": f.FUND_ID, "FLOW_DATE": rand_date(), "QUARTER_END": q, "FLOW_TYPE": "CAPITAL_CALL", "FLOW_PURPOSE": purpose, "AMOUNT_USD_M": a1, "IS_RECALLABLE": None})
                inv = round(inv - a1, 2)
            flow_rows.append({"FUND_ID": f.FUND_ID, "FLOW_DATE": rand_date(), "QUARTER_END": q, "FLOW_TYPE": "CAPITAL_CALL", "FLOW_PURPOSE": purpose, "AMOUNT_USD_M": inv, "IS_RECALLABLE": None})
        di = round(float(dist_inc[i]), 2)
        if di > 0:
            purpose = str(r.choice(["Realization", "Dividend", "Recapitalization"],
                                   p=[0.55, 0.40, 0.05] if f.STRATEGY in ("Private Credit", "Infrastructure", "Real Estate") else [0.80, 0.12, 0.08]))
            flow_rows.append({"FUND_ID": f.FUND_ID, "FLOW_DATE": rand_date(), "QUARTER_END": q, "FLOW_TYPE": "DISTRIBUTION", "FLOW_PURPOSE": purpose, "AMOUNT_USD_M": di, "IS_RECALLABLE": bool(r.random() < 0.1)})
    status = "LIQUIDATED" if liquidated else ("INVESTING" if n <= 20 else "HARVESTING")
    for row in nav_rows:
        row["_status"] = status
    return nav_rows, flow_rows


def build_quarterly(funds: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    nav_all, flow_all = [], []
    for _, f in funds.iterrows():
        r = rng(f"series:{f.FUND_ID}")
        nr, fr = _fund_series(f, r)
        nav_all += nr
        flow_all += fr
    nav = pd.DataFrame(nav_all)
    flows = pd.DataFrame(flow_all)
    flows = flows.sort_values(["FLOW_DATE", "FUND_ID"], kind="stable").reset_index(drop=True)
    flows.insert(0, "CASH_FLOW_ID", [f"CF-{i + 1:08d}" for i in range(len(flows))])
    return nav, flows


# ---------------------------------------------------------------------------
# BENCHMARK_QUARTERLY (derived from the funds — Harborline publishes what it collects)
# ---------------------------------------------------------------------------
def build_benchmark_quarterly(funds: pd.DataFrame, nav: pd.DataFrame) -> pd.DataFrame:
    perf = nav.merge(funds[["FUND_ID", "VINTAGE_YEAR", "STRATEGY", "REGION", "BENCHMARK_ID"]], on="FUND_ID")
    rows = []

    def pooled(g: pd.DataFrame) -> dict | None:
        g = g[g.CUMULATIVE_CALLED_USD_M > 0]
        if len(g) < 2:
            return None
        w = g.CUMULATIVE_CALLED_USD_M
        gi = g[g.IRR_SINCE_INCEPTION_PCT.notna()]
        gq = g[g.QUARTERLY_RETURN_PCT.notna() & (g.NAV_USD_M > 0)]
        return {
            "FUND_COUNT": int(len(g)),
            "POOLED_IRR_PCT": round(float((gi.IRR_SINCE_INCEPTION_PCT * gi.CUMULATIVE_CALLED_USD_M).sum() / gi.CUMULATIVE_CALLED_USD_M.sum()), 2) if len(gi) else None,
            "QUARTERLY_RETURN_PCT": round(float((gq.QUARTERLY_RETURN_PCT * gq.NAV_USD_M).sum() / gq.NAV_USD_M.sum()), 2) if len(gq) else None,
            "POOLED_TVPI": round(float((g.NAV_USD_M + g.CUMULATIVE_DISTRIBUTED_USD_M).sum() / w.sum()), 3),
            "POOLED_DPI": round(float(g.CUMULATIVE_DISTRIBUTED_USD_M.sum() / w.sum()), 3),
            "TOTAL_NAV_USD_M": round(float(g.NAV_USD_M.sum()), 1),
            "TOTAL_CALLED_USD_M": round(float(w.sum()), 1),
        }

    for bid, *_ in BENCHMARK_DEFS:
        members = funds[benchmark_constituents(bid, funds)].FUND_ID
        sub = perf[perf.FUND_ID.isin(members)]
        for q, g in sub.groupby("QUARTER_END"):
            p = pooled(g)
            if p:
                rows.append({"BENCHMARK_ID": bid, "VINTAGE_YEAR": None, "QUARTER_END": q, **p})
            for v, gv in g.groupby("VINTAGE_YEAR"):
                pv = pooled(gv)
                if pv:
                    rows.append({"BENCHMARK_ID": bid, "VINTAGE_YEAR": int(v), "QUARTER_END": q, **pv})
    df = pd.DataFrame(rows)
    df["VINTAGE_YEAR"] = df["VINTAGE_YEAR"].astype("Int64")
    return df.sort_values(["BENCHMARK_ID", "VINTAGE_YEAR", "QUARTER_END"], na_position="first").reset_index(drop=True)


# ---------------------------------------------------------------------------
# ALLOCATORS and COMMITMENTS
# ---------------------------------------------------------------------------
ALLOCATORS = [
    ("ALC-001", HERO_ALLOCATOR_NAME, "Public pension", "Westbrook, United States", 14200.0, "Premium Analytics", 46),
    ("ALC-002", "Thornfield University Endowment", "Endowment", "Providence, United States", 3900.0, "Premium Analytics", 30),
    ("ALC-003", "Marrow Lake Insurance Group", "Insurance", "Hartford, United States", 6100.0, "Standard", 28),
    ("ALC-004", "Pelham Family Office", "Family office", "London, United Kingdom", 1150.0, "Standard", 22),
    ("ALC-005", "Northern Harbour Sovereign Fund", "Sovereign wealth fund", "Oslo, Norway", 22800.0, "Premium Analytics", 38),
]


def build_allocators() -> pd.DataFrame:
    return pd.DataFrame([{"ALLOCATOR_ID": a[0], "ALLOCATOR_NAME": a[1], "ALLOCATOR_TYPE": a[2], "HEADQUARTERS": a[3],
                          "TOTAL_PC_COMMITMENT_USD_M": a[4], "PORTAL_TIER": a[5]} for a in ALLOCATORS])


def build_commitments(funds: pd.DataFrame, nav: pd.DataFrame, bq: pd.DataFrame) -> pd.DataFrame:
    r = rng("commitments")
    latest = nav[nav.QUARTER_END == LATEST_Q][["FUND_ID", "IRR_SINCE_INCEPTION_PCT"]]
    f = funds.merge(latest, on="FUND_ID", how="left")
    bvint = bq[(bq.QUARTER_END == LATEST_Q) & bq.VINTAGE_YEAR.notna()][["BENCHMARK_ID", "VINTAGE_YEAR", "POOLED_IRR_PCT"]]
    bvint = bvint.rename(columns={"POOLED_IRR_PCT": "_bench"})
    bvint["VINTAGE_YEAR"] = bvint["VINTAGE_YEAR"].astype(int)
    f = f.merge(bvint, on=["BENCHMARK_ID", "VINTAGE_YEAR"], how="left")
    f["_gap"] = f.IRR_SINCE_INCEPTION_PCT - f._bench
    active = f[f.FUND_STATUS != "LIQUIDATED"]
    rows = []
    for aid, _, _, _, _, _, n_funds in ALLOCATORS:
        chosen: list[str] = []
        if aid == HERO_ALLOCATOR_ID:
            # CP4: the 2018 sleeve = the two venture laggards plus six funds near benchmark; other vintages at or above benchmark
            lag = active[active.FUND_NAME.isin(LAGGARD_VENTURE_FUNDS.keys())].FUND_ID.tolist()
            near = active[(active.VINTAGE_YEAR == 2018) & (~active.FUND_ID.isin(lag)) & (active._gap.between(-1.5, 4.0)) & (active.STRATEGY != "Venture")]
            chosen += lag + near.sample(n=min(6, len(near)), random_state=int(r.integers(1 << 30))).FUND_ID.tolist()
            for v in range(FIRST_VINTAGE, LAST_VINTAGE + 1):
                if v == 2018:
                    continue
                pool = active[(active.VINTAGE_YEAR == v) & (active._gap >= 0.0) & active._gap.notna()]
                k = min(len(pool), int(r.integers(2, 4)))
                chosen += pool.sample(n=k, random_state=int(r.integers(1 << 30))).FUND_ID.tolist()
        else:
            pool = active[~active.FUND_ID.isin(chosen)]
            chosen = pool.sample(n=n_funds, random_state=int(r.integers(1 << 30))).FUND_ID.tolist()
        for fid in chosen:
            fr = f[f.FUND_ID == fid].iloc[0]
            pct = r.uniform(0.01, 0.04)
            amt = float(np.round(min(fr.FUND_SIZE_USD_M * pct, 250.0) / 5) * 5)
            amt = max(amt, 10.0)
            if aid == HERO_ALLOCATOR_ID and fr.FUND_NAME in LAGGARD_VENTURE_FUNDS:
                amt = 120.0 if fr.FUND_NAME == "Bramblewood Ventures III" else 100.0
            rows.append({"ALLOCATOR_ID": aid, "FUND_ID": fid, "COMMITMENT_USD_M": amt,
                         "COMMITMENT_DATE": fr.FIRST_CLOSE_DATE + timedelta(days=int(r.integers(-30, 60)))})
    df = pd.DataFrame(rows).sort_values(["ALLOCATOR_ID", "COMMITMENT_DATE"]).reset_index(drop=True)
    df.insert(0, "COMMITMENT_ID", [f"CMT-{i + 1:04d}" for i in range(len(df))])
    return df


# ---------------------------------------------------------------------------
# FUND_REPORT_EXTRACTS
# ---------------------------------------------------------------------------
def build_report_extracts(funds: pd.DataFrame, nav: pd.DataFrame, flows: pd.DataFrame) -> pd.DataFrame:
    r = rng("extracts")
    qflows = flows.groupby(["FUND_ID", "QUARTER_END", "FLOW_TYPE"]).AMOUNT_USD_M.sum().unstack(fill_value=0.0)
    rows = []
    for q in (date(2026, 3, 31), date(2026, 6, 30)):
        sub = nav[nav.QUARTER_END == q].merge(funds[["FUND_ID", "FUND_NAME", "USES_SUBSCRIPTION_LINE", "_hero"]], on="FUND_ID")
        for _, n in sub.iterrows():
            calls = float(qflows.loc[(n.FUND_ID, q)].get("CAPITAL_CALL", 0.0)) if (n.FUND_ID, q) in qflows.index else 0.0
            dists = float(qflows.loc[(n.FUND_ID, q)].get("DISTRIBUTION", 0.0)) if (n.FUND_ID, q) in qflows.index else 0.0
            nav_x, calls_x, dists_x = float(n.NAV_USD_M), round(calls, 1), round(dists, 1)
            line_x = float(n.CREDIT_LINE_BALANCE_USD_M) if n.USES_SUBSCRIPTION_LINE else None
            u = r.random()
            if n._hero:
                status, conf = "AUTO_ACCEPTED", 0.97
            elif u < 0.92:
                status, conf = "AUTO_ACCEPTED", round(float(r.uniform(0.92, 0.995)), 3)
            elif u < 0.97:
                status, conf = "ANALYST_REVIEW", round(float(r.uniform(0.80, 0.90)), 3)
                nav_x = round(nav_x * (1 + r.choice([-1, 1]) * r.uniform(0.003, 0.02)), 1)
            else:
                status, conf = "CORRECTED", round(float(r.uniform(0.70, 0.85)), 3)
                calls_x = round(calls_x + r.choice([-1, 1]) * r.uniform(0.5, 5.0), 1) if calls_x > 0 else calls_x
            qlabel = f"Q{(q.month - 1) // 3 + 1}_{q.year}"
            slug = re.sub(r"[^A-Za-z0-9]+", "_", n.FUND_NAME).strip("_")
            rows.append({
                "FUND_ID": n.FUND_ID, "REPORT_QUARTER_END": q,
                "SOURCE_DOCUMENT": HERO_REPORT_FILE if (n._hero and q == LATEST_Q) else f"{slug}_{qlabel}_LP_Report.pdf",
                "EXTRACTED_NAV_USD_M": nav_x, "EXTRACTED_CALLS_IN_QUARTER_USD_M": calls_x,
                "EXTRACTED_DISTRIBUTIONS_IN_QUARTER_USD_M": dists_x, "EXTRACTED_CREDIT_LINE_BALANCE_USD_M": line_x,
                "EXTRACTION_CONFIDENCE": conf, "EXTRACTION_MODEL": "harborline-docai-2.3",
                "EXTRACTED_AT": pd.Timestamp(datetime.combine(q + timedelta(days=int(r.integers(50, 86))), datetime.min.time()) + timedelta(hours=int(r.integers(7, 19)), minutes=int(r.integers(0, 60)))),
                "REVIEW_STATUS": status,
            })
    df = pd.DataFrame(rows).sort_values(["REPORT_QUARTER_END", "FUND_ID"]).reset_index(drop=True)
    df.insert(0, "EXTRACT_ID", [f"EXT-{i + 1:05d}" for i in range(len(df))])
    return df


# ---------------------------------------------------------------------------
# DATA_DICTIONARY (parsed from the DDL so it never drifts)
# ---------------------------------------------------------------------------
def build_data_dictionary(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    ddl = (Path(__file__).parent / "01_snowflake_ddl.sql").read_text()
    rows = []
    for m in re.finditer(r"CREATE OR REPLACE TABLE (\w+) \((.*?)\n\) COMMENT", ddl, re.S):
        table, body = m.group(1), m.group(2)
        for line in body.splitlines():
            cm = re.match(r"\s*(\w+)\s+([A-Z_]+(?:\([\d,]+\))?)\s.*?COMMENT '(.*)'", line)
            if not cm:
                continue
            col, dtype, desc = cm.groups()
            example = ""
            if table in frames and col in frames[table].columns:
                s = frames[table][col].dropna()
                example = str(s.iloc[0])[:100] if len(s) else ""
            rows.append({"TABLE_NAME": table, "COLUMN_NAME": col, "DATA_TYPE": dtype, "DESCRIPTION": desc, "EXAMPLE_VALUE": example})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# generate_all
# ---------------------------------------------------------------------------
def generate_all() -> dict[str, pd.DataFrame]:
    managers = build_managers()
    benchmarks = build_benchmarks()
    funds = build_funds(managers)
    nav, flows = build_quarterly(funds)
    status = nav.groupby("FUND_ID")._status.first()
    funds["FUND_STATUS"] = funds.FUND_ID.map(status)
    nav = nav.drop(columns=["_status"])
    bq = build_benchmark_quarterly(funds, nav)
    allocators = build_allocators()
    commitments = build_commitments(funds, nav, bq)
    extracts = build_report_extracts(funds, nav, flows)
    frames = {
        "MANAGERS": managers.drop(columns=["_base", "_region"]),
        "BENCHMARKS": benchmarks,
        "FUNDS": funds.drop(columns=["_target_irr", "_hero"]),
        "ALLOCATORS": allocators,
        "ALLOCATOR_COMMITMENTS": commitments,
        "FUND_QUARTERLY_NAV": nav,
        "FUND_CASH_FLOWS": flows,
        "BENCHMARK_QUARTERLY": bq,
        "FUND_REPORT_EXTRACTS": extracts,
    }
    frames["DATA_DICTIONARY"] = build_data_dictionary(frames)
    return frames


if __name__ == "__main__":
    for k, v in generate_all().items():
        print(f"{k:28s} {len(v):>7d} rows")
