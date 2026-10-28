# Kampanjplanering – runbook, edition 2026-09

Letterhead: Nordmark Dagligvaror AB — Demand Planning
Document: DP-RB-003 Kampanjplanering runbook, edition 2026-09 (replaces 2026-03)
Owner: Head of Campaign Planning (Sofia Lindahl)
Stewards: Demand Planning Analytics (Karl Öberg), Store Analytics (Amir Rashidi), chain planners Oskar Lindgren (Kronmat), Maja Sjöberg (Torghallen), Viktor Holmgren (Grosshallen)
Classification: Internal. Applies to all three chains.

## 1. Purpose and audience

This runbook describes how the campaign planners of Kronmat, Torghallen and Grosshallen read the Kampanjrapport, explain a forecast variance and draft an order adjustment before a campaign is delivered. It is written for the chain planners, the demand-planning analysts and the AI analytics layer, which must follow the same procedures so that the same question gives the same answer whoever asks it.

The procedures are deliberately fixed. A planner who needs a different cut of the data asks for it as a separate analysis; the procedures themselves are not adapted on the fly.

## 2. Definitions

| Term | Definition |
|---|---|
| Campaign week (Vecka) | The ISO week of the first delivery day of the campaign (KAMPANJ.LEVERANS_FRAN). Key: KALENDER_VECKA_ID (YYYYWW), label VECKA_LABEL (2026-W36). |
| Såld prognos (CatBoost) | The sold-quantity forecast from the group's CatBoost demand model, per campaign week and article. |
| Köpt prognos (kedjans prognos) | The purchase forecast from the chain's own plan, entered in the chain planning tool. Planerad kvantitet is this plan rounded up to whole cases and is what was ordered. |
| Faktisk såld | Actual units sold in the campaign week, from POS. |
| Forecast error % | (forecast − actual sold) / actual sold. Positive = over-forecast. Computed for CatBoost and for the chain forecast separately. |
| Bias | For a group of rows (a tactic, a chain, a week): SUM(forecast) / SUM(actual sold) − 1. A ratio of sums, never an average of row percentages. |
| Överprognos (over-forecast quantity) | MAX(köpt prognos − faktisk såld, 0) per row, summed. The units that were bought but not sold. |
| Prognosgap | For a future campaign: köpt prognos / CatBoost − 1. The flag threshold is 15 percent on perishables. |
| Marginaleffekt | The margin cost of over-forecasting: waste on perishables (over-forecast units × purchase cost × write-off share) plus the clearance markdown on the rest. Cost data is ILLUSTRATIVE (KALLA = 'ILLUSTRATIV - finanssystem ej migrerat') because the finance system is not migrated. |
| Layer rounding | Order adjustments are expressed in whole cases (kolli) rounded down to full pallet layers (lav). Never cut below the CatBoost forecast. |

Swedish terms used in the data and in this runbook:

| Term | Meaning |
|---|---|
| Kedja | Chain (Kronmat, Torghallen, Grosshallen) |
| Vecka | Week (campaign week, ISO) |
| Kampanj | Campaign |
| Artikel | Article, i.e. product or SKU |
| Butik | Store |
| Såld prognos | Sold forecast (CatBoost) |
| Köpt prognos / Kedjans prognos | Purchase forecast, the chain's own plan |
| Nyckel | Key: week label and article id, one row in the Kampanjrapport |
| Kolli | Case, the order unit (units per case in ARTIKEL.KOLLI) |
| Pall | Pallet (cases per pallet in ARTIKEL.PALL) |
| Lav | Pallet layer (cases per layer in ARTIKEL.LAV); adjustments are rounded to whole layers |
| Kvitto | Receipt, a customer transaction |
| Färskvara | Perishable article (fresh produce, dairy, bread, meat, fish, deli) |
| Svinn | Waste, goods written off |
| Taktiktyp | Tactic type, the promotion mechanic: Prisnedsättning, Multiköp 3 för 2, Medlemspris, Halva priset, Kupong |

## 3. Data

