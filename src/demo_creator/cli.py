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
    from .reviewed_queries import Registry, check_queries, load_registry, write_import_csv
    from .validate import build_duckdb, duckdb_query, snowflake_query

    spec = _spec(args)
    state = State.load(spec.dir)
    registry = load_registry(spec)
    payload: dict = {"count": len(registry)}
    if not args.json:
        print(f"Checking {len(registry)} reviewed queries against DuckDB...")
    con = build_duckdb(spec)
    try:
        results = check_queries(registry, duckdb_query(con), echo=not args.json, skip_tags=("cross_db", "federated"))
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
            sf_results = check_queries(registry, snowflake_query(conn), echo=not args.json, skip_tags=("cross_db", "federated"))
        finally:
            conn.close()
        payload["snowflake"] = [r.__dict__ for r in sf_results if not r.ok]
        ok = ok and all(r.ok for r in sf_results)

    # Queries that only run in the target domain: cross_db (joins to databases that exist only there) run
    # on the demo's warehouse connection; federated (source=<connection>) run on THAT connection in its
    # own dialect and database. Both go through Wisdom's SQL runner (read-only), the engine the demo answers with.
    cross = Registry()
    for rq in registry:
        if "cross_db" in rq.tags and not rq.federated:
            cross.add(rq.nl, rq.sql, tags=rq.tags)
    fed_sources = {f.connection: f for f in spec.wisdom.federated_sources}
    fed_groups = [(name, registry.for_source(name)) for name in fed_sources if len(registry.for_source(name))]
    remote = len(cross) + sum(len(g) for _, g in fed_groups)
    if remote and args.domain:
        domain_id = state.wisdom.get("domain_id") or spec.wisdom.domain_id
        if not domain_id:
            _die(args, "--domain needs wisdom.domain_id in demo.yaml or a published domain in .state.json", code=2)
        client = config.wisdom_client(spec.wisdom.deployment)
        payload["domain"] = []
        if len(cross):
            if not args.json:
                print(f"\nChecking {len(cross)} cross_db queries through the Wisdom SQL runner on domain {domain_id}...")

            def wisdom_query(sql: str):
                return client.run_sql(domain_id, sql, dialect=spec.wisdom.dialect, database_name=spec.snowflake.database)["rows"]
            dom_results = check_queries(cross, wisdom_query, echo=not args.json)
            payload["domain"] += [r.__dict__ for r in dom_results if not r.ok]
            ok = ok and all(r.ok for r in dom_results)
        for name, group in fed_groups:
            src = fed_sources[name]
            if not args.json:
                print(f"\nChecking {len(group)} federated queries on '{name}' ({src.dialect}, {src.database}) through the Wisdom SQL runner...")

            def fed_query(sql: str, _src=src):
                return client.run_sql(domain_id, sql, dialect=_src.dialect, database_name=_src.database)["rows"]
            fed_results = check_queries(group, fed_query, echo=not args.json)
            payload["domain"] += [r.__dict__ for r in fed_results if not r.ok]
            ok = ok and all(r.ok for r in fed_results)
    elif remote and not args.json:
        print(f"\n{remote} cross_db/federated queries skipped locally — run `demo rq-check {spec.name} --domain` to check them in the target domain")

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
    gen = spec.raw.get("generated_documents") or {}
    generated = []
    if gen.get("module"):
        # demo-specific renderer (e.g. contract PDFs built from the generated frames): render(spec, out_dir) -> [{file, ok}]
        from .validate import load_demo_module
        mod = load_demo_module(spec.dir / gen["module"], f"{spec.name}_generated_documents")
        generated = mod.render(spec, spec.dir / str(gen.get("out") or "build/contracts"), echo=not args.json)
    ok = all(r["ok"] for r in results) and all(r.get("ok", True) for r in generated)
    state.mark("docs", "ok" if ok else "failed", rendered=[r.get("pdf") for r in results if r["ok"]],
               generated=len(generated), failures=[r for r in results if not r["ok"]])
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
        if spec.wisdom.existing_domain:
            print(f"{'APPLY' if args.apply else 'DRY RUN'} — EXTENDING EXISTING domain '{spec.wisdom.domain_name}' ({spec.wisdom.domain_id}) on "
                  f"{spec.wisdom.deployment} / {pub.workspace_label}: adds {spec.qualified_schema} through connection "
                  f"'{spec.wisdom.connection_name}'; nothing pre-existing is deleted, renamed, overwritten or auto-accepted")
        else:
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


