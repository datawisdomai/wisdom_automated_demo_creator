# Agent prompt — Customer Supply Risk Monitor

Paste into Wisdom on the Halcyon Specialty Distribution domain. Treat 2026-09-25 as today when
testing; in the demo say the agent runs on the live data.

```
Create an agent called "Customer Supply Risk Monitor" that checks the data every weekday at 7am. Every Monday, email me a short summary of active customers renewing in the next 120 days, ranked by operational risk score from V_CUSTOMER_HEALTH, flagging any customer with a score of 40 or more. For each flagged customer include renewal date, annual contract value, the top risk reason, recent versus prior fill rate, aged backorders over 14 days, and one suggested next step. Lead with any customer newly above 40 since last week and include total contract value at risk. Tuesday through Friday, only email me if something needs attention today at a strategic or key customer inside 120 days of renewal: a backorder crossing 14 days open, a new CRITICAL service case or executive escalation, a MAJOR or CRITICAL cold chain excursion on a shipment to them, or Vanterra allocation utilization at 100 percent with a shortfall above 200 units in the current month. Keep daily alerts to a few lines with the customer, what happened, renewal date, contract value and one suggested next step. Never repeat the same alert on consecutive days and send nothing if nothing triggers.
```

Shorter variant if the agent builder prefers one trigger per agent:

```
Create an agent called "Renewal Risk Digest" that runs every Monday at 7am and emails me the active customers renewing in the next 120 days with an operational risk score of 40 or more from V_CUSTOMER_HEALTH, ranked by score, with renewal date, contract value, top risk reason, fill rate change, aged backorders and one suggested next step. Call out anyone newly above 40 first and total the contract value at risk.
```
