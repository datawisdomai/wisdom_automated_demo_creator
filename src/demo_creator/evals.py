"""Eval sets from the reviewed queries: create (or update), run at least 3 times, wait, report.

From examples/wisdomai/run_evalset.py. Every eval runs **MIN_RUN_COUNT (3) or more times**
so the score is a sample, not a coin flip: `runEvaluation(runCount=N)` returns a run-group
id; the N EvaluationRuns it spawns are discovered through `evaluationRuns(evalSetIds=...)`
(they share `runGroupId`), each is polled to completion, and `evaluationRunGroup` gives
the consistency view (consistently passing / failing / flaky prompts).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from wisdomai import Client

from .manifest import State
from .reviewed_queries import Registry, to_eval_items
from .spec import DemoSpec


MIN_RUN_COUNT = 3


def run_count_for(spec: DemoSpec) -> int:
    """`wisdom.eval.run_count` with the floor of MIN_RUN_COUNT applied (never fewer than 3 runs)."""
    try:
        n = int(spec.wisdom.eval.get("run_count") or MIN_RUN_COUNT)
    except (TypeError, ValueError):
        n = MIN_RUN_COUNT
    return max(MIN_RUN_COUNT, n)


@dataclass
class EvalReport:
    run_id: str                      # the run the per-prompt detail below comes from (the latest completed run)
    eval_set_id: str
    score: float | None              # mean score across the runs of the group
    total: int
    passed: int                      # prompts matched in the detail run
    failed_prompts: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    raw_status: str = ""
    run_group_id: str | None = None
    run_ids: list[str] = field(default_factory=list)
    run_scores: list[float] = field(default_factory=list)   # one score per run, in run order
    consistently_passing: int | None = None
    consistently_failing: int | None = None
    flaky: int | None = None
    flaky_prompts: list[dict] = field(default_factory=list)  # prompts that passed in some runs but not all

    @property
    def ok(self) -> bool:
        return self.score is not None


def ensure_eval_set(client: Client, spec: DemoSpec, state: State, registry: Registry) -> str:
    items = to_eval_items(registry)
    name = spec.wisdom.eval.get("name") or f"{spec.title} reviewed queries"
    domain_id = state.wisdom["domain_id"]
    existing_id = state.wisdom.get("eval_set_id")
    if existing_id:
        try:
            client.update_eval_set(existing_id, items, name=name, domain_id=domain_id)
            return existing_id
        except Exception:  # noqa: BLE001 — fall through to create a fresh one
            pass
    if not spec.wisdom.existing_domain:   # on a shared domain a same-named set is somebody else's: never adopt it
        for es in client.list_eval_sets(domain_id):
            if str(es.get("name", "")).strip().lower() == name.lower():
                client.update_eval_set(es["id"], items, name=name, domain_id=domain_id)
                state.set("wisdom", "eval_set_id", es["id"])
                return es["id"]
    created = client.create_eval_set(name, domain_id, items)
    eval_set_id = created["id"] if isinstance(created, dict) else str(created)
    state.set("wisdom", "eval_set_id", eval_set_id)
    return eval_set_id


def _list_runs(client: Client, eval_set_id: str, domain_id: str) -> list[dict]:
    try:
        runs = client.evaluation_runs(eval_set_ids=[eval_set_id], domain_ids=[domain_id], limit=20)
    except TypeError:
        runs = client.evaluation_runs(eval_set_ids=[eval_set_id])
    nodes = runs.get("nodes") if isinstance(runs, dict) else runs
    nodes = list(nodes or [])
    nodes.sort(key=lambda r: str(r.get("createdAt") or r.get("startedAt") or ""), reverse=True)
    return nodes


def _turns(run: dict) -> list[dict]:
    """Flatten the doubly-nested evaluations[session][turn] results (verified shape
    2026-10-12: each turn has softEvalScore, softEvalFeedback, gtError, generatedError,
    matchedGtSqlIndex; the prompt text is not repeated, so callers map by index)."""
    out = []
    for session in run.get("evaluations") or run.get("items") or run.get("results") or []:
        turns = session if isinstance(session, list) else session.get("turns") or session.get("items") or [session]
        for t in turns:
            if isinstance(t, dict):
                out.append(t)
    return out


def fetch_run_pages(client: Client, run_id: str, *, page_size: int = 100) -> dict:
    """evaluationRun pages are 0-based; merge every page's evaluations into one payload."""
    first = client.evaluation_run(run_id, page=0, page_size=page_size)
    merged = dict(first)
    merged["evaluations"] = list(first.get("evaluations") or [])
    page = 0
    while (merged.get("pageInfo") or {}).get("hasNextPage") and page < 50:
        page += 1
        nxt = client.evaluation_run(run_id, page=page, page_size=page_size)
        merged["evaluations"] += list(nxt.get("evaluations") or [])
        merged["pageInfo"] = nxt.get("pageInfo")
        if not (nxt.get("pageInfo") or {}).get("hasNextPage"):
            break
    return merged


