from __future__ import annotations

import os
from typing import Any

import httpx
from dotenv import load_dotenv

from . import operations as ops
from .deployments import get_deployment
from .errors import GraphQLError, MutationStatusError, WisdomAIError
from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectionInfo:
    """Flattened view of a workspace connection (see ``Client.list_connections``)."""

    id: str
    name: str
    dialect: str | None = None
    data_source_type: str | None = None
    connection_type: str | None = None
    snowflake_account: str | None = None
    snowflake_role: str | None = None
    snowflake_warehouse: str | None = None
    database_filters: tuple[str, ...] = ()
    created_at: str | None = None


class Client:
    """Sync client for the WisdomAI GraphQL API.

    Auth flow: the access key is exchanged for a JWT on first authenticated
    request (or explicitly via `exchange_access_token`), then cached on the
    instance. Call `refresh_token()` if you get a 401/expired-token error.
    """

    def __init__(
        self,
        access_key: str,
        tenant: str,
        *,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
        deployment: str | None = None,
        domains: tuple | list | None = None,
        host: str | None = None,
        impersonation_key: str | None = None,
    ):
        if not access_key:
            raise WisdomAIError("access_key is required")
        if not tenant:
            raise WisdomAIError("tenant is required (the {ACCOUNT} subdomain)")
        self.access_key = access_key
        # Impersonation is a SEPARATE permission on a Wisdom API key: a key
        # without the "Impersonator" role still returns a JWT from
        # `impersonateUser`, but that JWT does not authenticate (the API answers
        # "Not authenticated"), so embeds silently bounce to /login. Keep the
        # impersonator key distinct from the ordinary admin key and use it only
        # for `impersonate_user`.
        self.impersonation_key = impersonation_key
        self.tenant = tenant
        # Friendly deployment name + remembered domains, populated when the
        # client is built via `for_deployment`. Plain `Client(...)` leaves them
        # unset/empty.
        #   domains — the deployment's remembered domains (`Domain` objects with
        #     id/name/note), filled in by `examples/sync_domains.py` so you can
        #     pick a domain at session start without rediscovery. These are a
        #     convenience only: no domain is privileged as "safe", methods still
        #     take an explicit domain_id, and every write is announced.
        self.deployment = deployment
        self.domains = tuple(domains or ())
        # Standard SaaS tenants live at `{tenant}.askwisdom.ai`. Customer VPC
        # deployments run on their own FQDN (e.g. a host reachable only via a
        # VPN / /etc/hosts entry pointing at a private IP); `host` overrides the
        # derived hostname for those.
        self.host = host or f"{tenant}.askwisdom.ai"
        self.endpoint = f"https://{self.host}/graphql"
        self.ws_endpoint = f"wss://{self.host}/graphql"
        self._http = http_client or httpx.Client(timeout=timeout)
        self._owns_http = http_client is None
        self._token: str | None = None

    @classmethod
    def from_env(cls, *, dotenv_path: str | None = None, **kwargs) -> "Client":
        if dotenv_path:
            load_dotenv(dotenv_path)
        else:
            load_dotenv()
        tenant = os.getenv("WISDOMAI_TENANT", "proddemo")
        access_key = (
            os.getenv("WISDOMAI_ACCESS_KEY")
            or os.getenv(f"{tenant}_key")
        )
        if not access_key:
            raise WisdomAIError(
                "No access key in env. Set WISDOMAI_ACCESS_KEY "
                f"(or {tenant}_key) in .env."
            )
        return cls(access_key=access_key, tenant=tenant, **kwargs)

    @classmethod
    def for_deployment(
        cls,
        name: str,
        *,
        config_path: str | None = None,
        dotenv_path: str | None = None,
        **kwargs,
    ) -> "Client":
        """Build a client for a named deployment from the registry.

        Looks the deployment up in ``deployments.toml`` (your local, gitignored
        registry), then resolves its access key from ``.env`` via the
        deployment's ``access_key_env`` (defaults to ``<tenant>_key``), falling
        back to ``WISDOMAI_ACCESS_KEY``. The returned client carries
        ``.deployment`` (the name) and ``.domains`` (the deployment's remembered
        domains, if any) for convenience — methods still take an explicit
        ``domain_id``.
        """
        dep = get_deployment(name, config_path)
        if dotenv_path:
            load_dotenv(dotenv_path)
        else:
            load_dotenv()
        access_key = os.getenv(dep.access_key_env) or os.getenv(
            "WISDOMAI_ACCESS_KEY"
        )
        if not access_key:
            raise WisdomAIError(
                f"No access key for deployment '{name}'. Set "
                f"{dep.access_key_env} (or WISDOMAI_ACCESS_KEY) in .env."
            )
        return cls(
            access_key=access_key,
            tenant=dep.tenant,
            deployment=dep.name,
            domains=dep.domains,
            host=dep.host,
            impersonation_key=os.getenv(f"{dep.tenant}_impersonation_key"),
            **kwargs,
        )

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ---- auth ----
    @property
    def token(self) -> str:
        if self._token is None:
            self._token = self.exchange_access_token()
        return self._token

    def exchange_access_token(self) -> str:
        data = self._request(
            ops.EXCHANGE_ACCESS_TOKEN,
            {"accessToken": self.access_key},
            auth=False,
            op_name="exchangeAccessToken",
        )
        self._token = data["exchangeAccessToken"]
        return self._token

    def refresh_token(self) -> str:
        self._token = None
        return self.token

    # ---- low-level ----
    def _request(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        *,
        auth: bool = True,
        op_name: str | None = None,
    ) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if auth:
            headers["Authorization"] = f"Bearer {self.token}"
        payload = {"query": query, "variables": variables or {}}
        r = self._http.post(self.endpoint, json=payload, headers=headers)
        # The API claims "HTTP 200 even on failure," but GraphQL validation
        # errors actually come back as 400 with a JSON `errors` array. Parse
        # the body first so we surface the real GraphQL message rather than
        # an opaque HTTPStatusError.
        try:
            body = r.json()
        except ValueError:
            body = None
        if isinstance(body, dict) and body.get("errors"):
            raise GraphQLError(body["errors"], operation=op_name)
        r.raise_for_status()
        return (body or {}).get("data") or {}

    def request(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        *,
        op_name: str | None = None,
    ) -> dict[str, Any]:
        """Run an arbitrary authenticated query/mutation. Raises GraphQLError on errors."""
        return self._request(query, variables, auth=True, op_name=op_name)

    @staticmethod
    def _check_status(payload: dict | None, op_name: str) -> dict:
        if payload is None:
            raise WisdomAIError(f"{op_name} returned no payload")
        status = payload.get("status") if "status" in payload else payload
        code = status.get("code") if isinstance(status, dict) else None
        if code and code != "OK":
            raise MutationStatusError(code, status.get("message", ""), operation=op_name)
        return payload

    # ---- users ----
    def current_user(self) -> dict:
        return self.request(ops.CURRENT_USER, op_name="currentUser")["currentUser"]

    def list_users(
        self,
        workspace_id: str | None = None,
        *,
        email_search: str | None = None,
    ) -> list[dict]:
        input_obj: dict[str, Any] = {}
        if workspace_id is not None:
            input_obj["workspaceID"] = workspace_id
        if email_search is not None:
            input_obj["emailSearch"] = email_search
        data = self.request(
            ops.LIST_USERS,
            {"input": input_obj or None},
            op_name="users",
        )
        return data["users"]

    def create_users(
        self,
        emails: list[str],
        *,
        workspace_id: str | None = None,
        role_assignments: list[dict] | None = None,
        send_welcome_email: bool = False,
        user_attributes: list[dict] | None = None,
        user_group_ids: list[str] | None = None,
    ) -> dict:
        input_obj: dict[str, Any] = {
            "emails": emails,
            "workspaceID": workspace_id,
            "roleAssignments": role_assignments,
            "sendWelcomeEmail": send_welcome_email,
            "userAttributes": user_attributes,
            "userGroupIds": user_group_ids,
        }
        input_obj = {k: v for k, v in input_obj.items() if v is not None}
        data = self.request(
            ops.CREATE_USERS, {"input": input_obj}, op_name="createUsers"
        )
        return self._check_status(data["createUsers"], "createUsers")

    def set_user_attributes(self, user_id: str, user_attributes: list[dict]) -> dict:
        data = self.request(
            ops.SET_USER_ATTRIBUTES,
            {"input": {"userId": user_id, "userAttributes": user_attributes}},
            op_name="setUserAttributes",
        )
        return self._check_status(data["setUserAttributes"], "setUserAttributes")

    def impersonate_user(
        self,
        user_email: str,
        *,
        attributes: list[dict] | None = None,
        access_key: str | None = None,
    ) -> str:
        """Mint a 1-hour session JWT for `user_email` (for embed URLs).

        This is what the `?token=` query param on an `/embed/...` URL wants.
        Unlike every other call here it authenticates with the raw access key
        passed as an *argument* (no Bearer header), and — despite the docs
        calling it a mutation — it is a **Query** field in the live schema.

        `attributes` are transient `{key, value}` user attributes layered onto
        the session (used for row-level authorization) without persisting them.

        ⚠️ The key must have the **Impersonator** role (Settings → API Keys shows
        an "Impersonator" badge). A key without it still returns a JWT here, but
        that JWT fails with "Not authenticated" and the embed bounces to /login.
        Set `<tenant>_impersonation_key` in `.env` for that key; it is used in
        preference to the ordinary access key, or pass `access_key=` explicitly.

        SERVER-SIDE ONLY. The access key it consumes grants impersonation of any
        user in the org, so this must never run in a browser.
        """
        key = access_key or self.impersonation_key or self.access_key
        data = self._request(
            ops.IMPERSONATE_USER,
            {
                "accessToken": key,
                "userEmail": user_email,
                "attributes": attributes,
            },
            auth=False,
            op_name="impersonateUser",
        )
        return data["impersonateUser"]

    # ---- apps ----
    def list_apps(
        self,
        workspace_id: str | None = None,
        *,
        limit: int = 200,
        offset: int = 0,
    ) -> list[dict]:
        """Apps ("Live apps") in a workspace. Each is backed by a `dashboardId`.

        The `apps` field is paginated on newer builds and a plain list on older
        ones, so try the paginated form first and fall back. `limit`/`offset`
        are ignored by tenants still on the old shape.
        """
        if workspace_id is None:
            workspace_id = self.default_workspace_id()
        try:
            data = self.request(
                ops.LIST_APPS_PAGED,
                {"workspaceId": workspace_id, "offset": offset, "limit": limit},
                op_name="apps",
            )
            return data["apps"]["nodes"]
        except GraphQLError:
            data = self.request(
                ops.LIST_APPS, {"workspaceId": workspace_id}, op_name="apps"
            )
            return data["apps"]

    def get_app(self, app_id: str) -> dict:
        return self.request(ops.GET_APP, {"appId": app_id}, op_name="app")["app"]

    # ---- dashboards ----
    def dashboards(
        self,
        scope: str = "VIEWER",
        *,
        domain_id: str | None = None,
        owner_id: str | None = None,
    ) -> list[dict]:
        data = self.request(
            ops.DASHBOARDS,
            {"scope": scope, "domainId": domain_id, "ownerId": owner_id},
            op_name="dashboards",
        )
        return data["dashboards"]["nodes"]

    def dashboard(
        self,
        dashboard_id: str,
        scope: str = "VIEWER",
        version: str | None = None,
    ) -> dict:
        data = self.request(
            ops.DASHBOARD,
            {"id": dashboard_id, "scope": scope, "version": version},
            op_name="dashboard",
        )
        return data["dashboard"]

    def refresh_dashboard(self, dashboard_id: str, version: str | None = None) -> dict:
        data = self.request(
            ops.REFRESH_DASHBOARD,
            {"id": dashboard_id, "version": version},
            op_name="refreshDashboard",
        )
        return data["refreshDashboard"]

    # ---- chat ----
    def create_conversation(self, domain_id: str, hidden: bool = False) -> str:
        data = self.request(
            ops.CREATE_CONVERSATION,
            {"domainId": domain_id, "hidden": hidden},
            op_name="createConversation",
        )
        return data["id"]

    def send_user_message(
        self,
        conversation_id: str,
        domain_id: str,
        text: str,
    ) -> dict:
        # Quill-style Delta, but `insert` is a DeltaElementInput OBJECT (not a
        # bare string): one `{"insert": {"text": ...}}` op carries plain text.
        delta = {"ops": [{"insert": {"text": text + "\n"}}]}
        data = self.request(
            ops.SEND_USER_MESSAGE,
            {
                "conversationId": conversation_id,
                "domainId": domain_id,
                "query": delta,
            },
            op_name="sendUserMessage",
        )
        return self._check_status(data["sendUserMessage"], "sendUserMessage")

    # ---- workspaces ----
    def workspaces(self) -> list[dict]:
        """All workspaces visible to this user (``[{id, name}]``)."""
        return self.request(ops.WORKSPACES, op_name="workspaces")["workspaces"]

    def default_workspace_id(self) -> str:
        """The single workspace's id. Most tenants have exactly one
        ("Default Organization"); raises if there are zero or several so the
        caller passes an explicit id rather than guessing.
        """
        ws = self.workspaces()
        if len(ws) != 1:
            names = ", ".join(f"{w['name']} ({w['id']})" for w in ws) or "(none)"
            raise WisdomAIError(
                f"Expected exactly one workspace, found {len(ws)}: {names}. "
                "Pass workspace_id explicitly."
            )
        return ws[0]["id"]

    # ---- domains (admin) ----
    def list_domains(
        self,
        *,
        workspace_id: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[dict]:
        """List domains on this deployment (``[{id, name, updatedAt, isHidden}]``).

        ``workspace_id`` defaults to the tenant's sole workspace. Note the
        underlying ``domainsLightweight`` query requires both a workspace id and
        a limit — both are supplied here.
        """
        if workspace_id is None:
            workspace_id = self.default_workspace_id()
        data = self.request(
            ops.LIST_DOMAINS,
            {"workspaceID": workspace_id, "limit": limit, "offset": offset},
            op_name="domainsLightweight",
        )
        return data["domainsLightweight"]["nodes"]

    def create_domain(
        self,
        name: str,
        description: str | None = None,
        workspace_id: str | None = None,
    ) -> dict:
        input_obj: dict[str, Any] = {"name": name}
        if description is not None:
            input_obj["description"] = description
        if workspace_id is not None:
            input_obj["workspaceID"] = workspace_id
        data = self.request(
            ops.CREATE_DOMAIN, {"input": input_obj}, op_name="createDomain"
        )
        return data["createDomain"]

    def duplicate_domain(self, domain_id: str, workspace_id: str | None = None) -> dict:
        data = self.request(
            ops.DUPLICATE_DOMAIN,
            {"id": domain_id, "workspaceID": workspace_id},
            op_name="duplicateDomain",
        )
        return data["duplicateDomain"]

    def add_database_to_domain(
        self,
        domain_id: str,
        connection_id: str,
        database_name: str,
        *,
        description: str | None = None,
        relationship_graph: dict | None = None,
    ) -> dict:
        """Attach a connection's database (and its tables) to a domain.

        Replaces the old ``data_sources_update`` — the schema's data-source
        surface is now database-grained: you add a whole database from a
        connection (``connection_id`` + ``database_name``) rather than wiring a
        per-table list. ``relationship_graph`` is an optional
        ``RelationshipGraphInput`` (joins/relationships). Returns the updated
        domain (``{id, name}``).
        """
        input_obj: dict[str, Any] = {
            "domainId": domain_id,
            "connectionId": connection_id,
            "databaseName": database_name,
        }
        if description is not None:
            input_obj["databaseDescription"] = description
        if relationship_graph is not None:
            input_obj["relationshipGraph"] = relationship_graph
        data = self.request(
            ops.ADD_DATABASE_TO_DOMAIN,
            {"input": input_obj},
            op_name="addDatabaseToDomain",
        )
        return data["addDatabaseToDomain"]

    # ---- connections (admin) ----
    def create_connection(
        self,
        details: dict,
        *,
        workspace_id: str | None = None,
        skip_validation: bool | None = None,
    ) -> dict:
        """Create a new connection. Returns ``{id, details:{name, connectionType}}``.

        ``details`` is a ``ConnectionDetailsInput`` whose fields are specific to
        the connection type (Snowflake, BigQuery, S3, …) — introspect
        ``ConnectionDetailsInput`` for the exact shape
        (``examples/introspect_schema.py <deployment> --type ConnectionDetailsInput``).
        Pass ``skip_validation=True`` to skip the server-side connectivity check.
        """
        data = self.request(
            ops.CONNECTION_CREATE,
            {
                "details": details,
                "skipValidation": skip_validation,
                "workspaceID": workspace_id,
            },
            op_name="connectionCreate",
        )
        return data["connectionCreate"]

    def list_connections(self, workspace_id: str) -> list["ConnectionInfo"]:
        """Connections visible in one workspace, flattened to ``ConnectionInfo``.

        Raises ``GraphQLError`` ("You do not have permission to access this
        resource") when the key's user is not a member of the workspace.
        """
        data = self.request(
            ops.LIST_CONNECTIONS, {"workspaceID": workspace_id}, op_name="connections"
        )
        out = []
        for node in data["connections"]["nodes"]:
            d = node.get("details") or {}
            sf = d.get("snowflake") or {}
            out.append(ConnectionInfo(
                id=node["id"],
                name=d.get("name") or "",
                dialect=d.get("dialect"),
                data_source_type=d.get("dataSourceType"),
                connection_type=d.get("connectionType"),
                snowflake_account=sf.get("account"),
                snowflake_role=sf.get("role"),
                snowflake_warehouse=sf.get("warehouse"),
                database_filters=tuple(sf.get("databaseFilters") or ()),
                created_at=node.get("createdAt"),
            ))
        return out

    def find_connection(self, workspace_id: str, name: str) -> "ConnectionInfo | None":
        """First connection in the workspace whose name matches (case-insensitive)."""
        wanted = name.strip().lower()
        for conn in self.list_connections(workspace_id):
            if conn.name.strip().lower() == wanted:
                return conn
        return None

    def connection(self, connection_id: str) -> dict:
        data = self.request(
            ops.GET_CONNECTION, {"id": connection_id}, op_name="connection"
        )
        return data["connection"]

    def refresh_connection(self, connection_id: str) -> bool:
        """Kick off an async refresh of the connection. Returns True on accepted."""
        data = self.request(
            ops.CONNECTION_REFRESH, {"id": connection_id}, op_name="connectionRefresh"
        )
        return bool(data["connectionRefresh"])

    # ---- tables from a connection (demo creator) ----
    def database_hierarchy(self, connection_id: str, database_name: str) -> list[dict]:
        """``[{schema, id, name, type, numColumns}]`` for every table/view the connection exposes in the database."""
        data = self.request(ops.DATABASE_HIERARCHY_WITH_TABLES, {"connectionId": connection_id, "databaseName": database_name},
                            op_name="databaseHierarchyWithTables")
        out = []
        for schema in data["databaseHierarchyWithTables"]["nodes"]:
            for t in schema.get("tables") or []:
                out.append({"schema": schema["name"], **t})
        return out

    def add_tables_to_domain(self, domain_id: str, table_ids: list[str]) -> dict:
        """Add tables (ids from ``database_hierarchy``) to the domain's relationship graph."""
        data = self.request(ops.UPDATE_DOMAIN_RELATIONSHIP_GRAPH_DELTAS, {"input": {"domainId": domain_id, "tableIdsToAdd": table_ids}},
                            op_name="updateDomainRelationshipGraphDeltas")
        return data["updateDomainRelationshipGraphDeltas"]

    # ---- metrics (demo creator) ----
    def list_metrics(self, domain_id: str) -> list[dict]:
        data = self.request(ops.GET_DOMAIN_METRICS, {"id": domain_id}, op_name="domain")
        return (data.get("domain") or {}).get("metrics") or []

    def domain_system_instructions(self, domain_id: str) -> str:
        data = self.request(ops.GET_DOMAIN_METRICS, {"id": domain_id}, op_name="domain")
        return (data.get("domain") or {}).get("domainSystemInstructions") or ""

    def metric_input(self, *, name: str, expression: str, connection_id: str, description: str = "",
                     display_name: str | None = None, display_format: str = "DISPLAY_FORMAT_UNKNOWN",
                     precision: int = 0, visibility: bool = True) -> dict:
        """A ``MetricInput`` for a SQL metric (``SUM(TABLE.COLUMN) / NULLIF(...)``)."""
        return {"name": name, "displayName": display_name or name, "description": description or "",
                "definitionType": "SQL", "connectionId": connection_id, "authoredExpression": expression,
                "displayFormat": display_format, "precision": precision, "visibility": visibility}

    def validate_metric(self, domain_id: str, data: dict) -> dict:
        return self.request(ops.VALIDATE_METRIC, {"domainId": domain_id, "data": data}, op_name="validateMetric")["validateMetric"]

    def create_metric(self, domain_id: str, data: dict) -> dict:
        return self.request(ops.CREATE_METRIC, {"domainId": domain_id, "data": data}, op_name="createMetric")["createMetric"]

    def update_metric(self, domain_id: str, metric_id: str, data: dict) -> dict:
        return self.request(ops.UPDATE_METRIC, {"domainId": domain_id, "metricId": metric_id, "data": data}, op_name="updateMetric")["updateMetric"]

    def delete_metric(self, domain_id: str, metric_id: str) -> bool:
        return bool(self.request(ops.DELETE_METRIC, {"domainId": domain_id, "metricId": metric_id}, op_name="deleteMetric")["deleteMetric"])

    # ---- table columns / NER lookup (demo creator) ----
    def domain_table_columns(self, domain_id: str) -> list[dict]:
        """``[{database, id, version, name, columns:[{name, nerMode, visibility, isPrimaryKey, description}]}]``."""
        data = self.request(ops.GET_DOMAIN_TABLE_COLUMNS, {"id": domain_id}, op_name="domain")
        out = []
        for db in (data.get("domain") or {}).get("databases") or []:
            for t in db.get("tables") or []:
                out.append({"database": db["name"], **t})
        return out

    def update_table_columns(self, domain_id: str, table_id: str, table_version: int, columns: list[dict]) -> dict:
        """Bulk ``ColumnInput`` update, e.g. ``[{"name": "CUSTOMER_NAME", "nerMode": "NER_ENABLED"}]``."""
        return self.request(ops.UPDATE_TABLE_COLUMNS, {"domainId": domain_id, "tableId": table_id, "tableVersion": table_version,
                                                       "data": {"columns": columns}}, op_name="updateTableColumns")["updateTableColumns"]

    def update_domain_config(self, domain_id: str, data: dict) -> dict:
        """``DomainConfigInput`` — e.g. ``{"domainSystemInstructions": "..."}``."""
        return self.request(ops.UPDATE_DOMAIN_CONFIG, {"domainId": domain_id, "data": data}, op_name="updateDomainConfig")["updateDomainConfig"]

    # ---- documents (demo creator) ----
    def upload_context_documents(self, domain_id: str, paths: list, *, instructions: str = "",
                                 acceptance: str = "AUTO_ACCEPT_HIGH_CONFIDENCE", trigger: bool = True) -> dict:
        """Upload files for the Context Extractor: signed URLs -> PUT -> register -> (optionally) trigger extraction."""
        from pathlib import Path as _P

        files = [_P(p) for p in paths]
        urls = self.request(ops.GENERATE_SIGNED_URLS_FOR_KNOWLEDGE_EXTRACTION,
                            {"domainId": domain_id, "filenames": [f.name for f in files]},
                            op_name="generateSignedUrlsForKnowledgeExtraction")["generateSignedUrlsForKnowledgeExtraction"]
        if len(urls) != len(files):
            raise WisdomAIError(f"asked for {len(files)} signed urls, got {len(urls)}")
        for f, u in zip(files, urls):
            r = httpx.put(u["signedUrl"], content=f.read_bytes(), headers={"Content-Type": "application/octet-stream"}, timeout=120)
            r.raise_for_status()
        reg_files = [{"file": {"name": u["key"]}, "instructions": instructions, "acceptanceStrategy": acceptance} for u in urls]
        reg = self.request(ops.REGISTER_CONTEXT_EXTRACTION_UPLOADED_FILES, {"input": {"domainId": domain_id, "files": reg_files}},
                           op_name="registerContextExtractionUploadedFiles")
        return {"keys": [u["key"] for u in urls], "register": reg}

    def context_extraction_connections(self, domain_id: str) -> dict:
        data = self.request(ops.DOMAIN_CONTEXT_EXTRACTION_CONNECTIONS, {"id": domain_id}, op_name="domain")
        return data.get("domain") or {}

    def context_extraction_uploaded_files(self, domain_id: str, connection_id: str) -> list[dict]:
        return self.request(ops.CONTEXT_EXTRACTION_UPLOADED_FILES, {"input": {"domainId": domain_id, "connectionId": connection_id}},
                            op_name="contextExtractionUploadedFiles")["contextExtractionUploadedFiles"]

    def trigger_knowledge_extraction(self, domain_id: str, connection_id: str, file_names: list[str] | None = None,
                                     agent_types: list[str] | None = None) -> dict:
        src = {"connectionId": connection_id}
        if file_names:
            src["fileNames"] = file_names
        inp = {"domainId": domain_id, "sources": [src]}
        if agent_types:
            inp["agentTypes"] = agent_types
        return self.request(ops.TRIGGER_KNOWLEDGE_EXTRACTION, {"input": inp}, op_name="triggerKnowledgeExtraction")

    def upload_dataset_files(self, domain_id: str, paths: list, *, dataset_id: str | None = None) -> dict:
        """Upload files as domain DATA (unstructured files the AI reasons over)."""
        from pathlib import Path as _P

        files = [_P(p) for p in paths]
        if dataset_id is None:
            dataset_id = self.request(ops.GENERATE_DATASET_ID_FOR_DOMAIN, {"domainId": domain_id},
                                      op_name="generateDatasetIdForDomain")["generateDatasetIdForDomain"]
        urls = self.request(ops.GENERATE_SIGNED_URLS_FOR_DATASET_FILES,
                            {"datasetId": dataset_id, "domainId": domain_id, "filenames": [f.name for f in files]},
                            op_name="generateSignedUrlsForDatasetFiles")["generateSignedUrlsForDatasetFiles"]
        for f, u in zip(files, urls):
            r = httpx.put(u["signedUrl"], content=f.read_bytes(), headers={"Content-Type": "application/octet-stream"}, timeout=120)
            r.raise_for_status()
        ok = self.request(ops.HANDLE_DATASET_FILE_UPLOAD, {"datasetId": dataset_id, "domainId": domain_id, "rawFilePaths": [u["key"] for u in urls]},
                          op_name="handleDatasetFileUpload")["handleDatasetFileUpload"]
        return {"dataset_id": dataset_id, "keys": [u["key"] for u in urls], "ok": bool(ok)}

    # ---- live apps (demo creator) ----
    def create_app(self, workspace_id: str, name: str, domain_id: str) -> dict:
        return self.request(ops.CREATE_APP, {"workspaceId": workspace_id, "name": name, "domainId": domain_id}, op_name="createApp")["createApp"]

    def get_app_full(self, app_id: str) -> dict:
        return self.request(ops.GET_APP_FULL, {"appId": app_id}, op_name="app")["app"]

    def publish_app_draft(self, app_id: str, note: str | None = None) -> dict:
        return self.request(ops.PUBLISH_APP_DRAFT, {"appId": app_id, "note": note}, op_name="publishAppDraft")["publishAppDraft"]

    def create_conversation_full(self, domain_id: str, *, hidden: bool = False, workspace_id: str | None = None,
                                 live_app_edit_policy: str | None = None, request_channel_type: str | None = None,
                                 channel_source_id: str | None = None) -> str:
        """liveAppEditPolicy is only accepted together with requestChannelType LIVE_APP, and a
        Live App conversation also needs channelSourceId = the app id."""
        v = {"domainId": domain_id, "hidden": hidden, "workspaceId": workspace_id, "liveAppEditPolicy": live_app_edit_policy,
             "requestChannelType": request_channel_type, "channelSourceId": channel_source_id}
        return self.request(ops.CREATE_CONVERSATION_FULL, v, op_name="createConversation")["id"]

    def set_active_app_conversation(self, app_id: str, conversation_id: str | None) -> dict:
        return self.request(ops.SET_ACTIVE_APP_CONVERSATION, {"appId": app_id, "conversationId": conversation_id}, op_name="setActiveAppConversation")

    def active_app_conversation(self, app_id: str) -> dict | None:
        q = "query($a: ID!){ activeAppConversation(appId: $a){ conversationId domainId } }"
        return self.request(q, {"a": app_id}, op_name="activeAppConversation")["activeAppConversation"]

    def send_live_app_prompt(self, conversation_id: str, domain_id: str, text: str, *, workspace_id: str | None,
                             dashboard_id: str, dashboard_version: int = 0, dashboard_sub_version: str = "",
                             render_target: str = "REACT_APP", chat_mode: str | None = None) -> dict:
        delta = {"ops": [{"insert": {"text": text + "\n"}}]}
        v = {"conversationId": conversation_id, "domainId": domain_id, "query": delta, "workspaceId": workspace_id,
             "activeDashboardReference": {"dashboardId": dashboard_id, "version": dashboard_version, "subVersion": dashboard_sub_version},
             "dashUxRenderTarget": render_target, "chatMode": chat_mode}
        data = self.request(ops.SEND_USER_MESSAGE_LIVE_APP, v, op_name="sendUserMessage")
        return data["sendUserMessage"]

    def chat_messages(self, conversation_id: str) -> list[dict]:
        return self.request(ops.CHAT_MESSAGES, {"conversationId": conversation_id}, op_name="chatMessages")["chatMessages"]["nodes"]

    # ---- agents (demo creator) ----
    def generate_workflow_from_prompt(self, prompt: str, *, domain_id: str, workspace_id: str | None = None) -> dict:
        inp = {"messages": [{"role": "user", "content": prompt}], "domainId": domain_id}
        if workspace_id:
            inp["workspaceID"] = workspace_id
        return self.request(ops.GENERATE_WORKFLOW_FROM_PROMPT, {"input": inp}, op_name="generateWorkflowFromPrompt")["generateWorkflowFromPrompt"]

    def create_workflow_agent(self, specification: dict, *, workspace_id: str | None = None, as_draft: bool = True) -> dict:
        v = {"specification": specification, "workspaceID": workspace_id, "asDraft": as_draft}
        return self.request(ops.CREATE_WORKFLOW_AGENT, v, op_name="createWorkflowAgent")["createWorkflowAgent"]

    def update_agent_state(self, agent_id: str, state: str, reason: str | None = None) -> dict:
        return self.request(ops.UPDATE_AGENT_STATE, {"agentId": agent_id, "state": state, "reason": reason}, op_name="updateAgentState")

    def get_agent(self, agent_id: str, *, workspace_id: str | None = None, include_draft: bool = True) -> dict | None:
        return self.request(ops.GET_AGENT, {"id": agent_id, "workspaceID": workspace_id, "includeDraft": include_draft}, op_name="agent")["agent"]

    def list_agents(self, workspace_id: str | None = None) -> list[dict]:
        return self.request(ops.LIST_AGENTS, {"workspaceID": workspace_id}, op_name="agents")["agents"]

    # ---- domain health (demo creator) ----
    def trigger_domain_health_check(self, domain_id: str) -> dict:
        """Queue a Domain Health analysis run. Returns {status{code,message}, jobRunId, alreadyQueued}."""
        return self.request(ops.TRIGGER_DOMAIN_HEALTH_CHECK, {"domainId": domain_id}, op_name="triggerDomainHealthCheck")["triggerDomainHealthCheck"]

    # ---- teardown (demo creator) ----
    def delete_agent(self, agent_id: str) -> bool:
        return bool(self.request(ops.DELETE_AGENT, {"id": agent_id}, op_name="deleteAgent")["deleteAgent"])

    def delete_app(self, app_id: str) -> dict:
        return self.request(ops.DELETE_APP, {"appId": app_id}, op_name="deleteApp")["deleteApp"]

    def update_connection(self, connection_id: str, details: dict, *, skip_validation: bool | None = None) -> dict:
        """connectionUpdate with a full ConnectionDetailsInput (credentials included)."""
        return self.request(ops.CONNECTION_UPDATE, {"id": connection_id, "details": details, "skipValidation": skip_validation},
                            op_name="connectionUpdate")["connectionUpdate"]

    def delete_domain(self, domain_id: str) -> dict:
        """IRREVERSIBLE. Only `demo teardown --i-mean-it` calls this."""
        return self.request(ops.DELETE_DOMAIN, {"id": domain_id}, op_name="deleteDomain")

    # ---- knowledge / context (admin) ----
    def get_domain_knowledge(self, domain_id: str) -> list[dict]:
        data = self.request(
            ops.GET_DOMAIN_KNOWLEDGE, {"domainId": domain_id}, op_name="domain"
        )
        return (data.get("domain") or {}).get("knowledge") or []

    def add_knowledge(self, domain_id: str, entries: list[dict]) -> dict:
        """Add knowledge (free-form business context) entries to a domain.

        Each entry: {"description": "...", "name": "..."} (name optional).
        Duplicates (matched by description) are silently filtered server-side.
        """
        data = self.request(
            ops.ADD_KNOWLEDGE,
            {"domainId": domain_id, "knowledgeEntries": entries},
            op_name="addKnowledge",
        )
        return data["addKnowledge"]

    def update_knowledge(
        self,
        domain_id: str,
        old: dict,
        updated: dict,
    ) -> dict:
        """`old` must exactly match the existing entry's description."""
        data = self.request(
            ops.UPDATE_KNOWLEDGE,
            {
                "domainId": domain_id,
                "oldKnowledge": old,
                "updatedKnowledge": updated,
            },
            op_name="updateKnowledge",
        )
        return data["updateKnowledge"]

    def delete_knowledge(self, domain_id: str, knowledge: dict) -> dict:
        data = self.request(
            ops.DELETE_KNOWLEDGE,
            {"domainId": domain_id, "knowledge": knowledge},
            op_name="deleteKnowledge",
        )
        return data["deleteKnowledge"]

    # ---- evaluation sets and runs (admin) ----
    # NB: these operations are present in the live schema but not in the
    # published docs. Items use a doubly-nested list: items[session][turn].

    @staticmethod
    def _normalize_items(items: list) -> list[list[dict]]:
        """Accept a flat list of {prompt, sql} (single-turn shorthand) or a
        pre-nested list of sessions. Returns the canonical [[...]] shape.
        """
        if not items:
            return []
        first = items[0]
        if isinstance(first, dict):
            return [[item] for item in items]
        return items

    def list_eval_sets(
        self, domain_id: str, draft_id: str | None = None
    ) -> list[dict]:
        data = self.request(
            ops.LIST_EVAL_SETS,
            {"domainId": domain_id, "draftId": draft_id},
            op_name="evalSets",
        )
        return data["evalSets"]

    def get_eval_set(self, eval_set_id: str, domain_id: str) -> dict | None:
        """No top-level `evalSet(id)` query — filter the domain's list."""
        for s in self.list_eval_sets(domain_id):
            if s["id"] == eval_set_id:
                return s
        return None

    def create_eval_set(
        self,
        name: str,
        domain_id: str,
        items: list,
        draft_id: str | None = None,
    ) -> dict:
        """Create an eval set.

        `items` accepts either:
          - flat single-turn list: [{"prompt": "...", "sql": ["..."]}, ...]
          - doubly-nested multi-turn: [[{...}, {...}], [{...}], ...]
        """
        input_obj: dict[str, Any] = {
            "name": name,
            "domainId": domain_id,
            "items": self._normalize_items(items),
        }
        if draft_id is not None:
            input_obj["draftId"] = draft_id
        data = self.request(
            ops.CREATE_EVAL_SET, {"input": input_obj}, op_name="createEvalSet"
        )
        return data["createEvalSet"]

    def update_eval_set(
        self,
        eval_set_id: str,
        items: list,
        name: str | None = None,
    ) -> dict:
        input_obj: dict[str, Any] = {
            "id": eval_set_id,
            "items": self._normalize_items(items),
        }
        if name is not None:
            input_obj["name"] = name
        data = self.request(
            ops.UPDATE_EVAL_SET, {"input": input_obj}, op_name="updateEvalSet"
        )
        return data["updateEvalSet"]

    def delete_eval_set(self, eval_set_id: str) -> bool:
        data = self.request(
            ops.DELETE_EVAL_SET,
            {"input": {"id": eval_set_id}},
            op_name="deleteEvalSet",
        )
        return bool(data["deleteEvalSet"])

    def run_evaluation(
        self,
        domain_id: str,
        eval_set_id: str,
        *,
        run_count: int | None = None,
        parallelization: int | None = None,
        selected_model_name: str | None = None,
        experimental_mode: str | None = None,
        existing_run_id: str | None = None,
        draft_id: str | None = None,
    ) -> str:
        """Fire an eval run. Returns the new run ID; the run executes async."""
        variables: dict[str, Any] = {
            "domainId": domain_id,
            "existingEvalSetId": eval_set_id,
            "runCount": run_count,
            "parallelization": parallelization,
            "selectedModelName": selected_model_name,
            "experimentalMode": experimental_mode,
            "existingRunId": existing_run_id,
            "draftId": draft_id,
        }
        data = self.request(ops.RUN_EVALUATION, variables, op_name="runEvaluation")
        return data["runEvaluation"]

    def cancel_evaluation_run(self, run_id: str) -> bool:
        data = self.request(
            ops.CANCEL_EVALUATION_RUN, {"id": run_id}, op_name="cancelEvaluationRun"
        )
        return bool(data["cancelEvaluationRun"])

    def evaluation_run(
        self, run_id: str, *, page: int | None = None, page_size: int | None = None
    ) -> dict:
        data = self.request(
            ops.GET_EVALUATION_RUN,
            {"id": run_id, "page": page, "pageSize": page_size},
            op_name="evaluationRun",
        )
        return data["evaluationRun"]

    def evaluation_runs(
        self,
        *,
        eval_set_ids: list[str] | None = None,
        domain_ids: list[str] | None = None,
        eval_set_type: str | None = None,
        workspace_id: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        filt: dict[str, Any] = {}
        if eval_set_ids is not None:
            filt["evaluationSetIds"] = eval_set_ids
        if domain_ids is not None:
            filt["domainIds"] = domain_ids
        if eval_set_type is not None:
            filt["evalSetType"] = eval_set_type
        data = self.request(
            ops.LIST_EVALUATION_RUNS,
            {
                "filter": filt,
                "workspaceID": workspace_id,
                "offset": offset,
                "limit": limit,
            },
            op_name="evaluationRuns",
        )
        return data["evaluationRuns"]

    def evaluation_run_group(
        self, run_group_id: str, workspace_id: str | None = None
    ) -> dict:
        data = self.request(
            ops.GET_EVALUATION_RUN_GROUP,
            {"runGroupId": run_group_id, "workspaceId": workspace_id},
            op_name="evaluationRunGroup",
        )
        return data["evaluationRunGroup"]

    def eval_analysis_status(self, domain_id: str) -> dict:
        data = self.request(
            ops.GET_EVAL_ANALYSIS_STATUS,
            {"domainId": domain_id},
            op_name="getEvalAnalysisStatus",
        )
        return data["getEvalAnalysisStatus"]

    def update_evaluation_run(
        self,
        run_id: str,
        *,
        session_index: int,
        prompt_index: int,
        manual_score: float | None = None,
        manual_feedback: str | None = None,
        gt_sql: str | None = None,
    ) -> dict:
        input_obj: dict[str, Any] = {
            "sessionIndex": session_index,
            "promptIndex": prompt_index,
        }
        if manual_score is not None:
            input_obj["manualScore"] = manual_score
        if manual_feedback is not None:
            input_obj["manualFeedback"] = manual_feedback
        if gt_sql is not None:
            input_obj["gtSQL"] = gt_sql
        data = self.request(
            ops.UPDATE_EVALUATION_RUN,
            {"id": run_id, "input": input_obj},
            op_name="updateEvaluationRun",
        )
        return data["updateEvaluationRun"]

    def create_evalset_from_reviewed_queries(
        self,
        domain_id: str,
        *,
        run_eval: bool | None = None,
        tags: list[str] | None = None,
        run_count: int | None = None,
        experimental_mode: str | None = None,
    ) -> dict:
        data = self.request(
            ops.CREATE_EVALSET_FROM_REVIEWED_QUERIES,
            {
                "domainId": domain_id,
                "runEval": run_eval,
                "tags": tags,
                "runCount": run_count,
                "experimentalMode": experimental_mode,
            },
            op_name="createEvalsetFromReviewedQueries",
        )
        return data["createEvalsetFromReviewedQueries"]

    def build_evalset_items_from_reviewed_queries(
        self, domain_id: str, *, enabled_only: bool = True
    ) -> list[dict]:
        """Turn a domain's reviewed queries into eval-set items.

        Each executable SQL reviewed query becomes a single-turn item
        ``{"prompt": question, "sql": [ground_truth_sql]}``. Non-SQL or
        non-executable reviewed queries (no usable SQL ground truth) are skipped.
        """
        items: list[dict] = []
        for rq in self.list_reviewed_queries(domain_id, limit=500):
            if enabled_only and not rq.get("enabled", True):
                continue
            code = rq.get("answerCodeObj") or {}
            sql = code.get("codeStr")
            if rq.get("answerType") != "SQL" or not sql:
                continue
            items.append({"prompt": rq["question"], "sql": [sql]})
        return items

    def run_reviewed_queries_eval(
        self,
        domain_id: str,
        *,
        run_count: int = 3,
        experimental_mode: str = "EXPERIMENTAL_MODE_NONE",
        name: str | None = None,
        parallelization: int | None = None,
    ) -> dict:
        """Run a *normal, viewable* eval over the domain's reviewed queries.

        Workaround for the super-user-gated domain-health "RQ eval" (see
        CLAUDE.md). NB: ``createEvalsetFromReviewedQueries(runEval=True)`` does
        NOT do this — it drives the domain-health pipeline and returns an
        unreadable ``ET_JOB_RUN_…``. Instead this hand-builds a standard eval set
        from the reviewed queries' SQL ground truth and runs it via the plain
        ``runEvaluation`` mutation, whose run IS readable by a normal-user key
        through ``evaluation_run`` / ``evaluation_run_group``.

        Defaults encode the agreed config: run 3× on chat v1
        (``EXPERIMENTAL_MODE_NONE``, i.e. *not* the Canvas-V2 "Early Release"
        modes). Returns
        ``{evalSetId, evalSetName, itemCount, runGroupId, runIds}``.

        Fires and returns immediately — it does NOT wait for the runs, which can
        take a long time (potentially hours). Read results later with
        ``evaluation_runs(eval_set_ids=[evalSetId])`` then ``evaluation_run(id)``
        per run.

        Gotcha: ``runEvaluation`` with ``run_count > 1`` returns the *run-group*
        id, not a resolvable ``evaluation_run`` id. The individual run ids are
        discovered here via ``evaluation_runs(eval_set_ids=…)`` and returned as
        ``runIds`` — those are what ``evaluation_run`` can read.

        ⚠️ This is a WRITE: it creates an eval set and spins up real
        conversations (cost). Announce + confirm before calling.
        """
        items = self.build_evalset_items_from_reviewed_queries(domain_id)
        if not items:
            raise ValueError(
                f"no executable SQL reviewed queries to evaluate in {domain_id}"
            )
        es = self.create_eval_set(
            name=name or "Reviewed Queries eval (API)",
            domain_id=domain_id,
            items=items,
        )
        run_group_id = self.run_evaluation(
            domain_id=domain_id,
            eval_set_id=es["id"],
            run_count=run_count,
            parallelization=parallelization,
            experimental_mode=experimental_mode,
        )
        run_ids = [
            r["id"] for r in self.evaluation_runs(eval_set_ids=[es["id"]])
        ]
        return {
            "evalSetId": es["id"],
            "evalSetName": es.get("name"),
            "itemCount": len(items),
            "runGroupId": run_group_id,
            "runIds": run_ids,
        }

    def schedule_eval_set(
        self,
        eval_set_id: str,
        cron_expression: str | None = None,
        cron_timezone: str | None = None,
    ) -> dict:
        data = self.request(
            ops.SCHEDULE_EVAL_SET,
            {
                "evalSetId": eval_set_id,
                "cronExpression": cron_expression,
                "cronTimezone": cron_timezone,
            },
            op_name="scheduleEvalSet",
        )
        return data["scheduleEvalSet"]

    def pause_scheduled_eval(self, domain_id: str, eval_set_id: str) -> bool:
        data = self.request(
            ops.PAUSE_SCHEDULED_EVAL,
            {"domainId": domain_id, "evalSetId": eval_set_id},
            op_name="pauseScheduledEval",
        )
        return bool(data["pauseScheduledEval"])

    def trigger_eval_analysis(
        self,
        domain_id: str,
        *,
        include_schema_analysis: bool | None = None,
        require_rq_eval: bool | None = None,
    ) -> dict:
        data = self.request(
            ops.TRIGGER_EVAL_ANALYSIS,
            {
                "domainId": domain_id,
                "includeSchemaAnalysis": include_schema_analysis,
                "requireRqEval": require_rq_eval,
            },
            op_name="triggerEvalAnalysis",
        )
        return data["triggerEvalAnalysis"]

    def wait_for_evaluation_run(
        self,
        run_id: str,
        *,
        timeout_s: float = 600.0,
        poll_s: float = 5.0,
    ) -> dict:
        """Poll evaluation_run(id) until completedAt or cancelledAt is set.

        Raises TimeoutError if the run hasn't terminated within `timeout_s`.
        Returns the final EvaluationRun payload.
        """
        import time as _time

        deadline = _time.monotonic() + timeout_s
        while True:
            run = self.evaluation_run(run_id)
            if run.get("completedAt") or run.get("cancelledAt"):
                return run
            if _time.monotonic() >= deadline:
                raise TimeoutError(
                    f"evaluation run {run_id} did not finish within {timeout_s}s"
                )
            _time.sleep(poll_s)

    # ---- table inspection + SQL execution ----
    # Undocumented; confirmed via introspection. On CSV-backed domains the
    # warehouse db is `wisdom_storage` and the dialect is `duckdb`.
    def list_tables(self, domain_id: str) -> list[dict]:
        """Return the domain's tables: ``[{database, id, name, displayName,
        isUserCSVTable, columns:[{name, dataType, description}]}]``.

        There is no read wrapper for table structure elsewhere — this fills the
        gap left by ``get_domain_knowledge`` (which only returns knowledge).
        """
        data = self.request(ops.GET_DOMAIN_TABLES, {"id": domain_id}, op_name="domain")
        out: list[dict] = []
        for db in (data.get("domain") or {}).get("databases") or []:
            for t in db.get("tables") or []:
                out.append({"database": db["name"], **t})
        return out

    def run_sql(
        self,
        domain_id: str,
        sql: str,
        *,
        dialect: str = "duckdb",
        database_name: str = "wisdom_storage",
    ) -> dict:
        """Execute arbitrary SQL against a domain and return rows.

        Returns ``{columns: [name, ...], rows: [[value, ...], ...]}``. Defaults
        target CSV-backed domains (``duckdb`` / ``wisdom_storage``); pass
        ``dialect``/``database_name`` for warehouse-connected domains. Note
        ``dryExecuteSqlQuery`` only *validates* SQL — this actually runs it.
        """
        data = self.request(
            ops.RUN_SQL_QUERY,
            {
                "domainId": domain_id,
                "sql": sql,
                "dialect": dialect,
                "databaseName": database_name,
            },
            op_name="runSqlQuery",
        )
        viz = data["runSqlQuery"]["visualization"]
        return {
            "columns": [c["name"] for c in viz["columns"]],
            "rows": [[cell["value"] for cell in row] for row in viz["data"]],
        }

    def table_preview(
        self,
        table_id: str,
        domain_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """Preview a table's rows: ``{columns, rows}``.

        **Gotcha:** the underlying ``tablePreview.totalRows`` is unreliable (it
        can report a tiny number for a large table) and offset-paging can hang —
        for an accurate count use ``run_sql(domain_id, "SELECT COUNT(*) ...")``.
        """
        data = self.request(
            ops.TABLE_PREVIEW,
            {"tableId": table_id, "domainId": domain_id, "limit": limit, "offset": offset},
            op_name="tablePreview",
        )
        p = data["tablePreview"]
        return {
            "columns": [c["name"] for c in p["columns"]],
            "rows": [[cell["value"] for cell in row] for row in p["data"]],
        }

    # ---- CSV upload (structured table ingest) ----
    def upload_csv(
        self,
        domain_id: str,
        csv_path: str,
        *,
        table_name: str | None = None,
    ) -> str:
        """Load a local CSV as a new warehouse table on an existing domain.

        Despite ``upload_document`` being unimplemented, *structured* CSV ingest
        IS available: this generates a signed URL, PUTs the bytes, then calls
        ``processCsv(domainOperation=REUSE)``. Returns the new ``tableId``.

        Column names are sanitized server-side (spaces/symbols -> underscores,
        e.g. ``100% Items`` -> ``_100__Items``). Reverse with
        ``delete_csv_table``. ``table_name`` overrides the filename used as the
        CSV/table label.
        """
        with open(csv_path, "rb") as f:
            content = f.read()
        filename = (table_name or os.path.basename(csv_path)).removesuffix(".csv") + ".csv"
        signed = self.request(
            ops.GENERATE_CSV_UPLOAD_URLS,
            {"filenames": [filename]},
            op_name="generateSignedUrlsForCSVUpload",
        )["generateSignedUrlsForCSVUpload"][0]
        headers = {"Content-Type": "text/csv"}
        if signed["bucketType"] == "AZURE_BLOB_STORAGE":
            headers["x-ms-blob-type"] = "BlockBlob"
        put = self._http.put(signed["signedUrl"], content=content, headers=headers)
        put.raise_for_status()
        data = self.request(
            ops.PROCESS_CSV,
            {
                "data": {
                    "csvName": filename,
                    "csvKey": signed["key"],
                    "domainOperation": "REUSE",
                    "domainReuse": {"domainId": domain_id},
                }
            },
            op_name="processCsv",
        )
        return data["processCsv"]["tableId"]

    def delete_csv_table(self, table_id: str, domain_id: str, raw_file_path: str) -> bool:
        """Delete a user-uploaded CSV table. ``raw_file_path`` is the upload
        ``key`` returned during ``upload_csv`` (required by the API)."""
        data = self.request(
            ops.DELETE_CSV_TABLE,
            {"id": table_id, "domainId": domain_id, "rawFilePath": raw_file_path},
            op_name="deleteUnstructuredCsvTable",
        )
        return bool(data["deleteUnstructuredCsvTable"])

    # ---- reviewed queries (question + SQL pairs that teach the domain) ----
    def list_reviewed_queries(
        self, domain_id: str, *, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        data = self.request(
            ops.GET_REVIEWED_QUERY_ITEMS,
            {"domainId": domain_id, "limit": limit, "offset": offset, "draftId": None},
            op_name="getReviewedQueryItems",
        )
        return data["getReviewedQueryItems"]["nodes"]

    def add_sql_reviewed_queries(
        self, domain_id: str, items: list[dict], *, dialect: str = "duckdb", connection_id: str | None = None
    ) -> list[dict]:
        """Create reviewed queries from question+SQL pairs.

        Each item: ``{"query": "<natural-language question>", "sql": "<SQL>"}``
        (``dialect`` / ``connectionId`` keys per item override the defaults).
        ``connectionId`` became required on 2026-10-12 (``ReviewedQuerySqlItem``):
        pass the warehouse connection the SQL runs against. Returns the created
        ``ReviewedQueryItem`` summaries.
        """
        payload = []
        for it in items:
            cid = it.get("connectionId") or connection_id
            if not cid:
                raise WisdomAIError("add_sql_reviewed_queries needs connection_id (ReviewedQuerySqlItem.connectionId is required)")
            payload.append({"query": it["query"], "sql": it["sql"], "dialect": it.get("dialect", dialect), "connectionId": cid})
        data = self.request(
            ops.ADD_SQL_REVIEWED_QUERY_ITEMS,
            {"domainId": domain_id, "reviewedQuerySqlQueries": payload, "draftId": None},
            op_name="addSqlReviewedQueryItems",
        )
        return data["addSqlReviewedQueryItems"]

    def delete_reviewed_queries(self, domain_id: str, ids: list[str]) -> int:
        """Delete reviewed-query items by id. Returns the count deleted."""
        data = self.request(
            ops.DELETE_REVIEWED_QUERY_ITEMS,
            {"ids": ids, "domainId": domain_id, "draftId": None},
            op_name="deleteReviewedQueryItems",
        )
        return data["deleteReviewedQueryItems"]

    # ---- knowledge extraction + modeling suggestions (the "context extractor") ----
    # Undocumented; introspected. The extractor proposes MMSuggestion items you
    # then apply. NB the suggestion `task.type` reads back prefixed
    # (`MM_SUGGESTION_TASK_TYPE_X`) but the INPUT enum on create/patch wants the
    # bare `X`. `create_modeling_suggestion` returns only a bool — re-fetch via
    # `modeling_suggestions` to get the new id, then `apply_modeling_suggestions`.
    def knowledge_extraction_runs(
        self, domain_id: str, *, limit: int = 20, offset: int = 0
    ) -> list[dict]:
        """List context-extraction runs (the jobs that mine an uploaded spec/file
        into knowledge/metric/description suggestions)."""
        data = self.request(
            ops.KNOWLEDGE_EXTRACTION_RUNS,
            {"domainId": domain_id, "limit": limit, "offset": offset},
            op_name="knowledgeExtractionRuns",
        )
        return data["knowledgeExtractionRuns"]["runs"]

    def modeling_suggestions(
        self,
        domain_id: str,
        *,
        include_all_statuses: bool = True,
        job_run_id: str | None = None,
    ) -> list[dict]:
        """Return modeling/context suggestions (knowledge, column/table
        descriptions, metrics, formulas, joins, reviewed queries) with their
        `id`, `status` (PENDING/ACCEPTED/DECLINED/SKIPPED), `source`, and `task`.
        Pass these ids to `apply_modeling_suggestions`."""
        data = self.request(
            ops.GET_MODELING_SUGGESTIONS,
            {
                "domainId": domain_id,
                "includeAllStatuses": include_all_statuses,
                "jobRunId": job_run_id,
                "draftId": None,
            },
            op_name="modelingSuggestion",
        )
        return data["modelingSuggestion"]["nodes"]

    def apply_modeling_suggestions(self, domain_id: str, suggestion_ids: list[str]) -> list[dict]:
        """Apply suggestions by id — routes each through its proper channel
        (knowledge add, column description, metric, join, …). Returns
        `[{suggestionId, success, errorMessage}]`. Reverse with
        `undo_modeling_suggestions`."""
        data = self.request(
            ops.APPLY_MODELING_SUGGESTIONS,
            {"domainId": domain_id, "suggestionIds": suggestion_ids, "draftId": None},
            op_name="applyModelingSuggestions",
        )
        return data["applyModelingSuggestions"]

    def undo_modeling_suggestions(self, domain_id: str, suggestion_ids: list[str]) -> list[dict]:
        """Reverse previously-applied suggestions by id."""
        data = self.request(
            ops.UNDO_MODELING_SUGGESTIONS,
            {"domainId": domain_id, "suggestionIds": suggestion_ids},
            op_name="undoModelingSuggestions",
        )
        return data["undoModelingSuggestions"]

    def create_modeling_suggestion(
        self,
        domain_id: str,
        task: dict,
        *,
        source: str = "MM_SUGGESTION_SOURCE_MODEL_DERIVED",
    ) -> bool:
        """Author a new suggestion (e.g. a metric or join) to then apply.

        `task` is an `MMSuggestionTaskInput`: `{"type": "ADD_MISSING_JOINS",
        "addMissingJoin": {...}}` or `{"type": "ADD_LEARNED_METRIC",
        "addLearnedMetric": {...}}`. **Use the BARE task-type enum** (no
        `MM_SUGGESTION_TASK_TYPE_` prefix). Returns True; re-fetch via
        `modeling_suggestions` to get the new id, then apply it.
        """
        data = self.request(
            ops.CREATE_MODELING_SUGGESTION,
            {"domainId": domain_id, "task": task, "source": source},
            op_name="createModelingSuggestion",
        )
        return bool(data["createModelingSuggestion"])

    def patch_modeling_suggestion(self, data: dict) -> bool:
        """Edit a suggestion in place before applying (e.g. fix a metric
        expression). `data` is an `MMSuggestionInput`: `{id, status, source,
        task}` — again, bare task-type enum. Returns True."""
        out = self.request(
            ops.PATCH_MODELING_SUGGESTION, {"data": data}, op_name="patchModelingSuggestion"
        )
        return bool(out["patchModelingSuggestion"])

    # ---- documents / files (TODO: not in public API) ----
    def upload_document(self, *args, **kwargs):
        """Upload an *unstructured* document/file as context for a domain.

        NOT IMPLEMENTED — the API exposes no unstructured-document upload. (For
        *structured* CSV-as-table ingest, use `upload_csv()`, which is wired up.)
        Unstructured files reach a domain via a connector (SharePoint, S3, Azure
        Blob), surfaced as `DomainModel.datasets`.

        To add programmatic file ingestion you'd need to either:
          1. Use an existing storage connector (upload to S3 / SharePoint, then
             ensure the connector has indexed the new file via `refresh_connection`).
          2. Get access to a private upload endpoint from WisdomAI (the public
             OpenAPI spec at /api-reference/openapi.json was 404 when checked).
        """
        raise NotImplementedError(
            "Direct document upload is not exposed by the WisdomAI GraphQL API. "
            "Use a storage connector (S3, SharePoint, Azure Blob) and "
            "refresh_connection() instead, or contact WisdomAI for a private endpoint."
        )
