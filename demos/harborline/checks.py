"""Story control-point checks for the Harborline Private Capital demo.

`demo validate` calls run(q, check, spec) against DuckDB before loading and
against Snowflake after. `q(sql)` returns rows; `check(label, cond, detail)`
records a pass/fail. Control points CP1..CP4 per DEMO_PLAN.md.
"""
import generator as hg

LATEST = "DATE '2026-06-30'"


def run(q, check, spec):
    print("\n== Baseline health ==")
    (n_funds,) = q("SELECT COUNT(*) FROM FUNDS")[0]
    check("350 to 480 funds", 350 <= n_funds <= 480, f"({n_funds})")
    (n_latest,) = q(f"SELECT COUNT(*) FROM FUND_QUARTERLY_NAV WHERE QUARTER_END = {LATEST}")[0]
    check("at least 300 funds report the latest quarter 2026-06-30", n_latest >= 300, f"({n_latest})")
    (irr_all,) = q(f"SELECT ROUND(AVG(IRR_SINCE_INCEPTION_PCT),2) FROM V_FUND_PERFORMANCE_LATEST WHERE VINTAGE_YEAR <= 2019")[0]
    check("average IRR of 2012-2019 vintages between 8 and 16 percent", 8 <= irr_all <= 16, f"({irr_all})")
    (neg_nav,) = q("SELECT COUNT(*) FROM FUND_QUARTERLY_NAV WHERE NAV_USD_M < 0 OR CUMULATIVE_CALLED_USD_M < 0")[0]
    check("no negative NAV or called capital", neg_nav == 0, f"({neg_nav})")
    (cf_mismatch,) = q("""
        SELECT COUNT(*) FROM (
            SELECT n.FUND_ID, n.QUARTER_END,
                   n.CUMULATIVE_CALLED_USD_M - COALESCE(LAG(n.CUMULATIVE_CALLED_USD_M) OVER (PARTITION BY n.FUND_ID ORDER BY n.QUARTER_END), 0) AS CALLED_INC,
                   COALESCE(c.CALLS, 0) AS CALLS
            FROM FUND_QUARTERLY_NAV n
            LEFT JOIN (SELECT FUND_ID, QUARTER_END, SUM(AMOUNT_USD_M) AS CALLS FROM FUND_CASH_FLOWS WHERE FLOW_TYPE = 'CAPITAL_CALL' GROUP BY FUND_ID, QUARTER_END) c
                   ON c.FUND_ID = n.FUND_ID AND c.QUARTER_END = n.QUARTER_END
        ) x WHERE ABS(CALLED_INC - CALLS) > 0.2""")[0]
    check("quarterly capital calls reconcile to cumulative called capital", cf_mismatch == 0, f"({cf_mismatch} mismatches)")

    print("\n== CP1: NA buyout 2015-2020 custom index vs Harborline Broad PE Index ==")
    cohort = q(f"""
        SELECT COUNT(*), ROUND(MEDIAN(IRR_SINCE_INCEPTION_PCT),2)
        FROM V_FUND_PERFORMANCE_LATEST
        WHERE STRATEGY = 'Buyout' AND REGION = 'North America' AND VINTAGE_YEAR BETWEEN 2015 AND 2020 AND QUARTER_END = {LATEST}""")[0]
    broad = q(f"SELECT POOLED_IRR_PCT FROM V_BENCHMARK_QUARTERLY WHERE BENCHMARK_ID = '{hg.BROAD_PE}' AND VINTAGE_YEAR IS NULL AND QUARTER_END = {LATEST}")[0][0]
    print(f"   cohort funds={cohort[0]} median IRR={cohort[1]} broad PE pooled IRR={broad}")
    check("cohort has at least 40 funds", cohort[0] >= 40, f"({cohort[0]})")
    gap = cohort[1] - broad
    check("cohort median IRR beats the Broad PE Index by 2.0 to 4.5 pts", 2.0 <= gap <= 4.5, f"({gap:.2f})")
    sz = q(f"""
        SELECT SIZE_BUCKET, COUNT(*), ROUND(MEDIAN(IRR_SINCE_INCEPTION_PCT),2)
        FROM V_FUND_PERFORMANCE_LATEST
        WHERE STRATEGY = 'Buyout' AND REGION = 'North America' AND VINTAGE_YEAR BETWEEN 2015 AND 2020 AND QUARTER_END = {LATEST}
        GROUP BY SIZE_BUCKET ORDER BY SIZE_BUCKET""")
    print("   by size bucket:", sz)
    d = {r[0]: r for r in sz}
    check("mid-market and mega each have at least 8 cohort funds", d["MID_MARKET"][1] >= 8 and d["MEGA"][1] >= 8)
    check("mid-market median IRR beats mega by at least 2 pts", d["MID_MARKET"][2] - d["MEGA"][2] >= 2.0, f"({d['MID_MARKET'][2]} vs {d['MEGA'][2]})")

    print("\n== CP2: subscription lines and the Calder Ridge IV report ==")
    young = q("""
        SELECT ROUND(AVG(CASE WHEN USES_SUBSCRIPTION_LINE THEN IRR_SINCE_INCEPTION_PCT END)
                   - AVG(CASE WHEN USES_SUBSCRIPTION_LINE THEN NULL ELSE IRR_SINCE_INCEPTION_PCT END), 2),
               SUM(CASE WHEN USES_SUBSCRIPTION_LINE THEN 1 ELSE 0 END), SUM(CASE WHEN USES_SUBSCRIPTION_LINE THEN 0 ELSE 1 END)
        FROM V_FUND_PERFORMANCE_QUARTERLY WHERE VINTAGE_YEAR BETWEEN 2019 AND 2022 AND FUND_AGE_QUARTERS = 8""")[0]
    print(f"   2019-2022 vintages at 8 quarters: gap={young[0]} (with line {young[1]} / without {young[2]})")
    check("young vintages: IRR gap with line vs without at 8 quarters >= 3 pts", young[0] >= 3.0, f"({young[0]})")
    mature = q(f"""
        SELECT ROUND(AVG(CASE WHEN USES_SUBSCRIPTION_LINE THEN IRR_SINCE_INCEPTION_PCT END)
                   - AVG(CASE WHEN USES_SUBSCRIPTION_LINE THEN NULL ELSE IRR_SINCE_INCEPTION_PCT END), 2)
        FROM V_FUND_PERFORMANCE_LATEST WHERE VINTAGE_YEAR BETWEEN 2014 AND 2017 AND QUARTER_END = {LATEST}""")[0][0]
    check("mature vintages 2014-2017: gap at the latest quarter <= 1.5 pts", abs(mature) <= 1.5, f"({mature})")
    hero = q(f"""SELECT NAV_USD_M, CUMULATIVE_CALLED_USD_M, CUMULATIVE_DISTRIBUTED_USD_M, CREDIT_LINE_BALANCE_USD_M, IRR_SINCE_INCEPTION_PCT, TVPI, DPI
                 FROM V_FUND_PERFORMANCE_LATEST WHERE FUND_ID = '{hg.HERO_FUND_ID}' AND QUARTER_END = {LATEST}""")[0]
    print("   Calder Ridge IV Q2 2026:", hero)
    check("hero NAV 2614 called 2880 distributed 1152 line 210 IRR 18.4",
          (float(hero[0]), float(hero[1]), float(hero[2]), float(hero[3]), float(hero[4])) == (2614.0, 2880.0, 1152.0, 210.0, 18.4), f"({hero})")
    flows = q(f"SELECT FLOW_TYPE, ROUND(SUM(AMOUNT_USD_M),1) FROM FUND_CASH_FLOWS WHERE FUND_ID = '{hg.HERO_FUND_ID}' AND QUARTER_END = {LATEST} GROUP BY FLOW_TYPE ORDER BY FLOW_TYPE")
    check("hero Q2 2026 flows: calls 64.0 and distributions 96.0", [(a, float(b)) for a, b in flows] == [("CAPITAL_CALL", 64.0), ("DISTRIBUTION", 96.0)], f"({flows})")
    ext = q(f"""SELECT MATCHES_PUBLISHED, EXTRACTED_NAV_USD_M, EXTRACTED_CREDIT_LINE_BALANCE_USD_M, REVIEW_STATUS, SOURCE_DOCUMENT
                FROM V_REPORT_EXTRACTION_RECONCILIATION WHERE FUND_ID = '{hg.HERO_FUND_ID}' AND REPORT_QUARTER_END = {LATEST}""")[0]
    check("hero report extraction matches the published figures", bool(ext[0]) and float(ext[1]) == 2614.0 and float(ext[2]) == 210.0 and ext[4] == hg.HERO_REPORT_FILE, f"({ext})")
    (n_review,) = q("SELECT COUNT(*) FROM V_REPORT_EXTRACTION_RECONCILIATION WHERE REVIEW_STATUS <> 'AUTO_ACCEPTED'")[0]
    check("some extractions need analyst review (10 to 120)", 10 <= n_review <= 120, f"({n_review})")

    print("\n== CP3: distribution drought ==")
    dpi = q("""
        SELECT CASE WHEN VINTAGE_YEAR BETWEEN 2014 AND 2016 THEN 'old' ELSE 'new' END AS grp, ROUND(MEDIAN(DPI),3), COUNT(*)
        FROM V_FUND_PERFORMANCE_QUARTERLY
        WHERE FUND_AGE_QUARTERS = 16 AND (VINTAGE_YEAR BETWEEN 2014 AND 2016 OR VINTAGE_YEAR BETWEEN 2021 AND 2022)
        GROUP BY CASE WHEN VINTAGE_YEAR BETWEEN 2014 AND 2016 THEN 'old' ELSE 'new' END""")
    d = {r[0]: r for r in dpi}
    print("   median DPI at 16 quarters:", dpi)
    check("2021-2022 vintages median DPI at 16 quarters <= 0.30", d["new"][1] <= 0.30, f"({d['new'][1]})")
    check("2014-2016 vintages median DPI at 16 quarters >= 0.55", d["old"][1] >= 0.55, f"({d['old'][1]})")
    h = q("""
        SELECT SUM(CASE WHEN FLOW_DATE BETWEEN DATE '2021-01-01' AND DATE '2021-06-30' THEN AMOUNT_USD_M ELSE 0 END),
               SUM(CASE WHEN FLOW_DATE BETWEEN DATE '2026-01-01' AND DATE '2026-06-30' THEN AMOUNT_USD_M ELSE 0 END)
        FROM FUND_CASH_FLOWS WHERE FLOW_TYPE = 'DISTRIBUTION'""")[0]
    chg = float(h[1]) / float(h[0]) - 1
    check("H1 2026 distributions at least 25% below H1 2021", chg <= -0.25, f"(H1 2021 {float(h[0]):,.0f} -> H1 2026 {float(h[1]):,.0f}; {chg:+.1%})")

    print("\n== CP4: Westbrook State Retirement System 2018 sleeve ==")
    rows = q(f"""SELECT VINTAGE_YEAR, FUND_COUNT, COMMITTED_USD_M, PORTFOLIO_IRR_PCT, BENCHMARK_IRR_PCT, IRR_GAP_PTS
                 FROM V_ALLOCATOR_VINTAGE_VS_BENCHMARK WHERE ALLOCATOR_ID = '{hg.HERO_ALLOCATOR_ID}' AND QUARTER_END = {LATEST} ORDER BY VINTAGE_YEAR""")
    for r in rows:
        print("   ", r)
    g = {int(r[0]): r for r in rows}
    check("Westbrook holds 2018 vintage funds", 2018 in g)
    check("2018 sleeve lags its matching benchmarks by at least 2 pts", 2018 in g and float(g[2018][5]) <= -2.0, f"({g.get(2018)})")
    worst = min(int(r[0]) for r in rows if r[5] is not None) if rows else None
    worst = min(rows, key=lambda r: float(r[5]) if r[5] is not None else 99)
    check("2018 is the worst vintage for Westbrook", int(worst[0]) == 2018, f"(worst {worst[0]} {worst[5]})")
    others = [float(r[5]) for r in rows if int(r[0]) != 2018 and r[5] is not None]
    check("every other Westbrook vintage is within 1.5 pts of or above benchmark", min(others) >= -1.5, f"(min {min(others):.2f})")
    lag = q(f"""SELECT FUND_NAME, STRATEGY, FUND_IRR_PCT, BENCHMARK_IRR_PCT, IRR_GAP_VS_BENCHMARK_PTS
                FROM V_ALLOCATOR_HOLDINGS WHERE ALLOCATOR_ID = '{hg.HERO_ALLOCATOR_ID}' AND VINTAGE_YEAR = 2018 AND IRR_GAP_VS_BENCHMARK_PTS <= -8 ORDER BY IRR_GAP_VS_BENCHMARK_PTS""")
    print("   2018 funds 8+ pts below benchmark:", lag)
    check("exactly two venture funds explain the gap (8+ pts below benchmark)", len(lag) == 2 and all(r[1] == "Venture" for r in lag), f"({[r[0] for r in lag]})")

    print("\n== Referential integrity ==")
    fk = [
        ("FUNDS.MANAGER_ID", "SELECT COUNT(*) FROM FUNDS f LEFT JOIN MANAGERS m ON m.MANAGER_ID = f.MANAGER_ID WHERE m.MANAGER_ID IS NULL"),
        ("FUNDS.BENCHMARK_ID", "SELECT COUNT(*) FROM FUNDS f LEFT JOIN BENCHMARKS b ON b.BENCHMARK_ID = f.BENCHMARK_ID WHERE b.BENCHMARK_ID IS NULL"),
        ("FUND_QUARTERLY_NAV.FUND_ID", "SELECT COUNT(*) FROM FUND_QUARTERLY_NAV n LEFT JOIN FUNDS f ON f.FUND_ID = n.FUND_ID WHERE f.FUND_ID IS NULL"),
        ("FUND_CASH_FLOWS.FUND_ID", "SELECT COUNT(*) FROM FUND_CASH_FLOWS c LEFT JOIN FUNDS f ON f.FUND_ID = c.FUND_ID WHERE f.FUND_ID IS NULL"),
        ("ALLOCATOR_COMMITMENTS.FUND_ID", "SELECT COUNT(*) FROM ALLOCATOR_COMMITMENTS c LEFT JOIN FUNDS f ON f.FUND_ID = c.FUND_ID WHERE f.FUND_ID IS NULL"),
        ("ALLOCATOR_COMMITMENTS.ALLOCATOR_ID", "SELECT COUNT(*) FROM ALLOCATOR_COMMITMENTS c LEFT JOIN ALLOCATORS a ON a.ALLOCATOR_ID = c.ALLOCATOR_ID WHERE a.ALLOCATOR_ID IS NULL"),
        ("BENCHMARK_QUARTERLY.BENCHMARK_ID", "SELECT COUNT(*) FROM BENCHMARK_QUARTERLY q LEFT JOIN BENCHMARKS b ON b.BENCHMARK_ID = q.BENCHMARK_ID WHERE b.BENCHMARK_ID IS NULL"),
        ("FUND_REPORT_EXTRACTS.FUND_ID", "SELECT COUNT(*) FROM FUND_REPORT_EXTRACTS e LEFT JOIN FUNDS f ON f.FUND_ID = e.FUND_ID WHERE f.FUND_ID IS NULL"),
        ("Unique fund ids", "SELECT COUNT(*) - COUNT(DISTINCT FUND_ID) FROM FUNDS"),
        ("Unique fund names", "SELECT COUNT(*) - COUNT(DISTINCT FUND_NAME) FROM FUNDS"),
        ("Unique fund-quarter rows", "SELECT COUNT(*) - COUNT(DISTINCT FUND_ID || CAST(QUARTER_END AS VARCHAR)) FROM FUND_QUARTERLY_NAV"),
    ]
    for label, sql in fk:
        n = q(sql)[0][0]
        check(f"{label} orphan/dup count = 0", n == 0, f"({n})")
