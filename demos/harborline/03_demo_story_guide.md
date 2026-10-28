# Harborline Private Capital — story guide (expected answers)

As-of 2026-10-15; latest quarter 2026-06-30. Numbers below come from `demo validate` and the DuckDB facts sheet; use them to judge chat answers.

## Beat 1 — Natural language to a configured portal view (the centerpiece)
Prompt: "Build me a custom index of North American buyout funds, vintages 2015-2020, and compare quarterly IRR to the broad PE benchmark."
- 49 funds. Median IRR 15.9% at 2026-06-30 vs 13.3% for HPCI-BROAD-PE (all vintages): +2.6 pts. Pooled TVPI 1.58 vs 1.54. Pooled DPI 1.13.
- By vintage (HPCI-BUYOUT-NA pooled IRR): 2015 16.0, 2016 9.2, 2017 14.1, 2018 14.6, 2019 15.1, 2020 18.6.
Refinement "now split by fund size": MID_MARKET 21 funds median 16.3%; MEGA 12 funds 13.1%; SMALL 16 funds 17.7%. Mid-market beats mega by 3.3 pts; the published index is capital weighted so mega funds drag HPCI-BUYOUT-NA to 13.4.
Refinement "add a cash-flow pacing view": calls front-loaded in years 1–5; distributions start around year 3; the cohort turns cash-flow positive around year 5–6; 2021–2022 vintages at the same age show a much lower DPI (about 0.16 at 16 quarters vs 0.55–0.60 for 2014–2016).

## Beat 2 — Subscription lines and the quarterly report (extraction)
- "Do funds with a subscription line show higher IRR early?" → 2019–2022 vintages at 8 quarters: 7.4% with a line vs 2.3% without (gap ≈ 5 pts); at 4 quarters 2.9 vs −4.3. Mature 2014–2017 vintages: gap under 1.5 pts at the latest quarter.
- "What does the Calder Ridge IV Q2 2026 report say about its subscription line and does it match the NAV we hold?" → facility 400.0, balance 210.0 (232.0 at 31 March), 8.0% of NAV; report NAV 2,614.0 = published NAV 2,614.0; calls 64.0 (40.0 on 14 April and 24.0 on 2 June); distribution 96.0 on 20 May; extraction confidence 0.97, auto-accepted, MATCHES_PUBLISHED true. IRR 18.4%, TVPI 1.31, DPI 0.40.
- Extraction queue: 711 extractions; 647 auto-accepted, 47 analyst review, 17 corrected.

## Beat 3 — Governance (the "why not ChatGPT" objection)
- Ask for "the IRR of the broad PE index": answer must cite the certified definition (capital-weighted since-inception IRR; POOLED_IRR_PCT) and the index name; 13.3% at 2026-06-30, 260 constituents.
- Ask "which allocators lag their benchmarks" → Westbrook is the one with a negative vintage; every other allocator at or above.

## Follow-up question (chat, pre-answered)
"Compare Westbrook State Retirement System's commitments by vintage year to the matching Harborline benchmarks and tell me which vintage lags the most and which funds explain the gap"
Expected: 2018 is the only vintage below benchmark: portfolio IRR 8.5% vs 12.0% (gap −3.5 pts) on 8 funds / 760M committed. Bramblewood Ventures III (IRR −3.5%, 15.7 pts below HPCI-VENTURE-NA 2018 at 12.2%) and Sable Point Ventures II (0.1%, 12.2 pts below) explain it; the other six 2018 funds (including Calder Ridge IV at +3.8) are at or above. Other vintages: all gaps ≥ +0.4 (2013 +7.7, 2016 +6.8, 2020 +7.9).

## Agent (draft, never run)
"Subscription Line Watch": quarterly; funds with a line balance above 15% of NAV (5 at 2026-06-30) and vintage/strategy cohorts under four years old where the line IRR gap exceeds 3 pts.
