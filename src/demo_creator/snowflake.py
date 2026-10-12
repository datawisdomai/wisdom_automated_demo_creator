"""Snowflake access shared by every demo: connection, statement-by-statement DDL
runner with structured errors (so Claude can repair the failing statement),
`write_pandas` loader with the known coercions, count verification, grants, and
a DDL-vs-DataFrame schema diff that runs before any data is loaded.

Extracted from `wisdom demos/halcyon_poc/files/{sf_connect,run_ddl}.py` and
`arsenal/pipeline/load.py` (`_prep`).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

from .config import SnowflakeConfig


# ---------------------------------------------------------------- connection
def connect(sf: SnowflakeConfig, *, role: str | None = None, database: str | None = None,
            schema: str | None = None, warehouse: str | None = None):
    """Open a connection with the person's PAT. Never logs the token."""
    if not sf.has_credentials:
        raise RuntimeError("SNOWFLAKE_USER / SNOWFLAKE_PAT are not set in .env")
    return snowflake.connector.connect(
        account=sf.account,
        user=sf.user,
        password=sf.pat,  # PATs are accepted in the password slot by the connector
        role=role or sf.ddl_role,
        warehouse=warehouse or sf.warehouse,
        database=database,
        schema=schema,
        client_session_keep_alive=False,
    )


def run_query(conn, sql: str) -> list[tuple]:
    cur = conn.cursor()
    try:
        cur.execute(sql)
        return cur.fetchall()
    finally:
        cur.close()


# ---------------------------------------------------------------- statements
def split_statements(sql: str) -> list[str]:
    """Split a SQL script on `;` outside quotes/comments. Block comments are
    dropped; line comments are kept with their statement (Snowflake accepts them)."""
    stmts: list[str] = []
    buf: list[str] = []
    i, n = 0, len(sql)
    quote: str | None = None
    while i < n:
        ch = sql[i]
        if quote:
            buf.append(ch)
            if ch == quote:
                if i + 1 < n and sql[i + 1] == quote:  # doubled quote escape
                    buf.append(sql[i + 1])
                    i += 2
                    continue
                quote = None
            i += 1
            continue
        if sql.startswith("--", i):
            j = sql.find("\n", i)
            j = n if j < 0 else j
            buf.append(sql[i:j])
            i = j
            continue
        if sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if ch == ";":
            s = "".join(buf).strip()
            if _has_code(s):
                stmts.append(s)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if _has_code(tail):
        stmts.append(tail)
    return stmts


def _has_code(stmt: str) -> bool:
    return any(line.strip() and not line.strip().startswith("--") for line in stmt.splitlines())


def strip_leading_comments(stmt: str) -> str:
    """Drop the `--` comment lines that precede a statement's first code line."""
    lines = stmt.splitlines()
    while lines and (not lines[0].strip() or lines[0].strip().startswith("--")):
        lines.pop(0)
    return "\n".join(lines)


_SESSION_STMT = re.compile(r"^\s*(USE\s+(ROLE|DATABASE|SCHEMA|WAREHOUSE)\b|ALTER\s+SESSION\b)", re.I)


def is_session_statement(stmt: str) -> bool:
    return bool(_SESSION_STMT.match(strip_leading_comments(stmt)))


def statement_preview(stmt: str, width: int = 90) -> str:
    for line in stmt.splitlines():
        s = line.strip()
        if s and not s.startswith("--"):
            return s[:width]
    return stmt[:width]


class StatementError(RuntimeError):
    """One statement failed. Carries everything needed to repair and resume."""

    def __init__(self, index: int, statement: str, message: str, errno: int | None = None, sqlstate: str | None = None):
        super().__init__(message)
        self.index = index
        self.statement = statement
        self.message = message
        self.errno = errno
        self.sqlstate = sqlstate

    def as_dict(self) -> dict:
        return {"index": self.index, "statement": self.statement, "error": self.message,
                "errno": self.errno, "sqlstate": self.sqlstate, "preview": statement_preview(self.statement)}


@dataclass
class RunResult:
    executed: list[int] = field(default_factory=list)
    total: int = 0
    failure: StatementError | None = None

    @property
    def ok(self) -> bool:
        return self.failure is None


