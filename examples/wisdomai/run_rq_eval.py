"""Run a *viewable* eval over a domain's reviewed queries (RQ eval workaround).

Background: "Domain Health" analysis runs an eval over the domain's reviewed
queries, but its results land on a super-user-gated ``ET_JOB_RUN_…`` job run —
a normal-user key gets "not authorized" on the detail
(``getDomainHealthScoreHistory``). NB: ``createEvalsetFromReviewedQueries(
runEval=True)`` is NOT a way around this — it drives that same gated pipeline.
This script instead hand-builds a *standard* eval set from the reviewed queries'
SQL ground truth and runs it via the plain ``runEvaluation`` mutation, whose
per-query scores ARE readable by a normal-user key. (See CLAUDE.md → "Domain
health vs. reviewed-queries eval".)

    # read-only dry run (always safe): shows the reviewed queries + the plan
    python examples/run_rq_eval.py <deployment> <domain_id>

    # create the eval set + fire the run, then return (does NOT wait):
    python examples/run_rq_eval.py <deployment> <domain_id> --apply

    # check results later (read-only) — runs can take hours:
    python examples/run_rq_eval.py <deployment> <domain_id> --check <eval_set_id>

Defaults: run 3× on chat v1 (EXPERIMENTAL_MODE_NONE, i.e. NOT the Canvas-V2
"Early Release" modes). Override with --run-count / --experimental-mode.

⚠️ --apply is a WRITE: it creates an eval set and spins up real conversations
(cost). Announce + confirm before running it.
"""

from __future__ import annotations

import argparse

from wisdomai import Client

CHAT_V1 = "EXPERIMENTAL_MODE_NONE"  # "Early Release" == the CANVAS_V2_* modes


def _check(c: Client, eval_set_id: str) -> None:
    """Read-only: summarize every run of an eval set, with per-query detail."""
    runs = c.evaluation_runs(eval_set_ids=[eval_set_id])
    if not runs:
        print(f"no runs found yet for eval set {eval_set_id}")
        return
    print(f"{len(runs)} run(s) for eval set {eval_set_id} "
          f"(group {runs[0].get('runGroupId')}):")
    scores: list[float] = []
    detail_id = None
    for r in runs:
        rid = r["id"]
        full = c.evaluation_run(rid)
        sc = full.get("overallCombinedScore")
        if isinstance(sc, (int, float)):
            scores.append(sc)
        state = (
            "cancelled" if full.get("cancelledAt")
            else "done" if full.get("completedAt")
            else "running"
        )
        print(f"  {rid}  [{state}]  overallCombinedScore={sc}")
        if state == "done" and detail_id is None:
            detail_id = rid
    if scores:
        print(f"\nmean overallCombinedScore across {len(scores)} completed run(s): "
              f"{sum(scores) / len(scores):.4f}")
    if detail_id is None:
        print("\n(no completed run yet — re-run --check later for per-query scores)")
        return
    print(f"\nper-query scores (run {detail_id}):")
    full = c.evaluation_run(detail_id)
    for sp, se in zip(full.get("prompts") or [], full.get("evaluations") or []):
        for p, ev in zip(sp, se):
            soft = ev.get("softEvalScore")
            ge = ev.get("generatedError")
            tag = f"  generatedError={str(ge)[:50]!r}" if ge else ""
            print(f"  soft={soft}{tag}  {str(p)[:75]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("deployment")
    ap.add_argument("domain_id")
    ap.add_argument("--run-count", type=int, default=3)
    ap.add_argument("--experimental-mode", default=CHAT_V1)
    ap.add_argument("--check", metavar="EVAL_SET_ID", default=None,
                    help="read-only: show results for an existing eval set")
    ap.add_argument("--apply", action="store_true", help="actually create + run")
    args = ap.parse_args()

    with Client.for_deployment(args.deployment) as c:
        if args.check:
            _check(c, args.check)
            return

        items = c.build_evalset_items_from_reviewed_queries(args.domain_id)
        rqs = c.list_reviewed_queries(args.domain_id, limit=500)
        print(
            f"{len(rqs)} reviewed quer(ies) in {args.domain_id}; "
            f"{len(items)} usable as eval items (executable SQL):"
        )
        for it in items[:20]:
            print(f"  - {it['prompt']}")
        if len(items) > 20:
            print(f"  … and {len(items) - 20} more")

        plan = (
            f"create_eval_set({len(items)} items) + run_evaluation("
            f"run_count={args.run_count}, experimental_mode={args.experimental_mode!r})"
        )
        if not items:
            print("\nno executable SQL reviewed queries — nothing to evaluate.")
            return
        if not args.apply:
            print(f"\n[dry run] would: {plan}")
            print("re-run with --apply (after announcing the write) to perform it.")
            return

        print(f"\nrunning: {plan}")
        res = c.run_reviewed_queries_eval(
            args.domain_id,
            run_count=args.run_count,
            experimental_mode=args.experimental_mode,
        )
        print(
            f"created eval set {res['evalSetId']} "
            f"({res['evalSetName']}, {res['itemCount']} items)\n"
            f"run group: {res['runGroupId']}\n"
            f"runs: {', '.join(res['runIds'])}"
        )
        print(
            "\nfired — NOT waiting (runs can take hours). check later with:\n"
            f"  python examples/run_rq_eval.py {args.deployment} "
            f"{args.domain_id} --check {res['evalSetId']}"
        )


if __name__ == "__main__":
    main()
