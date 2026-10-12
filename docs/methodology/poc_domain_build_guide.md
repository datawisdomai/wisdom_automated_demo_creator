<!-- Converted from WisdomAI_POC_Domain_Build_Guide.docx (v1.0, WisdomAI Sales Engineering). Source of the 5-phase build method and Prompts A-F. -->


WisdomAI × Snowflake
POC Domain Build Guide
A repeatable engineering playbook for building
demo environments from first prompt to live demo

5 Phases
Schema + Data + Semantics + Test + Demo
Python + SQL
Snowflake-native loading via write_pandas
wACE Bootstrap
Domain knowledge document for WisdomAI
Repeatable
Works for any industry vertical

Version 1.0  ·  WisdomAI Sales Engineering  ·  Confidential

Contents
1.  Overview & Purpose	3
2.  What You Need to Get Started	4
3.  Phase 1 — Domain & Prospect Research	5
4.  Phase 2 — Schema Design & Snowflake DDL	7
5.  Phase 3 — Data Generation & Loading	10
6.  Phase 4 — wACE Domain Bootstrap Document	14
7.  Phase 5 — Testing, Iteration & Demo Questions	18
8.  Snowflake Infrastructure Reference	22
9.  Quality Checklist	24
10.  Appendix: Prompt Templates	25

1 · Overview & Purpose
This guide documents the end-to-end process for building a WisdomAI proof-of-concept demo environment in Snowflake. It is drawn from real builds across multiple industries — P&C Insurance, Managed Care Finance, Healthcare RCM, Manufacturing, and Retail — and captures the prompts, decisions, and best practices that make each domain land in a live demo.

A well-built POC domain has five components:

#
Component
What it is
1
Snowflake DDL
Database, schema, tables, views — the structural container for all synthetic data.
2
Synthetic Data
Python-generated CSV data loaded via write_pandas() or COPY INTO. Narrative-controlled and realistic.
3
wACE Bootstrap Doc
A markdown knowledge document that teaches WisdomAI's AI the domain — table semantics, synonyms, tribal knowledge, business nuances.
4
Demo Questions
A scripted set of 10–35 questions that walk through the domain story. Covers single-fact, analytical, and story-arc question types.
5
Supporting PDFs
Realistic synthetic documents (reports, memos, contracts) that the AI can reason over alongside the structured data.

→ The goal: Make the AI sound like it has worked in that industry for years — before the prospect has answered a single question.

2 · What You Need to Get Started
2.1  From the Prospect / Account Team
Before opening a code editor, collect this information. The quality of your inputs directly determines the quality of the demo.

Input
Example (Insurance POC)
Why it matters
Company name & industry
Midwest P&C insurer, commercial lines focus
Drives research, entity naming, and business nuances
Buying audience / personas
CUO, Head of Claims, VP Actuarial, Head of Broker Relations
Each persona needs 2-3 questions that speak to their pain
Primary pain points
Renewal attrition, loss ratio variance, broker channel visibility
These become your narrative control points in the data
Data sources in use
Guidewire PolicyCenter, Duck Creek Claims, Majesco
Name-drops in the domain doc make the AI credible
Key metrics they track
Combined ratio, loss ratio, retention rate, LAE
Must be computable from your schema
Discovery questions answered
Claims severity spiking in Southeast commercial auto
Seed the specific narrative into the data generator
Any RFP / evaluation criteria
15-question eval set, must answer in < 3 seconds
Shapes the question bank and performance requirements

2.2  Snowflake Environment
Every POC uses a dedicated database. You will need:

	•	Snowflake account identifier (format: ORGNAME-ACCOUNTNAME, e.g. XMSPMYE-PAB51256)
	•	Role: SYSADMIN — required to CREATE DATABASE, CREATE SCHEMA, CREATE STAGE
	•	Warehouse: any size (XSMALL is fine for POC data volumes)
	•	Auth: Programmatic Access Token (PAT) — preferred over password for scripting

