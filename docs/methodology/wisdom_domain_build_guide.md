<!-- Converted from 'Domain Build Guide (March 2026).docx.pdf' — WisdomAI's product-side 7-phase domain build process. Text extracted and re-flowed; tables flattened. -->



---
<!-- page 1 --> Domain Build Guide A step-by-step framework for building accurate, production-ready domains Overview This guide provides a structured, end-to-end process for building a high-quality Wisdom domain. Follow this guide in sequence. Each phase builds on the previous one - skipping steps will compromise domain accuracy.

PHASE
1 Environment Setup Provision the Wisdom instance and establish connectivity

1.1 Instance Provisioning (1-time only) Before any domain work can begin, a Wisdom environment must be provisioned for the prospect/customer.
1 Provision the Wisdom Instance Determine the deployment model - SaaS or VPC (customer-hosted). Provision the instance based on data residency requirements and security posture.
2 Enable SSO via Descope (optional) Configure Single Sign-On using Descope to ensure secure, managed access to the Wisdom environment. Validate access.
3 Establish Communication Channel Set up a shared Slack channel (or Teams/WhatsApp as appropriate) on Day 0. Ensure the prospect knows they have a direct line to the team - not just scheduled calls. Set SLA expectations: same-day for non-urgent, within 2 hours for blockers.

PHASE
2 Pre-Build Preparation Gather all inputs required before context loading begins

2.1 Pre-Build Checklist The quality of a domain is directly determined by the quality of inputs loaded during setup. The following items should be gathered before or during the first working session.

---
<!-- page 2 --> # Deliverable Description Status
1 Data Sources Identify and connect all data sources that will power this domain. Stick to a minimal set of data to start with and then expand later if needed. REQUIRED
2 Top 50-100 NL Questions + SQL Pairs Natural language questions paired with validated SQL queries. These become the foundation of the evaluation set and reviewed query baseline. The goal is coverage, not volume - see Section 5. To simplify collection, pull from existing dashboards, saved queries, and query logs, and supplement with brief business user interviews to capture common and edge-case questions. REQUIRED
3 Business User Questions - Admin Pre-Validation Have the admin collect ~5 questions each from 5-10 business users (in addition to the initial 50-100 questions). These should be tested by the admin in the playground after the domain is fully built, to catch issues early and eliminate surprises before handing it over for Business Users. REQUIRED 3 NL Context & Metric Definitions Business metric definitions, KPI logic, domain terminology, and any business rules that affect how questions should be interpreted. REQUIRED
4 Metadata & Schema Documentation Table/column descriptions, data dictionaries, schema documentation, or any existing data catalog content. Recommended
5 Existing BI Reports & Dashboards Pre-built reports, dashboards, LookML, Tableau workbooks (.tbx), or other BI assets that represent key business views. Recommended
6 Query Logs Historical SQL query logs from existing BI tools, data warehouses, or analytics platforms. Recommended 7 YAML / JSON Configuration Files Any structured metadata files that describe the data model or business logic. Recommended
8 Any Additional Source (Not supported today) If the customer has documentation in a format Wisdom does not currently support, flag this immediately to the Product & Engineering team. Note the format type and share it via the internal channel. FLAG TO PRODUCT & ENGG 💡 If the customer cannot provide SQL pairs before Day 1, set clear expectations that the first working session will be used to build them collaboratively. This is workable but consumes session time - communicate the trade-off early.

PHASE
3 Data Connection Connect to data sources and identify the tables/files/MCPs for the domain

---
<!-- page 3 -->

3.1 Connecting Data Sources
1 Connect via Wisdom Connectors Use the Connections interface to connect all domain data sources. Verify each connector authenticates successfully and data is accessible. Include MCP or Web sources in addition to structured and unstructured sources as needed. For new connections, trigger a sync (or use “Sync Now” if required); tables will be available only after sync completes.
2 Initiate Domain Build Start a new domain build by selecting the data connections you need. You will be associating specific tables and files from these connections in the next step.
3 Select Tables and Files Identify the specific tables, views, or files from each connection that are relevant to this domain. Add them to the domain. Be deliberate - only include tables that serve the business questions this domain will answer.

PHASE
4 Context Loading Load all semantic context, metadata, and domain knowledge

4.1 Cardinality & Table Relationships Once tables are added to the domain, define the relationships between them. Correct join paths are critical for multi-table query accuracy.
1 Define Table Cardinality For each pair of related tables, specify the join condition and cardinality (one-to-one, one-to-many, many-to-many). If cardinality is not immediately known, Wisdom can surface suggestions via the Suggestions tab, or it may become apparent through Reviewed Query analysis.

