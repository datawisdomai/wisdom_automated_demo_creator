"""
generator.py (Pecos Ridge OpenInvoice Supply Chain)
---------------------------------------------------
Deterministic synthetic Enverus OpenInvoice extract for the partner's existing "O&G" (Pecos Ridge)
domain. Every vendor, well, pad, AFE, property and contract id comes from the partner's own tables,
paged out of the Wisdom SQL playground into inputs/ref/*.csv by ref_extract.py; this module never
invents one. Two regimes:

  exact      SPEND_INVOICE rows for the five supply-chain categories dated 2025-01-01 or later
             (inputs/ref/spend_invoice_exact.csv): one OI_INVOICE per row, ERP_INVOICE_ID = INVOICE_ID,
             INVOICE_TOTAL_USD = AMOUNT_USD to the cent, lines sum to it.
  calibrated 2022-01-01 .. 2024-12-31: vendor x cost category x business unit x ledger x month
             aggregates (inputs/ref/spend_invoice_agg.csv) are split into that many invoices whose
             amounts sum to the aggregate; no ERP id (the January 2025 integration upgrade story).

Engineered control points (see DEMO_PLAN.md / demo.yaml):
  CP1  corrosion inhibitor price gap between the two chemical suppliers + small-pack premium
  CP2  Redline RL100 invoiced above its 2026 price book from February 2026 -> disputed lines
  CP3  5-1/2" 20# P-110 casing described six ways, per joint and per foot, across distributors
  CP4  ~8-9% of 2026 line spend unclassified, concentrated in rentals and distributor items
  CP5  capital lines carry AFE_NUMBER / CORP_WELL_ID so cost per lateral foot joins to WELL_MASTER
"""
from __future__ import annotations

import csv
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from demo_creator.rng import rng as _seeded_rng

import catalog as C

SEED = 20261019
AS_OF = date(2026, 9, 30)
GO_LIVE = date(2022, 1, 1)
ERP_STAMP_FROM = date(2025, 1, 1)
HERE = Path(__file__).resolve().parent
REF = Path(__import__("os").environ.get("PECOS_REF_DIR") or (HERE / "inputs" / "ref"))

CATEGORY_MANAGER = "Jessica Whitaker"
DATA_STEWARD = "Hector Brown"
FIELD_APPROVERS = ["Marcus Delgado", "Tanya Burkett", "Luis Ortega", "Wade Pruitt", "Sheila Okafor", "Brent Kessler", "Rosa Villanueva", "Cody Marsh"]
AP_APPROVERS = ["Priya Natarajan", "Dale Whitfield", "Monica Reyes", "Evan Schultz"]
BU_BASIN = {"Midland Basin": "Midland", "Delaware Basin": "Delaware", "Midcon": "Anadarko", "Hugoton": "Hugoton", "Corporate": "Midland"}
BASIN_BU = {"Midland": "Midland Basin", "Delaware": "Delaware Basin", "Anadarko": "Midcon", "Hugoton": "Hugoton"}
PRICEBOOK_SUPPLIERS = [C.CORROSION_CONTROL, C.BASIN_CHEMICAL, C.KERMIT, C.MONAHANS, C.REDLINE] + C.HAULERS
HERO_CHEM_INHIBITOR_SHARE = 0.42       # share of the two chemical suppliers' material lines that are the hero product
BASIN_PACK_MIX = {"TOTE": 0.40, "DRUM": 0.45, "PAIL": 0.15}
CCC_PACK_MIX = {"GAL": 0.25, "TOTE": 0.50, "DRUM": 0.25}
# invoice-level probability that a 2026 invoice is coded with vague (unclassified) distributor lines (CP4)
UNCLASSIFIED_P_2026 = {"Rentals": 0.50, "Casing & tubulars": 0.12, "Chemicals": 0.03, "Proppant": 0.02, "Water Disposal": 0.04, "Water sourcing/transfer": 0.04}
UNCLASSIFIED_P_EARLIER = {2025: 0.5, 2024: 0.15, 2023: 0.1, 2022: 0.1}   # multiplier on the 2026 probabilities
CAT_FAMILY = {"Chemicals": "SCM-01", "Proppant": "SCM-02", "Casing & tubulars": "SCM-03", "Rentals": "SCM-04",
              "Water Disposal": "SCM-05-01", "Water sourcing/transfer": "SCM-05-02"}
LINES_PER_INVOICE = {"Chemicals": (2, 6), "Proppant": (2, 4), "Casing & tubulars": (2, 4), "Rentals": (3, 6),
                     "Water Disposal": (2, 4), "Water sourcing/transfer": (2, 4)}
INTEGER_UOMS = {"TOTE", "DRUM", "PAIL", "BAG", "JT", "EA", "DAY", "WEEK", "MONTH", "LOAD"}


def rng(tag: str) -> np.random.Generator:
    return _seeded_rng(SEED, tag)


# ---------------------------------------------------------------------------
# Reference extracts (partner data via the SQL playground; cells are JSON-ish)
# ---------------------------------------------------------------------------
def _cell(v: str):
    if v is None or v == "":
        return None
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        try:
            return json.loads(v)
        except Exception:  # noqa: BLE001
            return v.strip('"')
    if v in ("true", "false"):
        return v == "true"
    try:
        if re.fullmatch(r"-?\d+", v):
            return int(v)
        if re.fullmatch(r"-?\d+\.\d*(e-?\d+)?", v):
            return float(v)
    except ValueError:
        pass
    return v


def load_ref(name: str) -> pd.DataFrame:
    path = REF / f"{name}.csv"
    if not path.is_file():
        raise FileNotFoundError(f"{path.name} missing — run `python demos/pecos_openinvoice/ref_extract.py` first")
    with path.open(newline="") as fh:
        rows = [{k: _cell(v) for k, v in r.items()} for r in csv.DictReader(fh)]
    df = pd.DataFrame(rows)
    for col in df.columns:
        if col.endswith("DATE") or col.endswith("_MONTH") or col in ("INVOICE_MONTH",):
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    return df


