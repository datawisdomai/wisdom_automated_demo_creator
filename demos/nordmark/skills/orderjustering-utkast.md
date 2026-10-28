---
name: orderjustering-utkast
description: "Draft an order adjustment or a planner summary for an upcoming campaign whose chain purchase forecast exceeds the CatBoost sold forecast. Use for 'draft the order adjustment', 'summarise for the planner', 'orderjustering', 'what should we cut before delivery'. Produces a governed draft for approval; never an order."
---

# Orderjustering, utkast (order adjustment draft)

A draft for a human to approve. Nothing is written anywhere and nothing is sent until the approver says so.

## 1. Scope
- The campaign name and/or week from the question. Use only `V_KAMPANJ_KOMMANDE` (campaign weeks after the as-of date 2026-09-30, with both forecasts and no actuals yet).
- If the campaign is not in that view it has already been delivered: say so and stop. Do not draft adjustments for completed weeks.

## 2. The rule (never change it)
- Propose a cut only for rows where FLAGGA is TRUE (perishable article and PROGNOSGAP_PCT above 15 percent).
- The cut is FORESLAGEN_MINSKNING_KOLLI: whole cases (kolli) rounded down to full pallet layers (lav). Units cut = cases × KOLLI. Never cut below the CatBoost forecast.
- Dry articles and rows under the threshold are listed under "Monitor" with no cut.

## 3. Margin protected
SKYDDAD_MARGINAL_SEK, summed per campaign, always printed with the label from KALLA: "illustrative cost data, finance system not migrated". Do not present it as a booked saving.

## 4. Output (the same layout every time)
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
