# Meridian Clinician Network — demo build report

Built 2026-10-16 01:41 UTC · demo as-of 2026-09-30 · seed 20260930

## Where everything is

| Asset | Value |
|---|---|
| Snowflake | `MERIDIAN_POC.ANALYTICS` (12 tables, 4 views) |
| Wisdom deployment / workspace | proddemo / ET_WORKSPACE_01dc4f2105194dc286b9d69df2a89024 |
| Domain | Meridian Clinician Network — `ET_DOMAIN_97f519e3d9f943179957fd72ebbbf0ec` |
| Live App | Contract Reconciliation Review — `app_99d32a563228427a884b41a537fe5d13` |
| Follow-up chat | `dd7f4372-9f1a-49a2-a63f-7c7d14172863` |
| Agent (disabled) | Amendment Sync Watch — `AGENT_9ca79491-0366-4e7b-965e-1b030c1461ab` |
| Eval | set `5d8d726e-2935-40ea-a4a2-3cc25b5c1f6b` · last score 0.9444444444444443 |
| Domain Health run | job `ET_JOB_RUN_2b7604ceee4840508777b06bb3046208` (review in the Domain Health tab) |
| Documents | 7 uploaded |
| Instance | https://proddemo.askwisdom.ai |

## Links

- **Instance**: https://proddemo.askwisdom.ai
- **Domain**: https://proddemo.askwisdom.ai/domains/ET_DOMAIN_97f519e3d9f943179957fd72ebbbf0ec
- **Domain Health**: https://proddemo.askwisdom.ai/domains/ET_DOMAIN_97f519e3d9f943179957fd72ebbbf0ec/domain-health
- **Live App**: https://proddemo.askwisdom.ai/apps/contract-reconciliation-review--app_99d32a563228427a884b41a537fe5d13
- **Follow-up chat**: https://proddemo.askwisdom.ai/chat/dd7f4372-9f1a-49a2-a63f-7c7d14172863
- **Live App build conversation**: https://proddemo.askwisdom.ai/chat/cd247834-0493-4c29-b2f6-fd41be0e1b99
- **Agent**: https://proddemo.askwisdom.ai/agents/AGENT_9ca79491-0366-4e7b-965e-1b030c1461ab/edit
- **Connection**: https://proddemo.askwisdom.ai/connections/et-connection-678570afa5f14afe9bb146040e70c28c

## Steps

| Step | Status | When | Notes |
|---|---|---|---|
| generate | ok | 2026-10-15T22:39 | counts={'CONTRACTS': 428, 'CONTRACT_BILLING_SCHEDULE': 2709, 'CONTR, mismatches=[], missing=[], schema_errors=[] |
| validate | ok | 2026-10-16T00:03 | failed=0, failures=[], passed=67 |
| ddl | ok | 2026-10-15T21:57 | seconds=8, statements=21 |
| load | ok | 2026-10-15T22:40 | counts={'CONTRACTS': 428, 'CONTRACT_BILLING_SCHEDULE': 2709, 'CONTR, failures=[], seconds=40, tables=['CUSTOMERS', 'PRODUCTS', 'RECONCILIATION_CONTROLS', 'CONTRA |
| validate_snowflake | ok | 2026-10-15T22:51 | failed=0, failures=[], passed=66 |
| rq_check_snowflake | ok | 2026-10-16T00:07 | count=48, failures=0 |
| metrics_check | ok | 2026-10-15T22:17 | count=27, failures=[] |
| docs | ok | 2026-10-15T22:22 | failures=[], rendered=['/Users/chick/Desktop/Claude Code/wisdom_automated_demo_cre |
| publish.connection | ok | 2026-10-15T22:24 | connection_id=et-connection-678570afa5f14afe9bb146040e70c28c, created=False |
| publish.domain | ok | 2026-10-15T22:25 | created=True, domain_id=ET_DOMAIN_97f519e3d9f943179957fd72ebbbf0ec |
| publish.database | ok | 2026-10-15T22:27 | missing=[], tables=16 |
| publish.instructions | ok | 2026-10-15T22:27 | chars=5305 |
| publish.lookup | ok | 2026-10-15T22:27 | changed=5, missing=[] |
| publish.documents | ok | 2026-10-15T22:27 | dataset_id=ET_DATASET_9ad15afc686147faa03ea201366c916a, uploaded=7 |
| eval | ok | 2026-10-16T01:31 | consistently_failing=1, consistently_passing=43, flaky=4, passed=45 |
| health | ok | 2026-10-16T01:41 | already_queued=False, analysis_status=RUNNING, code=OK, job_run_id=ET_JOB_RUN_1ed9eb7a7bbb4fc2bb774b2855426e29 |
| app | ok | 2026-10-16T01:13 | app_id=app_99d32a563228427a884b41a537fe5d13, conversation_id=cd247834-0493-4c29-b2f6-fd41be0e1b99, note=build finished server-side at 00:36 (liveSpecVersion 2) afte, tabs=['Findings Queue', 'Case Review', 'Export'] |
| chat | ok | 2026-10-16T01:21 | completed=False, conversation_id=dd7f4372-9f1a-49a2-a63f-7c7d14172863, note=answer completed at 01:19:29 (about 7.5 min); the text judge, score=3/5 by text match; all 5 points present in the answer's line |
| agent | ok | 2026-10-16T00:20 | agent_id=AGENT_9ca79491-0366-4e7b-965e-1b030c1461ab, is_draft=True, nodes=5 |
| document_chat | ok | 2026-10-16T01:28 | conversation_id=434f7d43-c444-43fe-8c8e-b4338c3be9f7, note=answered from MCN-2025-0142-A2.pdf in the S3 archive: quoted, question=What does Amendment 2 to agreement MCN-2025-0142 say about t |
| grants | ok | 2026-10-15T21:58 | seconds=2, statements=7 |
| publish.extraction | ok | 2026-10-16T00:13 | accepted={'accepted': 357, 'by_family': {'descriptions': 150, 'knowle, coverage={'knowledge': {'in_domain': 188, 'story_facts': 20}, 'metric, job_status=JOB_RUN_STATUS_SUCCESS, run_id=ET_JOB_RUN_1baf59949c9a421f86c5816203fba53b |
| publish.s3_dataset | ok | 2026-10-16T01:24 | connection_id=et-connection-6dc77f2c90d7487ebe8ebb896d97f28e, dataset_id=ET_DATASET_7ecd633c5c2c4150b0bfa35076153235, extracted=0, files=78 |
| rq_check | ok | 2026-10-16T00:03 | count=48, failures=0 |

## Still to do by hand

- Add MERIDIAN_POC to the database filter of the "Snowflake Demo" connection in Default Organization (done in the browser during the build, never by the pipeline).
- The S3 connectivity test left a 2-byte marker at meridian_contracts/_connectivity_check.txt (the uploader key cannot delete); remove it by hand if wanted.

## Control points in the data

- **CP1** Three-way match at Q3 close - 15-20% of live contract chains fail at least one check with more than 5M USD of exposure (hero: the 2026-09-30 three-way match)
- **CP2** Halvorsen Therapeutics chain of three amendments has drifted across both systems; amended chains fail far more often (hero: Halvorsen Therapeutics)
- **CP3** Contract billing milestones missing from the NetSuite billing schedule (hero: milestone-billed chains)
- **CP4** Findings split across the three owning teams; pharma carries the variance dollars; one account owner stands out (hero: Dana Whitfield)

## Follow-up question

> Show me the full amendment lineage for Halvorsen Therapeutics and where Salesforce and NetSuite each stand relative to the latest amendment and what the dollar exposure is