Naming convention: Use DB name = PROSPECT_POC or INDUSTRY_POC (e.g. INSURANCE_POC, CENTENE_DEMO, MFGDEMO). Schema name = PROSPECT or DOMAIN (e.g. INSURANCE_POC, FINANCE_ANALYTICS, APEX_INDUSTRIAL). Keep it generic enough to reuse the domain for similar prospects.

2.3  Local Dev Environment
Python 3.10+ with the following packages:

pip install snowflake-connector-python[pandas] faker numpy pandas python-dotenv

Create a .env file in your project directory (never commit this to git):

SNOWFLAKE_ACCOUNT=XMSPMYE-PAB51256
SNOWFLAKE_USER=JUSTIN
SNOWFLAKE_PAT=your_programmatic_access_token_here
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_ROLE=SYSADMIN

Generate a PAT token in Snowflake (run once, copy the token immediately):

ALTER USER YOUR_USER ADD PROGRAMMATIC ACCESS TOKEN your_poc_token ROLE_RESTRICTION = SYSADMIN;

PHASE 1  Domain & Prospect Research

3.1  Goal
Build enough domain knowledge to generate realistic data and make the AI sound credible to someone who has worked in that industry for 20 years. Do not skip this step — a demo that uses wrong terminology gets dismissed immediately.

3.2  Research Prompt
Use this prompt with Claude (or your preferred AI) before any schema design:

📋 PROMPT: I am building a WisdomAI POC demo for [COMPANY NAME], a [INDUSTRY DESCRIPTION]. The buying audience is [PERSONAS]. Their primary pain points are [PAIN POINTS]. Research this company and industry thoroughly, then give me: (1) the key data sources and systems they use, (2) the 5-7 most important KPIs and metrics the buying audience tracks, (3) realistic entity names I should use in synthetic data, (4) any industry-specific terminology and business nuances I should embed in the domain, (5) a list of narrative control points — specific data anomalies I should engineer into the dataset to drive demo moments.

3.3  Output to Capture
From research, document the following before moving to schema design:

Output
Insurance POC Example
KPI list (5-8 metrics)
Combined ratio, loss ratio, LAE ratio, retention rate, NWP, policy count, average premium
Entity names
Policies: HO3, BOP, CPP, WC, CA. Carriers: Guidewire, Duck Creek. States: FL, TX, GA, CA, NY
Narrative control points
Southeast commercial auto loss spike (Q3-Q4), broker X driving high attrition, renewal retention < 70% in coastal properties
Buying persona pain
CUO: combined ratio trending above 100. Head of Claims: severity variance. VP Actuarial: reserve adequacy. Head of Broker: channel performance
Terminology / synonyms
Policy = risk = account. Premium = written premium = NWP. Claim = loss. Renewal = re-underwriting. Lapse = non-renewal = attrition
Systems in use
Guidewire PolicyCenter, Duck Creek Claims, Majesco Billing, ISO/ACORD forms, Verisk analytics

3.4  Narrative Architecture
Before writing DDL, design your narrative. A great POC demo has 3-5 'story arcs' — connected sequences of questions that build to a revelation. Each arc should be answerable from the data you're about to build.

Insurance POC example: Arc 1 — Loss ratio is deteriorating. Why? → Commercial auto in Southeast. Why there? → Rate inadequacy + severity spike. Arc 2 — Renewal retention is dropping. Where? → Coastal property, post-reinsurance cost increases. Who? → One broker driving 40% of non-renewals. Arc 3 — What should the CUO do? → Segment, reprice, or exit coastal CAT exposure.

PHASE 2  Schema Design & Snowflake DDL

4.1  Schema Design Principles
These principles have been validated across every POC build:

