---
name: create-demo
description: Build a complete WisdomAI demo from a short brief — the front door of this repo. Use whenever someone asks to build, create, make, spin up or scaffold a demo, POC environment, demo domain or demo data for a prospect, customer or vertical. Runs intake → one approved Demo Plan → autonomous self-healing execution → finished demo kit (Snowflake data, Wisdom domain, Live App, answered chat, disabled agent, 5-minute script).
---

# /create-demo

You are building a demo the way the WisdomAI SE team does it, but the person only reviews ONE
document (the Demo Plan). After they approve it you run everything, repair what breaks (bounded, see
/run-step), and come back with the finished kit. Never ask them to read SQL or run commands.

Commands are `.venv/bin/demo <cmd> <name> [--apply] --json`. Read the JSON. Report progress in plain
one-liners ("Schema created (22 tables, 7 views)", "Data generated and validated: 6/6 story checks pass").

## Phase A — Intake (short)
1. `.venv/bin/demo doctor --json` — if anything fails, run /setup first and stop.
2. Collect what is missing, in one message, at most 5 questions: who the demo is for (prospect,
   vertical, buying persona), the headline problem the persona lives with, any material they have
   (transcripts, RFPs, notes — save pasted text to `demos/<slug>/inputs/`), systems to name-drop,
   names or facts that must not appear. If they gave a transcript, mine it first and only ask what
   it does not answer.
3. Read `docs/methodology/poc_domain_build_guide.md` Phase 1 (research) and the vertical's Disco
   Guide sheet (personas, discovery questions, metrics):
   `.venv/bin/python -c "import openpyxl;wb=openpyxl.load_workbook('docs/methodology/value_drivers_disco_guides.xlsx',read_only=True);ws=wb['Disco Guide <Vertical>'];[print(' | '.join(str(c) for c in r if c)) for r in ws.iter_rows(values_only=True)]"`
   (sheet names: `Disco Guide Fin Serv`, `Insurance`, `Healthcare Payer`, `Healthcare Provider`,
   `Retail`, `eCommerce`, `CPG`, `Manufacturing`, `Energy (Utilities &`, `Energy (Oil & Gas)`,
   `Automotive`, `Technology`, `Hospitality`, `Transportation`, `Media & Entertainme`, `Aerospace`,
   `Higher Ed`).
4. Choose a prospect-safe fictional company and a slug; `.venv/bin/demo new <slug> --title "<Company>" --vertical "<Vertical>"`.

## Phase B — Demo Plan (the one approval)
Write `demos/<slug>/DEMO_PLAN.md` from `docs/templates/DEMO_PLAN_template.md` and fill `demo.yaml`
(see `docs/demo_spec_reference.md`; leave `expected_rows` empty). Design rules:
- 3–5 story arcs with concrete target numbers (the data generator will plant them; `checks.py` will
  assert them). One is the hero arc the Live App, chat question and agent all revolve around.
- 8–14 Snowflake objects: dimensions first, facts in FK order, 4–8 `V_` views that pre-compute the
  KPIs, plus `DATA_DICTIONARY`. One database per demo (`<SLUG>_POC`), one schema.
- Live App = Executive Overview → Scenario Lab → Implementation Plan, built on the views.
- Follow-up question = a genuinely multi-step question about the hero arc, with 3–5 expected points.
- Agent = watches the hero metric on a schedule; created disabled.
- Documents (PDFs) only when the story needs unstructured evidence (a contract, a bulletin, a report).
- When the story needs the same answer every time (a report a BI user must recognise, a fixed investigation order, a
  governed draft), write it as a **skill** (`wisdom.skills[]`, `skills/<name>.md`) and author a `runbook` context asset
  that carries the same procedures so the extractor proposes them; evals then include the `/<name>` prompts.
- A **federated source** (`wisdom.federated_sources[]`: read-only tables from a connection somebody else owns,
  e.g. a partner's Teradata) only when the story needs it; the join to our data happens in chat (the follow-up
  question), never in a view; profile the foreign tables first through `Client.run_sql(<a domain that already
  has them>, ..., dialect=<theirs>, database_name=<theirs>)` and cache any keys the generator must reuse under
  `inputs/ref/` (pattern: `demos/pecos_openinvoice/ref_extract.py`).
Present the plan in plain language (≤ 15 lines) and wait. Iterate until they say go. **Nothing
touches Snowflake or Wisdom before approval.** After approval, do not ask further questions unless a
repair loop is exhausted.

