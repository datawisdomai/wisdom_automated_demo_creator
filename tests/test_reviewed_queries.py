import csv
import pytest

from demo_creator.reviewed_queries import Registry, check_queries, pretty_sql, to_eval_items


def test_registry_rejects_commas_and_duplicates():
    rq = Registry()
    rq.add("How many orders?", "SELECT COUNT(*) FROM ORDERS;")
    assert rq.queries[0].sql == "SELECT COUNT(*) FROM ORDERS"
    with pytest.raises(ValueError):
        rq.add("Orders, by region?", "SELECT 1")
    with pytest.raises(ValueError):
        rq.add("How many orders?", "SELECT 2")


def test_check_queries_reports_empty_and_errors():
    rq = Registry()
    rq.add("ok", "SELECT 1")
    rq.add("empty", "SELECT 1 WHERE 1=0")
    rq.add("broken", "SELEC 1")
    import duckdb
    con = duckdb.connect()
    results = check_queries(rq, lambda s: con.execute(s).fetchall(), echo=False)
    assert [r.status for r in results] == ["ok", "empty", "error"]


def test_pretty_sql_and_eval_items():
    rq = Registry()
    rq.add("q", 'select a from "T" where b=1')
    assert "FROM" in pretty_sql(rq.queries[0].sql)
    assert to_eval_items(rq)[0]["prompt"] == "q"
