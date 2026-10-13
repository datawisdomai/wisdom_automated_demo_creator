# Agent prompt — Renewal Risk Watch

Paste into Wisdom on the Keelstone Data Systems domain. Created as a draft and never run during the
demo; treat 2026-10-12 as today when testing.

```
Create an agent called "Renewal Risk Watch" on the Keelstone Data Systems domain. Every Monday at 7am, take the active contracts ending in the next 90 days from V_RENEWALS_AT_RISK_90D and list those that are flagged AT_RISK or whose product reaches end of support within 12 months or whose customer has an open P1 case, grouped by region and renewals specialist, with customer, partner, product family, end date, annual value and the risk reason. Compare the total ARR at risk with the previous Monday and call out any region where it rose by more than 10 percent or where new P1 cases on KeelOS 9.14.2 were opened during the week, using V_SUPPORT_CASE_SUMMARY. For each flagged region add the FY27 renewal rate to date from V_RENEWAL_PERFORMANCE next to its FY26 rate. Send the VP of Sales Operations a summary with the totals, the ranked list of the ten largest at-risk contracts and one suggested next step per contract taken from the renewal playbook (migration offer for end-of-support products, RCA and credit review for open P1 cases, right-sizing for under-utilised cloud commits). Never repeat the same alert on consecutive weeks for an unchanged contract and send nothing if nothing is at risk.
```
