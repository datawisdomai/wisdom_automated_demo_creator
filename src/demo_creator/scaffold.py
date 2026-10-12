"""`demo new <name>` — an empty demo folder with a commented demo.yaml skeleton."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from .config import DEMOS_DIR

TEMPLATE = """name: {name}
title: {title}
vertical: {vertical}
as_of: {today}
data_start: {start}
seed: {seed}
inputs: []

persona:
  primary:
  secondary: []
  kpis: []

snowflake:
  database: {db}
  schema: {schema}
  ddl: 01_snowflake_ddl.sql
  load_order: []        # FK order; every CREATE TABLE in the DDL must appear
  views: []
  expected_rows: {{}}    # filled after the first `demo generate`

generator:
  module: generator.py  # must define generate_all() -> dict[TABLE, DataFrame]
  checks: checks.py     # must define run(q, check, spec)
  constants: {{}}

control_points: []      # - {{id: CP1, name: ..., hero: ..., targets: [{{metric: ..., op: ">=", value: ...}}]}}

questions:
  reviewed_queries: reviewed_queries.py
  story_guide: 03_demo_story_guide.md
  opening_questions: 3

documents: []           # - {{spec: docs/<file>.md, kind: contract|report|memo}}

live_app:
  name:
  prompt: live_app_prompt.md
  tabs: [Executive Overview, Scenario Lab, Implementation Plan]

chat:
  followup_question:
  expected_points: []

agent:
  name:
  prompt: agent_prompt.md
  enabled: false

wisdom:
  deployment: proddemo
  workspace_id: ET_WORKSPACE_F01MFB
  connection: {{name: Certified Demos Snowflake}}
  domain_name: {title}
  domain_description:
  dialect: snowflake
  bootstrap: 02_wace_bootstrap.md
  knowledge_csv: knowledge.csv
  metrics_csv: metrics.csv
  reviewed_by:
  lookup_columns: []
  eval: {{run_count: 1, experimental_mode: EXPERIMENTAL_MODE_NONE, pass_threshold: 0.9}}

script:
  template: docs/templates/demo_script_example.md
  output: DEMO_SCRIPT.md
"""


def scaffold_demo(name: str, *, title: str | None = None, vertical: str | None = None) -> Path:
    slug = name.strip().lower().replace(" ", "_")
    d = DEMOS_DIR / slug
    if d.exists():
        raise FileExistsError(f"{d} already exists")
    (d / "inputs").mkdir(parents=True)
    (d / "docs").mkdir()
    today = date.today()
    (d / "demo.yaml").write_text(TEMPLATE.format(
        name=slug, title=title or name, vertical=vertical or "",
        today=today.isoformat(), start=today.replace(year=today.year - 1, month=1, day=1).isoformat(),
        seed=int(today.strftime("%Y%m%d")), db=f"{slug.upper()}_POC", schema="ANALYTICS",
    ))
    (d / "reviewed_queries.py").write_text(
        '"""Reviewed NL -> SQL pairs. NL text must not contain commas."""\n'
        "from demo_creator.reviewed_queries import Registry\n\nrq = Registry()\nadd = rq.add\n\n"
        "# add(\"Which ...?\", 'SELECT ... FROM \"TABLE\" ...')\n"
    )
    return d
