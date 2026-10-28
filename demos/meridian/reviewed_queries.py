"""Reviewed NL -> SQL pairs for the Meridian Clinician Network demo.

`demo rq-check meridian --snowflake` executes every pair against DuckDB and
Snowflake and writes build/reviewed-queries.csv in Wisdom's import format.
NL text must not contain commas; SQL uses upper-case identifiers with
double-quoted object names.

The eleven three-way checks and the roll-ups come verbatim from recon_sql.py —
the same text checks.py validates the data with. Wisdom runs these; nothing is
precomputed.
"""
from demo_creator.reviewed_queries import Registry

import recon_sql as R

rq = Registry()
add = rq.add


def add_eval_only(nl, sql):
    """Validated and in the eval set, but left out of the certified query library (keeps the
    extractor's file small; the question is answerable from the certified checks)."""
    rq.add(nl, sql, tags=("eval_only",))

HERO = "Halvorsen Therapeutics"

# ---------------------------------------------------------------- lookups / basics
add("What reconciliation checks do we run and which team owns each one?",
    'SELECT CONTROL_ID, CHECK_TYPE, CHECK_NAME, FIELD_NAME, SYSTEMS_COMPARED, TOLERANCE, DEFAULT_SEVERITY, HIGH_SEVERITY_USD, OWNING_TEAM, SOX_CONTROL_REF, CORRECTIVE_SYSTEM, DESCRIPTION FROM "RECONCILIATION_CONTROLS" ORDER BY CONTROL_ID')
add("Which SOX control does each reconciliation check map to?",
    'SELECT SOX_CONTROL_REF, CHECK_TYPE, CHECK_NAME, OWNING_TEAM, DESCRIPTION FROM "RECONCILIATION_CONTROLS" ORDER BY SOX_CONTROL_REF, CONTROL_ID')
add("How many customers do we have by customer type and segment?",
    'SELECT CUSTOMER_TYPE, SEGMENT, COUNT(*) AS CUSTOMERS FROM "CUSTOMERS" GROUP BY CUSTOMER_TYPE, SEGMENT ORDER BY CUSTOMER_TYPE, CUSTOMERS DESC')
add("What products do we sell and how is revenue recognised for each?",
    'SELECT PRODUCT_ID, PRODUCT_NAME, PRODUCT_FAMILY, UNIT_OF_MEASURE, LIST_PRICE, REVENUE_RECOGNITION FROM "PRODUCTS" ORDER BY PRODUCT_ID')
add(f"Show me the current terms of the {HERO} agreement.",
    f'SELECT CONTRACT_NUMBER, CUSTOMER_NAME, ACCOUNT_OWNER, ORIGINAL_SIGNED_DATE, AMENDMENT_COUNT, LATEST_CONTRACT_NUMBER, LATEST_SIGNED_DATE, CURRENT_TCV, EFFECTIVE_DATE, CURRENT_END_DATE, CURRENT_PAYMENT_TERMS, CURRENT_BILLING_FREQUENCY, CURRENT_PRODUCT_COUNT, CURRENT_MILESTONE_COUNT, CURRENT_PRODUCT_SUMMARY, LATEST_PDF_FILE_NAME FROM "V_CONTRACT_CHAIN" WHERE CUSTOMER_NAME = \'{HERO}\'')
add("Show me the agreement MCN-2025-0142 and every document in its chain.",
    'SELECT VERSION, DOCUMENT_NUMBER, DOCUMENT_TYPE, SIGNED_DATE, EFFECTIVE_DATE, END_DATE, TCV, TCV_CHANGE, END_DATE_CHANGE_DAYS, PAYMENT_TERMS, BILLING_FREQUENCY, PRODUCT_SUMMARY, SPECIAL_TERMS, DOCUSIGN_ENVELOPE_ID, PDF_FILE_NAME FROM "V_AMENDMENT_LINEAGE" WHERE CHAIN_CONTRACT_NUMBER = \'MCN-2025-0142\' ORDER BY VERSION')
