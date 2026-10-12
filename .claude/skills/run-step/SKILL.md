---
name: run-step
description: Run or re-run ONE pipeline step for a demo (schema, data, load, context, docs, publish, eval, app, chat, agent, script) with the self-healing rules — bounded repair loops, what to fix and what never to touch. Use when a step of /create-demo failed, when the user asks to redo a step, or to resume after a fix.
---

# /run-step <demo> <step>

Always run commands as `.venv/bin/demo <cmd> <demo> --json` and read the JSON. Each step gets **at most
3 repair attempts**; after that stop, show the last error in plain language, and ask the user how to
proceed. Report progress in one line per attempt ("Schema: statement 41 failed (positional GROUP BY in
V_FILL_RATE) → fixed, resuming from 41").

Never: print or paste secrets; change the demo's `seed`, `as_of`, or a control point's target numbers
to make a check pass (that needs the user's say-so); edit generated data to make a reviewed query pass
(fix the SQL); run `--apply` outside the demo's own database/domain; delete anything without asking.

## schema — `demo ddl <demo> --apply`
Success: `ok: true`. On failure the JSON has `failure.{index, preview, error, statement}`.
Fix the **statement** in `01_snowflake_ddl.sql`, then resume with `--start-at <index>` (earlier
statements already ran). Common errors and fixes:
- `invalid identifier` in a view → a column name that does not exist on the table/view it reads; check
  the CREATE TABLE above it and fix the reference (do not invent columns in the table).
- `GROUP BY` complaints with numbers → positional GROUP BY; list the expressions explicitly.
- `unexpected '...'` syntax → unbalanced quotes in a COMMENT (double any `'` inside), a trailing comma,
  or a Snowflake-unsupported type (use VARCHAR/NUMBER/DATE/TIMESTAMP_NTZ/BOOLEAN/FLOAT).
- `does not exist or not authorized` on a table → view ordering: views must follow the tables they read
  and other views they reference.
- `primary or unique key does not exist for the columns referenced by the foreign key` → the parent
  table needs `PRIMARY KEY (<col>)`; add it to the parent's CREATE TABLE and resume from the parent.
- Always resume from the index that failed (the JSON says which); a later index skips the fix and the
  CLI refuses it.
- `Insufficient privileges` → stop; the person's PAT role cannot create databases (see /setup).
After success run `demo schema-diff <demo>` if data already exists, and fix any `error` finding before load.

## data — `demo generate <demo>` then `demo validate <demo>`
`generate` fails on: missing frame for a table in `load_order` (add it to `generate_all()`), a column
present in data but not in the DDL (rename in the generator or add the column to the DDL and re-run
schema), or `expected_rows` mismatch. For a NEW demo set `expected_rows` to the generated counts once
the data is right; for an existing demo a mismatch means the generator changed — investigate.
`validate` FAIL on a control-point check → the story is not in the data strongly enough: adjust the
generator's injection (rates, dates, hero ids in `generator.constants`), regenerate, re-validate. A
built-in FK orphan failure → the generator creates child rows for parents that do not exist. A view
that does not compile in DuckDB but did in Snowflake → the view uses Snowflake-only syntax; prefer
portable SQL (ANSI CASE/CAST, `DATE 'YYYY-MM-DD'`, no `::` casts, no `IFF`, no `DATEDIFF('day',...)`
— use `(d2 - d1)` or `DATE_DIFF('day', d1, d2)` which both engines accept).

## load — `demo load <demo> --apply`, then `demo validate <demo> --snowflake`
A failed table lists in `failures[]`; re-run with `--tables A B`. `write_pandas` type errors → a column
whose DDL type disagrees with the data (e.g. strings into NUMBER); fix the DDL type (then schema
`--start-at` that statement) or the generator. Count mismatch → reload that table. If the Snowflake
validation fails where DuckDB passed, the SQL in `checks.py` is dialect-sensitive; make it portable.

## context — `demo rq-check <demo> --snowflake` and `demo metrics-check <demo>`
`error` → fix the SQL in `reviewed_queries.py` (never the data); `empty` → the question's filter does
not match the data (dates, spellings, ids) — fix the SQL or, if the question itself is wrong for this
story, replace the question. A comma in a question → reword it. Bootstrap facts that name columns that
do not exist (Prompt F) → fix the bootstrap. A metric that does not compile → fix its SQL or view name.

## docs — `demo docs <demo>`
Rendering errors name the markdown file and line; fix the markdown (tables need a header row).

## publish — `demo publish <demo> --apply`
Each sub-step reads back what it created. `permission` errors → stop and tell the user the key's user
is not in the workspace (/setup). Other GraphQL errors → read the message, fix the input (e.g. a
knowledge entry over the length limit, a metric SQL Wisdom rejects), re-run; publish is idempotent.

## eval — `demo eval <demo>`
The eval is a report, not a gate: run it, record the score in `.state.json` / `build/eval_results.json`,
and mention the score and any failing prompts in the final summary. Do **not** change context or
re-run to chase the score unless the user asks. `--report-last` reports the last completed run.

## health — `demo health <demo> --apply`
Queues a Domain Health analysis run and records the job id. Report-only: never apply or act on its
suggestions. If it says `alreadyQueued`, that is fine.

## app / chat / agent — `demo app|chat|agent <demo> --apply`
app: fewer tabs than `live_app.tabs` → tighten the prompt (name each page explicitly), recreate.
chat: the answer misses `chat.expected_points` → add knowledge/reviewed queries that make the point
answerable, publish, re-ask in a NEW conversation. agent: must end disabled — if the read-back says
enabled, disable it; if the API path is unavailable, use the Claude-in-Chrome skill with the same prompt
and record the ids in `.state.json` the same way.

## script — `/demo-script <demo>`
Regenerates `DEMO_SCRIPT.md` from the template and `.state.json`; no repair loop.
