---
name: demo-script
description: Write or refresh a demo's 5-minute DEMO_SCRIPT.md in the Shipping Optimization Cockpit format (prepare-ahead list, tab-by-tab script, follow-up chat, agent, agent prompt) from the demo's spec, prompts and build state. Use at the end of /create-demo or whenever someone asks for a demo script, talk track or run-of-show for a demo in this repo.
---

# /demo-script <demo>

Inputs: `demos/<demo>/demo.yaml`, `DEMO_PLAN.md`, `00_DESIGN.md` or control points, `live_app_prompt.md`,
`agent_prompt.md`, `chat.followup_question`, `.state.json` (real app/agent names and ids), and the
template `docs/templates/demo_script_example.md`. Read the template every time — match its voice:
first person as the persona, short sentences, {stage directions in braces}, no feature lists.

Write `demos/<demo>/DEMO_SCRIPT.md` with exactly these parts:
1. `# 5m Demo Script: <Live App name>` + "Companion video: add Loom link once recorded".
2. **Prepare ahead of time** — the Live App open with its original prompt visible in the side bar;
   the three tabs by their real names; the chat with the follow-up question already answered (quote
   the exact question); the agent open in the visualizer with its prompt showing, not saved or run.
3. **Script** — ~600–750 words: the persona's never-ending priority in one line; `{Executive
   Overview tab}` what the KPIs and the trade-off chart show, naming the hero arc's numbers; `{Scenario
   Lab tab}` three what-if questions the controls answer, the three side-by-side scenarios; `{Implementation
   Plan tab}` phased by confidence, leadership summary, the concrete queue; `{Ask WisdomAI side panel}`
   "every element came from a single prompt" + governance line; `{chat tab}` the follow-up question,
   what Wisdom did (multi-step, business definitions, evidence), and the answer's headline; `{agent tab}`
   what it watches, thresholds, what it sends, "generated from a single prompt in plain English".
4. **Agent prompt to pre-build** — the agent prompt verbatim from `agent_prompt.md`.

Numbers in the script must come from the data (reviewed queries / checks output), never invented.
Keep prospect names out. Finish by printing the "Prepare ahead of time" list in chat.
