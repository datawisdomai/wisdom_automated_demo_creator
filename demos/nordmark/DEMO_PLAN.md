# Demo Plan: Nordmark Dagligvaror — Revision 2 (2026-10-27): the Kampanjrapport

**Prospect / vertical:** Axfood (Swedish grocery), introduced and presented with the Teradata account team · Retail
**Audience (Axfood session, 10 or 17 Nov 2026, 30–45 min for our part):** IT and data leadership: platform managers, data &
analytics architects, BI development managers, C-1. MicroStrategy users under cost pressure.
**Internal checkpoint:** Friday 30 Oct 2026, 30 min with the Teradata team (Talal, Pär, Hadi, Suresh).
**Inputs:** `inputs/axfood_demo_brief_teradata.pdf` (Pär Fredander, 26 Oct), `inputs/teradata_call_2026-10-27_transcript.md`,
`inputs/ali_slack_notes.md`. Revision 1 (built 26 Oct, the Store Performance Cockpit) stays in the domain and is reproduced
at the bottom of this file.

## What changes and why
Pär's brief asks for one typical MicroStrategy report rebuilt as a conversation, then four things the report cannot do:
explain a variance, cross to cost, alert proactively, act with a governed draft. The call added the second half: the room is
technical, so after the outcome we show how the domain was built from a Teradata query log and a report definition, with a
human approving what the extractor proposes. Decisions taken with Chick on 27 Oct:
- Keep the Store Performance Cockpit; it stays in the same domain and serves move 2 (the store drill) and the deeper story.
- Snowflake remains the data home for Friday's review. Moving the data onto a Teradata sandbox for the Axfood session is an
  open ask to Pär and Suresh (section "Open with Teradata").
- The build walkthrough uses a **file** shaped like a Teradata DBQL export; direct query-log extraction from Teradata is not
  available in the product yet, so we say so and show the file path.
