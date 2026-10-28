"""Story control-point checks for the Meridian Clinician Network demo.

`demo validate` calls run(q, check, spec) against DuckDB before loading and
against Snowflake after. `q(sql)` returns rows; `check(label, cond, detail)`
records a pass/fail. Control points CP1..CP4 per DEMO_PLAN.md / demo.yaml.

The checks use the SAME SQL as the certified query library (recon_sql.py): the
union of the eleven three-way checks is the ground truth the demo is validated
against. There is no results table.
"""
import generator as gen
import recon_sql as R

HERO = gen.HERO_CUSTOMER
OWNER = gen.HERO_OWNER
NS_STALE_CHECKS = ("TERM_END_DATE_MISMATCH", "AMENDMENT_NOT_IN_NETSUITE", "PAYMENT_TERMS_MISMATCH", "BILLING_FREQUENCY_MISMATCH", "DUPLICATE_SALES_ORDERS")


def run(q, check, spec):
    targets = {cp["id"]: {t["metric"]: (t["op"], t["value"]) for t in cp.get("targets", [])} for cp in spec.raw.get("control_points", [])}

    def hit(cp, metric, value):
        op, target = targets[cp][metric]
        ok = {">=": value >= target, "<=": value <= target, ">": value > target, "<": value < target, "==": value == target}[op]
        check(f"{cp} {metric} {op} {target}", ok, f"(actual {value:,.4f})" if isinstance(value, float) else f"(actual {value:,})")

    print("\n== Baseline health ==")
    (chains,) = q('SELECT COUNT(*) FROM "V_CONTRACT_CHAIN"')[0]
    check("Between 250 and 300 contract chains", 250 <= chains <= 300, f"({chains})")
    (docs,) = q('SELECT COUNT(*) FROM "CONTRACTS"')[0]
    check("Between 360 and 440 signed documents", 360 <= docs <= 440, f"({docs})")
    n = q('SELECT COUNT(*) FROM "CONTRACTS" C JOIN (SELECT CONTRACT_ID, SUM(LINE_AMOUNT) T FROM "CONTRACT_LINE_ITEMS" GROUP BY CONTRACT_ID) L ON L.CONTRACT_ID = C.CONTRACT_ID WHERE ABS(L.T - C.TOTAL_CONTRACT_VALUE) > 0.01')[0][0]
    check("Every document's lines sum to its TCV", n == 0, f"({n} differ)")
    n = q('SELECT COUNT(*) FROM "CONTRACTS" C JOIN (SELECT CONTRACT_ID, SUM(SCHEDULED_AMOUNT) T FROM "CONTRACT_BILLING_SCHEDULE" GROUP BY CONTRACT_ID) B ON B.CONTRACT_ID = C.CONTRACT_ID WHERE ABS(B.T - C.TOTAL_CONTRACT_VALUE) > 0.01')[0][0]
    check("Every document's billing schedule sums to its TCV", n == 0, f"({n} differ)")
    n = q('SELECT COUNT(*) FROM "SALESFORCE_OPPORTUNITIES" O JOIN (SELECT OPPORTUNITY_ID, SUM(TOTAL_PRICE) T FROM "SALESFORCE_OPPORTUNITY_PRODUCTS" GROUP BY OPPORTUNITY_ID) P ON P.OPPORTUNITY_ID = O.OPPORTUNITY_ID WHERE ABS(P.T - O.AMOUNT) > 0.01')[0][0]
    check("Every opportunity's products sum to its amount", n == 0, f"({n} differ)")
    n = q('SELECT COUNT(*) FROM "NETSUITE_SALES_ORDERS" S JOIN (SELECT SALES_ORDER_ID, SUM(AMOUNT) T FROM "NETSUITE_SALES_ORDER_LINES" GROUP BY SALES_ORDER_ID) L ON L.SALES_ORDER_ID = S.SALES_ORDER_ID WHERE ABS(L.T - S.ORDER_TOTAL) > 0.01')[0][0]
    check("Every sales order's lines sum to its total", n == 0, f"({n} differ)")
    n = q('SELECT COUNT(*) FROM "V_CONTRACT_CHAIN" WHERE CHAIN_ID NOT IN (SELECT CHAIN_ID FROM "V_DEAL_CROSSWALK" WHERE SALES_ORDER_ID IS NOT NULL AND CHAIN_ID IS NOT NULL)')[0][0]
    check("Every chain has at least one NetSuite sales order", n == 0, f"({n} without)")

    print("\n== The three-way match (union of the eleven checks) ==")
    tot = q(R.SUMMARY_TOTALS)[0]
    findings, chains_with, chains_checked, rate, exposure, high, medium = tot
    print(f"   findings {findings}  chains with findings {chains_with}/{chains_checked}  rate {rate}  exposure ${float(exposure):,.0f}  high {high}  medium {medium}")
    per = q(R.FINDINGS_CTE + 'SELECT CHECK_TYPE, COUNT(*), COUNT(DISTINCT CHAIN_ID), ROUND(SUM(ABS(VARIANCE_USD))) FROM F GROUP BY CHECK_TYPE ORDER BY CHECK_TYPE')
    for r in per:
        print(f"   {r[0]:36s} findings {r[1]:4d}  chains {r[2]:3d}  exposure ${float(r[3]):,.0f}")
    check("Every check type produces at least one finding", {r[0] for r in per} == set(R.CHECKS), f"(missing {set(R.CHECKS) - {r[0] for r in per}})")
    slim = q(R.SLIM_FINDINGS_CTE + 'SELECT CHECK_TYPE, COUNT(*), COUNT(DISTINCT CHAIN_ID), ROUND(SUM(ABS(VARIANCE_USD))), SUM(CASE WHEN SEVERITY = \'High\' THEN 1 ELSE 0 END) FROM F GROUP BY CHECK_TYPE ORDER BY CHECK_TYPE')
    full = q(R.FINDINGS_CTE + 'SELECT CHECK_TYPE, COUNT(*), COUNT(DISTINCT CHAIN_ID), ROUND(SUM(ABS(VARIANCE_USD))), SUM(CASE WHEN SEVERITY = \'High\' THEN 1 ELSE 0 END) FROM F GROUP BY CHECK_TYPE ORDER BY CHECK_TYPE')
    check("The compact roll-up union agrees with the full union on every check (count, chains, exposure, High)", [tuple(r) for r in slim] == [tuple(r) for r in full])
    flagged = {r[0] for r in q(R.FINDINGS_CTE + 'SELECT DISTINCT CONTRACT_NUMBER FROM F WHERE CHAIN_ID IS NOT NULL')}
    if not gen.SEEDED:
        gen.generate_all(verbose=False)   # the registry only fills when the generator runs (deterministic, < 1 s)
    seeded = set(gen.SEEDED)
    extra, missing = sorted(flagged - seeded), sorted(seeded - flagged)
    check("The flagged chains are exactly the seeded drift chains", flagged == seeded, f"(unexpected {extra[:8]} / unflagged {missing[:8]})")

    print("\n== CP1: Q3 close ==")
    hit("CP1", "chain_mismatch_rate", float(rate))
    hit("CP1", "open_exposure_usd", float(exposure))
    hit("CP1", "high_severity_findings", int(high))

    print("\n== CP2: Halvorsen chain and amendments ==")
    h = q(f'SELECT AMENDMENT_COUNT, LATEST_VERSION, SF_VERSION_REFLECTED, NS_VERSION_REFLECTED, CURRENT_TCV, SF_AMOUNT, NS_AMOUNT, NS_SALES_ORDER_COUNT, NS_END_DATE, CURRENT_END_DATE, NS_PAYMENT_TERMS, CURRENT_PAYMENT_TERMS, NS_BILLING_SCHEDULE_TYPE, CURRENT_BILLING_FREQUENCY FROM "V_CHAIN_SYSTEM_SUMMARY" WHERE CUSTOMER_NAME = \'{HERO}\'')
    check("Halvorsen has exactly one chain", len(h) == 1, f"({len(h)})")
    h = h[0]
    print("   hero summary:", h)
    hit("CP2", "hero_amendment_count", int(h[0]))
    hit("CP2", "hero_netsuite_amendments_behind", int(h[1]) - int(h[3] or 0))
    hit("CP2", "hero_salesforce_amendments_behind", int(h[1]) - int(h[2] or 0))
    check("Hero current TCV is 2,730,000", float(h[4]) == 2730000.0, f"({h[4]})")
    check("Hero Salesforce bookings are 2,850,000", float(h[5]) == 2850000.0, f"({h[5]})")
    check("Hero NetSuite orders total 2,250,000 across two orders", float(h[6]) == 2250000.0 and int(h[7]) == 2, f"({h[6]}, {h[7]} orders)")
    check("Hero NetSuite still Net 30 / Quarterly / original end date", h[10] == "Net 30" and h[12] == "Quarterly" and str(h[8]).startswith("2026-08-31"), f"({h[10]}, {h[12]}, {h[8]})")
    hero_f = q(R.exposure_for(HERO))
    print("   hero findings:", [(r[1], float(r[6])) for r in hero_f])
    hit("CP2", "hero_exposure_usd", float(sum(abs(float(r[6])) for r in hero_f)))
    check("Hero findings include the amendment, end date, payment terms, billing and duplicate checks",
          {"AMENDMENT_NOT_IN_NETSUITE", "AMENDMENT_NOT_IN_SALESFORCE", "TERM_END_DATE_MISMATCH", "PAYMENT_TERMS_MISMATCH", "BILLING_FREQUENCY_MISMATCH", "DUPLICATE_SALES_ORDERS", "TCV_MISMATCH", "MISSING_BILLING_MILESTONE"} <= {r[1] for r in hero_f})
    lin = q(R.lineage_for(HERO))
    check("Hero lineage shows versions 0..3 with Salesforce Yes/Yes/Yes/No and NetSuite Yes/Yes/No/No",
          [(r[1], r[-2], r[-1]) for r in lin] == [(0, "Yes", "Yes"), (1, "Yes", "Yes"), (2, "Yes", "No"), (3, "No", "No")], f"({[(r[1], r[-2], r[-1]) for r in lin]})")
    stale = q(R.NETSUITE_STALE_AFTER_AMENDMENT)
    hit("CP2", "netsuite_stale_amended_chains", len(stale))
    av = {r[0]: (int(r[1]), int(r[2]), float(r[3])) for r in q(R.AMENDED_VS_UNAMENDED)}
    print("   amended vs not:", av)
    hit("CP2", "amended_vs_unamended_finding_ratio", round(av["Amended"][2] / max(av["Not amended"][2], 1e-9), 4))

    print("\n== CP3: missing billing milestones ==")
    m = q(R.FINDINGS_CTE + "SELECT COUNT(*), SUM(VARIANCE_USD), COUNT(DISTINCT CHAIN_ID) FROM F WHERE CHECK_TYPE = 'MISSING_BILLING_MILESTONE'")[0]
    print(f"   missing milestones {m[0]} on {m[2]} chains, ${float(m[1]):,.0f}")
    hit("CP3", "missing_milestones", int(m[0]))
    hit("CP3", "missing_milestone_usd", float(m[1]))

    print("\n== CP4: ownership ==")
    units = q(R.FINDINGS_CTE + "SELECT OWNING_TEAM, COUNT(*) FROM (SELECT DISTINCT OWNING_TEAM, COALESCE(CHAIN_ID, DETAIL_KEY) AS K, CHECK_TYPE FROM F) U GROUP BY OWNING_TEAM")
    units = {r[0]: int(r[1]) for r in units}
    total_units = sum(units.values())
    print("   finding units (chain x check) by team:", units)
    hit("CP4", "revenue_team_share", round(units.get("Revenue Accounting", 0) / total_units, 4))
    hit("CP4", "sales_ops_team_share", round(units.get("Sales Ops", 0) / total_units, 4))
    hit("CP4", "billing_team_share", round(units.get("Billing", 0) / total_units, 4))
    ct = {r[0]: float(r[3]) for r in q(R.EXPOSURE_BY_CUSTOMER_TYPE)}
    print("   exposure by customer type:", ct)
    hit("CP4", "pharma_share_of_variance_usd", round(ct.get("Pharma", 0) / max(sum(ct.values()), 1e-9), 4))
    owners = q(R.BY_ACCOUNT_OWNER)
    for r in owners[:5]:
        print("   ", r[0], r[1], f"chains {r[2]} with findings {r[3]} rate {r[4]} exposure ${float(r[6]):,.0f}")
    dana = [r for r in owners if r[0] == OWNER][0]
    overall = float(chains_with) / float(chains_checked)
    hit("CP4", "hero_owner_rate_vs_average", round(float(dana[4]) / overall, 4))
    check("Dana Whitfield has the highest mismatch rate of any account owner", owners[0][0] == OWNER, f"(top is {owners[0][0]})")

    print("\n== Integrity ==")
    n = q('SELECT COUNT(*) FROM "CONTRACTS" WHERE AMENDMENT_NUMBER > 0 AND PARENT_CONTRACT_ID IS NULL')[0][0]
    check("Every amendment points at its original agreement", n == 0, f"({n})")
    n = q('SELECT COUNT(*) FROM "CONTRACTS" A JOIN "CONTRACTS" O ON O.CONTRACT_ID = A.PARENT_CONTRACT_ID WHERE A.SIGNED_DATE <= O.SIGNED_DATE')[0][0]
    check("Amendments are signed after their original", n == 0, f"({n})")
    n = q('SELECT COUNT(*) FROM "CONTRACTS" WHERE SIGNED_DATE > DATE \'2026-09-30\'')[0][0]
    check("No document is signed after the as-of date", n == 0, f"({n})")
    n = q('SELECT COUNT(*) FROM "NETSUITE_BILLING_SCHEDULE" WHERE (BILLED = TRUE AND BILL_DATE > DATE \'2026-09-30\') OR (BILLED = FALSE AND BILL_DATE <= DATE \'2026-09-30\')')[0][0]
    check("Billed flag agrees with the bill date and the as-of date", n == 0, f"({n})")
    n = q('SELECT COUNT(*) - COUNT(DISTINCT CUSTOMER_NAME) FROM "CUSTOMERS"')[0][0]
    check("Customer names are unique", n == 0, f"({n})")
    n = q('SELECT COUNT(*) - COUNT(DISTINCT CONTRACT_NUMBER) FROM "CONTRACTS"')[0][0]
    check("Contract numbers are unique", n == 0, f"({n})")
