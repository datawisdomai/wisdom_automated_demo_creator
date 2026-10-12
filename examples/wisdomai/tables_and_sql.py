"""Inspect a domain's tables and run SQL against it. Read-only.

    python examples/tables_and_sql.py <deployment> <domain_id>
    python examples/tables_and_sql.py <deployment> <domain_id> --sql "SELECT 1"

With no --sql, this lists the domain's tables (with columns) and previews the
first table. With --sql, it runs your query and prints the rows.

Notes:
  - run_sql defaults to dialect=duckdb / database_name=wisdom_storage, which is
    right for CSV-backed (ET_ZSHEET_* / wisdom_storage) tables. For a
    warehouse-connected table, pass --dialect / --database.
  - tablePreview.totalRows is unreliable — for an accurate count use
    run_sql(..., "SELECT COUNT(*) FROM ...").
"""

from __future__ import annotations

import argparse

from wisdomai import Client


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("deployment")
    ap.add_argument("domain_id")
    ap.add_argument("--sql", default=None, help="run this SQL instead of listing tables")
    ap.add_argument("--dialect", default="duckdb")
    ap.add_argument("--database", default="wisdom_storage")
    args = ap.parse_args()

    with Client.for_deployment(args.deployment) as c:
        if args.sql:
            out = c.run_sql(
                args.domain_id, args.sql,
                dialect=args.dialect, database_name=args.database,
            )
            print("columns:", out["columns"])
            for row in out["rows"]:
                print("  ", row)
            return

        tables = c.list_tables(args.domain_id)
        print(f"{len(tables)} table(s) in {args.domain_id}:\n")
        for t in tables:
            cols = t.get("columns") or []
            csv = "  [csv]" if t.get("isUserCSVTable") else ""
            print(f"  {t['database']}.{t['name']}  (id={t['id']}, {len(cols)} cols){csv}")
            for col in cols[:6]:
                desc = f"  — {col['description']}" if col.get("description") else ""
                print(f"      {col['name']}: {col['dataType']}{desc}")
            if len(cols) > 6:
                print(f"      ... and {len(cols) - 6} more columns")

        if tables:
            first = tables[0]
            print(f"\npreview of {first['database']}.{first['name']}:")
            prev = c.table_preview(first["id"], args.domain_id, limit=5)
            print("  columns:", prev["columns"])
            for row in prev["rows"]:
                print("  ", row)


if __name__ == "__main__":
    main()
