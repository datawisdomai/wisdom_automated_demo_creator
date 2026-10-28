# Nordmark Dagligvaror — Demo Story Guide

Audience: Axfood (via the Teradata account team). Persona on stage: Head of Store Operations with the FP&A analytics team.
As-of 2026-09-30. Nothing names Axfood or its banners; the shape of the story mirrors their Q3 2026 situation
(growth on volume under deflation, a strong neighbourhood banner, a discount banner slightly behind the market, an
acquired hypermarket banner that has just reached break-even but still loses customer visits).

## The three levels (Ali's structure) and the flow

**Level 1 — key KPIs.** Sales and like-for-like growth, gross profit and margin percent, transactions and basket, sales by
store/banner/category, availability and stockouts, waste and markdowns, active members and visit frequency. Filterable by
store, region, category and period. Views: V_BANNER_KPI_MONTHLY, V_KPI_STORE_MONTHLY.

**Level 2 — what is driving performance.** Which stores grow or decline and whether it is transactions or basket
(V_STORE_GAP_DECOMPOSITION); which categories explain the change and where sales grow but margins erode
(SALES_WEEKLY_STORE_CATEGORY, V_PROMO_EFFECTIVENESS); how a store compares with similar stores (V_PEER_COMPARISON); where
availability lines up with weak sales (V_AVAILABILITY_VS_SALES); which segments visit less (V_LOYALTY_SEGMENT_TRENDS).

**Level 3 — where is the opportunity and what should we do.** Stores below their neighbourhood potential
(V_CATCHMENT_POTENTIAL); formats by neighbourhood type; why one store outperforms another with a similar catchment;
assortment, availability, pricing, promotions, retention or competition as the cause; what the peer store does; the action
with the biggest estimated upside and how to measure it.

**Flow on stage:** KPI summary → pick Grosshallen Västerhamn (largest SEK gap in the banner, index 0.62 vs cluster 0.92)
→ break the gap down (transactions −11%, basket +4%) → compare with peers and catchment (Nordstaden 0.97) → investigate
causes (Dairy/Bread OSA 89%, Billigmat opened 1.1 km away on 2026-03-12, Families visits −23%, late import suppliers) →
recommend the Nordstaden playbook as a 12-week test with about SEK 40 m upside.

## Opening questions (chat, in order)

1. "How did each banner perform over the last 12 months on sales like-for-like growth margin and transactions?"
2. "Which Grosshallen store has the largest gap to its catchment potential and is the gap transactions or basket?"
3. "Why is Grosshallen Västerhamn underperforming its catchment potential and are late inbound purchase orders from the
   import suppliers part of its non-food availability problem?" (the federation beat: Snowflake + Teradata)

## Numbers to remember

| Fact | Value |
|---|---|
| Group R12 net sales / margin | SEK 20.3 bn / 26.7 % |
| LFL R12: Kronmat / Torghallen / Grosshallen / group | +2.0 % / +4.8 % / −1.4 % / +1.3 % |
| Grosshallen transactions / basket R12 | −5.6 % / +4.4 % |
| Grosshallen EBIT Q3 2025 → Q3 2026 | about −SEK 35 m → +SEK 9 m |
| Västerhamn R12 sales / potential / index / gap | SEK 161 m / 259 m / 0.62 / 99 m (rank 1) |
| Västerhamn transactions / basket | −11 % / +4 % |
| Västerhamn Dairy & Bread OSA (13 w) | 89 % (worst in banner; target 96 %) |
| Billigmat opening | 2026-03-12, 1.1 km; sales −9.5 % in the six months after |
| Families visits: Grosshallen / Västerhamn | −17 % / −23 % |
| Nordstaden: index / LFL / PL share / OSA / markdown vs Västerhamn | 0.97 / +3.5 % / 21 % vs 14 % / 98 % / −40 % |
| Sommarpris 2026 | uplift 52 % (rank 1), dilution 7.5 pts (rank 1 from bottom) |
| Late import suppliers (Teradata keys) | Sterling Trading 39, Frontier Trading 26, Lakeshore Industries 52 |
| Their share of Grosshallen non-food lost sales | 68 % (SEK 22 m of 32 m) from 29 % of sales |

## Federation beat (what to say)

The store mart is in Snowflake. The import-purchasing platform came with the Grosshallen acquisition and still runs on
Teradata; it is attached to the same domain read-only (connection Ali-TD). The third question makes Wisdom query both:
lost sales by supplier key from Snowflake, supplier names and purchase-order lateness from Teradata, joined on the key in
the analysis step. No data was moved.

