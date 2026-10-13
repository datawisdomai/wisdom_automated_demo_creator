# Keelstone Data Systems — Demo Story Guide

As-of date 2026-10-12 (FY27-Q2). All figures below come from the generated data and are verified by
`checks.py` (DuckDB and Snowflake). Use this guide to know what a correct answer looks like.

## The hero arc: Americas East renewals are slipping

| Question | Expected answer |
|---|---|
| What is our current ARR? | About $501M (Finance definition, V_ARR_MONTHLY at 2026-10-12). |
| What is our renewal rate this fiscal year vs last? | Company FY26 about 90%; FY27 to date about 85%. |
| Which region's renewal rate has dropped the most this fiscal year? | Americas East: ~90% FY26 to ~79% FY27 (11 pts). Other regions within ~3 pts of FY26. |
| What is driving it? | KS-7000 end of support (2027-01-31, bulletin PLB-2026-014) and the KeelOS 9.14.2 P1 cases (66 in Americas East since July vs ≤4 elsewhere). Most of the shortfall is PENDING (~20% of due ARR), churn is small. |
| How much ARR is up for renewal there in the next 90 days? | About $28M, with about $13M flagged AT_RISK; reasons: Open P1 case (~$7.4M) and End of support product (~$5.6M). |
| Which customers to call first? | Largest at-risk ARR in Americas East; Brightwater Mutual Insurance, Tidewater Health Alliance, Pinecrest Regional Health are the named hero accounts. |
| What are customers saying? | P1 case notes on 9.14.2 mention the January renewal, migration quotes to KS-9000 and requests for a written RCA (51 cases mention "renewal"). |

## Governance beat: two ARRs

| Question | Expected answer |
|---|---|
| Why does Sales Ops report a different ARR? | Finance ARR for September 2026 about $500M; Sales Ops about $27M (5.4%) higher because lapsed contracts with open renewal opportunities are still counted. Largest gap in Americas East (7.0%). |
| Which definition is certified? | Finance (Metric Definitions Standard v3.2 section 3); the Sales Ops figure is "Pipeline ARR". |

## Cloud

| Question | Expected answer |
|---|---|
| How is cloud consumption growing? | Jun–Sep 2026 consumption about 78% above Jun–Sep 2025 (150 accounts). |
| Who is under-utilising their commit? | 27 enterprise accounts below 60% of FY27 commit, about $3.6M unconsumed. Overall FY27 utilisation about 98%. |

## Partners

| Question | Expected answer |
|---|---|
| Whose attach rate fell? | Altura Technology Partners: 77% FY26 to 61% FY27 on new systems; other large partners flat near 76%. |

## Installed base facts to recognise

- 2,310 active arrays: KS-7000 679 (272 in Americas East), KS-5000 639, KS-9000 583, HD-3000 409.
- About $104M of ARR sits on KS-7000 arrays.
- Americas East firmware today: 386 systems on 9.14.2, 144 already on 9.14.3.
- 11 P1 cases still open in Americas East, all on 9.14.2.
