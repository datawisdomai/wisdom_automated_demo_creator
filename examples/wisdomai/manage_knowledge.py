"""Read and manage a domain's knowledge (free-form business context).

    # read (always safe):
    python examples/manage_knowledge.py <deployment> <domain_id>

    # add an entry — prints what it WOULD do unless you pass --apply:
    python examples/manage_knowledge.py <deployment> <domain_id> \\
        --add-name "Fiscal year" --add-desc "Our fiscal year starts in February." --apply

Knowledge entries are {name, description}. `add_knowledge` de-dupes by
description server-side. `update_knowledge`/`delete_knowledge` match on the exact
existing description (see the commented examples below).

⚠️ add/update/delete are WRITES. Per the repo protocol, announce the deployment,
domain (name + id), and exact effect before running with --apply, and get an
explicit go. Writes are irreversible.
"""

from __future__ import annotations

import argparse

from wisdomai import Client


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("deployment")
    ap.add_argument("domain_id")
    ap.add_argument("--add-name", default=None)
    ap.add_argument("--add-desc", default=None)
    ap.add_argument("--apply", action="store_true", help="actually perform the write")
    args = ap.parse_args()

    with Client.for_deployment(args.deployment) as c:
        entries = c.get_domain_knowledge(args.domain_id)
        print(f"{len(entries)} knowledge entr(ies) in {args.domain_id}:")
        for e in entries:
            print(f"  - {e.get('name') or '(unnamed)'}: {(e.get('description') or '')[:80]}")

        if args.add_desc:
            new_entry = {"description": args.add_desc}
            if args.add_name:
                new_entry["name"] = args.add_name
            if not args.apply:
                print(f"\n[dry run] would add_knowledge: {new_entry}")
                print("re-run with --apply (after announcing the write) to perform it.")
                return
            print(f"\nadding knowledge: {new_entry}")
            c.add_knowledge(args.domain_id, [new_entry])
            print("done. current count:", len(c.get_domain_knowledge(args.domain_id)))

    # Update / delete (uncomment and adapt — both are writes, both irreversible):
    #   c.update_knowledge(domain_id,
    #       old={"description": "old text"},
    #       updated={"name": "New name", "description": "new text"})
    #   c.delete_knowledge(domain_id, {"description": "text to remove"})


if __name__ == "__main__":
    main()
