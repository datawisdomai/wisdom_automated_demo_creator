# 5m Demo Script: Contract Reconciliation Review
Companion video: add Loom link once recorded

## Prepare ahead of time
- Contract Reconciliation Review Live App with the original prompt used to generate it visible in the side bar: https://proddemo.askwisdom.ai/apps/contract-reconciliation-review--app_99d32a563228427a884b41a537fe5d13
- Tabs needed at a minimum: Findings Queue, Case Review, and Export. Open it once beforehand so the queries are cached; the queue should open on Halvorsen Therapeutics (11 findings).
- Ad hoc chat on the Meridian Clinician Network domain with this follow-up already answered: "Show me the full amendment lineage for Halvorsen Therapeutics and where Salesforce and NetSuite each stand relative to the latest amendment and what the dollar exposure is": https://proddemo.askwisdom.ai/chat/dd7f4372-9f1a-49a2-a63f-7c7d14172863
- Second chat on the domain answered from the signed PDF in the S3 contract archive: "What does Amendment 2 to agreement MCN-2025-0142 say about the billing milestones and the term? Quote the amended terms from the signed document.": https://proddemo.askwisdom.ai/chat/434f7d43-c444-43fe-8c8e-b4338c3be9f7
- "Amendment Sync Watch" agent in visualizer mode, pre-built as a draft with the prompt still showing. It does not need to be saved or run, just shown as made from a single prompt (prompt at the bottom of this doc): https://proddemo.askwisdom.ai/agents/AGENT_9ca79491-0366-4e7b-965e-1b030c1461ab/edit
- Domain (for the controls beat and the pending extracted context): https://proddemo.askwisdom.ai/domains/ET_DOMAIN_97f519e3d9f943179957fd72ebbbf0ec
- Domain Health tab (run queued at the end of the build; left running so the suggestions are there to show): https://proddemo.askwisdom.ai/domains/ET_DOMAIN_97f519e3d9f943179957fd72ebbbf0ec/domain-health
- Connection used (Snowflake Demo, database MERIDIAN_POC): https://proddemo.askwisdom.ai/connections/et-connection-678570afa5f14afe9bb146040e70c28c

## Script
Let's take on the role of the Chief Accounting Officer at a clinician professional network. I have one priority that never ends: every signed agreement has to agree with Salesforce and with NetSuite, because that is what we bill and what we recognise. Today three teams check their own slice by hand, in two spreadsheets and an Alteryx workflow, and the amendments still slip through.
To help with that, WisdomAI built me this Contract Reconciliation Review.

{Findings Queue tab}
This is the first time anyone has run the full three-way match. Nothing here was pre-computed: Wisdom runs eleven certified checks live against the DocuSign extraction, the Salesforce replica and the NetSuite replica, using our control matrix as the rulebook.
It is quarter end, 30 September. The match finds 149 findings on 54 of our 270 agreements, a 20 percent mismatch rate, and about 30 million dollars of exposure. 85 findings are High severity.
Every row already knows who owns it. Sales Ops has 35 findings, Revenue Accounting 23, Billing 91, and Billing carries most of the dollars because contract milestones with no NetSuite bill are the biggest category, 79 of them. Ten amendments never reached NetSuite at all.
I can filter by team, severity, customer type, account owner or check type. Filter by owner and one name stands out: Dana Whitfield fails on 16 of her 35 agreements, more than double the overall rate. That is a coaching conversation, not a control failure, but it is logged under OTC-04 either way.

