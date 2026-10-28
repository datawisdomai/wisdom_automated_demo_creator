# 10m Demo Script: Kampanjrapport (five moves) + the build half
Companion video: add Loom link once recorded

Revision 2 (2026-10-27). The Store Performance Cockpit script from revision 1 is kept at the end as the second act.

## Prepare ahead of time
- Live App "Kampanjrapport" open on page *Rapporten*, filters Kronmat and 2026-W36, with the original prompt visible in the
  side bar: https://proddemo.askwisdom.ai/apps/kampanjrapport--app_b6d31562abb6417697eb718feac392f5
- Tabs needed: Rapporten, Förklara och kostnad, Orderjustering (select Äpplen & Päron on page 3 once so the draft is cached).
- Chat tab 1, already answered: `/kampanjrapport Kronmat 2026-W36` (the "Skill loaded" indicator is the beat): https://proddemo.askwisdom.ai/chat/e8dd4c39-8f8e-462a-8d11-a424de49f683
- Chat tab 2, already answered: "Why is forecast error highest on Multiköp 3 för 2 campaigns over the last 13 campaign weeks
  and what did the over-forecast cost us in margin in Q3 2026?": https://proddemo.askwisdom.ai/chat/9317bc22-7963-483e-8489-1efd029ba9b1
- Agent "Kampanjprognos-vakt" open in the visualizer with its prompt showing (draft, never run): https://proddemo.askwisdom.ai/agents/AGENT_e4610bc1-e12a-4849-b350-16c31732cbb1/edit
- Domain (35 Snowflake objects + 4 Teradata tables, context, the three skills in the Skills tab):
  https://proddemo.askwisdom.ai/domains/ET_DOMAIN_be0ec587fe154e29930aceb65d5e04f3
- Context Builder sources to point at during the build half: nordmark_dbql_export_2026-05.sql, kampanjrapport_report_definition.txt,
  campaign_planning_runbook.pdf (same domain, Context Extraction tab).
- Domain Health tab with the analysis left running and the description rewrites pending (the steward beat):
  https://proddemo.askwisdom.ai/domains/ET_DOMAIN_be0ec587fe154e29930aceb65d5e04f3/domain-health
- Connections: Snowflake "Snowflake Demo" https://proddemo.askwisdom.ai/connections/et-connection-678570afa5f14afe9bb146040e70c28c
  and the read-only Teradata "Ali-TD" https://proddemo.askwisdom.ai/connections/et-connection-776daac6e8354e86a809ecd2dbf8a71f
- Second act, if time allows: Store Performance Cockpit https://proddemo.askwisdom.ai/apps/store-performance-cockpit--app_70651919ea3a464695794ee519ed7067
  and its chat https://proddemo.askwisdom.ai/chat/9f7f1fd2-f83d-4e62-9ced-ff2b8bd6db9a
- Open both Live Apps once before the session so they are cached. No Axfood names anywhere; say "Nordmark".

## Script
Let's take on the role of the Head of Campaign Planning at Nordmark Dagligvaror, a Swedish grocery group with three chains:
Kronmat for discount, Torghallen for the neighbourhood shop, and Grosshallen, the hypermarkets we acquired last year.
Every Monday my planners open one report: the Kampanjrapport. For each campaign week and article it shows what we planned,
what our CatBoost model said we would sell, what the chain's own purchase plan said, and what actually sold. It used to live in
MicroStrategy. Today it is a conversation.

{Live App Kampanjrapport, Rapporten tab}
This is the same grid, built once from one prompt. Kedja, Vecka, Kampanj and Taktik as filters. One row per Nyckel, the week
and article key. The same columns in the same order, and the totals are ratios of sums, the way the report engine always did it.
Kronmat, week 36: 28 article rows across four Höstskörd campaigns. We sold 615 thousand units. The chain's purchase plan was
18 percent over that. The model was 6 percent over. Nothing to author, nothing to reconcile, and the definitions live in the
semantic layer, not in anyone's prompt.

{Chat tab 1}
And because it is codified as a skill, the conversation gives the same answer every time. I type slash kampanjrapport, Kronmat,
2026-W36. Wisdom loads the skill, you can see the indicator, and returns the same grid and the same totals as the Live App.
Ten people asking in ten different ways get one report. That is the first thing MicroStrategy could not do for us.

{Chat tab 2}
Here is the second. I asked why forecast error is highest on our Multiköp three-for-two campaigns, and what it cost us.
Wisdom follows the planners' own procedure: tactic, then perishables, then articles, then stores, then weeks. The chain plan
over-forecasts perishable multibuys by 31 percent. Every other tactic sits under 9 percent. Perishables carry 87 percent of the
error. And one store stands out: Grosshallen Västerhamn, 53 percent over since a discounter opened a kilometre away in March,
while the plan kept allocating last year's volumes. Wisdom says "coincides with", not "caused by". Then the cost. Demand sits in
our warehouse; cost still sits in a finance system we have not migrated, so this is an illustrative extract and every number
carries that label. On that basis, over-forecasting cost us about 10.8 million kronor of margin in the third quarter, four
fifths of it waste on perishables, and Kronmat's multibuy campaigns are the largest single share.

{Agent tab}
If this is a question I'd ask every week, I turn it into an agent. Kampanjprognos-vakt runs every Monday at seven. It reads the
coming two weeks of campaigns, flags every perishable where the chain plan is more than 15 percent above the model, checks how
that tactic has performed, and sends the responsible planner a draft adjustment. Right now it would flag four campaigns:
Mejerivecka, Äpplen och Päron, Brödfest and Köttvecka. It never places an order. Generated from a single prompt in plain English.