All procedures read the campaign mart in the analytics warehouse: tables ARTIKEL, KAMPANJ, KAMPANJ_ARTIKEL_VECKA, KAMPANJ_BUTIK_VECKA, ARTIKEL_KOSTNAD_MANAD and the views V_KAMPANJRAPPORT (the report grid), V_PROGNOSFEL_TAKTIK (bias by tactic), V_KAMPANJ_BUTIK_AVVIKELSE (store drill), V_KAMPANJ_MARGINALEFFEKT (margin effect, illustrative cost) and V_KAMPANJ_KOMMANDE (upcoming campaign weeks). The MicroStrategy Kampanjrapport reads V_KAMPANJRAPPORT; the procedures below give the same numbers.

## 4. Procedure: kampanjrapport

**When to use:** The planners' Kampanjrapport: campaign performance and forecast accuracy by chain (kedja) and week (vecka), one row per campaign week and article. Use for any request for the campaign report, kampanjrapport, campaign quantities versus forecast for a chain and week, or /kampanjrapport <kedja> <vecka>. Same inputs always give the same grid.

Reproduce the MicroStrategy campaign report exactly, every time. Do not add columns, charts, filters or recommendations the user did not ask for.

### 1. Resolve the inputs
- Kedja (chain, banner): Kronmat, Torghallen or Grosshallen. Synonyms: chain, banner, kedja.
- Vecka (campaign week) as an ISO week label `YYYY-Www`. Accept "week 36", "v36", "vecka 36", "202636", "2026-W36"; a week without a year means 2026.
- Optional filters: kampanj (campaign name) and taktik (tactic type). Apply them as extra WHERE conditions, nothing else changes.
- If kedja or vecka is missing, ask one question. Never substitute another chain, week or period silently.

### 2. Data
- Use only `V_KAMPANJRAPPORT`. Filter `KEDJA = '<kedja>' AND VECKA_LABEL = '<vecka>'`. Do not join other tables.
- There is a reviewed query "Show the Kampanjrapport for Kronmat week 2026-W36 with planned quantity both forecasts actual sold and forecast error by article." Use its SQL and change only the chain and the week.
- Completed weeks have `FAKTISK_SALD`. For a future week show the forecasts and say that actual sold is not yet available; leave the error columns empty.

### 3. The grid (fixed)
Columns in this order: Vecka, Kampanj, Taktik, Nyckel, Artikel, Kategori, Färskvara, Planerad kvantitet, Såld prognos (CatBoost), Köpt prognos (kedjan), Faktisk såld, Prognosfel CatBoost %, Prognosfel kedjan %.
- One row per Nyckel (week || article). Sort by Taktik, then Kampanj, then Artikel name.
- A totals row: sums of the four quantities; the totals' error percentages are ratios of sums, (SUM(forecast) − SUM(actual)) / SUM(actual), never an average of row percentages.
- Quantities in units with thousands separators; percentages with one decimal.

### 4. Under the grid
Bias by tactic type for the same chain and week from `V_PROGNOSFEL_TAKTIK` (bias = SUM(forecast) / SUM(actual) − 1), sorted by Köpt prognos bias descending.

### 5. Definitions (never change them)
- Forecast error % = (forecast − actual sold) / actual sold. Positive means over-forecast.
- Såld prognos = the group's CatBoost demand model. Köpt prognos = the chain's own purchase plan (kedjans prognos).
- Campaign week = the ISO week of the first delivery day (leverans_fran).
- Quantities are units, not SEK.

### 6. Narrative
At most three sentences: total actual sold versus both forecasts, the tactic with the largest bias, the number of articles. No causes and no recommendations here; for "why", the prognosavvikelse skill applies.

## 5. Procedure: prognosavvikelse

**When to use:** Explain why campaign forecast error or forecast bias is high for a chain, tactic type, campaign, article, store or week, and what drove it. Use for 'why is forecast error highest', 'what drove the over-forecast', 'prognosavvikelse', 'which stores or articles missed the forecast', or any variance question about the Kampanjrapport.

Decision-ready explanation of a forecast variance, in the same order every time. Aggregate before detail; one query per step.

### 1. Scope
- Take kedja, vecka or period, taktik and kampanj from the question. Default period: the last 13 completed campaign weeks up to 2026-W39 (the as-of date is 2026-09-30).
- The measure is the chain purchase forecast (Köpt prognos, kedjan) unless the user names CatBoost. Bias = (SUM(forecast) − SUM(actual sold)) / SUM(actual sold); positive = over-forecast. Never average row percentages.