Principle
Guidance
Dimension + Fact model
Build 2-4 dimension/reference tables first (entities, categories, geographies). Then build 2-5 fact tables. Avoid wide flat tables — joins make demo moments richer.
One schema per domain
All tables in a single schema. DB = PROSPECT_POC, Schema = DOMAIN_NAME. Never split across schemas unless you have a clear reason (e.g. RAW vs ANALYTICS).
Declare FKs, don't enforce
Add FK relationships as REFERENCES comments in DDL. WisdomAI uses these for semantic understanding. Snowflake won't enforce them — that's fine for synthetic data.
Pre-build analytical views
Create 3-6 views that pre-compute your most important metrics. Named V_COMBINED_RATIO, V_RETENTION_BY_SEGMENT, etc. The AI hits views faster and more reliably than reconstructing metrics from raw tables.
Tightly scoped domain
8-14 objects is ideal. More tables = more ambiguity for the AI. If a table doesn't answer a demo question, leave it out.
Include a DATA_DICTIONARY table
One row per column with: TABLE_NAME, COLUMN_NAME, DESCRIPTION, SAMPLE_VALUE, METRIC_FORMULA. The AI uses this as a metadata fallback.

4.2  DDL Design Prompt
📋 PROMPT: Design a Snowflake DDL schema for [DOMAIN]. Database: [DB_NAME], Schema: [SCHEMA_NAME]. Role: SYSADMIN. The schema must support these demo questions: [LIST 5-8 QUESTIONS]. Key metrics to compute: [METRIC LIST]. Include: dimension tables for [ENTITIES], fact tables for [TRANSACTIONS/EVENTS], 4-6 analytical views, and a DATA_DICTIONARY table. Use REFERENCES declarations for FK relationships (no enforcement). Add column-level COMMENT strings with descriptions. Design for approximately [ROW COUNT] rows in the main fact table.

4.3  Standard Snowflake DDL Structure
Every DDL script should follow this section order:

-- SECTION 0: ENVIRONMENT SETUP
USE ROLE SYSADMIN;
CREATE DATABASE IF NOT EXISTS MY_DEMO;
CREATE SCHEMA IF NOT EXISTS MY_DEMO.MY_DOMAIN;
USE DATABASE MY_DEMO; USE SCHEMA MY_DOMAIN;

-- SECTION 1: FILE FORMAT (required for COPY INTO)
CREATE OR REPLACE FILE FORMAT CSV_STANDARD
  TYPE = 'CSV' FIELD_DELIMITER = ',' RECORD_DELIMITER = '\n'
  SKIP_HEADER = 1 NULL_IF = ('', 'NULL') EMPTY_FIELD_AS_NULL = TRUE
  FIELD_OPTIONALLY_ENCLOSED_BY = '"' DATE_FORMAT = 'YYYY-MM-DD';

-- SECTION 2: INTERNAL STAGE
CREATE OR REPLACE STAGE LOAD_STAGE FILE_FORMAT = (FORMAT_NAME = 'CSV_STANDARD');

-- SECTION 3: DIMENSION TABLES (reference/lookup)
-- SECTION 4: FACT TABLES (transactional)
-- SECTION 5: ANALYTICAL VIEWS
-- SECTION 6: DATA DICTIONARY TABLE

4.4  Common DDL Pitfalls
	•	Never use positional GROUP BY (GROUP BY 1, 2) in views — Snowflake rejects derived expressions in positional references. Always use explicit column expressions.
	•	Always add COMMENT = 'description' to every table and column. WisdomAI reads these for schema discovery.
	•	DATE columns: use DATE type, not TIMESTAMP, unless you need sub-day precision.
	•	VARCHAR sizing: use VARCHAR(50) for codes/IDs, VARCHAR(200) for descriptions, VARCHAR(500) for free text.
	•	Views with JOINs: alias every table (p for policies, c for claims, etc.) and qualify every column reference.

PHASE 3  Data Generation & Loading

5.1  Data Generation Strategy
Always use Python with write_pandas() — not row-by-row INSERTs (too slow) and not CSV → manual PUT → COPY INTO (too many manual steps). The standard pattern:

import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd, numpy as np
from faker import Faker
import os; from dotenv import load_dotenv

load_dotenv()
SEED = 42  # Always use a fixed seed — makes data reproducible
rng = np.random.default_rng(SEED)
fake = Faker(); Faker.seed(SEED)

conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PAT'),
    role='SYSADMIN',
    warehouse='COMPUTE_WH',
    database='MY_DEMO',
    schema='MY_DOMAIN'
)

# Generate DataFrame, then load:
success, n_chunks, n_rows, _ = write_pandas(conn, df, 'TABLE_NAME',
    auto_create_table=False, overwrite=True)

5.2  Data Generation Prompt
📋 PROMPT: Generate Python data generation scripts for the [DOMAIN] schema in Snowflake. Use write_pandas() for all loads. Fixed seed = [SEED VALUE]. The data must contain these narrative control points: [LIST THE STORY ARCS]. Dimension tables first, then fact tables in FK dependency order. For each script include: (1) connection block from .env, (2) data generation with realistic distributions (not uniform random), (3) narrative injection — the specific rows/values that create the demo story, (4) write_pandas load, (5) row count verification query.

5.3  Load Sequence — Always Follow FK Dependencies
Scripts must execute in this order. Never load a child table before its parent.

Step
Script
Tables
Notes
01
01_dimensions.py
All reference/dimension tables
No FKs — fully independent. Run first.
02
02_entities.py
Agents, producers, accounts
May reference dimension tables
03
03_policies.py
Main policy fact table
References agents, dimensions, geographies
04
04_claims.py
Claims transactions
References policies — run after 03
05
05_renewals.py
Renewal chains / policy history
Self-referencing policy IDs — run after 03
06
06_financials.py
Premium, loss, expense summaries
Aggregates from policies + claims
07
07_dictionary.py
DATA_DICTIONARY table
Always last — references all table/column names

5.4  Narrative Control Points
The most important technique in data generation. A narrative control point is a deliberate anomaly you engineer into the data — a specific combination of values that creates a "discovery moment" when the AI surfaces it. Examples from the Insurance POC:

Control Point
How it's engineered
Demo moment it creates
Southeast commercial auto loss spike
Claims in FL/GA/TX auto with loss_ratio > 1.15 in Q3-Q4, driven by 3 specific CAT events
CUO asks 'where is our loss ratio deteriorating?' → AI pinpoints region, line, and cause
Coastal property renewal attrition
Non-renewal rate = 38% for coastal HO3 vs 12% overall; tied to one broker ID
Head of Broker asks 'which segments are we losing?' → broker attribution surfaces immediately
Reserve inadequacy signal
Open claims with paid_to_incurred ratio > 0.92 AND claim age > 180 days
VP Actuarial asks about reserve adequacy → AI flags under-reserved claims
High-value broker concentration
One broker ID = 18% of NWP but 34% of losses
Head of Broker asks about broker profitability → concentration risk surfaces

5.5  Data Validation Queries
After loading, always run these verification queries before connecting WisdomAI:

-- Row counts per table
SELECT 'POLICIES' AS tbl, COUNT(*) AS n FROM POLICIES
UNION ALL SELECT 'CLAIMS', COUNT(*) FROM CLAIMS
UNION ALL SELECT 'AGENTS', COUNT(*) FROM AGENTS;

-- FK integrity check (no orphaned children)
SELECT COUNT(*) AS orphaned_claims FROM CLAIMS c
LEFT JOIN POLICIES p ON c.policy_id = p.policy_id
WHERE p.policy_id IS NULL;

-- Verify narrative control points loaded correctly
SELECT region, line_of_business, AVG(loss_ratio) AS avg_lr
FROM V_LOSS_RATIO_BY_SEGMENT
GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 10;

PHASE 4  wACE Domain Bootstrap Document

6.1  What is the wACE Bootstrap Document?
The wACE (WisdomAI Contextual Engine) domain bootstrap document is a single .md or .txt file you provide to WisdomAI when setting up the domain. It teaches the AI everything it needs to know about your data that isn't visible from schema inspection alone — the semantics, the tribal knowledge, the business nuances, and the synonyms that make it sound like a domain expert.

