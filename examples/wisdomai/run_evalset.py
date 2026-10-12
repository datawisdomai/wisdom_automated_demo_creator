"""Create an eval set from a JSON file, run it, wait for results, print scores.

Usage:
    python examples/run_evalset.py <deployment> <domain_id> <path/to/evalset.json> [--run-count N] [--parallelization N]

JSON shape:
    {
      "name": "My eval",
      "items": [
        {"prompt": "...", "sql": ["SELECT ..."]},
        ...
      ]
    }
  (single-turn shorthand; the Client wraps items into [[...]] for you)

Or pass `--existing-eval-set-id ID` to skip creation and just run an existing one.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wisdomai import Client


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("deployment")
    ap.add_argument("domain_id")
    ap.add_argument("evalset_path", nargs="?")
    ap.add_argument("--existing-eval-set-id", default=None)
    ap.add_argument("--run-count", type=int, default=1)
    ap.add_argument("--parallelization", type=int, default=None)
    ap.add_argument("--timeout-s", type=float, default=900.0)
    args = ap.parse_args()

    with Client.for_deployment(args.deployment) as client:
        if args.existing_eval_set_id:
            eval_set_id = args.existing_eval_set_id
            print(f"using existing eval set: {eval_set_id}")
        else:
            if not args.evalset_path:
                ap.error("evalset_path required when --existing-eval-set-id not given")
            spec = json.loads(Path(args.evalset_path).read_text())
            es = client.create_eval_set(
                name=spec["name"],
                domain_id=args.domain_id,
                items=spec["items"],
            )
            eval_set_id = es["id"]
            print(f"created eval set: {eval_set_id}  ({es['name']}, v{es['version']})")

        run_id = client.run_evaluation(
            domain_id=args.domain_id,
            eval_set_id=eval_set_id,
            run_count=args.run_count,
            parallelization=args.parallelization,
        )
        print(f"started run: {run_id}  (timeout {args.timeout_s:.0f}s)")

        try:
            run = client.wait_for_evaluation_run(run_id, timeout_s=args.timeout_s)
        except TimeoutError as e:
            print(f"\n{e}", file=sys.stderr)
            print(
                f"run still in flight; check later with "
                f"client.evaluation_run('{run_id}')",
                file=sys.stderr,
            )
            sys.exit(2)

        if run.get("cancelledAt"):
            print(f"\nrun was cancelled at {run['cancelledAt']}")
            return

        print(f"\ncompleted at: {run['completedAt']}")
        print(f"overall combined score: {run.get('overallCombinedScore')}")
        pi = run.get("pageInfo") or {}
        print(
            f"sessions={pi.get('totalSessions')}  "
            f"prompts={pi.get('totalPromptCount')}  "
            f"combinedScore={pi.get('totalCombinedEvalScore')}"
        )

        prompts = run.get("prompts") or []
        evals = run.get("evaluations") or []
        for si, (session_prompts, session_evals) in enumerate(zip(prompts, evals)):
            for ti, (p, ev) in enumerate(zip(session_prompts, session_evals)):
                soft = ev.get("softEvalScore")
                manual = ev.get("manualScore")
                gen_err = ev.get("generatedError")
                line = f"  [{si}:{ti}] soft={soft} manual={manual}"
                if gen_err:
                    line += f"  generatedError={gen_err[:60]!r}"
                print(line)
                print(f"        prompt: {p}")


if __name__ == "__main__":
    main()
