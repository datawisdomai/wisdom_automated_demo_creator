# wisdom_automated_demo_creator

Open this repo in Claude Code, say what demo you need, approve one plan, and get back a working
WisdomAI demo: Snowflake synthetic data with engineered story arcs, a Wisdom domain whose context
was **learned from realistic assets through the context extractor** (dbt semantic layer, certified
query library, glossary, metric standard, wiki pages, chat exports, PDFs), a Live App (Executive
Overview → Scenario Lab → Implementation Plan), an answered follow-up chat, a disabled agent, a
3-run eval score, a running Domain Health analysis, a 5-minute demo script and a report with
clickable links to all of it.

## Onboarding (about 10 minutes)
1. **Python**: `uv venv && uv pip install -e ".[dev]"` (or `python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"`).
2. **Secrets**: `cp .env.example .env` and fill in
   - `SNOWFLAKE_USER` / `SNOWFLAKE_PAT` — your own user and a Programmatic Access Token created with
     `ALTER USER <YOU> ADD PROGRAMMATIC ACCESS TOKEN demo_creator ROLE_RESTRICTION = SYSADMIN;`
   - `proddemo_key` — a WisdomAI API key (Settings → API Keys) on proddemo.
3. **Workspace access**: builds publish to the workspace named in `demo.yaml`
   (`wisdom.workspace_id`); the default from `config/deployments.toml` is **Certified Demos**, and
   `demos/keelstone` shows a build targeted at **Default Organization**. Your user must be a member of
   the target workspace or every call there returns 403.
4. **Check**: `.venv/bin/demo doctor` (or `/setup` inside Claude Code) must show all `OK`.
5. **Build a demo**: in Claude Code run `/create-demo` and describe the prospect/vertical. Drop any
   transcripts or RFPs in the chat or in `demos/<name>/inputs/`.

Everything non-sensitive (Snowflake account, warehouse, roles, workspace id) is committed in
`config/`; nothing in `.env` is ever committed.

## What a build does (the contract)
Intake → one approved `DEMO_PLAN.md` → autonomous execution with bounded self-healing:
schema → data → load → context files → docs → publish → eval (3 runs minimum) → Live App → chat →
agent → script + report → **Domain Health analysis last, left running** for the SE. Full rules in
`CLAUDE.md`; the step-by-step is `/create-demo`, single-step repair is `/run-step`.

Three house rules every build follows:
- **Context enters the domain only through the context extractor.** The local `metrics.csv`,
  `reviewed_queries.py` and `knowledge.csv` are the source of truth for checks and the eval, but the
  domain receives them disguised as real assets (a dbt semantic-layer YAML, a certified query
  library `.sql`, an analyst handbook) next to the authored `context_assets[]`. No CSV uploads.
- **Evals run at least 3 times**; the mean score and flaky prompts are reported, never chased.
- **Links, not ids.** `DEMO_REPORT.md` and `DEMO_SCRIPT.md` carry clickable URLs for the Live App,
  chat, agent, domain and Domain Health page.

## Shared Snowflake connection
Demos reuse an existing Wisdom connection by name (`wisdom.connection.name`). If the connection is
not yours (for example "Snowflake Demo", which logs in as the service user `WISDOMAI_PROD`), add the
new `<NAME>_POC` database to its database filter **in the Wisdom UI**, then let the pipeline refresh
and attach it. Only set `WISDOM_CONNECTION_SNOWFLAKE_*` in `.env` when you own the connection: the
pipeline re-sends those credentials when it extends a filter itself.

## Layout
See `CLAUDE.md` for the full map. Short version: `src/wisdomai` (GraphQL client + operations),
`src/demo_creator` (pipeline + `demo` CLI; `context_assets.py` renders the extractor assets),
`demos/<name>/` (one folder per demo; `build/` is regenerable and ignored, `.state.json` records
ids and step results), `docs/` (methodology, spec reference, templates), `examples/wisdomai/`
(API scripts; `introspect_schema.py` and `check_drift.py` keep the client honest).

Reference demos: `demos/halcyon` (specialty pharma distribution) and `demos/keelstone` (storage
vendor, governed self-service, extractor-based context assets under `docs/`). Both were built before
the extractor-only rule and are marked `context_mode: direct`; new builds default to `extractor`.

## Day-to-day commands
`demo <cmd> <name> [--json]`; writes need `--apply`. `doctor` · `new` · `generate` · `validate
[--snowflake]` · `rq-check [--snowflake]` · `metrics-check` · `ddl [--apply] [--grants]` · `load
[--apply]` · `docs` · `publish [--apply] [--only …]` · `eval [--report-last]` · `app` · `chat` ·
`agent` · `report` · `health [--apply]` (always last) · `all [--apply]` · `status` · `teardown`.
Tests: `.venv/bin/python -m pytest -q -m "not slow"`.