Key insight: WisdomAI is excellent at reading column and table names. What it cannot infer on its own: what a metric formula means in this specific industry, which synonym a user will actually use, what the narrative control points are in your data, and what tribal knowledge a 20-year veteran would carry in their head. The bootstrap document provides all of this.

6.2  Bootstrap Document Prompt
📋 PROMPT: Build a wACE domain bootstrap document for the [DOMAIN] WisdomAI domain. The database is [DB_NAME], schema is [SCHEMA_NAME]. Include all of the following sections:

1. DOMAIN OVERVIEW — 3-4 sentences describing what this data represents, the time period, and the organizational context.
2. TABLE CATALOG — for each table: description, every column with data type + description + sample values, FK relationships and cardinality.
3. ANALYTICAL VIEWS — for each view: what metric it computes, the formula in plain English, which questions it answers.
4. ENTITY RELATIONSHIP MAP — describe parent-child relationships in natural language (not a diagram).
5. METRICS DICTIONARY — every KPI: name, formula, unit, what it signals when high vs. low.
6. SYNONYMS MASTER LIST — map every business term a user might say to the exact column and table in the schema.
7. DOMAIN KNOWLEDGE (industrial/industry facts, one sentence per fact, 20-30 facts).
8. BUSINESS NUANCES — dataset-specific rules, filter requirements, data quality notes.
9. TRIBAL KNOWLEDGE — 10-15 entries of the kind of knowledge a 20-year veteran carries but never writes down.
10. QUERY ROUTING HINTS — for any tables with duplicate/overlapping coverage, tell the AI which to prefer and when.

6.3  Required Bootstrap Document Sections

Section
What to include
Insurance POC example
Domain Overview
What does this data represent? Time period? Org context? 3-5 sentences.
P&C insurance carrier operating in commercial and personal lines across 22 states. Data spans 2021-2025 and captures 340,000 policies through their full lifecycle from bind through renewal or non-renewal.
Table Catalog
Every table: description, every column with type + description + sample values.
POLICIES table: one row per policy. POLICY_ID (VARCHAR, PK, e.g. 'POL-2024-000001'), POLICY_TYPE (HO3, BOP, CPP, CA, WC), EFFECTIVE_DATE (DATE), WRITTEN_PREMIUM (NUMBER)...
Metrics Dictionary
Every KPI: name, SQL formula, unit, interpretation.
Loss Ratio = SUM(incurred_losses) / SUM(earned_premium). Expressed as decimal (0.87 = 87%). Values > 1.0 mean the line is unprofitable before expenses.
Synonyms Master List
Map what users say → what the column is called.
'retention rate' = 1 - non_renewal_rate. 'policy count' = COUNT(DISTINCT policy_id). 'premium' = written_premium OR earned_premium depending on context — clarify if ambiguous.
Domain Knowledge
20-30 one-sentence industry facts. Written as declarative statements.
Commercial auto loss ratios above 85% typically indicate rate inadequacy relative to actual claim severity trends. Coastal property insurance carries reinsurance cost that can make segments unprofitable even at < 100 combined ratio.
Business Nuances
Dataset-specific warnings, filter requirements, data quality notes.
Always filter WHERE policy_status != 'CANCELLED' for active book analysis unless specifically looking at cancellations. The RENEWAL_CHAIN_ID links a policy to all of its prior-term versions.
Tribal Knowledge
10-15 things a veteran knows but never writes down.
Broker ID BRK-0047 books primarily coastal commercial property — high NWP but the loss ratio on their book has been above 1.0 for 3 consecutive years. This is the 'problem broker' narrative in the data.

6.4  Pass/Fail Validation of Domain Knowledge Facts
After generating the bootstrap document, run a pass/fail check on every domain knowledge fact, synonym, and business nuance. Use this prompt:

📋 PROMPT: Review the following domain knowledge facts from my wACE bootstrap document. For each fact, verify that: (1) it is accurate against the actual schema and data as built, (2) the column names referenced actually exist, (3) the formula is correct, (4) there are no contradictions with other facts. Mark each as PASS or FAIL and explain any failures. [PASTE KNOWLEDGE FACTS]

