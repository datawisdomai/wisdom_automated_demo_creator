"""Story control-point checks for the Nordmark Dagligvaror demo.

`demo validate` calls run(q, check, spec) against DuckDB before loading and against
Snowflake after. `q(sql)` returns rows; `check(label, cond, detail)` records a pass/fail.
Control points CP1..CP6 (store performance) and CP7..CP11 (campaigns and forecasts) per DEMO_PLAN.md / demo.yaml.
"""
import generator as nm


def run(q, check, spec):
    targets = {cp["id"]: {t["metric"]: (t["op"], t["value"]) for t in cp.get("targets", [])} for cp in spec.raw.get("control_points", [])}

    def hit(cp, metric, value):
        op, target = targets[cp][metric]
        ok = {">=": value >= target, "<=": value <= target, ">": value > target, "<": value < target, "==": value == target}[op]
        check(f"{cp} {metric} {op} {target}", ok, f"(actual {value:,.4f})" if isinstance(value, float) else f"(actual {value:,})")

    def one(sql):
        rows = q(sql)
        return rows[0][0] if rows and rows[0] else None

    hero, peer = nm.HERO_STORE, nm.PEER_STORE

    print("\n== Baseline health ==")
    (sales_r12,) = q("SELECT SUM(net_sales_sek) FROM STORE_DAILY_SALES d JOIN CALENDAR c ON c.calendar_date = d.calendar_date WHERE c.rolling_12m_bucket = 'R12_CUR'")[0]
    check("Group rolling-12-month net sales between SEK 15bn and 30bn", 15e9 <= sales_r12 <= 30e9, f"(SEK {sales_r12:,.0f})")
    rows = q("""SELECT banner, SUM(gross_profit_sek)/SUM(net_sales_sek) FROM V_BANNER_KPI_MONTHLY
                WHERE month_start_date >= DATE '2025-10-01' AND month_start_date <= DATE '2026-09-01' GROUP BY banner ORDER BY banner""")
    gp = {r[0]: float(r[1]) for r in rows}
    print("  R12 gross margin by banner:", {k: round(v, 4) for k, v in gp.items()})
    check("Banner gross margins within 20-33 percent", all(0.20 <= v <= 0.33 for v in gp.values()))
    rows = q("SELECT COUNT(*), SUM(CASE WHEN is_lfl_comparable THEN 1 ELSE 0 END) FROM STORES")
    print(f"  stores: {rows[0][0]} total, {rows[0][1]} like-for-like comparable")
    check("Between 230 and 260 stores and at least 200 comparable", 230 <= rows[0][0] <= 260 and rows[0][1] >= 200)
    rows = q("SELECT MIN(sales_change_pct), MAX(sales_change_pct) FROM V_STORE_GAP_DECOMPOSITION")
    check("Every comparable store rolling-12-month change within -30% .. +30%", -0.30 <= rows[0][0] and rows[0][1] <= 0.30, f"({rows[0]})")
    views = ["V_KPI_STORE_MONTHLY", "V_BANNER_KPI_MONTHLY", "V_STORE_GAP_DECOMPOSITION", "V_PEER_COMPARISON", "V_CATCHMENT_POTENTIAL", "V_PROMO_EFFECTIVENESS",
             "V_AVAILABILITY_VS_SALES", "V_LOYALTY_SEGMENT_TRENDS", "V_NONFOOD_AVAILABILITY_BY_SUPPLIER",
             "V_KAMPANJRAPPORT", "V_PROGNOSFEL_TAKTIK", "V_KAMPANJ_BUTIK_AVVIKELSE", "V_KAMPANJ_MARGINALEFFEKT", "V_KAMPANJ_KOMMANDE"]
    counts = {v: one(f"SELECT COUNT(*) FROM {v}") for v in views}
    print("  view row counts:", counts)
    check("Every view returns rows", all(c and c > 0 for c in counts.values()))

    print("\n== CP1: Grosshallen lag, transactions-led; Vasterhamn below potential ==")
    rows = q("""SELECT banner, SUM(sales_r12_sek), SUM(sales_prior_r12_sek), SUM(transactions_r12), SUM(transactions_prior_r12)
                FROM V_STORE_GAP_DECOMPOSITION GROUP BY banner ORDER BY banner""")
    agg = {r[0]: r[1:] for r in rows}
    tot = [sum(r[i] for r in agg.values()) for i in range(4)]
    group_lfl = tot[0] / tot[1] - 1
    g = agg[nm.GRH]
    grh_lfl = g[0] / g[1] - 1
    for b, r in agg.items():
        print(f"   {b:12s} LFL {r[0]/r[1]-1:+.4f}  transactions {r[2]/r[3]-1:+.4f}  basket {(r[0]/r[2])/(r[1]/r[3])-1:+.4f}")
    print(f"   group LFL {group_lfl:+.4f}")
    hit("CP1", "grosshallen_lfl_r12_pct", round(grh_lfl, 4))
    hit("CP1", "group_lfl_minus_grosshallen_pts", round(group_lfl - grh_lfl, 4))
    hit("CP1", "grosshallen_transactions_change_pct", round(g[2] / g[3] - 1, 4))
    hit("CP1", "grosshallen_basket_change_pct", round((g[0] / g[2]) / (g[1] / g[3]) - 1, 4))
    hit("CP1", "grosshallen_gp_pct_gap_vs_kronmat_pts", round(gp[nm.KRM] - gp[nm.GRH], 4))
    ebit = {r[0]: float(r[1]) for r in q(f"SELECT quarter_label, SUM(ebit_sek) FROM V_BANNER_KPI_MONTHLY WHERE banner = '{nm.GRH}' GROUP BY quarter_label ORDER BY quarter_label")}
    print("   Grosshallen EBIT by quarter (MSEK):", {k: round(v / 1e6, 1) for k, v in ebit.items()})
    hit("CP1", "grosshallen_ebit_q3_2026_sek", ebit["2026-Q3"])
    hit("CP1", "grosshallen_ebit_q3_2025_sek", ebit["2025-Q3"])
    row = q(f"SELECT potential_index, cluster_median_index, gap_rank_in_banner, potential_gap_sek, peer_cluster FROM V_CATCHMENT_POTENTIAL WHERE store_name = '{hero}'")[0]
    print(f"   {hero}: index {row[0]:.3f} cluster median {row[1]:.3f} gap rank {row[2]} gap SEK {row[3]:,.0f} ({row[4]})")
    hit("CP1", "vasterhamn_potential_index", round(float(row[0]), 4))
    hit("CP1", "vasterhamn_cluster_median_index", round(float(row[1]), 4))
    hit("CP1", "vasterhamn_is_largest_sek_gap_in_banner", 1 if int(row[2]) == 1 else 0)
    drv = one(f"SELECT growth_driver FROM V_STORE_GAP_DECOMPOSITION WHERE store_name = '{hero}'")
    check("Vasterhamn growth driver is Transactions", drv == "Transactions", f"({drv})")

    print("\n== CP2: Kronmat Fresh & Produce growth with margin erosion; Sommarpris ==")
    row = q(f"""SELECT SUM(CASE WHEN w.week_start_date >= DATE '2025-10-01' THEN w.net_sales_sek ELSE 0 END),
                       SUM(CASE WHEN w.week_start_date < DATE '2025-10-01' THEN w.net_sales_sek ELSE 0 END),
                       SUM(CASE WHEN w.week_start_date >= DATE '2025-10-01' THEN w.gross_profit_sek ELSE 0 END),
                       SUM(CASE WHEN w.week_start_date < DATE '2025-10-01' THEN w.gross_profit_sek ELSE 0 END)
                FROM SALES_WEEKLY_STORE_CATEGORY w JOIN STORES s ON s.store_id = w.store_id JOIN PRODUCT_CATEGORIES c ON c.category_id = w.category_id
                WHERE s.banner = '{nm.KRM}' AND s.is_lfl_comparable AND c.category_name = '{nm.HERO_CATEGORY}'
                  AND w.week_start_date >= DATE '2024-10-07' AND w.week_start_date <= DATE '2026-09-28'""")[0]
    growth = row[0] / row[1] - 1
    gp_change = row[2] / row[0] - row[3] / row[1]
    print(f"   Kronmat Fresh & Produce: sales growth {growth:+.4f}, GP% change {gp_change:+.4f}")
    hit("CP2", "kronmat_fresh_sales_growth_pct", round(growth, 4))
    hit("CP2", "kronmat_fresh_gp_pct_change_pts", round(gp_change, 4))
    row = q(f"SELECT uplift_rank, margin_rank_from_bottom, uplift_pct, margin_dilution_pts, promo_verdict FROM V_PROMO_EFFECTIVENESS WHERE promotion_name = '{nm.HERO_PROMOTION}'")[0]
    print(f"   {nm.HERO_PROMOTION}: uplift rank {row[0]} ({row[2]:.3f}), margin rank from bottom {row[1]} ({row[3]:.3f}) -> {row[4]}")
    hit("CP2", "sommarpris_uplift_rank", int(row[0]))
    hit("CP2", "sommarpris_margin_rank_from_bottom", int(row[1]))

    print("\n== CP3: availability vs sales ==")
    rows = q("""SELECT s.store_id, s.store_name, s.banner, SUM(v.osa_pct * v.net_sales_13w_sek) / SUM(v.net_sales_13w_sek), MAX(v.store_lfl_growth_pct)
                FROM V_AVAILABILITY_VS_SALES v JOIN STORES s ON s.store_id = v.store_id
                WHERE v.category_name IN ('Dairy', 'Bread & Bakery') AND s.is_lfl_comparable
                GROUP BY s.store_id, s.store_name, s.banner""")
    low = [r for r in rows if r[3] < 0.94]
    high = [r for r in rows if r[3] >= 0.94]
    gap = (sum(r[4] for r in high) / len(high)) - (sum(r[4] for r in low) / len(low))
    print(f"   {len(low)} stores with Dairy/Bread OSA < 94%: mean LFL {sum(r[4] for r in low)/len(low):+.4f} vs {sum(r[4] for r in high)/len(high):+.4f} for the rest")
    hit("CP3", "low_osa_lfl_gap_pts", round(gap, 4))
    hero_osa = [r for r in rows if r[1] == hero][0][3]
    worst_grh = min(r[3] for r in rows if r[2] == nm.GRH)
    hit("CP3", "vasterhamn_osa_dairy_bread_pct", round(float(hero_osa), 4))
    hit("CP3", "vasterhamn_is_worst_osa_in_banner", 1 if hero_osa <= worst_grh else 0)

    print("\n== CP4: Families and the Billigmat opening ==")
    rows = q(f"""SELECT banner, SUM(CASE WHEN segment = '{nm.HERO_SEGMENT}' THEN visits_r12 ELSE 0 END), SUM(CASE WHEN segment = '{nm.HERO_SEGMENT}' THEN visits_prior_r12 ELSE 0 END),
                       SUM(visits_r12), SUM(visits_prior_r12) FROM V_LOYALTY_SEGMENT_TRENDS GROUP BY banner ORDER BY banner""")
    fam = {r[0]: r[1] / r[2] - 1 for r in rows}
    allv = {r[0]: r[3] / r[4] - 1 for r in rows}
    print("   Families visits change by banner:", {k: round(v, 4) for k, v in fam.items()}, "| all segments:", {k: round(v, 4) for k, v in allv.items()})
    hit("CP4", "grosshallen_families_visits_change_pct", round(fam[nm.GRH], 4))
    hit("CP4", "other_banners_families_vs_total_visits_gap_pts", round(max(abs(fam[b] - allv[b]) for b in fam if b != nm.GRH), 4))
    row = q(f"SELECT e.distance_km, e.competitor_name, e.event_date FROM COMPETITOR_EVENTS e JOIN STORES s ON s.store_id = e.store_id WHERE s.store_name = '{hero}' AND e.event_type = 'Opening' ORDER BY e.event_date")[0]
    print(f"   {hero}: {row[1]} opened {row[2]} at {row[0]} km")
    hit("CP4", "vasterhamn_competitor_distance_km", float(row[0]))
    row = q(f"""SELECT SUM(CASE WHEN d.calendar_date >= DATE '2026-03-12' AND d.calendar_date <= DATE '2026-09-11' THEN d.net_sales_sek ELSE 0 END) /
                       SUM(CASE WHEN d.calendar_date >= DATE '2025-03-12' AND d.calendar_date <= DATE '2025-09-11' THEN d.net_sales_sek ELSE 0 END) - 1
                FROM STORE_DAILY_SALES d JOIN STORES s ON s.store_id = d.store_id WHERE s.store_name = '{hero}'""")[0]
    hit("CP4", "vasterhamn_sales_change_after_opening_pct", round(float(row[0]), 4))

    print("\n== CP5: Nordstaden playbook ==")
    pc = {r[0]: r[1:] for r in q(f"SELECT store_name, pl_sales_share, osa_pct, markdown_rate, gp_pct, lfl_growth_pct FROM V_PEER_COMPARISON WHERE store_name IN ('{hero}', '{peer}')")}
    print(f"   {peer}: PL {pc[peer][0]:.3f} OSA {pc[peer][1]:.3f} markdown {pc[peer][2]:.4f} GP {pc[peer][3]:.3f} LFL {pc[peer][4]:+.3f}")
    print(f"   {hero}: PL {pc[hero][0]:.3f} OSA {pc[hero][1]:.3f} markdown {pc[hero][2]:.4f} GP {pc[hero][3]:.3f} LFL {pc[hero][4]:+.3f}")
    hit("CP5", "nordstaden_pl_share_minus_vasterhamn_pts", round(float(pc[peer][0] - pc[hero][0]), 4))
    hit("CP5", "nordstaden_osa_pct", round(float(pc[peer][1]), 4))
    hit("CP5", "nordstaden_markdown_rate_ratio_vs_vasterhamn", round(float(pc[peer][2] / pc[hero][2]), 4))
    idx = one(f"SELECT potential_index FROM V_CATCHMENT_POTENTIAL WHERE store_name = '{peer}'")
    hit("CP5", "nordstaden_potential_index", round(float(idx), 4))
    same = one(f"SELECT COUNT(DISTINCT peer_cluster) FROM STORES WHERE store_name IN ('{hero}', '{peer}')")
    check("Vasterhamn and Nordstaden share a peer cluster", same == 1)

    print("\n== CP6: late import suppliers (Teradata keys) ==")
    late = nm.late_suppliers()
    print("   late suppliers from the Teradata PO summary:", late)
    hit("CP6", "late_supplier_count", len(late))
    keys = ", ".join(str(k) for k in late)
    row = q(f"""SELECT SUM(CASE WHEN supplier_key IN ({keys}) THEN lost_sales_sek ELSE 0 END) / SUM(lost_sales_sek),
                       SUM(CASE WHEN supplier_key IN ({keys}) THEN net_sales_sek ELSE 0 END) / SUM(net_sales_sek)
                FROM V_NONFOOD_AVAILABILITY_BY_SUPPLIER WHERE month_start_date >= DATE '2025-10-01'""")[0]
    print(f"   late suppliers: {row[0]:.3f} of non-food lost sales from {row[1]:.3f} of non-food sales")
    hit("CP6", "late_supplier_share_of_nonfood_lost_sales", round(float(row[0]), 4))
    osa = one(f"""SELECT SUM(osa_pct * (net_sales_sek + lost_sales_sek)) / SUM(net_sales_sek + lost_sales_sek) FROM V_NONFOOD_AVAILABILITY_BY_SUPPLIER
                  WHERE store_name = '{hero}' AND month_start_date >= DATE '2025-10-01'""")
    hit("CP6", "vasterhamn_nonfood_osa_pct", round(float(osa), 4))
    n = one("SELECT COUNT(*) FROM NONFOOD_ASSORTMENT")
    check("Non-food range has 250 SKUs keyed like Teradata", n == nm.NONFOOD_SKU_COUNT, f"({n})")

    # ------------------------------------------------------------ Revision 2: campaigns and forecasts
    print("\n== CP7: Kampanjrapport grid for Kronmat week 2026-W36 ==")
    hw = nm.HERO_CAMPAIGN_WEEK
    row = q(f"""SELECT COUNT(*), COUNT(DISTINCT taktik_typ), SUM(faktisk_sald), SUM(kopt_prognos_kedjan), SUM(sald_prognos_catboost)
                FROM V_KAMPANJRAPPORT WHERE kedja = '{nm.KRM}' AND vecka_label = '{hw}'""")[0]
    print(f"   rows {row[0]}, tactics {row[1]}, actual {row[2]:,}, chain plan {row[3]:,}, CatBoost {row[4]:,}")
    hit("CP7", "kronmat_w36_rows", int(row[0]))
    hit("CP7", "kronmat_w36_tactic_types", int(row[1]))
    uniq = one("SELECT CASE WHEN COUNT(*) = COUNT(DISTINCT nyckel) THEN 1 ELSE 0 END FROM V_KAMPANJRAPPORT")
    hit("CP7", "kronmat_w36_nyckel_unique", int(uniq))
    kb = round(float(row[3]) / float(row[2]) - 1, 4)
    hit("CP7", "kronmat_w36_kedjan_bias_pct", kb)
    hit("CP7", "kronmat_w36_kedjan_bias_pct_max", kb)
    hit("CP7", "kronmat_w36_catboost_bias_pct", round(float(row[4]) / float(row[2]) - 1, 4))
    names = [r[0] for r in q(f"SELECT DISTINCT kampanj_namn FROM V_KAMPANJRAPPORT WHERE kedja = '{nm.KRM}' AND vecka_label = '{hw}' ORDER BY kampanj_namn")]
    check(f"Hero campaign '{nm.HERO_CAMPAIGN}' runs in {hw}", nm.HERO_CAMPAIGN in names, f"({names})")

    print("\n== CP8: Multiköp perishables, worst at Vasterhamn ==")
    rows = q("""SELECT taktik_typ_kod, farskvara, SUM(kopt_prognos_kedjan), SUM(faktisk_sald), SUM(abs_fel_kedjan)
                FROM V_PROGNOSFEL_TAKTIK GROUP BY taktik_typ_kod, farskvara ORDER BY taktik_typ_kod, farskvara""")
    by_t = {}
    per_err = tot_err = 0.0
    for code, fresh, kopt, act, err in rows:
        by_t.setdefault(code, [0.0, 0.0]); by_t[code][0] += float(kopt); by_t[code][1] += float(act)
        tot_err += float(err)
        if fresh:
            per_err += float(err)
        if code == "MK" and fresh:
            mk_fresh = float(kopt) / float(act) - 1
    print("   chain-plan bias by tactic:", {k: round(v[0] / v[1] - 1, 4) for k, v in by_t.items()})
    hit("CP8", "multikop_perishable_bias_pct", round(mk_fresh, 4))
    hit("CP8", "other_tactics_max_bias_pct", round(max(v[0] / v[1] - 1 for k, v in by_t.items() if k != "MK"), 4))
    hit("CP8", "perishable_share_of_abs_error", round(per_err / tot_err, 4))
    after = one(f"""SELECT SUM(prognos_kvantitet) * 1.0 / SUM(faktisk_sald) - 1 FROM V_KAMPANJ_BUTIK_AVVIKELSE
                    WHERE store_name = '{hero}' AND vecka_start >= DATE '2026-03-16'""")
    hit("CP8", "vasterhamn_overforecast_after_opening_pct", round(float(after), 4))
    rows = q(f"""SELECT store_name, SUM(prognos_kvantitet) * 1.0 / SUM(faktisk_sald) - 1 AS dev FROM V_KAMPANJ_BUTIK_AVVIKELSE
                 WHERE banner = '{nm.GRH}' AND vecka_start >= DATE '2025-10-01' GROUP BY store_name ORDER BY dev DESC""")
    print(f"   Grosshallen stores ranked by R12 over-forecast: worst {rows[0][0]} {float(rows[0][1]):+.3f}, best {rows[-1][0]} {float(rows[-1][1]):+.3f}")
    hit("CP8", "vasterhamn_is_worst_grosshallen_store", 1 if rows[0][0] == hero else 0)
    order = [r[0] for r in rows]
    hit("CP8", "nordstaden_in_best_quartile", 1 if order.index(peer) >= len(order) - max(1, len(order) // 4) else 0)

    print("\n== CP9: margin cost of over-forecasting (illustrative cost data) ==")
    rows = q("""SELECT kedja, taktik_typ, SUM(marginaleffekt_sek), SUM(CASE WHEN farskvara THEN svinnkostnad_sek ELSE 0 END)
                FROM V_KAMPANJ_MARGINALEFFEKT WHERE quarter_label = '2026-Q3' GROUP BY kedja, taktik_typ ORDER BY SUM(marginaleffekt_sek) DESC""")
    total = sum(float(r[2]) for r in rows); waste = sum(float(r[3]) for r in rows)
    print(f"   Q3 2026 total SEK {total:,.0f}; perishable waste share {waste / total:.3f}; largest share {rows[0][0]} / {rows[0][1]} ({float(rows[0][2]) / total:.3f})")
    hit("CP9", "q3_2026_marginaleffekt_sek", round(total, 2))
    hit("CP9", "q3_2026_marginaleffekt_sek_max", round(total, 2))
    hit("CP9", "q3_2026_perishable_waste_share", round(waste / total, 4))
    hit("CP9", "kronmat_multikop_is_largest_share", 1 if (rows[0][0], rows[0][1]) == (nm.KRM, nm.HERO_TACTIC) else 0)
    lab = one("SELECT MIN(kalla) FROM V_KAMPANJ_MARGINALEFFEKT")
    check("Illustrative cost label carried into the margin view", lab == nm.COST_SOURCE_LABEL, f"({lab})")

    print("\n== CP10: upcoming campaigns flagged before delivery ==")
    rows = q("""SELECT kampanj_namn, kedja, vecka_label, SUM(CASE WHEN flagga THEN 1 ELSE 0 END), COUNT(*) FROM V_KAMPANJ_KOMMANDE
                GROUP BY kampanj_namn, kedja, vecka_label HAVING SUM(CASE WHEN flagga THEN 1 ELSE 0 END) > 0 ORDER BY vecka_label""")
    print("   flagged:", [(r[0], r[1], r[2], int(r[3]), int(r[4])) for r in rows])
    hit("CP10", "upcoming_perishable_campaigns_flagged", len(rows))
    dry = one("SELECT COUNT(*) FROM V_KAMPANJ_KOMMANDE WHERE NOT farskvara AND prognosgap_pct > 0.15")
    hit("CP10", "upcoming_dry_rows_flagged", int(dry))

    print("\n== CP11: order adjustment draft for Äpplen & Päron week 2026-W42 ==")
    row = q(f"""SELECT SUM(CASE WHEN flagga THEN 1 ELSE 0 END), SUM(foreslagen_minskning_kolli * kolli), SUM(kopt_prognos_kedjan), SUM(skyddad_marginal_sek), COUNT(*), MIN(dagar_till_leverans)
                FROM V_KAMPANJ_KOMMANDE WHERE kampanj_namn = '{nm.DRAFT_CAMPAIGN}' AND vecka_label = '{nm.DRAFT_WEEK}'""")[0]
    print(f"   {row[4]} articles, {row[5]} days to delivery, cut {row[1]:,} of {row[2]:,} units, margin protected SEK {float(row[3]):,.0f}")
    hit("CP11", "applen_paron_w42_flagged", 1 if int(row[0]) > 0 else 0)
    cut = round(float(row[1]) / float(row[2]), 4)
    hit("CP11", "applen_paron_w42_cut_pct", cut)
    hit("CP11", "applen_paron_w42_cut_pct_max", cut)
    hit("CP11", "applen_paron_w42_skyddad_marginal_sek", round(float(row[3]), 2))
