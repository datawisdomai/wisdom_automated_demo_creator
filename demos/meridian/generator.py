"""
generator.py (Meridian Clinician Network)
-----------------------------------------
Deterministic synthetic data for the three-way contract reconciliation demo.
No Snowflake dependency. Every builder is seeded so the same rows are produced
on every run.

Demo "today" (AS_OF) = 2026-09-30 (Q3 2026 quarter end). Agreements are signed
2024-01-01 .. 2026-09-15.

The three systems are built FROM the contract truth and then the seeded drift is
applied. There is no results table: the mismatches are derived by the SQL in
recon_sql.py, which checks.py and reviewed_queries.py share.

Control points (see DEMO_PLAN.md / demo.yaml):
  CP1  15-20% of the ~270 chains fail at least one of the eleven checks; > $5M exposure.
  CP2  Halvorsen Therapeutics: MSA + 3 amendments; Salesforce at A2, NetSuite at A1
       with a duplicate order; >= 20 amended chains where NetSuite carries stale terms.
  CP3  >= 60 contract billing milestones (>= $3M) missing from NetSuite.
  CP4  Findings split across Sales Ops / Revenue Accounting / Billing; pharma carries
       the variance dollars; Dana Whitfield's finding rate >= 2x the average.

Drift categories (each tagged on SEEDED[chain] for checks.py):
  R  Salesforce amount rounded by the rep                     (TCV_MISMATCH)
  L  Salesforce opportunity missing a line item               (TCV_MISMATCH + PRODUCT_LINE_COUNT_MISMATCH)
  E  amendment extended the term, NetSuite end date stale     (TERM_END_DATE_MISMATCH)
  N  amendment never reached NetSuite                         (AMENDMENT_NOT_IN_NETSUITE + ...)
  D  latest amendment exists only in DocuSign                 (AMENDMENT_NOT_IN_SALESFORCE + AMENDMENT_NOT_IN_NETSUITE + ...)
  P  payment terms differ (contract Net 45/60, NetSuite Net 30) (PAYMENT_TERMS_MISMATCH)
  F  contract milestone-billed, NetSuite quarterly            (BILLING_FREQUENCY_MISMATCH + MISSING_BILLING_MILESTONE)
  M  NetSuite split two milestones differently                (MISSING_BILLING_MILESTONE)
  T  NetSuite billing schedule truncated (last bills missing) (MISSING_BILLING_MILESTONE)
  U  duplicate NetSuite sales order (full copy)               (DUPLICATE_SALES_ORDERS)
  S  NetSuite order with no opportunity id                    (SALES_ORDER_WITHOUT_OPPORTUNITY)
  O  opportunity with null / wrong contract number            (OPPORTUNITY_WITHOUT_CONTRACT_LINK + TCV_MISMATCH)
  H  the hero chain (compound, hand-built)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from demo_creator.rng import rng as _seeded_rng

SEED = 20260930
AS_OF = date(2026, 9, 30)
START = date(2024, 1, 1)
LAST_SIGNING = date(2026, 9, 29)

# Story constants (mirrored in demo.yaml generator.constants)
HERO_CUSTOMER = "Halvorsen Therapeutics"
HERO_CUSTOMER_ID = "CUST-0017"
HERO_CONTRACT_NUMBER = "MCN-2025-0142"
HERO_MSA_SIGNED = date(2025, 2, 10)
HERO_A1_SIGNED = date(2025, 6, 16)
HERO_A2_SIGNED = date(2025, 11, 3)
HERO_A3_SIGNED = date(2026, 7, 20)
HERO_OWNER = "Dana Whitfield"
BOOMI_INCIDENT_DATE = date(2026, 3, 1)
MILESTONE_TOLERANCE_DAYS = 7
AMOUNT_TOLERANCE_USD = 100
HIGH_SEVERITY_USD = 100000

# ---------------------------------------------------------------- reference data
OWNERS = {
    "Pharma East": ["Dana Whitfield", "Marcus Oyelaran", "Priya Natarajan"],
    "Pharma West": ["Elena Castellanos", "Tom Reinholt", "Aisha Bakare"],
    "Health Systems East": ["Jordan Feld", "Naomi Tsang", "Luis Arreola"],
    "Health Systems West": ["Grace Okafor", "Ben Halvorsen-Ruiz", "Sofia Marchetti"],
}
EAST_REGIONS = ["Northeast", "Southeast", "Midwest"]
WEST_REGIONS = ["West", "Midwest"]
STATES = {"Northeast": ["NY", "NJ", "MA", "PA", "CT"], "Southeast": ["NC", "GA", "FL", "VA", "TN"],
          "Midwest": ["IL", "OH", "MN", "MI", "WI", "IN"], "West": ["CA", "WA", "CO", "AZ", "OR", "TX"]}

PHARMA_PREFIX = ["Halvorsen", "Corvane", "Ardent", "Brightline", "Calyx", "Dorsey", "Ellery", "Fenwick", "Galloway", "Harlow",
                 "Ironwood", "Juniper", "Kestrel", "Lindqvist", "Marrow", "Northcote", "Oakhurst", "Pellam", "Quillon", "Rosslyn",
                 "Sable", "Tamsin", "Ulster", "Verano", "Westbrook", "Ashcombe", "Beaumont", "Caldera", "Driftwood", "Eastgate",
                 "Fairchild", "Greystone", "Hollis", "Ingram", "Jacoby", "Kingsley", "Larkin", "Merriweather", "Norwood", "Osgood",
                 "Prentiss", "Radley", "Stirling", "Thornbury", "Underhill", "Vantage", "Whitlock", "Yardley", "Zephyr", "Alder",
                 "Barrow", "Cromwell", "Danforth", "Elmsworth", "Fallon", "Gresham", "Hartwell", "Isling", "Jarrow", "Kendrick",
                 "Lowell", "Mansfield", "Newcombe", "Orrin", "Paxton", "Quincey", "Ravelle", "Sutter", "Tolliver", "Upton",
                 "Varden", "Wexley", "Amberly", "Bexley", "Carrow", "Dunmore", "Evander", "Farrow", "Glenmoor", "Haverly",
                 "Ivanhoe", "Jessup", "Kerrigan", "Lanyard", "Morrow"]
PHARMA_SUFFIX = ["Therapeutics", "Biosciences", "Pharma", "Biologics", "Labs", "Oncology", "Health", "Medicines"]
HS_PLACE = ["Lakeshore", "Pinecrest", "Brightwater", "Cedar Ridge", "Tidewater", "Blue Ridge", "Summit", "Harbor Point", "Prairie",
            "Riverbend", "Stonebridge", "Oak Valley", "Silver Lake", "Copper Creek", "Granite Peak", "Meadowbrook", "Maplewood",
            "Bayview", "Highland", "Clearwater", "Foxhollow", "Ironbridge", "Westfield", "Northgate", "Sandpiper", "Cypress",
            "Laurel", "Redwood", "Elk River", "Birchwood", "Canyon", "Seaside", "Willow Creek", "Timberline", "Fairhaven",
            "Greenfield", "Crescent", "Sierra", "Delta", "Evergreen", "Haven", "Juniper Hills", "Kingsport", "Lighthouse",
            "Mission", "Northern Lakes", "Orchard", "Peninsula", "Quarry", "Ridgeway", "Southport", "Three Rivers", "Union",
            "Valley", "Waterford"]
HS_SUFFIX = ["Regional Health", "Health System", "Medical Center", "Health Partners", "Hospital Network"]
PHARMA_SEG = (["Top 20 Pharma", "Mid-size Pharma", "Specialty Biotech"], [0.25, 0.40, 0.35])
HS_SEG = (["Academic Medical Center", "Regional Health System", "Community Hospital"], [0.25, 0.45, 0.30])
SIGNATORIES = ["VP Marketing", "Chief Commercial Officer", "Director of Brand Marketing", "VP Talent Acquisition",
               "Chief Human Resources Officer", "Director of Physician Recruitment", "Head of Omnichannel Engagement", "VP Medical Affairs"]
FIRST = ["Alex", "Jamie", "Morgan", "Taylor", "Casey", "Riley", "Jordan", "Avery", "Quinn", "Reese", "Drew", "Sam", "Kendall", "Blake", "Rowan", "Devin"]
LAST = ["Patel", "Nguyen", "Garcia", "Kim", "Johnson", "Brown", "Martin", "Lee", "Walker", "Young", "Hernandez", "King", "Wright", "Scott", "Green", "Adams"]

PRODUCTS = [
    # id, name, family, unit, list price, rev rec, description
    ("P-01", "Specialty Targeted Campaign", "Pharma Marketing", "Campaign", 150000, "Ratably over the campaign period",
     "Targeted digital campaign delivered to clinicians in a named specialty across the network feed and newsletter."),
    ("P-02", "Sponsored Content", "Pharma Marketing", "Placement", 60000, "Ratably over the campaign period",
     "Brand-sponsored clinical content placed in the specialty feed with engagement reporting."),
    ("P-03", "Clinical Newsletter Placement", "Pharma Marketing", "Insertion", 25000, "Point in time at placement",
     "Sponsored insertion in the weekly specialty newsletter."),
    ("P-04", "Peer Discussion Program", "Pharma Marketing", "Program", 90000, "Ratably over the campaign period",
     "Moderated peer-to-peer clinician discussion program on a therapeutic area."),
    ("P-05", "Recruiting Placement", "Health System Talent", "Placement", 18000, "Point in time at placement",
     "Targeted physician or APP job placement promoted to matching clinicians."),
    ("P-06", "Employer Branding", "Health System Talent", "Campaign", 45000, "Ratably over the campaign period",
     "Employer brand campaign for a health system across the network."),
    ("P-07", "Residency Navigator Sponsorship", "Health System Talent", "Sponsorship", 35000, "Ratably over the campaign period",
     "Sponsorship of residency program profiles and navigator content."),
    ("P-08", "Physician Directory Enhanced Profile", "Health System Talent", "Profile-Year", 6000, "Ratably over the campaign period",
     "Enhanced health system profile in the clinician directory for one year."),
]
PHARMA_PRODUCTS = ["P-01", "P-02", "P-03", "P-04"]
HS_PRODUCTS = ["P-05", "P-06", "P-07", "P-08"]
SPECIALTIES = ["Cardiology", "Oncology", "Endocrinology", "Neurology", "Rheumatology", "Dermatology", "Gastroenterology",
               "Pulmonology", "Psychiatry", "Nephrology", "Hematology", "Primary Care"]

CONTROLS = [
    # control_id, check_type, check_name, field_name, systems_compared, tolerance, default_severity, high_usd, owning_team, sox_ref, description, corrective_system
    ("RC-01", "TCV_MISMATCH", "Contract value vs Salesforce bookings", "total_contract_value", "Contract vs Salesforce", "100 USD", "Medium", 100000, "Sales Ops", "OTC-04 Order entry accuracy",
     "The sum of closed-won opportunity amounts for the agreement (original plus amendment increments) must equal the total contract value stated in the latest signed document within 100 USD.", "Salesforce"),
    ("RC-02", "PRODUCT_LINE_COUNT_MISMATCH", "Contract products vs Salesforce products", "products", "Contract vs Salesforce", "exact match", "Medium", None, "Sales Ops", "OTC-04 Order entry accuracy",
     "The distinct products across the agreement's opportunities must equal the distinct products in Exhibit A of the latest signed document.", "Salesforce"),
    ("RC-03", "OPPORTUNITY_WITHOUT_CONTRACT_LINK", "Opportunity not linked to a signed agreement", "linked_contract_number", "Salesforce vs Contract", "exact match", "Medium", None, "Sales Ops", "OTC-02 Completeness of contract linkage",
     "Every closed-won opportunity must reference a signed document of the same customer; a blank or wrong contract number breaks the lineage from contract to order.", "Salesforce"),
    ("RC-04", "AMENDMENT_NOT_IN_SALESFORCE", "Amendment not booked in Salesforce", "amendment", "Contract vs Salesforce", "exact match", "High", None, "Sales Ops", "OTC-07 Amendment processing",
     "Every signed amendment must have its own closed-won opportunity linked to the amendment document number.", "Salesforce"),
    ("RC-05", "TERM_END_DATE_MISMATCH", "Contract end date vs NetSuite service end", "end_date", "Contract vs NetSuite", "exact match", "High", None, "Revenue Accounting", "OTC-09 Revenue schedule accuracy",
     "The NetSuite service end date must equal the end date in the latest signed document; a stale end date misstates the revenue schedule.", "NetSuite"),
    ("RC-06", "AMENDMENT_NOT_IN_NETSUITE", "Amendment not reflected in NetSuite", "amendment", "Contract vs NetSuite", "exact match", "High", 100000, "Revenue Accounting", "OTC-07 Amendment processing",
     "The last Boomi sync of the agreement's sales order(s) must be on or after the signature date of the latest amendment; otherwise NetSuite still carries the prior terms.", "NetSuite"),
    ("RC-07", "DUPLICATE_SALES_ORDERS", "More than one sales order per agreement", "sales_order", "NetSuite vs Contract", "one order per agreement", "High", 100000, "Revenue Accounting", "OTC-05 Sales order uniqueness",
     "An agreement must map to exactly one NetSuite sales order; a second order double-books revenue and billing.", "NetSuite"),
    ("RC-08", "SALES_ORDER_WITHOUT_OPPORTUNITY", "Sales order not linked to an opportunity", "opportunity_id", "NetSuite vs Salesforce", "exact match", "Medium", None, "Revenue Accounting", "OTC-02 Completeness of contract linkage",
     "Every NetSuite sales order must carry the Salesforce opportunity id Boomi created it from.", "NetSuite"),
    ("RC-09", "PAYMENT_TERMS_MISMATCH", "Payment terms vs NetSuite", "payment_terms", "Contract vs NetSuite", "exact match", "Medium", None, "Billing", "OTC-11 Billing terms accuracy",
     "NetSuite payment terms must equal the payment terms in the latest signed document.", "NetSuite"),
    ("RC-10", "BILLING_FREQUENCY_MISMATCH", "Billing frequency vs NetSuite schedule type", "billing_frequency", "Contract vs NetSuite", "exact match", "Medium", None, "Billing", "OTC-11 Billing terms accuracy",
     "The NetSuite billing schedule type must equal the billing frequency in the latest signed document.", "NetSuite"),
    ("RC-11", "MISSING_BILLING_MILESTONE", "Contract milestone missing from NetSuite billing", "billing_milestone", "Contract vs NetSuite", "7 days and 1 USD", "Medium", 100000, "Billing", "OTC-12 Billing schedule completeness",
     "Every milestone in Exhibit B of the latest signed document must have a NetSuite bill for the same amount within 7 days of the scheduled date.", "NetSuite"),
]

MILESTONE_NAMES = ["Signature", "Campaign launch", "Mid-flight report", "Flight 2 launch", "Program completion", "Final report"]

# Seeded drift registry: chain contract_number -> set of category letters. Filled by generate_all().
SEEDED: dict[str, set[str]] = {}


def rng(tag: str) -> np.random.Generator:
    return _seeded_rng(SEED, tag)


def _ts(d: date, hour: int = 9, minute: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, hour, minute)


def _add_months(d: date, n: int) -> date:
    y, m = divmod(d.month - 1 + n, 12)
    y += d.year
    m += 1
    day = min(d.day, [31, 29 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return date(y, m, day)


def _round_cents(x: float) -> float:
    return float(round(x + 1e-9, 2))


def _pick(g, items, p=None):
    return items[int(g.choice(len(items), p=p))]


# ---------------------------------------------------------------- dimensions
def build_customers() -> pd.DataFrame:
    g = rng("customers")
    rows = []
    pn = list(PHARMA_PREFIX)
    g.shuffle(pn)
    used = set()
    i = 0
    for k in range(85):
        cid = f"CUST-{k + 1:04d}"
        if cid == HERO_CUSTOMER_ID:
            name, seg, pod, region = HERO_CUSTOMER, "Mid-size Pharma", "Pharma East", "Northeast"
            owner = HERO_OWNER
        else:
            while True:
                name = f"{pn[i % len(pn)]} {_pick(g, PHARMA_SUFFIX)}"
                i += 1
                if name not in used and name != HERO_CUSTOMER:
                    break
            seg = _pick(g, *PHARMA_SEG)
            pod = "Pharma East" if g.random() < 0.55 else "Pharma West"
            region = _pick(g, EAST_REGIONS if pod.endswith("East") else WEST_REGIONS)
            owner = _pick(g, OWNERS[pod], p=[0.34, 0.36, 0.30] if pod == "Pharma East" else None)
        used.add(name)
        rows.append((cid, name, "Pharma", seg, owner, pod, region, _pick(g, STATES[region])))
    hp = list(HS_PLACE)
    g.shuffle(hp)
    for k in range(55):
        cid = f"CUST-{86 + k:04d}"
        while True:
            name = f"{hp[k % len(hp)]} {_pick(g, HS_SUFFIX)}"
            if name not in used:
                break
            hp[k % len(hp)] = hp[k % len(hp)] + " North"
        used.add(name)
        seg = _pick(g, *HS_SEG)
        pod = "Health Systems East" if g.random() < 0.55 else "Health Systems West"
        region = _pick(g, EAST_REGIONS if pod.endswith("East") else WEST_REGIONS)
        rows.append((cid, name, "Health System", seg, _pick(g, OWNERS[pod]), pod, region, _pick(g, STATES[region])))
    df = pd.DataFrame(rows, columns=["CUSTOMER_ID", "CUSTOMER_NAME", "CUSTOMER_TYPE", "SEGMENT", "ACCOUNT_OWNER", "SALES_POD", "REGION", "HQ_STATE"])
    df["CUSTOMER_SINCE"] = pd.NaT
    return df


def build_products() -> pd.DataFrame:
    return pd.DataFrame(PRODUCTS, columns=["PRODUCT_ID", "PRODUCT_NAME", "PRODUCT_FAMILY", "UNIT_OF_MEASURE", "LIST_PRICE", "REVENUE_RECOGNITION", "DESCRIPTION"])


def build_controls() -> pd.DataFrame:
    return pd.DataFrame(CONTROLS, columns=["CONTROL_ID", "CHECK_TYPE", "CHECK_NAME", "FIELD_NAME", "SYSTEMS_COMPARED", "TOLERANCE", "DEFAULT_SEVERITY",
                                           "HIGH_SEVERITY_USD", "OWNING_TEAM", "SOX_CONTROL_REF", "DESCRIPTION", "CORRECTIVE_SYSTEM"])


# ---------------------------------------------------------------- contract truth (in-memory model)
class Doc:
    """One signed document (original or amendment) with its full restated exhibits."""

    def __init__(self):
        self.contract_id = ""
        self.number = ""
        self.version = 0
        self.type = "New"
        self.signed = None
        self.effective = None
        self.end = None
        self.term = 0
        self.payment_terms = "Net 30"
        self.billing = "Quarterly"
        self.auto_renew = False
        self.notice = 60
        self.signatory = ""
        self.lines: list[dict] = []        # {product_id, name, specialty, qty, price, start, end}
        self.schedule: list[dict] = []     # {n, desc, date, amount}
        self.special = None
        self.confidence = 0.95
        self.change_kind = None            # add_product | extend_term | price_change | billing_change (amendments)

    @property
    def tcv(self) -> float:
        return _round_cents(sum(l["qty"] * l["price"] for l in self.lines))


class Chain:
    def __init__(self):
        self.number = ""
        self.customer = None               # row of CUSTOMERS
        self.docs: list[Doc] = []
        self.tags: set[str] = set()

    @property
    def original(self) -> Doc:
        return self.docs[0]

    @property
    def latest(self) -> Doc:
        return self.docs[-1]


def _make_schedule(doc: Doc, g, keep: list[dict] | None = None, from_date: date | None = None) -> list[dict]:
    """Build Exhibit B for a document. `keep` = milestones already billed under the
    previous version that the restated schedule carries forward unchanged."""
    total = doc.tcv
    keep = list(keep or [])
    kept_total = _round_cents(sum(m["amount"] for m in keep))
    remaining = _round_cents(total - kept_total)
    start = from_date or doc.effective
    out = [dict(m) for m in keep]
    n0 = len(out)
    if remaining <= 0:
        # a price reduction: restate the last kept milestone downwards instead
        if out:
            out[-1]["amount"] = _round_cents(out[-1]["amount"] + remaining)
        for i, m in enumerate(out):
            m["n"] = i + 1
        return out
    if doc.billing == "Upfront":
        out.append({"desc": "Signature" if not keep else "Amendment execution", "date": start, "amount": remaining})
    elif doc.billing in ("Quarterly", "Monthly"):
        step = 3 if doc.billing == "Quarterly" else 1
        dates = []
        d = start
        while d < doc.end:
            dates.append(d)
            d = _add_months(d, step)
        if not dates:
            dates = [start]
        each = _round_cents(remaining / len(dates))
        amts = [each] * len(dates)
        amts[-1] = _round_cents(remaining - each * (len(dates) - 1))
        label = "Quarterly instalment" if doc.billing == "Quarterly" else "Monthly instalment"
        for i, (dd, a) in enumerate(zip(dates, amts)):
            out.append({"desc": f"{label} {n0 + i + 1}", "date": dd, "amount": a})
    else:  # Milestone
        k = int(g.integers(3, 6))
        span_days = max((doc.end - start).days, 30)
        weights = g.dirichlet(np.ones(k) * 2.0)
        amts = [_round_cents(remaining * w) for w in weights]
        amts[-1] = _round_cents(remaining - sum(amts[:-1]))
        names = (["Amendment execution"] if keep else ["Signature"]) + MILESTONE_NAMES[1:]
        for i in range(k):
            dd = start + timedelta(days=int(round(span_days * i / max(k - 1, 1)))) if k > 1 else start
            out.append({"desc": names[min(i, len(names) - 1)], "date": dd, "amount": amts[i]})
    for i, m in enumerate(out):
        m["n"] = i + 1
    return out


def _new_lines(cust, g, n: int | None = None, start: date = None, end: date = None) -> list[dict]:
    pharma = cust.CUSTOMER_TYPE == "Pharma"
    pool = PHARMA_PRODUCTS if pharma else HS_PRODUCTS
    n = n or int(g.choice([1, 2, 3, 4], p=[0.25, 0.40, 0.25, 0.10]))
    picks = list(g.choice(pool, size=min(n, len(pool)), replace=False))
    big = cust.SEGMENT in ("Top 20 Pharma", "Academic Medical Center")
    lines = []
    for pid in picks:
        p = next(x for x in PRODUCTS if x[0] == pid)
        base_qty = {"P-01": (2, 10), "P-02": (2, 8), "P-03": (4, 16), "P-04": (1, 4), "P-05": (4, 30), "P-06": (1, 4), "P-07": (1, 3), "P-08": (1, 6)}[pid]
        qty = int(g.integers(base_qty[0], base_qty[1] + 1)) * (2 if big else 1)
        price = _round_cents(p[4] * float(g.choice([0.85, 0.9, 0.95, 1.0, 1.0, 1.05, 1.1])))
        lines.append({"product_id": pid, "name": p[1], "specialty": _pick(g, SPECIALTIES) if pid in ("P-01", "P-02", "P-04") else None,
                      "qty": qty, "price": price, "start": start, "end": end})
    return lines


def _original_doc(cust, number: str, g, signed: date, term: int | None = None, billing: str | None = None,
                  terms: str | None = None, ctype: str = "New") -> Doc:
    d = Doc()
    d.number = number
    d.version = 0
    d.type = ctype
    d.signed = signed
    d.effective = signed + timedelta(days=int(g.integers(3, 35)))
    d.term = term or int(g.choice([12, 12, 18, 24, 24, 36], p=[0.30, 0.15, 0.15, 0.20, 0.10, 0.10]))
    d.end = _add_months(d.effective, d.term) - timedelta(days=1)
    pharma = cust.CUSTOMER_TYPE == "Pharma"
    d.billing = billing or (_pick(g, ["Milestone", "Quarterly", "Upfront", "Monthly"], p=[0.45, 0.35, 0.10, 0.10]) if pharma
                            else _pick(g, ["Upfront", "Quarterly", "Milestone", "Monthly"], p=[0.40, 0.30, 0.20, 0.10]))
    d.payment_terms = terms or _pick(g, ["Net 30", "Net 45", "Net 60"], p=[0.60, 0.30, 0.10])
    d.auto_renew = bool(g.random() < (0.35 if pharma else 0.55))
    d.notice = int(g.choice([30, 60, 90]))
    d.signatory = f"{_pick(g, FIRST)} {_pick(g, LAST)}, {_pick(g, SIGNATORIES)}"
    d.lines = _new_lines(cust, g, start=d.effective, end=d.end)
    d.schedule = _make_schedule(d, g)
    d.confidence = float(round(g.uniform(0.86, 0.995), 3))
    if g.random() < 0.25:
        d.special = _pick(g, ["Price protection: unit prices fixed for the term.", "Make-good clause: under-delivered impressions credited at the next milestone.",
                              "Exclusivity: no competing brand in the targeted specialty feed during the flight.", "Early termination for convenience with 90 days notice and payment for services rendered.",
                              "Credits for amendments applied to the final milestone."])
    return d


def _amend(chain: Chain, g, signed: date, kind: str | None = None) -> Doc:
    prev = chain.latest
    d = Doc()
    d.version = prev.version + 1
    d.number = f"{chain.number}-A{d.version}"
    d.type = "Amendment"
    d.signed = signed
    d.effective = prev.effective
    d.end = prev.end
    d.term = prev.term
    d.payment_terms = prev.payment_terms
    d.billing = prev.billing
    d.auto_renew = prev.auto_renew
    d.notice = prev.notice
    d.signatory = prev.signatory
    d.lines = [dict(l) for l in prev.lines]
    d.confidence = float(round(g.uniform(0.84, 0.99), 3))
    kind = kind or _pick(g, ["add_product", "extend_term", "price_change", "billing_change"], p=[0.40, 0.30, 0.20, 0.10])
    d.change_kind = kind
    cust = chain.customer
    pool = PHARMA_PRODUCTS if cust.CUSTOMER_TYPE == "Pharma" else HS_PRODUCTS
    if kind == "add_product":
        have = {l["product_id"] for l in d.lines}
        cands = [p for p in pool if p not in have]
        if cands:
            new = _new_lines(cust, g, n=1, start=signed + timedelta(days=14), end=d.end)
            new[0]["product_id"] = cands[int(g.integers(0, len(cands)))]
            p = next(x for x in PRODUCTS if x[0] == new[0]["product_id"])
            new[0]["name"] = p[1]
            new[0]["price"] = _round_cents(p[4] * float(g.choice([0.9, 0.95, 1.0, 1.05])))
            new[0]["specialty"] = _pick(g, SPECIALTIES) if p[0] in ("P-01", "P-02", "P-04") else None
            d.lines.append(new[0])
        else:
            kind = "extend_term"
            d.change_kind = kind
    if kind == "extend_term":
        months = int(g.choice([3, 6, 6, 12]))
        d.end = _add_months(prev.end + timedelta(days=1), months) - timedelta(days=1)
        d.term = prev.term + months
        # pro-rata increase on the largest line
        idx = max(range(len(d.lines)), key=lambda i: d.lines[i]["qty"] * d.lines[i]["price"])
        extra = max(1, int(round(d.lines[idx]["qty"] * months / prev.term)))
        d.lines[idx] = dict(d.lines[idx], qty=d.lines[idx]["qty"] + extra, end=d.end)
    if kind == "price_change":
        idx = max(range(len(d.lines)), key=lambda i: d.lines[i]["qty"] * d.lines[i]["price"])
        factor = float(g.choice([0.92, 0.95, 1.05, 1.08]))
        d.lines[idx] = dict(d.lines[idx], price=_round_cents(d.lines[idx]["price"] * factor))
        d.special = "Unit price on the principal line restated; credit or surcharge applied to the next milestone."
    if kind == "billing_change":
        d.billing = "Milestone" if prev.billing != "Milestone" else "Quarterly"
    # restated schedule: keep milestones already billable before the amendment, rebuild the rest
    kept = [m for m in prev.schedule if m["date"] < signed]
    d.schedule = _make_schedule(d, g, keep=kept, from_date=max(signed + timedelta(days=12), prev.effective))
    return d


def build_chains(customers: pd.DataFrame) -> list[Chain]:
    g = rng("chains")
    chains: list[Chain] = []
    seq = {}
    by_type = {t: customers[customers.CUSTOMER_TYPE == t] for t in ("Pharma", "Health System")}
    n_orig = 270
    # every customer gets at least one agreement; pharma gets more
    cust_rows = []
    for _, c in customers.iterrows():
        cust_rows.append(c)
    extra = 270 - len(cust_rows)
    pharma_idx = [i for i in by_type["Pharma"].index if customers.loc[i].CUSTOMER_ID != HERO_CUSTOMER_ID]
    hs_idx = list(by_type["Health System"].index)
    for _ in range(extra):
        pool = pharma_idx if g.random() < 0.72 else hs_idx
        cust_rows.append(customers.loc[pool[int(g.integers(0, len(pool)))]])
    # signing dates: spread 2024-01 .. 2026-09 with more volume later
    days = (LAST_SIGNING - START).days
    hero_done = False
    for c in cust_rows:
        ch = Chain()
        ch.customer = c
        if c.CUSTOMER_ID == HERO_CUSTOMER_ID and not hero_done:
            hero_done = True
            chains.append(_build_hero(ch, g))
            continue
        signed = START + timedelta(days=int(days * (g.random() ** 0.8)))
        year = signed.year
        seq[year] = seq.get(year, 0) + 1
        number = f"MCN-{year}-{seq[year]:04d}"
        if number == HERO_CONTRACT_NUMBER:
            seq[year] += 1
            number = f"MCN-{year}-{seq[year]:04d}"
        ch.number = number
        ctype = "Renewal" if (g.random() < 0.26 and signed > date(2024, 10, 1)) else "New"
        ch.docs.append(_original_doc(c, number, g, signed, ctype=ctype))
        chains.append(ch)
    # amendments: ~90 chains, 1-3 each, pharma-skewed, only on agreements with room before AS_OF
    cands = [ch for ch in chains if ch.customer.CUSTOMER_ID != HERO_CUSTOMER_ID and ch.original.signed < date(2026, 7, 1)]
    weights = np.array([1.6 if ch.customer.CUSTOMER_TYPE == "Pharma" else 0.7 for ch in cands])
    weights /= weights.sum()
    picked = g.choice(len(cands), size=min(112, len(cands)), replace=False, p=weights)
    total_amend = 0
    for i in picked:
        ch = cands[int(i)]
        n_am = int(g.choice([1, 2, 3], p=[0.50, 0.32, 0.18]))
        t = ch.original.signed
        for k in range(n_am):
            gap = int(g.integers(45, 240))
            t = t + timedelta(days=gap)
            if t > LAST_SIGNING or t > ch.latest.end - timedelta(days=30):
                break
            ch.docs.append(_amend(ch, g, t))
            total_amend += 1
    return chains


def _build_hero(ch: Chain, g) -> Chain:
    """Halvorsen Therapeutics: MSA + three amendments (CP2). Values are exact."""
    c = ch.customer
    ch.number = HERO_CONTRACT_NUMBER
    ch.tags.add("H")
    msa = Doc()
    msa.number = HERO_CONTRACT_NUMBER
    msa.version = 0
    msa.type = "New"
    msa.signed = HERO_MSA_SIGNED
    msa.effective = date(2025, 3, 1)
    msa.term = 18
    msa.end = date(2026, 8, 31)
    msa.payment_terms = "Net 30"
    msa.billing = "Quarterly"
    msa.auto_renew = False
    msa.notice = 90
    msa.signatory = "Renata Kowalski, VP Omnichannel Marketing"
    msa.lines = [
        {"product_id": "P-01", "name": "Specialty Targeted Campaign", "specialty": "Cardiology", "qty": 8, "price": 150000.0, "start": msa.effective, "end": msa.end},
        {"product_id": "P-03", "name": "Clinical Newsletter Placement", "specialty": "Cardiology", "qty": 12, "price": 25000.0, "start": msa.effective, "end": msa.end},
        {"product_id": "P-04", "name": "Peer Discussion Program", "specialty": "Cardiology", "qty": 3, "price": 100000.0, "start": msa.effective, "end": msa.end},
    ]
    assert msa.tcv == 1800000.0
    msa.schedule = [{"n": i + 1, "desc": f"Quarterly instalment {i + 1}", "date": _add_months(msa.effective, 3 * i), "amount": 300000.0} for i in range(6)]
    msa.confidence = 0.978
    msa.special = "Exclusivity: no competing cardiology brand in the targeted specialty feed during the flight."
    ch.docs.append(msa)

    a1 = Doc()
    a1.number = f"{HERO_CONTRACT_NUMBER}-A1"
    a1.version = 1
    a1.type = "Amendment"
    a1.signed = HERO_A1_SIGNED
    a1.effective, a1.end, a1.term = msa.effective, msa.end, msa.term
    a1.payment_terms, a1.billing, a1.auto_renew, a1.notice, a1.signatory = "Net 30", "Quarterly", False, 90, msa.signatory
    a1.change_kind = "add_product"
    a1.lines = [dict(l) for l in msa.lines] + [{"product_id": "P-02", "name": "Sponsored Content", "specialty": "Cardiology", "qty": 5, "price": 90000.0, "start": date(2025, 9, 1), "end": msa.end}]
    assert a1.tcv == 2250000.0
    a1.schedule = [dict(m) for m in msa.schedule] + [{"n": 7 + i, "desc": f"Sponsored Content quarterly instalment {i + 1}", "date": _add_months(date(2025, 9, 1), 3 * i), "amount": 112500.0} for i in range(4)]
    a1.confidence = 0.962
    a1.special = "Adds Sponsored Content (5 placements) billed in four quarterly instalments from 1 September 2025."
    ch.docs.append(a1)

    a2 = Doc()
    a2.number = f"{HERO_CONTRACT_NUMBER}-A2"
    a2.version = 2
    a2.type = "Amendment"
    a2.signed = HERO_A2_SIGNED
    a2.effective = msa.effective
    a2.end = date(2027, 2, 28)
    a2.term = 24
    a2.payment_terms, a2.billing, a2.auto_renew, a2.notice, a2.signatory = "Net 30", "Milestone", False, 90, msa.signatory
    a2.change_kind = "extend_term"
    a2.lines = [dict(l) for l in a1.lines]
    a2.lines[0] = dict(a2.lines[0], qty=12, end=a2.end)   # +4 campaign units = +600k
    assert a2.tcv == 2850000.0
    billed = [m for m in a1.schedule if m["date"] < HERO_A2_SIGNED]   # 300k x3 + 112.5k x1 = 1,012,500
    a2.schedule = [dict(m) for m in billed] + [
        {"desc": "Amendment 2 execution", "date": date(2025, 11, 15), "amount": 500000.0},
        {"desc": "Cardiology campaign flight 2 launch", "date": date(2026, 3, 1), "amount": 600000.0},
        {"desc": "Mid-flight report", "date": date(2026, 7, 1), "amount": 400000.0},
        {"desc": "Program completion", "date": date(2027, 2, 28), "amount": 337500.0},
    ]
    for i, m in enumerate(a2.schedule):
        m["n"] = i + 1
    assert _round_cents(sum(m["amount"] for m in a2.schedule)) == 2850000.0
    a2.confidence = 0.941
    a2.special = "Term extended to 28 February 2027; billing converted from quarterly instalments to milestones for all amounts not yet invoiced."
    ch.docs.append(a2)

    a3 = Doc()
    a3.number = f"{HERO_CONTRACT_NUMBER}-A3"
    a3.version = 3
    a3.type = "Amendment"
    a3.signed = HERO_A3_SIGNED
    a3.effective, a3.end, a3.term = a2.effective, a2.end, a2.term
    a3.payment_terms, a3.billing, a3.auto_renew, a3.notice, a3.signatory = "Net 45", "Milestone", False, 90, msa.signatory
    a3.change_kind = "price_change"
    a3.lines = [dict(l) for l in a2.lines]
    a3.lines[0] = dict(a3.lines[0], price=140000.0)   # 12 x 140k = 1.68M (-120k)
    assert a3.tcv == 2730000.0
    a3.schedule = [dict(m) for m in a2.schedule]
    a3.schedule[-1] = dict(a3.schedule[-1], amount=217500.0)
    assert _round_cents(sum(m["amount"] for m in a3.schedule)) == 2730000.0
    a3.confidence = 0.955
    a3.special = "Unit price of the Specialty Targeted Campaign reduced to 140,000 USD; the 120,000 USD credit is applied to the Program completion milestone. Payment terms changed to Net 45."
    ch.docs.append(a3)
    return ch


# ---------------------------------------------------------------- systems built from the truth
class Systems:
    def __init__(self):
        self.contracts = []
        self.lines = []
        self.schedule = []
        self.opps = []
        self.opp_products = []
        self.sos = []
        self.so_lines = []
        self.bills = []


def _envelope(g) -> str:
    return "-".join("".join(g.choice(list("0123456789abcdef"), size=n)) for n in (8, 4, 4, 4, 12))


def _emit_contract_rows(sy: Systems, ch: Chain, g, ids: dict):
    for d in ch.docs:
        ids["ctr"] += 1
        d.contract_id = f"CTR-{ids['ctr']:05d}"
    for d in ch.docs:
        parent = None if d.version == 0 else ch.original.contract_id
        sy.contracts.append({
            "CONTRACT_ID": d.contract_id, "CUSTOMER_ID": ch.customer.CUSTOMER_ID, "CONTRACT_NUMBER": d.number,
            "DOCUSIGN_ENVELOPE_ID": _envelope(g), "CONTRACT_TYPE": d.type, "PARENT_CONTRACT_ID": parent,
            "AMENDMENT_NUMBER": d.version, "SIGNED_DATE": d.signed, "EFFECTIVE_DATE": d.effective, "END_DATE": d.end,
            "TERM_MONTHS": d.term, "TOTAL_CONTRACT_VALUE": d.tcv, "CURRENCY": "USD", "PAYMENT_TERMS": d.payment_terms,
            "BILLING_FREQUENCY": d.billing, "AUTO_RENEW": d.auto_renew, "CANCELLATION_NOTICE_DAYS": d.notice,
            "SIGNATORY_NAME": d.signatory, "PRODUCT_SUMMARY": _summary(d), "SPECIAL_TERMS": d.special,
            "EXTRACTED_AT": _ts(d.signed + timedelta(days=int(g.integers(0, 3))), int(g.integers(8, 18)), int(g.integers(0, 60))),
            "EXTRACTION_CONFIDENCE": d.confidence, "PDF_FILE_NAME": f"{d.number}.pdf",
        })
        for i, l in enumerate(d.lines):
            ids["line"] += 1
            sy.lines.append({"LINE_ID": f"CL-{ids['line']:06d}", "CONTRACT_ID": d.contract_id, "LINE_NUMBER": i + 1, "PRODUCT_ID": l["product_id"],
                             "PRODUCT_NAME": l["name"], "SPECIALTY_TARGETED": l["specialty"], "QUANTITY": l["qty"], "UNIT_PRICE": l["price"],
                             "LINE_AMOUNT": _round_cents(l["qty"] * l["price"]), "START_DATE": l["start"] or d.effective, "END_DATE": l["end"] or d.end})
        for m in d.schedule:
            ids["ms"] += 1
            sy.schedule.append({"SCHEDULE_ID": f"CB-{ids['ms']:06d}", "CONTRACT_ID": d.contract_id, "MILESTONE_NUMBER": m["n"],
                                "MILESTONE_DESCRIPTION": m["desc"], "SCHEDULED_DATE": m["date"], "SCHEDULED_AMOUNT": m["amount"]})


def _summary(d: Doc) -> str:
    parts = []
    for l in d.lines:
        s = f"{l['qty']} x {l['name']}"
        if l["specialty"]:
            s += f" ({l['specialty']})"
        parts.append(s)
    head = "Amendment %d: " % d.version if d.version else ""
    return (head + "; ".join(parts))[:400]


def _opp_name(ch: Chain, d: Doc) -> str:
    if d.version:
        return f"{ch.customer.CUSTOMER_NAME} - Amendment {d.version}"
    main = max(d.lines, key=lambda l: l["qty"] * l["price"])
    tag = f"{main['specialty']} {main['name']}" if main["specialty"] else main["name"]
    return f"{ch.customer.CUSTOMER_NAME} - {tag} {d.signed.year}"[:120]


def _emit_opp(sy: Systems, ch: Chain, d: Doc, g, ids: dict, *, amount: float | None = None, products: list[dict] | None = None,
              linked: str | None = "auto", close: date | None = None) -> str:
    ids["opp"] += 1
    oid = f"006Q0000{ids['opp']:07d}"
    prev_tcv = ch.docs[d.version - 1].tcv if d.version else 0.0
    amt = _round_cents(d.tcv - prev_tcv) if amount is None else amount
    close = close or d.signed + timedelta(days=int(g.integers(0, 3)))
    sy.opps.append({"OPPORTUNITY_ID": oid, "CUSTOMER_ID": ch.customer.CUSTOMER_ID, "OPPORTUNITY_NAME": _opp_name(ch, d),
                    "OPPORTUNITY_TYPE": "Amendment" if d.version else ("Renewal" if d.type == "Renewal" else "New Business"),
                    "STAGE": "Closed Won", "AMOUNT": amt, "CLOSE_DATE": close, "CONTRACT_START_DATE": d.effective, "CONTRACT_END_DATE": d.end,
                    "TERM_MONTHS": d.term, "OWNER": ch.customer.ACCOUNT_OWNER,
                    "LINKED_CONTRACT_NUMBER": d.number if linked == "auto" else linked,
                    "LAST_MODIFIED_DATE": _ts(close + timedelta(days=int(g.integers(0, 20))), int(g.integers(8, 19)), int(g.integers(0, 60)))})
    prods = products if products is not None else _delta_products(ch, d)
    for p in prods:
        ids["op"] += 1
        sy.opp_products.append({"OPP_PRODUCT_ID": f"00kQ0000{ids['op']:07d}", "OPPORTUNITY_ID": oid, "PRODUCT_NAME": p["name"],
                                "QUANTITY": p["qty"], "UNIT_PRICE": p["price"], "TOTAL_PRICE": _round_cents(p["qty"] * p["price"])})
    return oid


def _delta_products(ch: Chain, d: Doc) -> list[dict]:
    """Opportunity products: the full lines for an original; the changed lines (as increments) for an amendment."""
    if d.version == 0:
        return [{"name": l["name"], "qty": l["qty"], "price": l["price"]} for l in d.lines]
    prev = {l["product_id"]: l for l in ch.docs[d.version - 1].lines}
    out = []
    for l in d.lines:
        p = prev.get(l["product_id"])
        if p is None:
            out.append({"name": l["name"], "qty": l["qty"], "price": l["price"]})
        elif l["qty"] != p["qty"]:
            out.append({"name": l["name"], "qty": l["qty"] - p["qty"], "price": l["price"]})
        elif l["price"] != p["price"]:
            out.append({"name": l["name"], "qty": l["qty"], "price": _round_cents(l["price"] - p["price"])})
    if not out:   # billing-only amendment: a zero-value line on the main product
        main = max(d.lines, key=lambda l: l["qty"] * l["price"])
        out.append({"name": main["name"], "qty": 1, "price": 0.0})
    return out


def _emit_so(sy: Systems, ch: Chain, d: Doc, g, ids: dict, *, opp_id: str | None, sync: date, end: date | None = None,
             payment_terms: str | None = None, billing: str | None = None, bills: list[dict] | None = None,
             truncate: int = 0, total: float | None = None) -> str:
    ids["so"] += 1
    sid = f"SO-{10000 + ids['so']}"
    end = end or d.end
    schedule = bills if bills is not None else _ns_bills_from(d, g, billing or d.billing)
    if truncate:
        schedule = schedule[:-truncate]
    tot = total if total is not None else d.tcv
    billed_amt = sum(b["amount"] for b in schedule if b["date"] <= AS_OF)
    status = "Billed" if billed_amt >= tot - 1 else ("Partially Billed" if billed_amt > 0 else "Pending Billing")
    sy.sos.append({"SALES_ORDER_ID": sid, "CUSTOMER_ID": ch.customer.CUSTOMER_ID, "OPPORTUNITY_ID": opp_id,
                   "ORDER_DATE": sync, "ORDER_TOTAL": tot, "START_DATE": d.effective, "END_DATE": end,
                   "PAYMENT_TERMS": payment_terms or d.payment_terms, "BILLING_SCHEDULE_TYPE": billing or d.billing, "STATUS": status,
                   "BOOMI_SYNC_TIMESTAMP": _ts(sync, int(g.integers(1, 6)), int(g.integers(0, 60)))})
    for i, l in enumerate(d.lines):
        ids["sol"] += 1
        sy.so_lines.append({"SO_LINE_ID": f"{sid}-L{i + 1}", "SALES_ORDER_ID": sid, "LINE_NUMBER": i + 1, "ITEM_NAME": l["name"],
                            "QUANTITY": l["qty"], "RATE": l["price"], "AMOUNT": _round_cents(l["qty"] * l["price"])})
    for i, b in enumerate(schedule):
        ids["bill"] += 1
        billed = b["date"] <= AS_OF
        sy.bills.append({"BILL_ID": f"{sid}-B{i + 1}", "SALES_ORDER_ID": sid, "BILL_NUMBER": i + 1, "BILL_DATE": b["date"], "BILL_AMOUNT": b["amount"],
                         "BILLED": billed, "INVOICE_NUMBER": f"INV-{ids['bill'] + 20000}" if billed else None})
    return sid


def _ns_bills_from(d: Doc, g, billing: str) -> list[dict]:
    """NetSuite bills generated from the document schedule (clean case), or a quarterly
    split of the TCV when NetSuite's schedule type differs from the contract."""
    if billing == d.billing:
        return [{"date": m["date"], "amount": m["amount"]} for m in d.schedule]
    dates = []
    t = d.effective
    step = 3 if billing == "Quarterly" else 1
    while t < d.end:
        dates.append(t)
        t = _add_months(t, step)
    each = _round_cents(d.tcv / len(dates))
    amts = [each] * len(dates)
    amts[-1] = _round_cents(d.tcv - each * (len(dates) - 1))
    return [{"date": dd, "amount": a} for dd, a in zip(dates, amts)]


