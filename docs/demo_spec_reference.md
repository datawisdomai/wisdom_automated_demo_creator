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
| `questions.reviewed_queries` | yes | python file that fills a `Registry` (NL → SQL, no commas in NL). `rq.add(nl, sql, tags=("eval_only",))` keeps a query in rq-check and the eval set but out of the certified query library the extractor receives (keep that file small: the extractor stalls on files over ~100 KB) |
| `questions.story_guide` | no | markdown walk-through with expected answers |
| `questions.opening_questions` | no | how many of the first reviewed queries `demo chat` asks as warm-up |
| `documents[]` | no | `{spec: docs/<file>.md, kind}` rendered to PDF and uploaded to the domain |
| `live_app.name/prompt/tabs` | yes | Live App created from `prompt`; `tabs` are verified on read-back |
| `chat.followup_question/expected_points` | yes | the complex follow-up asked in a visible conversation and how its answer is judged |
| `agent.name/prompt/enabled` | yes | agent created from `prompt`; `enabled: false` means created but never run |
| `wisdom.deployment/workspace_id` | yes | from `config/deployments.toml` (Certified Demos on proddemo) |
| `wisdom.connection.name` | yes | Snowflake connection in that workspace; created if missing (`create: false` forbids creating it) |
| `wisdom.federated_sources` | no | List of `{connection, database, tables[], dialect, schema?, description?}`: tables from **another, already existing connection** (e.g. a partner's Teradata) attached read-only to the domain by the publish step `federated` (after `database`). The connection is looked up by name in the workspace and never created, updated or refreshed; the tables are added through the relationship graph and read back; ids land in `.state.json` `wisdom.federated_sources`. Reviewed queries registered with `rq.add(..., source="<connection>")` are skipped by the local checks, kept out of the extractor's query library and the eval set, run by `rq-check --domain` through `runSqlQuery` in the source's dialect/database, and pushed directly to the domain bound to that connection. Demo as-is: `demos/nordmark` (Ali-TD Teradata) |
| `wisdom.existing_domain` / `wisdom.domain_id` | no | **Existing-domain mode**: add this demo's database, context, eval set, app and agent to a domain somebody else built (`domain_id` is required and `domain_name` must match the live name). The domain is never created, renamed or deleted; a connection not created by this demo is never updated; extractor files not uploaded by this demo are never deleted; suggestions pending before the first upload are never accepted; `teardown` keeps the domain |
| `wisdom.instructions_mode` | no | `replace` (default for own domains), `append` (only a `<!-- demo:<name> begin/end -->` block changes) or `skip` (default when `existing_domain`) |
| `wisdom.domain_name/domain_description/dialect` | yes | domain identity; dialect is `snowflake` |
| `wisdom.bootstrap/knowledge_csv/metrics_csv` | yes | context files; bootstrap sections 7–10 also become knowledge entries |
| `wisdom.lookup_columns` | no | `TABLE.COLUMN` noun columns to enable lookup (NER) on |
| `wisdom.context_mode` | no | `extractor` (default): knowledge, metrics and reviewed queries reach the domain **only** through the context extractor, rendered as a dbt semantic-layer YAML, a certified query library `.sql` and an analyst handbook; `direct` is the legacy CSV/API path and must not be used for new builds |
| `wisdom.extraction` | no | `accept` (suggestion families accepted after a run; default `[knowledge, synonyms, metrics, reviewed_queries]` — descriptions stay pending for steward review), `coverage_threshold` (default 0.9 for metrics and reviewed queries found in the domain), `batch_size` (optional: trigger one extraction run per N uploaded files instead of one run for all of them; suggestions are accepted and coverage read once at the end) |
| `context_assets[]` | no | `{spec: docs/<file>, kind: standard|glossary|wiki|chat_export|memo|bulletin|playbook|runbook|query_log|report_definition, instructions?}` authored assets uploaded to the extractor; they carry the story facts in a realistic voice. Markdown kinds are rendered to PDF; `query_log` (a `.sql` shaped like a warehouse query-log export) and `report_definition` (a `.txt` BI report export) are uploaded as the text file itself; `runbook` is the source the extractor's SKILL agent turns into skills |
| `wisdom.skills[]` | no | `{file: skills/<name>.md, availability?: [CHAT, COPILOT, AGENTS]}` domain skills: markdown with `name:` (= file stem, lowercase-hyphenated) and `description:` frontmatter and an instruction body. The extractor proposes skills from a `runbook` asset (`UPSERT_SKILL` suggestions, family `skills`); the publish step `skills` (after `extraction`) creates any listed skill the extractor did not produce, keeps an extractor-made one as is, and reads every one back into `.state.json` `wisdom.skills`. Invoke in chat with `/<name>` |
| `live_apps[]` / `chats[]` / `agents[]` | no | Several Live Apps, answered chats or agents per demo (same fields as `live_app` / `chat` / `agent`, plus an optional `key`; the first entry is the one `live_app` / `chat` / `agent` refer to). `demo app|chat|agent` build them all (or `--app|--chat|--agent <key>`); ids land in `.state.json` `wisdom.apps|chats|agents[<key>]` and the report links each one |
| `wisdom.eval` | no | `name`, `run_count` (minimum 3, enforced; the mean score over the run group is reported with the flaky prompts), `experimental_mode`; the eval only reports a score, it never gates the build |
| `script.template/output` | yes | demo-script template and output file |
| `generated_documents` | no | `{module: <file>.py, out: build/contracts}`: a demo-specific renderer whose `render(spec, out_dir)` builds PDFs from the generated frames (e.g. one signed contract per CONTRACTS row); run by `demo docs` after the markdown specs |
| `s3` | no | `{bucket_env, region_env, prefix_env, subfolder?, connection_name?, dataset_name?}` (set `connection_name` and `dataset_name` explicitly on a shared workspace): names of the `.env` variables holding the bucket, region and key prefix. `demo s3 --apply` uploads the generated PDFs (idempotent); the publish step `s3_dataset` creates a Wisdom S3 connection (key from `WISDOM_S3_*` or `AWS_*` in `.env`), a dataset on the prefix, attaches it to the domain and waits for the crawl |
| `manual_steps[]` | no | anything still done by hand; rendered into `DEMO_REPORT.md` |

`demo status <name>` prints spec problems; `.state.json` (committed) holds the ids and step results.
