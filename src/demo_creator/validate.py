"""Validate generated data offline in DuckDB (and again in Snowflake after load).

From `wisdom demos/halcyon_poc/files/validate_duckdb.py`. Built-in checks cover
what every demo needs (tables non-empty, expected row counts, views compile,
FK orphans from the DDL's REFERENCES); the demo's own `checks.py` asserts its
story control points through `run(q, check, spec)`.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import duckdb

from .snowflake import parse_ddl_tables, split_statements, strip_leading_comments
from .spec import DemoSpec

Query = Callable[[str], list[tuple]]

_VIEW_HEAD = re.compile(r"\s*CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w.]+)", re.I)
_COMMENT_CLAUSE = re.compile(r"\bCOMMENT\s*=?\s*'(?:[^']|'')*'", re.I)


def view_statements(ddl_sql: str) -> list[tuple[str, str]]:
    """(view_name, CREATE VIEW statement without COMMENT clauses, unqualified name)."""
    out = []
    for raw in split_statements(ddl_sql):
        stmt = strip_leading_comments(raw)
        m = _VIEW_HEAD.match(stmt)
        if not m:
            continue
        qualified = m.group(1)
        name = qualified.split(".")[-1].upper()
        body = _COMMENT_CLAUSE.sub("", stmt)
        if "." in qualified:
            body = body.replace(qualified, name, 1)
        out.append((name, body))
    return out


@dataclass
class CheckResult:
    label: str
    ok: bool
    detail: str = ""
    section: str = ""


@dataclass
class Checker:
    results: list[CheckResult] = field(default_factory=list)
    section: str = ""
    echo: bool = True

    def check(self, label: str, cond, detail: str = "") -> bool:
        ok = bool(cond)
        self.results.append(CheckResult(label, ok, str(detail), self.section))
        if self.echo:
            print(f"  [{'PASS' if ok else 'FAIL'}] {label} {detail}")
        return ok

    def begin(self, section: str) -> None:
        self.section = section
        if self.echo:
            print(f"\n== {section} ==")

    @property
    def failures(self) -> list[CheckResult]:
        return [r for r in self.results if not r.ok]

    @property
    def ok(self) -> bool:
        return not self.failures

    def as_dict(self) -> dict:
        return {"ok": self.ok, "passed": len(self.results) - len(self.failures), "failed": len(self.failures),
                "failures": [r.__dict__ for r in self.failures]}


# ---------------------------------------------------------------- DuckDB
def build_duckdb(spec: DemoSpec, *, path: Path | None = None) -> duckdb.DuckDBPyConnection:
    """Fresh DuckDB with every cached table and the DDL's views."""
    paths = spec.paths
    db = path or paths.duckdb
    if db.exists():
        db.unlink()
    con = duckdb.connect(str(db))
    for name in spec.tables:
        p = paths.parquet(name)
        if not p.is_file():
            raise FileNotFoundError(f"{p} missing — run `demo generate {spec.name}` first")
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_parquet('{p}')")
    for name, stmt in view_statements(spec.ddl_path.read_text()):
        con.execute(stmt)
    return con


def duckdb_query(con) -> Query:
    return lambda sql: con.execute(sql).fetchall()


def snowflake_query(conn) -> Query:
    def q(sql: str) -> list[tuple]:
        cur = conn.cursor()
        try:
            cur.execute(sql)
            return cur.fetchall()
        finally:
            cur.close()
    return q


# ---------------------------------------------------------------- checks
def builtin_checks(spec: DemoSpec, q: Query, checker: Checker) -> None:
    ddl = spec.ddl_path.read_text()
    checker.begin("Row counts")
    for name in spec.tables:
        n = q(f"SELECT COUNT(*) FROM {name}")[0][0]
        exp = spec.snowflake.expected_rows.get(name)
        if exp is not None:
            checker.check(f"{name} has {exp:,} rows", n == exp, f"({n:,})")
        else:
            checker.check(f"{name} is not empty", n > 0, f"({n:,})")

    checker.begin("Views compile")
    for name, _ in view_statements(ddl):
        try:
            n = q(f"SELECT COUNT(*) FROM {name}")[0][0]
            checker.check(f"{name} returns rows", n > 0, f"({n:,})")
        except Exception as exc:  # noqa: BLE001
            checker.check(f"{name} compiles", False, f"({type(exc).__name__}: {str(exc)[:160]})")

    fks = [(t.name, c, rt, rc) for t in parse_ddl_tables(ddl).values() for (c, rt, rc) in t.foreign_keys]
    if fks:
        checker.begin("Referential integrity (from DDL REFERENCES)")
        for table, col, rt, rc in fks:
            n = q(f"SELECT COUNT(*) FROM {table} c LEFT JOIN {rt} p ON p.{rc} = c.{col} "
                  f"WHERE c.{col} IS NOT NULL AND p.{rc} IS NULL")[0][0]
            checker.check(f"{table}.{col} -> {rt}.{rc} orphans = 0", n == 0, f"({n})")


def load_demo_module(path: Path, name: str):
    """Import a module from the demo folder with that folder on sys.path, so
    sibling imports (`import generator`) work."""
    demo_dir = str(path.parent)
    if demo_dir not in sys.path:
        sys.path.insert(0, demo_dir)
    mod_spec = importlib.util.spec_from_file_location(name, path)
    if mod_spec is None or mod_spec.loader is None:
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(mod_spec)
    sys.modules[name] = module
    mod_spec.loader.exec_module(module)
    return module


def demo_checks(spec: DemoSpec, q: Query, checker: Checker) -> None:
    """Run `checks.py::run(q, check, spec)` from the demo folder."""
    module = load_demo_module(spec.checks_path, f"{spec.name}_checks")
    run = getattr(module, "run", None)
    if run is None:
        checker.check(f"{spec.checks_path.name} defines run(q, check, spec)", False)
        return
    run(q, checker.check, spec)


def run_all_checks(spec: DemoSpec, q: Query, *, echo: bool = True) -> Checker:
    checker = Checker(echo=echo)
    builtin_checks(spec, q, checker)
    demo_checks(spec, q, checker)
    return checker