class Refs:
    def __init__(self):
        self.vendors = load_ref("s4_vendor_lfa1").set_index("LIFNR")
        self.counterparties = load_ref("counterparty_master")
        self.wells = load_ref("well_master").set_index("CORP_WELL_ID")
        self.pads = load_ref("pad").set_index("PAD_ID")
        self.afes = load_ref("od_afe_header").set_index("AFE_NUMBER")
        self.xwalk = load_ref("xwalk_well")
        self.contracts = load_ref("clm_contract")
        self.exact = load_ref("spend_invoice_exact")
        self.agg = load_ref("spend_invoice_agg")
        self.prop_to_well = {r.QUORUM_PROPERTY_NUMBER: r.CORP_WELL_ID for r in self.xwalk.itertuples() if r.QUORUM_PROPERTY_NUMBER}
        # properties and AFEs by basin for the calibrated years
        self.props_by_basin: dict[str, list[str]] = {}
        for prop, well in self.prop_to_well.items():
            if well in self.wells.index:
                self.props_by_basin.setdefault(self.wells.loc[well, "BASIN"], []).append(prop)
        self.afes_by_basin: dict[str, list[tuple[str, date]]] = {}
        for afe, r in self.afes.iterrows():
            w = r.CORP_WELL_ID
            if w in self.wells.index and r.AFE_DATE:
                self.afes_by_basin.setdefault(self.wells.loc[w, "BASIN"], []).append((afe, r.AFE_DATE))
        for k in self.afes_by_basin:
            self.afes_by_basin[k].sort(key=lambda t: t[1])

    def well_for(self, afe: str | None, prop: str | None) -> str | None:
        if afe and afe in self.afes.index:
            w = self.afes.loc[afe, "CORP_WELL_ID"]
            if isinstance(w, str) and w in self.wells.index:
                return w
        if prop and prop in self.prop_to_well and self.prop_to_well[prop] in self.wells.index:
            return self.prop_to_well[prop]
        return None

    def pad_basin(self, well: str | None, fallback_basin: str) -> tuple[str | None, str]:
        if well and well in self.wells.index:
            w = self.wells.loc[well]
            return (w.PAD_ID if isinstance(w.PAD_ID, str) else None), (w.BASIN or fallback_basin)
        return None, fallback_basin


# ---------------------------------------------------------------------------
# Master data
# ---------------------------------------------------------------------------
def _title(name: str) -> str:
    small = {"llc": "LLC", "inc": "Inc.", "inc.": "Inc.", "co": "Co", "l.l.c.": "L.L.C.", "lp": "LP", "&": "&", "(e-fleet)": "(E-Fleet)"}
    return " ".join(small.get(w.lower(), w.capitalize()) for w in name.split())


def build_suppliers(refs: Refs) -> pd.DataFrame:
    r = rng("suppliers")
    cats = pd.concat([refs.exact[["LIFNR", "SPEND_CATEGORY", "AMOUNT_USD", "INVOICE_DATE"]],
                      refs.agg.rename(columns={"INVOICE_MONTH": "INVOICE_DATE"})[["LIFNR", "SPEND_CATEGORY", "AMOUNT_USD", "INVOICE_DATE"]]])
    dom = cats.groupby(["LIFNR", "SPEND_CATEGORY"])["AMOUNT_USD"].sum().reset_index().sort_values("AMOUNT_USD", ascending=False).drop_duplicates("LIFNR")
    first = cats.groupby("LIFNR")["INVOICE_DATE"].min()
    cp_by_name = {str(x.LEGAL_NAME).upper(): x.DUNS_NUMBER for x in refs.counterparties.itertuples()}
    rows = []
    for i, (lifnr, cat) in enumerate(zip(dom.LIFNR, dom.SPEND_CATEGORY)):
        v = refs.vendors.loc[lifnr] if lifnr in refs.vendors.index else None
        name = _title(str(v.NAME1)) if v is not None else f"Vendor {lifnr}"
        duns = cp_by_name.get(str(v.NAME1).upper()) if v is not None else None
        if duns is None and v is not None:
            # counterparty legal names are title case with LLC; try a looser match
            duns = next((d for n, d in cp_by_name.items() if n.replace(",", "").replace(".", "") == str(v.NAME1).upper().replace(",", "").replace(".", "")), None)
        onboarded = GO_LIVE if first[lifnr] <= date(2022, 3, 31) else date(first[lifnr].year, first[lifnr].month, 1) - timedelta(days=int(r.integers(10, 60)))
        hero = lifnr in PRICEBOOK_SUPPLIERS
        basin_counts = refs.exact[refs.exact.LIFNR == lifnr].BUSINESS_UNIT.map(BU_BASIN).value_counts()
        rows.append(dict(
            OI_SUPPLIER_ID=f"OIS-{int(lifnr[-5:]):05d}", LIFNR=lifnr, SUPPLIER_NAME=name,
            SUPPLIER_CITY=(_title(str(v.ORT01)) if v is not None else None), SUPPLIER_STATE=(v.REGIO if v is not None else None),
            DUNS_NUMBER=duns, OI_SUPPLIER_CATEGORY=cat, ONBOARDED_DATE=onboarded,
            EINVOICE_ENABLED=bool(hero or r.random() < 0.8), PRICEBOOK_LOADED=hero,
            PRIMARY_BASIN=(basin_counts.index[0] if len(basin_counts) else "Midland"),
            PAYMENT_TERMS=str(r.choice(["NT30", "NT45", "NT60"], p=[0.5, 0.35, 0.15])),
            SUPPLIER_STATUS="Active",
        ))
    return pd.DataFrame(rows).sort_values("LIFNR").reset_index(drop=True)


def build_taxonomy() -> pd.DataFrame:
    rows = []
    for node, fam, cls, name, use, phase, uom, spec, unspsc, alt in C.TAXONOMY:
        rows.append(dict(TAXONOMY_NODE_ID=node, LEVEL1_FAMILY=fam, LEVEL2_CLASS=cls, GENERIC_PRODUCT_NAME=name, PRIMARY_USE=use,
                         USE_PHASE=phase, STANDARD_UOM=uom, KEY_SPEC_ATTRIBUTES=spec, UNSPSC_CODE=unspsc, ALTERNATE_SUPPLIER_ELIGIBLE=bool(alt),
                         CATEGORY_MANAGER=C.FAMILY_MANAGER[fam],
                         BENCHMARK_PRICE_USD_PER_STD_UOM=(None if fam in ("Fees & surcharges", "MRO & consumables") and C.BASE_PRICE[node] == 1.0 else C.BASE_PRICE[node]),
                         TAXONOMY_VERSION="3.0"))
    return pd.DataFrame(rows)


# ---- supplier item catalogs for every supplier (hero from catalog.py; long tail from templates) ----
def _style(desc: str, style: str) -> str:
    if style == "upper":
        return desc.upper()
    if style == "code":
        return re.sub(r"\s*\(per (\w+)\)", r" /\1", desc).replace("Produced water", "PW").replace("Fresh water", "FW")
    return desc


def _price(node: str, mult: float, pack_qty: float, year: int) -> float:
    return C.BASE_PRICE[node] * mult * pack_qty * C.PRICE_INDEX.get(year, 1.0)


