"""Federated (read-only, foreign-connection) sources: spec parsing, reviewed-query routing, publish step."""
from pathlib import Path

import yaml

from demo_creator.reviewed_queries import Registry, to_api_items, to_eval_items, pretty_sql
from demo_creator.spec import load_spec, validate_spec


def _write_demo(tmp_path: Path, extra_wisdom: dict) -> Path:
    d = tmp_path / "fed"
    d.mkdir()
    (d / "01_snowflake_ddl.sql").write_text("CREATE OR REPLACE TABLE X (A INT);\n")
    (d / "demo.yaml").write_text(yaml.safe_dump({
        "name": "fed", "title": "Fed", "as_of": "2026-09-30", "data_start": "2024-10-01", "seed": 7,
        "snowflake": {"database": "fed_poc", "schema": "analytics", "load_order": ["X"]},
        "wisdom": {"connection": {"name": "Snowflake Demo", "create": False}, **extra_wisdom},
    }))
    return d


def test_spec_parses_federated_sources(tmp_path):
    d = _write_demo(tmp_path, {"federated_sources": [
        {"connection": "Ali-TD", "database": "wisdomai", "dialect": "teradata",
         "tables": ["RTL_DIM_SUPPLIER", "RTL_FACT_PURCHASE_ORDER_LINE"], "description": "import purchasing"}]})
    spec = load_spec(d)
    f = spec.wisdom.federated_sources
    assert len(f) == 1 and f[0].connection == "Ali-TD" and f[0].dialect == "teradata" and f[0].schema is None
    assert f[0].tables == ["RTL_DIM_SUPPLIER", "RTL_FACT_PURCHASE_ORDER_LINE"]
    assert not [p for p in validate_spec(spec, stage="design") if "federated" in p]


def test_spec_flags_bad_federated_sources(tmp_path):
    d = _write_demo(tmp_path, {"federated_sources": [{"connection": "Snowflake Demo", "database": "OTHER", "tables": []}]})
    problems = validate_spec(load_spec(d), stage="design")
    assert any("lists no tables" in p for p in problems)
    assert any("own connection" in p for p in problems)


def test_registry_routes_federated_queries():
    rq = Registry()
    rq.add("Local sales?", "SELECT 1")
    rq.add("Late purchase orders?", "SELECT TOP 5 supplier_key FROM RTL_FACT_PURCHASE_ORDER_LINE WHERE days_late > 0", source="Ali-TD")
    assert rq.queries[1].federated and "federated" in rq.queries[1].tags
    assert [q.nl for q in rq.local()] == ["Local sales?"]
    assert [q.nl for q in rq.for_source("ali-td")] == ["Late purchase orders?"]
    # eval set only carries the warehouse queries
    assert [it["prompt"] for it in to_eval_items(rq)] == ["Local sales?"]
    # API items for the source carry its connection id and dialect, SQL untouched
    items = to_api_items(rq.for_source("Ali-TD"), "teradata", connection_id="et-connection-1")
    assert items == [{"query": "Late purchase orders?", "sql": rq.queries[1].sql, "dialect": "teradata", "connectionId": "et-connection-1"}]
    assert "connectionId" not in to_api_items(rq.local(), "snowflake")[0]


def test_pretty_sql_passes_non_snowflake_through():
    td = "SELECT TOP 3 x FROM t WHERE d >= DATE '2026-01-01'"
    assert pretty_sql(td, "teradata") == td
    assert "FROM" in pretty_sql("select x from t", "snowflake")


class _FakeClient:
    """Just enough of wisdomai.Client for the federated publish step."""
    def __init__(self):
        self.added: list[list[str]] = []
        self.rqs: list[dict] = []
        self._tables: list[dict] = []

    def find_connection(self, workspace_id, name):
        from wisdomai.client import ConnectionInfo
        return ConnectionInfo(id="et-connection-td", name=name, dialect="teradata") if name == "Ali-TD" else None

    def list_tables(self, domain_id):
        return list(self._tables)

    def database_hierarchy(self, connection_id, database_name):
        return [{"schema": "", "id": f"ET_ZSHEET_{n}", "name": n, "type": "TABLE"} for n in ("RTL_DIM_SUPPLIER", "RTL_DIM_PRODUCT", "OTHER")]

    def add_tables_to_domain(self, domain_id, ids):
        self.added.append(ids)
        self._tables = [{"database": "wisdomai", "name": i.replace("ET_ZSHEET_", ""), "id": i} for i in ids]
        return {}

    def list_reviewed_queries(self, domain_id, limit=500):
        return self.rqs

    def add_sql_reviewed_queries(self, domain_id, items, *, dialect, connection_id):
        self.rqs += [{"question": it["query"], "dialect": it["dialect"], "connectionId": it["connectionId"]} for it in items]
        return items

    def workspaces(self):
        return [{"id": "WS", "name": "Test"}]


def test_publish_federated_step_attaches_and_binds(tmp_path, monkeypatch):
    from demo_creator.manifest import State
    from demo_creator.publish import Publisher

    d = _write_demo(tmp_path, {"workspace_id": "WS", "federated_sources": [
        {"connection": "Ali-TD", "database": "wisdomai", "dialect": "teradata", "tables": ["RTL_DIM_SUPPLIER", "RTL_DIM_PRODUCT"]}]})
    spec = load_spec(d)
    state = State.load(d)
    state.set("wisdom", "domain_id", "ET_DOMAIN_x")
    client = _FakeClient()
    pub = Publisher(spec, state, client, apply=True, echo=False)
    rq = Registry()
    rq.add("Local?", "SELECT 1")
    rq.add("Suppliers?", "SELECT TOP 5 * FROM RTL_DIM_SUPPLIER", source="Ali-TD")
    pub.registry = rq
    rep = pub.attach_federated_sources(wait_s=1)
    assert rep.status == "ok", rep.detail
    assert client.added == [["ET_ZSHEET_RTL_DIM_SUPPLIER", "ET_ZSHEET_RTL_DIM_PRODUCT"]]
    assert client.rqs == [{"question": "Suppliers?", "dialect": "teradata", "connectionId": "et-connection-td"}]
    assert state.wisdom["federated_sources"]["Ali-TD"]["connection_id"] == "et-connection-td"
    # second run: nothing to add, nothing re-bound
    rep2 = pub.attach_federated_sources(wait_s=1)
    assert rep2.status == "ok" and len(client.added) == 1 and len(client.rqs) == 1


def test_publish_federated_step_dry_run_touches_nothing(tmp_path):
    from demo_creator.manifest import State
    from demo_creator.publish import Publisher

    d = _write_demo(tmp_path, {"workspace_id": "WS", "federated_sources": [
        {"connection": "Ali-TD", "database": "wisdomai", "dialect": "teradata", "tables": ["RTL_DIM_SUPPLIER"]}]})
    spec = load_spec(d)
    state = State.load(d)
    state.set("wisdom", "domain_id", "ET_DOMAIN_x")
    client = _FakeClient()
    pub = Publisher(spec, state, client, apply=False, echo=False)
    rep = pub.attach_federated_sources(wait_s=1)
    assert rep.status == "planned" and client.added == [] and "federated_sources" not in state.wisdom