⚠️ Common failures: Column names that don't exist (hallucinated during bootstrap generation). Formula references to columns in the wrong table. Synonym mappings that produce wrong query results (e.g. 'retention' mapped to a count instead of a rate). Business nuances that describe behavior not actually present in the synthetic data.

PHASE 5  Testing, Iteration & Demo Questions

7.1  Demo Question Architecture
A well-structured question bank has four types. Every demo should include all four:

Type
Purpose
Example
Count
Single-fact lookup
Establish that the AI can navigate the data and speak the domain language
What is our current combined ratio for commercial auto?
3-5 questions
Analytical / drill-down
Show the AI can compute, compare, and explain — not just retrieve
Which region is driving the loss ratio deterioration and what are the top contributing causes?
5-8 questions
Story arc
3-question chains that build to a revelation and a recommended action
Q1: Where is retention declining? Q2: Who is driving it? Q3: What is the revenue impact of fixing it?
2-3 arcs (6-9 questions)
Web + data hybrid
Show the AI can combine internal data with external context
How does our combined ratio compare to industry benchmarks for our segment?
1-2 questions

7.2  Question Generation Prompt
📋 PROMPT: Generate a demo question bank for the [DOMAIN] WisdomAI domain. The buying audience is [PERSONAS]. Build 15-20 questions covering: (1) 4-5 single-fact lookups that establish domain fluency, (2) 6-8 analytical questions that require computation and cross-table reasoning, (3) 2-3 story arcs — each a 3-question sequence that builds to a recommended action, (4) 1-2 questions that combine data with web search. For each story arc: name the arc, explain the revelation it delivers, and write the 3 questions in sequence. Frame all questions as a natural business user would ask them — not as SQL prompts.

7.3  Live Testing Protocol
Run every question live in WisdomAI before the demo. Log the results using this protocol:

Question
Expected
Actual
Pass/Fail
Action
What is our combined ratio for commercial auto YTD?
~1.08 (Southeast-driven)
Record actual response here
PASS / FAIL
Data fix / prompt fix / domain fix

Use a scoring spreadsheet: Track each question as PASS (correct answer, good narrative), PARTIAL (correct but verbose/slow/missing narrative), or FAIL (wrong, hallucinated, or broken). Target > 90% PASS before demo day. Any FAIL on a story arc question = data or domain fix required.

7.4  Iteration Loop
When questions fail, diagnose before fixing. There are four root causes:

Root Cause
Symptoms
Fix
Data gap
AI returns 'no data found' or NULL for a question you expect to work
Add or correct rows in the fact table. Run the data generator again with narrative control point adjusted.
Schema ambiguity
AI joins wrong tables, picks wrong column, or confuses two similar metrics
Add COMMENT strings to disambiguate columns. Add a query routing hint to the bootstrap doc.
Missing synonym
AI doesn't recognize a term the user used ('attrition rate', 'lapse', 'non-renew')
Add the synonym mapping to the SYNONYMS MASTER LIST in the bootstrap doc and re-upload.
Wrong business nuance
AI computes a metric correctly by formula but wrong for business context (e.g. includes cancelled policies in active book count)
Add a business nuance rule to the bootstrap doc: 'Always filter WHERE status = ACTIVE for count questions.'

7.5  Pre-Demo Checklist
	•	All questions in the question bank scored PASS or acceptable PARTIAL
	•	All narrative control points are visible in the data (run verification queries)
	•	Bootstrap document uploaded to WisdomAI domain and all knowledge facts pass/fail validated
	•	WisdomAI role for demo user has SELECT only on the POC schema (use WISDOMAI_READ_ONLY)
	•	Demo walkthrough document complete with SE talk tracks and expected AI responses
	•	Fallback ready: if AI gives a table instead of narrative, ask 'Can you explain that in plain language?' to re-rail