add("How many agreements and amendments were signed by year?",
    'SELECT EXTRACT(YEAR FROM SIGNED_DATE) AS SIGNING_YEAR, CONTRACT_TYPE, COUNT(*) AS DOCUMENTS, SUM(TOTAL_CONTRACT_VALUE) AS RESTATED_TCV FROM "CONTRACTS" GROUP BY EXTRACT(YEAR FROM SIGNED_DATE), CONTRACT_TYPE ORDER BY SIGNING_YEAR, CONTRACT_TYPE')
add("What is the definition and business owner of each field in the data dictionary?",
    'SELECT TABLE_NAME, COLUMN_NAME, DESCRIPTION, METRIC_FORMULA, BUSINESS_OWNER, SOURCE_SYSTEM FROM "DATA_DICTIONARY" ORDER BY TABLE_NAME, COLUMN_NAME')

# ---------------------------------------------------------------- the three systems side by side
add("Show the contract value and the Salesforce and NetSuite values side by side for every agreement.",
    'SELECT CONTRACT_NUMBER, CUSTOMER_NAME, CUSTOMER_TYPE, ACCOUNT_OWNER, AMENDMENT_COUNT, CURRENT_TCV, SF_AMOUNT, NS_AMOUNT, CURRENT_END_DATE, SF_END_DATE, NS_END_DATE, CURRENT_PAYMENT_TERMS, NS_PAYMENT_TERMS, CURRENT_BILLING_FREQUENCY, NS_BILLING_SCHEDULE_TYPE, SF_OPPORTUNITY_COUNT, NS_SALES_ORDER_COUNT FROM "V_CHAIN_SYSTEM_SUMMARY" ORDER BY CURRENT_TCV DESC')
add("What is the total contract value of the book and how much of it is booked in Salesforce and ordered in NetSuite?",
    'SELECT COUNT(*) AS AGREEMENTS, SUM(CURRENT_TCV) AS CONTRACT_TCV, SUM(SF_AMOUNT) AS SALESFORCE_BOOKED, SUM(NS_AMOUNT) AS NETSUITE_ORDERED, SUM(SF_AMOUNT) - SUM(CURRENT_TCV) AS SALESFORCE_NET_VARIANCE, SUM(NS_AMOUNT) - SUM(CURRENT_TCV) AS NETSUITE_NET_VARIANCE FROM "V_CHAIN_SYSTEM_SUMMARY"')
add("How many agreements are active today and how many have been amended?",
    'SELECT COUNT(*) AS AGREEMENTS, SUM(CASE WHEN IS_ACTIVE_TODAY THEN 1 ELSE 0 END) AS ACTIVE_TODAY, SUM(CASE WHEN AMENDMENT_COUNT > 0 THEN 1 ELSE 0 END) AS AMENDED, SUM(AMENDMENT_COUNT) AS AMENDMENTS FROM "V_CONTRACT_CHAIN"')

