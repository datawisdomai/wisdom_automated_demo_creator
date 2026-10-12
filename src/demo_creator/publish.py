"""Publish a demo into Wisdom: connection → domain → database → knowledge →
metrics → reviewed queries → lookup columns → instructions → documents.

Every step is idempotent (reads back what exists first) and records ids in
`.state.json`. Without `apply=True` the publisher only reads and prints the plan.
Built on `wisdomai.Client`; patterns from examples/wisdomai/create_domain_with_context.py.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

from wisdomai import Client, GraphQLError

from . import config
from .context_files import bootstrap_sections, bootstrap_to_knowledge, read_knowledge_csv, read_metrics_csv
from .manifest import State
from .reviewed_queries import Registry, to_api_items
from .spec import DemoSpec


class PublishError(RuntimeError):
    pass


@dataclass
class StepReport:
    step: str
    status: str            # ok | skipped | planned | failed
    detail: str = ""
    data: dict = field(default_factory=dict)


class Publisher:
    def __init__(self, spec: DemoSpec, state: State, client: Client, *, apply: bool = False, echo: bool = True):
        self.spec, self.state, self.client, self.apply, self.echo = spec, state, client, apply, echo
        self.dep = config.wisdom_deployment(spec.wisdom.deployment)
        self.sf = config.snowflake_config()
        self.workspace_id = spec.wisdom.workspace_id or self.dep.workspace_id
        if not self.workspace_id:
            raise PublishError("no workspace_id in demo.yaml or config/deployments.toml")
        self.reports: list[StepReport] = []

    # ---- plumbing ----
    def _say(self, msg: str) -> None:
        if self.echo:
            print(msg)

    def _report(self, step: str, status: str, detail: str = "", **data) -> StepReport:
        r = StepReport(step, status, detail, data)
        self.reports.append(r)
        self._say(f"  [{status:7s}] {step}: {detail}")
        if status in ("ok", "failed"):
            self.state.mark(f"publish.{step}", status, **{k: v for k, v in data.items() if not isinstance(v, (list, dict)) or len(str(v)) < 2000})
        return r

    def _announce(self, op: str, effect: str) -> None:
        self._say(f"  -> {op}: {effect}  [{self.dep.name} / {self.dep.workspace_name or self.workspace_id}]")

    @property
    def domain_id(self) -> str | None:
        return self.state.wisdom.get("domain_id")

    # ---- 1. connection ----
    def ensure_connection(self) -> StepReport:
        name = self.spec.wisdom.connection_name or self.sf.connection_name
        try:
            conn = self.client.find_connection(self.workspace_id, name)
        except GraphQLError as exc:
            if "permission" in str(exc).lower():
                raise PublishError(f"the API key's user cannot read workspace {self.workspace_id} "
                                   f"({self.dep.workspace_name}); ask a Wisdom admin to add you (see /setup)") from exc
            raise
        db = self.spec.snowflake.database
        if conn:
            self.state.set("wisdom", "connection_id", conn.id)
            if conn.database_filters and db not in conn.database_filters:
                return self._extend_database_filter(conn, db)
            return self._report("connection", "ok", f"'{name}' exists ({conn.id})", connection_id=conn.id, created=False)
        # The service user the Wisdom connection logs in as (the existing "Snowflake Demo"
        # connection uses WISDOMAI_PROD with a programmatic access token). Secrets come
        # from .env only; a PAT is preferred, a password works too.
        user = os.getenv("WISDOM_CONNECTION_SNOWFLAKE_USER")
        pat = os.getenv("WISDOM_CONNECTION_SNOWFLAKE_PAT")
        password = os.getenv("WISDOM_CONNECTION_SNOWFLAKE_PASSWORD")
        if not (user and (pat or password)):
            raise PublishError(
                f"connection '{name}' does not exist in workspace '{self.dep.workspace_name}' and no service credentials are set. "
                "Either create it once in Wisdom (Connections → Snowflake, role WISDOMAI_READ_ONLY, database filter including "
                f"{db}) or set WISDOM_CONNECTION_SNOWFLAKE_USER plus WISDOM_CONNECTION_SNOWFLAKE_PAT (or _PASSWORD) in .env "
                "so the pipeline can create it.")
        snowflake = {"account": self.sf.account, "warehouse": self.sf.warehouse, "user": user, "role": self.sf.read_role,
                     "databaseFilters": [db]}
        if pat:
            snowflake.update({"authType": "SNOWFLAKE_AUTH_TYPE_PROGRAMMATIC_ACCESS_TOKEN", "programmaticAccessToken": pat})
        else:
            snowflake.update({"authType": "SNOWFLAKE_AUTH_TYPE_PASSWORD", "password": password})
        details = self._connection_details(name, [db])
        self._announce("connectionCreate", f"create Snowflake connection '{name}' (role {self.sf.read_role}, databases [{db}])")
        if not self.apply:
            return self._report("connection", "planned", f"would create '{name}'")
        created = self.client.create_connection(details, workspace_id=self.workspace_id)
        self.state.set("wisdom", "connection_id", created["id"])
        return self._report("connection", "ok", f"created '{name}' ({created['id']})", connection_id=created["id"], created=True)

    def wait_for_connection_sync(self, connection_id: str, *, wait_s: int = 600) -> dict:
        """A new connection must crawl before its databases/tables exist. Trigger a
        refresh and poll the connection's job status until a run has succeeded."""
        def snapshot():
            st = (self.client.connection(connection_id) or {}).get("status") or {}
            return st.get("lastRun") or {}, st.get("lastSuccessfulRun") or {}
        last, ok = snapshot()
        if ok and last.get("status") == ok.get("status") and last.get("startedAt") == ok.get("startedAt"):
            return ok
        if not last or str(last.get("status", "")).upper() not in ("RUNNING", "IN_PROGRESS", "PENDING", "QUEUED"):
            try:
                self.client.refresh_connection(connection_id)
            except GraphQLError as exc:
                self._say(f"  note: connectionRefresh: {str(exc)[:160]}")
        deadline = time.time() + wait_s
        seen = None
        while time.time() < deadline:
            last, ok = snapshot()
            status = str(last.get("status", ""))
            if status != seen:
                self._say(f"  connection sync: {status or 'no run yet'}" + (f" (error: {last.get('conciseErrorMessage')})" if last.get("conciseErrorMessage") else ""))
                seen = status
            if ok and ok.get("startedAt") == last.get("startedAt"):
                return ok
            if status.upper() in ("FAILED", "ERROR", "CANCELLED"):
                raise PublishError(f"connection sync failed: {last.get('conciseErrorMessage') or status}")
            time.sleep(10)
        raise PublishError(f"connection {connection_id} did not finish syncing within {wait_s}s")

    def _connection_details(self, name: str, filters: list[str]) -> dict | None:
        """Full ConnectionDetailsInput for the shared Snowflake connection, or None when
        the service credentials are not in .env."""
        user = os.getenv("WISDOM_CONNECTION_SNOWFLAKE_USER")
        pat = os.getenv("WISDOM_CONNECTION_SNOWFLAKE_PAT")
        password = os.getenv("WISDOM_CONNECTION_SNOWFLAKE_PASSWORD")
        if not (user and (pat or password)):
            return None
        snowflake = {"account": self.sf.account, "warehouse": self.sf.warehouse, "user": user, "role": self.sf.read_role,
                     "databaseFilters": filters}
        if pat:
            snowflake.update({"authType": "SNOWFLAKE_AUTH_TYPE_PROGRAMMATIC_ACCESS_TOKEN", "programmaticAccessToken": pat})
        else:
            snowflake.update({"authType": "SNOWFLAKE_AUTH_TYPE_PASSWORD", "password": password})
        return {"name": name, "description": "Shared read-only Snowflake connection for automated demos",
                "connectionType": "SNOWFLAKE", "dataSourceType": "WAREHOUSE", "dialect": "snowflake", "snowflake": snowflake}

    def _extend_database_filter(self, conn, db: str) -> StepReport:
        """The shared connection exists but does not expose this demo's database yet:
        add it to databaseFilters (needs the service credentials) and re-crawl."""
        filters = sorted(set(conn.database_filters) | {db})
        details = self._connection_details(conn.name, filters)
        if details is None:
            return self._report("connection", "failed",
                                f"'{conn.name}' exists but its database filter lacks {db}; add {db} to the connection in Wisdom "
                                "(Connections → edit → databases) or set WISDOM_CONNECTION_SNOWFLAKE_USER/_PAT in .env so the pipeline can")
        self._announce("connectionUpdate", f"add {db} to the database filter of '{conn.name}' ({len(filters)} databases)")
        if not self.apply:
            return self._report("connection", "planned", f"would add {db} to '{conn.name}'")
        self.client.update_connection(conn.id, details)
        try:
            self.client.refresh_connection(conn.id)
        except GraphQLError as exc:
            self._say(f"  note: connectionRefresh: {str(exc)[:120]}")
        back = self.client.find_connection(self.workspace_id, conn.name)
        ok = bool(back and db in back.database_filters)
        return self._report("connection", "ok" if ok else "failed", f"'{conn.name}' now exposes {sorted(back.database_filters) if back else '?'}",
                            connection_id=conn.id, created=False, filters=list(back.database_filters) if back else [])

    # ---- 2. domain ----
    def ensure_domain(self) -> StepReport:
        name = self.spec.wisdom.domain_name
        existing = None
        for d in self.client.list_domains(workspace_id=self.workspace_id, limit=500):
            if str(d.get("name", "")).strip().lower() == name.strip().lower():
                existing = d
                break
        if self.domain_id and existing and existing["id"] != self.domain_id:
            self._say(f"  note: .state.json has domain {self.domain_id} but '{name}' resolves to {existing['id']}; using the live one")
        if existing:
            self.state.set("wisdom", "domain_id", existing["id"])
            return self._report("domain", "ok", f"'{name}' exists ({existing['id']})", domain_id=existing["id"], created=False)
        self._announce("createDomain", f"create domain '{name}'")
        if not self.apply:
            return self._report("domain", "planned", f"would create '{name}'")
        created = self.client.create_domain(name, self.spec.wisdom.domain_description, workspace_id=self.workspace_id)
        self.state.set("wisdom", "domain_id", created["id"])
        return self._report("domain", "ok", f"created '{name}' ({created['id']})", domain_id=created["id"], created=True)

    # ---- 3. database ----
    def attach_database(self, *, wait_s: int = 180) -> StepReport:
        db = self.spec.snowflake.database
        if not self.domain_id:
            return self._report("database", "planned", f"would attach {db} once the domain exists")
        tables = self.client.list_tables(self.domain_id)
        have = sorted({t["name"].upper() for t in tables if str(t.get("database", "")).upper() == db})
        if have:
            missing = [t for t in self.spec.tables + self.spec.snowflake.views if t not in have]
            return self._report("database", "ok", f"{db} attached with {len(have)} tables/views" + (f"; not yet visible: {missing}" if missing else ""),
                                tables=len(have), missing=missing)
        conn_id = self.state.wisdom.get("connection_id")
        self._announce("addDatabaseToDomain", f"attach database {db} from connection {conn_id}")
        if not self.apply:
            return self._report("database", "planned", f"would attach {db}")
        if not conn_id:
            raise PublishError("no connection id — run the connection step first")
        self.wait_for_connection_sync(conn_id)
        # Current product path: browse the connection for the database's table ids and add
        # them to the domain's relationship graph. addDatabaseToDomain is the legacy path
        # and 500s on fresh connections (verified 2026-10-12).
        wanted = set(self.spec.tables + self.spec.snowflake.views)
        hierarchy = [t for t in self.client.database_hierarchy(conn_id, db) if t["schema"].upper() == self.spec.snowflake.schema]
        ids = [t["id"] for t in hierarchy if t["name"].upper() in wanted]
        not_found = sorted(wanted - {t["name"].upper() for t in hierarchy})
        if not ids:
            raise PublishError(f"connection {conn_id} exposes no tables for {self.spec.qualified_schema} — is the database filter / grant right?")
        try:
            self.client.add_tables_to_domain(self.domain_id, ids)
        except GraphQLError as exc:
            self._say(f"  relationship-graph path failed ({str(exc)[:120]}); trying addDatabaseToDomain")
            self.client.add_database_to_domain(self.domain_id, conn_id, db, description=self.spec.wisdom.domain_description)
        if not_found:
            self._say(f"  note: not exposed by the connection (not in the DDL?): {not_found}")
        deadline = time.time() + wait_s
        have = []
        while time.time() < deadline:
            tables = self.client.list_tables(self.domain_id)
            have = sorted({t["name"].upper() for t in tables if str(t.get("database", "")).upper() == db})
            if have:
                break
            time.sleep(5)
        missing = [t for t in self.spec.tables + self.spec.snowflake.views if t not in have]
        status = "ok" if have else "failed"
        return self._report("database", status, f"{db}: {len(have)} tables/views visible" + (f"; missing {missing}" if missing else ""),
                            tables=len(have), missing=missing)

    # ---- 4. knowledge ----
    def knowledge_entries(self) -> list[dict]:
        entries: list[dict] = []
        seen: set[str] = set()
        for text in read_knowledge_csv(self.spec.knowledge_path):
            if text not in seen:
                entries.append({"description": text}); seen.add(text)
        for text in bootstrap_to_knowledge(self.spec.bootstrap_path.read_text()):
            if text not in seen:
                entries.append({"description": text}); seen.add(text)
        return entries

    def sync_knowledge(self) -> StepReport:
        entries = self.knowledge_entries()
        if not self.domain_id:
            return self._report("knowledge", "planned", f"would add {len(entries)} entries once the domain exists")
        existing = {str(k.get("description", "")).strip() for k in self.client.get_domain_knowledge(self.domain_id)}
        new = [e for e in entries if e["description"].strip() not in existing]
        if not new:
            return self._report("knowledge", "ok", f"{len(existing)} entries present, nothing to add", existing=len(existing), added=0)
        self._announce("addKnowledge", f"add {len(new)} knowledge entries ({len(existing)} already there)")
        if not self.apply:
            return self._report("knowledge", "planned", f"would add {len(new)} entries")
        for i in range(0, len(new), 25):
            self.client.add_knowledge(self.domain_id, new[i:i + 25])
        after = len(self.client.get_domain_knowledge(self.domain_id))
        return self._report("knowledge", "ok", f"added {len(new)}; domain now has {after}", existing=len(existing), added=len(new), total=after)

    # ---- 5. reviewed queries ----
    def sync_reviewed_queries(self, registry: Registry) -> StepReport:
        items = to_api_items(registry, self.spec.wisdom.dialect)
        if not self.domain_id:
            return self._report("reviewed_queries", "planned", f"would add {len(items)} reviewed queries once the domain exists")
        existing = {str(r.get("question", "")).strip() for r in self.client.list_reviewed_queries(self.domain_id, limit=500)}
        new = [it for it in items if it["query"].strip() not in existing]
        if not new:
            return self._report("reviewed_queries", "ok", f"{len(existing)} present, nothing to add", existing=len(existing), added=0)
        self._announce("addSqlReviewedQueries", f"add {len(new)} reviewed queries (dialect {self.spec.wisdom.dialect})")
        if not self.apply:
            return self._report("reviewed_queries", "planned", f"would add {len(new)}")
        conn_id = self.state.wisdom.get("connection_id")
        if not conn_id:
            raise PublishError("no connection id — run the connection step first")
        for i in range(0, len(new), 20):
            self.client.add_sql_reviewed_queries(self.domain_id, new[i:i + 20], dialect=self.spec.wisdom.dialect, connection_id=conn_id)
        after = len(self.client.list_reviewed_queries(self.domain_id, limit=500))
        return self._report("reviewed_queries", "ok", f"added {len(new)}; domain now has {after}", existing=len(existing), added=len(new), total=after)

    # ---- 6. metrics ----
    def sync_metrics(self) -> StepReport:
        metrics = read_metrics_csv(self.spec.metrics_path)
        if not self.domain_id:
            return self._report("metrics", "planned", f"would create {len(metrics)} metrics once the domain exists")
        conn_id = self.state.wisdom.get("connection_id")
        existing = {m["name"]: m for m in self.client.list_metrics(self.domain_id)}
        new = [m for m in metrics if m.name not in existing]
        if not new:
            return self._report("metrics", "ok", f"{len(existing)} metrics present, nothing to add", existing=len(existing), added=0)
        self._announce("createMetric", f"validate + create {len(new)} SQL metrics ({len(existing)} already there)")
        if not self.apply:
            return self._report("metrics", "planned", f"would create {len(new)} metrics")
        if not conn_id:
            raise PublishError("no connection id — run the connection step first")
        created, failed = [], []
        for m in new:
            data = self.client.metric_input(name=m.name, expression=m.sql, connection_id=conn_id, description=m.description)
            try:
                self.client.validate_metric(self.domain_id, data)
                self.client.create_metric(self.domain_id, data)
                created.append(m.name)
            except GraphQLError as exc:
                failed.append({"name": m.name, "error": str(exc)[:300]})
        after = len(self.client.list_metrics(self.domain_id))
        self.state.set("wisdom", "metric_names", sorted(set(self.state.wisdom.get("metric_names") or []) | set(created)))
        status = "ok" if not failed else "failed"
        return self._report("metrics", status, f"created {len(created)}; domain now has {after}" + (f"; {len(failed)} rejected: {[f['name'] for f in failed]}" if failed else ""),
                            created=created, failed=failed, total=after)

    # ---- 7. lookup (NER) columns ----
    def sync_lookup_columns(self) -> StepReport:
        wanted = [c.upper() for c in self.spec.wisdom.lookup_columns]
        if not wanted:
            return self._report("lookup", "ok", "no lookup_columns in demo.yaml", changed=0)
        if not self.domain_id:
            return self._report("lookup", "planned", f"would enable lookup on {len(wanted)} columns once the domain exists")
        by_table: dict[str, list[str]] = {}
        for item in wanted:
            if "." not in item:
                continue
            t, col = item.split(".", 1)
            by_table.setdefault(t, []).append(col)
        tables = {t["name"].upper(): t for t in self.client.domain_table_columns(self.domain_id)
                  if str(t.get("database", "")).upper() == self.spec.snowflake.database}
        plan, missing = [], []
        for t, cols in by_table.items():
            tm = tables.get(t)
            if not tm:
                missing.append(t); continue
            have = {c["name"].upper(): c for c in tm.get("columns") or []}
            todo = [c for c in cols if c in have and have[c].get("nerMode") != "NER_ENABLED"]
            missing += [f"{t}.{c}" for c in cols if c not in have]
            if todo:
                plan.append((tm, todo))
        if not plan:
            return self._report("lookup", "ok", "lookup already enabled on all requested columns" + (f"; not found: {missing}" if missing else ""), changed=0, missing=missing)
        self._announce("updateTableColumns", f"enable lookup (NER) on {sum(len(c) for _, c in plan)} columns across {len(plan)} tables")
        if not self.apply:
            return self._report("lookup", "planned", f"would enable lookup on {[f'{t['name']}.{c}' for t, cols in plan for c in cols]}")
        changed = 0
        for tm, cols in plan:
            self.client.update_table_columns(self.domain_id, tm["id"], int(tm["version"]), [{"name": c, "nerMode": "NER_ENABLED"} for c in cols])
            changed += len(cols)
        return self._report("lookup", "ok", f"enabled lookup on {changed} columns" + (f"; not found: {missing}" if missing else ""), changed=changed, missing=missing)

    # ---- 8. system instructions ----
    def instructions_text(self) -> str:
        """Bootstrap sections that read as instructions (overview, relationships,
        business nuances, routing hints); the fact-like sections go in as knowledge."""
        sections = bootstrap_sections(self.spec.bootstrap_path.read_text())
        keep = ("domain overview", "entity relationship", "business nuances", "query routing")
        parts = [f"## {title.title()}\n{body}" for title, body in sections.items() if any(k in title for k in keep)]
        text = (f"Demo as-of date: {self.spec.as_of.isoformat()}. Data spans {self.spec.data_start.isoformat()} to {self.spec.as_of.isoformat()}. "
                f"Warehouse: Snowflake {self.spec.qualified_schema}.\n\n" + "\n\n".join(parts))
        return text[:12000]

    def sync_instructions(self) -> StepReport:
        text = self.instructions_text()
        if not self.domain_id:
            return self._report("instructions", "planned", f"would set {len(text)} chars of domain instructions once the domain exists")
        current = self.client.domain_system_instructions(self.domain_id)
        if current.strip() == text.strip():
            return self._report("instructions", "ok", "domain instructions already up to date", chars=len(text))
        self._announce("updateDomainConfig", f"set domainSystemInstructions ({len(text)} chars{', replacing ' + str(len(current)) + ' chars' if current else ''})")
        if not self.apply:
            return self._report("instructions", "planned", f"would set {len(text)} chars")
        self.client.update_domain_config(self.domain_id, {"domainSystemInstructions": text})
        return self._report("instructions", "ok", f"set {len(text)} chars of domain instructions", chars=len(text))

    # ---- 9. documents (unstructured files stored in the domain) ----
    def upload_documents(self) -> StepReport:
        pdfs = sorted(self.spec.paths.docs_out.glob("*.pdf")) if self.spec.documents else []
        if not self.spec.documents:
            return self._report("documents", "ok", "no documents[] in demo.yaml", uploaded=0)
        if not pdfs:
            return self._report("documents", "failed", "documents[] declared but build/docs has no PDFs — run `demo docs` first")
        if not self.domain_id:
            return self._report("documents", "planned", f"would upload {len(pdfs)} PDFs once the domain exists")
        done = set(self.state.wisdom.get("uploaded_documents") or [])
        todo = [p for p in pdfs if p.name not in done]
        if not todo:
            return self._report("documents", "ok", f"{len(done)} documents already uploaded", uploaded=0)
        self._announce("upload dataset files", f"upload {len(todo)} PDFs as domain files: {[p.name for p in todo]}")
        if not self.apply:
            return self._report("documents", "planned", f"would upload {[p.name for p in todo]}")
        res = self.client.upload_dataset_files(self.domain_id, todo, dataset_id=self.state.wisdom.get("dataset_id"))
        self.state.set("wisdom", "dataset_id", res["dataset_id"])
        self.state.set("wisdom", "uploaded_documents", sorted(done | {p.name for p in todo}))
        return self._report("documents", "ok" if res["ok"] else "failed", f"uploaded {len(todo)} files to dataset {res['dataset_id']}", uploaded=len(todo), dataset_id=res["dataset_id"])

    # ---- orchestration ----
    def run(self, registry: Registry, *, steps: list[str] | None = None) -> list[StepReport]:
        order = [("connection", self.ensure_connection), ("domain", self.ensure_domain), ("database", self.attach_database),
                 ("instructions", self.sync_instructions), ("knowledge", self.sync_knowledge), ("metrics", self.sync_metrics),
                 ("reviewed_queries", lambda: self.sync_reviewed_queries(registry)), ("lookup", self.sync_lookup_columns),
                 ("documents", self.upload_documents)]
        for name, fn in order:
            if steps and name not in steps:
                continue
            try:
                fn()
            except PublishError as exc:
                self._report(name, "failed", str(exc))
                break
            except GraphQLError as exc:
                self._report(name, "failed", f"GraphQLError: {str(exc)[:300]}")
                break
        return self.reports