## Phase C — Execute (autonomous)
Keep `.state.json` current (the CLI does); if the session is interrupted, `demo status <slug>` shows
where to resume and `demo all <slug> --apply` skips finished steps.

| # | Do | Then run | Pass when |
|---|---|---|---|
| C1 | Write `01_snowflake_ddl.sql` (Prompt B in the build guide; `COMMENT` on every table and column; `PRIMARY KEY` on every dimension; `REFERENCES` on every FK; views portable to DuckDB — ANSI CASE, `DATE 'YYYY-MM-DD'`, no `::`, no `IFF`, no positional GROUP BY). Fill `snowflake.load_order`/`views`. | `demo ddl --apply` | `ok: true` (heal per /run-step schema) |
| C2 | Write `generator.py` (pattern: `demos/halcyon/generator.py` — `rng(tag)` from `demo_creator.rng`, constants from `demo.yaml`, one builder per table in FK order, `generate_all()` returning `{TABLE: DataFrame}`; realistic distributions; explicit story injection with a comment naming the control point) and `checks.py` (`run(q, check, spec)`; one `check()` per target in every control point, plus a baseline sanity check). | `demo generate` → set `expected_rows` from the counts → `demo validate` | ALL CHECKS PASSED |
| C3 | — | `demo load --apply` → `demo validate --snowflake` | counts match, checks pass in Snowflake |
| C4 | Write `02_wace_bootstrap.md` (10 sections, Prompt D; verify every column name against the DDL — Prompt F), `knowledge.csv` (15–25 one-sentence facts incl. the as-of date and each hero entity), `metrics.csv` (15–35 metrics as `AGG(VIEW.COLUMN)` expressions over the views), `reviewed_queries.py` (25–60 pairs: 5 lookups, 10+ analytical, each story arc as a 3-question chain, the follow-up question itself; no commas in questions; SQL that returns rows). These stay local as the source of truth for checks and the eval; **they never go to the domain as CSVs** — the publish step renders them into a dbt semantic-layer YAML, a certified query library `.sql` and an analyst handbook for the context extractor. Also write 4–7 **authored context assets** under `docs/` and list them in `context_assets[]`: a metric definitions standard, a business glossary with owners/stewards/source systems, a data-platform wiki page, a chat-channel export, plus the story documents (memo, bulletin, playbook). They must read like the real thing, not like a prompt. | `demo rq-check --snowflake` → `demo metrics-check` | all ok |
| C5 | Write `docs/*.md` document specs if the plan has documents (letterhead block, headings, bullets, tables). | `demo docs` | rendered |
| C6 | — | `demo publish --apply` | every publish step ok; the `extraction` step reports coverage (metrics and reviewed queries found in the domain vs. expected ≥ 90%, knowledge count, suggestions accepted / left pending). If coverage is short after its one automatic retry, improve the asset wording or file instructions and re-run `publish --only extraction`; never upload CSVs |
| C7 | — | `demo eval` | eval runs **at least 3 times** and completes (mean score and flaky prompts reported, never chased) |
| C8 | Write `live_app_prompt.md` (from `docs/templates/live_app_prompt_template.md`), `agent_prompt.md` (from `docs/templates/agent_prompt_template.md`), set `chat.followup_question` / `expected_points`. | `demo app --apply` → `demo chat --apply` → `demo agent --apply` | app built; answer hits the expected points; agent is a draft |
| C9 | /demo-script | `demo report` | `DEMO_SCRIPT.md` + `DEMO_REPORT.md` exist |
| C10 | — | `demo health --apply` | **always the last step**: the Domain Health analysis is queued and **left running** so the SE can demo the suggestions it creates. Never act on them, never cancel it |

If a Wisdom step is impossible through the API (the command says so), do that step with the
Claude-in-Chrome skill using the same prompt, then record the ids in `.state.json` and continue.

## Finish
Reply with: what was built (one line each: data, domain, Live App, chat, agent, script), **the clickable
links from the `## Links` block of `DEMO_REPORT.md` pasted in full (Live App, follow-up chat, agent, domain,
Domain Health, connection)** — the user always needs the links, never just ids —, the extraction coverage figures, the Domain Health job id that is
running, anything skipped and why, and the one thing to check before the demo (open the Live App once
so it is cached).