# ---------------------------------------------------------------- the eleven checks (certified, one per check type)
add("Which agreements have a Salesforce amount that differs from the contract value?", R.TCV_MISMATCH + " ORDER BY ABS(VARIANCE_USD) DESC")
add("Which agreements have a different number of products in Salesforce than in the contract?", R.PRODUCT_LINE_COUNT_MISMATCH + " ORDER BY CUSTOMER_NAME")
add("Which closed won opportunities have no valid contract number?", R.OPPORTUNITY_WITHOUT_CONTRACT_LINK + " ORDER BY VARIANCE_USD DESC")
add("Which amendments are signed in DocuSign but not booked in Salesforce?", R.AMENDMENT_NOT_IN_SALESFORCE + " ORDER BY CURRENT_TCV DESC")
add("Which agreements have a NetSuite end date that differs from the contract end date?", R.TERM_END_DATE_MISMATCH + " ORDER BY CURRENT_TCV DESC")
add("Which amendments are not reflected in NetSuite?", R.AMENDMENT_NOT_IN_NETSUITE + " ORDER BY VARIANCE_USD DESC")
add("Which agreements have more than one NetSuite sales order?", R.DUPLICATE_SALES_ORDERS + " ORDER BY VARIANCE_USD DESC")
add("Which NetSuite sales orders have no Salesforce opportunity id?", R.SALES_ORDER_WITHOUT_OPPORTUNITY + " ORDER BY CUSTOMER_NAME")
add("Which agreements have payment terms in NetSuite that differ from the contract?", R.PAYMENT_TERMS_MISMATCH + " ORDER BY CUSTOMER_NAME")
add("Which agreements have a NetSuite billing schedule type that differs from the contract billing frequency?", R.BILLING_FREQUENCY_MISMATCH + " ORDER BY CUSTOMER_NAME")
add("Which billing milestones in the contract are missing from the NetSuite billing schedule?", R.MISSING_BILLING_MILESTONE + " ORDER BY VARIANCE_USD DESC")

# ---------------------------------------------------------------- the full match and roll-ups
add("Run the full three-way reconciliation and list every finding ranked by exposure.", R.ALL_FINDINGS_RANKED)
add("Which closed won deals do not reconcile across all three systems?", R.CHAINS_NOT_RECONCILING)
add("How many agreements fail the three-way match and what is the total dollar exposure?", R.SUMMARY_TOTALS)
add("What is the dollar exposure of unreconciled items this quarter?",
    R.SLIM_FINDINGS_CTE + "SELECT COUNT(*) AS OPEN_FINDINGS, COUNT(DISTINCT F.CHAIN_ID) AS AGREEMENTS_WITH_FINDINGS, SUM(ABS(F.VARIANCE_USD)) AS EXPOSURE_USD, SUM(CASE WHEN F.SEVERITY = 'High' THEN ABS(F.VARIANCE_USD) ELSE 0 END) AS HIGH_SEVERITY_EXPOSURE_USD, SUM(CASE WHEN F.LATEST_SIGNED_DATE >= DATE '2026-07-01' THEN ABS(F.VARIANCE_USD) ELSE 0 END) AS EXPOSURE_ON_Q3_SIGNINGS_USD FROM F")
add("Which discrepancies belong to the Revenue team versus Billing versus Sales Ops?", R.BY_TEAM_TOTALS)
add("Break the findings down by owning team and check type with the SOX control for each.", R.BY_TEAM)
add("Which account owners have the most mismatches?", R.BY_ACCOUNT_OWNER)
add("Show total contract value by customer type where Salesforce and the contract disagree and by how much.", R.TCV_VARIANCE_BY_CUSTOMER_TYPE)
add_eval_only("What is the exposure by customer type?", R.EXPOSURE_BY_CUSTOMER_TYPE)
add("Show me every contract with amendments where NetSuite still reflects the original terms.", R.NETSUITE_STALE_AFTER_AMENDMENT)
add("Do amended agreements fail the match more often than unamended ones?", R.AMENDED_VS_UNAMENDED)
add("What are the High severity findings?",
    R.SLIM_FINDINGS_CTE + "SELECT F.CONTRACT_NUMBER, F.CUSTOMER_NAME, F.CUSTOMER_TYPE, F.ACCOUNT_OWNER, F.CHECK_TYPE, F.FIELD_NAME, F.VARIANCE_USD, F.OWNING_TEAM, F.SOX_CONTROL_REF FROM F WHERE F.SEVERITY = 'High' ORDER BY ABS(F.VARIANCE_USD) DESC")
