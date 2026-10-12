"""Eval sets from the reviewed queries: create (or update), run once, wait, report.

From examples/wisdomai/run_evalset.py. `run_count` is pinned to 1 because a
larger count returns a run-group id that `wait_for_evaluation_run` cannot poll.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from wisdomai import Client

from .manifest import State
from .reviewed_queries import Registry, to_eval_items
from .spec import DemoSpec


@dataclass
class EvalReport:
    run_id: str
    eval_set_id: str
    score: float | None
    total: int
    passed: int
    failed_prompts: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    raw_status: str = ""

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
            client.update_eval_set(existing_id, items, name=name)
            return existing_id
        except Exception:  # noqa: BLE001 — fall through to create a fresh one
            pass
    for es in client.list_eval_sets(domain_id):
        if str(es.get("name", "")).strip().lower() == name.lower():
            client.update_eval_set(es["id"], items, name=name)
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
    run_id = runs[0]["id"]
    return _report_from_run(spec, state, fetch_run_pages(client, run_id), run_id, eval_set_id, prompts=[q.nl for q in registry])


def run_and_wait(client: Client, spec: DemoSpec, state: State, eval_set_id: str, registry: Registry, *, timeout_s: int = 1200) -> EvalReport:
    domain_id = state.wisdom["domain_id"]
    mode = spec.wisdom.eval.get("experimental_mode", "EXPERIMENTAL_MODE_NONE")
    import time as _time

    existing = _list_runs(client, eval_set_id, domain_id)
    inflight = [r for r in existing if not r.get("completedAt") and not r.get("cancelledAt")]
    if inflight:  # an earlier trigger is still running — wait on it instead of starting another
        run_id = inflight[0]["id"]
        state.set("wisdom", "last_eval_run_id", run_id)
        client.wait_for_evaluation_run(run_id, timeout_s=timeout_s, poll_s=10)
        return _report_from_run(spec, state, fetch_run_pages(client, run_id), run_id, eval_set_id, prompts=[q.nl for q in registry])
    before = {r.get("id") for r in existing}
    trigger_id = client.run_evaluation(domain_id, eval_set_id, run_count=1, experimental_mode=mode)
    # runEvaluation now answers with an ET_JOB_RUN_… id that evaluationRun(id) cannot resolve
    # (2026-10-12); find the EvaluationRun it spawned by listing the set's runs.
    run_id = trigger_id if not str(trigger_id).startswith("ET_JOB_RUN_") else None
    deadline = _time.time() + 180
    while run_id is None and _time.time() < deadline:
        new = [r for r in _list_runs(client, eval_set_id, domain_id) if r.get("id") not in before]
        if new:
            run_id = new[0]["id"]
            break
        _time.sleep(5)
    if run_id is None:
        raise RuntimeError(f"evaluation was triggered ({trigger_id}) but no EvaluationRun appeared for eval set {eval_set_id} within 180s")
    state.set("wisdom", "last_eval_run_id", run_id)
    client.wait_for_evaluation_run(run_id, timeout_s=timeout_s, poll_s=10)
    return _report_from_run(spec, state, fetch_run_pages(client, run_id), run_id, eval_set_id, prompts=[q.nl for q in registry])


def _report_from_run(spec: DemoSpec, state: State, run: dict, run_id: str, eval_set_id: str,
                     prompts: list[str] | None = None) -> EvalReport:
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
    spec.paths.ensure().eval_results.write_text(json.dumps({"run_id": run_id, "eval_set_id": eval_set_id, "score": report.score,
                                                            "total": report.total, "passed": report.passed, "failed": failed}, indent=2, default=str))
    state.set("wisdom", "last_score", report.score)
    return report