def report_last(client: Client, spec: DemoSpec, state: State, registry: Registry) -> EvalReport:
    """Report the most recent completed run for the eval set without triggering a new one."""
    eval_set_id = state.wisdom.get("eval_set_id")
    runs = [r for r in _list_runs(client, eval_set_id, state.wisdom["domain_id"]) if r.get("completedAt")]
    if not runs:
        raise RuntimeError("no completed evaluation run yet — run `demo eval` without --report-last")
    group_id = runs[0].get("runGroupId")
    group_runs = [r for r in runs if group_id and r.get("runGroupId") == group_id] or runs[:1]
    return _report_from_group(client, spec, state, eval_set_id, group_runs, prompts=[q.nl for q in registry.local()])


def run_and_wait(client: Client, spec: DemoSpec, state: State, eval_set_id: str, registry: Registry, *, timeout_s: int = 1200) -> EvalReport:
    """Trigger `run_count_for(spec)` (>= 3) runs of the eval set, wait for every run in the
    group to finish, then report the mean score plus the group's consistency figures."""
    domain_id = state.wisdom["domain_id"]
    mode = spec.wisdom.eval.get("experimental_mode", "EXPERIMENTAL_MODE_NONE")
    n_runs = run_count_for(spec)
    prompts = [q.nl for q in registry.local()]   # the eval set carries only the warehouse queries (to_eval_items); keep labels aligned
    import time as _time

    existing = _list_runs(client, eval_set_id, domain_id)
    inflight = [r for r in existing if not r.get("completedAt") and not r.get("cancelledAt")]
    if inflight:  # an earlier trigger is still running — wait on that group instead of starting another
        group_id = inflight[0].get("runGroupId")
        group_runs = [r for r in existing if group_id and r.get("runGroupId") == group_id] or inflight
        state.set("wisdom", "last_eval_run_group_id", group_id)
        return _wait_and_report(client, spec, state, eval_set_id, domain_id, group_id, {r["id"] for r in group_runs}, n_runs, prompts, timeout_s)

    before = {r.get("id") for r in existing}
    trigger_id = client.run_evaluation(domain_id, eval_set_id, run_count=n_runs, experimental_mode=mode)
    # runEvaluation answers with the run-group id (an ET_JOB_RUN_… id). The runs it spawns show up
    # in evaluationRuns(evalSetIds=…) with runGroupId == trigger id (verified 2026-10-13); they may
    # appear one at a time, so keep collecting until n_runs are visible.
    group_id = str(trigger_id)
    state.set("wisdom", "last_eval_run_group_id", group_id)
    return _wait_and_report(client, spec, state, eval_set_id, domain_id, group_id, set(), n_runs, prompts, timeout_s, before=before)


def _wait_and_report(client: Client, spec: DemoSpec, state: State, eval_set_id: str, domain_id: str, group_id: str | None,
                     run_ids: set[str], n_runs: int, prompts: list[str], timeout_s: int, *, before: set | None = None) -> EvalReport:
    import time as _time

    deadline = _time.time() + timeout_s
    group_runs: list[dict] = []
    while _time.time() < deadline:
        runs = _list_runs(client, eval_set_id, domain_id)
        if group_id:
            group_runs = [r for r in runs if r.get("runGroupId") == group_id or r.get("id") in run_ids]
        if not group_runs and before is not None:
            group_runs = [r for r in runs if r.get("id") not in before]
        done = [r for r in group_runs if r.get("completedAt") or r.get("cancelledAt")]
        if len(group_runs) >= n_runs and len(done) == len(group_runs):
            break
        _time.sleep(10)
    if not group_runs:
        raise RuntimeError(f"evaluation was triggered ({group_id}) but no EvaluationRun appeared for eval set {eval_set_id} within {timeout_s}s")
    unfinished = [r["id"] for r in group_runs if not (r.get("completedAt") or r.get("cancelledAt"))]
    if unfinished or len(group_runs) < n_runs:
        raise TimeoutError(f"eval run group {group_id}: {len(group_runs)}/{n_runs} runs visible, {len(unfinished)} still running after {timeout_s}s "
                           f"— re-run `demo eval {spec.name}` to keep waiting or `--report-last` for the finished runs")
    state.set("wisdom", "last_eval_run_id", group_runs[0]["id"])
    return _report_from_group(client, spec, state, eval_set_id, group_runs, prompts=prompts)


