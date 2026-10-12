# 5m Demo Script: Shipping Optimization Cockpit
Companion video: add Loom link once recorded

## Prepare ahead of time
- Shipping Optimization Cockpit with the original prompt used to generate it visible in the side bar.
- Tabs needed at a minimum: Executive Overview, Optimization Lab (scenario lab), and Implementation Plan.
- Ad hoc chat with the cockpit, with this follow up already answered: "Which USPS zones and weight bands are dragging on-time below 90%?"
- "Carrier Reliability Guardrail" agent in visualizer mode, pre-built with the prompt still showing. Doesn't need to be saved or actually run, just needs to show it was made from a single prompt (prompt at the bottom of this doc).

## Script
Let's take on the role of a shipping manager at an ecommerce company. I have one priority that never ends: get shipping costs down without breaking delivery promises to our customers.
To help with that, WisdomAI built me this Shipping Optimization Cockpit.

{Executive Overview tab}
This gives me a single place to understand our shipping performance. I can see total shipping costs, average cost per label, and our on-time delivery rate, and break them down by carrier, zone, and weight band.
This chart plots cost against reliability for every carrier. Shifting everything to USPS would save us money, but it would hurt how many packages arrive on time. It's up to me as the shipping Manager to model the best case scenario between cost and reliability.

{Optimization Lab tab}
So this is where this Live app becomes more than just a reporting dashboard. It is an operational cockpit.
In this Optimization Lab that I've created I can model the tradeoff between cost and reliability directly.
What happens if we set our minimum on-time rate to 93%?
What if we reallocate 50% of eligible shipments to lower cost carriers?
What if we roll this out to a quarter of our volume instead of all of it?
I adjust those assumptions and immediately see the impact. The cockpit shows three views side by side: the observed baseline, my own custom scenario, and a system recommended scenario where Wisdom has already found the best compromise between cost and reliability.

{Open Implementation Plan tab}
Going further, Wisdom turns the scenario I chose into a rollout plan. It's phased by confidence: quick wins, a controlled pilot, and segments to monitor and hold. There's a leadership summary written from my current assumptions, monitoring thresholds, and the actual routing queue of current shipments that can move to cheaper carriers.
So now, let's look at how this application was created.

{Open Ask WisdomAI side panel, scroll to the original prompt}
Every element you see here came from a single prompt. I described the business problem, the views to use, the rules to follow, and the pages I wanted.
WisdomAI then created the application: the queries, charts, calculations, and scenario controls. There was no need to drag together a dashboard or write a separate application from scratch.
And because the cockpit is backed by shared business context, it understands what effective cost means in our business, how a fiscal week is defined, and which data each user is allowed to see. I can audit every step, from the context the agent used to the full trajectory from raw SQL to visualization. The experience is interactive, but the analysis stays governed and repeatable.

{Move to second Chrome tab with chat}
There will always be a next question. If I need more than the filters on the cockpit, I just ask. Here I asked Wisdom "Which USPS zones and weight bands are dragging on-time below 90%?"
Wisdom doesn't just summarize what's on the screen. It runs a multi step analysis across the underlying data, using our definition of on-time and the right lookback period, and isolates the zones and weight bands driving the drop.
It then explains the result, shows the evidence behind it, and lets me inspect the calculations and underlying data. So I go from a high level signal to a fully explainable root cause without leaving the application.
If this is a question I'd ask every week, I turn it into an agent.

{Move to Chrome tab with agent}
This Carrier Reliability Guardrail runs every Monday. It watches on-time rate and effective cost per label by carrier and zone. If any carrier drops below 90%, falls below 80% anywhere, or its cost per label jumps more than 10%, it runs the same investigation.
It checks whether a like for like alternative carrier performed better on those segments, then sends the shipping operations team the finding with the evidence attached, straight to email, Slack, or Teams.
Again, like all things in Wisdom, this was generated from a single prompt in plain English.

## Agent prompt to pre-build
Create an agent called "Carrier Reliability Guardrail" on the shipping domain. Every Monday, calculate delivered-shipment on-time rate and average effective cost per label for the prior week by carrier and zone, ground shipments only, excluding refunded labels. If any carrier falls below 90% on-time, or below 80% anywhere, or its effective cost per label rises more than 10% versus the trailing 4-week average, investigate which zones, weight bands, and locations are driving it and whether a like-for-like alternative carrier performed better on those segments. Send the shipping operations team a summary with the finding, the affected segments, and the supporting data.
