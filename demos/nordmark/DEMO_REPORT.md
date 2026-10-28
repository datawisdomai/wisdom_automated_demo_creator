# Nordmark Dagligvaror — demo build report

Built 2026-10-28 19:24 UTC · demo as-of 2026-09-30 · seed 20261026

## Where everything is

| Asset | Value |
|---|---|
| Snowflake | `NORDMARK_POC.ANALYTICS` (21 tables, 14 views) |
| Federated source (read-only) | Ali-TD — `wisdomai` (4 tables, teradata) |
| Wisdom deployment / workspace | proddemo / ET_WORKSPACE_01dc4f2105194dc286b9d69df2a89024 |
| Domain | Nordmark Dagligvaror — `ET_DOMAIN_be0ec587fe154e29930aceb65d5e04f3` |
| Live App | Store Performance Cockpit — `app_70651919ea3a464695794ee519ed7067` |
| Live App (Kampanjrapport) | `app_b6d31562abb6417697eb718feac392f5` |
| Follow-up chat | `9f7f1fd2-f83d-4e62-9ced-ff2b8bd6db9a` |
| Chat (explain_cost) | `9317bc22-7963-483e-8489-1efd029ba9b1` · score 0.3333333333333333 |
| Chat (kampanjrapport) | `e8dd4c39-8f8e-462a-8d11-a424de49f683` · score 0.3333333333333333 |
| Agent (disabled) | Grosshallen Store Watch — `AGENT_d6eb699a-5bbf-4705-9859-8347a1b2c7b6` |
| Agent (Kampanjprognos-vakt) | `AGENT_e4610bc1-e12a-4849-b350-16c31732cbb1` |
| Skills | kampanjrapport v4 (extractor+steward-edit), orderjustering-utkast v2 (extractor+steward-edit), prognosavvikelse v2 (extractor+steward-edit) |
| Eval | set `d2191573-0a9c-456d-99f3-50c5207e5616` · last score 0.6417910447761194 |
| Domain Health run | job `ET_JOB_RUN_23183631f6d74fcbb88124785e974c6c` (review in the Domain Health tab) |
| Documents | 7 uploaded |
| Instance | https://proddemo.askwisdom.ai |

## Links

- **Instance**: https://proddemo.askwisdom.ai
- **Domain**: https://proddemo.askwisdom.ai/domains/ET_DOMAIN_be0ec587fe154e29930aceb65d5e04f3
- **Domain Health**: https://proddemo.askwisdom.ai/domains/ET_DOMAIN_be0ec587fe154e29930aceb65d5e04f3/domain-health
- **Live App**: https://proddemo.askwisdom.ai/apps/store-performance-cockpit--app_70651919ea3a464695794ee519ed7067
- **Live App (Kampanjrapport)**: https://proddemo.askwisdom.ai/apps/kampanjrapport--app_b6d31562abb6417697eb718feac392f5
- **Follow-up chat**: https://proddemo.askwisdom.ai/chat/9f7f1fd2-f83d-4e62-9ced-ff2b8bd6db9a
- **Chat (explain_cost)**: https://proddemo.askwisdom.ai/chat/9317bc22-7963-483e-8489-1efd029ba9b1
- **Chat (kampanjrapport)**: https://proddemo.askwisdom.ai/chat/e8dd4c39-8f8e-462a-8d11-a424de49f683
- **Live App build conversation**: https://proddemo.askwisdom.ai/chat/93b4fde9-e317-408f-8511-25109a53ae81
- **Live App build conversation (Kampanjrapport)**: https://proddemo.askwisdom.ai/chat/c0e85f37-ce7d-48ac-a0ac-c5e7f7120255
- **Agent**: https://proddemo.askwisdom.ai/agents/AGENT_d6eb699a-5bbf-4705-9859-8347a1b2c7b6/edit
- **Agent (Kampanjprognos-vakt)**: https://proddemo.askwisdom.ai/agents/AGENT_e4610bc1-e12a-4849-b350-16c31732cbb1/edit
- **Connection**: https://proddemo.askwisdom.ai/connections/et-connection-678570afa5f14afe9bb146040e70c28c
- **Federated connection (Ali-TD, read-only)**: https://proddemo.askwisdom.ai/connections/et-connection-776daac6e8354e86a809ecd2dbf8a71f

## Steps

