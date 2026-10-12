# `demo.yaml` reference

One file per demo at `demos/<name>/demo.yaml`. It is the contract between what Claude writes (DDL,
generator, checks, bootstrap, questions, prompts) and what the `demo` CLI executes. Dates are
`YYYY-MM-DD`; table/view names are upper-cased on load.

| Field | Required | Meaning |
|---|---|---|
| `name` | yes | folder name and CLI key |
| `title` | yes | fictional company / demo title (prospect-safe) |
| `vertical` | no | Disco Guide sheet to use ("Transportation", "Healthcare Provider", …) |
| `as_of` | yes | the demo's "today"; every relative question resolves against it |
| `data_start` | yes | first date in the data |
| `seed` | yes | integer; the whole dataset is a pure function of it |
| `inputs` | no | files the user supplied, stored under `inputs/` |
| `persona.primary/secondary/kpis` | yes | who the demo is for and what they are measured on |
| `snowflake.database/schema` | yes | one database per demo (`<NAME>_POC`) |
| `snowflake.ddl` | yes | DDL file; must create the database, schema, every table and view |
| `snowflake.load_order` | yes | FK order; must list every `CREATE TABLE` in the DDL |
| `snowflake.views` | yes | every `CREATE VIEW` in the DDL |
| `snowflake.expected_rows` | yes after first generate | exact row counts; `generate` and `load` verify them |
| `generator.module` | yes | python file defining `generate_all() -> dict[TABLE, DataFrame]` |
| `generator.checks` | yes | python file defining `run(q, check, spec)` with the control-point assertions |
| `generator.constants` | no | hero ids, story dates; exposed as `spec.constants` |
| `control_points[]` | yes | `id`, `name`, optional `hero`, `targets[{metric, op, value}]`; every id must appear in `checks.py` |
| `questions.reviewed_queries` | yes | python file that fills a `Registry` (NL → SQL, no commas in NL) |
| `questions.story_guide` | no | markdown walk-through with expected answers |
| `questions.opening_questions` | no | how many of the first reviewed queries `demo chat` asks as warm-up |
| `documents[]` | no | `{spec: docs/<file>.md, kind}` rendered to PDF and uploaded to the domain |
| `live_app.name/prompt/tabs` | yes | Live App created from `prompt`; `tabs` are verified on read-back |
| `chat.followup_question/expected_points` | yes | the complex follow-up asked in a visible conversation and how its answer is judged |
| `agent.name/prompt/enabled` | yes | agent created from `prompt`; `enabled: false` means created but never run |
| `wisdom.deployment/workspace_id` | yes | from `config/deployments.toml` (Certified Demos on proddemo) |
| `wisdom.connection.name` | yes | Snowflake connection in that workspace; created if missing |
| `wisdom.domain_name/domain_description/dialect` | yes | domain identity; dialect is `snowflake` |
| `wisdom.bootstrap/knowledge_csv/metrics_csv` | yes | context files; bootstrap sections 7–10 also become knowledge entries |
| `wisdom.lookup_columns` | no | `TABLE.COLUMN` noun columns to enable lookup (NER) on |
| `wisdom.eval` | no | `name`, `run_count` (keep 1), `experimental_mode`; the eval only reports a score, it never gates the build |
| `script.template/output` | yes | demo-script template and output file |
| `manual_steps[]` | no | anything still done by hand; rendered into `DEMO_REPORT.md` |

`demo status <name>` prints spec problems; `.state.json` (committed) holds the ids and step results.
