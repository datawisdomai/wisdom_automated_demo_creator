---
name: setup
description: First-run setup for this repo — verify the person's Snowflake PAT, Wisdom API key and Certified Demos workspace access with `demo doctor`, and walk them through any fix. Use when someone is new to the repo, when `demo doctor` fails, or before the first /create-demo.
---

# /setup

Goal: `demo doctor` prints only `OK` lines. Never ask the person to paste a secret into chat; they edit
`.env` themselves.

1. If `.venv` is missing: run `uv venv && uv pip install -e ".[dev]"` (fallback: `python3 -m venv .venv
   && .venv/bin/pip install -e ".[dev]"`).
2. If `.env` is missing: `cp .env.example .env`, then tell them exactly which lines to fill in and
   where each value comes from (PAT command and Wisdom Settings → API Keys are in `.env.example`).
3. Run `.venv/bin/demo doctor --json` and read the checks:
   - `Snowflake connection` FAIL → the PAT is wrong/expired or the role is not allowed; re-issue the PAT
     with `ROLE_RESTRICTION = SYSADMIN`.
   - `workspace 'Certified Demos' visible` FAIL or `connections readable` FAIL → their user must be
     added to that workspace by a Wisdom admin on proddemo. Say so plainly; nothing else will work
     until it is done.
4. Re-run `demo doctor` after each fix. When everything is `OK`, say they can run `/create-demo`.