def _select(entries: list[dict], key: str | None, what: str, args) -> list[dict]:
    """The spec entries to act on: all of them, or the one whose key matches --<what>."""
    if not key:
        return entries
    hit = [e for e in entries if e.get("key") == key]
    if not hit:
        _die(args, f"no {what} with key '{key}' in demo.yaml (have {[e.get('key') for e in entries]})", code=2)
    return hit


def cmd_chat(args) -> int:
    """Ask every chats[] question (or --chat KEY, or an ad-hoc --question) and judge the answers."""
    from .experiences import ask_followup

    spec = _spec(args)
    state = State.load(spec.dir)
    _need_domain(args, state)
    client = config.wisdom_client(spec.wisdom.deployment)
    entries = _select(spec.chats, args.chat, "chat", args) or [{"key": "followup"}]
    if args.question:
        entries = [{**entries[0], "followup_question": args.question, "expected_points": entries[0].get("expected_points") or []}]
    if not args.apply:
        qs = "\n".join(f"  [{e.get('key')}] {e.get('followup_question') or e.get('question')}" for e in entries)
        _emit(args, {"ok": True, "dry_run": True, "questions": [e.get("followup_question") for e in entries]},
              f"DRY RUN — would open {len(entries)} visible conversation(s) on the domain and ask:\n{qs}\nRe-run with --apply.")
        return 0
    results, all_ok = [], True
    for e in entries:
        question = e.get("followup_question") or e.get("question")
        if not args.json:
            print(f"Asking [{e.get('key')}]: {question}\n(waiting for the full answer, up to {args.timeout}s)...")
        ans = ask_followup(client, spec, state, question=question, timeout_s=args.timeout, entry=e)
        ok = ans.completed and len(ans.text) > 40 and (ans.score is None or ans.score >= 0.6)
        all_ok = all_ok and ok
        results.append({"key": e.get("key"), "ok": ok, **ans.__dict__, "score": ans.score})
        if not args.json:
            print(f"conversation {ans.conversation_id} — {'complete' if ans.completed else 'TIMED OUT'} in {ans.seconds}s, {len(ans.text)} chars\n"
                  f"expected points hit {len(ans.hits)}/{len(ans.hits) + len(ans.misses)}" + (f"; missed: {ans.misses}" if ans.misses else "") +
                  f"\n--- answer ---\n{ans.text[:3000]}\n")
    if not args.chat and not args.question:
        first = results[0]
        state.mark("chat", "ok" if all_ok else "failed", conversation_id=first["conversation_id"], score=first["score"], seconds=first["seconds"],
                   completed=first["completed"], chats={r["key"]: {"conversation_id": r["conversation_id"], "score": r["score"], "ok": r["ok"]} for r in results})
    _emit(args, {"ok": all_ok, "results": results}, f"{sum(1 for r in results if r['ok'])}/{len(results)} chat(s) ok")
    return 0 if all_ok else 1


