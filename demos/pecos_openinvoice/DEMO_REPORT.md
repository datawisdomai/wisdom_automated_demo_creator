# Pecos Ridge OpenInvoice Supply Chain — demo build report

Built 2026-10-19 19:26 UTC · demo as-of 2026-09-30 · seed 20261019

## Where everything is

| Asset | Value |
|---|---|
| Snowflake | `PECOS_RIDGE_SCM_OPENINVOICE.OPENINVOICE` (12 tables, 6 views) |
| Wisdom deployment / workspace | digitz / ET_WORKSPACE_01dc4f2105194dc286b9d69df2a89024 |
| Domain | O&G — `ET_DOMAIN_4804a0b2ffcd484ab6d7cf410dceed55` (EXISTING, shared — this demo added `PECOS_RIDGE_SCM_OPENINVOICE.OPENINVOICE`) |
| Live App | Pecos Ridge Supply Chain Spend Cube — `app_4b81a7c81be443f88dde538298003164` |
| Follow-up chat | `753bf304-424d-4067-845c-96ea503d6119` |
| Agent (disabled) | Price Variance Watch — `AGENT_29a65fdc-fd29-4d84-9264-e5d96387a39b` |
| Eval | set `060fed35-54ae-46eb-8061-51e7a89b49d3` · last score 0.9249999999999999 |
| Domain Health run | job `ET_JOB_RUN_4bdd8470db6848f9b2ceb8fd40c75c56` (review in the Domain Health tab) |
| Documents | 0 uploaded; S3 dataset `ET_DATASET_0ca65a7fffa941ff99c3677e1c02e6e3` on connection `et-connection-7a91e471f568495d9eed2a2f2006d7b1` |
| Instance | https://digitz.wisdom.ai |

## Links

- **Instance**: https://digitz.wisdom.ai
- **Domain**: https://digitz.wisdom.ai/domains/ET_DOMAIN_4804a0b2ffcd484ab6d7cf410dceed55
- **Domain Health**: https://digitz.wisdom.ai/domains/ET_DOMAIN_4804a0b2ffcd484ab6d7cf410dceed55/domain-health
- **Live App**: https://digitz.wisdom.ai/apps/pecos-ridge-supply-chain-spend-cube--app_4b81a7c81be443f88dde538298003164
- **Follow-up chat**: https://digitz.wisdom.ai/chat/753bf304-424d-4067-845c-96ea503d6119
- **Live App build conversation**: https://digitz.wisdom.ai/chat/d4e4c2be-2077-4035-886e-4ce0e4717619
- **Agent**: https://digitz.wisdom.ai/agents/AGENT_29a65fdc-fd29-4d84-9264-e5d96387a39b/edit
- **Connection**: https://digitz.wisdom.ai/connections/et-connection-c4c6ff12a0b94fb0908ddad0099488d1
- **S3 document archive connection**: https://digitz.wisdom.ai/connections/et-connection-7a91e471f568495d9eed2a2f2006d7b1

## Steps