def run_statements(conn, statements: list[str], *, start_at: int = 0,
                   on_progress: Callable[[int, str], None] | None = None) -> RunResult:
    """Execute statements in order from `start_at`; stop at the first failure and
    return it as structured data (nothing is raised)."""
    result = RunResult(total=len(statements))
    cur = conn.cursor()
    try:
        # A resume runs in a fresh session: replay the session-context statements
        # (USE ROLE/DATABASE/SCHEMA/WAREHOUSE, ALTER SESSION) that precede start_at.
        for idx in range(0, min(start_at, len(statements))):
            if is_session_statement(statements[idx]):
                try:
                    cur.execute(statements[idx])
                except snowflake.connector.errors.Error as exc:  # type: ignore[attr-defined]
                    result.failure = StatementError(idx, statements[idx], str(exc.msg or exc), getattr(exc, "errno", None), getattr(exc, "sqlstate", None))
                    return result
        for idx in range(start_at, len(statements)):
            stmt = statements[idx]
            try:
                cur.execute(stmt)
            except snowflake.connector.errors.Error as exc:  # type: ignore[attr-defined]
                result.failure = StatementError(idx, stmt, str(exc.msg or exc), getattr(exc, "errno", None), getattr(exc, "sqlstate", None))
                return result
            result.executed.append(idx)
            if on_progress:
                on_progress(idx, statement_preview(stmt))
    finally:
        cur.close()
    return result


def run_sql_file(conn, path: Path, **kw) -> RunResult:
    return run_statements(conn, split_statements(Path(path).read_text()), **kw)


# ---------------------------------------------------------------- loading
def coerce_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Make a DataFrame safe for write_pandas against a pre-created table:
    upper-case column names, date-like object columns -> datetime64[ns]
    (parquet round-trips python dates as objects), and drop all-null columns
    (they would be written as parquet NULL type and fail the COPY type check).
    Returns (frame, dropped_columns)."""
    df = df.copy()
    df.columns = [str(c).upper() for c in df.columns]
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_datetime64_any_dtype(s):
            df[col] = pd.to_datetime(s).astype("datetime64[ns]")
        elif s.dtype == "object":
            sample = s.dropna().head(20)
            if len(sample) and all(hasattr(v, "year") for v in sample):
                df[col] = pd.to_datetime(s, errors="coerce").astype("datetime64[ns]")
    dropped = [c for c in df.columns if df[c].isna().all()]
    if dropped:
        df = df.drop(columns=dropped)
    return df, dropped


def load_frame(conn, df: pd.DataFrame, table: str, database: str, schema: str) -> tuple[bool, int, list[str]]:
    """Overwrite `table` with `df`. Returns (success, rows, dropped_all_null_columns)."""
    frame, dropped = coerce_frame(df)
    if frame.empty:
        run_query(conn, f'TRUNCATE TABLE "{database}"."{schema}"."{table}"')
        return True, 0, dropped
    success, _chunks, nrows, _ = write_pandas(
        conn, frame, table, database=database, schema=schema,
        auto_create_table=False, overwrite=True, use_logical_type=True,
    )
    return bool(success), int(nrows), dropped


def count_rows(conn, database: str, schema: str, table: str) -> int:
    return int(run_query(conn, f'SELECT COUNT(*) FROM "{database}"."{schema}"."{table}"')[0][0])


def verify_counts(conn, database: str, schema: str, tables: Iterable[str],
                  expected: dict[str, int] | None = None) -> dict[str, dict]:
    """{table: {count, expected, ok}} for every table."""
    out = {}
    expected = expected or {}
    for t in tables:
        n = count_rows(conn, database, schema, t)
        exp = expected.get(t)
        out[t] = {"count": n, "expected": exp, "ok": (exp is None and n >= 0) or n == exp}
    return out


# ---------------------------------------------------------------- grants
def render_grants(database: str, schema: str, warehouse: str, role: str = "WISDOMAI_READ_ONLY",
                  *, create_role: bool = False) -> str:
    """Read-only grants for the Wisdom connection role. The database owner
    (SYSADMIN) can grant these; `create_role` adds CREATE ROLE, which needs
    SECURITYADMIN — the role already exists on the shared SE account.
    Mirrors halcyon_poc/01b_wisdomai_grants.sql."""
    head = f"-- Grants for the WisdomAI connection role on {database}.{schema}\n"
    if create_role:
        head += f"CREATE ROLE IF NOT EXISTS {role};\n"
    return head + f"""GRANT USAGE ON WAREHOUSE {warehouse} TO ROLE {role};