def cmd_agent(args) -> int:
    """Create every agents[] entry (or --agent KEY) as a DRAFT; existing ones are kept unless --recreate."""
    from .experiences import create_agent

    spec = _spec(args)
    state = State.load(spec.dir)
    _need_domain(args, state)
    dep = config.wisdom_deployment(spec.wisdom.deployment)
    workspace_id = spec.wisdom.workspace_id or dep.workspace_id
    client = config.wisdom_client(spec.wisdom.deployment)
    entries = _select(spec.agents, args.agent, "agent", args)
    if not entries:
        _emit(args, {"ok": True, "skipped": True}, "no agents[] / agent in demo.yaml")
        return 0
    results, all_ok, first_key = [], True, entries[0].get("key")
    for e in entries:
        name, key = e.get("name"), e.get("key")
        have = dict((state.wisdom.get("agents") or {}).get(key) or {})
        if not have.get("agent_id") and key == spec.agents[0].get("key") and state.wisdom.get("agent_id"):
            have = {"agent_id": state.wisdom["agent_id"]}
        if have.get("agent_id") and not args.recreate:
            back = client.get_agent(have["agent_id"], workspace_id=workspace_id)
            if back:
                results.append({"key": key, "ok": True, "agent_id": back["id"], "name": name, "is_draft": back.get("isDraft"), "existing": True})
                if not args.json:
                    print(f"agent '{name}' already exists ({back['id']}, draft={back.get('isDraft')}); use --recreate to rebuild")
                continue
        if not args.apply:
            results.append({"key": key, "ok": True, "dry_run": True, "name": name})
            if not args.json:
                print(f"DRY RUN — would generate a workflow from {e.get('prompt', 'agent_prompt.md')} and create DRAFT agent '{name}' (never scheduled).")
            continue
        me = (client.current_user() or {}).get("email")
        res = create_agent(client, spec, state, workspace_id=workspace_id, default_email=me, entry=e)
        ok = res.is_draft or not res.schedule_id
        all_ok = all_ok and ok
        results.append({"key": key, "ok": ok, **res.__dict__})
        if not args.json:
            print(f"agent '{res.name}' created as {'DRAFT' if res.is_draft else 'ACTIVE?!'} ({res.agent_id}), {res.workflow_nodes} workflow nodes")
    if args.apply and not args.agent:
        first = next((r for r in results if r.get("key") == first_key), results[0])
        state.mark("agent", "ok" if all_ok else "failed", agent_id=first.get("agent_id"), is_draft=first.get("is_draft"),
                   nodes=first.get("workflow_nodes"), agents={r["key"]: {"agent_id": r.get("agent_id"), "ok": r["ok"]} for r in results})
    _emit(args, {"ok": all_ok, "results": results}, f"{sum(1 for r in results if r['ok'])}/{len(results)} agent(s) ok" + ("" if args.apply else " (dry run; re-run with --apply)"))
    return 0 if all_ok else 1


def cmd_app(args) -> int:
    """Build every live_apps[] entry (or --app KEY) from its prompt; existing ones are kept unless --recreate."""
    from .experiences import create_live_app

    spec = _spec(args)
    state = State.load(spec.dir)
    _need_domain(args, state)
    dep = config.wisdom_deployment(spec.wisdom.deployment)
    workspace_id = spec.wisdom.workspace_id or dep.workspace_id
    client = config.wisdom_client(spec.wisdom.deployment)
    entries = _select(spec.live_apps, args.app, "live app", args)
    if not entries:
        _emit(args, {"ok": True, "skipped": True}, "no live_apps[] / live_app in demo.yaml")
        return 0
    results, all_ok, first_key = [], True, entries[0].get("key")
    for e in entries:
        name, key = e.get("name"), e.get("key")
        have = dict((state.wisdom.get("apps") or {}).get(key) or {})
        if not have.get("app_id") and key == spec.live_apps[0].get("key") and state.wisdom.get("app_id"):
            have = {"app_id": state.wisdom["app_id"], "conversation_id": state.wisdom.get("app_conversation_id")}
        if have.get("app_id") and have.get("conversation_id") and not args.recreate:
            back = client.get_app_full(have["app_id"])
            results.append({"key": key, "ok": True, "app_id": back["id"], "name": name, "existing": True,
                            **{k: back.get(k) for k in ("liveSpecVersion", "hasUnpublishedChanges")}})
            if not args.json:
                print(f"Live App '{name}' already exists ({back['id']}); use --recreate to build a new one")
            continue
        if not args.apply:
            results.append({"key": key, "ok": True, "dry_run": True, "name": name})
            if not args.json:
                print(f"DRY RUN — would create Live App '{name}' and send {e.get('prompt', 'live_app_prompt.md')} to build it (takes 5-15 minutes).")
            continue
        if not args.json:
            print(f"Creating Live App '{name}' and sending the build prompt (this takes 5-15 minutes)...")
        res = create_live_app(client, spec, state, workspace_id=workspace_id, timeout_s=args.timeout, echo=not args.json, entry=e)
        ok = res.completed
        all_ok = all_ok and ok
        results.append({"key": key, "ok": ok, **res.__dict__})
        if not args.json:
            print(f"Live App '{res.name}' ({res.app_id}) — build {'complete' if ok else 'DID NOT FINISH'} in {res.seconds}s; conversation {res.conversation_id}\n"
                  f"liveSpecVersion={res.live_spec_version} unpublished={res.has_unpublished_changes}\n--- assistant ---\n{res.assistant_text[:1500]}\n")
    if args.apply and not args.app:
        first = next((r for r in results if r.get("key") == first_key), results[0])
        state.mark("app", "ok" if all_ok else "failed", app_id=first.get("app_id"), conversation_id=first.get("conversation_id"),
                   seconds=first.get("seconds"), live_spec_version=first.get("live_spec_version") or first.get("liveSpecVersion"),
                   apps={r["key"]: {"app_id": r.get("app_id"), "ok": r["ok"]} for r in results})
    _emit(args, {"ok": all_ok, "results": results}, f"{sum(1 for r in results if r['ok'])}/{len(results)} Live App(s) ok" + ("" if args.apply else " (dry run; re-run with --apply)"))
    return 0 if all_ok else 1