def _choose_drift(chains: list[Chain]) -> None:
    """Tag chains with drift categories (CP1-CP4). Deterministic."""
    g = rng("drift")
    hero = next(ch for ch in chains if "H" in ch.tags)
    pool = [ch for ch in chains if ch is not hero]
    amended = [ch for ch in pool if len(ch.docs) > 1]
    unamended = [ch for ch in pool if len(ch.docs) == 1]
    dana_un = [ch for ch in unamended if ch.customer.ACCOUNT_OWNER == HERO_OWNER]
    dana_am = [ch for ch in amended if ch.customer.ACCOUNT_OWNER == HERO_OWNER]
    other_un = [ch for ch in unamended if ch.customer.ACCOUNT_OWNER != HERO_OWNER]
    other_am = [ch for ch in amended if ch.customer.ACCOUNT_OWNER != HERO_OWNER]
    for lst in (dana_un, dana_am, other_un, other_am):
        g.shuffle(lst)

    def take(lists, n, tag, cond=None):
        """Tag up to n untagged chains, trying the candidate lists in order."""
        if not isinstance(lists, list) or (lists and not isinstance(lists[0], list)):
            lists = [lists]
        out = []
        for lst in lists:
            while lst and len(out) < n:
                ch = lst.pop()
                if ch.tags or (cond and not cond(ch)):
                    continue
                ch.tags.add(tag)
                out.append(ch)
            if len(out) >= n:
                break
        return out

    ext = lambda ch: any(d.change_kind == "extend_term" for d in ch.docs[1:])
    milestone_latest = lambda ch: ch.latest.billing == "Milestone" and len(ch.latest.schedule) >= 3
    many_lines = lambda ch: len(ch.original.lines) >= 2
    four_plus = lambda ch: len(ch.latest.schedule) >= 4

    # Drift is amendment-heavy (CP2 ratio) and Dana-heavy (CP4). Dana: ~14 of her ~30 chains.
    take([dana_am, dana_un], 5, "R")                       # R rounding: 8 total
    take([other_am], 2, "R"); take([other_un], 1, "R")
    take([dana_am, dana_un], 3, "L", many_lines)           # L line drop: 4 total
    take([other_un], 1, "L", many_lines)
    take([dana_am], 2, "E", ext); take([other_am], 4, "E", ext)          # E stale end date: 6 amended
    take([dana_am], 1, "N"); take([other_am], 6, "N")                     # N amendment not in NetSuite: 7 amended
    take([other_am], 3, "D")                                              # D DocuSign-only: 3 amended
    take([dana_am], 1, "P"); take([other_am], 3, "P")                     # P payment terms: 4 amended
    take([other_am, other_un], 5, "F", milestone_latest)                  # F milestone vs quarterly: 5 (amended first)
    take([other_am, other_un], 3, "M", milestone_latest)                  # M milestone amounts differ: 3
    take([dana_am], 1, "T", four_plus); take([other_am, other_un], 4, "T", four_plus)   # T truncated schedule: 5
    take([other_am], 2, "U")                                              # U duplicate order: 2 amended
    take([other_un], 2, "S")                                              # S order without opportunity id: 2
    take([other_un], 2, "O")                                              # O opportunity link problems: 2
    # compound: payment terms also wrong on two E chains
    for ch in [c for c in chains if "E" in c.tags][:2]:
        ch.tags.add("P")
    # Dana Whitfield ends up with at least 15 drifted agreements (rounded amounts) whatever the draw
    dana_all = sorted([c for c in chains if c.customer.ACCOUNT_OWNER == HERO_OWNER and "H" not in c.tags], key=lambda c: c.number)
    for ch in dana_all:
        if sum(1 for c in dana_all if c.tags) >= 15:
            break
        if not ch.tags:
            ch.tags.add("R")
    # one amendment-not-in-NetSuite chain was signed in the last week (the agent's catch)
    recent = sorted([c for c in chains if "N" in c.tags], key=lambda c: c.number)[0]
    prev, last = recent.docs[-2], recent.docs[-1]
    last.signed = date(2026, 9, 25)
    last.schedule = _make_schedule(last, rng("recent_amendment"), keep=[m for m in prev.schedule if m["date"] < last.signed],
                                   from_date=last.signed + timedelta(days=12))
    recent.tags.add("W")
    for ch in chains:
        if ch.tags:
            SEEDED[ch.number] = set(ch.tags)