def build_item_catalogs(refs: Refs, suppliers: pd.DataFrame) -> dict[str, list[dict]]:
    """LIFNR -> list of item dicts {code, desc, uom, pack_qty, node, mult, classified(bool)}."""
    r = rng("item_catalogs")
    cats: dict[str, list[dict]] = {}
    for lifnr, items in C.SUPPLIER_ITEMS.items():
        cats[lifnr] = [dict(it, classified=True) for it in items]
    for lifnr in C.HAULERS:
        mult, style = C.HAULER_STYLE[lifnr]
        cats[lifnr] = [dict(it, desc=_style(it["desc"], style), mult=(it["mult"] * mult if it["node"].startswith("SCM-05") else it["mult"]), classified=True)
                       for it in C.HAULER_TEMPLATE]
    # categories each vendor actually invoices (from the slices)
    vend_cats = pd.concat([refs.exact[["LIFNR", "COST_CATEGORY"]], refs.agg[["LIFNR", "COST_CATEGORY"]]]).drop_duplicates()
    long_tail = sorted(set(vend_cats.LIFNR) - set(cats))
    for idx, lifnr in enumerate(long_tail):
        items: list[dict] = []
        vcats = set(vend_cats[vend_cats.LIFNR == lifnr].COST_CATEGORY)
        vmult = float(r.uniform(0.93, 1.12))
        if "Casing & tubulars" in vcats:
            for k, node in enumerate(C.OCTG_DESCRIPTIONS):
                variants = C.OCTG_DESCRIPTIONS[node]
                desc, uom, pack = variants[(idx + k) % len(variants)]
                items.append(dict(code=f"{node[-6:].replace('-', '')}-{'J' if uom == 'JT' else 'F' if uom == 'FT' else 'E'}", desc=desc, uom=uom, pack_qty=pack,
                                  node=node, mult=vmult * float(r.uniform(0.98, 1.02)), classified=True))
            items.append(dict(code="DELIV", desc="Freight / delivery", uom="EA", pack_qty=1, node="SCM-06-01-002", mult=1.0, classified=True))
        if "Rentals" in vcats:
            for k, node in enumerate(C.RENTAL_DESCRIPTIONS):
                variants = C.RENTAL_DESCRIPTIONS[node]
                desc, uom, pack = variants[(idx + k) % len(variants)]
                items.append(dict(code=f"R{node[-6:].replace('-', '')}-{uom[0]}", desc=desc, uom=uom, pack_qty=pack, node=node,
                                  mult=vmult * float(r.uniform(0.97, 1.03)), classified=True))
            items.append(dict(code="MOB", desc="Mobilization / minimum charge", uom="EA", pack_qty=1, node="SCM-06-02-003", mult=1.0, classified=True))
        if "Chemicals" in vcats:   # a distributor reselling chemicals
            items += [dict(code="CI-WS-5", desc="INHIBITOR CORR WS 5GAL PAIL", uom="PAIL", pack_qty=5, node="SCM-01-01-001", mult=1.38, classified=True),
                      dict(code="SOLV-55", desc="PARAFFIN SOLVENT 55GAL", uom="DRUM", pack_qty=55, node="SCM-01-03-001", mult=1.15, classified=True)]
        if vcats & {"Water Disposal", "Water sourcing/transfer"}:
            items += [dict(it, desc=it["desc"].upper(), mult=it["mult"] * vmult, classified=True) for it in C.HAULER_TEMPLATE]
        if "Proppant" in vcats:
            items += [dict(code="SAND-100", desc="100 MESH SAND DELIVERED", uom="TON", pack_qty=1, node="SCM-02-01-001", mult=vmult, classified=True)]
        # vague distributor items: unclassified (CP4) — every long-tail vendor has a few
        n_vague = int(r.integers(2, 5))
        for k in r.choice(len(C.UNCLASSIFIED_DESCRIPTIONS), size=n_vague, replace=False):
            desc, uom = C.UNCLASSIFIED_DESCRIPTIONS[int(k)]
            items.append(dict(code=f"MISC-{int(k):02d}", desc=desc, uom=uom, pack_qty=1, node=None, mult=1.0, classified=False))
        if not any(it["classified"] for it in items):   # vendor only in a category we have no template for
            items.append(dict(code="SVC", desc="Services per ticket", uom="EA", pack_qty=1, node=None, mult=1.0, classified=False))
        if not any(it["node"] and it["node"].startswith("SCM-06") and it["uom"] == "EA" for it in items):
            items.append(dict(code="DELIV", desc="Delivery charge", uom="EA", pack_qty=1, node="SCM-06-01-002", mult=1.0, classified=True))
        cats[lifnr] = items
    for lifnr in cats:   # the fallback line for invoices too small for any pack: unclassified by nature
        cats[lifnr].append(dict(code="TKT", desc="Charges per field ticket", uom="EA", pack_qty=1, node=None, mult=1.0, classified=False))
    return cats


def build_pricebooks(refs: Refs, suppliers: pd.DataFrame, catalogs: dict[str, list[dict]]) -> pd.DataFrame:
    sup = suppliers.set_index("LIFNR")
    contract_by_lifnr = {}
    for c in refs.contracts.itertuples():
        if c.LIFNR and c.CONTRACT_TYPE in ("Chemical Supply Agreement", "Proppant Supply Agreement", "Water Hauling MSA"):
            contract_by_lifnr[c.LIFNR] = c.CLM_CONTRACT_ID
    rows, n = [], 0
    for lifnr in PRICEBOOK_SUPPLIERS:
        name = sup.loc[lifnr, "SUPPLIER_NAME"]
        versions = C.PRICEBOOK_VERSIONS.get(lifnr)
        if versions is None:   # haulers
            abbr = "".join(w[0] for w in name.split()[:3]).upper()
            versions = [(f"{abbr}-WH-2024", "2024-01-01", "2025-12-31", 0.0), (f"{abbr}-WH-2026", "2026-01-01", "2026-12-31", 2.0)]
        for version, eff_from, eff_to, esc in versions:
            f, t = date.fromisoformat(eff_from), date.fromisoformat(eff_to)
            doc = C.pricing_exhibit_filename(name, version)
            for it in catalogs[lifnr]:
                if it["node"] is None or it["node"].startswith("SCM-06") and it["uom"] == "EA":
                    continue   # flat fees are not rated in the exhibit
                n += 1
                rate = round(_price(it["node"], it["mult"], it["pack_qty"], f.year), 2)
                rows.append(dict(PRICEBOOK_ITEM_ID=f"PBI-{n:06d}", OI_SUPPLIER_ID=sup.loc[lifnr, "OI_SUPPLIER_ID"], LIFNR=lifnr,
                                 CLM_CONTRACT_ID=contract_by_lifnr.get(lifnr), PRICEBOOK_VERSION=version, SUPPLIER_ITEM_CODE=it["code"],
                                 SUPPLIER_ITEM_DESCRIPTION=it["desc"], UOM=it["uom"], CONTRACT_RATE_USD=rate, EFFECTIVE_FROM=f, EFFECTIVE_TO=t,
                                 ESCALATION_PCT=esc, SOURCE_DOCUMENT=doc, LOADED_DATE=f - timedelta(days=int(rng(f"pb{version}").integers(5, 25)))))
    return pd.DataFrame(rows)


