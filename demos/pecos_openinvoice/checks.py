"""Story control-point checks for the Pecos Ridge OpenInvoice demo.

`demo validate` calls run(q, check, spec) against DuckDB before loading and against Snowflake
after. `q(sql)` returns rows; `check(label, cond, detail)` records a pass/fail. CP1..CP5 per
DEMO_PLAN.md / demo.yaml. The reconciliation section reads the partner extract in inputs/ref/
so the exact slice is proven to match SPEND_INVOICE to the cent.
"""
import csv
import json
from pathlib import Path

import catalog as C

HERE = Path(__file__).resolve().parent
HERO = "Corrosion inhibitor, water-soluble, filming amine"
CASING = "Production casing 5-1/2 in 20 lb/ft P-110 BTC"


def _targets(spec, cp):
    for c in spec.control_points:
        if c.id == cp:
            return {t["metric"]: (t["op"], t["value"]) for t in c.targets}
    return {}


def _ok(op, target, v):
    """_ok(*targets[metric], observed) — the YAML target comes first, the observed value last."""
    return {">=": v >= target, "<=": v <= target, "==": v == target, ">": v > target, "<": v < target}[op]


def run(q, check, spec):
    print("\n== Baseline health ==")
    (n_inv,) = q("SELECT COUNT(*) FROM OI_INVOICE")[0]
    (n_lines,) = q("SELECT COUNT(*) FROM OI_INVOICE_LINE")[0]
    check("40k to 70k invoices", 40_000 <= n_inv <= 70_000, f"({n_inv:,})")
    check("lines per invoice between 2.2 and 4.5", 2.2 <= n_lines / n_inv <= 4.5, f"({n_lines / n_inv:.2f})")
    (bad_sum,) = q("""SELECT COUNT(*) FROM OI_INVOICE i JOIN (SELECT OI_INVOICE_ID, SUM(LINE_AMOUNT_USD) AS S FROM OI_INVOICE_LINE GROUP BY OI_INVOICE_ID) l
                      ON l.OI_INVOICE_ID = i.OI_INVOICE_ID WHERE ABS(l.S - i.INVOICE_TOTAL_USD) > 0.011""")[0]
    check("every invoice total equals the sum of its lines", bad_sum == 0, f"({bad_sum} off)")
    (bad_ext,) = q("SELECT COUNT(*) FROM OI_INVOICE_LINE WHERE ABS(QUANTITY * UNIT_PRICE_USD - LINE_AMOUNT_USD) > 0.5")[0]
    check("quantity x unit price reproduces the line amount (within 50 cents)", bad_ext / n_lines < 0.002, f"({bad_ext} lines off)")
    (orphan_cls,) = q("""SELECT COUNT(*) FROM OI_INVOICE_LINE l LEFT JOIN SCM_ITEM_CLASSIFICATION c ON c.LIFNR = l.LIFNR AND c.SUPPLIER_ITEM_CODE = l.SUPPLIER_ITEM_CODE
                         WHERE c.CLASSIFICATION_ID IS NULL""")[0]
    check("every invoiced item has a classification row (approved or not)", orphan_cls == 0, f"({orphan_cls})")
    (dmin, dmax) = q("SELECT MIN(INVOICE_DATE), MAX(INVOICE_DATE) FROM OI_INVOICE")[0]
    check("invoices span 2022-01 to 2026-09", str(dmin)[:7] == "2022-01" and str(dmax)[:7] == "2026-09", f"({dmin} .. {dmax})")
    (well_share,) = q("SELECT AVG(CASE WHEN CORP_WELL_ID IS NOT NULL THEN 1.0 ELSE 0.0 END) FROM OI_INVOICE")[0]
    check("at least 95% of invoices resolve to a well", well_share >= 0.95, f"({well_share:.3f})")

    print("\n== Keys exist in the partner tables (inputs/ref) ==")
    ref = HERE / "inputs" / "ref"

    def ids(name, col):
        with (ref / f"{name}.csv").open(newline="") as fh:
            return {json.loads(r[col]) if r[col].startswith('"') else r[col] for r in csv.DictReader(fh) if r[col]}
    vendors = ids("s4_vendor_lfa1", "LIFNR"); wells = ids("well_master", "CORP_WELL_ID"); afes = ids("od_afe_header", "AFE_NUMBER")
    props = ids("xwalk_well", "QUORUM_PROPERTY_NUMBER"); contracts = ids("clm_contract", "CLM_CONTRACT_ID")
    sup = {r[0] for r in q("SELECT DISTINCT LIFNR FROM OI_SUPPLIER")}
    check("every OI_SUPPLIER.LIFNR is in S4_VENDOR_LFA1", sup <= vendors, f"({len(sup - vendors)} unknown)")
    w = {r[0] for r in q("SELECT DISTINCT CORP_WELL_ID FROM OI_INVOICE WHERE CORP_WELL_ID IS NOT NULL")}
    check("every CORP_WELL_ID is in WELL_MASTER", w <= wells, f"({len(w - wells)} unknown)")
    a = {r[0] for r in q("SELECT DISTINCT AFE_NUMBER FROM OI_INVOICE WHERE AFE_NUMBER IS NOT NULL")}
    check("every AFE_NUMBER is in OD_AFE_HEADER", a <= afes, f"({len(a - afes)} unknown of {len(a)})")
    p = {r[0] for r in q("SELECT DISTINCT PROPERTY_NUMBER FROM OI_INVOICE WHERE PROPERTY_NUMBER IS NOT NULL")}
    check("every PROPERTY_NUMBER is in ZFI_SYSTEM_XWALK", p <= props, f"({len(p - props)} unknown of {len(p)})")
    cc = {r[0] for r in q("SELECT DISTINCT CLM_CONTRACT_ID FROM OI_PRICEBOOK_ITEM WHERE CLM_CONTRACT_ID IS NOT NULL")}
    check("every pricebook CLM_CONTRACT_ID is in CLM_CONTRACT", cc <= contracts, f"({sorted(cc)})")

    print("\n== Exact slice reconciles to SPEND_INVOICE ==")
    exact_path = ref / "spend_invoice_exact.csv"
    if not exact_path.is_file():
        exact_path = ref / "spend_invoice_exact.partial.csv"   # smoke runs before the extract finished
    with exact_path.open(newline="") as fh:
        exact = {json.loads(r["INVOICE_ID"]): round(float(r["AMOUNT_USD"]), 2) for r in csv.DictReader(fh)}
    got = {r[0]: round(float(r[1]), 2) for r in q("SELECT ERP_INVOICE_ID, INVOICE_TOTAL_USD FROM OI_INVOICE WHERE ERP_INVOICE_ID IS NOT NULL")}
    missing = set(exact) - set(got); extra = set(got) - set(exact)
    mism = [k for k in exact if k in got and abs(exact[k] - got[k]) > 0.005]
    check("every SPEND_INVOICE row in the slice has a stamped OpenInvoice header", not missing and not extra, f"({len(missing)} missing, {len(extra)} extra)")
    check("stamped invoice totals equal SPEND_INVOICE.AMOUNT_USD to the cent", not mism, f"({len(mism)} mismatches)")
    t5 = _targets(spec, "CP5")
    check("CP5 exact_slice_reconciles", _ok(*t5.get("cp5_exact_slice_reconciles", ("==", 1)), 1 if (not missing and not extra and not mism) else 0))
    (legacy,) = q("SELECT COUNT(*) FROM OI_INVOICE WHERE INVOICE_DATE < DATE '2025-01-01' AND ERP_INVOICE_ID IS NOT NULL")[0]
    check("no invoice before 2025-01-01 carries an ERP id (Legacy - Coupa id only)", legacy == 0, f"({legacy})")

    print("\n== CP1: corrosion inhibitor price gap and pack premium ==")
    t = _targets(spec, "CP1")
    rows = q(f"""SELECT SUPPLIER_NAME, STD_QUANTITY, SPEND_USD, AVG_STD_UNIT_PRICE_USD, SAVINGS_AT_BEST_PRICE_USD, PRICE_DISPERSION_PCT
                 FROM V_SUPPLIER_ALTERNATIVES WHERE GENERIC_PRODUCT_NAME = '{HERO}' AND INVOICE_YEAR = 2025 ORDER BY AVG_STD_UNIT_PRICE_USD""")
    for r in rows:
        print(f"   {r[0]:32s} gal={float(r[1]):>12,.0f} spend=${float(r[2]):>12,.0f} $/gal={float(r[3]):6.2f} savings=${float(r[4]):>10,.0f}")
    check("two suppliers sold the hero product in 2025", len(rows) == 2, f"({len(rows)})")
    gap = float(rows[0][5]) if rows else 0.0
    check(f"CP1 supplier price gap {t['cp1_supplier_price_gap_pct'][0]} {t['cp1_supplier_price_gap_pct'][1]}%", _ok(*t["cp1_supplier_price_gap_pct"], gap), f"({gap:.1f}%)")
    sav = sum(float(r[4]) for r in rows)
    check(f"CP1 savings at best price 2025 {t['cp1_savings_at_best_price_2025_usd'][0]} {t['cp1_savings_at_best_price_2025_usd'][1]:,}", _ok(*t["cp1_savings_at_best_price_2025_usd"], sav), f"(${sav:,.0f})")
    packs = q(f"""SELECT INVOICED_UOM, SUM(LINE_AMOUNT_USD) / NULLIF(SUM(STD_QUANTITY), 0) FROM V_INVOICE_LINE_CLASSIFIED
                  WHERE GENERIC_PRODUCT_NAME = '{HERO}' AND INVOICE_YEAR = 2025 AND LIFNR = '{C.BASIN_CHEMICAL}' GROUP BY INVOICED_UOM""")
    pp = {r[0]: float(r[1]) for r in packs}
    prem = (pp.get("PAIL", 0) / pp.get("TOTE", 1) - 1) * 100 if pp.get("TOTE") else 0.0
    check(f"CP1 pail premium over tote at Basin Chemical {t['cp1_pack_premium_pct'][0]} {t['cp1_pack_premium_pct'][1]}%", _ok(*t["cp1_pack_premium_pct"], prem), f"({prem:.1f}%: {pp})")

    print("\n== CP2: Redline RL100 above its 2026 price book ==")
    t = _targets(spec, "CP2")
    (n_over, var, n_disp) = q(f"""SELECT COUNT(*), COALESCE(SUM(PRICE_VARIANCE_USD), 0), SUM(CASE WHEN LINE_STATUS = 'Disputed' THEN 1 ELSE 0 END)
                                  FROM V_PRICEBOOK_VARIANCE WHERE LIFNR = '{C.REDLINE}' AND SUPPLIER_ITEM_CODE = 'RL100' AND INVOICE_YEAR = 2026 AND IS_OVER_CONTRACT = 1""")[0]
    n_over, var, n_disp = int(n_over), float(var), int(n_disp or 0)
    check(f"CP2 Redline RL100 lines over contract in 2026 {t['cp2_redline_over_pricebook_lines_2026'][0]} {t['cp2_redline_over_pricebook_lines_2026'][1]}", _ok(*t["cp2_redline_over_pricebook_lines_2026"], n_over), f"({n_over})")
    check(f"CP2 Redline variance 2026 {t['cp2_redline_variance_usd_2026'][0]} ${t['cp2_redline_variance_usd_2026'][1]:,}", _ok(*t["cp2_redline_variance_usd_2026"], var), f"(${var:,.0f})")
    share = n_disp / n_over if n_over else 0
    check(f"CP2 disputed share of those lines {t['cp2_disputed_share_redline'][0]} {t['cp2_disputed_share_redline'][1]}", _ok(*t["cp2_disputed_share_redline"], share), f"({share:.2f})")
    (other_over,) = q(f"SELECT COUNT(*) FROM V_PRICEBOOK_VARIANCE WHERE LIFNR IN ('{C.KERMIT}', '{C.MONAHANS}') AND INVOICE_YEAR = 2026 AND PRICE_VARIANCE_PCT > 2")[0]
    check("Kermit and Monahans stay within 2% of their price books in 2026", other_over == 0, f"({other_over})")

    print("\n== CP3: one casing, many descriptions ==")
    t = _targets(spec, "CP3")
    rows = q(f"""SELECT COUNT(DISTINCT SUPPLIER_ITEM_DESCRIPTION), COUNT(DISTINCT INVOICED_UOM), COUNT(DISTINCT LIFNR),
                 MIN(AVG_PRICE), MAX(AVG_PRICE) FROM (
                   SELECT SUPPLIER_ITEM_DESCRIPTION, INVOICED_UOM, LIFNR, SUM(LINE_AMOUNT_USD) / NULLIF(SUM(STD_QUANTITY), 0) AS AVG_PRICE
                   FROM V_INVOICE_LINE_CLASSIFIED WHERE GENERIC_PRODUCT_NAME = '{CASING}' AND INVOICE_YEAR >= 2025 AND STD_QUANTITY > 0
                   GROUP BY SUPPLIER_ITEM_DESCRIPTION, INVOICED_UOM, LIFNR) x""")[0]
    n_desc, n_uom, n_sup, pmin, pmax = int(rows[0]), int(rows[1]), int(rows[2]), float(rows[3] or 0), float(rows[4] or 0)
    spread = (pmax / pmin - 1) * 100 if pmin else 0
    print(f"   {n_desc} descriptions, {n_uom} UOMs, {n_sup} suppliers, $/ft {pmin:.2f}..{pmax:.2f}")
    check(f"CP3 distinct descriptions {t['cp3_distinct_descriptions'][0]} {t['cp3_distinct_descriptions'][1]}", _ok(*t["cp3_distinct_descriptions"], n_desc), f"({n_desc})")
    check(f"CP3 distinct UOMs {t['cp3_distinct_uoms'][0]} {t['cp3_distinct_uoms'][1]}", _ok(*t["cp3_distinct_uoms"], n_uom), f"({n_uom})")
    check(f"CP3 $/ft spread {t['cp3_price_spread_pct'][0]} {t['cp3_price_spread_pct'][1]}%", _ok(*t["cp3_price_spread_pct"], spread), f"({spread:.1f}%)")

    print("\n== CP4: classification backlog ==")
    t = _targets(spec, "CP4")
    (tot26, uncl26) = q("SELECT SUM(LINE_AMOUNT_USD), SUM(CASE WHEN IS_CLASSIFIED = 0 THEN LINE_AMOUNT_USD ELSE 0 END) FROM V_INVOICE_LINE_CLASSIFIED WHERE INVOICE_YEAR = 2026")[0]
    share = float(uncl26) / float(tot26)
    check(f"CP4 unclassified share of 2026 line spend in [{t['cp4_unclassified_share_2026'][1]}, 0.10]", 0.06 <= share <= 0.10, f"({share:.3f} = ${float(uncl26):,.0f} of ${float(tot26):,.0f})")
    (rent,) = q("SELECT SUM(CASE WHEN OI_SUPPLIER_CATEGORY = 'Rental Equipment' THEN LINE_AMOUNT_USD ELSE 0 END) / NULLIF(SUM(LINE_AMOUNT_USD), 0) FROM V_UNCLASSIFIED_SPEND WHERE INVOICE_YEAR = 2026")[0]
    check(f"CP4 rental share of unclassified {t['cp4_rental_share_of_unclassified'][0]} {t['cp4_rental_share_of_unclassified'][1]}", _ok(*t["cp4_rental_share_of_unclassified"], float(rent)), f"({float(rent):.2f})")
    (share25,) = q("SELECT SUM(CASE WHEN IS_CLASSIFIED = 0 THEN LINE_AMOUNT_USD ELSE 0 END) / SUM(LINE_AMOUNT_USD) FROM V_INVOICE_LINE_CLASSIFIED WHERE INVOICE_YEAR = 2025")[0]
    check("2025 unclassified share is below the 2026 share (backlog is recent)", float(share25) < share, f"({float(share25):.3f})")
    (needs,) = q("SELECT COUNT(*) FROM SCM_ITEM_CLASSIFICATION WHERE REVIEW_STATUS = 'Needs review'")[0]
    check("there is an ML-suggested review queue", needs >= 20, f"({needs})")

    print("\n== CP5: operational hook (AFE lines to wells) ==")
    t = _targets(spec, "CP5")
    (n_wells,) = q("""SELECT COUNT(DISTINCT CORP_WELL_ID) FROM V_AFE_PRODUCT_COST WHERE LEVEL1_FAMILY = 'Proppant' AND CORP_WELL_ID IS NOT NULL
                      AND FIRST_INVOICE_DATE >= DATE '2025-01-01'""")[0]
    check(f"CP5 wells with 2025-26 proppant AFE lines {t['cp5_wells_with_afe_lines'][0]} {t['cp5_wells_with_afe_lines'][1]}", _ok(*t["cp5_wells_with_afe_lines"], int(n_wells)), f"({n_wells})")
    (afe_spend,) = q("SELECT SUM(SPEND_USD) FROM V_AFE_PRODUCT_COST")[0]
    check("capital spend by AFE and generic product is populated", float(afe_spend) > 50_000_000, f"(${float(afe_spend):,.0f})")