add_eval_only("Which findings should Billing review first?",
    R.FINDINGS_CTE + "SELECT F.CONTRACT_NUMBER, F.CUSTOMER_NAME, F.CHECK_TYPE, F.CONTRACT_VALUE, F.NETSUITE_VALUE, F.VARIANCE_USD, F.SEVERITY, F.SOX_CONTROL_REF, F.REASON FROM F WHERE F.OWNING_TEAM = 'Billing' ORDER BY ABS(F.VARIANCE_USD) DESC")
add_eval_only("Which findings should Revenue Accounting review first?",
    R.FINDINGS_CTE + "SELECT F.CONTRACT_NUMBER, F.CUSTOMER_NAME, F.CHECK_TYPE, F.CONTRACT_VALUE, F.SALESFORCE_VALUE, F.NETSUITE_VALUE, F.VARIANCE_USD, F.SEVERITY, F.SOX_CONTROL_REF, F.REASON FROM F WHERE F.OWNING_TEAM = 'Revenue Accounting' ORDER BY ABS(F.VARIANCE_USD) DESC")
add_eval_only("Which findings should Sales Ops review first?",
    R.FINDINGS_CTE + "SELECT F.CONTRACT_NUMBER, F.CUSTOMER_NAME, F.ACCOUNT_OWNER, F.CHECK_TYPE, F.CONTRACT_VALUE, F.SALESFORCE_VALUE, F.VARIANCE_USD, F.SEVERITY, F.SOX_CONTROL_REF, F.REASON FROM F WHERE F.OWNING_TEAM = 'Sales Ops' ORDER BY ABS(F.VARIANCE_USD) DESC")
add("How does the mismatch rate trend by the month the latest document was signed and do amendments drive it?",
    R.SLIM_FINDINGS_CTE + "SELECT CAST(EXTRACT(YEAR FROM C.LATEST_SIGNED_DATE) AS VARCHAR) || '-' || CASE WHEN EXTRACT(MONTH FROM C.LATEST_SIGNED_DATE) < 10 THEN '0' ELSE '' END || CAST(EXTRACT(MONTH FROM C.LATEST_SIGNED_DATE) AS VARCHAR) AS SIGNING_MONTH, COUNT(DISTINCT C.CHAIN_ID) AS AGREEMENTS, COUNT(DISTINCT F.CHAIN_ID) AS WITH_FINDINGS, ROUND(COUNT(DISTINCT F.CHAIN_ID) * 1.0 / COUNT(DISTINCT C.CHAIN_ID), 4) AS MISMATCH_RATE, COUNT(DISTINCT CASE WHEN C.AMENDMENT_COUNT > 0 THEN F.CHAIN_ID END) AS AMENDED_WITH_FINDINGS, COUNT(DISTINCT CASE WHEN C.AMENDMENT_COUNT > 0 THEN C.CHAIN_ID END) AS AMENDED_AGREEMENTS FROM \"V_CONTRACT_CHAIN\" C LEFT JOIN F ON F.CHAIN_ID = C.CHAIN_ID GROUP BY CAST(EXTRACT(YEAR FROM C.LATEST_SIGNED_DATE) AS VARCHAR) || '-' || CASE WHEN EXTRACT(MONTH FROM C.LATEST_SIGNED_DATE) < 10 THEN '0' ELSE '' END || CAST(EXTRACT(MONTH FROM C.LATEST_SIGNED_DATE) AS VARCHAR) ORDER BY SIGNING_MONTH")
add_eval_only("How many findings and how much exposure sit on agreements signed or amended since the Boomi upgrade on 2026-03-01?",
    R.SLIM_FINDINGS_CTE + "SELECT CASE WHEN F.LATEST_SIGNED_DATE >= DATE '2026-03-01' THEN 'Since Boomi upgrade' ELSE 'Before Boomi upgrade' END AS PERIOD, COUNT(*) AS FINDINGS, COUNT(DISTINCT F.CHAIN_ID) AS AGREEMENTS, SUM(ABS(F.VARIANCE_USD)) AS EXPOSURE_USD FROM F GROUP BY CASE WHEN F.LATEST_SIGNED_DATE >= DATE '2026-03-01' THEN 'Since Boomi upgrade' ELSE 'Before Boomi upgrade' END ORDER BY PERIOD")

