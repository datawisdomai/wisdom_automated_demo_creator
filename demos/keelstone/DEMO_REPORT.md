# Keelstone Data Systems — demo build report

Built 2026-10-13 04:46 UTC · demo as-of 2026-10-12 · seed 20261012

## Where everything is

| Asset | Value |
|---|---|
| Snowflake | `KEELSTONE_POC.ANALYTICS` (13 tables, 8 views) |
| Wisdom deployment / workspace | proddemo / ET_WORKSPACE_01dc4f2105194dc286b9d69df2a89024 |
| Domain | Keelstone Data Systems — `ET_DOMAIN_f6df7b3a5120419383a6babb46d0f65d` |
| Live App | Renewals and Installed Base Cockpit — `app_4c27c3346904444482aae6d66649c4b6` |
| Follow-up chat | `e8daec43-eb9c-409d-a0a9-ef43ba576350` |
| Agent (disabled) | Renewal Risk Watch — `AGENT_146c8d79-a16a-47b7-b3da-d8511b10e515` |
| Eval | set `88a08951-b850-4c98-b0f2-a4529051af35` · last score 0.9236111111111112 |
| Domain Health run | job `ET_JOB_RUN_5b96c547fd4f4f2882e665dbc776c09c` (review in the Domain Health tab) |
| Documents | 7 uploaded |
| Instance | https://proddemo.askwisdom.ai |

## Links

- **Instance**: https://proddemo.askwisdom.ai
- **Domain**: https://proddemo.askwisdom.ai/domains/ET_DOMAIN_f6df7b3a5120419383a6babb46d0f65d
- **Domain Health**: https://proddemo.askwisdom.ai/domains/ET_DOMAIN_f6df7b3a5120419383a6babb46d0f65d/domain-health
- **Live App**: https://proddemo.askwisdom.ai/apps/renewals-and-installed-base-cockpit--app_4c27c3346904444482aae6d66649c4b6
- **Follow-up chat**: https://proddemo.askwisdom.ai/chat/e8daec43-eb9c-409d-a0a9-ef43ba576350
- **Live App build conversation**: https://proddemo.askwisdom.ai/chat/f897adbd-3dcf-46d1-b7ce-ea1a4b803171
- **Agent**: https://proddemo.askwisdom.ai/agents/AGENT_146c8d79-a16a-47b7-b3da-d8511b10e515/edit
- **Connection**: https://proddemo.askwisdom.ai/connections/et-connection-678570afa5f14afe9bb146040e70c28c

## Steps

| Step | Status | When | Notes |
|---|---|---|---|
| generate | ok | 2026-10-13T00:29 | counts={'CLOUD_CONSUMPTION_MONTHLY': 2119, 'CONTRACTS': 10684, 'CUS, mismatches=[], missing=[], schema_errors=[] |
| validate | failed | 2026-10-13T00:29 | failed=1, failures=['SUPPORT_CASES has 5,282 rows'], passed=73 |
| ddl | ok | 2026-10-13T00:14 | seconds=12, statements=28 |
| load | ok | 2026-10-13T00:29 | counts={'CLOUD_CONSUMPTION_MONTHLY': 2119, 'CONTRACTS': 10684, 'CUS, failures=[], seconds=3, tables=['SUPPORT_CASES'] |
| validate_snowflake | ok | 2026-10-13T00:30 | failed=0, failures=[], passed=74 |
| rq_check_snowflake | ok | 2026-10-13T00:23 | count=48, failures=0 |
| metrics_check | ok | 2026-10-13T00:23 | count=37, failures=[] |
| docs | ok | 2026-10-13T00:30 | failures=[], rendered=['/Users/chick/Desktop/Claude Code/wisdom_automated_demo_cre |
| publish.connection | ok | 2026-10-13T00:36 | connection_id=et-connection-678570afa5f14afe9bb146040e70c28c, created=False |
| publish.domain | ok | 2026-10-13T00:36 | created=False, domain_id=ET_DOMAIN_f6df7b3a5120419383a6babb46d0f65d |
| publish.database | ok | 2026-10-13T00:36 | missing=[], tables=21 |
| publish.instructions | ok | 2026-10-13T00:36 | chars=5968 |
| publish.knowledge | ok | 2026-10-13T00:36 | added=49, existing=0, total=49 |
| publish.metrics | ok | 2026-10-13T04:10 | created=['p1_cases', 'open_cases', 'avg_csat', 'bookings'], failed=[], total=37 |
| publish.reviewed_queries | ok | 2026-10-13T04:10 | added=48, existing=0, total=48 |
| publish.lookup | ok | 2026-10-13T04:10 | changed=5, missing=[] |
| publish.documents | ok | 2026-10-13T04:11 | dataset_id=ET_DATASET_a5c2a5203cde4cf1af9102cf64ec395b, uploaded=7 |
| eval | ok | 2026-10-13T04:29 | consistently_failing=2, consistently_passing=43, flaky=3, passed=45 |
| health | ok | 2026-10-13T04:15 | already_queued=False, code=OK, job_run_id=ET_JOB_RUN_5b96c547fd4f4f2882e665dbc776c09c |
| app | ok | 2026-10-13T04:20 | app_id=app_4c27c3346904444482aae6d66649c4b6, conversation_id=f897adbd-3dcf-46d1-b7ce-ea1a4b803171, live_spec_version=2, seconds=531.3 |
| chat | ok | 2026-10-13T04:22 | completed=True, conversation_id=e8daec43-eb9c-409d-a0a9-ef43ba576350, judge_note=lexical judge saw 3/5 because the figures (79.09% vs 90.27%,, judged_by=Claude (browser review of the answer widgets, 2026-10-13) |
| agent | ok | 2026-10-13T04:16 | agent_id=AGENT_146c8d79-a16a-47b7-b3da-d8511b10e515, is_draft=True, nodes=9 |
| grants | ok | 2026-10-13T00:14 | seconds=1, statements=7 |
| publish.extraction | ok | 2026-10-13T04:29 | job_status=JOB_RUN_STATUS_SUCCESS, run_id=ET_JOB_RUN_a139c7d31965461199ac748c60a607e5, uploaded=0 |

## Still to do by hand

- Add KEELSTONE_POC to the database filter of the "Snowflake Demo" connection in Default Organization (done in the browser during the build, not by the pipeline).

## Control points in the data

- **CP1** Americas East renewal rate slips on KS-7000 end of support and KeelOS 9.14 P1 cases (hero: Americas East)
- **CP2** Sales Ops ARR exceeds certified Finance ARR because open renewal quotes are counted
- **CP3** Keelstone Cloud Volumes consumption grows while enterprise commits go unused (hero: Keelstone Cloud Volumes)
- **CP4** Altura Technology Partners support attach rate falls while peer partners hold (hero: Altura Technology Partners)

## Follow-up question

> Which region's renewal rate has dropped the most this fiscal year and what is driving it and how much ARR is up for renewal there in the next 90 days?
