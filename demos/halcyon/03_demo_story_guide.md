# Halcyon Specialty Distribution — Demo Story Guide

Audience: Tiger Analytics (Karthik Balakrishnan, Shobhit Sachdeva) ahead of McKesson. 45 minutes.
Persona you are playing: Director of Customer Supply Operations at Halcyon, a specialty distributor.
Frame: "This is what a distributor's operations lead sees on a Monday morning. Wisdom sits on the
operational data (orders, allocation, cold chain, inventory, chargebacks, cases) and lets the team go
from question to decision to action without waiting for a report."

Every number below comes from the generated data. Numbers marked SE only are for your back pocket.

---

## Arc 1 — Who needs attention this week (chat, 8 min)

**Q1.** *Which customers renewing in the next 120 days show the highest operational risk?*
Expected: 29 customers in the window. Top three by risk score: **Bayview Regional Health 78.6**
(35 backorders over 14 days), **Cascade Oncology Partners 65.7**, **Northgate Health Alliance 64.7**.
Everyone else is under 25. Point out `TOP_RISK_REASON` is plain language and the score is built from
four visible components, not a black box.

**Q2.** *Give me the full operational health picture for Bayview Regional Health.*
Expected: $48.2M ACV, renews 2026-12-15 (81 days), line fill 92% to 83%, 51 open backorders,
$1.76M backordered, 14 open high severity cases, 3 exec escalations in 90 days, non-allocated order
value down 18%, allocation shortfall 3,372 units in 90 days.

**Q3.** *How has Bayview's fill rate changed by therapeutic class over the last 8 weeks versus the prior 8?*
Expected: GLP1_METABOLIC 79% to 57%. Every other class is 93% to 100% and flat.
Reveal: this is not a DC problem, it is one product family.

Without Wisdom: pull a fill rate report, filter, export, pivot by class, 30 minutes.
With Wisdom: three questions, two minutes, and the root cause is already narrowing.

---

## Arc 2 — Why: the Vanterra allocation squeeze (chat, 8 min)

**Q4.** *How has the Veltrix allocation of Vanterra to Halcyon changed month by month in 2026?*
Expected: Halcyon allocation ~21.8K units in May, flat through June and July while requests climb
past 24K, then ~17.3K in August and ~14.2K in September. Shortfall grows from ~450 to ~5,200 units
a month. Say: "Veltrix held us flat all summer while demand grew, then cut us twice."

**Q5.** *Show Bayview's Vanterra requested versus allocated versus consumed by month.*
Expected: allocated ~3,250 in April, ~1,850 in September; requested 3,300 to 4,400. Utilization 100%
every month. Bayview is consuming everything it is given and asking for nearly twice as much.

**Q6.** *Which customers have the largest Vanterra allocation shortfall since August?*
Expected: Bayview, Northgate and Cascade at the top by a wide margin, then a steep drop.
Reveal: historical share allocation is protecting slow customers and starving the three fastest growing
ones, and two of them renew in the next 90 days. Follow with *Which customers are using less than 60
percent of their Vanterra allocation?* to show the donor pool: about eight customers sitting on
~1,100 unused units a month (Beacon Hill Health Network at 10% utilization is the standout).

**Q7.** *Has Bayview reduced ordering of products that are not on allocation since late July?*
Expected: non-allocated ordered value down roughly a quarter, recent 8 weeks vs prior. Allocated value flat.
Say: "They are not just short on Vanterra. They have started moving oncology and immunology volume
somewhere else. That is the early warning before a renewal conversation goes badly."

SE only: `V_CUSTOMER_HEALTH.DISCRETIONARY_VALUE_CHANGE_PCT` excludes allocated products on purpose.
If Tiger asks why total order value is flat, that is the answer, and it is a good data modeling point.

---

## Arc 3 — Decide and act: the Live App (10 min)

Open **Customer Supply Rescue Workbench** (built from `04_live_app_prompt.md`).

1. **Case Queue** opens on the 120-day renewal list, Bayview preselected. Click through the case file:
   fill rate by class, Vanterra allocation chart, aged backorders, open cases, the non-allocated
   volume drop.
