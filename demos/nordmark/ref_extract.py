"""Pull the reference rows the Nordmark generator needs from Ali's Teradata (read-only, no direct access)
through the Wisdom SQL runner on a domain that already exposes it (TD-Wisdomai, database `wisdomai`).
100 rows per call, paged with TOP/QUALIFY ROW_NUMBER, cached under inputs/ref/<name>.csv (gitignored);
an existing file is skipped so the script is resumable.

    .venv/bin/python demos/nordmark/ref_extract.py [--only NAME ...]

Outputs:
  rtl_dim_supplier.csv          60 suppliers (key, name, country, lead time, on-time rate, tier)
  rtl_dim_product.csv           2,000 SKUs (key, sku, name, department, category, subcategory, brand, PL flag, supplier, prices)
  rtl_supplier_po_summary.csv   per supplier: PO lines, avg days late, short-received share (Oct 2024 - Sep 2026)
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from wisdomai import Client  # noqa: E402

DOMAIN = "ET_DOMAIN_d64f246f28534c9f9bf121425a90fee2"   # TD-Wisdomai (connection Ali-TD, database wisdomai)
DB = "wisdomai"
REF = Path(__file__).resolve().parent / "inputs" / "ref"
PAGE = 100

# name -> (select list, from/where, order key)
EXTRACTS: dict[str, tuple[str, str, str]] = {
    "rtl_dim_supplier": ("supplier_key, supplier_name, country, lead_time_days, on_time_rate, payment_terms, supplier_tier, is_active",
                         "RTL_DIM_SUPPLIER", "supplier_key"),
    "rtl_dim_product": ("product_key, sku, product_name, department, category, subcategory, brand, is_private_label, supplier_key, "
                        "price_tier, list_price, unit_cost, launch_date, is_seasonal, product_status",
                        "RTL_DIM_PRODUCT", "product_key"),
    "rtl_supplier_po_summary": ("supplier_key, COUNT(*) AS po_lines, AVG(CAST(days_late AS DECIMAL(10,4))) AS avg_days_late, "
                                "SUM(CASE WHEN po_status = 'Short-Received' THEN 1 ELSE 0 END) AS short_received_lines, "
                                "SUM(CASE WHEN days_late > 3 THEN 1 ELSE 0 END) AS late_lines, SUM(ordered_cost) AS ordered_cost",
                                "RTL_FACT_PURCHASE_ORDER_LINE GROUP BY supplier_key", "supplier_key"),
}


def _clean(v):
    if isinstance(v, str) and len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        return v[1:-1].strip()
    return v.strip() if isinstance(v, str) else v


def extract(client: Client, name: str) -> Path:
    out = REF / f"{name}.csv"
    if out.exists():
        print(f"  {name}: cached ({out.stat().st_size} bytes)")
        return out
    select, source, key = EXTRACTS[name]
    rows_all: list[list] = []
    columns: list[str] = []
    page = 0
    while True:
        lo, hi = page * PAGE + 1, (page + 1) * PAGE
        sql = (f"SELECT * FROM (SELECT {select}, ROW_NUMBER() OVER (ORDER BY {key}) AS rn FROM {source}) t "
               f"WHERE rn BETWEEN {lo} AND {hi} ORDER BY rn")
        t0 = time.time()
        res = client.run_sql(DOMAIN, sql, dialect="teradata", database_name=DB)
        rows = res["rows"]
        if not columns:
            columns = [c for c in res["columns"] if c.lower() != "rn"]
        rows_all += [[_clean(v) for v in r[:len(columns)]] for r in rows]
        print(f"  {name}: page {page + 1} -> {len(rows)} rows ({time.time() - t0:.1f}s)")
        if len(rows) < PAGE:
            break
        page += 1
    REF.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(columns)
        w.writerows(rows_all)
    print(f"  {name}: wrote {len(rows_all)} rows -> {out.relative_to(ROOT)}")
    return out


def main() -> None:
    only = sys.argv[sys.argv.index("--only") + 1:] if "--only" in sys.argv else list(EXTRACTS)
    client = Client.for_deployment("proddemo")
    with client:
        for name in only:
            extract(client, name)


if __name__ == "__main__":
    main()