# ---------------------------------------------------------------- health
def cmd_s3(args) -> int:
    from .s3_sync import sync

    spec = _spec(args)
    state = State.load(spec.dir)
    res = sync(spec, apply=args.apply, echo=not args.json)
    if args.apply:
        state.mark("s3", "ok" if res.get("ok") else "failed", **{k: v for k, v in res.items() if k != "ok"})
    _emit(args, res, (f"{'uploaded' if args.apply else 'would upload'} {res.get('uploaded', res.get('would_upload'))} of {res.get('files')} PDFs to s3://{res.get('bucket')}/{res.get('prefix')}/"
                      if res.get("ok") else f"FAILED: {res.get('error') or res}"))
    return 0 if res.get("ok") else 1


def cmd_health(args) -> int:
    """Trigger the Domain Health ANALYSIS (what the "Run Analysis" button on the domain's Health ->
    Recommendations tab does: triggerEvalAnalysis, verified 2026-10-16) and LEAVE IT RUNNING: it is the
    final step of every build so an SE can demo the recommendations it produces. Nothing in the pipeline
    acts on them. `triggerDomainHealthCheck` is only the quick table-health check (10 s, no
    recommendations); it is run as well so the Health level is fresh."""
    spec = _spec(args)
    state = State.load(spec.dir)
    domain_id = _need_domain(args, state)
    if not args.apply:
        _emit(args, {"ok": True, "dry_run": True}, f"DRY RUN — would start the Domain Health analysis for {domain_id}. Re-run with --apply.")
        return 0
    client = config.wisdom_client(spec.wisdom.deployment)
    before = client.eval_analysis_status(domain_id) or {}
    if str(before.get("analysisStatus") or "").upper() == "RUNNING":
        res = {"status": "RUNNING", "message": "an analysis is already running"}
    else:
        res = client.trigger_eval_analysis(domain_id, include_schema_analysis=True, require_rq_eval=False)
    quick = client.trigger_domain_health_check(domain_id)
    after = client.eval_analysis_status(domain_id) or {}
    status = str(after.get("analysisStatus") or res.get("status") or "")
    ok = status.upper() in ("RUNNING", "QUEUED", "PENDING", "OK", "SUCCESS", "COMPLETED")
    state.set("wisdom", "health_job_run_id", quick.get("jobRunId"))
    state.set("wisdom", "health_analysis", {"status": status, "eval_run_id": res.get("evalRunId"), "run_group_id": res.get("runGroupId"), "job_run_id": res.get("jobRunId")})
    state.mark("health", "ok" if ok else "failed", analysis_status=status, trigger=res, quick_check_job=quick.get("jobRunId"))
    _emit(args, {"ok": ok, "analysis": after, "trigger": res, "quick_check": quick},
          f"Domain Health analysis {status} for the domain (the Recommendations tab fills when it completes; it can take a while); "
          f"quick health check job {quick.get('jobRunId')}. Left running — the SE demos the recommendations; nothing here acts on them.")
    return 0 if ok else 1


