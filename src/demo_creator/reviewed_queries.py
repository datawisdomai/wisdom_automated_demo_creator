"""Reviewed NL -> SQL pairs: the registry a demo's `reviewed_queries.py` fills,
execution against DuckDB/Snowflake, and the outputs Wisdom consumes.

From `halcyon_poc/files/build_reviewed_queries.py` + `arsenal/verify_queries.py`.
Rules carried over: NL text has no commas (Wisdom's CSV import), SQL is upper
case with double-quoted object names, pretty-printed by sqlglot (snowflake).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import sqlglot

from .spec import DemoSpec
from .validate import Query, load_demo_module


FEDERATED_TAG = "federated"


@dataclass
class ReviewedQuery:
    nl: str
    sql: str
    tags: tuple[str, ...] = ()
    source: str | None = None   # name of a `wisdom.federated_sources` connection the SQL runs on (None = the demo's warehouse)

    @property
    def federated(self) -> bool:
        return self.source is not None


@dataclass
class Registry:
    queries: list[ReviewedQuery] = field(default_factory=list)

    def add(self, nl: str, sql: str, tags: tuple[str, ...] | list[str] = (), *, source: str | None = None) -> None:
        """`source=<connection name>` marks SQL that runs on a federated (foreign, read-only) connection:
        it is skipped by the local DuckDB/Snowflake checks, left out of the extractor's query library
        and the eval set, and bound to that connection (with its dialect) when published."""
        nl = " ".join(nl.split())
        if "," in nl:
            raise ValueError(f"reviewed query text must not contain commas (CSV import): {nl}")
        if any(q.nl == nl for q in self.queries):
            raise ValueError(f"duplicate reviewed query: {nl}")
        tags = tuple(tags)
        if source and FEDERATED_TAG not in tags:
            tags = tags + (FEDERATED_TAG,)
        self.queries.append(ReviewedQuery(nl, sql.strip().rstrip(";"), tags, source))

    def local(self) -> "Registry":
        """The queries that run on the demo's own warehouse (no `source`)."""
        return Registry([q for q in self.queries if not q.federated])

    def for_source(self, source: str) -> "Registry":
        return Registry([q for q in self.queries if (q.source or "").strip().lower() == source.strip().lower()])

    def __len__(self) -> int:
        return len(self.queries)

    def __iter__(self):
        return iter(self.queries)


def load_registry(spec: DemoSpec) -> Registry:
    module = load_demo_module(spec.reviewed_queries_path, f"{spec.name}_reviewed_queries")
    for value in vars(module).values():
        if isinstance(value, Registry):
            return value
    raise ValueError(f"{spec.reviewed_queries_path.name} must create a Registry (rq = Registry(); rq.add(...))")


@dataclass
class QueryResult:
    nl: str
    status: str  # ok | empty | error
    rows: int = 0
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def check_queries(registry: Registry, q: Query, *, echo: bool = True, skip_tags: tuple[str, ...] = ()) -> list[QueryResult]:
    """Run every query through `q`. Queries carrying one of `skip_tags` (e.g. cross_db: joins to
    databases that only exist in the target domain) are reported as skipped, not failed."""
    results = []
    for rq in registry:
        if skip_tags and any(t in rq.tags for t in skip_tags):
            if echo:
                print(f"  [skip {','.join(t for t in rq.tags if t in skip_tags):>7s}] {rq.nl}")
            continue
        try:
            rows = q(rq.sql)
            r = QueryResult(rq.nl, "ok" if rows else "empty", len(rows))
        except Exception as exc:  # noqa: BLE001
            r = QueryResult(rq.nl, "error", 0, f"{type(exc).__name__}: {str(exc)[:300]}")
        results.append(r)
        if echo:
            tag = {"ok": f"ok {r.rows:>5} rows", "empty": "EMPTY        ", "error": "ERROR        "}[r.status]
            print(f"  [{tag}] {r.nl}")
            if r.error:
                print(f"           {r.error}")
    return results


def pretty_sql(sql: str, dialect: str = "snowflake") -> str:
    """Pretty-print Snowflake SQL with sqlglot. Any other dialect is passed through untouched:
    sqlglot rewrites literals (e.g. Teradata `DATE '2026-01-01'` -> `CAST(... AS DATE)`) and the
    authored, verified text must reach the domain verbatim."""
    if dialect != "snowflake":
        return sql
    try:
        return sqlglot.transpile(sql, read="snowflake", write="snowflake", pretty=True, identify=False)[0]
    except Exception:  # noqa: BLE001 — never block on a formatter
        return sql


def reviewer_stamp(reviewed_by: str, on: date) -> str:
    return f"{reviewed_by} at {on.month}/{on.day}/{on.year}, 12:00:00 PM"


def write_import_csv(registry: Registry, spec: DemoSpec, out: Path, *, connection_name: str) -> Path:
    """Wisdom's reviewed-query import format: Query, SQL, Connection, Database, Reviewed by."""
    out.parent.mkdir(parents=True, exist_ok=True)
    stamp = reviewer_stamp(spec.wisdom.reviewed_by or "Demo Creator", spec.as_of)
    with out.open("w", newline="") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_ALL)
        w.writerow(["Query", "SQL", "Connection", "Database", "Reviewed by"])
        for rq in registry.local():
            w.writerow([rq.nl, pretty_sql(rq.sql) + ";", connection_name, spec.snowflake.database, stamp])
    return out


def to_api_items(registry: Registry, dialect: str = "snowflake", *, connection_id: str | None = None) -> list[dict]:
    """`ReviewedQuerySqlItem`s for ONE connection: pass `registry.local()` with the warehouse dialect, or
    `registry.for_source(name)` with that source's dialect and connection id."""
    items = []
    for rq in registry:
        it = {"query": rq.nl, "sql": pretty_sql(rq.sql, dialect), "dialect": dialect}
        if connection_id:
            it["connectionId"] = connection_id
        items.append(it)
    return items


def to_eval_items(registry: Registry) -> list[dict]:
    """Eval prompts: only the demo's own warehouse queries. Federated SQL runs on another connection
    and dialect, which the eval runner cannot be told, so those prompts are left out."""
    return [{"prompt": rq.nl, "sql": [pretty_sql(rq.sql)]} for rq in registry.local()]
