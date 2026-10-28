---
name: kampanjrapport
description: "The planners' Kampanjrapport: campaign performance and forecast accuracy by chain (kedja) and week (vecka), one row per campaign week and article. Use for any request for the campaign report, kampanjrapport, campaign quantities versus forecast for a chain and week, or /kampanjrapport <kedja> <vecka>. Same inputs always give the same grid."
---

# Kampanjrapport

Reproduce the MicroStrategy campaign report exactly, every time. Do not add columns, charts, filters or recommendations the user did not ask for.

## 1. Resolve the inputs
- Kedja (chain, banner): Kronmat, Torghallen or Grosshallen. Synonyms: chain, banner, kedja.
- Vecka (campaign week) as an ISO week label `YYYY-Www`. Accept "week 36", "v36", "vecka 36", "202636", "2026-W36"; a week without a year means 2026.
- Optional filters: kampanj (campaign name) and taktik (tactic type). Apply them as extra WHERE conditions, nothing else changes.
- If kedja or vecka is missing, ask one question. Never substitute another chain, week or period silently.

## 2. Data
- Use only `V_KAMPANJRAPPORT`. Filter `KEDJA = '<kedja>' AND VECKA_LABEL = '<vecka>'`. Do not join other tables.
- There is a reviewed query "Show the Kampanjrapport for Kronmat week 2026-W36 with planned quantity both forecasts actual sold and forecast error by article." Use its SQL and change only the chain and the week.
- Completed weeks have `FAKTISK_SALD`. For a future week show the forecasts and say that actual sold is not yet available; leave the error columns empty.

## 3. The grid (fixed)
Columns in this order: Vecka, Kampanj, Taktik, Nyckel, Artikel, Kategori, Färskvara, Planerad kvantitet, Såld prognos (CatBoost), Köpt prognos (kedjan), Faktisk såld, Prognosfel CatBoost %, Prognosfel kedjan %.
- One row per Nyckel (week || article). Sort by Taktik, then Kampanj, then Artikel name.
- A totals row, rendered the same way every time: Vecka keeps the week label; Kampanj, Taktik, Nyckel, Artikel and Kategori show the word `Totalt`; Färskvara is empty; the four quantities are sums; the totals' error percentages are ratios of sums, (SUM(forecast) − SUM(actual)) / SUM(actual), never an average of row percentages. Do not invent other labels such as a combined week-and-total text.
- Quantities in units with thousands separators; percentages with one decimal.

## 4. Under the grid
Bias by tactic type for the same chain and week from `V_PROGNOSFEL_TAKTIK` (bias = SUM(forecast) / SUM(actual) − 1), sorted by Köpt prognos bias descending.

## 5. Definitions (never change them)
- Forecast error % = (forecast − actual sold) / actual sold. Positive means over-forecast.
- Såld prognos = the group's CatBoost demand model. Köpt prognos = the chain's own purchase plan (kedjans prognos).
- Campaign week = the ISO week of the campaign's first delivery day, which is the column KAMPANJ.LEVERANS_FRAN (not a column of the report view).
- Quantities are units, not SEK.

## 6. Narrative
Answer in the language of the question; a bare `/kampanjrapport <kedja> <vecka>` invocation gets an English narrative with the Swedish column labels above. At most three sentences: total actual sold versus both forecasts, the tactic with the largest bias, the number of articles. No causes and no recommendations here; for "why", the prognosavvikelse skill applies.