{Live App, Orderjustering tab}
Which brings us to the last move. Äpplen och Päron, Torghallen, week 42, delivery on the twelfth of October, twelve days out.
Twenty fruit articles. The draft cuts 45 thousand units, 17 percent of the chain plan, in whole pallet layers, never below the
model. On the illustrative cost data that protects about 640 thousand kronor from the bin. The approval block says who asked,
what data was used, who proposed it and who approves: Viktor Holmgren, the responsible planner. I can edit the threshold, I can
approve, and the app logs it. Nothing is sent anywhere. That is governance the old report never had.

{Open the Ask WisdomAI side panel, scroll to the original prompt}
Every element you have seen came from one prompt: the three pages, the grid, the drill order, the draft, the approval block.
So now, let's look at how this was built, because that is the question your team will ask.

{Domain, Context Extraction tab}
We connected the warehouse and picked the tables. Then we gave the Context Builder three things a data team already has.
First, a query-log export. This file is shaped like a Teradata DBQL extract: 74 logged statements from three days in May, in
MicroStrategy's own SQL shape. Forty-one are the real reports; the rest is statistics collection, ETL audit and session noise.
Wisdom separated the two, turned the reports into reviewed queries and the recurring formulas into knowledge. Today this is a
file; in the POC it is a connection. Second, the MicroStrategy report definition export: attributes, metrics with formulas,
drill paths. Third, the planners' runbook. From the runbook Wisdom proposed the three skills you just watched run.

{Skills tab, then the suggestions report}
Here they are, versioned. And here is the report of everything the extractor proposed. The steward accepts or declines; the
description rewrites are still pending, on purpose, because a human stays in the loop.

{Evals tab}
Then we test it. The eval set runs every prompt three times. The slash kampanjrapport prompt is the proof of determinism: same
grid, three runs. Where answers are flaky, Domain Health tells the steward which piece of context to fix.
That is the whole build: a connection, three files, one afternoon, a steward's review. In a POC we do it with your team in
eight one-hour sessions.

## Second act, if time allows: Store Performance Cockpit (revision 1)
Switch persona to the Head of Store Operations. Executive Overview: Torghallen +4.8 percent like for like, Kronmat +2, Grosshallen
−1.4 with margin 24.4 and quarterly EBIT just back to break-even. Store Gap Lab: Grosshallen Västerhamn at 62 percent of its
catchment potential against 92 for its peers, trips −11, basket +4, Dairy and Bread availability 89, Billigmat 1.1 km away,
Families −23. Implementation Plan: the Nordstaden playbook as a 12-week test worth about 40 million. Chat: the federation beat
across Snowflake and Teradata, the three late import suppliers Frontier Trading, Sterling Trading and Lakeshore Industries.

## Agent prompts to pre-build
### Kampanjprognos-vakt
Create an agent called "Kampanjprognos-vakt" on the Nordmark Dagligvaror domain. Every Monday at 7am, read V_KAMPANJ_KOMMANDE for campaign weeks delivering in the next 14 days and find every perishable article (FARSKVARA true) where the chain purchase forecast (KOPT_PROGNOS_KEDJAN) exceeds the CatBoost sold forecast (SALD_PROGNOS_CATBOOST) by more than 15 percent (PROGNOSGAP_PCT above 0.15, FLAGGA true). For each flagged campaign, look up how the same chain and tactic type performed against forecast in the last 13 completed campaign weeks from V_PROGNOSFEL_TAKTIK, and compute the proposed reduction in whole cases rounded down to full pallet layers (FORESLAGEN_MINSKNING_KOLLI) and the margin it protects (SKYDDAD_MARGINAL_SEK, labelled as illustrative cost data because the finance system is not migrated). Send the responsible campaign planner (ANSVARIG_PLANERARE in KAMPANJ) and the Head of Campaign Planning a summary with the flagged campaigns, delivery dates, the forecast gap, the historical bias for that tactic, the proposed order adjustment as a draft for approval, and the supporting data. Never place or change an order; the draft is for a human to approve. Never repeat the same alert for the same campaign in consecutive weeks and send nothing if nothing is flagged.

### Grosshallen Store Watch (revision 1)
Create an agent called "Grosshallen Store Watch" on the Nordmark Dagligvaror domain. Every Tuesday at 7am, calculate for each Grosshallen store the prior week's net sales and transactions versus the same week last year from STORE_DAILY_SALES and CALENDAR, and the prior week's on-shelf availability in Dairy and Bread & Bakery from SALES_WEEKLY_STORE_CATEGORY, comparable stores only. If any store's transactions are more than 5 percent below last year for two consecutive weeks, or Dairy and Bread & Bakery availability falls below 94 percent, or the store's weekly sales drop more than 8 percent versus its trailing 4-week average, investigate whether the cause is availability (stockout hours by category), a competitor event logged within 2 km in the last 90 days (COMPETITOR_EVENTS), or a loyalty segment shift (Families visits in LOYALTY_ACTIVITY_MONTHLY), and compare the store with the median of its peer cluster from V_PEER_COMPARISON. Send the Grosshallen banner director and the regional manager a summary with the finding, the affected stores, the most likely cause and the supporting data. Never repeat the same alert on consecutive weeks and send nothing if nothing triggers.