4.2 Extraction Feature The Extraction feature accelerates context loading by automatically pulling semantic information from existing assets. Use it aggressively - every piece of documentation loaded reduces manual context entry. Upload and extract context from: • Existing BI reports and dashboards • Query logs from current data tools • Data dictionaries and metadata documentation • LookML, Tableau workbook files (.tbx), etc. • YAML or JSON configuration files • Any other domain documentation provided by the customer

---
<!-- page 4 --> Extraction Options Choose the extraction acceptance mode based on data complexity and the time available for review: Option Behavior Best Used When Auto-Accept Highly Confident Automatically accepts suggestions with high confidence scores Data is well-documented, and schema is clean Auto-Accept All Automatically accepts all extracted suggestions Not Recommended: Time is limited; review can happen post-load Manual Review Only All suggestions queue for human approval before being added Data is sensitive or domain is complex; accuracy is critical
2 Review and Approve Extracted Context After extraction runs, review the proposed additions. Approve context that is accurate and aligned with the domain's business logic. Reject or modify anything that is incorrect or misleading. Approved items are added to the Context Engine and appear under table and column descriptions.

4.3 Manual Context Enrichment After extraction, supplement with manually entered context to fill gaps and improve accuracy for business-specific concepts.
3 Add Natural Language Context Enter domain-specific terminology, business rules, and interpretive guidance in the NL Context tab. This is especially important for ambiguous terms - for example, how 'revenue' is defined, what 'active customer' means, or which date field should be used as the primary time dimension.
4 Add Table & Column Descriptions Write clear, business-oriented descriptions for key tables and columns. Focus on the columns most likely to appear in user queries and any that have non-obvious names or business-specific meaning.
5 Enable Lookup for key noun columns Enable lookup (NER) for key noun columns (e.g., Name, Customer, Supplier, Department) so users can enter natural, approximate values instead of exact database matches. Example: If the database has “John A. Smith” under Customer, a user can simply type “john”, and NER will correctly identify and match it to the right record.
6 Define Metrics and Derived Columns Create calculated metrics and derived columns that represent key business metrics and transformations used in queries.
7 Hide Unnecessary Columns (when necessary) Remove columns that are not relevant to business queries to reduce noise and improve query accuracy.

---
<!-- page 5 -->
8 Add Row Level Security (when necessary) Configure row-level security rules to ensure users only access data they are authorized to see.

PHASE
5 Reviewed Queries & Evaluation Setup Establish the baseline query set and configure evaluation

5.1 Building the Reviewed Query Set Reviewed Queries are the highest-value component of domain context. They provide explicit, validated examples of how natural language questions map to correct SQL - and they directly inform Wisdom's query generation for similar questions. Selecting the Right 50-100 Questions Identify the top 50-100 questions that are asked in this domain. The goal is coverage, not volume - these questions must collectively exercise the major tables, columns, and join conditions in the dataset. When selecting questions, ensure they: • Cover all major tables in the domain - every frequently queried table should appear in at least several questions • Exercise the most-used columns, especially those involved in filtering, grouping, and aggregation • Include multi-table questions that require joins - these reveal whether cardinality and join conditions are correctly defined • Represent the real business questions users ask • Include questions with different complexity levels: simple lookups, aggregations, time-series, and comparisons SQL Pairing Paths Ideally, the customer provides the SQL that goes with each question. When that is not available, there are two alternative approaches. Choose the path that fits the situation: Path When to Use Steps Path A – Customer Provides SQL (Preferred) Customer has verified, production-quality SQL for their top questions Load NL + SQL pairs directly as Reviewed Queries → Configure Eval Set → Run evaluation immediately from Day
1 Path B – Bulk Evaluation Run Customer has questions but no SQL; large question set; time-efficient approach preferred Load all 50–100 questions into an eval run → Wisdom generates SQL → Download in bulk → Customer reviews and approves → Load approved pairs as Reviewed Queries Path C – Playground Review Customer has questions but no SQL; smaller set or interactive session preferred; real-time iteration needed Run each question through the Playground → Review AI-generated SQL and answer → Provide feedback via product → Add validated pairs as Reviewed Queries directly

