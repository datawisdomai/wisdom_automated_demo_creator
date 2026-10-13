# #data-help channel export

Letterhead: Keelstone Data Systems — Slack workspace export
Channel: #data-help (public)
Exported: 2026-10-09 for the data governance review
Period: 2026-08-18 to 2026-10-08
Note: messages are reproduced as posted. Names are Keelstone employees.

## Thread: Which ARR number do I use?

**2026-08-18 09:12 — Chloe Varga (Sales Ops analyst):** Quick one. The Finance ARR pack says 487.1M for July and our Sales Ops Power BI says 508.7M. Same month. Which one goes in the QBR deck?

**2026-08-18 09:20 — Priya Iyer (Finance data steward):** Finance. 487.1M is the certified number (V_ARR_MONTHLY, measured at month end). The Sales Ops measure keeps counting contracts that have lapsed but still have an open renewal opp in Salesforce. In July that was about 21.6M.

**2026-08-18 09:23 — Chloe Varga:** So the Sales Ops number is not wrong, it just answers a different question?

**2026-08-18 09:26 — Priya Iyer:** Right. It is a pipeline view. If the opp closes won the ARR comes back; if it closes lost it drops out. Finance stops counting on the lapse date because that is what we recognise. The gap is in V_ARR_FINANCE_VS_SALESOPS as LAPSED_OPEN_ARR so you can show both and explain it.

**2026-08-18 09:31 — Daniel Okafor (Sales Ops data steward):** Adding: we are renaming the Power BI measure to "Pipeline ARR" in the October release (KI-441). Until then please label it that way in decks.

**2026-08-18 09:40 — Chloe Varga:** Got it. Using Finance ARR and a footnote. Thanks both.

## Thread: Is Q2 August to October?

**2026-08-25 14:02 — Omar Mbeki (Americas East sales director office):** Dumb question. When someone says Q2 FY27 is that calendar Q2 or ours?

**2026-08-25 14:05 — Priya Iyer:** Ours. Fiscal year ends 30 April. FY27 Q1 is May to July, Q2 is August to October, Q3 November to January, Q4 February to April. FISCAL_CALENDAR has FISCAL_QUARTER if you are writing SQL.

**2026-08-25 14:06 — Omar Mbeki:** So "this quarter" right now is FY27-Q2 and it ends 31 October. Thanks.

## Thread: Renewal rate looks wrong for Americas East

**2026-09-02 10:48 — Omar Mbeki:** Renewals dashboard shows Americas East at 79 percent renewal rate FY27 to date vs 90 last year. Finance pack says the same. But the renewals team says most of those deals are not lost, they are just not signed yet. Which is it?

**2026-09-02 10:55 — Priya Iyer:** Both are true. Renewal rate is ARR renewed over ARR due (standard v3.2 section 5). A lapsed contract with the renewal still open is pending and counts as not yet renewed. Americas East has about 20 percent of FY27 due ARR sitting in pending right now, which is why the rate is low. Churned (closed lost) is actually small.

**2026-09-02 10:58 — Daniel Okafor:** The pending pile is mostly KS-7000 accounts waiting for a migration quote and the accounts that had the 9.14.2 P1 outages in July and August. Victoria's team is working them. V_RENEWAL_PERFORMANCE splits ARR_PENDING from ARR_CHURNED so you can show the difference.

**2026-09-02 11:03 — Omar Mbeki:** OK so the headline is right and the story is "stalled not lost". That helps.

**2026-09-02 11:05 — Hannah Moreau (Renewals specialist):** Confirming from the floor. Of my 31 pending contracts 24 are KS-7000 estates. Customers want the EOS plan and the KS-9000 pricing before they sign support again. Three told me straight out they are waiting to see the RCA on the 9.14.2 failovers.

## Thread: Attach rate definition

**2026-09-15 16:20 — Elena Ramirez (Partner Ops steward):** For the partner QBR: is attach rate "has support today" or "bought support with the system"?

**2026-09-15 16:27 — Priya Iyer:** Bought with the system. Support contract starting within 60 days of the install date, by partner and fiscal quarter (V_PARTNER_ATTACH_RATE). "Has support today" is a different measure, HAS_ACTIVE_SUPPORT in V_INSTALLED_BASE_HEALTH.

**2026-09-15 16:29 — Elena Ramirez:** Then Altura is the outlier. 77 percent last year, 61 so far this year. Everyone else is flat. Flagging to channel leadership.

## Thread: Cloud commit under-utilisation list

**2026-09-29 11:41 — Mateo Delgado (Cloud billing steward):** Finance asked for the list of enterprise accounts below 60 percent of commit. V_CLOUD_COMMIT_UTILIZATION, FISCAL_YEAR = FY27, SEGMENT = ENTERPRISE, IS_UNDER_UTILIZED = 1. 27 accounts, about 3.6M of commit not consumed so far this year. Consumption overall is up about 78 percent on last year so this is a mix problem, not a demand problem.

**2026-09-29 11:50 — Chloe Varga:** Can we get that into the renewals list so the cloud specialists see it before the commit renews?

**2026-09-29 11:52 — Mateo Delgado:** Yes. Join on CUSTOMER_ID to V_RENEWALS_AT_RISK_90D where CONTRACT_TYPE is CLOUD_COMMIT.

## Thread: P1 case counts by region

**2026-10-06 08:15 — Jonas Lindqvist (Support Engineering steward):** PSA before anyone builds a chart. P1 counts by region are dominated by the KeelOS 9.14.2 failover defect (KB-2026-0917). Americas East got the managed upgrade first so it has 66 of the 74 P1s on that release since July. Other regions started upgrading in September and 9.14.3 is the fix. Always slice by FIRMWARE_VERSION.

**2026-10-06 08:22 — Omar Mbeki:** And this is why half my renewals are pending. Noted.

**2026-10-08 17:03 — Marcus Whitfield (Head of Data Governance):** Thanks all. Capturing these answers in the glossary register (GOV-GLS-001 v2026.10) so nobody has to ask twice.