def build_systems(chains: list[Chain]) -> Systems:
    g = rng("systems")
    sy = Systems()
    ids = {"ctr": 0, "line": 0, "ms": 0, "opp": 0, "op": 0, "so": 0, "sol": 0, "bill": 0}
    others = [ch for ch in chains if ch.number != HERO_CONTRACT_NUMBER]
    # wrong-link target for the O chain: another customer's agreement number
    o_chains = [ch for ch in chains if "O" in ch.tags]
    for ch in chains:
        _emit_contract_rows(sy, ch, g, ids)
    for ch in chains:
        if "H" in ch.tags:
            _emit_hero_systems(sy, ch, g, ids)
            continue
        tags = ch.tags
        docs = ch.docs
        orig = docs[0]
        # ---- Salesforce: one opp per document (D: skip the latest amendment)
        sf_docs = docs[:-1] if ("D" in tags and len(docs) > 1) else docs
        opp_ids = {}
        for d in sf_docs:
            kw = {}
            if d.version == 0 and "R" in tags:
                rounded = float(round(d.tcv / 25000.0) * 25000.0)
                if abs(rounded - d.tcv) < 500:
                    rounded = d.tcv + 7500.0
                prods = _delta_products(ch, d)
                prods[0] = dict(prods[0], price=_round_cents(prods[0]["price"] + (rounded - d.tcv) / prods[0]["qty"]))
                kw["products"] = prods
                kw["amount"] = _round_cents(sum(p["qty"] * p["price"] for p in prods))
            if d.version == 0 and "L" in tags:
                prods = _delta_products(ch, d)
                dropped = min(prods, key=lambda p: p["qty"] * p["price"])
                prods = [p for p in prods if p is not dropped]
                kw["products"] = prods
                kw["amount"] = _round_cents(sum(p["qty"] * p["price"] for p in prods))
            if d.version == 0 and "O" in tags:
                idx = o_chains.index(ch)
                if idx == 0:
                    kw["linked"] = None
                else:
                    kw["linked"] = others[(others.index(ch) + 37) % len(others)].number   # another customer's agreement
            opp_ids[d.version] = _emit_opp(sy, ch, d, g, ids, **kw)
        # ---- NetSuite: one order per chain, restated to the latest synced version
        if "N" in tags and len(docs) > 1:
            ns_doc = docs[-2]           # the amendment never arrived: NetSuite sits on the previous version
        elif "D" in tags and len(docs) > 1:
            ns_doc = docs[-2]
        else:
            ns_doc = docs[-1]
        sync = ns_doc.signed + timedelta(days=int(g.integers(1, 4)))
        kw = {}
        if "E" in tags:
            # amount and lines restated, end date left at the original
            kw["end"] = orig.end
        if "P" in tags:
            kw["payment_terms"] = "Net 30"
            if ns_doc.payment_terms == "Net 30":
                # force the contract side to Net 45 so the mismatch is real
                for d in docs:
                    d.payment_terms = "Net 45"
                for row in sy.contracts:
                    if row["CONTRACT_NUMBER"] in {d.number for d in docs}:
                        row["PAYMENT_TERMS"] = "Net 45"
        if "F" in tags:
            kw["billing"] = "Quarterly"
        if "M" in tags:
            bills = [{"date": m["date"], "amount": m["amount"]} for m in ns_doc.schedule]
            # split the last two milestones differently (same total)
            a, b = bills[-2]["amount"], bills[-1]["amount"]
            shift = _round_cents(min(a, b) * 0.4)
            bills[-2]["amount"] = _round_cents(a - shift)
            bills[-1]["amount"] = _round_cents(b + shift)
            kw["bills"] = bills
        if "T" in tags:
            kw["truncate"] = 2
        opp_for_so = opp_ids.get(0)
        if "S" in tags:
            opp_for_so = None
        sid = _emit_so(sy, ch, ns_doc, g, ids, opp_id=opp_for_so, sync=sync, **kw)
        if "U" in tags:
            # Boomi created a second, full copy of the restated order from the amendment opportunity
            am_opp = opp_ids.get(docs[-1].version) or opp_for_so
            _emit_so(sy, ch, ns_doc, g, ids, opp_id=am_opp, sync=sync + timedelta(days=1), **kw)
    return sy