{Case Review tab}
The queue opens on Halvorsen Therapeutics, our compound case. One master agreement and three amendments. Here is the evidence side by side: the signed terms with the chain of amendments, the Salesforce opportunities, the NetSuite orders and their billing schedule, with the field that failed highlighted.
Salesforce stops at Amendment 2, so the price reduction in Amendment 3 is missing and bookings are 120 thousand too high. NetSuite stops at Amendment 1: original end date, quarterly billing, Net 30, and two sales orders because Boomi created a second order instead of updating the first. Four milestones from the amended Exhibit B will never be billed. Eleven findings, 2.3 million dollars of exposure, and I can read the check definition and the SOX control behind each one in the side panel.
I decide per finding: Confirmed, Rejected as a false positive, or Needs follow-up, with the system to correct and a note. The Billing lead does not re-review what Revenue Accounting already confirmed. One queue, one decision, nobody checks the same deal three times.

{Export tab}
Every reviewed finding comes out as JSON: the three system values, the variance, the owning team, the control reference, my decision, my note and the timestamp. This is what we would write back to Snowflake, to NetSuite or into a ticket. The write is a one-line integration away; this app does not write anywhere, and that is deliberate for an audit audience.

{Open Ask WisdomAI side panel, scroll to the original prompt}
Every element you see here came from a single prompt. I described the review workflow I wanted, the checks to run, the evidence to show and the decisions to capture.
WisdomAI built the application: the queries, the queue, the case view, the export. And because it is backed by shared business context, it knows what an agreement is, that an amendment restates the whole contract, that a Salesforce amendment is an increment, and which SOX control each check evidences. The context itself was extracted from our own documents: the metric definitions standard, the glossary, the control matrix, the close memo. Every step is auditable, from the definition used to the SQL that ran.

{Move to second Chrome tab with chat}
There will always be a next question. Here I asked Wisdom for the full amendment lineage of Halvorsen Therapeutics, where Salesforce and NetSuite each stand, and the dollar exposure.
Wisdom reconstructed the four signed versions, placed Salesforce at Amendment 2 and NetSuite at Amendment 1, listed the eleven findings and totalled the exposure, all from the live match, with the evidence and the SQL behind it.
And when a reviewer wants the legal truth rather than the extracted table, I ask what Amendment 2 actually says. Wisdom opens the signed PDF from our contract archive, quotes the amendment language and lays out the restated Exhibit B, eight milestones totalling 2.85 million, so the finding can be confirmed against the document itself.
If this is a question I would ask every week, I turn it into an agent.

{Move to Chrome tab with agent}
Amendment Sync Watch runs every weekday morning. It applies the same eleven checks to anything signed or amended in the last seven days and posts the new findings grouped by owning team, High severity first, calling out any amendment that has not reached NetSuite or Salesforce. Same checks as the app, so the app and the agent never disagree.
Again, like all things in Wisdom, this was generated from a single prompt in plain English.

## Agent prompt to pre-build
Create an agent called "Amendment Sync Watch" on the Meridian Clinician Network domain. Every weekday at 7am, run the eleven certified three-way reconciliation checks (the query library entries for TCV_MISMATCH, PRODUCT_LINE_COUNT_MISMATCH, OPPORTUNITY_WITHOUT_CONTRACT_LINK, AMENDMENT_NOT_IN_SALESFORCE, TERM_END_DATE_MISMATCH, AMENDMENT_NOT_IN_NETSUITE, DUPLICATE_SALES_ORDERS, SALES_ORDER_WITHOUT_OPPORTUNITY, PAYMENT_TERMS_MISMATCH, BILLING_FREQUENCY_MISMATCH, MISSING_BILLING_MILESTONE) restricted to agreements whose latest document was signed or amended in the last 7 days, using the certified query "Which agreements signed or amended in the last 7 days have findings and which team owns each one?". If any findings exist, group them by owning team (Sales Ops, Revenue Accounting, Billing) and post one summary with, for each team, the agreements affected, the check type, the contract value against the Salesforce and NetSuite values, the dollar variance, the severity and the SOX control reference, with High severity findings first; call out any amendment that is not reflected in NetSuite or not booked in Salesforce explicitly, since those are the Boomi propagation failures. Send nothing if nothing triggers and never repeat the same finding on consecutive days.
