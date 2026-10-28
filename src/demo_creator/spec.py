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
class FederatedSource:
    """Tables from ANOTHER connection (somebody else's warehouse, e.g. a partner's Teradata) attached
    read-only to the demo's domain for a federation beat. The pipeline never creates, updates or
    refreshes that connection; it only adds the listed tables to the domain's relationship graph and
    binds the reviewed queries that carry `source=<connection>` to it."""
    connection: str                       # connection name as shown in Wisdom (looked up, never created)
    database: str                         # database name as the connection exposes it
    tables: list[str]                     # table/view names to attach (case as the connection exposes them)
    dialect: str = "snowflake"            # SQL dialect for reviewed queries / runSqlQuery on this source
    schema: str | None = None             # schema filter; None = any (Teradata exposes '' as schema)
    description: str | None = None        # one paragraph for the domain instructions (what this source is)


@dataclass
class SkillSpec:
    """A domain skill: a markdown file with `name:` / `description:` frontmatter and an instruction
    body. Skills normally reach the domain through the context extractor (SKILL agent, UPSERT_SKILL
    suggestions) from an authored runbook; the publish step `skills` creates any skill listed here
    that the extractor did not produce, straight from this markdown, and reads every one back."""
    file: str                                   # path relative to the demo dir (skills/<name>.md)
    availability: list[str] = field(default_factory=lambda: ["CHAT", "COPILOT", "AGENTS"])

    @property
    def name(self) -> str:
        return Path(self.file).stem


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
    context_mode: str = "extractor"            # extractor (default: all context via the context extractor) | direct (legacy CSV/API path)
    extraction: dict[str, Any] = field(default_factory=dict)   # accept: [knowledge, synonyms, metrics, reviewed_queries]; coverage_threshold: 0.9
    # Existing-domain mode: ADD this demo's database and context to a domain somebody else built.
    # The domain is never created, renamed, deleted or (by default) re-instructed; see publish.py.
    existing_domain: bool = False
    domain_id: str | None = None
    instructions_mode: str = "replace"         # replace (own domain) | append (only our delimited block) | skip
    connection_create: bool = True             # create the Snowflake connection when it does not exist
    federated_sources: list[FederatedSource] = field(default_factory=list)   # read-only tables from other connections
    skills: list[SkillSpec] = field(default_factory=list)                    # domain skills (markdown files)


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
    live_apps: list[dict[str, Any]] = field(default_factory=list)   # every Live App (live_apps[] or [live_app])
    chats: list[dict[str, Any]] = field(default_factory=list)       # every answered chat (chats[] or [chat])
    agents: list[dict[str, Any]] = field(default_factory=list)      # every agent (agents[] or [agent])

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
    federated: list[FederatedSource] = []
    for f in w_raw.get("federated_sources") or []:
        if not isinstance(f, dict) or not f.get("connection") or not f.get("database"):
            raise SpecError(f"wisdom.federated_sources entries need connection and database: {f!r}")
        federated.append(FederatedSource(
            connection=str(f["connection"]), database=str(f["database"]),
            tables=[str(t) for t in f.get("tables") or []], dialect=str(f.get("dialect") or "snowflake"),
            schema=(None if f.get("schema") is None else str(f["schema"])), description=f.get("description"),
        ))
    skills: list[SkillSpec] = []
    for sk in w_raw.get("skills") or []:
        if isinstance(sk, str):
            sk = {"file": sk}
        if not isinstance(sk, dict) or not sk.get("file"):
            raise SpecError(f"wisdom.skills entries need a file: {sk!r}")
        skills.append(SkillSpec(file=str(sk["file"]), availability=[str(a).upper() for a in (sk.get("availability") or ["CHAT", "COPILOT", "AGENTS"])]))
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
        context_mode=str(w_raw.get("context_mode") or "extractor"),
        extraction=dict(w_raw.get("extraction") or {}),
        existing_domain=bool(w_raw.get("existing_domain", False)),
        domain_id=w_raw.get("domain_id"),
        instructions_mode=str(w_raw.get("instructions_mode") or ("skip" if w_raw.get("existing_domain") else "replace")),
        connection_create=bool(conn.get("create", True)) if isinstance(conn, dict) else True,
        federated_sources=federated,
        skills=skills,
    )

    def _many(plural: str, singular: str) -> list[dict[str, Any]]:
        """`live_apps[]` (etc.) when given, else the legacy single `live_app` mapping as a one-item list.
        Every entry gets a `key` (its own, else a slug of its name, else its index) used in .state.json."""
        items = raw.get(plural)
        if items is None:
            one = raw.get(singular)
            items = [one] if one else []
        out = []
        for i, it in enumerate(items):
            if not isinstance(it, dict):
                raise SpecError(f"{plural}[{i}] must be a mapping")
            it = dict(it)
            default = re.sub(r"[^a-z0-9]+", "_", str(it.get("name") or "").lower()).strip("_")[:40]
            it.setdefault("key", default or ("followup" if (singular == "chat" and i == 0) else f"{singular}{i + 1}"))
            out.append(it)
        keys = [it["key"] for it in out]
        if len(keys) != len(set(keys)):
            raise SpecError(f"{plural}[] keys must be unique: {keys}")
        return out

    live_apps, chats, agents = _many("live_apps", "live_app"), _many("chats", "chat"), _many("agents", "agent")
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
        live_app=dict(live_apps[0] if live_apps else {}),
        chat=dict(chats[0] if chats else {}),
        agent=dict(agents[0] if agents else {}),
        wisdom=wisdom,
        script=dict(raw.get("script") or {}),
        manual_steps=list(raw.get("manual_steps") or []),
        raw=raw,
        live_apps=live_apps, chats=chats, agents=agents,
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
    if spec.wisdom.context_mode not in ("extractor", "direct"):
        problems.append("wisdom.context_mode must be 'extractor' (default) or 'direct'")
    if spec.wisdom.instructions_mode not in ("replace", "append", "skip"):
        problems.append("wisdom.instructions_mode must be replace, append or skip")
    if spec.wisdom.existing_domain:
        if not str(spec.wisdom.domain_id or "").startswith("ET_DOMAIN_"):
            problems.append("wisdom.existing_domain needs wisdom.domain_id (ET_DOMAIN_...) of the domain to extend")
        if not spec.wisdom.workspace_id:
            problems.append("wisdom.existing_domain needs an explicit wisdom.workspace_id")
        if spec.wisdom.instructions_mode == "replace":
            problems.append("wisdom.instructions_mode=replace would overwrite the shared domain's instructions; use append or skip")
    for f in spec.wisdom.federated_sources:
        if not f.tables:
            problems.append(f"wisdom.federated_sources[{f.connection}] lists no tables")
        if f.connection.strip().lower() == (spec.wisdom.connection_name or "").strip().lower():
            problems.append(f"wisdom.federated_sources[{f.connection}] is the demo's own connection — federated sources are OTHER connections")
    try:
        if int(spec.wisdom.eval.get("run_count") or 3) < 3:
            problems.append("wisdom.eval.run_count must be at least 3 (every eval set runs a minimum of 3 times)")
    except (TypeError, ValueError):
        problems.append("wisdom.eval.run_count must be an integer >= 3")

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
    for sk in spec.wisdom.skills:
        p = spec.dir / sk.file
        if not p.is_file():
            problems.append(f"skill file missing: {sk.file}")
        else:
            fm = skill_frontmatter(p.read_text())
            if not fm.get("name") or not fm.get("description"):
                problems.append(f"skill {sk.file} needs 'name:' and 'description:' frontmatter")
            elif fm["name"] != sk.name:
                problems.append(f"skill {sk.file}: frontmatter name '{fm['name']}' must equal the file stem '{sk.name}'")
            elif not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", fm["name"]):
                problems.append(f"skill {sk.file}: name must be lowercase and hyphenated")
        bad = [a for a in sk.availability if a not in ("CHAT", "COPILOT", "AGENTS")]
        if bad:
            problems.append(f"skill {sk.file}: availability must be CHAT, COPILOT or AGENTS (got {bad})")
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
    for label, entries in (("live_apps", spec.live_apps), ("agents", spec.agents)):
        for it in entries:
            prompt = it.get("prompt")
            if prompt and not (spec.dir / prompt).is_file():
                problems.append(f"{label}[{it.get('key')}] prompt missing: {prompt}")
    return problems


def skill_frontmatter(markdown: str) -> dict[str, str]:
    """`name:` and `description:` from a skill file's YAML frontmatter (quotes stripped)."""
    m = re.match(r"\s*---\n(.*?)\n---", markdown, re.S)
    if not m:
        return {}
    out: dict[str, str] = {}
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}
    for k in ("name", "description"):
        if data.get(k) is not None:
            out[k] = str(data[k]).strip()
    return out
