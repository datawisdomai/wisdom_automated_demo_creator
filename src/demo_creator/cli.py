"""`demo` command line. Every command accepts --json so Claude can parse results.

Writes to Snowflake/Wisdom are dry-run unless --apply is given. Exit codes:
0 ok, 1 a check/step failed (details printed), 2 the spec/setup is wrong.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from . import config
from .manifest import State
from .paths import DemoPaths
from .spec import DemoSpec, SpecError, load_spec, validate_spec


# ---------------------------------------------------------------- helpers
def _spec(args) -> DemoSpec:
    try:
        return load_spec(args.name)
    except SpecError as exc:
        _die(args, str(exc), code=2)
        raise  # unreachable


def _die(args, message: str, *, code: int = 1, **extra) -> None:
    if getattr(args, "json", False):
        print(json.dumps({"ok": False, "error": message, **extra}, indent=2, default=str))
    else:
        print(f"ERROR: {message}", file=sys.stderr)
        for k, v in extra.items():
            print(f"  {k}: {v}", file=sys.stderr)
    sys.exit(code)


def _emit(args, payload: dict, text: str | None = None) -> None:
    if args.json:
        print(json.dumps(payload, indent=2, default=str))
    elif text:
        print(text)


def _require_spec_ok(args, spec: DemoSpec, stage: str) -> None:
    problems = validate_spec(spec, stage=stage)
    if problems:
        _die(args, "demo.yaml / files are not ready", code=2, problems=problems)


def _read_frames(spec: DemoSpec, tables: list[str] | None = None):
    import pandas as pd

    frames = {}
    for t in tables or spec.tables:
        p = spec.paths.parquet(t)
        if not p.is_file():
            raise FileNotFoundError(f"{p} missing — run `demo generate {spec.name}` first")
        frames[t] = pd.read_parquet(p)
    return frames


def _frame_columns(spec: DemoSpec) -> dict[str, "pd.DataFrame"]:
    """Column-only frames (cheap) for schema-diff."""
    import pandas as pd
    import pyarrow.parquet as pq

    out = {}
    for t in spec.tables:
        p = spec.paths.parquet(t)
        if p.is_file():
            out[t] = pd.DataFrame(columns=pq.read_schema(p).names)
    return out


# ---------------------------------------------------------------- new
def cmd_new(args) -> int:
    from .scaffold import scaffold_demo

    path = scaffold_demo(args.name, title=args.title, vertical=args.vertical)
    _emit(args, {"ok": True, "path": str(path)}, f"Created {path}")
    return 0


# ---------------------------------------------------------------- generate
def cmd_generate(args) -> int:
    from .snowflake import schema_diff
    from .validate import load_demo_module

    spec = _spec(args)
    _require_spec_ok(args, spec, "data")
    paths = spec.paths.ensure()
    state = State.load(spec.dir)
    t0 = time.time()
    module = load_demo_module(spec.generator_path, f"{spec.name}_generator")
    gen = getattr(module, "generate_all", None)
    if gen is None:
        _die(args, f"{spec.generator_path.name} must define generate_all() -> dict[str, DataFrame]", code=2)
    try:
        frames = gen(verbose=not args.json)
    except TypeError:
        frames = gen()
    frames = {str(k).upper(): v for k, v in frames.items()}

    counts, mismatches, missing = {}, [], []
    for t in spec.tables:
        if t not in frames:
            missing.append(t)
            continue
        frames[t].to_parquet(paths.parquet(t), index=False)
        counts[t] = len(frames[t])
        exp = spec.snowflake.expected_rows.get(t)
        if exp is not None and exp != counts[t]:
            mismatches.append({"table": t, "expected": exp, "actual": counts[t]})
    unknown = [t for t in frames if t not in spec.tables]
    diff = schema_diff(spec.ddl_path.read_text(), {t: frames[t] for t in spec.tables if t in frames})
    errors = [d for d in diff if d["level"] == "error"]
    ok = not (missing or mismatches or errors)
    state.mark("generate", "ok" if ok else "failed", counts=counts, seconds=round(time.time() - t0),
               mismatches=mismatches, missing=missing, schema_errors=errors)
    payload = {"ok": ok, "counts": counts, "expected_mismatches": mismatches, "missing_tables": missing,
               "unexpected_tables": unknown, "schema_diff": diff, "seconds": round(time.time() - t0)}
    lines = ["", "Row counts:"] + [f"  {t:28s} {n:>10,}" for t, n in counts.items()]
    if mismatches:
        lines.append("Expected row counts differ (fix the generator, or update snowflake.expected_rows in demo.yaml):")
        lines += [f"  {m['table']}: expected {m['expected']:,} got {m['actual']:,}" for m in mismatches]
    if missing:
        lines.append(f"generate_all() returned no frame for: {', '.join(missing)}")
    if unknown:
        lines.append(f"frames not in snowflake.load_order (ignored): {', '.join(unknown)}")
    for d in diff:
        lines.append(f"  schema-diff {d['level'].upper()} {d['table']}: {d['message']}")
    lines.append(f"{'OK' if ok else 'FAILED'} in {payload['seconds']}s — cache: {paths.cache}")
    _emit(args, payload, "\n".join(lines))
    return 0 if ok else 1


# ---------------------------------------------------------------- schema-diff
def cmd_schema_diff(args) -> int:
    from .snowflake import schema_diff

    spec = _spec(args)
    frames = _frame_columns(spec)
    if not frames:
        _die(args, "no generated data yet — run `demo generate` first", code=2)
    diff = schema_diff(spec.ddl_path.read_text(), frames)
    errors = [d for d in diff if d["level"] == "error"]
    _emit(args, {"ok": not errors, "findings": diff},
          "\n".join(f"  {d['level'].upper():5s} {d['table']}: {d['message']}" for d in diff) or "  DDL and generated data agree")
    return 0 if not errors else 1


# ---------------------------------------------------------------- validate
def cmd_validate(args) -> int:
    from .validate import build_duckdb, duckdb_query, run_all_checks, snowflake_query

    spec = _spec(args)
    _require_spec_ok(args, spec, "data")
    state = State.load(spec.dir)
    if args.snowflake:
        from .snowflake import connect

        sf = config.snowflake_config()
        conn = connect(sf, database=spec.snowflake.database, schema=spec.snowflake.schema)
        try:
            checker = run_all_checks(spec, snowflake_query(conn), echo=not args.json)
        finally:
            conn.close()
        step = "validate_snowflake"
    else:
        con = build_duckdb(spec)
        try:
            checker = run_all_checks(spec, duckdb_query(con), echo=not args.json)
        finally:
            con.close()
            if not args.keep_duckdb and spec.paths.duckdb.exists():
                spec.paths.duckdb.unlink()
        step = "validate"
    summary = checker.as_dict()
    state.mark(step, "ok" if checker.ok else "failed", passed=summary["passed"], failed=summary["failed"],
               failures=[f["label"] for f in summary["failures"]])
    text = ("\nALL CHECKS PASSED" if checker.ok else
            f"\n{summary['failed']} CHECK(S) FAILED:\n" + "\n".join(f"  - {f['label']} {f['detail']}" for f in summary["failures"]))
    _emit(args, summary, text)
    return 0 if checker.ok else 1


# ---------------------------------------------------------------- rq-check
def cmd_rq_check(args) -> int:
    from .reviewed_queries import check_queries, load_registry, write_import_csv
    from .validate import build_duckdb, duckdb_query, snowflake_query

    spec = _spec(args)
    state = State.load(spec.dir)
    registry = load_registry(spec)
    payload: dict = {"count": len(registry)}
    if not args.json:
        print(f"Checking {len(registry)} reviewed queries against DuckDB...")
    con = build_duckdb(spec)
    try:
        results = check_queries(registry, duckdb_query(con), echo=not args.json)
    finally:
        con.close()
        if not args.keep_duckdb and spec.paths.duckdb.exists():
            spec.paths.duckdb.unlink()
    payload["duckdb"] = [r.__dict__ for r in results if not r.ok]
    ok = all(r.ok for r in results)

    if args.snowflake:
        from .snowflake import connect

        if not args.json:
            print("\nChecking against Snowflake...")
        sf = config.snowflake_config()
        conn = connect(sf, database=spec.snowflake.database, schema=spec.snowflake.schema)
        try:
            sf_results = check_queries(registry, snowflake_query(conn), echo=not args.json)
        finally:
            conn.close()
        payload["snowflake"] = [r.__dict__ for r in sf_results if not r.ok]
        ok = ok and all(r.ok for r in sf_results)

    if ok:
        out = write_import_csv(registry, spec, spec.paths.ensure().reviewed_csv,
                               connection_name=spec.wisdom.connection_name or config.snowflake_config().connection_name)
        payload["csv"] = str(out)
    payload["ok"] = ok
    state.mark("rq_check" + ("_snowflake" if args.snowflake else ""), "ok" if ok else "failed",
               count=len(registry), failures=len(payload["duckdb"]) + len(payload.get("snowflake", [])))
    _emit(args, payload, f"\n{'all ' + str(len(registry)) + ' ok — wrote ' + payload['csv'] if ok else 'FAILED — fix the SQL above (not the data)'}")
    return 0 if ok else 1


# ---------------------------------------------------------------- ddl
def cmd_ddl(args) -> int:
    from .snowflake import connect, render_grants, run_statements, split_statements, statement_preview

    spec = _spec(args)
    _require_spec_ok(args, spec, "design")
    state = State.load(spec.dir)
    sf = config.snowflake_config()
    statements = split_statements(spec.ddl_path.read_text())
    if args.grants:
        statements = split_statements(render_grants(spec.snowflake.database, spec.snowflake.schema, sf.warehouse, sf.read_role))
    if not args.apply:
        previews = [statement_preview(s) for s in statements]
        _emit(args, {"ok": True, "dry_run": True, "statements": len(statements), "previews": previews},
              f"DRY RUN — {len(statements)} statement(s) would run against {sf.account} as {sf.ddl_role}:\n" +
              "\n".join(f"  [{i:3d}] {p}" for i, p in enumerate(previews)) + "\nRe-run with --apply to execute.")
        return 0
    last = state.step("grants" if args.grants else "ddl")
    if args.start_at and last.get("status") == "failed" and args.start_at > int(last.get("failed_index", args.start_at)):
        _die(args, f"--start-at {args.start_at} would skip statement {last['failed_index']}, which failed last time; "
                   f"resume with --start-at {last['failed_index']} (or 0 to run everything)", code=2)
    conn = connect(sf)
    t0 = time.time()
    try:
        result = run_statements(conn, statements, start_at=args.start_at,
                                on_progress=None if args.json else (lambda i, p: print(f"  ok  [{i:3d}] {p}")))
    finally:
        conn.close()
    step = "grants" if args.grants else "ddl"
    if result.ok:
        state.mark(step, "ok", statements=len(statements), seconds=round(time.time() - t0))
        if not args.grants:
            state.set("snowflake", "database", spec.snowflake.database)
            state.set("snowflake", "schema", spec.snowflake.schema)
        _emit(args, {"ok": True, "executed": len(result.executed), "statements": len(statements)},
              f"{step.upper()} complete: {len(result.executed)} statement(s) in {round(time.time() - t0)}s.")
        return 0
    f = result.failure.as_dict()
    state.mark(step, "failed", failed_index=f["index"], error=f["error"])
    _emit(args, {"ok": False, "executed": len(result.executed), "failure": f},
          f"FAILED at statement [{f['index']}] {f['preview']}\n  error: {f['error']}\n"
          f"  Fix that statement in {spec.snowflake.ddl} and re-run: demo ddl {spec.name} --apply --start-at {f['index']}")
    if not args.json:
        print(json.dumps({"failure": f}, indent=2))
    return 1


# ---------------------------------------------------------------- load
def cmd_load(args) -> int:
    from .snowflake import connect, load_frame, verify_counts

    spec = _spec(args)
    _require_spec_ok(args, spec, "data")
    state = State.load(spec.dir)
    sf = config.snowflake_config()
    tables = [t.upper() for t in args.tables] or spec.tables
    unknown = [t for t in tables if t not in spec.tables]
    if unknown:
        _die(args, f"not in snowflake.load_order: {', '.join(unknown)}", code=2)
    frames = _read_frames(spec, tables)
    if not args.apply:
        _emit(args, {"ok": True, "dry_run": True, "tables": {t: len(df) for t, df in frames.items()}},
              f"DRY RUN — would overwrite {len(frames)} table(s) in {spec.qualified_schema}:\n" +
              "\n".join(f"  {t:28s} {len(df):>10,} rows" for t, df in frames.items()) + "\nRe-run with --apply to load.")
        return 0
    conn = connect(sf, database=spec.snowflake.database, schema=spec.snowflake.schema)
    t0 = time.time()
    loaded, failures = {}, []
    try:
        for t in tables:
            try:
                success, n, dropped = load_frame(conn, frames[t], t, spec.snowflake.database, spec.snowflake.schema)
                loaded[t] = {"rows": n, "dropped_all_null_columns": dropped}
                if not args.json:
                    print(f"  {t:28s} loaded={success} rows={n:,}" + (f" (all-null columns omitted: {', '.join(dropped)})" if dropped else ""))
                if not success:
                    failures.append({"table": t, "error": "write_pandas returned success=False"})
            except Exception as exc:  # noqa: BLE001
                failures.append({"table": t, "error": f"{type(exc).__name__}: {str(exc)[:400]}"})
                if not args.json:
                    print(f"  {t:28s} FAILED: {failures[-1]['error']}")
        counts = verify_counts(conn, spec.snowflake.database, spec.snowflake.schema, tables, spec.snowflake.expected_rows)
    finally:
        conn.close()
    bad_counts = {t: c for t, c in counts.items() if not c["ok"]}
    ok = not failures and not bad_counts
    state.mark("load", "ok" if ok else "failed", tables=list(loaded), failures=failures,
               counts={t: c["count"] for t, c in counts.items()}, seconds=round(time.time() - t0))
    lines = ["", "Verifying counts:"] + [
        f"  {t:28s} {c['count']:>10,}" + ("" if c['expected'] is None else f"  (expected {c['expected']:,}) {'ok' if c['ok'] else 'MISMATCH'}")
        for t, c in counts.items()]
    lines.append(f"{'LOAD complete' if ok else 'LOAD FAILED'} in {round(time.time() - t0)}s." +
                 ("" if ok else " Re-run for the failed tables: demo load " + spec.name + " --apply --tables " + " ".join([f['table'] for f in failures] + list(bad_counts))))
    _emit(args, {"ok": ok, "loaded": loaded, "failures": failures, "counts": counts}, "\n".join(lines))
    return 0 if ok else 1


# ---------------------------------------------------------------- docs
def cmd_docs(args) -> int:
    from .documents import render_all

    spec = _spec(args)
    state = State.load(spec.dir)
    spec.paths.ensure()
    from .documents import context_assets
    if not spec.documents and not context_assets(spec):
        _emit(args, {"ok": True, "rendered": []}, "No documents[] or context_assets[] in demo.yaml — nothing to render.")
        state.mark("docs", "ok", rendered=0)
        return 0
    results = render_all(spec, echo=not args.json)
    ok = all(r["ok"] for r in results)
    state.mark("docs", "ok" if ok else "failed", rendered=[r.get("pdf") for r in results if r["ok"]],
               failures=[r for r in results if not r["ok"]])
    _emit(args, {"ok": ok, "rendered": results}, f"{'rendered' if ok else 'FAILED'} {sum(r['ok'] for r in results)}/{len(results)} document(s) -> {spec.paths.docs_out}")
    return 0 if ok else 1


# ---------------------------------------------------------------- publish
def cmd_publish(args) -> int:
    from .publish import Publisher, PublishError
    from .reviewed_queries import load_registry

    spec = _spec(args)
    _require_spec_ok(args, spec, "all")
    state = State.load(spec.dir)
    registry = load_registry(spec)
    client = config.wisdom_client(spec.wisdom.deployment)
    try:
        pub = Publisher(spec, state, client, apply=args.apply, echo=not args.json)
    except PublishError as exc:
        _die(args, str(exc), code=2)
    if not args.json:
        print(f"{'APPLY' if args.apply else 'DRY RUN'} — publishing '{spec.wisdom.domain_name}' to {spec.wisdom.deployment} / {pub.workspace_label}")
    reports = pub.run(registry, steps=args.only or None)
    failed = [r for r in reports if r.status == "failed"]
    payload = {"ok": not failed, "apply": args.apply, "domain_id": pub.domain_id, "steps": [r.__dict__ for r in reports]}
    _emit(args, payload, "\n" + ("PUBLISH FAILED: " + failed[0].detail if failed else
                                 ("publish complete" if args.apply else "dry run complete — re-run with --apply to execute")))
    return 0 if not failed else 1


# ---------------------------------------------------------------- eval
def cmd_eval(args) -> int:
    from .evals import ensure_eval_set, report_last, run_and_wait
    from .reviewed_queries import load_registry

    spec = _spec(args)
    state = State.load(spec.dir)
    if not state.wisdom.get("domain_id"):
        _die(args, "no domain yet — run `demo publish --apply` first", code=2)
    client = config.wisdom_client(spec.wisdom.deployment)
    registry = load_registry(spec)
    if args.report_last:
        report = report_last(client, spec, state, registry)
    else:
        eval_set_id = ensure_eval_set(client, spec, state, registry)
        if not args.json:
            from .evals import run_count_for
            print(f"Eval set {eval_set_id} with {len(registry)} prompts — running {run_count_for(spec)} times (this takes a while)...")
        report = run_and_wait(client, spec, state, eval_set_id, registry, timeout_s=args.timeout)
    # The eval is a REPORT, not a gate: a completed run is success whatever the score.
    ok = report.score is not None
    state.mark("eval", "ok" if ok else "failed", score=report.score, total=report.total, passed=report.passed, run_id=report.run_id,
               run_group_id=report.run_group_id, run_ids=report.run_ids, run_scores=report.run_scores,
               consistently_passing=report.consistently_passing, consistently_failing=report.consistently_failing, flaky=report.flaky)
    per_run = ", ".join(f"{x:.3f}" for x in report.run_scores) if report.run_scores else "?"
    lines = [f"mean score {report.score:.3f} over {len(report.run_ids) or 1} run(s) [{per_run}] — latest run {report.passed}/{report.total} prompts matched; group {report.run_group_id or report.run_id}"
             if report.score is not None else f"score ? — run {report.run_id}"]
    if report.consistently_passing is not None:
        lines.append(f"  consistency: {report.consistently_passing} always pass, {report.consistently_failing} always fail, {report.flaky} flaky")
    for f in report.flaky_prompts[:15]:
        lines.append(f"  ~ flaky {f['pass_count']}/{f['total_runs']}: {f['prompt']}")
    for f in report.failed_prompts[:25]:
        lines.append(f"  - [{f['soft_score']}] {f['prompt']}" + (f" — ERROR {str(f['generated_error'])[:120]}" if f['generated_error'] else "") + (f"\n      {f['feedback'][:200]}" if f['feedback'] else ""))
    lines.append("EVAL COMPLETE (results in build/eval_results.json)" if ok else "EVAL DID NOT COMPLETE")
    _emit(args, {"ok": ok, **report.__dict__}, "\n".join(lines))
    return 0 if ok else 1


# ---------------------------------------------------------------- metrics-check
def cmd_metrics_check(args) -> int:
    """Compile every metrics.csv expression against its view/table in DuckDB."""
    from .context_files import read_metrics_csv
    from .validate import build_duckdb

    spec = _spec(args)
    metrics = read_metrics_csv(spec.metrics_path)
    con = build_duckdb(spec)
    results = []
    try:
        for m in metrics:
            table = m.view
            if not table:
                results.append({"name": m.name, "ok": False, "error": "no TABLE.COLUMN reference in SQL"}); continue
            try:
                con.execute(f"SELECT {m.sql} FROM {table}").fetchall()
                results.append({"name": m.name, "ok": True, "table": table})
            except Exception as exc:  # noqa: BLE001
                results.append({"name": m.name, "ok": False, "table": table, "error": f"{type(exc).__name__}: {str(exc)[:200]}"})
    finally:
        con.close()
        if spec.paths.duckdb.exists():
            spec.paths.duckdb.unlink()
    bad = [r for r in results if not r["ok"]]
    State.load(spec.dir).mark("metrics_check", "ok" if not bad else "failed", count=len(results), failures=[b["name"] for b in bad])
    _emit(args, {"ok": not bad, "results": results},
          "\n".join(f"  [{'ok ' if r['ok'] else 'ERR'}] {r['name']}" + ("" if r["ok"] else f" — {r['error']}") for r in results) +
          f"\n{len(results) - len(bad)}/{len(results)} metrics compile")
    return 0 if not bad else 1


# ---------------------------------------------------------------- chat / agent
def _need_domain(args, state: State) -> str:
    did = state.wisdom.get("domain_id")
    if not did:
        _die(args, "no domain yet — run `demo publish --apply` first", code=2)
    return did


def cmd_chat(args) -> int:
    from .experiences import ask_followup

    spec = _spec(args)
    state = State.load(spec.dir)
    _need_domain(args, state)
    client = config.wisdom_client(spec.wisdom.deployment)
    question = args.question or spec.chat.get("followup_question")
    if not args.apply:
        _emit(args, {"ok": True, "dry_run": True, "question": question},
              f"DRY RUN — would open a visible conversation on the domain and ask:\n  {question}\nRe-run with --apply.")
        return 0
    if not args.json:
        print(f"Asking: {question}\n(waiting for the full answer, up to {args.timeout}s)...")
    ans = ask_followup(client, spec, state, question=question, timeout_s=args.timeout)
    ok = ans.completed and len(ans.text) > 40 and (ans.score is None or ans.score >= 0.6)
    state.mark("chat", "ok" if ok else "failed", conversation_id=ans.conversation_id, score=ans.score, seconds=ans.seconds, completed=ans.completed)
    text = (f"conversation {ans.conversation_id} — {'complete' if ans.completed else 'TIMED OUT'} in {ans.seconds}s, {len(ans.text)} chars\n"
            f"expected points hit {len(ans.hits)}/{len(ans.hits) + len(ans.misses)}" + (f"; missed: {ans.misses}" if ans.misses else "") +
            f"\n--- answer ---\n{ans.text[:3000]}")
    _emit(args, {"ok": ok, **ans.__dict__, "score": ans.score}, text)
    return 0 if ok else 1


def cmd_agent(args) -> int:
    from .experiences import create_agent

    spec = _spec(args)
    state = State.load(spec.dir)
    _need_domain(args, state)
    dep = config.wisdom_deployment(spec.wisdom.deployment)
    workspace_id = spec.wisdom.workspace_id or dep.workspace_id
    client = config.wisdom_client(spec.wisdom.deployment)
    name = spec.agent.get("name")
    if state.wisdom.get("agent_id") and not args.recreate:
        back = client.get_agent(state.wisdom["agent_id"], workspace_id=workspace_id)
        if back:
            _emit(args, {"ok": True, "agent_id": back["id"], "is_draft": back.get("isDraft"), "existing": True},
                  f"agent '{name}' already exists ({back['id']}, draft={back.get('isDraft')}); use --recreate to rebuild")
            return 0
    if not args.apply:
        _emit(args, {"ok": True, "dry_run": True, "name": name}, f"DRY RUN — would generate a workflow from agent_prompt.md and create DRAFT agent '{name}' (never scheduled). Re-run with --apply.")
        return 0
    me = (client.current_user() or {}).get("email")
    res = create_agent(client, spec, state, workspace_id=workspace_id, default_email=me)
    ok = res.is_draft or not res.schedule_id
    state.mark("agent", "ok" if ok else "failed", agent_id=res.agent_id, is_draft=res.is_draft, nodes=res.workflow_nodes)
    _emit(args, {"ok": ok, **res.__dict__}, f"agent '{res.name}' created as {'DRAFT' if res.is_draft else 'ACTIVE?!'} ({res.agent_id}), {res.workflow_nodes} workflow nodes")
    return 0 if ok else 1


def cmd_app(args) -> int:
    from .experiences import create_live_app

    spec = _spec(args)
    state = State.load(spec.dir)
    _need_domain(args, state)
    dep = config.wisdom_deployment(spec.wisdom.deployment)
    workspace_id = spec.wisdom.workspace_id or dep.workspace_id
    client = config.wisdom_client(spec.wisdom.deployment)
    name = spec.live_app.get("name")
    if state.wisdom.get("app_id") and not args.recreate:
        back = client.get_app_full(state.wisdom["app_id"])
        _emit(args, {"ok": True, "app_id": back["id"], "existing": True, **{k: back.get(k) for k in ("liveSpecVersion", "hasUnpublishedChanges")}},
              f"Live App '{name}' already exists ({back['id']}); use --recreate to build a new one")
        return 0
    if not args.apply:
        _emit(args, {"ok": True, "dry_run": True, "name": name}, f"DRY RUN — would create Live App '{name}' and send live_app_prompt.md to build it (takes 5-15 minutes). Re-run with --apply.")
        return 0
    if not args.json:
        print(f"Creating Live App '{name}' and sending the build prompt (this takes 5-15 minutes)...")
    res = create_live_app(client, spec, state, workspace_id=workspace_id, timeout_s=args.timeout, echo=not args.json)
    ok = res.completed
    state.mark("app", "ok" if ok else "failed", app_id=res.app_id, conversation_id=res.conversation_id, seconds=res.seconds,
               live_spec_version=res.live_spec_version)
    _emit(args, {"ok": ok, **res.__dict__},
          f"Live App '{res.name}' ({res.app_id}) — build {'complete' if ok else 'DID NOT FINISH'} in {res.seconds}s; conversation {res.conversation_id}\n"
          f"liveSpecVersion={res.live_spec_version} unpublished={res.has_unpublished_changes}\n--- assistant ---\n{res.assistant_text[:1500]}")
    return 0 if ok else 1


# ---------------------------------------------------------------- health
def cmd_health(args) -> int:
    """Trigger a Domain Health analysis run and LEAVE IT RUNNING: it is the final step of every build so an
    SE can demo the suggestions it produces in the Domain Health tab. Nothing in the pipeline acts on them."""
    spec = _spec(args)
    state = State.load(spec.dir)
    domain_id = _need_domain(args, state)
    if not args.apply:
        _emit(args, {"ok": True, "dry_run": True}, f"DRY RUN — would queue a Domain Health analysis run for {domain_id}. Re-run with --apply.")
        return 0
    client = config.wisdom_client(spec.wisdom.deployment)
    res = client.trigger_domain_health_check(domain_id)
    code = (res.get("status") or {}).get("code")
    ok = code in (None, "OK", "SUCCESS") or bool(res.get("jobRunId")) or bool(res.get("alreadyQueued"))
    state.set("wisdom", "health_job_run_id", res.get("jobRunId"))
    state.mark("health", "ok" if ok else "failed", job_run_id=res.get("jobRunId"), already_queued=res.get("alreadyQueued"), code=code)
    _emit(args, {"ok": ok, **res}, f"Domain Health analysis {'already queued' if res.get('alreadyQueued') else 'queued'} (job {res.get('jobRunId')}); left running — the SE demos its suggestions from the domain's Domain Health tab; nothing here acts on them.")
    return 0 if ok else 1


# ---------------------------------------------------------------- teardown
def cmd_teardown(args) -> int:
    """Delete everything this demo created in Wisdom (app, agent, eval set, domain).
    The shared connection and the Snowflake database are kept. IRREVERSIBLE."""
    from wisdomai import GraphQLError

    spec = _spec(args)
    state = State.load(spec.dir)
    w = dict(state.wisdom)
    plan = [("Live App", w.get("app_id")), ("agent", w.get("agent_id")), ("eval set", w.get("eval_set_id")), ("domain", w.get("domain_id"))]
    plan = [(k, v) for k, v in plan if v]
    if not plan:
        _emit(args, {"ok": True, "deleted": []}, "nothing recorded in .state.json to delete")
        return 0
    if not args.i_mean_it:
        _emit(args, {"ok": True, "dry_run": True, "would_delete": plan},
              "DRY RUN — would PERMANENTLY delete on " + spec.wisdom.deployment + ":\n" + "\n".join(f"  {k}: {v}" for k, v in plan) +
              "\nRe-run with --i-mean-it to delete. The Snowflake database and the shared connection are kept.")
        return 0
    client = config.wisdom_client(spec.wisdom.deployment)
    deleted, failures = [], []
    for kind, ident in plan:
        try:
            if kind == "Live App":
                client.delete_app(ident)
            elif kind == "agent":
                client.delete_agent(ident)
            elif kind == "eval set":
                client.delete_eval_set(ident)
            elif kind == "domain":
                client.delete_domain(ident)
            deleted.append((kind, ident))
            if not args.json:
                print(f"  deleted {kind} {ident}")
        except GraphQLError as exc:
            failures.append((kind, ident, str(exc)[:200]))
            if not args.json:
                print(f"  FAILED {kind} {ident}: {str(exc)[:200]}")
    # forget the Wisdom ids and the Wisdom-side steps; keep connection_id and Snowflake steps
    keep = {k: v for k, v in state.wisdom.items() if k == "connection_id"}
    state.overwrite(sections={"wisdom": keep}, drop_steps=("publish", "eval", "health", "app", "chat", "agent"))
    ok = not failures
    _emit(args, {"ok": ok, "deleted": deleted, "failures": failures},
          f"teardown {'complete' if ok else 'INCOMPLETE'}: deleted {len(deleted)}/{len(plan)}; .state.json reset (connection kept)")
    return 0 if ok else 1


# ---------------------------------------------------------------- report / all
def cmd_report(args) -> int:
    from .report import render

    spec = _spec(args)
    state = State.load(spec.dir)
    out = spec.dir / "DEMO_REPORT.md"
    out.write_text(render(spec, state))
    _emit(args, {"ok": True, "path": str(out)}, f"wrote {out}")
    return 0


ALL_STEPS = ["generate", "validate", "ddl", "load", "validate_snowflake", "rq_check_snowflake", "metrics_check", "docs",
             "publish", "eval", "app", "chat", "agent", "report", "health"]   # health LAST: left running for the SE to demo its suggestions


def cmd_all(args) -> int:
    """Run every step in order, skipping ones already ok in .state.json; stop at the first failure."""
    spec = _spec(args)
    state = State.load(spec.dir)
    plan = [
        ("generate", ["generate", spec.name]),
        ("validate", ["validate", spec.name]),
        ("ddl", ["ddl", spec.name, "--apply"]),
        ("load", ["load", spec.name, "--apply"]),
        ("validate_snowflake", ["validate", spec.name, "--snowflake"]),
        ("rq_check_snowflake", ["rq-check", spec.name, "--snowflake"]),
        ("metrics_check", ["metrics-check", spec.name]),
        ("docs", ["docs", spec.name]),
        ("publish", ["publish", spec.name, "--apply"]),
        ("eval", ["eval", spec.name]),
        ("app", ["app", spec.name, "--apply"]),
        ("chat", ["chat", spec.name, "--apply"]),
        ("agent", ["agent", spec.name, "--apply"]),
        ("report", ["report", spec.name]),
        ("health", ["health", spec.name, "--apply"]),   # always the final step; the analysis stays queued/running for the SE
    ]
    if not args.apply:
        _emit(args, {"ok": True, "dry_run": True, "steps": [p[0] for p in plan]},
              "DRY RUN — `demo all --apply` would run: " + " → ".join(p[0] for p in plan) +
              "\nSteps already ok in .state.json are skipped unless --redo is given.")
        return 0
    for step, argv in plan:
        state = State.load(spec.dir)
        if not args.redo and step not in ("report",) and state.step_ok(step) and step != "publish":
            if not args.json:
                print(f"== {step}: already ok, skipping")
            continue
        if not args.json:
            print(f"\n== {step}: demo {' '.join(argv)}")
        rc = main(argv + (["--json"] if args.json else []))
        if rc != 0:
            print(f"\nSTOPPED at step '{step}' (exit {rc}). Fix it (see /run-step) and re-run `demo all {spec.name} --apply`.", file=sys.stderr)
            return rc
    print("\nALL STEPS COMPLETE")
    return 0


# ---------------------------------------------------------------- status
def cmd_status(args) -> int:
    spec = _spec(args)
    state = State.load(spec.dir)
    problems = validate_spec(spec, stage="all")
    payload = {"demo": spec.name, "title": spec.title, "snowflake": spec.qualified_schema,
               "wisdom": {"deployment": spec.wisdom.deployment, "workspace_id": spec.wisdom.workspace_id,
                          "domain_name": spec.wisdom.domain_name, **state.wisdom},
               "steps": state.data["steps"], "spec_problems": problems}
    lines = [f"{spec.title} ({spec.name}) — {spec.qualified_schema} → {spec.wisdom.deployment}/{spec.wisdom.domain_name}"]
    for step, info in state.data["steps"].items():
        lines.append(f"  {step:20s} {info.get('status', '?'):7s} {info.get('at', '')}")
    if state.wisdom:
        lines.append("  wisdom ids: " + ", ".join(f"{k}={v}" for k, v in state.wisdom.items()))
    if problems:
        lines.append("  spec problems:")
        lines += [f"    - {p}" for p in problems]
    _emit(args, payload, "\n".join(lines))
    return 0


# ---------------------------------------------------------------- doctor
def cmd_doctor(args) -> int:
    from .doctor import run_checks

    checks = run_checks(args.deployment, network=not args.offline)
    if args.json:
        print(json.dumps([c.__dict__ for c in checks], indent=2))
    else:
        for c in checks:
            print(f"[{'OK ' if c.ok else 'FAIL'}] {c.name}: {c.detail}")
            if not c.ok and c.fix:
                print(f"       fix: {c.fix}")
    return 0 if all(c.ok for c in checks) else 1


# ---------------------------------------------------------------- parser
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="demo", description="Build WisdomAI demos end to end.")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, func, help_, *, demo=True):
        sp = sub.add_parser(name, help=help_)
        if demo:
            sp.add_argument("name", help="demo name (folder under demos/) or path")
        sp.set_defaults(func=func)
        return sp

    d = add("doctor", cmd_doctor, "check keys, Snowflake and Wisdom access", demo=False)
    d.add_argument("--deployment", default="proddemo")
    d.add_argument("--offline", action="store_true")

    n = add("new", cmd_new, "scaffold demos/<name>/")
    n.add_argument("--title")
    n.add_argument("--vertical")

    add("generate", cmd_generate, "run generator.py -> build/_cache/*.parquet, check counts and DDL columns")
    add("schema-diff", cmd_schema_diff, "compare DDL columns with the generated data")

    v = add("validate", cmd_validate, "run built-in + control-point checks (DuckDB, or --snowflake after load)")
    v.add_argument("--snowflake", action="store_true")
    v.add_argument("--keep-duckdb", action="store_true")

    r = add("rq-check", cmd_rq_check, "execute every reviewed query; write build/reviewed-queries.csv")
    r.add_argument("--snowflake", action="store_true")
    r.add_argument("--keep-duckdb", action="store_true")

    dd = add("ddl", cmd_ddl, "run the DDL statement by statement (dry-run without --apply)")
    dd.add_argument("--apply", action="store_true")
    dd.add_argument("--grants", action="store_true", help="run read-only grants for the Wisdom role instead")
    dd.add_argument("--start-at", type=int, default=0, help="resume from this statement index")

    ld = add("load", cmd_load, "load cached tables into Snowflake with write_pandas (dry-run without --apply)")
    ld.add_argument("--apply", action="store_true")
    ld.add_argument("--tables", nargs="*", default=[])

    add("docs", cmd_docs, "render documents[] markdown specs to build/docs/*.pdf")
    pb = add("publish", cmd_publish, "create/update the Wisdom domain: connection, database, knowledge, reviewed queries (dry-run without --apply)")
    pb.add_argument("--apply", action="store_true")
    pb.add_argument("--only", nargs="*", help="run only these steps: connection domain database instructions knowledge metrics reviewed_queries lookup documents extraction")
    ev = add("eval", cmd_eval, "build the eval set from the reviewed queries, run it at least 3 times, report the mean score and flaky prompts")
    ev.add_argument("--timeout", type=int, default=1200)
    ev.add_argument("--report-last", action="store_true", help="report the last completed run instead of starting one")
    add("metrics-check", cmd_metrics_check, "compile every metrics.csv expression in DuckDB")
    ch = add("chat", cmd_chat, "ask the follow-up question in a visible conversation and judge the answer")
    ch.add_argument("--apply", action="store_true")
    ch.add_argument("--question")
    ch.add_argument("--timeout", type=int, default=420)
    ap = add("app", cmd_app, "create the Live App from live_app_prompt.md (one prompt; takes minutes)")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--recreate", action="store_true")
    ap.add_argument("--timeout", type=int, default=1500)
    ag = add("agent", cmd_agent, "create the agent from agent_prompt.md as a DRAFT (never runs)")
    ag.add_argument("--apply", action="store_true")
    ag.add_argument("--recreate", action="store_true")
    td = add("teardown", cmd_teardown, "PERMANENTLY delete the demo's Wisdom app, agent, eval set and domain (dry-run without --i-mean-it)")
    td.add_argument("--i-mean-it", action="store_true")
    he = add("health", cmd_health, "queue a Domain Health analysis run and leave it running for the SE (always the last step of a build)")
    he.add_argument("--apply", action="store_true")
    add("report", cmd_report, "write DEMO_REPORT.md from .state.json")
    al = add("all", cmd_all, "run every step in order (skips steps already ok); dry-run without --apply")
    al.add_argument("--apply", action="store_true")
    al.add_argument("--redo", action="store_true", help="re-run steps even if already ok")
    add("status", cmd_status, "show .state.json and spec problems")
    return p


def main(argv: list[str] | None = None) -> int:
    if argv is not None and "--json" in argv:  # allow --json anywhere (cmd_all appends it)
        argv = ["--json"] + [a for a in argv if a != "--json"]
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except SystemExit as exc:  # _die() inside a nested call
        return int(exc.code or 0)


if __name__ == "__main__":
    sys.exit(main())