def build_classification(suppliers: pd.DataFrame, catalogs: dict[str, list[dict]]) -> pd.DataFrame:
    r = rng("classification")
    sup = suppliers.set_index("LIFNR")
    rows, n = [], 0
    for lifnr, items in catalogs.items():
        name = sup.loc[lifnr, "SUPPLIER_NAME"]
        hero = lifnr in C.SUPPLIER_ITEMS
        for it in items:
            n += 1
            node = it["node"]
            if node is None:
                status, method, conf, doc, by, when, note = "Unclassified", None, None, None, None, None, "Description too vague to map; supplier asked for item detail"
                if r.random() < 0.3:
                    status, method, conf, by, when = "Needs review", "ML suggested", round(float(r.uniform(0.41, 0.69)), 2), "classifier v2", date(2026, int(r.integers(7, 10)), int(r.integers(1, 28)))
                    note = "ML suggestion below the 0.70 auto-approve threshold"
            elif node.startswith("SCM-06"):
                status, method, conf, doc, by, when, note = "Approved", "Rule", 1.0, None, "rule: fee keywords", date(2024, 3, 15), None
            elif node.startswith("SCM-03"):
                status, method, conf, doc, by, when, note = "Approved", "Spec sheet review", 1.0, C.octg_mill_sheet_filename(node), DATA_STEWARD, date(2025, int(r.integers(2, 12)), int(r.integers(1, 28))), None
                if r.random() < 0.06:
                    status, method, conf, by, note = "Needs review", "ML suggested", round(float(r.uniform(0.55, 0.69)), 2), "classifier v2", "Grade and weight read from a free-text description; steward to confirm"
            elif hero:
                family_code = it["code"].rsplit("-", 1)[0] if it["uom"] in ("TOTE", "DRUM", "PAIL", "GAL", "BAG") else it["code"]
                status, method, conf, doc, by, when, note = "Approved", "Spec sheet review", 1.0, C.spec_sheet_filename(name, family_code), DATA_STEWARD, date(2024, int(r.integers(2, 12)), int(r.integers(1, 28))), None
            elif node.startswith("SCM-05"):
                status, method, conf, doc, by, when, note = "Approved", "Rule", 0.98, None, "rule: hauling UOM and keywords", date(2024, 4, 2), None
            else:
                status, method, conf, doc, by, when, note = "Approved", "Steward", 0.95, None, DATA_STEWARD, date(2025, int(r.integers(1, 12)), int(r.integers(1, 28))), None
            rows.append(dict(CLASSIFICATION_ID=f"CLS-{n:06d}", OI_SUPPLIER_ID=sup.loc[lifnr, "OI_SUPPLIER_ID"], LIFNR=lifnr, SUPPLIER_ITEM_CODE=it["code"],
                             SUPPLIER_ITEM_DESCRIPTION=it["desc"], INVOICED_UOM=it["uom"], TAXONOMY_NODE_ID=(node if status == "Approved" else None),
                             CONVERSION_FACTOR_TO_STD_UOM=(float(it["pack_qty"]) if status == "Approved" else None), CLASSIFICATION_METHOD=method,
                             CONFIDENCE=conf, SOURCE_DOCUMENT=doc, CLASSIFIED_BY=by, CLASSIFIED_DATE=when, REVIEW_STATUS=status, STEWARD_NOTE=note))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Invoices and lines
# ---------------------------------------------------------------------------
def _split_amount(total: float, n: int, r: np.random.Generator) -> list[float]:
    w = r.dirichlet(np.ones(n) * 2.0)
    parts = [round(float(total * x), 2) for x in w]
    parts[-1] = round(total - sum(parts[:-1]), 2)
    return parts


def _rebalance(line: list) -> None:
    """Line amount was set to an exact residual: move quantity (bulk units) or unit price (integer packs
    and hours) so QUANTITY x UNIT_PRICE_USD reproduces the amount to within a cent or two."""
    it, qty, unit, amount = line[0], line[1], line[2], line[3]
    if it["uom"] in INTEGER_UOMS or it["uom"] == "HR":
        line[2] = round(amount / qty, 4) if qty else unit
    else:
        line[1] = round(amount / unit, 3) if unit else qty


def _qty_round(q: float, uom: str) -> float:
    if uom in INTEGER_UOMS:
        return float(max(1, int(round(q))))
    if uom == "HR":
        return max(0.5, round(q * 2) / 2)
    return max(0.1, round(q, 1))


def _header_rows_exact(refs: Refs) -> list[dict]:
    rows = []
    for x in refs.exact.sort_values("INVOICE_ID").itertuples():
        rows.append(dict(src="exact", erp_id=x.INVOICE_ID, lifnr=x.LIFNR, name_as=x.VENDOR_NAME_AS_INVOICED, bu=x.BUSINESS_UNIT, cat=x.SPEND_CATEGORY,
                         cost_cat=x.COST_CATEGORY, dt=x.INVOICE_DATE, total=round(float(x.AMOUNT_USD), 2), po=x.PO_NUMBER, afe=x.AFE_NUMBER,
                         prop=x.PROPERTY_NUMBER, ledger=x.SOURCE_LEDGER, status=x.APPROVAL_STATUS, paid=x.PAID_DATE))
    return rows


