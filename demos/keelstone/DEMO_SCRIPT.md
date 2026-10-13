# 5m Demo Script: Renewals and Installed Base Cockpit
Companion video: add Loom link once recorded

## Prepare ahead of time
- Renewals and Installed Base Cockpit — https://proddemo.askwisdom.ai/apps/renewals-and-installed-base-cockpit--app_4c27c3346904444482aae6d66649c4b6 — with the original prompt used to generate it visible in the side bar (domain Keelstone Data Systems in Default Organization: https://proddemo.askwisdom.ai/domains/ET_DOMAIN_f6df7b3a5120419383a6babb46d0f65d).
- Tabs needed at a minimum: Executive Overview, Renewal Rescue Lab (scenario lab), and Implementation Plan. Americas East preselected.
- Ad hoc chat on the Keelstone Data Systems domain, with this follow up already answered: "Which region's renewal rate has dropped the most this fiscal year and what is driving it and how much ARR is up for renewal there in the next 90 days?" — https://proddemo.askwisdom.ai/chat/e8daec43-eb9c-409d-a0a9-ef43ba576350
- A second chat ready for the governance beat: "What is our ARR?" then "Why does the Sales Ops ARR number differ from the Finance ARR number?" (ask live or pre-answer; both are reviewed queries).
- "Renewal Risk Watch" agent — https://proddemo.askwisdom.ai/agents/AGENT_146c8d79-a16a-47b7-b3da-d8511b10e515/edit — open in visualizer mode, pre-built with the prompt still showing. It is a draft; it does not need to be enabled or run (prompt at the bottom of this doc).
- Optional: the domain's Documents panel open to show the metric standard, glossary and playbook PDFs the context was extracted from; the Domain Health tab for the suggestions beat: https://proddemo.askwisdom.ai/domains/ET_DOMAIN_f6df7b3a5120419383a6babb46d0f65d/domain-health

## Script
Let's take on the role of the VP of Sales Operations at Keelstone Data Systems, a storage and hybrid-cloud infrastructure vendor. I have one priority that never ends: keep renewals from slipping, and know which ones are slipping before the quarter closes.
To help with that, WisdomAI built me this Renewals and Installed Base Cockpit.

{Executive Overview tab}
This gives me one place to see the business the way Finance defines it. ARR is just over 500 million dollars, and it is the certified Finance number, not a number someone built in a spreadsheet. Renewal rate this fiscal year is running at 85 percent against 90 last year.
The chart tells me where. Every region held within a few points of last year except Americas East, which fell from 90 percent to 79. Underneath it I can see 28 million dollars of Americas East ARR renewing in the next 90 days, and 13 million of that flagged at risk by my renewals team. Two reasons dominate: the KS-7000 array family reaches end of support in January, and a cluster of P1 outages followed the KeelOS 9.14.2 upgrade. Seventy P1 cases on that release in Americas East since July, five or fewer anywhere else, because that region upgraded first.
And there is one more panel I use every month. Finance says ARR is 500 million; my own Sales Ops dashboard says 527. The cockpit shows the gap and the reason in one sentence: Sales Ops keeps counting lapsed contracts while their renewal opportunity is still open in Salesforce. Same data, two definitions, and now everyone can see which one is certified.

{Renewal Rescue Lab tab}
So this is where the cockpit becomes more than a dashboard. It is an operational tool.
What happens if we put a migration offer and the extended support bridge in front of every at-risk KS-7000 renewal?
What if we pair a credit with the written root cause analysis for the accounts that had an outage?
What if I move two renewals specialists into the region and right-size the cloud commits that are under-used?
I set those controls and see the impact immediately. Three scenarios sit side by side: the observed baseline, my custom scenario, and a system recommended scenario where Wisdom ranks the at-risk contracts by value and save probability and spends the budget and specialist capacity in that order. Every assumption is on screen and editable, and the confidence rating tells me how much of the uplift depends on them.

{Implementation Plan tab}
Going further, Wisdom turns the scenario I chose into a rollout plan. It is phased by confidence: quick wins on the largest end-of-support renewals, a controlled pilot on the accounts with open P1 cases, and the segments to monitor and hold. There is a leadership summary written from my current assumptions, monitoring thresholds for the regional renewal rate and new P1 cases, and the actual queue of contracts with customer, partner, rep, end date and annual value. I can edit, assign owners and approve, and the handoff to Salesforce is shown as a labelled mock payload, because nothing here is wired to production.
So now, let's look at how this application was created.

{Open Ask WisdomAI side panel, scroll to the original prompt}
Every element you see here came from a single prompt. I described the business problem, the views to use, the rules to follow and the three pages I wanted.
WisdomAI created the application: the queries, charts, calculations and scenario controls. Nobody dragged a dashboard together or wrote an app from scratch.
And because the cockpit is backed by shared business context, it knows that ARR means contracts in force on the measurement date, that our fiscal year ends in April, and that renewal rate is dollars renewed over dollars due. Those definitions came out of the documents our stewards already own: the Finance metric standard, the glossary with its owners and source systems, the data platform wiki page, even a Slack thread from the data help channel. I can audit every step, from the context the agent used to the full trajectory from SQL to visualization.

{Move to second Chrome tab with chat}
There will always be a next question. If I need more than the filters on the cockpit, I just ask. Here I asked Wisdom which region's renewal rate dropped the most, what is driving it, and how much is up for renewal in the next 90 days.
Wisdom does not summarize what is on the screen. It runs a multi-step analysis: renewal rate by region for both fiscal years using the certified definition, the at-risk pipeline by reason, and the P1 case counts by firmware version. It explains the result, Americas East down 11 points with 28 million renewing and 13 million at risk, and it shows the evidence behind each number. And if I ask what customers are actually saying, it reads the engineers' free-text case notes, where customers are telling us they want a migration plan before they sign.
If this is a question I'd ask every week, I turn it into an agent.

{Move to Chrome tab with agent}
This Renewal Risk Watch runs every Monday. It watches the contracts ending in the next 90 days, flags anything at risk, on an end-of-support product, or at a customer with an open P1 case, and compares the at-risk total with last week. If a region jumps more than 10 percent, or new P1 cases appear on 9.14.2, it adds the renewal rate context and sends me the ten largest at-risk contracts with a suggested next step from our renewal playbook.
Again, like all things in Wisdom, this was generated from a single prompt in plain English.

## Agent prompt to pre-build
Create an agent called "Renewal Risk Watch" on the Keelstone Data Systems domain. Every Monday at 7am, take the active contracts ending in the next 90 days from V_RENEWALS_AT_RISK_90D and list those that are flagged AT_RISK or whose product reaches end of support within 12 months or whose customer has an open P1 case, grouped by region and renewals specialist, with customer, partner, product family, end date, annual value and the risk reason. Compare the total ARR at risk with the previous Monday and call out any region where it rose by more than 10 percent or where new P1 cases on KeelOS 9.14.2 were opened during the week, using V_SUPPORT_CASE_SUMMARY. For each flagged region add the FY27 renewal rate to date from V_RENEWAL_PERFORMANCE next to its FY26 rate. Send the VP of Sales Operations a summary with the totals, the ranked list of the ten largest at-risk contracts and one suggested next step per contract taken from the renewal playbook (migration offer for end-of-support products, RCA and credit review for open P1 cases, right-sizing for under-utilised cloud commits). Never repeat the same alert on consecutive weeks for an unchanged contract and send nothing if nothing is at risk.