2. **Scenario Lab.** Baseline: keep historical share, do nothing. Custom: move the sliders. System
   Recommended: reallocate unused Vanterra from the under-60% utilization donors (covers roughly a
   third of the shortfall), expedite the oldest backorders from another DC, renewal credit,
   executive outreach. Show the ranked action list and the assumptions panel. Select it.
3. **Implementation.** The plan is prepopulated: reallocation task for supply planning, expedite task
   for DC-ATL, commercial credit for Dana Whitfield to approve, exec call with Bayview pharmacy
   director, review date six weeks out. Approve, submit, show the action log and the mock CRM payload.

Say: "Insight, decision, action, audit trail. One surface, no handoffs."

---

## Arc 4 — Automate it: the agent (4 min)

Build or show the **Customer Supply Risk Monitor** agent (`05_agent_prompt.md`).
"Every Monday I get the renewal risk digest. Tuesday to Friday I only hear from it if something
crosses a line: a backorder passing 14 days on a strategic account, a critical excursion, or
allocation utilization above 95% on an account inside 90 days of renewal."

---

## Arc 5 — Same pattern, different problem (chat, 8 min)

Pick one or two depending on time and who is on the call.

**Cold chain (operations audience)**
- *Compare cold chain excursion rates across DCs for refrigerated product in July and August.*
  Memphis 4.2%, next highest 1.3%.
- *At which stage are Memphis excursions happening since June?* Packout.
- *Compare packout excursion rates by packaging type at Memphis since June.*
  GEL_PACK_STD 17.7% vs PHASE_CHANGE_48H 0.7%. $1.36M quarantined or destroyed, all gel pack.
- *When did Memphis start using gel pack packaging?* June 2026. Case closed in four questions.

**Chargebacks (finance audience)**
- *Which manufacturers have the highest chargeback dispute rate since May?* Keldon 24%, next 5.5%.
- *Compare Keldon's dispute rate before and after the April 2026 price file.* 3.8% to 24%.
- *What are the dispute reasons on Keldon chargebacks since the April price file?*
  PRICE_MISMATCH 310 claims ($968K), INELIGIBLE_CUSTOMER 178 ($457K), EXPIRED_CONTRACT 49.
  Say: "That is a price file reconciliation with one manufacturer, not 500 individual disputes."

**Expiry (supply chain audience)**
- *Where do we have the most inventory value expiring in the next 90 days?*
  Oncaryl at Dallas: 835 units, $2.38M, 313 days of supply, 204 more on order.
- *How has monthly Oncaryl demand from Dallas served sites changed in 2026?* ~750 a month to ~90 in May.
- *Which customers served by Dallas are still ordering Oncaryl?* Gulfstream Cancer Care, Bayou City
  Oncology Group, Lone Star Hematology Oncology Associates, all Houston.
  Say: "Short-dated sale to the Houston practices, cancel the open PO, avoid a $2M write-off."

---

## Close (2 min)

For Tiger: the build pattern is what matters. Twenty tables, nine views, a bootstrap document, fifty
reviewed queries. On McKesson's real data the same shape gets you the same workbench. Ask what the
equivalent of "Bayview" is inside McKesson today and who owns that Monday morning question.

---

## Back pocket

- **"Is the risk score predictive?"** No. It is a transparent triage score with four weighted
  components. Call it an operational risk indicator. Wisdom exposes the weights and the inputs.
- **"How do you avoid double counting across these tables?"** Each fact is aggregated to customer or
  DC grain before joining. The views do it; the bootstrap tells Wisdom to do it in ad hoc queries.
- **"What about the partial week?"** `CALENDAR.IS_COMPLETE_WEEK`; the latest complete week ends
  2026-09-20 and the bootstrap tells Wisdom to exclude the current one.
- **"Why is Bayview's total order value flat if they are leaving?"** Allocated product requests inflate
  when customers expect to be shorted. Look at non-allocated value. That is the discretionary metric.
- **"Can this write back?"** The app writes to an in-app action log with a mock payload for CRM and
  service management. Real integration is a follow-up, and the payload shape is already there.
- **Do not** claim Memphis's problem is proven to be gel packs. Say the data points there and the next
  step is a packaging validation review. Same posture for every story.
