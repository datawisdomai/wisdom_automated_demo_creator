"""End-to-end admin example: create a domain, wire a database to it, add knowledge.

Usage:
    python examples/create_domain_with_context.py <deployment> <connection_id> <database> [--apply]

This walks the full admin path:
  1. createDomain  -> get a new domain ID
  2. addDatabaseToDomain -> attach a database (and its tables) from a connection
  3. addKnowledge  -> attach two business-context entries
  4. get_domain_knowledge -> read it back

The connection_id must point to an existing connection. You can create one via
`client.create_connection(...)`, or set it up in the WisdomAI UI and reference
its ID here.

⚠️ This is a WRITE. It defaults to a dry run; pass --apply to actually create,
and announce the write first.
"""

import argparse

from wisdomai import Client


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("deployment")
    ap.add_argument("connection_id")
    ap.add_argument("database")
    ap.add_argument("--apply", action="store_true", help="actually create the domain")
    args = ap.parse_args()

    if not args.apply:
        print(f"[dry run] would create a domain on '{args.deployment}', attach "
              f"database {args.database!r} (connection {args.connection_id}), and "
              f"add 2 knowledge entries.")
        print("re-run with --apply (after announcing the write) to perform it.")
        return

    with Client.for_deployment(args.deployment) as client:
        domain = client.create_domain(
            name=f"API-created domain ({args.database})",
            description=f"Created via wisdomai client for {args.database}",
        )
        print(f"created domain: {domain['id']}  ({domain['name']})")

        client.add_database_to_domain(
            domain_id=domain["id"],
            connection_id=args.connection_id,
            database_name=args.database,
        )
        print(f"attached database {args.database}")

        client.add_knowledge(
            domain_id=domain["id"],
            entries=[
                {
                    "name": "Fiscal year",
                    "description": "Our fiscal year starts in February.",
                },
                {
                    "name": "Active users",
                    "description": (
                        "An 'active user' is any account that logged in at least "
                        "once in the trailing 28 days."
                    ),
                },
            ],
        )
        print("added 2 knowledge entries")

        entries = client.get_domain_knowledge(domain["id"])
        print(f"\ndomain now has {len(entries)} knowledge entries:")
        for e in entries:
            print(f"  - {e.get('name') or '(unnamed)'}: {e['description']}")


if __name__ == "__main__":
    main()