---
<!-- page 6 --> Path A - Customer Provides SQL (Preferred) This is the ideal scenario and should always be attempted first. The customer submits their top 50–100 natural language questions paired with verified, production-quality SQL queries. • Load the NL + SQL pairs directly as Reviewed Queries in Wisdom • These pairs give Wisdom an authoritative understanding of the domain from Day 1 • Configure the evaluation set immediately using these same questions • Evaluation runs can begin on Day 1 - no waiting period to build SQL coverage Path B - Bulk Evaluation Run Use this path when the customer has a list of questions but cannot provide SQL pairs. It is the most efficient approach for larger question sets and minimizes workshop time spent on SQL generation. • Load all 50–100 questions into an evaluation run without SQL pairs • Wisdom generates candidate SQL for each question automatically • Download the full generated SQL set as a bulk export • Provide the export to the customer for review and approval outside the session • Once the customer validates and returns approved SQL, load the pairs as Reviewed Queries • Re-run the evaluation with the approved pairs to confirm accuracy 💡 Path B requires a turnaround window for the customer to review SQL outside the session. Build this into the schedule - do not assume same-day approval. For a 50–100 question set, allow at least one business day for review. Path C - Playground Review Use this path when the customer has questions but no SQL, and an interactive, real-time approach is preferred - or when the question set is smaller and can be worked through in a single session. • Run each of the 50–100 questions through the Playground one by one • For each question, review the generated SQL and the answer returned in the session • Provide feedback via hint and Mark Reviewed • Questions with validated SQL can be added directly as Reviewed Queries from the Playground • This method allows real-time context iteration - if a question fails, update context and re-test immediately ✅ Path C works well for the first 50 questions in a working session, where interactive review builds domain understanding quickly. For larger sets, switch to Path B to avoid running over session time. 💡 Aim for at least 50 validated NL + SQL pairs before running the first evaluation. The broader the coverage across tables and columns, the more accurately the evaluation will reflect real-world domain capability.

5.2 Evaluation Configuration The Evaluation feature measures how accurately Wisdom generates SQL for a defined question set. Configure and run evaluations regularly throughout the domain build process.

---
<!-- page 7 -->
1 Configure the Evaluation Set Add the top 50–100 NL questions to the evaluation set. These should be the questions most representative of real user behavior in this domain - covering the primary tables, metrics, and business questions the domain will serve.
2 Run the Initial Evaluation Run the first evaluation to establish a baseline domain health score. Review results carefully - failures will identify gaps in context, missing join conditions, or ambiguous column definitions.
3 Iterate on Context Based on Failures For each failing question, diagnose the root cause: incorrect join path, missing NL context, ambiguous column name, or missing metric definition. Update the relevant context and re-run the evaluation. Repeat until the score reaches 100%.

PHASE
6 Testing & Refinement Validate domain accuracy and expand coverage

6.1 Playground Testing The Playground provides a direct interface to test questions against the domain and observe Wisdom's SQL generation and answers in real time. Have the admin gather ~5 questions each from 5-10 business users.
1 Test Top Questions via Playground Run the Business user questions gathered plus any questions from the top 50-100 list, through the Playground. For each question, review the generated SQL, the answer returned, and the reasoning. Where the answer is not accurate, use the Hint mechanism to get the correct answer, and update the domain context (NL context, column descriptions, reviewed queries) and re-test.

6.2 Suggestions Tab Review The Suggestions tab surfaces recommendations for join relationships that will improve domain accuracy. Review suggestions regularly throughout the build process.
2 Review and Act on Suggestions Examine each suggestion carefully. Verify its accuracy before approving. Not all suggestions will be correct - treat them as candidates for review, not automatic additions. Ignore suggestions that are not relevant or that contradict validated domain context. ⚠ Do not bulk-approve suggestions. Each one should be individually verified against the actual data and business logic. Incorrect suggestions that are approved will degrade query accuracy.

6.3 Domain Health Tab

---
<!-- page 8 --> The Domain Health tab provides a view of domain completeness and quality signals. Use it throughout the build process to monitor progress and identify gaps.
3 Monitor Domain Health Continuously Check the Domain Health tab after each major context addition or evaluation run. Use it to identify areas of the domain that have low coverage, missing context, or declining accuracy. Note that the Domain Health tab is currently in Beta - use it as a directional signal, not an absolute measure.

PHASE
7 Stakeholder Validation & Domain Release Canvas demos, business user testing, final refinement, and production readiness