def _emit_hero_systems(sy: Systems, ch: Chain, g, ids: dict):
    msa, a1, a2, a3 = ch.docs
    # Salesforce: MSA, A1, A2 booked; A3 missing
    o0 = _emit_opp(sy, ch, msa, g, ids, close=HERO_MSA_SIGNED)
    o1 = _emit_opp(sy, ch, a1, g, ids, close=HERO_A1_SIGNED + timedelta(days=1))
    _emit_opp(sy, ch, a2, g, ids, close=HERO_A2_SIGNED + timedelta(days=2))
    # NetSuite: SO-1 from the MSA (never updated), SO-2 created by Boomi for the A1 increment; A2/A3 never synced
    _emit_so(sy, ch, msa, g, ids, opp_id=o0, sync=date(2025, 2, 12))
    inc = Doc()
    inc.effective, inc.end, inc.term = msa.effective, msa.end, msa.term
    inc.payment_terms, inc.billing = "Net 30", "Quarterly"
    inc.lines = [a1.lines[-1]]
    inc.schedule = [m for m in a1.schedule if m["desc"].startswith("Sponsored Content")]
    _emit_so(sy, ch, inc, g, ids, opp_id=o1, sync=date(2025, 6, 18), bills=[{"date": m["date"], "amount": m["amount"]} for m in inc.schedule], total=450000.0)