def _report_from_group(client: Client, spec: DemoSpec, state: State, eval_set_id: str, group_runs: list[dict], *, prompts: list[str]) -> EvalReport:
    """Mean score across the runs of one run group, per-prompt detail from the latest run, and the
    group's consistency breakdown from evaluationRunGroup (None when the group query is unavailable)."""
    group_runs = sorted(group_runs, key=lambda r: str(r.get("createdAt") or ""))
    reports = []
    for r in group_runs:
        rep = _report_from_run(spec, state, fetch_run_pages(client, r["id"]), r["id"], eval_set_id, prompts=prompts, write=False)
        reports.append(rep)
    detail = reports[-1]
    scores = [rep.score for rep in reports if rep.score is not None]
    mean = sum(scores) / len(scores) if scores else None
    group_id = group_runs[-1].get("runGroupId")
    cp = cf = fl = None
    flaky_prompts: list[dict] = []
    if group_id:
        try:
            g = client.evaluation_run_group(group_id) or {}
            cp, cf, fl = g.get("consistentlyPassing"), g.get("consistentlyFailing"), g.get("flaky")
            for item in g.get("sampleConsistency") or []:
                pc, tr = item.get("passCount"), item.get("totalRuns")
                if pc is not None and tr and 0 < pc < tr:
                    flaky_prompts.append({"prompt": item.get("prompt"), "pass_count": pc, "total_runs": tr})
        except Exception:  # noqa: BLE001 — consistency is a bonus; the mean score stands on its own
            pass
    report = EvalReport(run_id=detail.run_id, eval_set_id=eval_set_id, score=mean, total=detail.total, passed=detail.passed,
                        failed_prompts=detail.failed_prompts, errors=detail.errors, raw_status=detail.raw_status,
                        run_group_id=group_id, run_ids=[rep.run_id for rep in reports], run_scores=scores,
                        consistently_passing=cp, consistently_failing=cf, flaky=fl, flaky_prompts=flaky_prompts)
    spec.paths.ensure().eval_results.write_text(json.dumps({
        "run_group_id": group_id, "run_ids": report.run_ids, "run_scores": scores, "score": mean, "eval_set_id": eval_set_id,
        "run_count": len(reports), "consistently_passing": cp, "consistently_failing": cf, "flaky": fl, "flaky_prompts": flaky_prompts,
        "detail_run_id": detail.run_id, "total": detail.total, "passed": detail.passed, "failed": detail.failed_prompts}, indent=2, default=str))
    state.set("wisdom", "last_score", mean)
    state.set("wisdom", "last_eval_run_scores", scores)
    return report


def _report_from_run(spec: DemoSpec, state: State, run: dict, run_id: str, eval_set_id: str,
                     prompts: list[str] | None = None, *, write: bool = True) -> EvalReport:
    turns = _turns(run)
    info = run.get("pageInfo") or {}
    score = run.get("overallScore")
    if score is None:
        score = run.get("overallCombinedScore", run.get("score"))
    if score is None and info.get("totalPromptCount"):
        score = float(info.get("totalCombinedEvalScore") or 0) / float(info["totalPromptCount"])
    scores = [t.get("softEvalScore") for t in turns if t.get("softEvalScore") is not None]
    if score is None and scores:
        score = sum(scores) / len(scores)
    prompts = prompts or []
    failed = [{"prompt": t.get("prompt") or t.get("question") or (prompts[i] if i < len(prompts) else f"#{i}"),
               "soft_score": t.get("softEvalScore"), "generated_error": t.get("generatedError"),
               "feedback": (t.get("softEvalFeedback") or t.get("automatedFeedback") or t.get("feedback") or "")[:400]}
              for i, t in enumerate(turns) if (t.get("softEvalScore") is not None and t.get("softEvalScore") < 1) or t.get("generatedError")]
    if not turns and info.get("totalPromptCount"):
        turns = [{}] * int(info["totalPromptCount"])
    errors = [f for f in failed if f["generated_error"]]
    report = EvalReport(run_id=run_id, eval_set_id=eval_set_id, score=float(score) if score is not None else None,
                        total=len(turns), passed=len(turns) - len(failed), failed_prompts=failed, errors=errors,
                        raw_status=str(run.get("status") or ("completed" if run.get("completedAt") else "")))
    if write:
        spec.paths.ensure().eval_results.write_text(json.dumps({"run_id": run_id, "eval_set_id": eval_set_id, "score": report.score,
                                                                "total": report.total, "passed": report.passed, "failed": failed}, indent=2, default=str))
        state.set("wisdom", "last_score", report.score)
    return report
