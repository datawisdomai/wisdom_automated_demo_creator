"""Publish a demo into Wisdom: connection → domain → database → instructions →
lookup columns → documents → context extraction.

Context (knowledge, metrics, reviewed queries, synonyms, descriptions) reaches the domain
ONLY through the context extractor in `context_mode: extractor` (the default): the local
definitions are rendered into realistic assets (dbt semantic layer, certified query
library, analyst handbook) and uploaded next to the authored context_assets[]; the run's
suggestions are accepted by family and the result is read back as coverage. The direct
CSV / API steps (knowledge, metrics, reviewed_queries) only run in `context_mode: direct`.

Every step is idempotent (reads back what exists first) and records ids in
`.state.json`. Without `apply=True` the publisher only reads and prints the plan.
Built on `wisdomai.Client`; patterns from examples/wisdomai/create_domain_with_context.py.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path

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


def _digest(path) -> str:
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


class Publisher:
    def __init__(self, spec: DemoSpec, state: State, client: Client, *, apply: bool = False, echo: bool = True):
        self.spec, self.state, self.client, self.apply, self.echo = spec, state, client, apply, echo
        self.registry: Registry | None = None
        self.dep = config.wisdom_deployment(spec.wisdom.deployment)
        self.sf = config.snowflake_config()
        self.workspace_id = spec.wisdom.workspace_id or self.dep.workspace_id
        if not self.workspace_id:
            raise PublishError("no workspace_id in demo.yaml or config/deployments.toml")
        # demo.yaml may point at a different workspace than the deployment default: label it honestly
        self.workspace_label = self.dep.workspace_name if self.workspace_id == self.dep.workspace_id else None
        if self.workspace_label is None:
            try:
                self.workspace_label = next((w["name"] for w in client.workspaces() if w["id"] == self.workspace_id), None)
            except Exception:  # noqa: BLE001
                self.workspace_label = None
        self.workspace_label = self.workspace_label or self.workspace_id
        self.existing = bool(spec.wisdom.existing_domain)
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
        tag = f"{self.dep.name} / {self.workspace_label}" + (f" / EXISTING domain {self.spec.wisdom.domain_name}" if self.existing else "")
        self._say(f"  -> {op}: {effect}  [{tag}]")

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
            ours = self.state.wisdom.get("connection_id") == conn.id and bool(self.state.wisdom.get("connection_created"))
            if conn.database_filters and db not in conn.database_filters:
                if self.existing and not ours:
                    # updateConnection re-sends credentials: never do that to a connection somebody else owns
                    return self._report("connection", "failed",
                                        f"'{name}' exists in this workspace ({conn.id}) but was not created by this demo and its database "
                                        f"filter lacks {db}; pick another wisdom.connection.name or add {db} to it by hand in Wisdom")
                self.state.set("wisdom", "connection_id", conn.id)
                return self._extend_database_filter(conn, db)
            self.state.set("wisdom", "connection_id", conn.id)
            return self._report("connection", "ok", f"'{name}' exists ({conn.id})", connection_id=conn.id, created=False)
        if not self.spec.wisdom.connection_create:
            return self._report("connection", "failed", f"connection '{name}' does not exist and wisdom.connection.create is false")
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
        self.state.set("wisdom", "connection_created", True)
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
    def _ensure_existing_domain(self) -> StepReport:
        """Existing-domain mode: resolve wisdom.domain_id in the workspace, insist the live name
        matches wisdom.domain_name (a guard against a wrong id) and never create anything."""
        want = self.spec.wisdom.domain_id
        name = self.spec.wisdom.domain_name
        live = next((d for d in self.client.list_domains(workspace_id=self.workspace_id, limit=500) if d.get("id") == want), None)
        if live is None:
            raise PublishError(f"existing domain {want} not found in workspace {self.workspace_label} on {self.dep.name}")
        if str(live.get("name", "")).strip().lower() != name.strip().lower():
            raise PublishError(f"refusing to touch {want}: it is named '{live.get('name')}' but demo.yaml says '{name}'")
        self.state.set("wisdom", "domain_id", want)
        self.state.set("wisdom", "domain_owned", False)
        return self._report("domain", "ok", f"EXISTING domain '{live.get('name')}' ({want}) — additive only; never created, renamed or deleted by this demo",
                            domain_id=want, created=False, existing=True)

    def ensure_domain(self) -> StepReport:
        if self.existing:
            return self._ensure_existing_domain()
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
        self.state.set("wisdom", "domain_owned", True)
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
            if not missing:
                return self._report("database", "ok", f"{db} attached with {len(have)} tables/views", tables=len(have), missing=[])
            # Additive path (a revision added tables/views after the first publish): attach only the missing ones.
            conn_id = self.state.wisdom.get("connection_id")
            self._announce("updateDomainRelationshipGraphDeltas", f"attach {len(missing)} new objects from {db}: {', '.join(missing)}")
            if not self.apply:
                return self._report("database", "planned", f"{db} attached with {len(have)}; would attach {missing}", tables=len(have), missing=missing)
            if not conn_id:
                raise PublishError("no connection id — run the connection step first")
            hierarchy = [t for t in self.client.database_hierarchy(conn_id, db) if t["schema"].upper() == self.spec.snowflake.schema]
            ids = [t["id"] for t in hierarchy if t["name"].upper() in set(missing)]
            not_found = sorted(set(missing) - {t["name"].upper() for t in hierarchy})
            if not_found:
                return self._report("database", "failed", f"connection {conn_id} does not expose {not_found} yet — refresh the connection (grants? filter?) and re-run",
                                    tables=len(have), missing=missing)
            self.client.add_tables_to_domain(self.domain_id, ids)
            deadline = time.time() + wait_s
            while time.time() < deadline:
                tables = self.client.list_tables(self.domain_id)
                have = sorted({t["name"].upper() for t in tables if str(t.get("database", "")).upper() == db})
                if all(m in have for m in missing):
                    break
                time.sleep(5)
            still = [t for t in missing if t not in have]
            return self._report("database", "ok" if not still else "failed",
                                f"{db}: attached {len(missing) - len(still)} new objects, now {len(have)} tables/views" + (f"; still missing {still}" if still else ""),
                                tables=len(have), missing=still)
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

    # ---- 3b. federated sources: tables from OTHER connections, attached read-only ----
    def attach_federated_sources(self, *, wait_s: int = 180) -> StepReport:
        sources = self.spec.wisdom.federated_sources
        if not sources:
            return self._report("federated", "ok", "no wisdom.federated_sources in demo.yaml", sources=0)
        if not self.domain_id:
            return self._report("federated", "planned", f"would attach {sum(len(f.tables) for f in sources)} tables from {len(sources)} other connection(s) once the domain exists")
        done = dict(self.state.wisdom.get("federated_sources") or {})
        details: list[str] = []
        attached_total = 0
        for src in sources:
            conn = self.client.find_connection(self.workspace_id, src.connection)
            if conn is None:
                raise PublishError(f"federated source connection '{src.connection}' not found in workspace {self.workspace_label} — it must already exist (the pipeline never creates it)")
            wanted = {t.upper() for t in src.tables}
            present = self.client.list_tables(self.domain_id)
            have = sorted({t["name"].upper() for t in present if str(t.get("database", "")).upper() == src.database.upper() and t["name"].upper() in wanted})
            missing = sorted(wanted - set(have))
            if not missing:
                details.append(f"{src.connection}/{src.database}: {len(have)} tables already attached")
                done[src.connection] = {"connection_id": conn.id, "database": src.database, "tables": have, "dialect": src.dialect}
                attached_total += len(have)
                continue
            self._announce("updateDomainRelationshipGraphDeltas", f"attach {len(missing)} read-only tables from '{src.connection}' ({src.database}): {', '.join(missing)}")
            if not self.apply:
                details.append(f"{src.connection}/{src.database}: would attach {len(missing)}")
                continue
            hierarchy = [t for t in self.client.database_hierarchy(conn.id, src.database)
                         if src.schema is None or str(t.get("schema") or "").upper() == src.schema.upper()]
            ids = [t["id"] for t in hierarchy if t["name"].upper() in missing]
            not_found = sorted(set(missing) - {t["name"].upper() for t in hierarchy})
            if not_found:
                raise PublishError(f"'{src.connection}' does not expose {not_found} in {src.database} (exposed: {len(hierarchy)} tables) — check the names in wisdom.federated_sources")
            self.client.add_tables_to_domain(self.domain_id, ids)
            deadline = time.time() + wait_s
            while time.time() < deadline:
                present = self.client.list_tables(self.domain_id)
                have = sorted({t["name"].upper() for t in present if str(t.get("database", "")).upper() == src.database.upper() and t["name"].upper() in wanted})
                if len(have) == len(wanted):
                    break
                time.sleep(5)
            still = sorted(wanted - set(have))
            if still:
                raise PublishError(f"'{src.connection}': {still} not visible in the domain after {wait_s}s")
            done[src.connection] = {"connection_id": conn.id, "database": src.database, "tables": have, "dialect": src.dialect}
            details.append(f"{src.connection}/{src.database}: attached {len(missing)} (now {len(have)})")
            attached_total += len(have)
        if self.apply:
            self.state.set("wisdom", "federated_sources", done)
            self._sync_federated_reviewed_queries(done, details)
        return self._report("federated", "ok" if self.apply else "planned", "; ".join(details), sources=len(sources), tables=attached_total)

    def _sync_federated_reviewed_queries(self, done: dict, details: list[str]) -> None:
        """Reviewed queries with `source=<connection>` are bound to THAT connection and dialect. They
        cannot travel through the context extractor (its reviewed-query suggestions bind to the demo's
        warehouse connection), so this is the one place reviewed SQL is pushed directly."""
        if self.registry is None:
            return
        existing = {str(r.get("question", "")).strip() for r in self.client.list_reviewed_queries(self.domain_id, limit=500)}
        for name, info in done.items():
            sub = self.registry.for_source(name)
            items = [it for it in to_api_items(sub, info["dialect"], connection_id=info["connection_id"]) if it["query"].strip() not in existing]
            if not items:
                continue
            self._announce("addSqlReviewedQueries", f"add {len(items)} reviewed queries bound to '{name}' (dialect {info['dialect']})")
            for i in range(0, len(items), 20):
                self.client.add_sql_reviewed_queries(self.domain_id, items[i:i + 20], dialect=info["dialect"], connection_id=info["connection_id"])
            details.append(f"{name}: {len(items)} reviewed queries bound")

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

    def _extractor_only(self, step: str) -> StepReport | None:
        if self.spec.wisdom.context_mode == "extractor":
            return self._report(step, "skipped", f"context_mode is extractor — {step} reaches the domain only through the context extractor (see the extraction step)")
        return None

    def sync_knowledge(self) -> StepReport:
        if (skip := self._extractor_only("knowledge")):
            return skip
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
        if (skip := self._extractor_only("reviewed_queries")):
            return skip
        items = to_api_items(registry.local(), self.spec.wisdom.dialect)
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
        if (skip := self._extractor_only("metrics")):
            return skip
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
            except Exception as exc:  # noqa: BLE001 — e.g. a transient HTTP read timeout on validateMetric; keep going, retry on the next run
                failed.append({"name": m.name, "error": f"{type(exc).__name__}: {str(exc)[:200]}"})
                self._say(f"  metric {m.name}: {type(exc).__name__} — skipped, re-run publish --only metrics to retry")
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
        fed = ""
        for src in self.spec.wisdom.federated_sources:
            fed += (f" Federated source '{src.connection}' ({src.dialect} dialect; database {src.database}; tables "
                    f"{', '.join(src.tables)}): {src.description or 'read-only tables from another system'} "
                    f"Query it in {src.dialect} SQL on its own connection and combine results with the Snowflake data in the analysis step.")
        text = (f"Demo as-of date: {self.spec.as_of.isoformat()}. Data spans {self.spec.data_start.isoformat()} to {self.spec.as_of.isoformat()}. "
                f"Warehouse: Snowflake {self.spec.qualified_schema}.{fed}\n\n" + "\n\n".join(parts))
        return text[:12000]

    def sync_instructions(self) -> StepReport:
        mode = self.spec.wisdom.instructions_mode
        if mode == "skip":
            return self._report("instructions", "skipped", "wisdom.instructions_mode is skip — the domain's instructions are left exactly as they are")
        text = self.instructions_text()
        if not self.domain_id:
            return self._report("instructions", "planned", f"would set {len(text)} chars of domain instructions once the domain exists")
        current = self.client.domain_system_instructions(self.domain_id) or ""
        if mode == "append":
            # Only our delimited block ever changes; everything outside it is preserved byte for byte.
            begin, end = f"<!-- demo:{self.spec.name} begin -->", f"<!-- demo:{self.spec.name} end -->"
            block = f"{begin}\n{text.strip()}\n{end}"
            if begin in current and end in current:
                head, rest = current.split(begin, 1)
                _, tail = rest.split(end, 1)
                text = head.rstrip() + "\n\n" + block + tail
            else:
                text = (current.rstrip() + "\n\n" if current.strip() else "") + block
        if current.strip() == text.strip():
            return self._report("instructions", "ok", "domain instructions already up to date", chars=len(text))
        effect = (f"append our delimited block to domainSystemInstructions ({len(current)} chars kept)" if mode == "append"
                  else f"set domainSystemInstructions ({len(text)} chars{', replacing ' + str(len(current)) + ' chars' if current else ''})")
        self._announce("updateDomainConfig", effect)
        if not self.apply:
            return self._report("instructions", "planned", f"would {effect}")
        self.client.update_domain_config(self.domain_id, {"domainSystemInstructions": text})
        return self._report("instructions", "ok", f"{'appended our block to' if mode == 'append' else 'set'} domain instructions ({len(text)} chars)", chars=len(text))

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

    # ---- 10. context extraction (the only way context enters the domain in extractor mode) ----
    def extract_context_assets(self, *, wait_s: int = 1500) -> StepReport:
        from .context_assets import ACCEPT_DEFAULT, ALL_AGENTS, accept_suggestions, coverage, extraction_files

        files = extraction_files(self.spec, self.registry)
        if not files:
            return self._report("extraction", "ok", "nothing to extract (no metrics, reviewed queries, knowledge or context_assets[])", uploaded=0)
        missing_pdfs = [f.path.name for f in files if not f.path.is_file()]
        if missing_pdfs:
            return self._report("extraction", "failed", f"{missing_pdfs} not rendered — run `demo docs` first")
        if not self.domain_id:
            return self._report("extraction", "planned", f"would upload {len(files)} files for context extraction once the domain exists: {[f.path.name for f in files]}")
        attached = (self.client.context_extraction_connections(self.domain_id) or {}).get("contextExtractionConnectionIds") or []
        if "files" not in attached:
            self._announce("attachContextExtractionConnection", "attach the uploaded-files source ('files') to the domain for context extraction")
            if not self.apply:
                return self._report("extraction", "planned", f"would attach the 'files' source, upload {len(files)} files and trigger extraction")
            self.client.attach_context_extraction_connection(self.domain_id, "files", acceptance="DO_NOT_AUTO_ACCEPT", auto_extract=False)
            attached = (self.client.context_extraction_connections(self.domain_id) or {}).get("contextExtractionConnectionIds") or []
            if "files" not in attached:
                return self._report("extraction", "failed", f"'files' source not attached after attachContextExtractionConnection (have {attached})")
        already = {f["fileName"]: f for f in self.client.context_extraction_uploaded_files(self.domain_id, "files")}
        uploaded_by_us = self.state.wisdom.get("extraction_uploaded") or {}
        # a file is (re-)uploaded when the domain lacks it or when its content changed since we uploaded it
        # (generated assets: the rendered file; authored assets: the markdown/text source, since PDF bytes vary per render)
        todo = []
        for f in files:
            if f.path.name not in already:
                todo.append(f)
            elif f.path.name in uploaded_by_us and uploaded_by_us.get(f.path.name) != _digest(f.digest_path):
                todo.append(f)
        foreign = [f.path.name for f in todo if f.path.name in already and f.path.name not in uploaded_by_us]
        if foreign:
            return self._report("extraction", "failed", f"{foreign} already exist in the domain's extractor and were not uploaded by this demo — rename the asset(s)")
        # Pending suggestions that existed before our first upload are somebody else's: remember them once so
        # acceptance can leave them untouched whatever the run filter does.
        if self.apply and self.state.wisdom.get("suggestions_preexisting") is None:
            pre = sorted(s["id"] for s in self.client.modeling_suggestions(self.domain_id, include_all_statuses=True) if "PENDING" in str(s.get("status", "")))
            self.state.set("wisdom", "suggestions_preexisting", pre)
            if pre:
                self._say(f"  note: {len(pre)} pending suggestions already in the domain are recorded and will never be accepted by this demo")
        if todo:
            self._announce("registerContextExtractionUploadedFiles", f"upload {len(todo)} files to the context extractor: {[f.path.name for f in todo]}")
            if not self.apply:
                return self._report("extraction", "planned", f"would upload {[f.path.name for f in todo]} and trigger extraction")
            for f in todo:
                if f.path.name in already:
                    self.client.delete_context_extraction_uploaded_file(self.domain_id, already[f.path.name]["sourceFileId"])
                self.client.upload_context_documents(self.domain_id, [f.path], instructions=f.instructions, acceptance="DO_NOT_AUTO_ACCEPT")
                self.state.set("wisdom", "extraction_uploaded", {**(self.state.wisdom.get("extraction_uploaded") or {}), f.path.name: _digest(f.digest_path)})
            after = {f["fileName"] for f in self.client.context_extraction_uploaded_files(self.domain_id, "files")}
            missing = [f.path.name for f in todo if f.path.name not in after]
            if missing:
                return self._report("extraction", "failed", f"uploaded files not registered: {missing}")
        batch = int(self.spec.wisdom.extraction.get("batch_size") or 0)
        names = [f.path.name for f in files]
        # Runs already triggered for these files (resume support): a file is covered when a run
        # that included it succeeded or is still running, unless the file was just re-uploaded.
        runs: dict = dict(self.state.wisdom.get("extraction_runs") or {})
        statuses = {r["jobRun"]["jobRunId"]: (r["jobRun"]["status"] or "") for r in self.client.knowledge_extraction_runs(self.domain_id, limit=50)}
        changed = {f.path.name for f in todo}
        covered, active = set(), []
        for rid, info in runs.items():
            st = statuses.get(rid, "")
            if "SUCCESS" in st:
                covered |= set(info.get("files") or [])
            elif "RUNNING" in st or "PENDING" in st or "QUEUED" in st:
                covered |= set(info.get("files") or [])
                active.append(rid)
        covered -= changed
        pending = [n for n in names if n not in covered]
        if not pending and not active and self.state.wisdom.get("extraction_coverage"):
            return self._report("extraction", "ok", "extraction already complete for every file", uploaded=0,
                                coverage=self.state.wisdom.get("extraction_coverage"))
        chunks = [pending[i:i + batch] for i in range(0, len(pending), batch)] if batch > 0 else ([pending] if pending else [])
        if chunks:
            self._announce("triggerKnowledgeExtraction", f"extract {ALL_AGENTS} from {len(pending)} uploaded files"
                           + (f" in {len(chunks)} concurrent runs of at most {batch} files" if batch > 0 else ""))
        if not self.apply:
            return self._report("extraction", "planned", f"would trigger {len(chunks)} extraction run(s)" + (f" and wait on {len(active)} running" if active else ""))
        # trigger every batch first (runs execute concurrently on the platform), then wait on all of them
        for i, chunk in enumerate(chunks, 1):
            rid = self._trigger(chunk)
            if rid is None:
                return self._report("extraction", "failed", f"extraction run {i}/{len(chunks)} did not appear within 180s of the trigger")
            self._say(f"  extraction run {i}/{len(chunks)} {rid}: {chunk}")
            runs[rid] = {"files": chunk}
            active.append(rid)
            self.state.set("wisdom", "extraction_runs", runs)
            self.state.set("wisdom", "extraction_run_id", rid)
        rep = None
        for rid in active:
            rep = self._wait_extraction(rid, wait_s, uploaded=len(todo))
            if rep.status != "ok":
                return rep
        return self._finish_extraction(rep)

    def _trigger(self, file_names: list[str], *, force_full: bool | None = None) -> str | None:
        """Trigger one extraction run for `file_names`; returns its run id (found by diffing the
        run list, the mutation returns nothing useful) or None after 180 s."""
        from .context_assets import ALL_AGENTS

        before = {r["jobRun"]["jobRunId"] for r in self.client.knowledge_extraction_runs(self.domain_id, limit=50)}
        self.client.trigger_knowledge_extraction(self.domain_id, "files", file_names, agent_types=ALL_AGENTS, force_full=force_full)
        deadline = time.time() + 180
        while time.time() < deadline:
            new = [r for r in self.client.knowledge_extraction_runs(self.domain_id, limit=50) if r["jobRun"]["jobRunId"] not in before]
            if new:
                return new[0]["jobRun"]["jobRunId"]
            time.sleep(5)
        return None

    def _trigger_and_wait(self, file_names: list[str], wait_s: int, *, uploaded: int, force_full: bool | None = None) -> StepReport:
        from .context_assets import ALL_AGENTS

        before = {r["jobRun"]["jobRunId"] for r in self.client.knowledge_extraction_runs(self.domain_id, limit=50)}
        self.client.trigger_knowledge_extraction(self.domain_id, "files", file_names, agent_types=ALL_AGENTS, force_full=force_full)
        run_id = None
        deadline = time.time() + 180
        while run_id is None and time.time() < deadline:
            new = [r for r in self.client.knowledge_extraction_runs(self.domain_id, limit=50) if r["jobRun"]["jobRunId"] not in before]
            if new:
                run_id = new[0]["jobRun"]["jobRunId"]
                self.state.set("wisdom", "extraction_run_id", run_id)
                break
            time.sleep(10)
        if run_id is None:
            return self._report("extraction", "failed", "extraction run did not appear within 180s of the trigger")
        return self._wait_extraction(run_id, wait_s, uploaded=uploaded)

    def _finish_extraction(self, rep: StepReport) -> StepReport:
        """Accept the configured suggestion families, read back coverage, retry once with a
        full re-extraction when coverage is short, then report — never fall back to CSV."""
        from .context_assets import ACCEPT_DEFAULT, accept_suggestions, coverage, extraction_files

        if rep is None:   # resumed after every run had already finished (e.g. a network drop before coverage was read)
            rep = StepReport("extraction", "ok", "resumed: all runs finished", {})
        families = list(self.spec.wisdom.extraction.get("accept") or ACCEPT_DEFAULT)
        threshold = float(self.spec.wisdom.extraction.get("coverage_threshold", 0.9))
        scope = dict(job_run_ids=list((self.state.wisdom.get("extraction_runs") or {}).keys()),
                     exclude_ids=set(self.state.wisdom.get("suggestions_preexisting") or []))
        acc = accept_suggestions(self.client, self.domain_id, families, **scope)
        self._remember_accepted(acc)
        self._say(f"  accepted {acc['accepted']} suggestions ({acc['by_family']}); {acc['left_pending']} left pending for steward review"
                  + (f"; scoped to {len(scope['job_run_ids'])} run(s), {len(scope['exclude_ids'])} pre-existing untouched" if self.existing else ""))
        cov = coverage(self.client, self.domain_id, self.spec, self.registry)
        short = [k for k in ("metrics", "reviewed_queries") if cov[k]["expected"] and cov[k]["coverage"] < threshold]
        if short and not self.state.wisdom.get("extraction_retried"):
            self._say(f"  coverage short on {short} ({ {k: cov[k]['coverage'] for k in short} }) — one full re-extraction")
            self.state.set("wisdom", "extraction_retried", True)
            names2 = [f.path.name for f in extraction_files(self.spec, self.registry)]
            batch = int(self.spec.wisdom.extraction.get("batch_size") or 0)
            rids = []
            for chunk in ([names2[i:i + batch] for i in range(0, len(names2), batch)] if batch > 0 else [names2]):
                rid = self._trigger(chunk, force_full=True)
                if rid is None:
                    return self._report("extraction", "failed", "re-extraction run did not appear within 180s of the trigger")
                rids.append(rid)
                runs_state = dict(self.state.wisdom.get("extraction_runs") or {})
                runs_state[rid] = {"files": chunk, "full": True}
                self.state.set("wisdom", "extraction_runs", runs_state)
            for rid in rids:
                rep2 = self._wait_extraction(rid, 1500, uploaded=0)
                if rep2.status != "ok":
                    return rep2
            scope["job_run_ids"] = list((self.state.wisdom.get("extraction_runs") or {}).keys()) + rids
            acc2 = accept_suggestions(self.client, self.domain_id, families, **scope)
            self._remember_accepted(acc2)
            acc["accepted"] += acc2["accepted"]
            cov = coverage(self.client, self.domain_id, self.spec, self.registry)
            short = [k for k in ("metrics", "reviewed_queries") if cov[k]["expected"] and cov[k]["coverage"] < threshold]
        self.state.set("wisdom", "extraction_coverage", cov)
        summary = (f"metrics {cov['metrics']['found']}/{cov['metrics']['expected']}, reviewed queries {cov['reviewed_queries']['found']}/{cov['reviewed_queries']['expected']}, "
                   f"knowledge {cov['knowledge']['in_domain']} entries; accepted {acc['accepted']}, {acc['left_pending']} pending for review")
        status = "ok" if not short else "failed"
        detail = summary if not short else (summary + f" — coverage below {threshold:.0%} on {short}; missing: "
                                            + "; ".join(f"{k}: {cov[k]['missing'][:8]}" for k in short))
        return self._report("extraction", status, detail, run_id=rep.data.get("run_id"), job_status=rep.data.get("job_status"),
                            accepted=acc, coverage=cov, uploaded=rep.data.get("uploaded"))

    def _remember_accepted(self, acc: dict) -> None:
        ids = sorted(set(self.state.wisdom.get("accepted_suggestion_ids") or []) | set(acc.get("accepted_ids") or []))
        self.state.set("wisdom", "accepted_suggestion_ids", ids)

    def _wait_extraction(self, run_id: str, wait_s: int, *, uploaded: int) -> StepReport:
        deadline = time.time() + wait_s
        status = None
        while time.time() < deadline:
            run = next((r for r in self.client.knowledge_extraction_runs(self.domain_id, limit=50) if r["jobRun"]["jobRunId"] == run_id), None)
            status = (run or {}).get("jobRun", {}).get("status")
            if status and ("SUCCESS" in status or "FAIL" in status or "ERROR" in status or "CANCEL" in status):
                break
            if run:
                self._say(f"  extraction {run_id}: {status} ({run.get('filesCompletedCount')}/{run.get('filesTotalCount')} files)")
            time.sleep(20)
        ok = bool(status and "SUCCESS" in status)
        return self._report("extraction", "ok" if ok else ("running" if status and "RUNNING" in status else "failed"),
                            f"run {run_id} {status}", uploaded=uploaded, run_id=run_id, job_status=status)

    def _extraction_status(self, run_id: str) -> str | None:
        for r in self.client.knowledge_extraction_runs(self.domain_id, limit=50):
            if r["jobRun"]["jobRunId"] == run_id:
                return r["jobRun"]["status"]
        return None

    # ---- 10b. skills: every wisdom.skills[] file exists in the domain (extractor first, direct create as the fallback) ----
    def sync_skills(self) -> StepReport:
        from .spec import skill_frontmatter

        wanted = list(self.spec.wisdom.skills)
        if not wanted:
            return self._report("skills", "ok", "no wisdom.skills in demo.yaml", skills=0)
        if not self.domain_id:
            return self._report("skills", "planned", f"would ensure {len(wanted)} skills once the domain exists: {[w.name for w in wanted]}")
        have = {str(x.get("name", "")): x for x in self.client.list_domain_skills(self.domain_id, include_markdown=True)}
        done = dict(self.state.wisdom.get("skills") or {})
        details, created, updated, kept = [], 0, 0, 0
        for sk in wanted:
            path = self.spec.dir / sk.file
            md = path.read_text()
            fm = skill_frontmatter(md)
            name = fm.get("name") or sk.name
            cur = have.get(name)
            if cur is None:
                self._announce("createDomainSkill", f"create skill '{name}' from {sk.file} (availability {sk.availability})")
                if not self.apply:
                    details.append(f"{name}: would create")
                    continue
                back = self.client.create_domain_skill(self.domain_id, md, availability=sk.availability)
                done[name] = {"id": back["id"], "version": back.get("version"), "via": "direct", "file": sk.file}
                created += 1
                details.append(f"{name}: created v{back.get('version')} ({back['id']})")
            else:
                via = (done.get(name) or {}).get("via") or ("extractor" if not done.get(name) else "direct")
                if (cur.get("skillMarkdown") or "").strip() == md.strip():
                    kept += 1
                    done[name] = {"id": cur["id"], "version": cur.get("version"), "via": via, "file": sk.file}
                    details.append(f"{name}: present v{cur.get('version')} via {via}")
                    continue
                if via == "extractor" and not done.get(name):
                    # proposed by the context extractor (and accepted): keep its wording, that is the demo beat
                    kept += 1
                    done[name] = {"id": cur["id"], "version": cur.get("version"), "via": "extractor", "file": sk.file}
                    details.append(f"{name}: present v{cur.get('version')} via extractor (wording differs from {sk.file}; kept)")
                    continue
                self._announce("updateDomainSkill", f"update skill '{name}' from {sk.file} (v{cur.get('version')})")
                if not self.apply:
                    details.append(f"{name}: would update")
                    continue
                back = self.client.update_domain_skill(self.domain_id, cur["id"], int(cur.get("version") or 1), md, availability=sk.availability)
                done[name] = {"id": back["id"], "version": back.get("version"), "via": "direct", "file": sk.file}
                updated += 1
                details.append(f"{name}: updated to v{back.get('version')}")
            if self.apply and not (have.get(name) or {}).get("isActive", True):
                self.client.set_domain_skill_active(self.domain_id, done[name]["id"], True)
        if self.apply:
            # read-back verification: every skill present, active, and without dangling schema references
            # (a skill that names a column on the wrong view is shown as "Stale" in the UI and never loads)
            back = {str(x.get("name", "")): x for x in self.client.list_domain_skills(self.domain_id, include_markdown=False)}
            missing = [sk.name for sk in wanted if sk.name not in back]
            stale = {sk.name: back[sk.name].get("danglingSchemaRefs") for sk in wanted if sk.name in back and back[sk.name].get("danglingSchemaRefs")}
            self.state.set("wisdom", "skills", done)
            if missing:
                return self._report("skills", "failed", f"not in the domain after sync: {missing}", skills=len(done))
            if stale:
                return self._report("skills", "failed", f"stale (dangling schema references, fix the wording): {stale}", skills=len(done), stale=stale)
        return self._report("skills", "ok" if self.apply else "planned", "; ".join(details),
                            skills=len(wanted), created=created, updated=updated, kept=kept)

    # ---- 11. S3 dataset (stretch): the contract PDFs in the customer's bucket, read through Wisdom's S3 connection ----
    def attach_s3_dataset(self, *, wait_s: int = 600) -> StepReport:
        from .s3_sync import s3_settings

        cfg = self.spec.raw.get("s3") or {}
        if not cfg:
            return self._report("s3_dataset", "ok", "no s3: block in demo.yaml", attached=False)
        st = s3_settings(self.spec)
        if not st["bucket"]:
            return self._report("s3_dataset", "failed", "S3 bucket not configured in .env")
        if not self.domain_id:
            return self._report("s3_dataset", "planned", "would create the S3 connection and dataset once the domain exists")
        conn_name = str(cfg.get("connection_name") or f"{self.spec.title} Contract Archive")
        conn = self.client.find_connection(self.workspace_id, conn_name)
        if conn:
            conn_id = conn.id
        else:
            key = os.getenv("WISDOM_S3_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID")
            secret = os.getenv("WISDOM_S3_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
            if not (key and secret):
                return self._report("s3_dataset", "failed", "no AWS key in .env for the Wisdom S3 connection")
            details = {"name": conn_name, "description": f"Signed contract PDFs for the {self.spec.title} demo (s3://{st['bucket']}/{st['key_prefix']}/)",
                       "connectionType": "S3", "dataSourceType": "FILE",
                       "s3": {"bucketName": st["bucket"], "region": st["region"], "authType": "S3_AUTH_TYPE_ACCESS_KEY", "awsAccessKeyId": key, "awsSecretAccessKey": secret}}
            self._announce("connectionCreate", f"create S3 connection '{conn_name}' on bucket {st['bucket']}")
            if not self.apply:
                return self._report("s3_dataset", "planned", f"would create S3 connection '{conn_name}'")
            conn_id = self.client.create_connection(details, workspace_id=self.workspace_id)["id"]
        self.state.set("wisdom", "s3_connection_id", conn_id)
        ds_name = str(cfg.get("dataset_name") or f"{self.spec.title} contracts")
        existing = [d for d in self.client.connection_datasets(conn_id) if d["name"] == ds_name]
        if existing:
            ds_id = existing[0]["id"]
        else:
            self._announce("createConnectionDataset", f"dataset '{ds_name}' on prefix {st['key_prefix']}/")
            if not self.apply:
                return self._report("s3_dataset", "planned", f"would create dataset '{ds_name}'")
            ds_id = self.client.create_connection_dataset(conn_id, ds_name, prefix=st["key_prefix"] + "/",
                                                          description="Signed agreements and amendments (DocuSign archive)")["id"]
        self.state.set("wisdom", "s3_dataset_id", ds_id)
        refs = self.client.domain_dataset_references(self.domain_id)
        have = [r for r in refs.get("references", []) if r["datasetId"] == ds_id]
        if not have:
            self._announce("setDomainDatasetReference", f"attach dataset {ds_id} (all files) to the domain")
            if not self.apply:
                return self._report("s3_dataset", "planned", "would attach the dataset to the domain")
            self.client.set_domain_dataset_reference(self.domain_id, ds_id, active=True, expected_revision=0)
        try:
            self.client.trigger_dataset_crawl(ds_id, self.domain_id)
        except GraphQLError as exc:
            self._say(f"  note: triggerDatasetCrawl: {str(exc)[:160]}")
        deadline = time.time() + wait_s
        state = {}
        while time.time() < deadline:
            state = self.client.connection_dataset_state(ds_id)
            refs = self.client.domain_dataset_references(self.domain_id)
            ref = next((r for r in refs.get("references", []) if r["datasetId"] == ds_id), None)
            self._say(f"  dataset {ds_id}: files {state.get('totalFiles')} extracted {state.get('extractedFiles')} crawl {(state.get('dataset') or {}).get('crawlJobStatus')}; domain pending {refs.get('pendingFiles')} failed {refs.get('failedFiles')}")
            if (state.get("totalFiles") or 0) > 0 and ref and not ref.get("indexingPending") and not refs.get("pendingFiles"):
                break
            time.sleep(20)
        ref = next((r for r in self.client.domain_dataset_references(self.domain_id).get("references", []) if r["datasetId"] == ds_id), None)
        ok = bool(ref and ref.get("active"))
        return self._report("s3_dataset", "ok" if ok else "failed",
                            f"connection {conn_id}, dataset {ds_id}: {state.get('totalFiles')} files seen, {state.get('extractedFiles')} extracted; domain reference {'active' if ok else 'missing'}"
                            + (f" (indexing still pending)" if ref and ref.get("indexingPending") else ""),
                            connection_id=conn_id, dataset_id=ds_id, files=state.get("totalFiles"), extracted=state.get("extractedFiles"),
                            indexing_pending=bool(ref and ref.get("indexingPending")))

    # ---- orchestration ----
    def run(self, registry: Registry, *, steps: list[str] | None = None) -> list[StepReport]:
        self.registry = registry
        order = [("connection", self.ensure_connection), ("domain", self.ensure_domain), ("database", self.attach_database),
                 ("federated", self.attach_federated_sources), ("instructions", self.sync_instructions), ("knowledge", self.sync_knowledge), ("metrics", self.sync_metrics),
                 ("reviewed_queries", lambda: self.sync_reviewed_queries(registry)), ("lookup", self.sync_lookup_columns),
                 ("documents", self.upload_documents), ("extraction", self.extract_context_assets), ("skills", self.sync_skills),
                 ("s3_dataset", self.attach_s3_dataset)]
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