---

# Revision 2 (2026-10-27): the Kampanjrapport — five moves and the build half

Audience: Axfood IT and data leadership (platform managers, architects, BI development managers, C-1) with the Teradata
account team; 30–45 minutes. Persona on stage: Head of Campaign Planning (Sofia Lindahl), then the data steward. The Store
Performance Cockpit (revision 1) stays as the second act and as the store drill in move 2.

## The five moves (Pär's brief §6)

| # | Move | What we show | Proof in the data |
|---|---|---|---|
| 1 | Recreate | Live App "Kampanjrapport", page *Rapporten*, Kronmat 2026-W36; then `/kampanjrapport Kronmat 2026-W36` in chat: the skill loads and the same grid comes back | 28 rows, 4 campaigns (Höstskörd Veckans pris / 3 för 2 / Medlemspris / Halva priset); actual 615,385 units; chain plan +18.0 %, CatBoost +6.0 % |
| 2 | Explain | Chat: "Why is forecast error highest on Multiköp 3 för 2 campaigns over the last 13 campaign weeks …" (skill prognosavvikelse): tactic → perishability → article → store → week | Multiköp perishables +31.1 % vs ≤ +8.4 % other tactics; perishables 87.1 % of the absolute error; Grosshallen Västerhamn worst store (+36.8 % R12, +53.3 % after the Billigmat opening); Nordstaden best quartile |
| 3 | Cross to cost | Same answer continues: V_KAMPANJ_MARGINALEFFEKT, every figure with the KALLA label | Q3 2026 SEK 10.84 m; 79.2 % perishable waste; Kronmat Multiköp 31.8 % the largest share; "illustrative, finance not migrated" |
| 4 | Watch | Agent "Kampanjprognos-vakt" (draft): Mondays 07:00, V_KAMPANJ_KOMMANDE, perishables with chain forecast > CatBoost + 15 % | 4 flagged: Mejerivecka 3 för 2 (Kronmat W41), Äpplen & Päron (Torghallen W42), Brödfest 3 för 2 (Grosshallen W43), Köttvecka 3 för 2 (Kronmat W44); no dry campaign above the threshold |
| 5 | Act and govern | Live App page *Orderjustering* or `/orderjustering-utkast Äpplen & Päron 2026-W42`: draft in whole layers, approver, audit block, nothing sent | Äpplen & Päron: delivery 2026-10-12, 20 articles, cut 45,183 of 262,743 units (17.25 %), margin protected SEK 637,078 (illustrative), approver Viktor Holmgren |

## The build half (for the IT room)

Domain → tables (Snowflake + the Ali-TD Teradata tables) → Context Builder: the sources are a query-log export shaped like
Teradata DBQL (`nordmark_dbql_export_2026-05.sql`: 41 business statements in MicroStrategy shape, 33 noise), the MicroStrategy
report definition export (`kampanjrapport_report_definition.txt`), the planners' runbook (`campaign_planning_runbook.pdf`,
the source of the three skills), plus the glossary, metric standard and wiki → the suggestion report (reviewed queries,
knowledge, synonyms, skills; descriptions left pending for the steward) → Skills tab (kampanjrapport, prognosavvikelse,
orderjustering-utkast, versioned) → Evals: the eval set runs three times; the `/kampanjrapport` prompt is the determinism
proof → Domain Health. Talk track: direct DBQL extraction is "file today, connection in the POC"; POC frame 8 one-hour
sessions; Cisco built a domain in two weeks for 200 users.

## Definitions to say out loud (brief §7, in the semantic layer, not in prompts)
Forecast error = (forecast − actual sold) / actual sold, positive = over-forecast, totals as ratios of sums. Campaign week =
ISO week of the first delivery day. Tactic type = the promotion mechanic (PN, MK, MP, HP, KU). Cost = the illustrative
ARTIKEL_KOSTNAD_MANAD extract, always labelled.

## Opening questions (chat, in order)
1. `/kampanjrapport Kronmat 2026-W36`
2. "Why is forecast error highest on Multiköp 3 för 2 campaigns over the last 13 campaign weeks and what did the over-forecast cost us in margin in Q3 2026?"
3. "Which campaigns in the coming weeks are flagged because the chain forecast exceeds CatBoost by more than 15 percent on perishables?"
4. `/orderjustering-utkast Äpplen & Päron 2026-W42`
