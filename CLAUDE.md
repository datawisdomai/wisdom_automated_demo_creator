# wisdom_automated_demo_creator

Builds a complete WisdomAI demo from one approved plan. **`/create-demo` is the front door** — when
someone says "build me a demo for X", run that skill. First-time users run `/setup`.

## How a demo gets built (the contract)
1. **Intake** (short): what the demo is for, who the persona is, any material they hand over
   (transcripts, RFPs, notes → `demos/<name>/inputs/`). Pull the vertical's Disco Guide sheet.
2. **One approval**: write `demos/<name>/DEMO_PLAN.md` + `demo.yaml`; present it in plain language;
   iterate until the user says go. Nothing touches Snowflake or Wisdom before that.
3. **Execute autonomously** with self-healing: schema → data → load → context → docs → publish →
   eval → Live App / chat / agent → script + report. Each step has a bounded repair loop (3 tries);
   on exhaustion, stop and explain in plain language. The user never has to read SQL.

Writes after approval are pre-authorised **only** inside the demo's own Snowflake database and its
own Wisdom domain in the configured workspace. Anything destructive outside that (deleting a domain,
dropping a database, touching another workspace) is announced and confirmed first.

## Where things are
- `config/deployments.toml`, `config/snowflake.toml` — committed, non-sensitive (tenant, workspace
  "Certified Demos" `ET_WORKSPACE_F01MFB`, Snowflake account/warehouse/roles).
- `.env` — per-person secrets only (`SNOWFLAKE_USER`, `SNOWFLAKE_PAT`, `proddemo_key`). Never print,
  log, or commit them. `.env.example` is the template.
- `src/wisdomai/` — GraphQL client (`Client.for_deployment("proddemo")`); `examples/wisdomai/` — scripts.
- `src/demo_creator/` — pipeline library + `demo` CLI (every command takes `--json`).
- `demos/<name>/` — one folder per demo; `build/` is regenerable; `.state.json` records ids/steps.
- `docs/methodology/` — the POC Domain Build Guide (5 phases, Prompts A–F), WisdomAI's Domain Build
  Guide (7 phases), and the Value Drivers / Disco Guides workbook. `docs/templates/` — the demo
  script, Live App prompt and agent prompt patterns.

## Wisdom API rules (carried over from wisdom_api_access)
- The live schema is the source of truth: `examples/wisdomai/introspect_schema.py proddemo --grep X`
  / `--type Y` before using any operation; docs cover ~60%.
- Add an operation = raw GraphQL in `src/wisdomai/operations.py` → thin `Client` method requesting
  only needed fields → status check → **read-back verification** → covered by `check_drift.py`.
- Always pass `workspace_id` (proddemo has several workspaces; `default_workspace_id()` raises).
  403 on `connections`/`domains` for a workspace = the key's user is not a member.
- Reviewed queries: `dialect="snowflake"`; NL text must not contain commas (CSV import).
- `run_sql(..., dialect="snowflake", database_name=<DB>)` ~5 s/query; `tablePreview.totalRows` is wrong.
- Evals: `run_count=1` (more returns a run-group id you cannot poll); never
  `createEvalsetFromReviewedQueries(runEval=True)`.
- Knowledge de-dups by description; metrics do not — track names in `.state.json`.

## Snowflake rules
- One database per demo (`<NAME>_POC`), one schema; `CREATE OR REPLACE`; `COMMENT` on every table and
  column; `V_` views; a `DATA_DICTIONARY` table; never positional `GROUP BY` in views.
- Load with `write_pandas` (dates → `datetime64[ns]`, drop all-null columns, `use_logical_type=True`,
  `overwrite=True`); column names must match the DDL exactly.
- Validate control points in DuckDB **before** loading, then again in Snowflake after.

## `demo` command cheat-sheet (all take `<name>` and `--json`; writes need `--apply`)
`doctor` · `new` · `generate` · `schema-diff` · `validate [--snowflake]` · `rq-check [--snowflake]` ·
`metrics-check` · `ddl [--apply] [--start-at N] [--grants]` · `load [--apply] [--tables ...]` · `docs` ·
`publish [--apply] [--only ...]` · `eval [--report-last]` · `health [--apply]` · `app [--apply]` · `chat [--apply] [--question ...]` ·
`agent [--apply]` · `report` · `all [--apply] [--redo]` · `status`.
Skills: `/setup`, `/create-demo` (front door), `/run-step` (heal one step), `/demo-script`.
Reference demo: `demos/halcyon/` (migrated from `wisdom demos/halcyon_poc`; same seed, same rows).
