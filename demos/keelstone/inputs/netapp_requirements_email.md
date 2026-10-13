# Prospect requirements email (received 2026-10-12, forwarded by Paul)

Current BI tool and cloud data warehouse: Microsoft Power BI within Microsoft Fabric for analytics
and visualization; Snowflake as cloud data warehouse and AI data platform. Both stay; native
integration with each matters.

Why they are looking: storage, compute and visualization layers are fine. Gaps are governance,
catalog, and how business users get trusted answers.

Main pain points:
- Lineage and metadata: fragmented; no dependable column-level view across source systems,
  Snowflake, Fabric, Power BI reports and AI outputs. Impact analysis and root cause are manual.
- Business glossary: no living glossary tied to physical data assets; metrics defined
  inconsistently across teams.
- Ontology / semantic context: no layer capturing relationships between business entities, which
  limits accuracy of natural-language and AI use cases built on Snowflake.
- Governance, quality, observability: policies, ownership and quality rules fragmented or manual;
  issues found by report consumers rather than detected proactively.
- Source onboarding: adding new sources takes significant manual cataloging, classification,
  documentation effort.
- Self-service: business users depend on IT and analysts; Power BI usage limited to pre-built reports.

Goals: governed self-service including natural-language and AI-assisted analytics on trusted,
certified definitions and the data already in Snowflake; metadata, lineage and semantic context AI
workloads can rely on; faster decisions, less duplicated effort, more trust in data.

End users: business users (executives, finance, sales ops); business analysts (power users who
find certified data, trace lineage, build analyses); data stewards and governance owners (glossary,
quality rules, policies); IT, data and AI teams (source onboarding, lineage, observability,
integration).

Demo scheduling: October.