| Step | Status | When | Notes |
|---|---|---|---|
| generate | ok | 2026-10-27T22:31 | counts={'ARTIKEL': 1200, 'ARTIKEL_KOSTNAD_MANAD': 31200, 'BANNERS':, mismatches=[], missing=[], schema_errors=[] |
| validate | ok | 2026-10-27T22:31 | failed=0, failures=[], passed=121 |
| ddl | ok | 2026-10-27T22:29 | seconds=6, statements=42 |
| load | ok | 2026-10-27T22:32 | counts={'ARTIKEL': 1200, 'ARTIKEL_KOSTNAD_MANAD': 31200, 'BANNERS':, failures=[], seconds=23, tables=['ARTIKEL', 'KAMPANJ', 'ARTIKEL_KOSTNAD_MANAD', 'KAMPANJ_ART |
| validate_snowflake | ok | 2026-10-27T22:33 | failed=0, failures=[], passed=121 |
| rq_check_snowflake | ok | 2026-10-27T22:47 | count=71, failures=0 |
| metrics_check | ok | 2026-10-27T22:46 | count=50, failures=[] |
| docs | ok | 2026-10-27T22:51 | failures=[], generated=0, rendered=['/Users/chick/Desktop/Claude Code/wisdom_automated_demo_cre |
| publish.connection | ok | 2026-10-26T20:23 | connection_id=et-connection-678570afa5f14afe9bb146040e70c28c, created=False |
| publish.domain | ok | 2026-10-26T20:23 | created=False, domain_id=ET_DOMAIN_be0ec587fe154e29930aceb65d5e04f3 |
| publish.database | ok | 2026-10-27T22:50 | missing=[], tables=35 |
| publish.federated | ok | 2026-10-27T22:49 | sources=1, tables=4 |
| publish.instructions | ok | 2026-10-27T22:49 | chars=8066 |
| publish.lookup | ok | 2026-10-27T22:50 | changed=5, missing=[] |
| publish.documents | ok | 2026-10-26T20:24 | dataset_id=ET_DATASET_12a0ce13026f4d23ac04c5e55a42864d, uploaded=7 |
| publish.extraction | ok | 2026-10-27T23:20 | coverage={'knowledge': {'in_domain': 262, 'story_facts': 40}, 'metric, detail=metrics 35/35, reviewed queries 40/40 after accepting the ex, job_status=JOB_RUN_STATUS_SUCCESS, previous=None |
| publish.skills | ok | 2026-10-27T23:20 | created=0, kept=3, skills=3, updated=0 |
| publish.s3_dataset | ok | 2026-10-26T20:17 | attached=False |
| eval | ok | 2026-10-28T00:49 | consistently_failing=13, consistently_passing=34, flaky=20, passed=40 |
| health | ok | 2026-10-28T00:49 | analysis_status=RUNNING, quick_check_job=ET_JOB_RUN_23183631f6d74fcbb88124785e974c6c, trigger={'evalRunId': None, 'message': 'Analysis started.', 'runGrou |
| app | ok | 2026-10-27T23:32 | app_id=app_70651919ea3a464695794ee519ed7067, apps={'kampanjrapport': {'app_id': 'app_b6d31562abb6417697eb718fe, conversation_id=93b4fde9-e317-408f-8511-25109a53ae81, detail=rev1 cockpit + rev2 Kampanjrapport (651 s, liveSpecVersion 2 |
| chat | ok | 2026-10-27T23:30 | chats={'explain_cost': {'conversation_id': '9317bc22-7963-483e-848, completed=True, conversation_id=9f7f1fd2-f83d-4e62-9ced-ff2b8bd6db9a, detail=rev1 followup 5/6; kampanjrapport skill 3/3 (page, identical |
| agent | ok | 2026-10-26T21:00 | agent_id=AGENT_d6eb699a-5bbf-4705-9859-8347a1b2c7b6, is_draft=True, nodes=7 |
| grants | ok | 2026-10-27T22:47 | seconds=3, statements=7 |
| rq_check | ok | 2026-10-27T22:45 | count=71, failures=0 |

## Still to do by hand

- Add NORDMARK_POC to the database filter of the "Snowflake Demo" connection in Default Organization (browser, not the pipeline), then refresh the connection.

## Control points in the data

- **CP1** Grosshallen like-for-like lags the group and the gap is transactions not basket; Västerhamn sells far below its catchment potential (hero: Grosshallen Västerhamn)
- **CP2** Kronmat Fresh & Produce grows while its margin erodes; Sommarpris 2026 has top uplift and bottom margin (hero: Sommarpris 2026)
- **CP3** Dairy and Bread availability below 94 percent lines up with weaker like-for-like; Västerhamn has the worst availability in its banner (hero: Grosshallen Västerhamn)
- **CP4** Families visit Grosshallen less while other banners hold; a discount competitor opened 1.1 km from Västerhamn (hero: Families)
- **CP5** Peer store Nordstaden shows the playbook: higher private label share better availability and fewer markdowns (hero: Grosshallen Nordstaden)
- **CP6** Grosshallen non-food lost sales concentrate in SKUs from the three import suppliers whose purchase orders run late in the Teradata purchasing platform (hero: Grosshallen Västerhamn)
- **CP7** Kampanjrapport recreates the MicroStrategy grid for Kronmat week 2026-W36: the chain purchase forecast lands 18 percent over actual and CatBoost 6 percent (hero: Höstskörd 3 för 2)
- **CP8** Forecast error is highest on Multiköp perishables and worst at Grosshallen Västerhamn after the competitor opening; Nordstaden is in the best quartile (hero: Multiköp 3 för 2)
- **CP9** Over-forecasting costs margin on the illustrative cost data: SEK 9-15 m in Q3 2026 mostly perishable waste with Kronmat Multiköp the largest share (hero: Kronmat)
- **CP10** Upcoming perishable campaigns whose chain forecast exceeds CatBoost by more than 15 percent are flagged before delivery (hero: Äpplen & Päron)
- **CP11** The order adjustment draft for Äpplen & Päron week 2026-W42 cuts the purchase 15-22 percent in whole layers and protects at least SEK 300k of margin (hero: Äpplen & Päron)

## Follow-up questions

> Why is Grosshallen Västerhamn underperforming its catchment potential and are late inbound purchase orders from the import suppliers part of its non-food availability problem?

> /kampanjrapport Kronmat 2026-W36

> Why is forecast error highest on Multiköp 3 för 2 campaigns over the last 13 campaign weeks and what did the over-forecast cost us in margin in Q3 2026?