| Step | Status | When | Notes |
|---|---|---|---|
| generate | ok | 2026-10-19T18:31 | counts={'DATA_DICTIONARY': 175, 'OI_ERP_INTEGRATION_LOG': 23556, 'O, mismatches=[], missing=[], schema_errors=[] |
| validate | ok | 2026-10-19T17:36 | failed=0, failures=[], passed=47 |
| ddl | ok | 2026-10-19T18:33 | seconds=3, statements=23 |
| load | ok | 2026-10-19T18:34 | counts={'DATA_DICTIONARY': 175, 'OI_ERP_INTEGRATION_LOG': 23556, 'O, failures=[], seconds=16, tables=['OI_REF_WELL', 'OI_REF_AFE', 'OI_REF_VENDOR', 'OI_ERP_INTEG |
| validate_snowflake | ok | 2026-10-19T18:34 | failed=0, failures=[], passed=51 |
| rq_check_snowflake | ok | 2026-10-19T18:34 | count=40, failures=0 |
| metrics_check | ok | 2026-10-19T18:29 | count=26, failures=[] |
| docs | ok | 2026-10-19T17:38 | failures=[], generated=63, rendered=['/Users/chick/Desktop/Claude Code/wisdom_automated_demo_cre |
| publish.connection | ok | 2026-10-19T17:38 | connection_id=et-connection-c4c6ff12a0b94fb0908ddad0099488d1, created=True |
| publish.domain | ok | 2026-10-19T17:38 | created=False, domain_id=ET_DOMAIN_4804a0b2ffcd484ab6d7cf410dceed55, existing=True |
| publish.database | ok | 2026-10-19T17:39 | missing=[], tables=14 |
| publish.lookup | ok | 2026-10-19T17:40 | changed=4, missing=[] |
| publish.documents | ok | 2026-10-19T17:40 | uploaded=0 |
| publish.extraction | failed | 2026-10-19T19:12 | accepted={'accepted': 2, 'accepted_ids': ['ET_MM_SUGGESTION_affb69998, coverage={'knowledge': {'in_domain': 404, 'story_facts': 42}, 'metric, job_status=JOB_RUN_STATUS_SUCCESS, run_id=ET_JOB_RUN_9c9a0bf0c8914369ad8cec8cf4ea3612 |
| publish.s3_dataset | ok | 2026-10-19T18:37 | connection_id=et-connection-7a91e471f568495d9eed2a2f2006d7b1, dataset_id=ET_DATASET_0ca65a7fffa941ff99c3677e1c02e6e3, extracted=0, files=63 |
| eval | ok | 2026-10-19T19:25 | consistently_failing=1, consistently_passing=36, flaky=3, passed=38 |
| health | ok | 2026-10-19T19:26 | analysis_status=RUNNING, quick_check_job=ET_JOB_RUN_4bdd8470db6848f9b2ceb8fd40c75c56, trigger={'evalRunId': 'ET_JOB_RUN_25b72ca5f39b495b8591d5938a8a805e', |
| app | ok | 2026-10-19T19:23 | app_id=app_4b81a7c81be443f88dde538298003164, conversation_id=d4e4c2be-2077-4035-886e-4ce0e4717619, live_spec_version=2, seconds=768.3 |
| chat | ok | 2026-10-19T19:01 | answer_chars=156, completed=True, conversation_id=753bf304-424d-4067-845c-96ea503d6119, hits=['two suppliers: Corrosion Control Chem (CorroShield CS-7000 |
| agent | ok | 2026-10-19T18:50 | agent_id=AGENT_29a65fdc-fd29-4d84-9264-e5d96387a39b, is_draft=True, nodes=8 |
| grants | ok | 2026-10-19T17:01 | error=002003 (02000): SQL compilation error:
Database 'PECOS_RIDGE, failed_index=1, seconds=2, statements=7 |
| rq_check | ok | 2026-10-19T19:09 | count=40, failures=0 |
| s3 | ok | 2026-10-19T17:38 | already_there=0, bucket=wisdom-proddemo, error=S3 bucket not configured (set S3_BUCKET in .env), files=63 |

## Control points in the data

- **CP1** Hidden price dispersion: the same water-soluble corrosion inhibitor costs 20%+ more per gallon from one supplier and in small packs; invisible in SPEND_INVOICE (hero: Corrosion inhibitor, water-soluble, filming amine)
- **CP2** Proppant: 100 mesh from three mines on delivered vs FOB plus last-mile pricing; Redline invoiced above its pricebook rate in 2026 and the lines are disputed (hero: Redline Sand LLC)
- **CP3** OCTG: 5-1/2 in 20# P-110 casing is described five different ways and priced per joint or per foot; normalised to $/ft the spread is visible (hero: Production casing 5-1/2 in 20 lb/ft P-110 BTC)
- **CP4** Classification backlog: about 8% of 2026 line spend has no approved generic product, concentrated in rentals and distributor items (hero: Hector Brown's steward queue)
- **CP5** Operational hook: completion-phase generic product cost per lateral foot for 2025-26 wells and a +10% proppant sensitivity against the Q3 reforecast (hero: 2025-26 completions)

## Follow-up question

> What did we pay per gallon for water-soluble corrosion inhibitor by supplier and pack size in 2025 and how much would we have saved at the best observed price
