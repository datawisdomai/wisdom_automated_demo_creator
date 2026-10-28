# 5m Demo Script: Pecos Ridge Supply Chain Spend Cube
Companion video: add Loom link once recorded

## Prepare ahead of time
- Pecos Ridge Supply Chain Spend Cube open with the original prompt visible in the side bar: https://digitz.wisdom.ai/apps/pecos-ridge-supply-chain-spend-cube--app_4b81a7c81be443f88dde538298003164
- Tabs needed at a minimum: Category Overview, Price Dispersion (set to Corrosion inhibitor, water-soluble, filming amine / 2025), Pricebook Variance & Disputes (Redline Sand LLC / 2026) and Cost per Lateral Foot. Classification Queue is the optional fifth.
- Ad hoc chat on the O&G domain with this follow-up already answered: "What did we pay per gallon for water-soluble corrosion inhibitor by supplier and pack size in 2025 and how much would we have saved at the best observed price": https://digitz.wisdom.ai/chat/753bf304-424d-4067-845c-96ea503d6119
- "Price Variance Watch" agent open in the visualizer with the prompt still showing. It is a disabled draft; it is never saved as active or run: https://digitz.wisdom.ai/agents/AGENT_29a65fdc-fd29-4d84-9264-e5d96387a39b/edit
- Domain (the partner's O&G domain, now with the OpenInvoice database and the supplier document archive): https://digitz.wisdom.ai/domains/ET_DOMAIN_4804a0b2ffcd484ab6d7cf410dceed55
- Domain Health tab, with the analysis queued by the build left running: https://digitz.wisdom.ai/domains/ET_DOMAIN_4804a0b2ffcd484ab6d7cf410dceed55/domain-health

## Script
Let's take on the role of the supply chain category manager at Pecos Ridge Energy, an operator in the Permian, the Anadarko and the Hugoton. I have one priority that never ends: pay the right price for what the field actually uses, across every supplier, without slowing the wells down.
Accounting already has years of OpenInvoice invoices. The cost codes on them are fine for the ledger. They tell me nothing about which product was bought, how much, or what we paid per gallon or per ton. So WisdomAI built me this Spend Cube on top of the line items and our product taxonomy.

{Category Overview tab}
This is the whole picture for 2026 year to date: about 224 million dollars of invoiced spend across the categories supply chain owns, how much of it is classified to a generic product, and the slice that is still unclassified, 18 million dollars or about 8 percent. The chart stacks spend by family since 2022, and Unclassified is its own segment so nobody can hide it.
The table underneath is the one accounting could never give me. One row per generic product: spend, standard quantity, the standard unit price we paid and how many suppliers we bought it from. The corrosion inhibitor row shows two suppliers and a 29 percent price dispersion. Let me click into it.

{Price Dispersion tab}
Same product, water-soluble corrosion inhibitor, two suppliers. Corrosion Control Chem sells it as CorroShield CS-7000 and we paid 16.53 dollars a gallon on a volume-weighted basis. Basin Chemical sells it as CorroGuard BC-220 and we paid 21.41. In spend analytics both are just "Chemicals".
The pack table shows why. Bulk gallons were 15.95, totes 16.45, drums 17.59. On the Basin side totes were 19.89, drums 21.22 and the five-gallon pails 23.34. Pails carry a 17 percent premium over the same supplier's totes.
The headline: had we bought all of 2025 at the best observed supplier price we would have saved 1.83 million dollars on this one product. The best-price line on the chart makes the gap obvious, and the monthly trend shows it was there all year.

{Pricebook Variance & Disputes tab}
This tab compares every invoice line to the price book we loaded from the supplier's MSA pricing exhibit. It opens on Redline Sand. From February 2026 every RL100 line came in above the contract rate: 36 lines, about 79.48 dollars a ton invoiced against 73.17 in the RLS-2026 schedule, 232 thousand dollars of variance, 27 of the lines already disputed. The drill-down shows the invoice number, the rate, the variance and the Exhibit B file the rate came from, so the dispute is documented before I pick up the phone.

{Cost per Lateral Foot tab}
This is where the invoice detail meets operations. Completion spend per well divided by lateral feet. Proppant alone runs about 46 dollars a lateral foot in the Midland, 58 in the Delaware and 69 in the Anadarko, across 174 wells with 2025 and 2026 completion AFEs. The assumptions panel applies a 10 percent proppant price rise and shows the delta per foot and on year-to-date completion spend. It is arithmetic on invoiced data, not a forecast, and that is exactly what I need for a budget conversation.

{Open Ask WisdomAI side panel, scroll to the original prompt}
Every element you see here came from a single prompt. I described the business problem, the views to use, the rules to follow and the five pages I wanted. WisdomAI built the queries, the charts, the pack table and the assumptions panel.
And because it sits on shared business context, it knows that a standard unit price is spend over standard quantity, that a drum is 55 gallons and a joint is 42 feet, that fees are excluded from price comparisons, and that only approved classifications count. Every number can be traced from the chart back to the SQL and the invoice line.

{Move to second Chrome tab with chat}
There is always a next question. Here I asked what we paid per gallon for water-soluble corrosion inhibitor by supplier and pack size in 2025 and how much we would have saved at the best observed price.
Wisdom did not summarise the screen. It pulled the approved classifications, excluded fees and surcharges, computed the six supplier-pack prices, worked out the supplier-wide best price of 16.53 and the 1.83 million dollar opportunity, and explained that this is a sourcing opportunity, not recoverable overbilling. When I asked for it in plain words it gave me one paragraph with every number. That is the same answer a category analyst would take two days to build.
If I would ask this every week, I turn it into an agent.

{Move to Chrome tab with agent}
Price Variance Watch runs every Monday at 7. It looks at the prior seven days of OpenInvoice lines, flags any supplier invoicing more than 5 percent over its price book with the dollar variance and the dispute status, and any supplier with more than 25 thousand dollars of new unclassified spend. It investigates which item codes and invoices drive it, then sends me and our data steward one message with the tables, the drivers and the dollars at risk.
Again, like everything in Wisdom, this was generated from a single prompt in plain English.

## Agent prompt to pre-build
Create an agent called "Price Variance Watch" on the O&G domain. Every Monday at 7am, look at the prior 7 days of OpenInvoice lines. First, from V_PRICEBOOK_VARIANCE, take every line with SERVICE_DATE in the last 7 days whose PRICE_VARIANCE_PCT is above 5 percent (invoiced unit price more than 5 percent above the contract rate in the loaded price book) and group it by SUPPLIER_NAME: the number of lines, SUM(PRICE_VARIANCE_USD) as the dollar variance, the invoiced amount, the PRICEBOOK_VERSION in force and the dispute status as the count and dollar variance of lines whose LINE_STATUS is Disputed or Short-paid against those still Approved. Second, from V_UNCLASSIFIED_SPEND, take every line with INVOICE_DATE in the last 7 days and group it by SUPPLIER_NAME; keep the suppliers whose SUM(LINE_AMOUNT_USD) is above 25,000 USD and show the amount, the line count, the top three SUPPLIER_ITEM_DESCRIPTION values by amount and their REVIEW_STATUS. If either list is not empty, investigate which supplier item codes and invoices drive the variance, whether the same item was invoiced at the contract rate by the same supplier earlier in the month, and whether the unclassified descriptions match an item the steward already classified for another supplier. Send Jessica Whitaker and Hector Brown one message in this format: a one-line subject "Price Variance Watch for the week ending <date>: <n> suppliers over contract, <m> suppliers with new unclassified spend"; section 1 "Invoiced above contract", a table by supplier with lines, dollar variance, invoiced amount, price book version, disputed lines and dollar variance, approved but over-contract lines and dollar variance, largest variance first; section 2 "New unclassified spend", a table by supplier with amount, lines, top descriptions and review status, largest amount first; section 3 "What is driving it", three to five bullets with the item codes, invoice numbers and the comparison to the contract rate; and a closing line with the total dollar variance at risk and the amount not yet disputed. Never repeat the same line in consecutive weeks and send nothing if neither list triggers.