### 2. Drill in this fixed order
1. Tactic type: `V_PROGNOSFEL_TAKTIK` grouped by TAKTIK_TYP (sum the columns, then compute the bias).
2. Perishability: the same view split by FARSKVARA. Report the share of the absolute error (ABS_FEL_KEDJAN) that perishables carry.
3. Article: `V_KAMPANJRAPPORT`, top 10 articles by OVERPROGNOS_KVANTITET and the top 10 by PROGNOSFEL_KEDJAN_PCT with at least 500 units actually sold.
4. Store: `V_KAMPANJ_BUTIK_AVVIKELSE`, stores ranked by (SUM(PROGNOS_KVANTITET) − SUM(FAKTISK_SALD)) / SUM(FAKTISK_SALD), with the median of the store's PEER_CLUSTER beside it and HAR_KONKURRENTHANDELSE_90D shown.
5. Week: the bias trend by VECKA_LABEL for the scope.

### 3. Causes to check (only these, in this order)
- Competitor events near the worst stores: HAR_KONKURRENTHANDELSE_90D and the rows in `COMPETITOR_EVENTS` within 2 km (event, date, distance).
- Availability: Dairy and Bread & Bakery on-shelf availability for the worst stores from `V_AVAILABILITY_VS_SALES` against the 94 percent threshold.
- Loyalty: segment visit changes for the worst stores from `V_LOYALTY_SEGMENT_TRENDS`, Families first.
Report evidence that is absent as absent. Do not invent a cause.

### 4. Reconcile
The over-forecast units of the drivers you name must add up to at most the total over-forecast of the scope. State the share each driver explains. Separate an arithmetic contribution from a cause: write "coincides with", not "caused by", unless the user has evidence.

### 5. Output (always this shape)
- One sentence conclusion with the bias of the scope.
- Up to three quantified drivers, each with its share of the over-forecast and its evidence strength (strong, moderate, weak).
- The store or article that stands out, with the peer comparison.
- The next question to ask.
If the user asks what it cost, use `V_KAMPANJ_MARGINALEFFEKT` and always carry the label in KALLA: the cost data is illustrative because the finance system has not been migrated.

## 6. Procedure: orderjustering-utkast

**When to use:** Draft an order adjustment or a planner summary for an upcoming campaign whose chain purchase forecast exceeds the CatBoost sold forecast. Use for 'draft the order adjustment', 'summarise for the planner', 'orderjustering', 'what should we cut before delivery'. Produces a governed draft for approval; never an order.

A draft for a human to approve. Nothing is written anywhere and nothing is sent until the approver says so.

### 1. Scope
- The campaign name and/or week from the question. Use only `V_KAMPANJ_KOMMANDE` (campaign weeks after the as-of date 2026-09-30, with both forecasts and no actuals yet).
- If the campaign is not in that view it has already been delivered: say so and stop. Do not draft adjustments for completed weeks.

### 2. The rule (never change it)
- Propose a cut only for rows where FLAGGA is TRUE (perishable article and PROGNOSGAP_PCT above 15 percent).
- The cut is FORESLAGEN_MINSKNING_KOLLI: whole cases (kolli) rounded down to full pallet layers (lav). Units cut = cases × KOLLI. Never cut below the CatBoost forecast.
- Dry articles and rows under the threshold are listed under "Monitor" with no cut.

### 3. Margin protected
SKYDDAD_MARGINAL_SEK, summed per campaign, always printed with the label from KALLA: "illustrative cost data, finance system not migrated". Do not present it as a booked saving.