def _header_rows_calibrated(refs: Refs, suppliers: pd.DataFrame) -> list[dict]:
    r = rng("calibrated_headers")
    names = {s.LIFNR: s.SUPPLIER_NAME for s in suppliers.itertuples()}
    rows = []
    for a in refs.agg.sort_values(["LIFNR", "COST_CATEGORY", "BUSINESS_UNIT", "SOURCE_LEDGER", "INVOICE_MONTH"]).itertuples():
        n = int(a.INVOICES)
        parts = _split_amount(float(a.AMOUNT_USD), n, r)
        month = a.INVOICE_MONTH
        basin = BU_BASIN.get(a.BUSINESS_UNIT, "Midland")
        afe_pool = refs.afes_by_basin.get(basin) or refs.afes_by_basin["Midland"]
        prop_pool = refs.props_by_basin.get(basin) or refs.props_by_basin["Midland"]
        n_afe = int(a.AFE_INVOICES)
        for k in range(n):
            day = month + timedelta(days=int(r.integers(0, 28)))
            capex = (a.SOURCE_LEDGER or "").startswith("AFE") or k < n_afe
            afe = prop = None
            if capex:
                # an AFE issued in the 9 months before the invoice
                cands = [x for x in afe_pool if day - timedelta(days=270) <= x[1] <= day]
                afe = str(r.choice([c[0] for c in cands])) if cands else afe_pool[max(0, min(len(afe_pool) - 1, int(np.searchsorted([x[1] for x in afe_pool], day)) - 1))][0]
            else:
                prop = str(r.choice(prop_pool))
            status = str(r.choice(["Paid", "Paid", "Paid", "Paid", "Approved", "Disputed", "On hold - coding"], p=[0.235, 0.235, 0.235, 0.235, 0.03, 0.02, 0.01]))
            paid = day + timedelta(days=int(r.integers(25, 70))) if status == "Paid" else None
            variant = names[a.LIFNR]
            vs = r.random()
            if vs < 0.25:
                variant = variant.upper()
            elif vs < 0.4:
                variant = variant.replace(" LLC", "").replace(" Inc.", "")
            rows.append(dict(src="calibrated", erp_id=None, lifnr=a.LIFNR, name_as=variant, bu=a.BUSINESS_UNIT, cat=a.SPEND_CATEGORY, cost_cat=a.COST_CATEGORY,
                             dt=day, total=parts[k], po=(f"45000{int(r.integers(10000, 99999)):05d}" if r.random() < 0.45 else None), afe=afe, prop=prop,
                             ledger=a.SOURCE_LEDGER, status=status, paid=paid))
    return rows


def _pick_items(cat_items: list[dict], cost_cat: str, lifnr: str, year: int, vague: bool, r: np.random.Generator, n: int) -> list[dict]:
    fam = CAT_FAMILY[cost_cat]
    if vague:
        pool = [it for it in cat_items if not it["classified"] and it["code"] != "TKT"]
        if pool:
            return [pool[int(i)] for i in r.choice(len(pool), size=min(n, len(pool)), replace=False)]
    mat = [it for it in cat_items if it["classified"] and it["node"].startswith(fam)]
    if cost_cat == "Water Disposal":
        mat = [it for it in cat_items if it["classified"] and (it["node"].startswith("SCM-05-01") or it["node"].startswith("SCM-05-03"))]
    if not mat:
        mat = [it for it in cat_items if it["classified"] and not it["node"].startswith("SCM-06")] or cat_items
    picks: list[dict] = []
    if lifnr in (C.CORROSION_CONTROL, C.BASIN_CHEMICAL) and cost_cat == "Chemicals":
        mix = CCC_PACK_MIX if lifnr == C.CORROSION_CONTROL else BASIN_PACK_MIX
        hero = [it for it in mat if it["node"] == "SCM-01-01-001"]
        others = [it for it in mat if it["node"] != "SCM-01-01-001"]
        for _ in range(n):
            if r.random() < HERO_CHEM_INHIBITOR_SHARE:
                uom = str(r.choice(list(mix), p=list(mix.values())))
                picks.append(next(it for it in hero if it["uom"] == uom))
            else:
                picks.append(others[int(r.integers(len(others)))])
    else:
        idx = r.choice(len(mat), size=min(n, len(mat)), replace=False)
        picks = [mat[int(i)] for i in idx]
        if lifnr == C.REDLINE and cost_cat == "Proppant":
            picks = [it for it in mat if it["code"] == "RL100"] + [it for it in picks if it["code"] != "RL100"]
    # de-duplicate items within an invoice
    seen, out = set(), []
    for it in picks:
        if it["code"] not in seen:
            seen.add(it["code"]); out.append(it)
    return out


CONTINUOUS_UOMS = {"GAL", "TON", "FT", "BBL", "LB"}


def _unit_price(it: dict, lifnr: str, dt: date, year: int, pb: dict, redline_from: date, r: np.random.Generator) -> tuple[float, str | None, float | None]:
    """Invoiced unit price for an item on a date: the price-book rate in force (with sub-1% noise, and the
    Redline RL100 overbilling from February 2026) or the catalog price with +-1.5% noise."""
    node = it["node"]
    hit = [x for x in pb.get((lifnr, it["code"]), []) if x[0] <= dt <= x[1]]
    if hit:
        pb_rate, pb_id = hit[0][2], hit[0][3]
        unit = pb_rate * float(r.uniform(0.995, 1.01))
        if lifnr == C.REDLINE and it["code"] == "RL100" and dt >= redline_from:
            unit = pb_rate * (1 + C.REDLINE_OVERBILL_PCT) * float(r.uniform(0.995, 1.005))
        return round(unit, 4), pb_id, pb_rate
    return round(_price(node, it["mult"], it["pack_qty"], year) * float(r.uniform(0.985, 1.015)), 4), None, None


