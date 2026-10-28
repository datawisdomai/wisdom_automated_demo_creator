# wisdom_automated_demo_creator

Builds a complete WisdomAI demo from one approved plan. **`/create-demo` is the front door** — when
someone says "build me a demo for X", run that skill. First-time users run `/setup`.

## How a demo gets built (the contract)
1. **Intake** (short): what the demo is for, who the persona is, any material they hand over
   (transcripts, RFPs, notes → `demos/<name>/inputs/`). Pull the vertical's Disco Guide sheet.
2. **One approval**: write `demos/<name>/DEMO_PLAN.md` + `demo.yaml`; present it in plain language;
   iterate until the user says go. Nothing touches Snowflake or Wisdom before that.
3. **Execute autonomously** with self-healing: schema → data → load → context → docs → publish →
   eval → Live App / chat / agent → script + report → **Domain Health analysis last, left running**.
   Each step has a bounded repair loop (3 tries); on exhaustion, stop and explain in plain language.
   The user never has to read SQL.

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
- Evals: **every eval set runs at least 3 times** (`run_count` >= 3; the pipeline enforces the floor, reports the
  mean score and the run group's flaky prompts; `runEvaluation` returns the run-group id and the runs are found
  via `evaluationRuns(evalSetIds)` sharing `runGroupId`); never
  `createEvalsetFromReviewedQueries(runEval=True)`.
- Knowledge de-dups by description; metrics do not — track names in `.state.json`.
- **Federated sources** (`wisdom.federated_sources[]`, see `docs/demo_spec_reference.md`): tables from another
  existing connection (e.g. a partner's read-only Teradata) are attached to the domain by the publish step
  `federated`; that connection is never created/updated/refreshed. Reviewed queries for it use
  `rq.add(..., source="<connection>")`: local checks skip them, `rq-check --domain` runs them via `runSqlQuery` in
  the source dialect, they stay out of the eval set and the extractor's query library, and publish binds them
  directly to that connection (the one exception to extractor-only context, because the extractor cannot bind a
  reviewed query to a second connection). `runSqlQuery` runs on ONE connection; cross-connection joins happen only
  in chat/Live App (Python step), so the federation beat is a chat question, not a view.
- **Skills** (`wisdom.skills[]`, markdown with `name:`/`description:` frontmatter, see `docs/demo_spec_reference.md`): the way to make
  a recurring analysis return the same shape every time (a report grid, a fixed drill order, a governed draft). They enter through the
  extractor's `SKILL` agent from a `runbook` context asset (`UPSERT_SKILL` suggestions, accepted as the `skills` family); publish step
  `skills` creates any listed skill the extractor did not produce and reads all of them back (`domainSkills`). `/<name>` in chat forces one.
  A demo can carry several Live Apps / chats / agents (`live_apps[]`, `chats[]`, `agents[]`).
- **Context enters the domain only through the context extractor** (`wisdom.context_mode: extractor`, the
  default). The local `metrics.csv` / `reviewed_queries.py` / `knowledge.csv` stay the source of truth for
  `rq-check`, `metrics-check` and the eval set, but the domain receives them *disguised* as real assets —
  a dbt semantic-layer YAML, a certified query library `.sql`, an analyst handbook — plus the authored
  `context_assets[]` (glossary, metric standard, wiki page, chat export …). The extraction step accepts the
  knowledge / synonym / metric / reviewed-query suggestions, leaves description rewrites pending for the
  steward-review demo beat, reads back coverage and retries once; it never falls back to CSV uploads.
  Extractor file facts: upload connection id is `files` (attach it first); FileInput needs the GCS/S3
  source from the signed URL; `.yml .yaml .sql .txt .csv .pdf` register, `.md` does not. **Keep extractor files small
  and runs short**: `wisdom.extraction.batch_size: 3` (runs are triggered concurrently, resumed per file); tag duplicative
  reviewed queries `eval_only` so the certified query library stays well under 100 KB (a 308 KB library stalled a run).
- `DEMO_REPORT.md` and `DEMO_SCRIPT.md` always carry **clickable links** (Live App `/apps/<slug>--<app_id>`,
  chat `/chat/<conversation>`, agent `/agents/<id>/edit`, domain `/domains/<id>`, Domain Health tab,
  connection `/connections/<id>`) via `report.links()`; the finish message pastes them. Ids alone are not enough.
- **The last step of every build is `demo health --apply`**: queue the Domain Health analysis and leave it
  running so the SE can demo the suggestions it creates. Never act on them.

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
`agent [--apply]` · `report` · `s3 [--apply]` (stretch: generated contract PDFs → bucket; then `publish --only s3_dataset`) · `health [--apply]` (always last, left running) · `all [--apply] [--redo]` · `status`.
Skills: `/setup`, `/create-demo` (front door), `/run-step` (heal one step), `/demo-script`.
Reference demo: `demos/halcyon/` (migrated from `wisdom demos/halcyon_poc`; same seed, same rows).