7.1 Build Canvas Dashboards and Agents Before handing the domain to business users, build initial Canvas dashboards and agent workflows to demonstrate what the domain can do. This gives business users concrete examples to validate the domain's end-to-end capability beyond chat.
1 Build Initial Canvas Dashboards and Agents Build one or two representative dashboards and agent workflows in Canvas that reflect real business questions in this domain. These should show the customer how Wisdom can power programmatic, repeatable analysis - not just ad hoc questions. Having these ready before business user sessions makes the demo more compelling and gives users a frame of reference for what good looks like.

7.2 Business User Testing Before releasing the domain to end users, validate accuracy with business-side stakeholders who understand the domain and can evaluate answers in context.
1 Engage Domain-Knowledgeable Business Users Identify 2–3 analytically-oriented business users who are deeply familiar with this domain. Brief them on what data is available in the domain and encourage them to ask questions freely - not just from a predefined list.
2 Collect Structured Feedback via Product Have business users use Thumbs Up / Thumbs Down feedback for every question they ask. Any question that returns an unexpected or incorrect answer should be flagged for context refinement.
3 Refine Based on Business User Feedback Analyze the feedback collected. Update NL context, column descriptions, metric definitions, or reviewed queries as needed.
4 Add an Evalset from Business User Questions

---
<!-- page 9 --> Run evaluations after each significant context update

7.3 Final Evaluation & Release Criteria A domain is ready for release when it meets the following criteria: • Validated NL + SQL Reviewed Query pairs loaded in the domain • Evaluation set of RQ and business user questions configured • Evaluation score reaches 100% match between ground truth SQL and Wisdom-generated SQL • Initial Canvas dashboards and agents built and reviewed • Business users have tested the domain, and feedback has been reviewed and addressed • Domain Health tab reflects adequate coverage and no critical gaps • Daily evaluation runs configured to detect accuracy drift post-release
5 Configure Daily Evaluation Runs Set up automated evaluation runs on a daily cadence. Daily evaluations are the primary mechanism for detecting context drift. When the daily eval score drops below 100%, investigate immediately and update context to restore accuracy.

7.4 Ongoing Maintenance A domain is a living artifact. As data evolves, business logic changes, and new questions emerge, the domain requires ongoing maintenance to remain accurate. • Review the Suggestions tab weekly for new learning opportunities • Monitor daily evaluation scores and address any drops immediately • Add new Reviewed Queries for question types that emerge in production usage • Update metric definitions, NL context, synonyms, and entities when business logic changes • Expand the evaluation set as the domain grows to cover new question categories Quick Reference - Domain Build Checklist Use this checklist to track progress through a domain build. Phase Action Status Ph
1 Instance provisioned (SaaS or VPC) ☐ Ph 1 SSO configured via Descope ☐ Ph
1 Communication channel established with prospect ☐ Ph
2 Top 50–100 NL questions identified ☐ Ph 2 NL context & metric definitions gathered ☐ Ph 2 BI assets, query logs, metadata uploaded ☐ Ph
3 All data source connectors authenticated and verified ☐

---
<!-- page 10 --> Phase Action Status Ph
3 Domain created with relevant tables/files added ☐ Ph
4 Table cardinality / join conditions defined ☐ Ph
4 Extraction run on all available assets ☐ Ph
4 Unsupported documentation formats flagged to Product & Engg ☐ Ph
4 Extracted context reviewed and approved/rejected ☐ Ph 4 NL context, table & column descriptions entered ☐ Ph
4 Enable Lookup for key Noun Columns ☐ Ph
4 Hide necessary Columns ☐ Ph
4 Create Metrics and Derived Columns ☐ Ph
4 Add Row Level Security ☐ Ph
5 Reviewed Query set loaded (min 50 NL+SQL pairs) ☐ Ph
5 Evaluation set configured with top 50–100 questions ☐ Ph
5 Initial evaluation run and gaps identified ☐ Ph
5 Evaluation score iterated to 100% ☐ Ph
6 Have the admin gather ~5 questions each from 5-10 business users ☐ Ph
6 Business User Questions Pre-Validation by Admin on Playground ☐ Ph
6 Feedback captured ☐ Ph
6 Suggestions tab reviewed and relevant items approved ☐ Ph
6 Domain Health tab reviewed ☐ Ph
7 Initial Canvas dashboards/agents built ☐ Ph
7 Business user validation sessions completed ☐ Ph
7 Feedback reviewed and context refined ☐ Ph
7 Final evaluation score at 100% ☐ Ph
7 Daily evaluation runs configured ☐