"""Parse exported RQ eval-run CSV(s), classify each query pass/fail/flaky.

This is the DEFAULT way to iterate on failing reviewed queries (RQs). Eval runs
(esp. domain-health-triggered ones) take a long time, so rather than re-running,
the user exports a completed run's results from the UI and hands Claude the file:

    WisdomAI UI → domain → Evaluation tab → Run History → a completed run →
    "Export CSV". (Export one CSV per run; export all runs in a group to detect
    flaky queries across runs.)

Then:

    # one run:
    python examples/read_evalset_csv.py "/path/to/run-export.csv"
    # a whole run group (flaky detection needs ≥2 runs of the same set):
    python examples/read_evalset_csv.py run1.csv run2.csv run3.csv
    # also print GT + predicted SQL for the failing/flaky ones:
    python examples/read_evalset_csv.py run*.csv --show-sql

Expected columns (from the UI export):
    Index, Question, Soft Match Result, Automated Feedback, GT SQL, Predicted SQL,
    GT Error, Generated Error, GT Viz ID, Generated Viz ID, Conversation ID

`Soft Match Result` is 1 (pass) or 0 (fail). Across multiple runs of the same
set: always-1 = passing, always-0 = failing, mixed = flaky (the ones most worth
context work).
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict


def _truthy_pass(v: str) -> bool | None:
    v = (v or "").strip().lower()
    if v in ("1", "1.0", "true", "pass", "passed"):
        return True
    if v in ("0", "0.0", "false", "fail", "failed"):
        return False
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_paths", nargs="+", help="one or more exported run CSVs")
    ap.add_argument("--show-sql", action="store_true",
                    help="print GT + predicted SQL for failing/flaky queries")
    args = ap.parse_args()

    # question -> list of per-run records
    by_q: dict[str, list[dict]] = defaultdict(list)
    n_rows = 0
    for path in args.csv_paths:
        try:
            with open(path, newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    q = (row.get("Question") or "").strip()
                    if not q:
                        continue
                    by_q[q].append(row)
                    n_rows += 1
        except FileNotFoundError:
            print(f"file not found: {path}", file=sys.stderr)
            sys.exit(1)

    if not by_q:
        print("no rows parsed — is this an eval-run export CSV?", file=sys.stderr)
        sys.exit(1)

    failing, flaky, passing, unknown = [], [], [], []
    for q, recs in by_q.items():
        results = [_truthy_pass(r.get("Soft Match Result", "")) for r in recs]
        known = [r for r in results if r is not None]
        if not known:
            unknown.append((q, recs))
        elif all(known):
            passing.append((q, recs))
        elif not any(known):
            failing.append((q, recs))
        else:
            flaky.append((q, recs))

    n_runs = max(len(r) for r in by_q.values())
    print(f"parsed {n_rows} rows across {len(args.csv_paths)} file(s) "
          f"({len(by_q)} unique questions, up to {n_runs} run(s) each)")
    print(f"  passing: {len(passing)}   failing: {len(failing)}   "
          f"flaky: {len(flaky)}   unknown: {len(unknown)}")

    def _dump(title: str, group: list) -> None:
        if not group:
            return
        print(f"\n=== {title} ({len(group)}) ===")
        for q, recs in group:
            res = "/".join(
                "1" if _truthy_pass(r.get("Soft Match Result", "")) else "0"
                for r in recs
            )
            print(f"\n• [{res}] {q}")
            # feedback from the first failing record (most informative)
            fb = next(
                (r.get("Automated Feedback") for r in recs
                 if _truthy_pass(r.get("Soft Match Result", "")) is False
                 and r.get("Automated Feedback")),
                recs[0].get("Automated Feedback"),
            )
            if fb:
                print(f"    feedback: {fb.strip()}")
            err = next((r.get("Generated Error") for r in recs
                        if (r.get("Generated Error") or "").strip()), "")
            if err:
                print(f"    generated error: {err.strip()[:200]}")
            if args.show_sql:
                r0 = recs[0]
                if r0.get("GT SQL"):
                    print(f"    GT SQL: {r0['GT SQL'].strip()[:400]}")
                if r0.get("Predicted SQL"):
                    print(f"    predicted SQL: {r0['Predicted SQL'].strip()[:400]}")

    _dump("FLAKY (pass sometimes — usually highest-value to fix)", flaky)
    _dump("FAILING (fail in every run)", failing)
    if unknown:
        _dump("UNKNOWN (no parseable Soft Match Result)", unknown)


if __name__ == "__main__":
    main()