# ---------------------------------------------------------------- teardown
def cmd_teardown(args) -> int:
    """Delete everything this demo created in Wisdom (app, agent, eval set, domain).
    The shared connection and the Snowflake database are kept. IRREVERSIBLE."""
    from wisdomai import GraphQLError

    spec = _spec(args)
    state = State.load(spec.dir)
    w = dict(state.wisdom)
    shared = spec.wisdom.existing_domain or w.get("domain_owned") is False
    plan = [("Live App", w.get("app_id")), ("agent", w.get("agent_id")), ("eval set", w.get("eval_set_id"))]
    if not shared:
        plan.append(("domain", w.get("domain_id")))
    plan = [(k, v) for k, v in plan if v]
    kept_note = (f"\nThe domain {w.get('domain_id')} is EXISTING (shared) and is KEPT, as are our database, extractor files, accepted "
                 "suggestions and S3 dataset inside it (ids stay in .state.json for a manual undo)." if shared else "")
    if not plan:
        _emit(args, {"ok": True, "deleted": []}, "nothing recorded in .state.json to delete" + kept_note)
        return 0
    if not args.i_mean_it:
        _emit(args, {"ok": True, "dry_run": True, "would_delete": plan},
              "DRY RUN — would PERMANENTLY delete on " + spec.wisdom.deployment + ":\n" + "\n".join(f"  {k}: {v}" for k, v in plan) +
              "\nRe-run with --i-mean-it to delete. The Snowflake database and the shared connection are kept." + kept_note)
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
    # (on a shared domain also keep everything a manual undo would need)
    keep_keys = {"connection_id", "connection_created"} | ({"domain_id", "domain_owned", "suggestions_preexisting", "accepted_suggestion_ids",
                                                            "extraction_uploaded", "extraction_runs", "dataset_id", "s3_connection_id", "s3_dataset_id"}
                                                           if shared else set())
    keep = {k: v for k, v in state.wisdom.items() if k in keep_keys}
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

    spec = None
    deployment = args.deployment
    if getattr(args, "demo", None):
        spec = _spec(argparse.Namespace(name=args.demo))
        deployment = spec.wisdom.deployment
    checks = run_checks(deployment, network=not args.offline, spec=spec)
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
    d.add_argument("--demo", help="also check a demo's target (deployment, workspace and, for existing_domain demos, the domain)")

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
    r.add_argument("--domain", action="store_true", help="also run cross_db-tagged queries through the Wisdom SQL runner on the target domain")

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
    pb.add_argument("--only", nargs="*", help="run only these steps: connection domain database federated instructions knowledge metrics reviewed_queries lookup documents extraction skills s3_dataset")
    ev = add("eval", cmd_eval, "build the eval set from the reviewed queries, run it at least 3 times, report the mean score and flaky prompts")
    ev.add_argument("--timeout", type=int, default=1200)
    ev.add_argument("--report-last", action="store_true", help="report the last completed run instead of starting one")
    add("metrics-check", cmd_metrics_check, "compile every metrics.csv expression in DuckDB")
    ch = add("chat", cmd_chat, "ask the follow-up question in a visible conversation and judge the answer")
    ch.add_argument("--apply", action="store_true")
    ch.add_argument("--question", help="ask this ad-hoc question instead of chats[] (judged with the first entry's expected points)")
    ch.add_argument("--chat", help="only the chats[] entry with this key")
    ch.add_argument("--timeout", type=int, default=420)
    ap = add("app", cmd_app, "create the Live App from live_app_prompt.md (one prompt; takes minutes)")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--recreate", action="store_true")
    ap.add_argument("--app", help="only the live_apps[] entry with this key")
    ap.add_argument("--timeout", type=int, default=1500)
    ag = add("agent", cmd_agent, "create the agent from agent_prompt.md as a DRAFT (never runs)")
    ag.add_argument("--apply", action="store_true")
    ag.add_argument("--recreate", action="store_true")
    ag.add_argument("--agent", help="only the agents[] entry with this key")
    td = add("teardown", cmd_teardown, "PERMANENTLY delete the demo's Wisdom app, agent, eval set and domain (dry-run without --i-mean-it)")
    td.add_argument("--i-mean-it", action="store_true")
    s3p = add("s3", cmd_s3, "upload the generated contract PDFs (build/contracts) to the S3 bucket configured in .env (stretch: Wisdom reads them through an S3 connection)")
    s3p.add_argument("--apply", action="store_true", help="upload; without it, report what would be uploaded")
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