# ---------------------------------------------------------------- hero chain (CP2): lineage and where each system stands
add(f"Show me the full amendment lineage for {HERO} and where each system is relative to the latest amendment.", R.lineage_for(HERO))
add_eval_only(f"What findings does the {HERO} agreement have and what is the dollar exposure?", R.exposure_for(HERO))
add(f"Show me the full amendment lineage for {HERO} and where Salesforce and NetSuite each stand relative to the latest amendment and what the dollar exposure is",
    R.SLIM_FINDINGS_CTE + f"""SELECT L.VERSION, L.DOCUMENT_NUMBER, L.DOCUMENT_TYPE, L.SIGNED_DATE, L.END_DATE, L.TCV, L.TCV_CHANGE, L.PAYMENT_TERMS, L.BILLING_FREQUENCY,
       CASE WHEN L.VERSION <= COALESCE(S.SF_VERSION_REFLECTED, 0) THEN 'Yes' ELSE 'No' END AS IN_SALESFORCE,
       CASE WHEN L.VERSION <= COALESCE(S.NS_VERSION_REFLECTED, 0) THEN 'Yes' ELSE 'No' END AS IN_NETSUITE,
       S.SF_AMOUNT AS SALESFORCE_BOOKED, S.NS_AMOUNT AS NETSUITE_ORDERED, S.NS_SALES_ORDER_COUNT, S.NS_END_DATE, S.NS_PAYMENT_TERMS, S.NS_BILLING_SCHEDULE_TYPE,
       (SELECT SUM(ABS(F.VARIANCE_USD)) FROM F WHERE F.CUSTOMER_NAME = '{HERO}') AS TOTAL_EXPOSURE_USD,
       (SELECT COUNT(*) FROM F WHERE F.CUSTOMER_NAME = '{HERO}') AS FINDINGS
FROM "V_AMENDMENT_LINEAGE" L
JOIN "V_CHAIN_SYSTEM_SUMMARY" S ON S.CHAIN_ID = L.CHAIN_ID
WHERE L.CUSTOMER_NAME = '{HERO}'
ORDER BY L.VERSION""")
add(f"Show the NetSuite sales orders and billing schedule for {HERO}.",
    f'SELECT SO.SALES_ORDER_ID, SO.OPPORTUNITY_ID, SO.ORDER_DATE, SO.ORDER_TOTAL, SO.START_DATE, SO.END_DATE, SO.PAYMENT_TERMS, SO.BILLING_SCHEDULE_TYPE, SO.STATUS, SO.BOOMI_SYNC_TIMESTAMP, B.BILL_NUMBER, B.BILL_DATE, B.BILL_AMOUNT, B.BILLED, B.INVOICE_NUMBER FROM "NETSUITE_SALES_ORDERS" SO JOIN "CUSTOMERS" CU ON CU.CUSTOMER_ID = SO.CUSTOMER_ID LEFT JOIN "NETSUITE_BILLING_SCHEDULE" B ON B.SALES_ORDER_ID = SO.SALES_ORDER_ID WHERE CU.CUSTOMER_NAME = \'{HERO}\' ORDER BY SO.SALES_ORDER_ID, B.BILL_NUMBER')
add(f"Show the Salesforce opportunities and products for {HERO}.",
    f'SELECT O.OPPORTUNITY_ID, O.OPPORTUNITY_NAME, O.OPPORTUNITY_TYPE, O.AMOUNT, O.CLOSE_DATE, O.CONTRACT_START_DATE, O.CONTRACT_END_DATE, O.LINKED_CONTRACT_NUMBER, O.OWNER, P.PRODUCT_NAME, P.QUANTITY, P.UNIT_PRICE, P.TOTAL_PRICE FROM "SALESFORCE_OPPORTUNITIES" O JOIN "CUSTOMERS" CU ON CU.CUSTOMER_ID = O.CUSTOMER_ID LEFT JOIN "SALESFORCE_OPPORTUNITY_PRODUCTS" P ON P.OPPORTUNITY_ID = O.OPPORTUNITY_ID WHERE CU.CUSTOMER_NAME = \'{HERO}\' ORDER BY O.CLOSE_DATE, P.PRODUCT_NAME')