def _compose_lines(items: list[dict], fee: dict | None, total: float, lifnr: str, dt: date, year: int, pb: dict,
                   redline_from: date, r: np.random.Generator) -> list[list]:
    """Turn an invoice total into lines [item, qty, unit, amount, pb_id, pb_rate] that sum to it exactly.
    Integer packs (totes, drums, joints, days) are whole units at their real price; the residual goes into a
    continuous line (gallons, tons, feet, barrels) when the invoice has one, otherwise into a fee line."""
    vague = [it for it in items if it["node"] is None]
    if vague:   # distributor "per ticket" lines: amounts are whatever the ticket said
        parts = _split_amount(total, len(vague), r)
        out = []
        for it, amt in zip(vague, parts):
            qty = float(int(r.integers(1, 4))) if it["uom"] not in ("MONTH", "DAY") else 1.0
            out.append([it, qty, round(amt / qty, 4), amt, None, None])
        _rebalance(out[-1]); out[-1][3] = round(total - sum(x[3] for x in out[:-1]), 2)
        return out
    priced = []
    for it in items:
        unit, pb_id, pb_rate = _unit_price(it, lifnr, dt, year, pb, redline_from, r)
        priced.append((it, unit, pb_id, pb_rate))
    # only items whose single pack fits the invoice; prefer small packs on small invoices
    fit = [x for x in priced if x[0]["uom"] in CONTINUOUS_UOMS or x[1] <= total]
    if not fit:
        return []
    if not any(x[0]["uom"] in CONTINUOUS_UOMS for x in fit) and total < 2 * min(x[1] for x in fit):
        fit = sorted(fit, key=lambda x: x[1])[:1]
    targets = _split_amount(total, len(fit), r)
    lines = []
    for (it, unit, pb_id, pb_rate), target in zip(fit, targets):
        if it["uom"] in CONTINUOUS_UOMS:
            qty = max(0.1, round(target / unit, 1))
        elif it["uom"] == "HR":
            qty = max(0.5, round(target / unit * 2) / 2)
        else:
            qty = float(int(target // unit))
        if qty > 0:
            lines.append([it, qty, unit, round(qty * unit, 2), pb_id, pb_rate])
    if not lines:
        it, unit, pb_id, pb_rate = fit[0]
        lines = [[it, 1.0, unit, round(unit, 2), pb_id, pb_rate]]
    # overshoot (continuous rounding or forced single packs): trim the largest line
    def residual():
        return round(total - sum(x[3] for x in lines), 2)
    while residual() < 0 and len(lines) > 1:
        lines.sort(key=lambda x: -x[3])
        lines.pop(0)
    cont = [x for x in lines if x[0]["uom"] in CONTINUOUS_UOMS]
    res = residual()
    if cont and (res > 0 or cont[0][1] * cont[0][2] + res > 0):
        ln = cont[0]
        ln[3] = round(ln[3] + res, 2)
        ln[1] = round(ln[3] / ln[2], 3)
        ln[3] = round(total - sum(x[3] for x in lines if x is not ln), 2)
        return lines
    # no continuous line: fill with whole packs while the residual is large, then a fee line takes the rest
    for _ in range(200):
        res = residual()
        if res <= 0.08 * total:
            break
        cands = [x for x in lines if x[2] <= res]
        if not cands:
            break
        ln = max(cands, key=lambda x: x[2])
        ln[1] += 1.0
        ln[3] = round(ln[1] * ln[2], 2)
    res = residual()
    if res < 0:   # cannot happen after trimming, but keep the total exact whatever happens
        lines[-1][3] = round(lines[-1][3] + res, 2); _rebalance(lines[-1])
    elif res >= 0.01:
        if fee is not None:
            lines.append([fee, 1.0, res, res, None, None])
        else:
            lines[-1][3] = round(lines[-1][3] + res, 2); _rebalance(lines[-1])
    return lines


def build_transactions(refs: Refs, suppliers: pd.DataFrame, catalogs: dict[str, list[dict]], pricebooks: pd.DataFrame,
                       classification: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    r = rng("transactions")
    sup = suppliers.set_index("LIFNR")
    cls_ok = {(c.LIFNR, c.SUPPLIER_ITEM_CODE): c.REVIEW_STATUS == "Approved" for c in classification.itertuples()}
    # pricebook lookup: (lifnr, code) -> list of (from, to, rate, id)
    pb: dict[tuple[str, str], list[tuple[date, date, float, str]]] = {}
    for p in pricebooks.itertuples():
        pb.setdefault((p.LIFNR, p.SUPPLIER_ITEM_CODE), []).append((p.EFFECTIVE_FROM, p.EFFECTIVE_TO, float(p.CONTRACT_RATE_USD), p.PRICEBOOK_ITEM_ID))
    headers = _header_rows_exact(refs) + _header_rows_calibrated(refs, suppliers)
    headers.sort(key=lambda h: (h["dt"], h["lifnr"], h["erp_id"] or ""))
    inv_rows, line_rows, ticket_rows = [], [], []
    seq_by_year: dict[int, int] = {}
    ticket_n = 0
    redline_from = date.fromisoformat(C.REDLINE_OVERBILL_FROM)
    for h in headers:
        year = h["dt"].year
        seq_by_year[year] = seq_by_year.get(year, 0) + 1
        inv_id = f"OI-{year}-{seq_by_year[year]:06d}"
        lifnr = h["lifnr"]
        s = sup.loc[lifnr]
        cost_cat = h["cost_cat"] if h["cost_cat"] in CAT_FAMILY else {"Chemicals": "Chemicals", "Sand/Proppant": "Proppant", "Tubulars / OCTG": "Casing & tubulars",
                                                                      "Rental Equipment": "Rentals", "Trucking/Water Hauling": "Water Disposal"}.get(h["cat"], "Rentals")
        well = refs.well_for(h["afe"], h["prop"])
        pad, basin = refs.pad_basin(well, BU_BASIN.get(h["bu"], "Midland"))
        total = h["total"]
        p_vague = UNCLASSIFIED_P_2026.get(cost_cat, 0.0) * (1.0 if year == 2026 else UNCLASSIFIED_P_EARLIER.get(year, 0.1))
        if lifnr in PRICEBOOK_SUPPLIERS:
            p_vague *= 0.15
        vague = r.random() < p_vague
        lo, hi = LINES_PER_INVOICE[cost_cat]
        n_lines = int(r.integers(lo, hi + 1)) if not vague else int(r.integers(1, 3))
        if total < 500:
            n_lines = 1
        items = _pick_items(catalogs[lifnr], cost_cat, lifnr, year, vague, r, n_lines)
        fee_items = [it for it in catalogs[lifnr] if it["classified"] and it["node"].startswith("SCM-06") and it["uom"] == "EA"]
        fee = fee_items[int(r.integers(len(fee_items)))] if fee_items else None
        lines_tmp = _compose_lines(items, fee, total, lifnr, h["dt"], year, pb, redline_from, r)
        if not lines_tmp:   # nothing in the catalog fits this invoice amount: one vague ticket line
            tkt = next(it for it in catalogs[lifnr] if it["code"] == "TKT")
            lines_tmp = [[tkt, 1.0, total, total, None, None]]
        # one field ticket per invoice for deliveries, services and rentals (not PO-backed material)
        ticket_id = None
        if cost_cat != "Casing & tubulars" and not (h["po"] and cost_cat == "Proppant"):
            ticket_n += 1
            ticket_id = f"FT-{ticket_n:07d}"
            tdate = h["dt"] - timedelta(days=int(r.integers(2, 21)))
            approver = FIELD_APPROVERS[int(r.integers(len(FIELD_APPROVERS)))]
            ticket_rows.append(dict(FIELD_TICKET_ID=ticket_id, OI_SUPPLIER_ID=s.OI_SUPPLIER_ID, LIFNR=lifnr, TICKET_NUMBER=f"T{int(r.integers(100000, 999999))}",
                                    TICKET_DATE=tdate, TICKET_TYPE=("Rental" if cost_cat == "Rentals" else "Delivery" if cost_cat in ("Chemicals", "Proppant") else "Service"),
                                    CORP_WELL_ID=well, PAD_ID=pad, PROPERTY_NUMBER=h["prop"], AFE_NUMBER=h["afe"], BASIN=basin, APPROVED_BY=approver,
                                    APPROVED_TS=datetime.combine(tdate, datetime.min.time()) + timedelta(hours=int(r.integers(6, 19)), minutes=int(r.integers(0, 60))),
                                    APPROVAL_STATUS="Approved", TICKET_TOTAL_USD=total, OI_INVOICE_ID=inv_id))
        ap_approver = AP_APPROVERS[int(r.integers(len(AP_APPROVERS)))]
        inv_status = h["status"] if h["status"] in ("Paid", "Approved", "Disputed", "On hold - coding") else "Paid"
        dispute_reason = None
        surcharges = round(sum(x[3] for x in lines_tmp if x[0]["node"] and x[0]["node"].startswith("SCM-06")), 2)
        for k, (it, qty, unit, amount, pb_id, pb_rate) in enumerate(lines_tmp, 1):
            var = round((unit - pb_rate) * qty, 2) if pb_rate else None
            lstatus, lreason = "Approved", None
            if var is not None and pb_rate and unit / pb_rate - 1 > 0.02:
                u = r.random()
                lstatus = "Disputed" if u < 0.72 else "Short-paid" if u < 0.85 else "Approved"
                lreason = "Unit price above contract rate" if lstatus != "Approved" else None
                if lstatus == "Disputed":
                    inv_status, dispute_reason = "Disputed", "Unit price above contract rate"
            node = it["node"]
            code_desc = C.OI_COST_CODES.get(cost_cat, ("CAP-RENT", "Rental equipment"))
            line_rows.append(dict(OI_LINE_ID=f"{inv_id}-{k:02d}", OI_INVOICE_ID=inv_id, LINE_NO=k, FIELD_TICKET_ID=ticket_id,
                                  SERVICE_DATE=h["dt"] - timedelta(days=int(r.integers(1, 25))), SUPPLIER_ITEM_CODE=it["code"], SUPPLIER_ITEM_DESCRIPTION=it["desc"],
                                  UOM=it["uom"], QUANTITY=qty, UNIT_PRICE_USD=unit, LINE_AMOUNT_USD=amount, OI_COST_CODE=code_desc[0], OI_COST_CODE_DESC=code_desc[1],
                                  OI_SUPPLIER_CATEGORY=h["cat"], LIFNR=lifnr, OI_SUPPLIER_ID=s.OI_SUPPLIER_ID, AFE_NUMBER=h["afe"], PROPERTY_NUMBER=h["prop"],
                                  CORP_WELL_ID=well, PAD_ID=pad, BASIN=basin, PRICEBOOK_ITEM_ID=pb_id, PRICEBOOK_RATE_USD=pb_rate, PRICE_VARIANCE_USD=var,
                                  LINE_STATUS=lstatus, APPROVER_NAME=ap_approver, DISPUTE_REASON=lreason))
        submitted = datetime.combine(h["dt"], datetime.min.time()) + timedelta(days=int(r.integers(1, 6)), hours=int(r.integers(7, 18)))
        approved = (h["dt"] + timedelta(days=int(r.integers(3, 21)))) if inv_status in ("Paid", "Approved") else None
        paid = h["paid"] if inv_status == "Paid" else None
        if inv_status == "Paid" and not paid:
            paid = approved + timedelta(days=int(r.integers(10, 40)))
        stamped = h["erp_id"] is not None and h["dt"] >= ERP_STAMP_FROM
        inv_rows.append(dict(OI_INVOICE_ID=inv_id, SUPPLIER_INVOICE_NUMBER=f"{''.join(w[0] for w in s.SUPPLIER_NAME.split()[:2]).upper()}-{year % 100:02d}{int(r.integers(10000, 99999))}",
                             OI_SUPPLIER_ID=s.OI_SUPPLIER_ID, LIFNR=lifnr, SUPPLIER_NAME_AS_SUBMITTED=h["name_as"], INVOICE_DATE=h["dt"], SUBMITTED_TS=submitted,
                             APPROVED_DATE=approved, PAID_DATE=paid, INVOICE_STATUS=inv_status, SOURCE_LEDGER=h["ledger"], OI_SUPPLIER_CATEGORY=h["cat"],
                             COST_CODE=C.OI_COST_CODES.get(cost_cat, ("CAP-RENT", ""))[0], PO_NUMBER=h["po"], AFE_NUMBER=h["afe"], PROPERTY_NUMBER=h["prop"],
                             CORP_WELL_ID=well, PAD_ID=pad, BASIN=basin, BUSINESS_UNIT=h["bu"], SUBTOTAL_USD=round(total - surcharges, 2), SURCHARGES_USD=surcharges,
                             INVOICE_TOTAL_USD=total, LINE_COUNT=len(lines_tmp), COUPA_DOC_ID=f"CPA-{int(r.integers(10_000_000, 99_999_999))}",
                             ERP_INVOICE_ID=(h["erp_id"] if stamped else None), ERP_MATCH_STATUS=("Stamped" if stamped else "Legacy - Coupa id only"),
                             APPROVER_NAME=ap_approver, DISPUTE_REASON=dispute_reason))
    inv = pd.DataFrame(inv_rows)
    lines = pd.DataFrame(line_rows)
    tickets = pd.DataFrame(ticket_rows)
    return inv, lines, tickets


def build_data_dictionary() -> pd.DataFrame:
    ddl = (HERE / "01_snowflake_ddl.sql").read_text()
    rows = []
    table = None
    for line in ddl.splitlines():
        m = re.match(r"CREATE OR REPLACE (?:TABLE|VIEW) (\w+)", line)
        if m:
            table = m.group(1)
            continue
        m = re.match(r"\s+(\w+)\s+[\w(),]+(?:\s+NOT NULL)?(?:\s+PRIMARY KEY)?\s+COMMENT '([^']*)'", line)
        if m and table and not table.startswith("V_"):
            rows.append(dict(TABLE_NAME=table, COLUMN_NAME=m.group(1), DESCRIPTION=m.group(2)[:400], EXAMPLE_VALUE=None))
    examples = {("OI_INVOICE", "OI_INVOICE_ID"): "OI-2025-000123", ("OI_INVOICE", "ERP_INVOICE_ID"): "INV-0116119", ("OI_INVOICE_LINE", "SUPPLIER_ITEM_DESCRIPTION"): "CorroShield CS-7000 Corrosion Inhibitor 55 gal drum",
                ("SCM_PRODUCT_TAXONOMY", "GENERIC_PRODUCT_NAME"): "Corrosion inhibitor, water-soluble, filming amine", ("SCM_PRODUCT_TAXONOMY", "TAXONOMY_NODE_ID"): "SCM-01-01-001",
                ("OI_SUPPLIER", "LIFNR"): "0000100039", ("OI_FIELD_TICKET", "FIELD_TICKET_ID"): "FT-0001234", ("OI_PRICEBOOK_ITEM", "PRICEBOOK_VERSION"): "CCC-PB-2025A",
                ("SCM_ITEM_CLASSIFICATION", "CONVERSION_FACTOR_TO_STD_UOM"): "55 (a 55 gal drum)", ("OI_INVOICE_LINE", "AFE_NUMBER"): "TX25-01255C", ("OI_INVOICE", "CORP_WELL_ID"): "PRW-101020"}
    df = pd.DataFrame(rows)
    df["EXAMPLE_VALUE"] = [examples.get((t, c)) for t, c in zip(df.TABLE_NAME, df.COLUMN_NAME)]
    return df


def build_reference_tables(refs: Refs, inv: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """OpenInvoice's synced copies of the cost objects it validates against, taken verbatim from the
    partner extracts (inputs/ref), plus the ERP stamp-back log for every stamped invoice."""
    synced = AS_OF
    w = refs.wells.reset_index()
    wells = pd.DataFrame(dict(CORP_WELL_ID=w.CORP_WELL_ID, WELL_NAME=w.WELL_NAME, API14=w.API14, PAD_ID=w.PAD_ID, DSU_ID=w.DSU_ID, BASIN=w.BASIN,
                              COUNTY=w.COUNTY, STATE_CODE=w.STATE_CODE, WELL_TYPE=w.WELL_TYPE, TRAJECTORY=w.TRAJECTORY, IS_OPERATED=w.IS_OPERATED.astype(bool),
                              WORKING_INTEREST_PCT=w.WORKING_INTEREST_PCT, SPUD_DATE=w.SPUD_DATE, FIRST_PRODUCTION_DATE=w.FIRST_PRODUCTION_DATE,
                              LATERAL_LENGTH_FT=w.LATERAL_LENGTH_FT.fillna(0).astype(int), WELL_STATUS=w.WELL_STATUS, SYNCED_DATE=synced))
    a = refs.afes.reset_index()
    afes = pd.DataFrame(dict(AFE_NUMBER=a.AFE_NUMBER, CORP_WELL_ID=a.CORP_WELL_ID, PROPERTY_NUMBER=a.PROPERTY_NUMBER, AFE_TYPE=a.AFE_TYPE, AFE_DATE=a.AFE_DATE,
                             GROSS_AFE_AMOUNT=a.GROSS_AFE_AMOUNT, COMPANY_WI_DECIMAL=a.COMPANY_WI_DECIMAL, AFE_STATUS=a.AFE_STATUS, SYNCED_DATE=synced))
    v = refs.vendors.reset_index()
    vendors = pd.DataFrame(dict(LIFNR=v.LIFNR, NAME1=v.NAME1, ORT01=v.ORT01, REGIO=v.REGIO, VENDOR_CATEGORY=v.VENDOR_CATEGORY, BLOCKED=v.BLOCKED.astype(bool), SYNCED_DATE=synced))
    stamped = inv[inv.ERP_INVOICE_ID.notna()][["ERP_INVOICE_ID", "OI_INVOICE_ID", "LIFNR", "APPROVED_DATE"]]
    e = refs.exact.set_index("INVOICE_ID")
    log = pd.DataFrame(dict(ERP_INVOICE_ID=stamped.ERP_INVOICE_ID.values, OI_INVOICE_ID=stamped.OI_INVOICE_ID.values, LIFNR=stamped.LIFNR.values,
                            ERP_PLATFORM=e.loc[stamped.ERP_INVOICE_ID, "PLATFORM"].values, ERP_INVOICE_DATE=e.loc[stamped.ERP_INVOICE_ID, "INVOICE_DATE"].values,
                            ERP_AMOUNT_USD=e.loc[stamped.ERP_INVOICE_ID, "AMOUNT_USD"].values, ERP_COST_CATEGORY=e.loc[stamped.ERP_INVOICE_ID, "COST_CATEGORY"].values,
                            ERP_SOURCE_LEDGER=e.loc[stamped.ERP_INVOICE_ID, "SOURCE_LEDGER"].values, ERP_APPROVAL_STATUS=e.loc[stamped.ERP_INVOICE_ID, "APPROVAL_STATUS"].values,
                            ERP_PAID_DATE=e.loc[stamped.ERP_INVOICE_ID, "PAID_DATE"].values))
    log["POSTED_TS"] = pd.to_datetime(log.ERP_INVOICE_DATE) + pd.to_timedelta(2, unit="D") + pd.to_timedelta(9, unit="h")
    return {"OI_REF_WELL": wells, "OI_REF_AFE": afes, "OI_REF_VENDOR": vendors, "OI_ERP_INTEGRATION_LOG": log.sort_values("ERP_INVOICE_ID").reset_index(drop=True)}


# ---------------------------------------------------------------------------
def generate_all(verbose: bool = True) -> dict[str, pd.DataFrame]:
    refs = Refs()
    suppliers = build_suppliers(refs)
    taxonomy = build_taxonomy()
    catalogs = build_item_catalogs(refs, suppliers)
    pricebooks = build_pricebooks(refs, suppliers, catalogs)
    classification = build_classification(suppliers, catalogs)
    inv, lines, tickets = build_transactions(refs, suppliers, catalogs, pricebooks, classification)
    frames = {"OI_SUPPLIER": suppliers, "SCM_PRODUCT_TAXONOMY": taxonomy, "OI_PRICEBOOK_ITEM": pricebooks, "SCM_ITEM_CLASSIFICATION": classification,
              "OI_FIELD_TICKET": tickets, "OI_INVOICE": inv, "OI_INVOICE_LINE": lines, **build_reference_tables(refs, inv), "DATA_DICTIONARY": build_data_dictionary()}
    for name, df in frames.items():
        for col in df.columns:
            if col.endswith("_DATE") or col in ("EFFECTIVE_FROM", "EFFECTIVE_TO"):
                df[col] = pd.to_datetime(df[col], errors="coerce")
            if col.endswith("_TS"):
                df[col] = pd.to_datetime(df[col], errors="coerce")
        if verbose:
            print(f"  {name:26s} {len(df):>9,} rows")
    return frames


if __name__ == "__main__":
    generate_all()