# ---------------------------------------------------------------- data dictionary
DATA_DICTIONARY_ROWS = [
    ("CUSTOMERS", "customer_id", "VARCHAR", "Customer code shared by DocuSign extraction, Salesforce and NetSuite", "CUST-0017", None, "Deal Desk", "Salesforce"),
    ("CUSTOMERS", "customer_type", "VARCHAR", "Pharma (brand marketing buyer) or Health System (talent buyer)", "Pharma", None, "Deal Desk", "Salesforce"),
    ("CUSTOMERS", "account_owner", "VARCHAR", "Sales rep who owns the account and enters its opportunities", "Dana Whitfield", None, "Sales Ops", "Salesforce"),
    ("RECONCILIATION_CONTROLS", "check_type", "VARCHAR", "Machine name of a three-way check; every finding carries one", "AMENDMENT_NOT_IN_NETSUITE", None, "Revenue Accounting", "Deal Desk"),
    ("RECONCILIATION_CONTROLS", "owning_team", "VARCHAR", "Team that reviews findings of the check: Sales Ops, Revenue Accounting or Billing", "Billing", None, "Chief Accounting Officer", "Deal Desk"),
    ("RECONCILIATION_CONTROLS", "sox_control_ref", "VARCHAR", "Order-to-cash SOX control the check evidences", "OTC-07 Amendment processing", None, "SOX and Automation", "Deal Desk"),
    ("RECONCILIATION_CONTROLS", "high_severity_usd", "NUMBER", "Absolute dollar variance at or above which the finding is High severity", "100000", None, "Revenue Accounting", "Deal Desk"),
    ("CONTRACTS", "contract_number", "VARCHAR", "Agreement number on the document; amendments append -A1, -A2 ...", "MCN-2025-0142-A2", None, "Deal Desk", "DocuSign"),
    ("CONTRACTS", "parent_contract_id", "VARCHAR", "For an amendment the contract_id of the original agreement; NULL for originals", "CTR-00142", None, "Deal Desk", "DocuSign"),
    ("CONTRACTS", "amendment_number", "NUMBER", "0 for the original, 1..n for amendments", "2", None, "Deal Desk", "DocuSign"),
    ("CONTRACTS", "total_contract_value", "NUMBER", "Total contract value restated by this document (not the increment)", "2850000.00", None, "Revenue Accounting", "DocuSign"),
    ("CONTRACTS", "end_date", "DATE", "Term end restated by this document", "2027-02-28", None, "Revenue Accounting", "DocuSign"),
    ("CONTRACTS", "billing_frequency", "VARCHAR", "Upfront, Quarterly, Monthly or Milestone", "Milestone", None, "Billing", "DocuSign"),
    ("CONTRACTS", "payment_terms", "VARCHAR", "Net 30, Net 45 or Net 60", "Net 45", None, "Billing", "DocuSign"),
    ("CONTRACTS", "extraction_confidence", "NUMBER", "Confidence of the term extraction from the PDF; below 0.90 reviewed by Deal Desk", "0.941", None, "Deal Desk", "DocuSign"),
    ("CONTRACTS", "pdf_file_name", "VARCHAR", "Signed PDF in the contract archive", "MCN-2025-0142-A2.pdf", None, "Deal Desk", "DocuSign"),
    ("CONTRACT_LINE_ITEMS", "line_amount", "NUMBER", "quantity x unit_price; sums to the document TCV", "1200000.00", None, "Revenue Accounting", "DocuSign"),
    ("CONTRACT_BILLING_SCHEDULE", "scheduled_amount", "NUMBER", "Milestone amount per Exhibit B; sums to the document TCV", "500000.00", None, "Billing", "DocuSign"),
    ("SALESFORCE_OPPORTUNITIES", "amount", "NUMBER", "Booked amount entered by the rep; an amendment opportunity carries the increment", "600000.00", None, "Sales Ops", "Salesforce"),
    ("SALESFORCE_OPPORTUNITIES", "linked_contract_number", "VARCHAR", "Contract number the rep linked; sometimes blank or wrong", "MCN-2025-0142-A2", None, "Sales Ops", "Salesforce"),
    ("SALESFORCE_OPPORTUNITIES", "opportunity_type", "VARCHAR", "New Business, Renewal or Amendment", "Amendment", None, "Sales Ops", "Salesforce"),
    ("NETSUITE_SALES_ORDERS", "opportunity_id", "VARCHAR", "Salesforce opportunity Boomi created the order from; sometimes missing", "006Q00000000421", None, "Revenue Accounting", "NetSuite"),
    ("NETSUITE_SALES_ORDERS", "order_total", "NUMBER", "Order total; Boomi should restate it on amendments", "2250000.00", None, "Revenue Accounting", "NetSuite"),
    ("NETSUITE_SALES_ORDERS", "end_date", "DATE", "Service end used for revenue scheduling", "2026-08-31", None, "Revenue Accounting", "NetSuite"),
    ("NETSUITE_SALES_ORDERS", "billing_schedule_type", "VARCHAR", "NetSuite billing schedule type: Upfront, Quarterly, Monthly or Milestone", "Quarterly", None, "Billing", "NetSuite"),
    ("NETSUITE_SALES_ORDERS", "boomi_sync_timestamp", "TIMESTAMP", "Last Boomi create/update; before an amendment signature means the amendment is not reflected", "2025-06-18 03:14:00", None, "Revenue Accounting", "NetSuite"),
    ("NETSUITE_BILLING_SCHEDULE", "bill_amount", "NUMBER", "Scheduled invoice amount", "300000.00", None, "Billing", "NetSuite"),
    ("NETSUITE_BILLING_SCHEDULE", "billed", "BOOLEAN", "TRUE once invoiced (bill_date on or before 2026-09-30)", "TRUE", None, "Billing", "NetSuite"),
    ("V_CONTRACT_CHAIN", "chain_id", "VARCHAR", "The original agreement's contract_id; the grain of every reconciliation question", "CTR-00142", None, "Revenue Accounting", "Derived"),
    ("V_CONTRACT_CHAIN", "current_tcv", "NUMBER", "TCV from the latest signed document of the chain", "2730000.00", "latest CONTRACTS.total_contract_value in the chain", "Revenue Accounting", "Derived"),
    ("V_CONTRACT_CHAIN", "amendment_count", "NUMBER", "Number of amendments signed on the chain", "3", "COUNT of amendments with parent_contract_id = chain_id", "Deal Desk", "Derived"),
    ("V_AMENDMENT_LINEAGE", "tcv_change", "NUMBER", "TCV restated by this version minus the previous version", "-120000.00", "tcv - previous_tcv", "Revenue Accounting", "Derived"),
    ("V_DEAL_CROSSWALK", "so_link_method", "VARCHAR", "How the order was linked: opportunity_id or customer_and_start_date (Boomi left the id blank)", "opportunity_id", None, "Revenue Accounting", "Derived"),
    ("V_CHAIN_SYSTEM_SUMMARY", "sf_amount", "NUMBER", "Salesforce value of the chain: sum of its closed-won opportunity amounts", "2850000.00", "SUM(SALESFORCE_OPPORTUNITIES.amount) over the chain", "Sales Ops", "Derived"),
    ("V_CHAIN_SYSTEM_SUMMARY", "ns_amount", "NUMBER", "NetSuite value of the chain: sum of its sales order totals", "2250000.00", "SUM(NETSUITE_SALES_ORDERS.order_total) over the chain", "Revenue Accounting", "Derived"),
    ("V_CHAIN_SYSTEM_SUMMARY", "ns_version_reflected", "NUMBER", "Highest amendment number signed on or before the last Boomi sync of the chain's orders", "1", "MAX(version) WHERE signed_date <= ns_last_sync", "Revenue Accounting", "Derived"),
    ("V_CHAIN_SYSTEM_SUMMARY", "sf_version_reflected", "NUMBER", "Highest amendment number linked by any opportunity of the chain", "2", "MAX(linked amendment suffix)", "Sales Ops", "Derived"),
    ("METRIC", "mismatch_rate", "NUMBER", "Chains with at least one finding divided by all chains", "0.18", "COUNT(DISTINCT chains with findings) / COUNT(chains)", "Revenue Accounting", "Derived"),
    ("METRIC", "open_exposure_usd", "NUMBER", "Sum of the absolute dollar variance across open findings; a chain contributes once per check", "6400000", "SUM(ABS(variance_usd)) over findings", "Chief Accounting Officer", "Derived"),
]