8 · Snowflake Infrastructure Reference
8.1  Standard Object Hierarchy
ACCOUNT: XMSPMYE-PAB51256 (WisdomAI SE shared account)
  └─ DATABASE: {PROSPECT}_POC  (e.g. INSURANCE_POC, CENTENE_DEMO)
       └─ SCHEMA: {DOMAIN}     (e.g. INSURANCE_POC, FINANCE_ANALYTICS)
            ├─ TABLES (dimensions + facts)
            ├─ VIEWS (V_ prefix, analytical pre-computations)
            ├─ STAGE: LOAD_STAGE
            └─ FILE FORMAT: CSV_STANDARD

8.2  Access Control
Two roles are used for every POC:

Role
Used for
Grant command
SYSADMIN
DDL creation, data loading, schema management
Default — already available
WISDOMAI_READ_ONLY
WisdomAI MCP connector, demo user access
GRANT USAGE ON DATABASE X TO ROLE WISDOMAI_READ_ONLY;
GRANT USAGE ON SCHEMA X.Y TO ROLE WISDOMAI_READ_ONLY;
GRANT SELECT ON ALL TABLES IN SCHEMA X.Y TO ROLE WISDOMAI_READ_ONLY;

8.3  Connecting WisdomAI MCP to Snowflake
After the schema and data are loaded, point the WisdomAI MCP connector at the POC schema:

	•	In WisdomAI, navigate to Settings → Data Sources → Add Snowflake
	•	Account: XMSPMYE-PAB51256, Role: WISDOMAI_READ_ONLY, Warehouse: COMPUTE_WH
	•	Select database: {PROSPECT}_POC, schema: {DOMAIN}
	•	WisdomAI will auto-discover tables and views via INFORMATION_SCHEMA
	•	Upload the bootstrap .md document as the Domain Knowledge file
	•	Run the first 5 questions from your question bank as a smoke test before the demo

8.4  Performance Tips
	•	Use XSMALL warehouse for all POC loads — data volumes are small enough that bigger doesn't help
	•	Cluster keys: not needed for POC volumes (< 10M rows). Add only if query times exceed 3 seconds during testing.
	•	Views with heavy aggregation: materialize as tables if they slow down during demo (CTAS pattern).
	•	Auto-suspend the warehouse at 1 minute idle — POC databases are not queried continuously.

9 · Quality Checklist
Use this checklist to gate each phase before moving to the next.

✓
Gate
Acceptance criteria
☐
Phase 1 — Research
Domain knowledge captured
KPI list ≥ 6 metrics. Narrative control points ≥ 3 story arcs. Entity names are realistic and industry-accurate. Buying persona pain mapped to demo questions.
☐
Phase 2 — Schema
DDL runs clean
DDL executes without errors in SYSADMIN. All views compile. No orphaned column references. FILE FORMAT and STAGE objects created. DATA_DICTIONARY table present.
☐
Phase 3 — Data
Data loaded and verified
Row counts match spec. FK integrity queries return 0 orphans. Narrative control points visible in verification queries. Metric views return expected values (ballpark check).
☐
Phase 4 — Bootstrap
Bootstrap doc complete and validated
All 10 sections present. All domain knowledge facts pass/fail reviewed — no FAILs remaining. All column references verified against actual DDL. Synonyms cover at least 15 common business terms.
☐
Phase 5 — Testing
Question bank passes
> 90% of demo questions score PASS in live WisdomAI testing. All story arc questions pass. No FAIL on any question in the first 5 (the live demo opening). Pre-demo checklist complete.

10 · Appendix: Prompt Templates
Copy-paste ready versions of every prompt referenced in this guide.

Prompt A — Domain Research
I am building a WisdomAI POC demo for [COMPANY NAME], a [INDUSTRY].
The buying audience is [PERSONAS — e.g. CUO, Head of Claims, VP Actuarial].
Their primary pain points are [PAIN POINTS].