add(f"Compare the billing schedule in the latest {HERO} amendment with what NetSuite will actually bill.",
    f'SELECT M.MILESTONE_NUMBER, M.MILESTONE_DESCRIPTION, M.SCHEDULED_DATE, M.SCHEDULED_AMOUNT, NB.SALES_ORDER_ID, NB.BILL_DATE, NB.BILL_AMOUNT, NB.BILLED FROM "V_CONTRACT_CHAIN" CH JOIN "CONTRACT_BILLING_SCHEDULE" M ON M.CONTRACT_ID = CH.LATEST_CONTRACT_ID LEFT JOIN (SELECT DISTINCT X.CHAIN_ID, B.SALES_ORDER_ID, B.BILL_DATE, B.BILL_AMOUNT, B.BILLED FROM "V_DEAL_CROSSWALK" X JOIN "NETSUITE_BILLING_SCHEDULE" B ON B.SALES_ORDER_ID = X.SALES_ORDER_ID WHERE X.CHAIN_ID IS NOT NULL) NB ON NB.CHAIN_ID = CH.CHAIN_ID AND DATEDIFF(\'day\', M.SCHEDULED_DATE, NB.BILL_DATE) BETWEEN -7 AND 7 AND ABS(NB.BILL_AMOUNT - M.SCHEDULED_AMOUNT) <= 1 WHERE CH.CUSTOMER_NAME = \'{HERO}\' ORDER BY M.MILESTONE_NUMBER')
add_eval_only("Show the amendment lineage for Dana Whitfield's agreements that have findings.",
    R.SLIM_FINDINGS_CTE + "SELECT L.CUSTOMER_NAME, L.CHAIN_CONTRACT_NUMBER, L.VERSION, L.DOCUMENT_NUMBER, L.SIGNED_DATE, L.TCV, L.TCV_CHANGE, L.END_DATE, COUNT(DISTINCT F.CHECK_TYPE) AS CHECKS_FAILED FROM \"V_AMENDMENT_LINEAGE\" L JOIN F ON F.CHAIN_ID = L.CHAIN_ID WHERE L.ACCOUNT_OWNER = 'Dana Whitfield' GROUP BY L.CUSTOMER_NAME, L.CHAIN_CONTRACT_NUMBER, L.VERSION, L.DOCUMENT_NUMBER, L.SIGNED_DATE, L.TCV, L.TCV_CHANGE, L.END_DATE ORDER BY L.CUSTOMER_NAME, L.CHAIN_CONTRACT_NUMBER, L.VERSION")

# ---------------------------------------------------------------- the agent's question
add("Which agreements signed or amended in the last 7 days have findings and which team owns each one?", R.RECENT_SIGNINGS_FINDINGS)
add("Which agreements were signed or amended in the last 30 days?",
    'SELECT CONTRACT_NUMBER, CUSTOMER_NAME, CUSTOMER_TYPE, ACCOUNT_OWNER, LATEST_CONTRACT_NUMBER, LATEST_VERSION, LATEST_SIGNED_DATE, CURRENT_TCV, CURRENT_END_DATE, SF_VERSION_REFLECTED, NS_VERSION_REFLECTED, SF_AMOUNT, NS_AMOUNT FROM "V_CHAIN_SYSTEM_SUMMARY" WHERE LATEST_SIGNED_DATE >= DATE \'2026-08-31\' ORDER BY LATEST_SIGNED_DATE DESC')
