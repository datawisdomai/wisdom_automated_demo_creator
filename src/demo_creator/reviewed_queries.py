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


@dataclass
class ReviewedQuery:
    nl: str
    sql: str
    tags: tuple[str, ...] = ()


@dataclass
class Registry:
    queries: list[ReviewedQuery] = field(default_factory=list)

    def add(self, nl: str, sql: str, tags: tuple[str, ...] | list[str] = ()) -> None:
        nl = " ".join(nl.split())
        if "," in nl:
            raise ValueError(f"reviewed query text must not contain commas (CSV import): {nl}")
        if any(q.nl == nl for q in self.queries):
            raise ValueError(f"duplicate reviewed query: {nl}")
        self.queries.append(ReviewedQuery(nl, sql.strip().rstrip(";"), tuple(tags)))

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


def check_queries(registry: Registry, q: Query, *, echo: bool = True) -> list[QueryResult]:
    results = []
    for rq in registry:
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


def pretty_sql(sql: str) -> str:
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
        for rq in registry:
            w.writerow([rq.nl, pretty_sql(rq.sql) + ";", connection_name, spec.snowflake.database, stamp])
    return out


def to_api_items(registry: Registry, dialect: str = "snowflake") -> list[dict]:
    return [{"query": rq.nl, "sql": pretty_sql(rq.sql), "dialect": dialect} for rq in registry]


def to_eval_items(registry: Registry) -> list[dict]:
    return [{"prompt": rq.nl, "sql": [pretty_sql(rq.sql)]} for rq in registry]
