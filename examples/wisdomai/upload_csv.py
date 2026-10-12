"""Load a local CSV as a new warehouse table on an existing domain.

    # dry-run (default) — shows what would happen, no upload:
    python examples/upload_csv.py <deployment> <domain_id> path/to/data.csv

    # actually upload:
    python examples/upload_csv.py <deployment> <domain_id> path/to/data.csv --apply

Structured CSV ingest IS supported (generateSignedUrlsForCSVUpload -> HTTP PUT ->
processCsv(REUSE)); `upload_csv` returns the new tableId. Column names are
sanitized server-side (spaces/symbols -> underscores; `100% Items` -> `_100__Items`;
duplicate headers get `_duplicated_N`). Unstructured docs are NOT supported — use
a storage connector for those.

⚠️ This is a WRITE: it adds a real table to the domain. Reverse with
`delete_csv_table(table_id, domain_id, raw_file_path)` (the raw_file_path is the
upload `key`). Announce + confirm before --apply.
"""

from __future__ import annotations

import argparse
import os

from wisdomai import Client


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("deployment")
    ap.add_argument("domain_id")
    ap.add_argument("csv_path")
    ap.add_argument("--table-name", default=None, help="override the table/file label")
    ap.add_argument("--apply", action="store_true", help="actually upload")
    args = ap.parse_args()

    if not os.path.isfile(args.csv_path):
        raise SystemExit(f"no such file: {args.csv_path}")
    size = os.path.getsize(args.csv_path)
    label = args.table_name or os.path.basename(args.csv_path)

    if not args.apply:
        print(f"[dry run] would upload {args.csv_path} ({size} bytes) as table "
              f"{label!r} into domain {args.domain_id} on {args.deployment}.")
        print("re-run with --apply (after announcing the write) to perform it.")
        return

    with Client.for_deployment(args.deployment) as c:
        print(f"uploading {args.csv_path} -> {args.domain_id} ...")
        table_id = c.upload_csv(args.domain_id, args.csv_path, table_name=args.table_name)
        print(f"created table: {table_id}")
        # To reverse: c.delete_csv_table(table_id, domain_id, raw_file_path=<upload key>)


if __name__ == "__main__":
    main()