- **Skills** codify the report so the same question returns the same grid every time (Pär's success criterion). The extractor
  supports a SKILL agent type and UPSERT_SKILL suggestions, so skills enter through the extractor and the steward approves
  them; direct creation is the fallback.
- No Axfood names anywhere. Swedish business terms in the data, English (or Swedish) in the conversation.

## The story in one paragraph
Nordmark Dagligvaror runs weekly campaigns in all three banners. The campaign planner's MicroStrategy report, the
**Kampanjrapport**, shows for each campaign week and article the planned quantity, the sold forecast from the group's
machine-learning model (CatBoost), the purchase forecast from the chain's own plan, and what actually sold. The demo rebuilds that
grid as a conversation and a Live App with the same numbers, then goes where the report cannot: the chain's own plan
systematically over-forecasts multibuy campaigns on perishables, the excess turns into waste and markdowns that cost real
margin (illustrative cost data, labelled, because finance still sits in a separate system), an agent watches the coming weeks'
campaigns and flags the ones about to miss before the goods are delivered, and the planner gets a drafted order adjustment
with an approval step and an audit trail. The second half shows how the domain was built in an afternoon from a query-log
export, a report definition and a runbook, with the steward approving each suggestion.

## Story arcs (what the new data will prove)
| # | Move (brief §6) | Hero entity | Target numbers the data will contain |
|---|---|---|---|
| CP7 | **Recreate**: the grid matches, no report authoring | Kronmat campaign "Höstskörd" week 2026-W36 | 28 articles, 4 tactic types; the view and the skill return the same rows and totals; chain purchase forecast +18 % over actual, CatBoost +6 % |
| CP8 | **Explain**: why forecast error is highest on one tactic | Tactic "Multiköp 3 för 2", perishables | Multiköp bias ≥ +25 % vs ≤ +10 % on other tactics; perishables carry ≥ 60 % of the absolute error; Grosshallen Västerhamn is the worst store (over-forecast ≥ +35 % since the Billigmat opening), Nordstaden among the best |
| CP9 | **Cross to cost** (illustrative, labelled) | Q3 2026 group | Over-forecast cost ≈ SEK 12 m in the quarter: ≥ 55 % waste on perishables, the rest markdown; Kronmat multibuy campaigns are the largest share |
| CP10 | **Watch**: the agent fires before delivery | Campaign weeks 2026-W41–W44 (future rows, no actuals) | ≥ 3 perishable campaigns where the chain forecast exceeds CatBoost by > 15 %; at most 1 dry-grocery campaign does |
| CP11 | **Act and govern**: a draft, never a write | Torghallen "Äpplen & Päron" week 2026-W42 | Proposed purchase cut −18 % = whole cases rounded down to layers (lav); margin protected ≈ SEK 0.4 m; approver, timestamp and data lineage recorded in the app's action log |

CP1–CP6 (store performance, federation to the Teradata purchasing platform) remain as built.

## Data added to Snowflake `NORDMARK_POC.ANALYTICS` (Swedish names, English comments)
- `ARTIKEL` (≈ 1,200 articles): artikel_id, artikel_namn, kategori → PRODUCT_CATEGORIES, varumärke, egna_märkesvaror (private label),
  färskvara (perishable), hållbarhet_dagar, kolli (units per case), lav (cases per layer), pall (cases per pallet), enhet.
- `KAMPANJ` (≈ 150 campaigns, 24 months, three banners): kampanj_id, kampanj_namn, kedja (banner), koncept_kod, taktik_typ_kod and
  taktik_typ (Prisnedsättning, Multiköp 3 för 2, Medlemspris, Halva priset, Kupong), leverans_från, leverans_till, kalender_vecka_id
  (YYYYWW), promotion_id (nullable link to the existing PROMOTIONS so Sommarpris 2026 appears in both worlds).
- `KAMPANJ_ARTIKEL_VECKA` (≈ 7,000 rows; the report's grain): nyckel = kalender_vecka_id || artikel_id, kampanj_id, kedja, artikel_id,
  planerad_kvantitet (Quantity), såld_prognos_catboost, köpt_prognos_kedjan, faktisk_såld (NULL for weeks after 2026-09-30),
  levererad_kvantitet, kampanjpris.
- `KAMPANJ_BUTIK_VECKA` (≈ 27,000 rows): campaign × store × week actual sold and allocated forecast, so variance drills to store.
- `ARTIKEL_KOSTNAD_MÅNAD` (≈ 30,000 rows): inköpspris, listpris, marginal_pct per article and month, column `källa` =
  'ILLUSTRATIV – finanssystem ej migrerat' and a table comment saying the same; every cost figure on screen carries the label.
- Views: `V_KAMPANJRAPPORT` (the MicroStrategy grid: filters kedja, vecka, kampanj, taktik; rows week × article; measures planned,
  sold forecast, purchase forecast, actual, prognosfel_pct, bias), `V_PROGNOSFEL_TAKTIK` (bias by tactic and perishability),
  `V_KAMPANJ_BUTIK_AVVIKELSE` (store-level variance with the competitor-event flag), `V_KAMPANJ_MARGINALEFFEKT` (over-forecast
  cost split into waste and markdown, labelled illustrative), `V_KAMPANJ_KOMMANDE` (upcoming campaign weeks with the two forecasts
  and their gap, for the agent).
- Definitions agreed in the semantic layer, not in prompts (brief §7): forecast error = (forecast − actual) / actual, positive =
  over-forecast; campaign week = the ISO week of leverans_från; tactic type = taktik_typ; margin and purchase cost = the
  illustrative table. These go into the metric standard, the glossary and the skills.
- Unchanged: the 16 existing tables and 9 views, the Ali-TD federated tables, the two PDFs.

## Skills (new, three, in the domain's Skills tab)
1. `kampanjrapport` — "Use for campaign performance and forecast accuracy by chain and week; `/kampanjrapport <kedja> <vecka>`."
   Fixed steps (resolve chain and week, use V_KAMPANJRAPPORT, the agreed error formula, the fixed column order and sort, totals
   row, bias by tactic underneath), fixed presentation, never substitutes a different period silently. This is move 1 and the
   determinism proof: the eval runs it three times and expects identical totals.
2. `prognosavvikelse` — "Use when asked why forecast error is high for a campaign, tactic, article or store." Fixed drill order
   (tactic → perishability → article → store → week), then the three causes to check (competitor events within 2 km, Dairy and
   Bread availability, loyalty segment visits), reconciles the decomposition before naming drivers, states evidence strength.
3. `orderjustering-utkast` — "Use when asked to summarise for the planner or draft an order adjustment." Computes the cut in
   whole kolli rounded down to lav, shows margin protected using the illustrative cost with the label, produces a draft for
   approval and never writes anywhere; records who asked, what data was used and who approves.
Skills travel through the extractor from the authored runbook (below); if the SKILL agent does not propose them, publish
creates them directly from the same markdown and reads them back.

## Context assets added (through the extractor, never CSV)
- `nordmark_dbql_export_2026-05.sql` — shaped like a Teradata DBQL extract (QueryID, UserName, StartTime, AMPCPUTime, QueryText),
  about 60 statements: 40 relevant in MicroStrategy style (quoted identifiers, a11/a12 aliases, grouped by week, Teradata date
  literals, `SEL`, `QUALIFY`, `TOP`) against the Nordmark objects, 20 noise (COLLECT STATISTICS, session checks, ETL audit
  tables, an HR query) so the audience sees the extractor separate signal from noise. Registered as a `.sql`, since direct
  DBQL extraction is not in the product yet; the script says so.
- `kampanjrapport_report_definition.txt` — a MicroStrategy-style report definition export (attributes, metrics with formulas,
  filters, drill paths) for the Kampanjrapport: the "MicroStrategy as a context source" beat.
- `campaign_planning_runbook.md` → PDF — the planners' runbook: the three workflows above written as procedures, the definitions,
  the approval rule; this is what the SKILL agent turns into skills.
- Updates to the existing metric standard and glossary (Swedish terms table from the brief §8: Kedja, Vecka, Kampanj, Artikel,
  Butik, Såld prognos, Köpt prognos, Nyckel, Kolli, Pall, Lav, Kvitto) and the data-platform wiki (campaign mart, forecast feed,
  illustrative cost extract).
- Pipeline renders the dbt semantic YAML, certified query library and analyst handbook as before (new metrics ≈ 12, new reviewed
  queries ≈ 20 incl. Swedish-language variants, new knowledge ≈ 15).

## What the audience sees (10-minute flow, brief §1; the cockpit stays as the deeper second act)
1. **Live App "Kampanjrapport"** (new): page 1 *Rapporten* — the familiar grid with Kedja / Vecka / Kampanj / Taktik filters and the
   drill chain → campaign → tactic → article, preselected on Kronmat 2026-W36; page 2 *Förklara & kostnad* — variance by tactic,
   article, store and week, the store panel linking to the Billigmat opening, the illustrative margin cost clearly labelled;
   page 3 *Orderjustering* — the drafted purchase adjustment for Torghallen W42 in kolli and lav, editable, approve button, action
   log with who/what/when and a labelled mock hand-off payload ("no external system connected").
2. **Chat, move 1**: `/kampanjrapport Kronmat 2026-W36` — the skill loads, the same grid and totals as the Live App. Then the
   **follow-up question** (moves 2 and 3): "Why is forecast error highest on Multiköp campaigns in week 36 and what did the
   over-forecast cost us in margin?" → expected: multibuy bias ≥ 25 % vs ≤ 10 %; perishables carry most of the error; Västerhamn
   the worst store since the competitor opened; ≈ SEK 12 m quarterly cost, mostly waste, labelled illustrative; the recommendation
   to let CatBoost cap the chain plan on perishables.
3. **Agent "Kampanjprognos-vakt"** (created disabled, move 4): every Monday, scans V_KAMPANJ_KOMMANDE for perishable campaigns
   delivering in the next two weeks where the chain forecast exceeds CatBoost by more than 15 %, investigates the last comparable
   campaign's error, and sends the planner and the category manager the list with a drafted adjustment. Never repeats an alert.
4. **Build walkthrough** (second half, for the IT room): pick tables on the connection → Context Builder sources: the DBQL-shaped
   file, the report definition, the runbook → the suggestions report (reviewed queries, knowledge, synonyms, the three skills) →
   accept, with description rewrites left pending → evals (3 runs, identical results on the skill) → Domain Health. Talk track
   includes the POC frame (8 one-hour sessions) and the Cisco reference (domain in 2 weeks, 200 users).
5. **Script**: `DEMO_SCRIPT.md` rewritten for the five moves plus the build half, with clickable links to both Live Apps, the two
   chats, the agents, the domain, Domain Health and both connections. Existing Store Performance Cockpit kept as act two.

## Pipeline changes needed first (generic, tested, ≈ half a day)
- `wisdom.skills[]` in the spec (markdown files), publish step `skills` after `extraction`: accept `UPSERT_SKILL` suggestions,
  else `createDomainSkill`; read back with `domainSkills`; `demo status` and the report list them.
- Extraction: add `SKILL` to the agent types and a `skills` family to `extraction.accept`.
- `context_assets[]` kinds `query_log` (rendered as `.sql`, not PDF) and `report_definition` (`.txt`).
- `live_apps[]` and `chat.questions[]` so a demo can carry two Live Apps and more than one answered chat; `agents[]` likewise.
- Eval: prompts that invoke a skill by name, with the pass rule "identical totals across the three runs".

## Where it is published
Same as revision 1: proddemo Default Organization, domain "Nordmark Dagligvaror", Snowflake via the shared "Snowflake Demo"
connection, Teradata via Ali-TD read-only. New tables load into the existing database; the domain gains the new tables, views,
context and skills. Evals run 3 times. Domain Health is queued last and left running.

## Open with Teradata (to raise on Friday)
- **Data home for the Axfood session.** The brief says queries must run in place on Teradata. Options: Teradata provides a sandbox
  database with write access and we load the generated data there; or we hand Pär and Suresh the Teradata-dialect DDL and CSVs
  and they load it. Either way the domain is re-pointed and the pipeline re-run; the story does not change.
- **Branding and environment** ("Tera, powered by WisdomAI"; separate URL or tenant): Talal and Edvin. The build is repeatable in
  another environment, but the shared Snowflake Demo and Ali-TD connections exist only in proddemo.
- Confirmation from Axfood that the Kampanjrapport is the right report, and which chain (brief §9). Until then: Kronmat.
- Whether the Teradata team wants the "same answer over MCP" success criterion demonstrated; it needs the Wisdom MCP server
  configured against this domain and is out of scope for Friday.

## Timeline
- Tue 27 – Wed 28 Oct: pipeline changes, data module, checks, load, context assets, skills, publish, eval.
- Thu 29 Oct: Live App, chats, agent, script, report, health; rehearsal of the 10-minute flow twice.
- Fri 30 Oct: review with the Teradata team.

## Questions for you
- None blocking. Assumptions: three skills as listed; a second Live App rather than new pages in the cockpit; Kronmat as the
  demo chain; your email as the agent recipient.

Reply "go" (or ask for changes) and the build runs end to end without further questions.

---

# Revision 1 (built 2026-10-26): Store Performance Cockpit

**Prospect / vertical:** Axfood (Swedish grocery: Willys, Hemköp, City Gross), introduced by the Teradata account team · Retail
**Persona:** Head of Store Operations with the group FP&A analytics team (secondary: Grosshallen banner director, Fresh & Produce
category manager, loyalty lead, data steward) · **As-of date:** 2026-09-30 (data 2024-10-01 → 2026-09-30, 24 months)

## The story in one paragraph
Nordmark Dagligvaror is a fictional Swedish grocery group with three banners: **Kronmat** (discount, ~120 stores), **Torghallen**
(neighbourhood stores, ~90 incl. franchise) and **Grosshallen** (38 hypermarkets acquired in January 2025, the problem child).
The group grows on volume while food prices fall (deflation, the April 2026 VAT cut), Torghallen is the star, Kronmat is slightly
behind the market and Grosshallen has just reached break-even on cost cuts but still loses like-for-like sales. The demo follows
Ali's three levels and flow: KPI summary → pick the underperforming store (Grosshallen Västerhamn) → break the gap down
(transactions, not basket) → compare with peer stores and catchments → investigate causes (availability, a new discount
competitor, lost family shoppers, late import purchase orders) → recommend a specific action and a 12-week test, learned from
the peer store Grosshallen Nordstaden. Nothing names Axfood or its banners.

## Story arcs (what the data will prove)
| # | Arc | Hero entity | Target numbers the data will contain |
|---|---|---|---|
| CP1 | Grosshallen lags: LFL −1.5% vs group +1.5%; gap is transactions (−6%) not basket (+4%); margin 2.5 pts below Kronmat; Q3 2026 EBIT break-even after a Q3 2025 loss | Grosshallen Västerhamn | Västerhamn sells 62% of its catchment potential vs 90% for its peer cluster — the largest SEK gap in the banner |
| CP2 | Growth with margin erosion | Kronmat Fresh & Produce / promotion "Sommarpris 2026" | Fresh & Produce +8% sales, −2 pts gross margin; Sommarpris top-3 uplift, bottom-3 margin |
| CP3 | Availability lines up with weak sales | Dairy & Bread | Stores with OSA < 94% run ≥ 3 pts weaker LFL; Västerhamn worst in banner at 91% |
| CP4 | Customer segments and competition | Families segment / "Billigmat" opening | Families visits −12% at Grosshallen vs flat elsewhere; discount competitor opened 1.1 km from Västerhamn on 2026-03-12, sales −7% after |
| CP5 | Peer playbook | Grosshallen Nordstaden | Same cluster, 95%+ of potential: PL share +6 pts, OSA 97%, markdowns −30% → the action and the test |
| CP6 | **Federation beat** (Teradata) | Import suppliers | Grosshallen non-food lost sales concentrate (≥ 55%) in SKUs from the 3 suppliers whose purchase orders run late in the Teradata purchasing platform |

## Data (Snowflake `NORDMARK_POC.ANALYTICS` + federated Teradata)
- Dimensions: CALENDAR, BANNERS, NEIGHBORHOODS (catchment demographics, competitors, potential), STORES (banner, region, format, peer
  cluster), PRODUCT_CATEGORIES, NONFOOD_ASSORTMENT (250 imported SKUs keyed like Teradata), PROMOTIONS
- Facts (~1.1M rows): STORE_DAILY_SALES (store×day), SALES_WEEKLY_STORE_CATEGORY (store×week×category: sales, COGS, units, promo,
  markdowns, waste, availability), STORE_MONTHLY_COSTS, PROMOTION_RESULTS, LOYALTY_ACTIVITY_MONTHLY (store×segment×month),
  STORE_ASSORTMENT_MONTHLY, COMPETITOR_EVENTS, NONFOOD_AVAILABILITY_MONTHLY
- Views: V_KPI_STORE_MONTHLY, V_BANNER_KPI_MONTHLY, V_STORE_GAP_DECOMPOSITION, V_PEER_COMPARISON, V_CATCHMENT_POTENTIAL,
  V_PROMO_EFFECTIVENESS, V_AVAILABILITY_VS_SALES, V_LOYALTY_SEGMENT_TRENDS, V_NONFOOD_AVAILABILITY_BY_SUPPLIER
- **Federated (read-only, Ali-TD Teradata, database `wisdomai`)**: RTL_DIM_SUPPLIER, RTL_DIM_PRODUCT, RTL_FACT_PURCHASE_ORDER_LINE,
  RTL_VW_PURCHASE_ORDER — framed as the import-purchasing platform Grosshallen brought with it. The connection is never touched;
  the join to our data happens in chat (Wisdom runs SQL per connection and combines in Python).
- Documents: Grosshallen turnaround memo (Q3 2026), store review playbook
- Context assets (through the context extractor, never CSV): metric definitions standard (LFL, GP %, OSA, basket), business glossary
  with owners, data-platform wiki (Snowflake POS mart + Teradata purchasing), store-ops channel export, the two documents, a
  Sommarpris post-mortem; plus the pipeline's dbt semantic YAML, certified query library and analyst handbook
- Final step: Domain Health analysis queued and left running for the SE

## What the audience sees
1. **Live App "Store Performance Cockpit"** — Executive Overview (group/banner KPIs, filter by banner/region/category/period) →
   Store Gap Lab (pick a store: gap decomposition, peer comparison, catchment potential, availability, segments) → Implementation
   Plan (the Västerhamn action list and the 12-week test design with estimated upside)
2. **Follow-up question** (the federation beat): "Why is Grosshallen Västerhamn underperforming its catchment potential and are late
   inbound purchase orders from the import suppliers part of its non-food availability problem?" → expected: 62% vs 90% of
   potential; transactions-led; worst Dairy/Bread OSA (91%); Families −12% since Billigmat opened; the three late Teradata suppliers;
   Nordstaden playbook
3. **Agent "Grosshallen Store Watch"** (created disabled): weekly, flags Grosshallen stores whose LFL or OSA fall below threshold
4. **5-minute script** in the Shipping Cockpit format, with clickable links (Live App, chat, agent, domain, health, both connections)

## Where it is published
proddemo **Default Organization** (Ali-TD lives there), domain "Nordmark Dagligvaror", Snowflake via the shared "Snowflake Demo"
connection (NORDMARK_POC added to its filter by hand), Teradata via Ali-TD attached read-only. Evals run 3 times.
