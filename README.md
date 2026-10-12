# wisdom_automated_demo_creator

Open this repo in Claude Code, say what demo you need, approve one plan, and get back a working
WisdomAI demo: Snowflake synthetic data with engineered story arcs (plus PDFs when relevant), a
Wisdom domain with context/metrics/reviewed queries, a Live App (Executive Overview → Scenario Lab →
Implementation Plan), an answered follow-up chat, a disabled agent, and a 5-minute demo script.

## Onboarding (about 10 minutes)
1. **Python**: `uv venv && uv pip install -e ".[dev]"` (or `python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"`).
2. **Secrets**: `cp .env.example .env` and fill in
   - `SNOWFLAKE_USER` / `SNOWFLAKE_PAT` — your own user and a Programmatic Access Token created with
     `ALTER USER <YOU> ADD PROGRAMMATIC ACCESS TOKEN demo_creator ROLE_RESTRICTION = SYSADMIN;`
   - `proddemo_key` — a WisdomAI API key (Settings → API Keys) on proddemo.
3. **Workspace access**: ask a Wisdom admin to add your user to the **Certified Demos** workspace on
   proddemo. Until then every call to that workspace returns 403.
4. **Check**: `.venv/bin/demo doctor` (or `/setup` inside Claude Code) must show all `OK`.
5. **Build a demo**: in Claude Code run `/create-demo` and describe the prospect/vertical. Drop any
   transcripts or RFPs in the chat or in `demos/<name>/inputs/`.

Everything non-sensitive (Snowflake account, warehouse, roles, workspace id) is committed in
`config/`; nothing in `.env` is ever committed.

## Layout
See `CLAUDE.md` for the full map. Short version: `src/wisdomai` (API client), `src/demo_creator`
(pipeline + `demo` CLI), `demos/<name>/` (one folder per demo), `docs/` (methodology + templates).
