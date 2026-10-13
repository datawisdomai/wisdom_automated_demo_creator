# Demo Plan: [TITLE]

**Prospect / vertical:** [who this is for] · **Persona:** [primary persona] · **As-of date:** [YYYY-MM-DD]

## The story in one paragraph
[Fictional company], a [what they do]. The [persona] is measured on [KPIs]. The demo shows [headline
problem], finds [the cause], models [the fix] and automates [the watch]. Nothing here names the prospect.

## Story arcs (what the data will prove)
| # | Arc | Hero entity | Target numbers the data will contain |
|---|---|---|---|
| CP1 | [headline arc] | [entity] | [e.g. on-time 86% vs 94% elsewhere; cost/label +9%] |
| CP2 | [second arc] | | |
| CP3 | [third arc] | | |

## Data (Snowflake `[DB]_POC.[SCHEMA]`)
- Dimensions: [4-6 tables]
- Facts: [3-5 tables, ~N rows in the main fact]
- Views: [V_... 4-8 analytical views]
- Documents: [0-3 PDFs: e.g. carrier contract, surcharge bulletin] (or "none")
- Context assets (go through the context extractor, never as CSV): [metric definitions standard, business glossary with owners, data-platform wiki page, chat-channel export, plus the story documents]; the pipeline adds a dbt semantic-layer YAML, a certified query library and an analyst handbook rendered from the local definitions
- Final step: Domain Health analysis queued and left running for the SE

## What the audience sees
1. **Live App "[name]"** — Executive Overview → [Scenario Lab] → Implementation Plan
2. **Follow-up question**: "[the complex question]" → expected answer: [points]
3. **Agent "[name]"** (created disabled): [one sentence on what it watches]
4. **5-minute script** in the Shipping Cockpit format

## Questions for you
- [anything still ambiguous — at most 3]

Reply "go" (or ask for changes) and the build runs end to end without further questions.