### 4. Output (the same layout every time)
1. Header: Kampanj, Kedja, Vecka, Leverans från, days to delivery (DAGAR_TILL_LEVERANS).
2. Table, one row per flagged article, sorted by SKYDDAD_MARGINAL_SEK descending: Artikel, Kategori, Kolli (units per case), Köpt prognos, Såld prognos CatBoost, Gap %, Föreslagen minskning (kolli), Units cut, Skyddad marginal SEK.
3. Totals row and the cut as a percentage of the chain purchase forecast for the flagged rows.
4. "Monitor" list: the remaining articles with their gap.
5. Planner summary, at most five sentences, in plain language: what is over-forecast, by how much, what the draft changes, what it protects, what happens if nothing is done (waste on perishables).
6. Approval block:
   - Requested by: the user asking
   - Data used: V_KAMPANJ_KOMMANDE, ARTIKEL_KOSTNAD_MANAD (illustrative), as of 2026-09-30
   - Proposed by: Wisdom, with the rule above
   - Approver: the campaign planner in KAMPANJ.ANSVARIG_PLANERARE for this campaign
   - Status: DRAFT, awaiting approval
7. One closing line: the approved draft is a hand-off to the order system; no external system is connected and nothing has been sent.

## 7. Approval rule

- A draft is never an order. Nothing produced by procedure 6 is sent to the order system until the responsible planner has approved it.
- The approver is the planner named in KAMPANJ.ANSVARIG_PLANERARE for the campaign. A draft for another planner's campaign is forwarded, not approved.
- Every draft carries the audit fields: requested by, data used (views and the as-of date), proposed by (analyst or the analytics layer, with the rule applied), approver, status (DRAFT awaiting approval, APPROVED, REJECTED), timestamp.
- Approved drafts are entered in the chain planning tool by the planner. No system writes orders automatically.

## 8. Weekly cadence

- Monday 06:00: campaign mart loaded, the Kampanjrapport is distributed per chain.
- Monday 07:00: the planners review V_KAMPANJ_KOMMANDE for campaigns delivering in the next two weeks. Every perishable article where the chain forecast exceeds the CatBoost forecast by more than 15 percent is flagged; a draft adjustment (procedure 6) is produced for each flagged campaign.
- Tuesday: post-campaign review of last week's grid (procedure 4) and, for any tactic with a bias above 15 percent, a variance explanation (procedure 5).
- Monthly: the margin effect of over-forecasting is reported to the Head of Campaign Planning with the illustrative label until finance is migrated.

## 9. Appendix: known results, September 2026

These results were confirmed by Demand Planning Analytics against the warehouse as of 2026-09-30 and are reused in planning reviews.

- Kronmat week 2026-W36 (Höstskörd): 28 article rows in four campaigns, one per tactic type (Höstskörd Veckans pris, Höstskörd 3 för 2, Höstskörd Medlemspris, Höstskörd Halva priset). Actual sold 615,385 units. Chain purchase forecast 726,153 units, an over-forecast of 18.0 percent. CatBoost 652,308 units, an over-forecast of 6.0 percent.
- Over the last 13 completed campaign weeks the chain forecast's bias on Multiköp 3 för 2 campaigns for perishables was +31.1 percent. No other tactic type exceeded +8.4 percent. Perishables carried 87.1 percent of the absolute forecast error.
- Grosshallen Västerhamn is the Grosshallen store with the largest forecast deviation over the rolling 12 months (+36.8 percent). After the Billigmat discount store opened 1.1 km away on 2026-03-12 its campaign over-forecast rose to +53.3 percent. Grosshallen Nordstaden, in the same peer cluster, is in the best quartile.
- The margin effect of over-forecasting in 2026-Q3 was SEK 10.84 million on the illustrative cost data (KALLA = 'ILLUSTRATIV - finanssystem ej migrerat'). 79.2 percent of it was waste on perishables. The single largest share was Kronmat's Multiköp 3 för 2 campaigns, 31.8 percent.
- Upcoming campaigns flagged on 2026-09-30 (chain forecast more than 15 percent above CatBoost on perishables): Mejerivecka 3 för 2 (Kronmat, 2026-W41), Äpplen & Päron (Torghallen, 2026-W42), Brödfest 3 för 2 (Grosshallen, 2026-W43), Köttvecka 3 för 2 (Kronmat, 2026-W44). No dry-grocery article exceeded the threshold.
- Draft adjustment for Äpplen & Päron (Torghallen, 2026-W42, delivery 2026-10-12, 12 days after the as-of date, 20 fruit articles, planner Viktor Holmgren): proposed cut 45,183 of 262,743 units in the chain forecast, 17.25 percent, in whole layers; margin protected SEK 637,078 on the illustrative cost data. Status DRAFT, awaiting approval.
