# Live App prompt — Customer Supply Rescue Workbench

Paste into Wisdom on the Halcyon Specialty Distribution domain.

```
Create a live app called "Customer Supply Rescue Workbench" for Halcyon Specialty Distribution, a specialty pharmaceutical distributor. It is an operational tool for the Director of Customer Supply Operations, not a dashboard. Every page should answer "which customers need intervention and what do we do about it." Use three connected pages.

DATA RULES
Use V_CUSTOMER_HEALTH as the queue source. Use V_ORDER_LINE_DETAIL, V_FILL_RATE_CUSTOMER_MONTH, V_ALLOCATION_UTILIZATION, V_BACKORDER_AGING, SERVICE_CASES, COLD_CHAIN_EVENTS and CUSTOMERS for the case file. Aggregate each source to customer level before combining; never join the fact tables as raw rows.
Anchor "today" to 2026-09-25. The latest complete week ends 2026-09-20; exclude the partial week from any trend.
Describe every risk figure as an operational risk indicator, never as a churn prediction.

PAGE 1: CASE QUEUE
Open directly on a ranked list of active customers renewing in the next 120 days, one row per customer, sorted by OPERATIONAL_RISK_SCORE descending.
Show only: customer name, tier, annual contract value, renewal date, risk score, and TOP_RISK_REASON. Add a toggle to widen the list to all customers.
Include a compact "How risk is scored" disclosure: 35 points fill rate deterioration, 25 backorder aging, 25 service cases and escalations, 15 discretionary (non-allocated) volume decline, with the underlying values for the selected row.
Preselect the highest risk customer in the window (Bayview Regional Health) so the demo starts there.
Clicking a row opens a case file with: fill rate by therapeutic class recent 8 weeks vs prior 8 weeks; monthly line fill for allocated vs non-allocated products; for any allocated product the customer buys, requested vs allocated vs consumed units by month; open backorders with age and value; open service cases with severity and exec escalation flag; weekly non-allocated ordered value since June; cold chain excursions in the last 90 days. Show renewal date, days to renewal, ACV, account manager and serving DC in the header.

PAGE 2: SCENARIO LAB
For the selected customer show three scenarios side by side: Baseline, Custom, and System Recommended.
Baseline is the current state with no intervention: keep historical share allocation, no expedite, no credit.
Custom has five controls: Vanterra reallocation to this customer (units per month, taken from customers whose utilization is below 60 percent), expedite budget for aged backorders (dollars), renewal credit (percent of ACV, 0 to 6), account team hours, and executive outreach (on or off).
System Recommended allocates the budget and hours with a simple transparent greedy approach: build candidate actions (reallocate allocation units, expedite each backorder over 14 days from another DC, renewal credit in 1 percent steps, executive outreach), estimate retained contract value per dollar from the editable assumptions, rank descending, and select until budget or hours run out. Show the ranked candidate list with selected state, value per dollar, cost, hours, and a plain language reason.
Assumptions panel, editable, clearly labeled as assumptions: retention likelihood +4 points per 10 percent fill rate recovery, +3 points per aged backorder cleared, +1.5 points per 1 percent renewal credit, +2 points for executive outreach; expedite cost $1,800 and 3 hours per backorder; reallocation cost $0 but 2 hours per 500 units of coordination; executive outreach 6 hours. Baseline retention likelihood equals max(20 percent, 100 minus risk score). Cap at 95 percent.
Compare all three on: contract value at risk (ACV times risk score / 100), expected retained value (ACV times retention likelihood), projected fill rate, aged backorders remaining, allocation shortfall remaining, intervention cost, net value (retained minus cost), and confidence (High, Medium, Low based on how much of the uplift depends on assumptions).
The user explicitly selects one scenario. Any selected scenario flows to Implementation.

PAGE 3: IMPLEMENTATION
Receive the selected scenario and prepopulate a customer supply rescue plan with: customer and site context, supporting evidence from the case file, recommended actions grouped into Supply Planning tasks (allocation change with source customers and units), DC Operations tasks (expedites by backorder with source DC), Commercial tasks (credit, approver), and Customer Outreach steps (executive call, weekly review cadence). Include owner, approver, priority, due dates, dependencies, success metrics (target fill rate, aged backorders to zero, renewal signed), and a follow up review date six weeks after 2026-09-25.
Let the user edit any field, assign owners and approve.
On submit, save the plan to a persisted action log inside the app and show a labeled mock payload for CRM and service management handoff. State plainly that no external system is connected.
Keep an audit record for each plan: selected scenario, all assumptions used, rationale, approver, timestamp and expected outcomes.

DESIGN
Case oriented, calm, minimal. Few KPI tiles. Top stepper Case Queue -> Scenario Lab -> Implementation. Preserve selected customer and scenario across pages. Tables where precision matters, tabular numerals for money.
```
