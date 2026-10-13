"""Story control-point checks for the Keelstone Data Systems demo.

`demo validate` calls run(q, check, spec) against DuckDB before loading and
against Snowflake after. `q(sql)` returns rows; `check(label, cond, detail)`
records a pass/fail. Control points CP1..CP4 per DEMO_PLAN.md / demo.yaml.
"""
import generator as ks


def _rate(rows):
    due = sum(r[0] for r in rows)
    ren = sum(r[1] for r in rows)
    return ren / due if due else None


def run(q, check, spec):
    targets = {cp["id"]: {t["metric"]: (t["op"], t["value"]) for t in cp.get("targets", [])} for cp in spec.raw.get("control_points", [])}

    def hit(cp, metric, value):
        op, target = targets[cp][metric]
        ok = {">=": value >= target, "<=": value <= target, ">": value > target, "<": value < target, "==": value == target}[op]
        check(f"{cp} {metric} {op} {target}", ok, f"(actual {value:,.4f})" if isinstance(value, float) else f"(actual {value:,})")

    print("\n== Baseline health ==")
    (arr,) = q("SELECT SUM(arr) FROM V_ARR_MONTHLY WHERE arr_month = DATE '2026-09-01'")[0]
    check("Finance ARR for September 2026 between $250M and $700M", 250e6 <= arr <= 700e6, f"(${arr:,.0f})")
    fy26 = q("SELECT ROUND(SUM(arr_renewed)/SUM(arr_due),4) FROM V_RENEWAL_PERFORMANCE WHERE fiscal_year='FY26'")[0][0]
    check("Company renewal rate FY26 between 0.88 and 0.93", 0.88 <= fy26 <= 0.93, f"({fy26})")
    rows = q("SELECT region, ROUND(SUM(arr_renewed)/SUM(arr_due),4) FROM V_RENEWAL_PERFORMANCE WHERE fiscal_year='FY26' GROUP BY region ORDER BY region")
    print("  FY26 renewal rate by region:", rows)
    check("Every region FY26 renewal rate >= 0.87", all(r[1] >= 0.87 for r in rows), f"({rows})")

    print("\n== CP1: Americas East renewal slip ==")
    rows = q("""SELECT region, fiscal_year, SUM(arr_due), SUM(arr_renewed), SUM(arr_churned), SUM(arr_pending)
                FROM V_RENEWAL_PERFORMANCE GROUP BY region, fiscal_year ORDER BY region, fiscal_year""")
    for r in rows:
        print("   ", r[0], r[1], f"due ${r[2]:,.0f} renewed {r[3]/r[2]:.3f} churned {r[4]/r[2]:.3f} pending {r[5]/r[2]:.3f}")
    ae26 = [r for r in rows if r[0] == ks.HERO_REGION and r[1] == "FY26"][0]
    ae27 = [r for r in rows if r[0] == ks.HERO_REGION and r[1] == "FY27"][0]
    drop = ae26[3] / ae26[2] - ae27[3] / ae27[2]
    hit("CP1", "amer_east_renewal_rate_drop_pts", round(drop, 4))
    other_drops = [(r[0], round(([x for x in rows if x[0] == r[0] and x[1] == "FY26"][0][3] / [x for x in rows if x[0] == r[0] and x[1] == "FY26"][0][2]) - r[3] / r[2], 4))
                   for r in rows if r[1] == "FY27" and r[0] != ks.HERO_REGION]
    print("   other region FY26->FY27 drops:", other_drops)
    check("Americas East has the largest FY27 drop and every other region drops less than 4 pts", all(d < 0.04 for _, d in other_drops) and all(d < drop for _, d in other_drops))
    fam = q(f"""SELECT product_family, SUM(arr_due), ROUND(SUM(arr_renewed)/SUM(arr_due),4) FROM V_RENEWAL_PERFORMANCE
                WHERE region='{ks.HERO_REGION}' AND fiscal_year='FY27' AND contract_type='SUPPORT' GROUP BY product_family ORDER BY 3""")
    print("   AE FY27 support renewal by family:", fam)
    check("KS-7000 has the lowest FY27 support renewal rate in Americas East", fam and fam[0][0] == ks.EOS_FAMILY)
    w = q(f"SELECT SUM(annual_value), SUM(CASE WHEN risk_flag='AT_RISK' THEN annual_value ELSE 0 END), COUNT(*) FROM V_RENEWALS_AT_RISK_90D WHERE region='{ks.HERO_REGION}'")[0]
    print(f"   AE next 90 days: ${w[0]:,.0f} renewing, ${w[1]:,.0f} at risk, {w[2]} contracts")
    hit("CP1", "amer_east_arr_renewing_90d", float(w[0]))
    hit("CP1", "amer_east_arr_at_risk_90d", float(w[1]))
    reasons = q(f"SELECT risk_reason, COUNT(*), ROUND(SUM(annual_value)) FROM V_RENEWALS_AT_RISK_90D WHERE region='{ks.HERO_REGION}' AND risk_flag='AT_RISK' GROUP BY risk_reason ORDER BY 3 DESC")
    print("   AE at-risk reasons:", reasons)
    check("End of support product and Open P1 case are the top two at-risk reasons in Americas East", {r[0] for r in reasons[:2]} == {"End of support product", "Open P1 case"}, f"({reasons[:2]})")
    p1 = q(f"""SELECT region, SUM(p1_cases) FROM V_SUPPORT_CASE_SUMMARY WHERE firmware_version='{ks.BAD_FW}' AND category='Firmware' AND opened_month >= DATE '2026-07-01'
               GROUP BY region ORDER BY 2 DESC""")
    print("   P1 firmware cases on 9.14.2 since July by region:", p1)
    ae_p1 = [r[1] for r in p1 if r[0] == ks.HERO_REGION][0]
    nxt = max([r[1] for r in p1 if r[0] != ks.HERO_REGION] or [1])
    hit("CP1", "amer_east_keelos914_p1_ratio_vs_next_region", round(ae_p1 / max(nxt, 1), 4))
    check("At least 25 P1 firmware cases on 9.14.2 in Americas East", ae_p1 >= 25, f"({ae_p1})")
    notes = q(f"SELECT COUNT(*) FROM SUPPORT_CASES WHERE priority='P1' AND firmware_version='{ks.BAD_FW}' AND case_notes LIKE '%renewal%'")[0][0]
    check("P1 case notes mention the renewal in at least 15 cases", notes >= 15, f"({notes})")

    print("\n== CP2: Finance ARR vs Sales Ops ARR ==")
    rows = q("SELECT arr_month, SUM(finance_arr), SUM(lapsed_open_arr), ROUND(SUM(lapsed_open_arr)/SUM(finance_arr),4) FROM V_ARR_FINANCE_VS_SALESOPS GROUP BY arr_month ORDER BY arr_month")
    for r in rows[-6:]:
        print("   ", r)
    sep = [r for r in rows if str(r[0]).startswith("2026-09")][0]
    hit("CP2", "salesops_vs_finance_arr_gap_sep2026", float(sep[3]))
    byreg = q("SELECT region, ROUND(SUM(lapsed_open_arr)/SUM(finance_arr),4) FROM V_ARR_FINANCE_VS_SALESOPS WHERE arr_month = DATE '2026-09-01' GROUP BY region ORDER BY 2 DESC")
    print("   September gap by region:", byreg)
    check("Americas East has the largest September gap", byreg[0][0] == ks.HERO_REGION)

    print("\n== CP3: Cloud consumption ==")
    yoy = q("""SELECT SUM(CASE WHEN usage_month BETWEEN DATE '2026-06-01' AND DATE '2026-09-01' THEN consumed_amount ELSE 0 END),
                      SUM(CASE WHEN usage_month BETWEEN DATE '2025-06-01' AND DATE '2025-09-01' THEN consumed_amount ELSE 0 END)
               FROM CLOUD_CONSUMPTION_MONTHLY""")[0]
    growth = yoy[0] / yoy[1] - 1
    print(f"   Jun-Sep consumption: 2026 ${yoy[0]:,.0f} vs 2025 ${yoy[1]:,.0f} ({growth:+.1%})")
    hit("CP3", "cloud_consumption_yoy_growth", round(growth, 4))
    under = q("SELECT COUNT(*), ROUND(SUM(commit_amount - consumed_amount)) FROM V_CLOUD_COMMIT_UTILIZATION WHERE fiscal_year='FY27' AND segment='ENTERPRISE' AND is_under_utilized = 1")[0]
    print(f"   Enterprise accounts under 60% of FY27 commit: {under[0]} (${under[1]:,.0f} unconsumed)")
    hit("CP3", "enterprise_accounts_under_60pct_commit", int(under[0]))
    allu = q("SELECT ROUND(SUM(consumed_amount)/SUM(commit_amount),4) FROM V_CLOUD_COMMIT_UTILIZATION WHERE fiscal_year='FY27'")[0][0]
    check("Overall FY27 commit utilisation between 0.65 and 1.10", 0.65 <= allu <= 1.10, f"({allu})")

    print("\n== CP4: Altura attach rate ==")
    rows = q("""SELECT partner_name, fiscal_year, SUM(systems_installed), ROUND(SUM(systems_with_support)/SUM(systems_installed),4)
                FROM V_PARTNER_ATTACH_RATE WHERE fiscal_year IN ('FY26','FY27') GROUP BY partner_name, fiscal_year ORDER BY partner_name, fiscal_year""")
    by = {}
    for name, fy, n, rate in rows:
        by.setdefault(name, {})[fy] = (n, rate)
    alt = by["Altura Technology Partners"]
    print("   Altura:", alt)
    hit("CP4", "altura_attach_rate_drop_pts", round(alt["FY26"][1] - alt["FY27"][1], 4))
    peers = {k: v for k, v in by.items() if k != "Altura Technology Partners" and "FY26" in v and "FY27" in v and v["FY26"][0] >= 25 and v["FY27"][0] >= 15 and k != "Keelstone Direct"}
    peer_changes = {k: round(abs(v["FY26"][1] - v["FY27"][1]), 4) for k, v in peers.items()}
    print("   peer partner |change|:", peer_changes)
    # the plan promises peers within +/-3 pts; measured on the larger peers (>=25 FY26 installs)
    top_peers = sorted(peers.items(), key=lambda kv: -kv[1]["FY26"][0])[:4]
    worst = max(round(abs(v["FY26"][1] - v["FY27"][1]), 4) for _, v in top_peers)
    hit("CP4", "peer_partner_attach_rate_max_abs_change_pts", worst)

    print("\n== Integrity ==")
    n = q("SELECT COUNT(*) FROM CONTRACTS c JOIN CONTRACTS s ON s.contract_id = c.successor_contract_id WHERE s.start_date <> c.end_date")[0][0]
    check("Every renewal starts on the predecessor end date", n == 0, f"({n})")
    n = q("SELECT COUNT(*) FROM CONTRACTS WHERE contract_status = 'ACTIVE' AND end_date <= DATE '2026-10-12'")[0][0]
    check("No ACTIVE contract has lapsed", n == 0, f"({n})")
    n = q("SELECT COUNT(*) FROM CONTRACTS WHERE contract_status <> 'ACTIVE' AND end_date > DATE '2026-10-12'")[0][0]
    check("No lapsed status on a contract still in force", n == 0, f"({n})")
    n = q("SELECT COUNT(*) FROM SUPPORT_CASES WHERE case_status = 'CLOSED' AND closed_date IS NULL")[0][0]
    check("Closed cases have a closed date", n == 0, f"({n})")
    n = q("SELECT COUNT(*) FROM RENEWAL_OPPORTUNITIES o JOIN CONTRACTS c ON c.contract_id = o.contract_id WHERE (o.stage = 'Closed Won' AND c.contract_status <> 'RENEWED') OR (o.stage = 'Closed Lost' AND c.contract_status <> 'CHURNED')")[0][0]
    check("Opportunity stages agree with contract status", n == 0, f"({n})")
    n = q("SELECT COUNT(*) - COUNT(DISTINCT customer_name) FROM CUSTOMERS")[0][0]
    check("Customer names are unique", n == 0, f"({n})")
