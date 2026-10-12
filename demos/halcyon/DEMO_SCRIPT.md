# 5m Demo Script: Customer Supply Rescue Workbench
Companion video: add Loom link once recorded

## Prepare ahead of time
- Customer Supply Rescue Workbench Live App open (proddemo → Certified Demos → Halcyon Specialty Distribution) with the original prompt visible in the Ask WisdomAI side bar.
- Tabs needed at a minimum: Case Queue (executive overview), Scenario Lab, and Implementation.
- Ad hoc chat on the Halcyon Specialty Distribution domain with this follow-up already answered: "Which contracted customers renewing in the next 120 days show deteriorating service, and for the top one, what is driving it and how much of the drop is the Vanterra allocation versus everything else?"
- "Customer Supply Risk Monitor" agent open in the visualizer, pre-built as a draft with the prompt still showing. It is never saved as active or run; it only needs to show it was made from a single prompt (prompt at the bottom of this doc).
- Demo "today" is 2026-09-25; the data runs from 2025-01-01.

## Script
Let's take on the role of the Director of Customer Supply Operations at Halcyon, a specialty pharmaceutical distributor. I have one question that never goes away: which customers need an intervention today, and what do we do about it before a renewal is at risk.
To help with that, WisdomAI built me this Customer Supply Rescue Workbench.

{Case Queue tab}
This opens on the customers renewing in the next 120 days, ranked by an operational risk score that is fully transparent: fill-rate deterioration, backorder aging, service cases and escalations, and a decline in the non-allocated volume they choose to buy from us. It is a triage score, not a churn prediction.
Bayview Regional Health is at the top. $48 million of annual contract value, renewing on 15 December, risk score around 79. Their line fill rate has dropped from 92 percent to 83 percent over the last eight weeks, 35 backorders are more than two weeks old, worth $1.8 million, and 14 high-severity service cases are open. And the volume they are not forced to buy from us is down 18 percent. That is the early signal that a customer is quietly moving categories to another distributor.
Clicking the row opens the case file: fill rate by therapeutic class, Vanterra allocation requested versus allocated versus consumed, the aged backorders, the open cases, and the weekly non-allocated spend. The story is one product: Vanterra, a GLP-1 on manufacturer allocation, is filling at 57 percent while everything else is stable.

{Scenario Lab tab}
This is where the app stops being a report and becomes an operational cockpit.
For Bayview I can model the rescue directly. What happens if I reallocate Vanterra units from the customers using less than 60 percent of their allocation? What if I expedite the aged backorders from another DC? What if I add a renewal credit, or executive outreach?
I adjust those levers and see the impact immediately, side by side: the observed baseline, my own custom scenario, and a system-recommended scenario where Wisdom has already ranked the actions by retained contract value per dollar. Every assumption behind the retention uplift is visible and editable.

{Implementation tab}
Going further, Wisdom turns the scenario I chose into a customer supply rescue plan: supply planning tasks with the donor customers and units, DC operations expedites by backorder, the commercial credit with its approver, and the customer outreach cadence, each with an owner, a due date and a success metric. There is a leadership summary written from my assumptions, and a follow-up review date six weeks out.
So now, let's look at how this application was created.

{Open Ask WisdomAI side panel, scroll to the original prompt}
Every element you see here came from a single prompt. I described the business problem, the views to use, the data rules to follow, and the three pages I wanted.
WisdomAI then created the application: the queries, the charts, the scenario math, and the plan. There was no dashboard to drag together and no application to write.
And because the workbench is backed by shared business context, it knows what a line fill rate is, why allocated products are excluded from the demand signal, and that today is 25 September. I can audit every step, from the context the agent used to the SQL behind each number. The experience is interactive, but the analysis stays governed and repeatable.

{Move to second Chrome tab with chat}
There will always be a next question. If I need more than the filters on the workbench, I just ask. Here I asked Wisdom which contracted customers renewing in the next 120 days show deteriorating service, and for the top one, how much of the drop is the Vanterra allocation versus everything else.
Wisdom doesn't just summarize what's on the screen. It ranks the renewal window on the operational risk indicators, isolates Bayview, splits the 8.5-point fill-rate decline into Vanterra and non-Vanterra effects, and finds that Vanterra accounts for most of it while non-Vanterra fill actually improved.
It then explains the result, shows the evidence, and offers the next questions: who has unused Vanterra allocation that could be rebalanced, and what change would get Bayview back above 90 percent.
If this is a question I'd ask every week, I turn it into an agent.

{Move to Chrome tab with agent}
This Customer Supply Risk Monitor runs every weekday at 7am. On Mondays it emails me the customers renewing in the next 120 days with a risk score of 40 or more, leading with anyone newly above the line and the contract value at risk. Tuesday to Friday it only emails if something needs attention at a strategic or key account: a backorder crossing 14 days, a new critical case or executive escalation, a major cold-chain excursion, or a Vanterra allocation fully consumed with a shortfall above 200 units.
It never repeats an alert on consecutive days, and it sends nothing if nothing triggers.
Again, like all things in Wisdom, this was generated from a single prompt in plain English.

## Agent prompt to pre-build
Create an agent called "Customer Supply Risk Monitor" that checks the data every weekday at 7am. Every Monday, email me a short summary of active customers renewing in the next 120 days, ranked by operational risk score from V_CUSTOMER_HEALTH, flagging any customer with a score of 40 or more. For each flagged customer include renewal date, annual contract value, the top risk reason, recent versus prior fill rate, aged backorders over 14 days, and one suggested next step. Lead with any customer newly above 40 since last week and include total contract value at risk. Tuesday through Friday, only email me if something needs attention today at a strategic or key customer inside 120 days of renewal: a backorder crossing 14 days open, a new CRITICAL service case or executive escalation, a MAJOR or CRITICAL cold chain excursion on a shipment to them, or Vanterra allocation utilization at 100 percent with a shortfall above 200 units in the current month. Keep daily alerts to a few lines with the customer, what happened, renewal date, contract value and one suggested next step. Never repeat the same alert on consecutive days and send nothing if nothing triggers.
