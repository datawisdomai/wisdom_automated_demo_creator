# AE instructions (Alex Torti, Sr. AE) — received 2026-10-15

Chick here is the call. Can you give. Bit of a custom demo around the use case to add another sku for
these guys of advanced analytics in the product

Nan basically wrote your SE's script on the call. He told you exactly what he's building, what he's
stuck on, and the objection that will kill the deal internally. Build the 30 minutes around those
three things, in this order.

1. His live project: natural language to a configured portal view (about 10 min). This is the
   centerpiece. He's building an AI layer that turns a client's plain-English request into the clicks
   needed to configure a custom index or dashboard on their portal. He's swapping between Microsoft
   and Amazon agentic models and hasn't picked one for production. Have the SE show an
   allocator-style prompt producing a finished, interactive app in seconds, for example: "Build me a
   custom index of North American buyout funds, vintages 2015–2020, and compare quarterly IRR to the
   broad PE benchmark." Then refine it conversationally ("now split by fund size," "add a cash-flow
   pacing view"). The point to land is that this is the production-grade version of the prototype his
   team is trying to stitch together.

Build a synthetic private-capital dataset with fund cash flows, NAVs, vintages, strategies, regions,
and a line-of-credit field. Add one unstructured document, like a sample fund quarterly report or
10-K PDF, so extraction is part of the story. That's a core piece of his team's workflow.

Chick's focus for this demo build: simplicity of the build and speed.

## Chick's script notes (corrected, 2026-10-15)
Wisdom is aimed at two personas: business users (possibly non-technical decision makers who need
access to data and insight) and data administrators (who own governance and access and maintain
accuracy and consistency). Look at the product through both lenses.
Flow: (1) open with the fictional company and scenario; (2) create the Live App from the prompt and
say it takes a few minutes to generate; (3) while it cooks, switch to the data-administrator side and
run the standard domain-building demo (no script needed for that section); (4) come back and walk
through the generated Live App (needs a walkthrough script of what it should have generated, since the
output varies); (5) ask a follow-up question directly in the Live App; (6) "if I want to automate a
question I can do so with agents": transition to the pre-built agent and walk through what it does.
