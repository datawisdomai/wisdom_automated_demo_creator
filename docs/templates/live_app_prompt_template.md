# Live App prompt template (Executive Overview → Scenario Lab → Implementation Plan)

Fill the [brackets], keep the structure. One prompt builds the whole app; the user sees this prompt in
the side panel during the demo, so it must read well. Reference ONLY views/tables that exist in the
domain. Anchor "today" to the demo as-of date. Keep it under ~900 words.

```
Create a live app called "[APP NAME]" for [COMPANY], a [one-line description]. It is an operational
cockpit for the [PERSONA], not a reporting dashboard. Every page answers "[the persona's standing
question]". Use three connected pages.

DATA RULES
Use [V_MAIN_VIEW] as the primary source for KPIs. Use [V_DETAIL_VIEW, V_OTHER_VIEW, TABLE] for
drill-downs. Aggregate each source before combining; never join fact tables as raw rows.
Anchor "today" to [AS_OF]. The latest complete [week/month] ends [DATE]; exclude the partial period
from trends. [Any business rule: e.g. exclude cancelled lines; on-time means delivered on or before
the promised date.]

PAGE 1: EXECUTIVE OVERVIEW
KPI tiles: [metric 1], [metric 2], [metric 3], [metric 4] with the change versus the prior period.
One chart that shows the core trade-off: [e.g. cost against reliability for every carrier].
Breakdowns by [dimension A], [dimension B], [dimension C] with the segments driving [the headline
story] highlighted. Preselect [HERO ENTITY] so the demo starts there.

PAGE 2: [SCENARIO LAB NAME]
For the selected [entity/segment], show three scenarios side by side: Baseline, Custom, and System
Recommended.
Baseline is the current state with no intervention.
Custom has [3-5] controls: [control 1 with range], [control 2], [control 3], [control 4].
System Recommended uses a simple transparent approach: [describe the greedy/ranking rule in one or
two sentences], and shows the ranked candidate actions with cost, impact and a plain-language reason.
Assumptions panel, editable and clearly labelled as assumptions: [assumption 1 with number],
[assumption 2], [assumption 3].
Compare all three scenarios on: [outcome metric 1], [outcome metric 2], [cost], [net value],
[confidence High/Medium/Low].
The user explicitly selects one scenario; the selection flows to the Implementation Plan.

PAGE 3: IMPLEMENTATION PLAN
Receive the selected scenario and prepopulate a rollout plan phased by confidence: quick wins, a
controlled pilot, and segments to monitor and hold. Include a leadership summary written from the
current assumptions, monitoring thresholds, the concrete queue of [items] to act on, owners, due
dates and success metrics. Let the user edit any field and approve. On submit, save the plan to an
action log inside the app and show a labelled mock payload for the [downstream system] handoff;
state plainly that no external system is connected.

DESIGN
Calm, operational, few KPI tiles. Top stepper Executive Overview -> [Scenario Lab] -> Implementation
Plan. Preserve the selected [entity] and scenario across pages. Tables where precision matters,
tabular numerals for money.
```
