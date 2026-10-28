# #close-reconciliation channel export

Workspace: Meridian Clinician Network
Channel: #close-reconciliation
Exported: 2026-09-29
Period: 2026-07-02 to 2026-09-29 (selected threads)

## Thread: which contract value do I use

**Priya N. (Sales Ops)** 2026-07-02 09:14
Quick one. For Ardent Therapeutics the contract shows 1,003,000 on the A2 row but if I add up the three CONTRACTS rows I get way more. Which one is the deal value?

**Rahul M. (Revenue Accounting)** 2026-07-02 09:21
Never add CONTRACTS rows. Every amendment restates the whole agreement, so the latest row IS the deal value. 1,003,000. Use V_CONTRACT_CHAIN.current_tcv and you never have to think about it.

**Priya N. (Sales Ops)** 2026-07-02 09:22
And Salesforce?

**Rahul M. (Revenue Accounting)** 2026-07-02 09:24
Salesforce is the other way round. Original opp has the original value, each amendment opp has the increment. Sum them. V_CHAIN_SYSTEM_SUMMARY.sf_amount does it.

**Priya N. (Sales Ops)** 2026-07-02 09:25
So contract = latest row, Salesforce = sum of opps. Got it. Writing that on a sticky note.

## Thread: NetSuite still shows the old end date

**Devon K. (Billing)** 2026-07-15 14:02
Ardent Therapeutics A2 extended the term to 2026-11-01 but NetSuite service end is still 2026-08-01. Boomi says it synced. Do I fix the order or wait?

**Rahul M. (Revenue Accounting)** 2026-07-15 14:10
Check boomi_sync_timestamp on the order. If it is after the A2 signed date Boomi ran but did not restate the end date (we have seen that since the March upgrade). If it is before, the amendment never arrived at all. Different fix, different ticket.

**Devon K. (Billing)** 2026-07-15 14:12
Sync is 2024-10-11, A2 was signed 2025-02-13. So it never arrived.

**Rahul M. (Revenue Accounting)** 2026-07-15 14:13
Then NetSuite is on A1 terms for everything, not just the end date. The order total, the lines and the billing schedule are all stale. That is a Revenue Accounting finding (amendment not reflected in NetSuite, OTC-07). Log it, I will take it.

**Jonathan G. (SOX and Automation)** 2026-07-15 14:30
Please make sure the ticket references OTC-07. The auditors sample these in Q4.

## Thread: how are we counting exposure

**Sid S. (CAO)** 2026-08-05 08:40
The Q2 memo says 24 million of exposure. Is that money we will lose?

**Rahul M. (Revenue Accounting)** 2026-08-05 08:52
No. Exposure is a review-priority number: the sum of the absolute dollar variance on findings nobody has dispositioned yet. A missing milestone contributes its full amount even though most of them get billed late rather than never. The standard (v1.4 section 6) spells out what each check contributes.

**Sid S. (CAO)** 2026-08-05 08:55
Fine. But I want one list, not three. Billing has their spreadsheet, Sales Ops has theirs, you have the Alteryx workflow. Nobody sees the whole picture.

**Rahul M. (Revenue Accounting)** 2026-08-05 08:58
Agreed. That is the point of the certified check queries. Same eleven checks for everyone, owning team on every row.

## Thread: duplicate sales orders

**Devon K. (Billing)** 2026-08-20 11:05
Halvorsen Therapeutics has SO-10017 and a second order SO-10018 for 450,000. Both have quarterly bills. Are we double billing?

**Rahul M. (Revenue Accounting)** 2026-08-20 11:14
That is the Boomi behaviour from last June: it created a new order from the A1 opportunity instead of updating SO-10017. Together they equal A1 (2,250,000) so not double billed yet. But A2 converted the whole thing to milestones and A3 cut the price and neither reached NetSuite, so the quarterly bills on both orders are wrong going forward. It is the compound case. Four of the Exhibit B milestones have no bill at all.

**Devon K. (Billing)** 2026-08-20 11:16
Can we please use this one for the training deck. It has everything.

**Rahul M. (Revenue Accounting)** 2026-08-20 11:16
Already in the wiki.

## Thread: Dana's deals

**Marcus O. (Sales Ops)** 2026-09-10 16:40
Not naming names but one rep rounds every opp to the nearest 25k and leaves the newsletter line off. Can the recon flag the rep so we can coach rather than re-review every deal?

**Rahul M. (Revenue Accounting)** 2026-09-10 16:44
It already groups findings by account owner. Dana is at roughly double the overall mismatch rate. It is a coaching conversation, not a control failure, but TCV mismatch is OTC-04 so it still gets logged.

**Jonathan G. (SOX and Automation)** 2026-09-10 16:50
And please stop re-reviewing. If the check says Match, it matched. The whole point of one reconciliation is that nobody has to do it twice.

## Thread: this week's signings

**Rahul M. (Revenue Accounting)** 2026-09-29 17:05
Reminder for the Q3 close: the as-of date is 2026-09-30. Anything signed or amended in the last 7 days gets the same eleven checks on Thursday morning. The Amendment Sync Watch agent will post the list grouped by owning team. Do not start a spreadsheet.
