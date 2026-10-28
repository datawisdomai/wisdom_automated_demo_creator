---
name: prognosavvikelse
description: "Explain why campaign forecast error or forecast bias is high for a chain, tactic type, campaign, article, store or week, and what drove it. Use for 'why is forecast error highest', 'what drove the over-forecast', 'prognosavvikelse', 'which stores or articles missed the forecast', or any variance question about the Kampanjrapport."
---

# Prognosavvikelse (forecast variance explanation)

Decision-ready explanation of a forecast variance, in the same order every time. Aggregate before detail; one query per step.

## 1. Scope
- Take kedja, vecka or period, taktik and kampanj from the question. Default period: the last 13 completed campaign weeks up to 2026-W39 (the as-of date is 2026-09-30).
- The measure is the chain purchase forecast (Köpt prognos, kedjan) unless the user names CatBoost. Bias = (SUM(forecast) − SUM(actual sold)) / SUM(actual sold); positive = over-forecast. Never average row percentages.

## 2. Drill in this fixed order
1. Tactic type: `V_PROGNOSFEL_TAKTIK` grouped by TAKTIK_TYP (sum the columns, then compute the bias).
2. Perishability: the same view split by FARSKVARA. Report the share of the absolute error (ABS_FEL_KEDJAN) that perishables carry.
3. Article: `V_KAMPANJRAPPORT`, top 10 articles by OVERPROGNOS_KVANTITET and the top 10 by PROGNOSFEL_KEDJAN_PCT with at least 500 units actually sold.
4. Store: `V_KAMPANJ_BUTIK_AVVIKELSE`, stores ranked by (SUM(PROGNOS_KVANTITET) − SUM(FAKTISK_SALD)) / SUM(FAKTISK_SALD), with the median of the store's PEER_CLUSTER beside it and HAR_KONKURRENTHANDELSE_90D shown.
5. Week: the bias trend by VECKA_LABEL for the scope.

## 3. Causes to check (only these, in this order)
- Competitor events near the worst stores: HAR_KONKURRENTHANDELSE_90D and the rows in `COMPETITOR_EVENTS` within 2 km (event, date, distance).
- Availability: Dairy and Bread & Bakery on-shelf availability for the worst stores from `V_AVAILABILITY_VS_SALES` against the 94 percent threshold.
- Loyalty: segment visit changes for the worst stores from `V_LOYALTY_SEGMENT_TRENDS`, Families first.
Report evidence that is absent as absent. Do not invent a cause.

## 4. Reconcile
The over-forecast units of the drivers you name must add up to at most the total over-forecast of the scope. State the share each driver explains. Separate an arithmetic contribution from a cause: write "coincides with", not "caused by", unless the user has evidence.

## 5. Output (always this shape)
- One sentence conclusion with the bias of the scope.
- Up to three quantified drivers, each with its share of the over-forecast and its evidence strength (strong, moderate, weak).
- The store or article that stands out, with the peer comparison.
- The next question to ask.
If the user asks what it cost, use `V_KAMPANJ_MARGINALEFFEKT` and always carry the label in KALLA: the cost data is illustrative because the finance system has not been migrated.
