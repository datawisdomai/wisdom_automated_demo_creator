# Revision notes (2026-10-15)

1. No precomputed RECONCILIATION_RESULTS. Wisdom identifies mismatches live from the three raw systems.
   RECONCILIATION_CONTROLS stays as the rulebook (one row per check).
2. Join helper views only (V_CONTRACT_CHAIN, V_AMENDMENT_LINEAGE, V_DEAL_CROSSWALK); no status column.
   Comparison logic lives in reviewed queries + context. Reviewed queries per check type (11) + roll-ups.
3. Live App "Contract Reconciliation Review": Findings Queue -> Case Review (decisions persist in session)
   -> Export (JSON blob, copyable, no write).
4. Agent "Amendment Sync Watch": same checks on contracts signed/amended in the last 7 days.
5. Scope: structured path first; contract PDFs in S3 are a stretch (Halvorsen chain + ~20 others);
   evals and Domain Health only if everything else is done.
6. All structured data in Snowflake (BigQuery split dropped).