def build_data_dictionary() -> pd.DataFrame:
    return pd.DataFrame(DATA_DICTIONARY_ROWS, columns=["TABLE_NAME", "COLUMN_NAME", "DATA_TYPE", "DESCRIPTION", "SAMPLE_VALUE", "METRIC_FORMULA", "BUSINESS_OWNER", "SOURCE_SYSTEM"])


# ---------------------------------------------------------------- assembly
def _frame(rows: list[dict], date_cols=(), ts_cols=()) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    for c in date_cols:
        df[c] = pd.to_datetime(df[c])
    for c in ts_cols:
        df[c] = pd.to_datetime(df[c])
    return df


def generate_all(verbose=True) -> dict:
    def log(msg):
        if verbose:
            print(msg, flush=True)
    SEEDED.clear()
    log("Building dimensions...")
    customers = build_customers()
    products = build_products()
    controls = build_controls()
    log("Building contract chains (the truth)...")
    chains = build_chains(customers)
    _choose_drift(chains)
    log(f"  {len(chains)} chains, {sum(len(c.docs) for c in chains)} documents, {len(SEEDED)} chains with seeded drift")
    log("Building Salesforce and NetSuite from the truth and applying the drift...")
    sy = build_systems(chains)
    first = {}
    for ch in chains:
        cid = ch.customer.CUSTOMER_ID
        first[cid] = min(first.get(cid, ch.original.signed), ch.original.signed)
    customers["CUSTOMER_SINCE"] = pd.to_datetime(customers.CUSTOMER_ID.map(first))
    frames = {
        "CUSTOMERS": customers,
        "PRODUCTS": products,
        "RECONCILIATION_CONTROLS": controls,
        "CONTRACTS": _frame(sy.contracts, ("SIGNED_DATE", "EFFECTIVE_DATE", "END_DATE"), ("EXTRACTED_AT",)),
        "CONTRACT_LINE_ITEMS": _frame(sy.lines, ("START_DATE", "END_DATE")),
        "CONTRACT_BILLING_SCHEDULE": _frame(sy.schedule, ("SCHEDULED_DATE",)),
        "SALESFORCE_OPPORTUNITIES": _frame(sy.opps, ("CLOSE_DATE", "CONTRACT_START_DATE", "CONTRACT_END_DATE"), ("LAST_MODIFIED_DATE",)),
        "SALESFORCE_OPPORTUNITY_PRODUCTS": _frame(sy.opp_products),
        "NETSUITE_SALES_ORDERS": _frame(sy.sos, ("ORDER_DATE", "START_DATE", "END_DATE"), ("BOOMI_SYNC_TIMESTAMP",)),
        "NETSUITE_SALES_ORDER_LINES": _frame(sy.so_lines),
        "NETSUITE_BILLING_SCHEDULE": _frame(sy.bills, ("BILL_DATE",)),
        "DATA_DICTIONARY": build_data_dictionary(),
    }
    for k, v in frames.items():
        log(f"  {k}: {len(v):,}")
    return frames


if __name__ == "__main__":
    fr = generate_all()
    from collections import Counter
    print(Counter(t for tags in SEEDED.values() for t in tags))
