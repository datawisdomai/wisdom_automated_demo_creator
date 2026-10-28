"""`demo doctor` — verify a person's setup before any demo work starts.

Each check returns (name, ok, detail, fix). Nothing here writes anywhere and
no secret value is ever included in output.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import config


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    fix: str = ""


def run_checks(deployment: str = "proddemo", *, network: bool = True, spec=None) -> list[Check]:
    checks: list[Check] = []

    env_present = config.load_env()
    checks.append(Check(
        ".env present", env_present,
        str(config.ENV_PATH) if env_present else "missing",
        "cp .env.example .env and fill in your keys",
    ))

    sf = config.snowflake_config()
    checks.append(Check(
        "Snowflake credentials in .env", sf.has_credentials,
        f"user={'set' if sf.user else 'MISSING'} pat={'set' if sf.pat else 'MISSING'} account={sf.account} warehouse={sf.warehouse}",
        "set SNOWFLAKE_USER and SNOWFLAKE_PAT in .env (see .env.example for the PAT command)",
    ))

    try:
        dep = config.wisdom_deployment(deployment)
        key_present = bool(__import__("os").getenv(dep.access_key_env))
        checks.append(Check(
            f"Wisdom key for {deployment} in .env", key_present,
            f"{dep.access_key_env}={'set' if key_present else 'MISSING'}; workspace {dep.workspace_name} ({dep.workspace_id})",
            f"create an API key in Wisdom (Settings -> API Keys) and set {dep.access_key_env} in .env",
        ))
    except Exception as exc:  # registry problems are setup problems too
        checks.append(Check(f"deployment {deployment} in config/deployments.toml", False, str(exc)))
        return checks

    if not network:
        return checks

    # --- Snowflake round trip ---
    if sf.has_credentials:
        try:
            from .snowflake import connect

            with connect(sf, role=sf.ddl_role) as conn:
                row = conn.cursor().execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE()").fetchone()
            checks.append(Check("Snowflake connection", True, f"user={row[0]} role={row[1]} warehouse={row[2]}"))
        except Exception as exc:
            checks.append(Check(
                "Snowflake connection", False, _short(exc),
                "PAT expired/wrong user, or the role cannot be assumed; regenerate the PAT with ROLE_RESTRICTION = SYSADMIN",
            ))

    # --- Wisdom auth + workspace membership ---
    if key_present:
        try:
            client = config.wisdom_client(deployment)
            me = client.current_user()
            checks.append(Check("Wisdom API key authenticates", True, f"as {me.get('email', '?')}"))
            ws = {w["id"]: w["name"] for w in client.workspaces()}
            in_ws = dep.workspace_id in ws
            if spec is not None and spec.wisdom.existing_domain:
                checks.append(_existing_domain_check(client, spec))
            checks.append(Check(
                f"workspace '{dep.workspace_name}' visible", in_ws,
                f"visible workspaces: {', '.join(sorted(ws.values()))}",
                f"ask a Wisdom admin to add your user to the '{dep.workspace_name}' workspace on {deployment}",
            ))
            if in_ws:
                try:
                    conns = client.list_connections(dep.workspace_id)
                    names = [c.name for c in conns]
                    checks.append(Check(
                        "connections readable in workspace", True,
                        f"{len(conns)} connection(s)" + (f": {', '.join(names[:8])}" if names else " (none yet — the pipeline will create one)"),
                    ))
                except Exception as exc:
                    checks.append(Check(
                        "connections readable in workspace", False, _short(exc),
                        f"your user is not a member of '{dep.workspace_name}' — ask a Wisdom admin to add you",
                    ))
        except Exception as exc:
            checks.append(Check("Wisdom API key authenticates", False, _short(exc), "check the key value in .env"))

    return checks


def _existing_domain_check(client, spec) -> Check:
    """An existing_domain demo: the id must resolve in the target workspace and carry the expected name."""
    want, name, ws_id = spec.wisdom.domain_id, spec.wisdom.domain_name, spec.wisdom.workspace_id
    try:
        live = next((d for d in client.list_domains(workspace_id=ws_id, limit=500) if d.get("id") == want), None)
        if live is None:
            return Check("EXISTING domain resolves", False, f"{want} not found in workspace {ws_id}", "check wisdom.domain_id / workspace_id in demo.yaml")
        if str(live.get("name", "")).strip().lower() != str(name).strip().lower():
            return Check("EXISTING domain resolves", False, f"{want} is named '{live.get('name')}', demo.yaml says '{name}'",
                         "fix wisdom.domain_name so the id and name agree")
        dbs = {t["database"] for t in client.domain_table_columns(want)}
        return Check("EXISTING domain resolves", True,
                     f"'{live.get('name')}' ({want}) has {len(dbs)} databases; additive mode will ADD {spec.snowflake.database}, nothing pre-existing is modified")
    except Exception as exc:  # noqa: BLE001
        return Check("EXISTING domain resolves", False, _short(exc), "the key must be able to read the domain")


def _short(exc: Exception) -> str:
    text = str(exc).replace("\n", " ")
    return f"{type(exc).__name__}: {text[:200]}"
