"""Story control-point checks for the Halcyon demo (from validate_duckdb.py).

`demo validate` calls run(q, check, spec) against DuckDB before loading and
against Snowflake after. `q(sql)` returns rows; `check(label, cond, detail)`
records a pass/fail. Control points CP1..CP6 per 00_DESIGN.md.
"""
import generator as hc


def run(q, check, spec):
    print("\n== Baseline health ==")
    (fr,) = q("SELECT ROUND(AVG(is_line_filled_complete),4) FROM V_ORDER_LINE_DETAIL WHERE line_status <> 'CANCELLED' AND order_date < DATE '2026-06-01'")[0]
    check("Overall line fill rate before June 2026 between 0.94 and 0.98", 0.94 <= fr <= 0.98, f"({fr})")

    print("\n== CP1: Vanterra allocation squeeze / Bayview ==")
    rows = q(f"""
        SELECT customer_id, customer_name, ROUND(recent_line_fill_rate,3), ROUND(prior_line_fill_rate,3), ROUND(fill_rate_change,3),
               open_backorders_over_14d, open_high_severity_cases, exec_escalations_90d, ROUND(discretionary_value_change_pct,3), operational_risk_score, top_risk_reason, days_to_renewal
        FROM V_CUSTOMER_HEALTH WHERE days_to_renewal BETWEEN 0 AND 120 ORDER BY operational_risk_score DESC""")
    print("  Renewal window queue (next 120 days):")
    for r in rows:
        print("   ", r)
    check("8+ customers renew in the next 120 days", len(rows) >= 8, f"({len(rows)})")
    check("Bayview is #1 in the renewal queue", rows and rows[0][0] == hc.HERO_CUSTOMER)
    hero = q(f"SELECT recent_line_fill_rate, prior_line_fill_rate, open_backorders_over_14d, open_high_severity_cases, discretionary_value_change_pct, operational_risk_score FROM V_CUSTOMER_HEALTH WHERE customer_id='{hc.HERO_CUSTOMER}'")[0]
    check("Bayview fill rate fell at least 8 pts", (hero[1] - hero[0]) >= 0.08, f"(prior {hero[1]:.3f} -> recent {hero[0]:.3f})")
    check("Bayview has 3+ backorders over 14 days", hero[2] >= 3, f"({hero[2]})")
    check("Bayview has 3+ open high severity cases", hero[3] >= 3, f"({hero[3]})")
    check("Bayview risk score >= 50", hero[5] >= 50, f"({hero[5]})")
    van = q(f"""
        SELECT period_month, MAX(halcyon_total_allocation_units), SUM(customer_requested_units), SUM(customer_allocated_units), SUM(shortfall_units)
        FROM CUSTOMER_ALLOCATIONS WHERE ndc='{hc.VANTERRA_NDC}' AND period_month >= DATE '2026-03-01' GROUP BY 1 ORDER BY 1""")
    print("  Vanterra monthly: month, halcyon_total, requested, allocated, shortfall")
    for r in van:
        print("   ", r)
    may = [r for r in van if str(r[0]).startswith("2026-05")][0]
    aug = [r for r in van if str(r[0]).startswith("2026-08")][0]
    check("Vanterra Halcyon allocation cut >= 20% May -> August", (may[1] - aug[1]) / may[1] >= 0.20, f"({may[1]} -> {aug[1]})")
    bfill = q(f"""
        SELECT ROUND(AVG(CASE WHEN order_date < DATE '2026-06-01' THEN is_line_filled_complete END),3),
               ROUND(AVG(CASE WHEN order_date >= DATE '2026-06-01' THEN is_line_filled_complete END),3)
        FROM V_ORDER_LINE_DETAIL WHERE customer_id='{hc.HERO_CUSTOMER}' AND ndc='{hc.VANTERRA_NDC}'""")[0]
    check("Bayview Vanterra line fill before >= 0.93 and after <= 0.75", bfill[0] >= 0.93 and bfill[1] <= 0.75, f"({bfill})")
    leak = q(f"""
        SELECT ROUND(SUM(CASE WHEN order_date >= DATE '2026-07-27' THEN ordered_value_wac END) / SUM(CASE WHEN order_date >= DATE '2026-06-01' AND order_date < DATE '2026-07-27' THEN ordered_value_wac END) - 1, 3)
        FROM V_ORDER_LINE_DETAIL WHERE customer_id='{hc.HERO_CUSTOMER}' AND therapeutic_class <> 'GLP1_METABOLIC' AND line_status <> 'CANCELLED'""")[0][0]
    check("Bayview non-GLP-1 order value down at least 10% recent vs prior 8 weeks", leak <= -0.10, f"({leak})")
    sq = q("SELECT customer_id FROM V_CUSTOMER_HEALTH ORDER BY operational_risk_score DESC LIMIT 6")
    check("Cascade and Northgate appear in the top 6 overall risk", all(c in [x[0] for x in sq] for c in ["CUST-0007", "CUST-0003"]), f"({[x[0] for x in sq]})")

    print("\n== CP2: Memphis cold chain / GEL_PACK_STD ==")
    rows = q("""
        SELECT dc_id, ROUND(SUM(excursions)/SUM(readings),4) AS rate
        FROM V_COLD_CHAIN_EXCURSIONS WHERE event_month >= DATE '2026-07-01' AND event_month < DATE '2026-09-01' AND storage_class='REFRIGERATED_2_8C'
        GROUP BY dc_id ORDER BY rate DESC""")
    for r in rows:
        print("   ", r)
    mem = [r[1] for r in rows if r[0] == "DC-MEM"][0]
    others = max(r[1] for r in rows if r[0] != "DC-MEM")
    check("DC-MEM 2-8C excursion rate >= 3x the next DC in Jul-Aug 2026", mem >= 3 * others, f"({mem} vs {others})")
    pk = q("""
        SELECT packaging_type, ROUND(SUM(excursions)/SUM(readings),4) FROM V_COLD_CHAIN_EXCURSIONS
        WHERE dc_id='DC-MEM' AND stage='PACKOUT' AND event_month >= DATE '2026-06-01' GROUP BY 1 ORDER BY 2 DESC""")
    print("   DC-MEM packout by packaging since June:", pk)
    check("GEL_PACK_STD packout rate >= 4x PHASE_CHANGE_48H at DC-MEM", pk[0][0] == "GEL_PACK_STD" and pk[0][1] >= 4 * max(x[1] for x in pk if x[0] != "GEL_PACK_STD"))
    val = q("SELECT ROUND(SUM(value_quarantined_or_destroyed_wac)) FROM V_COLD_CHAIN_EXCURSIONS WHERE dc_id='DC-MEM' AND event_month >= DATE '2026-06-01'")[0][0]
    check("DC-MEM quarantined/destroyed value since June >= $800K", val >= 800_000, f"(${val:,.0f})")
    tr = q("SELECT COUNT(*) FROM RETURNS WHERE return_reason='TEMP_EXCURSION' AND dc_id='DC-MEM' AND return_date >= DATE '2026-06-01'")[0][0]
    check("TEMP_EXCURSION returns from DC-MEM since June >= 15", tr >= 15, f"({tr})")

    print("\n== CP3: Oncaryl short-dated at Dallas ==")
    onc = q(f"SELECT dc_id, on_hand_units, expiring_90d_units, ROUND(expiring_90d_value_wac), days_of_supply, on_order_units, is_expiry_write_off_risk FROM V_INVENTORY_RISK WHERE ndc='{hc.ONCARYL_NDC}' ORDER BY expiring_90d_value_wac DESC")
    for r in onc:
        print("   ", r)
    dal = [r for r in onc if r[0] == "DC-DAL"][0]
    check("DC-DAL Oncaryl expiring-90d value >= $1.5M and flagged write-off risk", dal[3] >= 1_500_000 and dal[6] == 1, f"(${dal[3]:,.0f})")
    check("DC-DAL Oncaryl days of supply > 90", (dal[4] or 0) > 90, f"({dal[4]})")
    hou = q(f"""SELECT customer_name, SUM(qty_ordered) FROM V_ORDER_LINE_DETAIL WHERE ndc='{hc.ONCARYL_NDC}' AND dc_id='DC-DAL' AND order_date >= DATE '2026-06-01'
                     GROUP BY 1 ORDER BY 2 DESC LIMIT 5""")
    print("   Top Oncaryl buyers at DC-DAL since June:", hou)
    check("Houston oncology practices still buying Oncaryl at DC-DAL", any("Gulfstream" in h[0] or "Bayou" in h[0] or "Lone Star" in h[0] for h in hou))

    print("\n== CP4: Keldon chargeback disputes ==")
    kd = q("""
        SELECT manufacturer_name, ROUND(SUM(disputed_or_rejected_claims)/SUM(claims),4) AS dr, ROUND(SUM(amount_disputed_or_rejected))
        FROM V_CHARGEBACK_SUMMARY WHERE submitted_month >= DATE '2026-05-01' GROUP BY 1 ORDER BY dr DESC LIMIT 5""")
    for r in kd:
        print("   ", r)
    check("Keldon has the highest dispute rate since May 2026 and it is >= 0.18", kd[0][0] == "Keldon Pharma" and kd[0][1] >= 0.18)
    base = q("SELECT ROUND(SUM(disputed_or_rejected_claims)/SUM(claims),4) FROM V_CHARGEBACK_SUMMARY WHERE manufacturer_name <> 'Keldon Pharma' AND submitted_month >= DATE '2026-05-01'")[0][0]
    check("Non-Keldon dispute rate <= 0.06", base <= 0.06, f"({base})")
    kb = q("SELECT ROUND(SUM(disputed_or_rejected_claims)/SUM(claims),4) FROM V_CHARGEBACK_SUMMARY WHERE manufacturer_name = 'Keldon Pharma' AND submitted_month < DATE '2026-04-01'")[0][0]
    check("Keldon dispute rate before April 2026 <= 0.06", kb <= 0.06, f"({kb})")
    check("Keldon disputed/rejected amount since May >= $1.2M", kd[0][2] >= 1_200_000, f"(${kd[0][2]:,.0f})")

    print("\n== CP5: Backorder aging drives HIGH severity cases ==")
    ag = q("""
        SELECT CASE WHEN b.days_open > 14 THEN 'over_14' ELSE 'under_14' END AS bucket, COUNT(*) AS cases
        FROM SERVICE_CASES c JOIN BACKORDERS b ON b.backorder_id = c.related_backorder_id
        WHERE c.severity IN ('HIGH','CRITICAL') GROUP BY 1""")
    print("   ", ag)
    d = dict(ag)
    check("Majority of HIGH/CRITICAL backorder cases come from backorders over 14 days", d.get("over_14", 0) > d.get("under_14", 0))

    print("\n== CP6: AUTO_REPLENISH outperforms ==")
    ch = q("""
        SELECT order_channel, ROUND(AVG(is_line_filled_complete),4), ROUND(AVG(CASE WHEN order_priority='STAT' THEN 1 ELSE 0 END),4)
        FROM V_ORDER_LINE_DETAIL WHERE line_status <> 'CANCELLED' GROUP BY 1 ORDER BY 2 DESC""")
    for r in ch:
        print("   ", r)
    check("AUTO_REPLENISH has the best fill rate and lowest STAT share", ch[0][0] == "AUTO_REPLENISH" and ch[0][2] == min(x[2] for x in ch))

    print("\n== Referential integrity ==")
    fk = [
        ("ORDER_LINES.order_id", "SELECT COUNT(*) FROM ORDER_LINES l LEFT JOIN ORDERS o ON o.order_id=l.order_id WHERE o.order_id IS NULL"),
        ("SHIPMENTS.order_id", "SELECT COUNT(*) FROM SHIPMENTS s LEFT JOIN ORDERS o ON o.order_id=s.order_id WHERE o.order_id IS NULL"),
        ("COLD_CHAIN_EVENTS.shipment_id", "SELECT COUNT(*) FROM COLD_CHAIN_EVENTS e LEFT JOIN SHIPMENTS s ON s.shipment_id=e.shipment_id WHERE s.shipment_id IS NULL"),
        ("BACKORDERS.order_line_id", "SELECT COUNT(*) FROM BACKORDERS b LEFT JOIN ORDER_LINES l ON l.order_line_id=b.order_line_id WHERE l.order_line_id IS NULL"),
        ("CHARGEBACKS.order_line_id", "SELECT COUNT(*) FROM CHARGEBACKS c LEFT JOIN ORDER_LINES l ON l.order_line_id=c.order_line_id WHERE l.order_line_id IS NULL"),
        ("RETURNS.order_line_id", "SELECT COUNT(*) FROM RETURNS r LEFT JOIN ORDER_LINES l ON l.order_line_id=r.order_line_id WHERE l.order_line_id IS NULL"),
        ("SERVICE_CASES.related_backorder_id", "SELECT COUNT(*) FROM SERVICE_CASES c LEFT JOIN BACKORDERS b ON b.backorder_id=c.related_backorder_id WHERE c.related_backorder_id IS NOT NULL AND b.backorder_id IS NULL"),
        ("SERVICE_CASES.related_shipment_id", "SELECT COUNT(*) FROM SERVICE_CASES c LEFT JOIN SHIPMENTS s ON s.shipment_id=c.related_shipment_id WHERE c.related_shipment_id IS NOT NULL AND s.shipment_id IS NULL"),
        ("CUSTOMER_SITES.customer_id", "SELECT COUNT(*) FROM CUSTOMER_SITES s LEFT JOIN CUSTOMERS c ON c.customer_id=s.customer_id WHERE c.customer_id IS NULL"),
        ("PRODUCTS.manufacturer_id", "SELECT COUNT(*) FROM PRODUCTS p LEFT JOIN MANUFACTURERS m ON m.manufacturer_id=p.manufacturer_id WHERE m.manufacturer_id IS NULL"),
        ("Unique customer ids", "SELECT COUNT(*) - COUNT(DISTINCT customer_id) FROM CUSTOMERS"),
        ("Unique product ndcs", "SELECT COUNT(*) - COUNT(DISTINCT ndc) FROM PRODUCTS"),
    ]
    for label, sql in fk:
        n = q(sql)[0][0]
        check(f"{label} orphan/dup count = 0", n == 0, f"({n})")
