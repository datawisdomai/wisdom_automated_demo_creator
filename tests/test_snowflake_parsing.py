from demo_creator.snowflake import parse_ddl_tables, render_grants, schema_diff, split_statements
import pandas as pd

DDL = """
-- header comment; with a semicolon
USE ROLE SYSADMIN;
CREATE OR REPLACE TABLE CUSTOMERS (
    CUSTOMER_ID VARCHAR(20) COMMENT 'id; with semicolon',
    NAME VARCHAR(200) COMMENT 'it''s quoted',
    REGION VARCHAR(50)
) COMMENT = 'customers';
CREATE OR REPLACE TABLE ORDERS (
    ORDER_ID VARCHAR(20),
    CUSTOMER_ID VARCHAR(20) REFERENCES CUSTOMERS(CUSTOMER_ID),
    AMOUNT NUMBER(12,2),
    CONSTRAINT FK_X FOREIGN KEY (CUSTOMER_ID) REFERENCES CUSTOMERS (CUSTOMER_ID)
);
/* block; comment */
CREATE OR REPLACE VIEW V_ORDERS COMMENT = 'v' AS SELECT * FROM ORDERS
"""


def test_split_statements_respects_quotes_and_comments():
    stmts = split_statements(DDL)
    assert len(stmts) == 4
    assert stmts[0].endswith("USE ROLE SYSADMIN")
    assert "it''s" in stmts[1]
    assert stmts[3].startswith("CREATE OR REPLACE VIEW")


def test_parse_ddl_tables_columns_and_fks():
    tables = parse_ddl_tables(DDL)
    assert tables["CUSTOMERS"].columns == ["CUSTOMER_ID", "NAME", "REGION"]
    assert tables["ORDERS"].columns == ["ORDER_ID", "CUSTOMER_ID", "AMOUNT"]
    assert ("CUSTOMER_ID", "CUSTOMERS", "CUSTOMER_ID") in tables["ORDERS"].foreign_keys


def test_schema_diff_flags_extra_columns_as_errors():
    frames = {"CUSTOMERS": pd.DataFrame(columns=["customer_id", "name", "region", "EXTRA"]),
              "ORDERS": pd.DataFrame(columns=["ORDER_ID", "CUSTOMER_ID"])}
    findings = schema_diff(DDL, frames)
    levels = {(f["table"], f["level"]) for f in findings}
    assert ("CUSTOMERS", "error") in levels
    assert ("ORDERS", "warn") in levels


def test_render_grants_mentions_schema_and_role():
    sql = render_grants("X_POC", "OPS", "COMPUTE_WH", "WISDOMAI_READ_ONLY")
    assert "X_POC.OPS" in sql and "FUTURE VIEWS" in sql
    assert len(split_statements(sql)) == 7
    assert len(split_statements(render_grants("X_POC", "OPS", "COMPUTE_WH", create_role=True))) == 8


def test_session_statements_detected():
    from demo_creator.snowflake import is_session_statement
    assert is_session_statement("-- c\nUSE SCHEMA X.Y")
    assert is_session_statement("ALTER SESSION SET TIMEZONE = 'UTC'")
    assert not is_session_statement("CREATE OR REPLACE TABLE T (A INT)")
