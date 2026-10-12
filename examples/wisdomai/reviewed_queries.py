"""Read and manage a domain's reviewed queries (question + SQL pairs that teach
the domain the "right" answer to a question).

    # read (always safe):
    python examples/reviewed_queries.py <deployment> <domain_id>

    # add a reviewed query — dry-run unless --apply:
    python examples/reviewed_queries.py <deployment> <domain_id> \\
        --question "How many vendors?" --sql "SELECT COUNT(DISTINCT vendor_id) FROM vendor_payments_acme_2025" --apply

The read view (`list_reviewed_queries`) returns items keyed by `id`, `question`,
`enabled`, `isAnswerExecutable`, `answerType`, `createdAt`, `updatedAt`.

⚠️ add/delete are WRITES — announce + confirm before --apply. `delete_reviewed_queries`
is irreversible.
"""

from __future__ import annotations

import argparse

from wisdomai import Client


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("deployment")
    ap.add_argument("domain_id")
    ap.add_argument("--question", default=None)
    ap.add_argument("--sql", default=None)
    ap.add_argument("--dialect", default="duckdb")
    ap.add_argument("--apply", action="store_true", help="actually perform the write")
    args = ap.parse_args()

    with Client.for_deployment(args.deployment) as c:
        items = c.list_reviewed_queries(args.domain_id, limit=50)
        print(f"{len(items)} reviewed quer(ies) in {args.domain_id}:")
        for q in items:
            flag = "" if q.get("enabled", True) else "  [disabled]"
            print(f"  {q['id']}  {q.get('question')}{flag}")

        if args.question and args.sql:
            item = {"query": args.question, "sql": args.sql}
            if not args.apply:
                print(f"\n[dry run] would add_sql_reviewed_queries: {item} (dialect={args.dialect})")
                print("re-run with --apply (after announcing the write) to perform it.")
                return
            print(f"\nadding reviewed query: {args.question!r}")
            created = c.add_sql_reviewed_queries(args.domain_id, [item], dialect=args.dialect)
            print("created:", [x.get("id") for x in created])

    # Delete (write, irreversible):
    #   c.delete_reviewed_queries(domain_id, ["<reviewed_query_id>", ...])


if __name__ == "__main__":
    main()
