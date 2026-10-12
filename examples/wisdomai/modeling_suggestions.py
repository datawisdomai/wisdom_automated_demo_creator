"""Inspect the context-extractor's modeling suggestions for a domain and
(optionally) apply some.

    # read (always safe) — list suggestions, optionally filter by status:
    python examples/modeling_suggestions.py <deployment> <domain_id>
    python examples/modeling_suggestions.py <deployment> <domain_id> --status PENDING

    # apply suggestions by id — dry-run unless --apply:
    python examples/modeling_suggestions.py <deployment> <domain_id> \\
        --apply-ids <id1> <id2> --apply

The extractor mines an uploaded spec/file into MMSuggestion items (knowledge,
column/table descriptions, metrics, formulas, joins, reviewed queries). Each has
`id`, `status` (read back prefixed, e.g. MM_SUGGESTION_STATUS_PENDING), `source`,
and a `task`. `knowledge_extraction_runs` lists the jobs that produced them.

⚠️ `apply_modeling_suggestions` is a WRITE (it mutates the domain model). Reverse
with `undo_modeling_suggestions`. Announce + confirm before --apply.
"""

from __future__ import annotations

import argparse
from collections import Counter

from wisdomai import Client


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("deployment")
    ap.add_argument("domain_id")
    ap.add_argument("--status", default=None, help="substring filter on status, e.g. PENDING")
    ap.add_argument("--apply-ids", nargs="*", default=None, help="suggestion ids to apply")
    ap.add_argument("--apply", action="store_true", help="actually apply --apply-ids")
    args = ap.parse_args()

    with Client.for_deployment(args.deployment) as c:
        runs = c.knowledge_extraction_runs(args.domain_id)
        print(f"{len(runs)} extraction run(s).")

        sugg = c.modeling_suggestions(args.domain_id)
        by_status = Counter(s.get("status") for s in sugg)
        print(f"{len(sugg)} suggestion(s) by status:")
        for st, n in by_status.most_common():
            print(f"  {n:>4}  {st}")

        if args.status:
            sel = [s for s in sugg if args.status.upper() in (s.get("status") or "")]
            print(f"\n{len(sel)} matching status~{args.status!r} (showing 15):")
            for s in sel[:15]:
                task_type = (s.get("task") or {}).get("type")
                print(f"  {s['id']}  {task_type}")

        if args.apply_ids:
            if not args.apply:
                print(f"\n[dry run] would apply_modeling_suggestions: {args.apply_ids}")
                print("re-run with --apply (after announcing the write) to perform it.")
                return
            print(f"\napplying {len(args.apply_ids)} suggestion(s)...")
            res = c.apply_modeling_suggestions(args.domain_id, args.apply_ids)
            for r in res:
                print(f"  {r.get('suggestionId')}: success={r.get('success')} {r.get('errorMessage') or ''}")
            # reverse with: c.undo_modeling_suggestions(domain_id, ids)


if __name__ == "__main__":
    main()
