# Agent prompt template (one prompt, created as a draft — never run during the demo)

The agent watches the story-arc metric on a schedule, investigates when a threshold breaks, and sends
a summary. Name the exact views/columns. Keep it to one paragraph the audience can read on screen.

```
Create an agent called "[AGENT NAME]" on the [DOMAIN NAME] domain. Every [Monday / weekday at 7am],
calculate [metric 1] and [metric 2] for the prior [week] by [dimension A] and [dimension B], [scope
rule, e.g. ground shipments only, excluding refunded labels]. If any [segment] falls below [threshold
1], or [threshold 2 anywhere], or [metric] rises more than [X%] versus the trailing [4-week] average,
investigate which [dimensions] are driving it and whether [a like-for-like alternative] performed
better on those segments. Send the [team] a summary with the finding, the affected segments, and the
supporting data. Never repeat the same alert on consecutive days and send nothing if nothing triggers.
```
