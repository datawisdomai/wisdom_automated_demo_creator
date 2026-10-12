"""`demo.yaml` — the contract between the Claude-authored artifacts and the pipeline.

See docs/demo_spec_reference.md for every field. Loading is tolerant (unknown keys
are kept in `raw`); `validate_spec` reports problems without raising so the CLI can
print all of them at once.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from .config import DEMOS_DIR
from .paths import DemoPaths


class SpecError(ValueError):
    pass


def _date(v: Any, what: str) -> date:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        return datetime.strptime(v, "%Y-%m-%d").date()
    raise SpecError(f"{what} must be a YYYY-MM-DD date, got {v!r}")


@dataclass
class SnowflakeSpec:
    database: str
    schema: str
    ddl: str = "01_snowflake_ddl.sql"
    load_order: list[str] = field(default_factory=list)
    views: list[str] = field(default_factory=list)
    expected_rows: dict[str, int] = field(default_factory=dict)
    warehouse: str | None = None


@dataclass
class ControlPoint:
    id: str
    name: str
    targets: list[dict[str, Any]] = field(default_factory=list)
    hero: str | None = None
    description: str | None = None


@dataclass
class WisdomSpec:
    deployment: str = "proddemo"
    workspace_id: str | None = None
    connection_name: str | None = None
    domain_name: str = ""
    domain_description: str | None = None
    dialect: str = "snowflake"
    bootstrap: str = "02_wace_bootstrap.md"
    knowledge_csv: str = "knowledge.csv"
    metrics_csv: str = "metrics.csv"
    reviewed_by: str = ""
    lookup_columns: list[str] = field(default_factory=list)
    eval: dict[str, Any] = field(default_factory=dict)


@dataclass
class DemoSpec:
    name: str
    title: str
    dir: Path
    vertical: str | None
    as_of: date
    data_start: date
    seed: int
    persona: dict[str, Any]
    inputs: list[str]
    snowflake: SnowflakeSpec
    generator: dict[str, Any]
    control_points: list[ControlPoint]
    questions: dict[str, Any]
    documents: list[dict[str, Any]]
    live_app: dict[str, Any]
    chat: dict[str, Any]
    agent: dict[str, Any]
    wisdom: WisdomSpec
    script: dict[str, Any]
    manual_steps: list[dict[str, Any]]
    raw: dict[str, Any]

    # ---- derived paths ----
    @property
    def paths(self) -> DemoPaths:
        return DemoPaths(self.dir)

    def file(self, rel: str | None) -> Path | None:
        return (self.dir / rel) if rel else None

    @property
    def ddl_path(self) -> Path:
        return self.dir / self.snowflake.ddl

    @property
    def generator_path(self) -> Path:
        return self.dir / self.generator.get("module", "generator.py")

    @property
    def checks_path(self) -> Path:
        return self.dir / self.generator.get("checks", "checks.py")

    @property
    def reviewed_queries_path(self) -> Path:
        return self.dir / self.questions.get("reviewed_queries", "reviewed_queries.py")

    @property
    def bootstrap_path(self) -> Path:
        return self.dir / self.wisdom.bootstrap

    @property
    def knowledge_path(self) -> Path:
        return self.dir / self.wisdom.knowledge_csv

    @property
    def metrics_path(self) -> Path:
        return self.dir / self.wisdom.metrics_csv

    @property
    def constants(self) -> dict[str, Any]:
        return dict(self.generator.get("constants") or {})

    @property
    def tables(self) -> list[str]:
        return list(self.snowflake.load_order)

    @property
    def qualified_schema(self) -> str:
        return f"{self.snowflake.database}.{self.snowflake.schema}"


def resolve_demo_dir(name_or_path: str | Path) -> Path:
    p = Path(name_or_path)
    if p.is_dir() and (p / "demo.yaml").is_file():
        return p.resolve()
    cand = DEMOS_DIR / str(name_or_path)
    if (cand / "demo.yaml").is_file():
        return cand.resolve()
    raise SpecError(f"No demo.yaml found for '{name_or_path}' (looked in {p} and {cand})")


def load_spec(name_or_path: str | Path) -> DemoSpec:
    demo_dir = resolve_demo_dir(name_or_path)
    raw = yaml.safe_load((demo_dir / "demo.yaml").read_text()) or {}
    if not isinstance(raw, dict):
        raise SpecError("demo.yaml must be a mapping")

    sf_raw = raw.get("snowflake") or {}
    if "database" not in sf_raw or "schema" not in sf_raw:
        raise SpecError("snowflake.database and snowflake.schema are required")
    snowflake = SnowflakeSpec(
        database=str(sf_raw["database"]).upper(),
        schema=str(sf_raw["schema"]).upper(),
        ddl=sf_raw.get("ddl", "01_snowflake_ddl.sql"),
        load_order=[str(t).upper() for t in sf_raw.get("load_order") or []],
        views=[str(v).upper() for v in sf_raw.get("views") or []],
        expected_rows={str(k).upper(): int(v) for k, v in (sf_raw.get("expected_rows") or {}).items()},
        warehouse=sf_raw.get("warehouse"),
    )

    cps = []
    for cp in raw.get("control_points") or []:
        if not isinstance(cp, dict) or "id" not in cp:
            raise SpecError(f"control point without id: {cp!r}")
        cps.append(ControlPoint(
            id=str(cp["id"]), name=str(cp.get("name", cp["id"])),
            targets=list(cp.get("targets") or []), hero=cp.get("hero"), description=cp.get("description"),
        ))

    w_raw = raw.get("wisdom") or {}
    conn = w_raw.get("connection") or {}
    wisdom = WisdomSpec(
        deployment=w_raw.get("deployment", "proddemo"),
        workspace_id=w_raw.get("workspace_id"),
        connection_name=conn.get("name") if isinstance(conn, dict) else conn,
        domain_name=w_raw.get("domain_name") or raw.get("title") or raw.get("name", ""),
        domain_description=w_raw.get("domain_description"),
        dialect=w_raw.get("dialect", "snowflake"),
        bootstrap=w_raw.get("bootstrap", "02_wace_bootstrap.md"),
        knowledge_csv=w_raw.get("knowledge_csv", "knowledge.csv"),
        metrics_csv=w_raw.get("metrics_csv", "metrics.csv"),
        reviewed_by=w_raw.get("reviewed_by", ""),
        lookup_columns=list(w_raw.get("lookup_columns") or []),
        eval=dict(w_raw.get("eval") or {}),
    )

    return DemoSpec(
        name=str(raw.get("name") or demo_dir.name),
        title=str(raw.get("title") or raw.get("name") or demo_dir.name),
        dir=demo_dir,
        vertical=raw.get("vertical"),
        as_of=_date(raw.get("as_of"), "as_of"),
        data_start=_date(raw.get("data_start"), "data_start"),
        seed=int(raw.get("seed", 0)),
        persona=dict(raw.get("persona") or {}),
        inputs=list(raw.get("inputs") or []),
        snowflake=snowflake,
        generator=dict(raw.get("generator") or {}),
        control_points=cps,
        questions=dict(raw.get("questions") or {}),
        documents=list(raw.get("documents") or []),
        live_app=dict(raw.get("live_app") or {}),
        chat=dict(raw.get("chat") or {}),
        agent=dict(raw.get("agent") or {}),
        wisdom=wisdom,
        script=dict(raw.get("script") or {}),
        manual_steps=list(raw.get("manual_steps") or []),
        raw=raw,
    )


_TABLE_RE = re.compile(r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:TRANSIENT\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w.]+)", re.I)
_VIEW_RE = re.compile(r"CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w.]+)", re.I)


def ddl_object_names(ddl_sql: str) -> tuple[list[str], list[str]]:
    """(tables, views) declared in a DDL script, unqualified and upper-cased."""
    tables = [m.group(1).split(".")[-1].upper() for m in _TABLE_RE.finditer(ddl_sql)]
    views = [m.group(1).split(".")[-1].upper() for m in _VIEW_RE.finditer(ddl_sql)]
    return tables, views


def validate_spec(spec: DemoSpec, *, stage: str = "all") -> list[str]:
    """Problems with the spec and the files it points at. Empty list = fine.

    `stage` narrows the checks: "design" (spec + DDL), "data" (+ generator/checks),
    "context" (+ bootstrap/CSVs/reviewed queries), "all".
    """
    problems: list[str] = []
    if spec.as_of < spec.data_start:
        problems.append(f"as_of {spec.as_of} is before data_start {spec.data_start}")
    if not spec.seed:
        problems.append("seed must be a non-zero integer")

    if not spec.ddl_path.is_file():
        problems.append(f"DDL file missing: {spec.ddl_path.name}")
    else:
        tables, views = ddl_object_names(spec.ddl_path.read_text())
        missing = [t for t in tables if t not in spec.snowflake.load_order]
        extra = [t for t in spec.snowflake.load_order if t not in tables]
        if missing:
            problems.append(f"tables in DDL but not in snowflake.load_order: {', '.join(missing)}")
        if extra:
            problems.append(f"tables in snowflake.load_order but not in DDL: {', '.join(extra)}")
        vmissing = [v for v in views if v not in spec.snowflake.views]
        if vmissing:
            problems.append(f"views in DDL but not in snowflake.views: {', '.join(vmissing)}")
    if stage == "design":
        return problems

    if not spec.generator_path.is_file():
        problems.append(f"generator missing: {spec.generator_path.name}")
    if not spec.checks_path.is_file():
        problems.append(f"checks module missing: {spec.checks_path.name}")
    else:
        text = spec.checks_path.read_text()
        for cp in spec.control_points:
            if cp.id not in text:
                problems.append(f"control point {cp.id} is not referenced in {spec.checks_path.name}")
    if stage == "data":
        return problems

    for label, p in (("bootstrap", spec.bootstrap_path), ("knowledge csv", spec.knowledge_path),
                     ("metrics csv", spec.metrics_path), ("reviewed queries", spec.reviewed_queries_path)):
        if not p.is_file():
            problems.append(f"{label} missing: {p.name}")
    for d in spec.documents:
        p = spec.file(d.get("spec"))
        if p is None or not p.is_file():
            problems.append(f"document spec missing: {d.get('spec')}")
    for key in ("live_app", "agent"):
        prompt = getattr(spec, key).get("prompt")
        if prompt and not (spec.dir / prompt).is_file():
            problems.append(f"{key} prompt missing: {prompt}")
    return problems