Research this company and industry thoroughly, then provide:
1. Key data sources and systems they use in production
2. The 5-8 most important KPIs the buying audience tracks
3. Realistic entity names for synthetic data (products, regions, org units)
4. Industry terminology and business nuances to embed in the domain
5. 3-5 narrative control points — specific anomalies to engineer into
   the dataset that create demo discovery moments

Prompt B — Schema Design
Design a Snowflake DDL schema for [DOMAIN NAME].
Database: [DB_NAME], Schema: [SCHEMA_NAME], Role: SYSADMIN.

The schema must answer these demo questions:
- [QUESTION 1]
- [QUESTION 2] (add 5-8 total)

Key metrics to compute: [METRIC LIST]

Include:
- [N] dimension/reference tables for [ENTITIES]
- [N] fact tables for [TRANSACTIONS/EVENTS]
- 4-6 analytical views (V_ prefix)
- DATA_DICTIONARY table
- FILE FORMAT CSV_STANDARD and STAGE LOAD_STAGE

Use REFERENCES declarations for FK relationships (no enforcement).
Add COMMENT strings to every table and column.
Target ~[ROW COUNT] rows in the main fact table.

Prompt C — Data Generation
Generate Python data generation scripts for the [DOMAIN] schema.
Use write_pandas() for all Snowflake loads.
Fixed seed = [SEED — e.g. 20240101].

Narrative control points to engineer into the data:
- [CONTROL POINT 1: e.g. FL commercial auto loss ratio > 1.15 in Q3-Q4]
- [CONTROL POINT 2]
- [CONTROL POINT 3]

Generate scripts in FK dependency order:
01_dimensions.py → 02_entities.py → 03_[main fact].py → ...

Each script must include:
1. .env-based connection block
2. Realistic distributions (not uniform random)
3. Explicit narrative injection (show the code that creates the anomaly)
4. write_pandas() load with overwrite=True
5. Row count verification query

Prompt D — wACE Bootstrap Document
Build a wACE domain bootstrap document for the [DOMAIN] WisdomAI domain.
Database: [DB_NAME], Schema: [SCHEMA_NAME].

Include all 10 sections:
1. DOMAIN OVERVIEW (3-5 sentences)
2. TABLE CATALOG (every table, every column, sample values)
3. ANALYTICAL VIEWS (metric, formula, questions answered)
4. ENTITY RELATIONSHIP MAP (natural language, not diagram)
5. METRICS DICTIONARY (name, formula, unit, interpretation)
6. SYNONYMS MASTER LIST (business term → column/table mapping)
7. DOMAIN KNOWLEDGE (20-30 one-sentence industry facts)
8. BUSINESS NUANCES (filter rules, data quality, edge cases)
9. TRIBAL KNOWLEDGE (10-15 veteran-knowledge entries)
10. QUERY ROUTING HINTS (which table to prefer when ambiguous)

Prompt E — Demo Question Bank
Generate a demo question bank for the [DOMAIN] WisdomAI domain.
Buying audience: [PERSONAS]

Build 15-20 questions across four types:
1. Single-fact lookups (4-5) — establish domain fluency
2. Analytical / drill-down (6-8) — cross-table reasoning
3. Story arcs (2-3 arcs, 3 questions each) — build to a revelation
4. Web + data hybrid (1-2) — combine internal data with external search

For each story arc:
- Name the arc
- State the revelation it delivers (the 'so what')
- Write 3 questions in sequence, each building on the prior answer

Frame all questions as a natural business user would ask them.
Do NOT write them as SQL prompts.

Prompt F — Pass/Fail Validation
Review these domain knowledge facts from my wACE bootstrap document.
The actual schema is [DB_NAME].[SCHEMA_NAME].

For each fact, verify:
1. Column names referenced actually exist in the schema
2. Formula or computation is correct
3. No contradictions with other facts
4. Narrative control points described actually exist in the data

Mark each: PASS | FAIL (with reason) | WARN (minor issue)

[PASTE DOMAIN KNOWLEDGE FACTS HERE]



WisdomAI Sales Engineering  ·  POC Domain Build Guide v1.0  ·  Confidential
