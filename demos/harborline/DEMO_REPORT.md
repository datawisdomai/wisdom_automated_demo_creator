# Harborline Private Capital — demo build report

Built 2026-10-16 02:17 UTC · demo as-of 2026-10-15 · seed 20261015

## Where everything is

| Asset | Value |
|---|---|
| Snowflake | `HARBORLINE_POC.ANALYTICS` (10 tables, 9 views) |
| Wisdom deployment / workspace | proddemo / ET_WORKSPACE_01dc4f2105194dc286b9d69df2a89024 |
| Domain | Harborline Private Capital — `ET_DOMAIN_89571564869a4aabaf43849235f7ee4e` |
| Live App | Custom Index Studio — `app_cda547e0db5a4719bc27f597afa9161d` |
| Follow-up chat | `ac368c43-b2b6-4369-8284-7a2f1db7b2f0` |
| Agent (disabled) | Subscription Line Watch — `AGENT_286770aa-a5fc-41db-9b3e-e522f7a97ae1` |
| Eval | set `d93329a4-9a55-44ea-a998-c166a3bfb794` · last score 0.9191919191919192 |
| Domain Health run | job `ET_JOB_RUN_a01648479dc1402195a23c39aa18f3c9` (review in the Domain Health tab) |
| Documents | 5 uploaded |
| Instance | https://proddemo.askwisdom.ai |

## Links

- **Instance**: https://proddemo.askwisdom.ai
- **Domain**: https://proddemo.askwisdom.ai/domains/ET_DOMAIN_89571564869a4aabaf43849235f7ee4e
- **Domain Health**: https://proddemo.askwisdom.ai/domains/ET_DOMAIN_89571564869a4aabaf43849235f7ee4e/domain-health
- **Live App**: https://proddemo.askwisdom.ai/apps/custom-index-studio--app_cda547e0db5a4719bc27f597afa9161d
- **Follow-up chat**: https://proddemo.askwisdom.ai/chat/ac368c43-b2b6-4369-8284-7a2f1db7b2f0
- **Live App build conversation**: https://proddemo.askwisdom.ai/chat/8fdc1f09-ff5a-4e0b-a76d-35dea6af3aaa
- **Agent**: https://proddemo.askwisdom.ai/agents/AGENT_286770aa-a5fc-41db-9b3e-e522f7a97ae1/edit
- **Connection**: https://proddemo.askwisdom.ai/connections/et-connection-678570afa5f14afe9bb146040e70c28c

## Steps

| Step | Status | When | Notes |
|---|---|---|---|
| generate | ok | 2026-10-16T01:36 | counts={'ALLOCATORS': 5, 'ALLOCATOR_COMMITMENTS': 156, 'BENCHMARKS', mismatches=[], missing=[], schema_errors=[] |
| validate | ok | 2026-10-16T01:34 | failed=0, failures=[], passed=61 |
| ddl | ok | 2026-10-16T01:30 | seconds=12, statements=24 |
| load | ok | 2026-10-16T01:35 | counts={'ALLOCATORS': 5, 'ALLOCATOR_COMMITMENTS': 156, 'BENCHMARKS', failures=[], seconds=32, tables=['MANAGERS', 'BENCHMARKS', 'FUNDS', 'ALLOCATORS', 'ALLOCATOR |
| validate_snowflake | ok | 2026-10-16T01:35 | failed=0, failures=[], passed=61 |
| rq_check_snowflake | ok | 2026-10-16T01:38 | count=33, failures=0 |
| metrics_check | ok | 2026-10-16T01:38 | count=29, failures=[] |
| docs | ok | 2026-10-16T01:43 | failures=[], generated=0, rendered=['/Users/chick/Desktop/Claude Code/wisdom_automated_demo_cre |
| publish.connection | ok | 2026-10-16T01:46 | connection_id=et-connection-678570afa5f14afe9bb146040e70c28c, created=False |
| publish.domain | ok | 2026-10-16T01:46 | created=False, domain_id=ET_DOMAIN_89571564869a4aabaf43849235f7ee4e |
| publish.database | ok | 2026-10-16T01:48 | missing=[], tables=19 |
| publish.instructions | ok | 2026-10-16T01:48 | chars=4022 |
| publish.lookup | ok | 2026-10-16T01:48 | changed=6, missing=[] |
| publish.documents | ok | 2026-10-16T01:48 | dataset_id=ET_DATASET_b4e1f03cec864905b930bbf97971d09c, uploaded=5 |
| eval | ok | 2026-10-16T02:13 | consistently_failing=2, consistently_passing=29, flaky=2, passed=31 |
| health | ok | 2026-10-16T02:17 | analysis_status=RUNNING, quick_check_job=ET_JOB_RUN_a01648479dc1402195a23c39aa18f3c9, trigger={'evalRunId': None, 'message': 'Analysis started.', 'runGrou |
| app | ok | 2026-10-16T02:13 | app_id=app_cda547e0db5a4719bc27f597afa9161d, conversation_id=8fdc1f09-ff5a-4e0b-a76d-35dea6af3aaa, live_spec_version=2, seconds=576.6 |
| chat | ok | 2026-10-16T02:16 | completed=True, conversation_id=ac368c43-b2b6-4369-8284-7a2f1db7b2f0, score=1.0, seconds=107.2 |
| agent | ok | 2026-10-16T02:15 | agent_id=AGENT_286770aa-a5fc-41db-9b3e-e522f7a97ae1, is_draft=True, nodes=8 |
| grants | ok | 2026-10-16T01:30 | seconds=2, statements=7 |
| publish.extraction | ok | 2026-10-16T02:03 | accepted={'accepted': 304, 'by_family': {'descriptions': 288, 'knowle, coverage={'knowledge': {'in_domain': 131, 'story_facts': 22}, 'metric, job_status=JOB_RUN_STATUS_SUCCESS, run_id=ET_JOB_RUN_f554bea04b1945cd8e1b6488dc80838e |
| publish.s3_dataset | ok | 2026-10-16T02:03 | attached=False |

## Still to do by hand

- Add HARBORLINE_POC to the database filter of the "Snowflake Demo" connection in Default Organization (done in the browser during the build, never by the pipeline).

## Control points in the data

- **CP1** Custom index: North American buyout funds of vintages 2015-2020 beat the Harborline Broad Private Equity Index; mid-market beats mega (hero: NA buyout 2015-2020 cohort vs HPCI-BROAD-PE)
- **CP2** Subscription lines flatter early IRR; the gap closes with age; Calder Ridge IV matches its Q2 2026 quarterly report (hero: Calder Ridge Capital Partners IV)
- **CP3** Distribution drought: 2021-2022 vintages return capital far more slowly than 2014-2016 vintages did at the same age (hero: 2021-2022 vintages)
- **CP4** Westbrook State Retirement System's 2018 vintage sleeve lags its matching benchmarks because of two venture funds (hero: Westbrook State Retirement System)

## Follow-up question

> Compare Westbrook State Retirement System's commitments by vintage year to the matching Harborline benchmarks and tell me which vintage lags the most and which funds explain the gap