GRANT USAGE ON DATABASE {database} TO ROLE {role};
GRANT USAGE ON SCHEMA {database}.{schema} TO ROLE {role};
GRANT SELECT ON ALL TABLES IN SCHEMA {database}.{schema} TO ROLE {role};
GRANT SELECT ON ALL VIEWS IN SCHEMA {database}.{schema} TO ROLE {role};
GRANT SELECT ON FUTURE TABLES IN SCHEMA {database}.{schema} TO ROLE {role};
GRANT SELECT ON FUTURE VIEWS IN SCHEMA {database}.{schema} TO ROLE {role};
"""


# ---------------------------------------------------------------- DDL parsing
_CREATE_TABLE = re.compile(r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:TRANSIENT\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w.]+)\s*\(", re.I)
_CONSTRAINT_PREFIX = ("CONSTRAINT", "PRIMARY", "FOREIGN", "UNIQUE", "CHECK")
_REFERENCES = re.compile(r"REFERENCES\s+([\w.]+)\s*\(\s*(\w+)\s*\)", re.I)
_FK_TABLE_LEVEL = re.compile(r"FOREIGN\s+KEY\s*\(\s*(\w+)\s*\)\s*REFERENCES\s+([\w.]+)\s*\(\s*(\w+)\s*\)", re.I)


def _balanced_body(text: str, open_idx: int) -> str:
    depth, i = 0, open_idx
    quote = None
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[open_idx + 1:i]
        i += 1
    return text[open_idx + 1:]


def _split_top_level(body: str) -> list[str]:
    parts, buf, depth, quote = [], [], 0, None
    for ch in body:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    if "".join(buf).strip():
        parts.append("".join(buf))
    return parts


def _strip_line_comments(text: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in text.splitlines())


@dataclass
class TableDef:
    name: str
    columns: list[str]
    foreign_keys: list[tuple[str, str, str]]  # (column, ref_table, ref_column)


def parse_ddl_tables(ddl_sql: str) -> dict[str, TableDef]:
    """Column lists and FK declarations per table, from the DDL text."""
    out: dict[str, TableDef] = {}
    clean = _strip_line_comments(ddl_sql)
    for m in _CREATE_TABLE.finditer(clean):
        name = m.group(1).split(".")[-1].upper()
        body = _balanced_body(clean, m.end() - 1)
        cols: list[str] = []
        fks: list[tuple[str, str, str]] = []
        for part in _split_top_level(body):
            p = part.strip()
            if not p:
                continue
            first = p.split()[0].strip('"').upper()
            if first in _CONSTRAINT_PREFIX:
                for fm in _FK_TABLE_LEVEL.finditer(p):
                    fks.append((fm.group(1).upper(), fm.group(2).split(".")[-1].upper(), fm.group(3).upper()))
                continue
            cols.append(first)
            rm = _REFERENCES.search(p)
            if rm:
                fks.append((first, rm.group(1).split(".")[-1].upper(), rm.group(2).upper()))
        out[name] = TableDef(name, cols, fks)
    return out


def schema_diff(ddl_sql: str, frames: dict[str, pd.DataFrame]) -> list[dict]:
    """Compare DDL tables with generated frames before loading.
    Each finding: {level: error|warn, table, message}."""
    findings: list[dict] = []
    tables = parse_ddl_tables(ddl_sql)
    for name, df in frames.items():
        t = name.upper()
        if t not in tables:
            findings.append({"level": "error", "table": t, "message": "frame has no CREATE TABLE in the DDL"})
            continue
        ddl_cols = tables[t].columns
        frame_cols = [str(c).upper() for c in df.columns]
        extra = [c for c in frame_cols if c not in ddl_cols]
        missing = [c for c in ddl_cols if c not in frame_cols]
        if extra:
            findings.append({"level": "error", "table": t, "message": f"columns in generated data but not in DDL (COPY would fail): {', '.join(extra)}"})
        if missing:
            findings.append({"level": "warn", "table": t, "message": f"DDL columns absent from generated data (will load as NULL): {', '.join(missing)}"})
    for t in tables:
        if t not in {n.upper() for n in frames}:
            findings.append({"level": "warn", "table": t, "message": "table in DDL has no generated frame"})
    return findings
