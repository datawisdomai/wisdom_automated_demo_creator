# #supply-chain-category — channel export (Jul–Sep 2026)

Workspace: Pecos Ridge Energy
Channel: #supply-chain-category (category managers, data steward, completions, AP)
Export range: 2026-07-06 to 2026-09-29
Exported by: Data Platform for the supply chain analytics onboarding pack
Participants: Jessica Whitaker (Category Manager, chemicals and water logistics); Clint Johnson (Category Manager, proppant and OCTG); Hector Brown (Supply Chain Data Steward; rentals, fees and MRO); Marcus Pena (Completions Engineer, Delaware Basin); Renee Alvarado (AP Analyst)

## 2026-07-06

**Renee Alvarado (AP)** 08:41
Another batch of Redline Sand lines landed in my queue flagged "Unit price above contract rate". All RL100. That is every invoice since February now. Do you want me to keep disputing them or is there a new rate I don't have?

**Clint Johnson** 08:52
Keep disputing. RLS-2026 loaded on January 1 with the 2 percent escalation and that is the rate in the contract (CLM-00044). They are invoicing about 8.5 percent over book on RL100, call it six dollars a ton. I've raised it with their account manager twice.

**Renee Alvarado (AP)** 08:55
OK. For the record the RL4070 lines are fine, it's only the 100 mesh.

**Clint Johnson** 08:57
Yes, which is why I think it is a price-list error on their side rather than a deliberate increase. V_PRICEBOOK_VARIANCE filtered to Redline shows it line by line if anyone needs the list.

## 2026-07-09

**Jessica Whitaker** 10:14
First proper cut of the corrosion inhibitor spend using the taxonomy views instead of the cost code. Same generic product, SCM-01-01-001, water-soluble filming amine. CorroShield CS-7000 from Corrosion Control Chem is about $16.40 a gallon in totes. CorroGuard BC-220 from Basin Chemical is about $19.80 a gallon in totes. Same chemistry, same spec sheet claims, 21 percent apart.

**Hector Brown** 10:20
And look at the pails. BC-220 5 gal pails come out around $23 a gallon once you convert. Drums about $21.

**Jessica Whitaker** 10:22
Who is ordering pails of corrosion inhibitor?

**Marcus Pena (Completions)** 10:31
Pumpers in the Delaware. They keep pails on the truck for batch treating wells that are not on continuous injection. It's convenience, not chemistry.

**Jessica Whitaker** 10:34
A tote on a skid with a transfer pump at the battery solves that. I'm putting it in the Q3 category review.

**Hector Brown** 10:36
For anyone following along: the per-gallon numbers are STD_UNIT_PRICE_USD in V_INVOICE_LINE_CLASSIFIED. UNIT_PRICE_USD is per tote or per drum or per pail and is not comparable.

## 2026-07-14

**Hector Brown** 14:02
Steward queue status for the month. About 8 percent of 2026 line spend still has no approved generic product. More than half of that is rental equipment, the rest is distributor stuff. The usual suspects: RENTAL EQUIP PER TICKET, EQUIPMENT RENTAL - SEE ATTACHED, MISC SUPPLIES, PART# 44-1093.

**Clint Johnson** 14:05
PART# 44-1093 again? Did we ever find out what that is?

**Hector Brown** 14:08
Three different distributors use the same part number for three different things. Without the field ticket attachment I cannot classify it, so it stays Unclassified rather than guessed. ML suggested a mapping for a couple of them and those sit in Needs review until I see evidence.

**Jessica Whitaker** 14:11
Reminder that Needs review does not count as classified. Only Approved does.

## 2026-07-21

**Clint Johnson** 09:17
Casing. I pulled every 2025 and 2026 line approved to Production casing 5-1/2 in 20 lb/ft P-110 BTC. Six distributors, six wordings for the same pipe: "CSG 5.500 20.00 P110 BTC R3", "5-1/2in 20# P-110 BTC casing, per ft", "CASING 5 1/2" 20.00# P-110 BTC RANGE 3 (jt)", "Prod csg 5.5 x 20 P110 BTC-M, ft", "OCTG 5.5 20PPF P110 BUTTRESS R3 PE", "5.500 OD 20# P110 BTC SMLS casing / ft". Half bill per joint, half per foot.

**Marcus Pena (Completions)** 09:21
What are you using for a joint?

**Clint Johnson** 09:23
42 ft, Range 3 average. That is the conversion factor on the classification row. Tubing joints are 31. Once it's all dollars per foot the spread across the distributors is north of 12 percent against a $42.60 benchmark. Nobody could see that when three of them billed per joint.

**Marcus Pena (Completions)** 09:26
Drilling will want that before the Q4 OCTG RFQ.

## 2026-07-28

**Renee Alvarado (AP)** 11:05
Audit asked me to reconcile 2024 OpenInvoice totals to SAP. There's no ERP invoice id on anything before 2025. Is that a load problem?

**Hector Brown** 11:12
No, that is how it is. ERP_INVOICE_ID only exists from the January 2025 integration upgrade, when SAP started stamping the INV number back onto the OpenInvoice header. Before that ERP_MATCH_STATUS says "Legacy - Coupa id only" and you go through COUPA_DOC_ID in your Coupa extract. For 2025 and 2026 the header total equals SPEND_INVOICE.AMOUNT_USD exactly, we check it on every load.

**Renee Alvarado (AP)** 11:14
Got it. I'll do 2024 through Coupa.

## 2026-08-04

**Jessica Whitaker** 15:40
Finance asked why chemicals is suddenly a topic when the Chemicals category total in spend analytics was flat year over year. Because SPEND_INVOICE shows Corrosion Control Chem and Basin Chemical as the same thing: "Chemicals", LOE-CHEM, one amount per invoice. The product, the pack and the price per gallon only exist on the OpenInvoice line, and the generic product only exists because of the classification table.

**Hector Brown** 15:44
This is the slide for the VP. Cost codes tell you where the money landed. The taxonomy tells you what you bought.

## 2026-08-11

**Marcus Pena (Completions)** 09:02
Planning is building the Q3 reforecast (version date 20 August). They want a plus 10 percent proppant price sensitivity on the Delaware program. Can we get completion spend per lateral foot by generic product for the 2025-26 wells instead of per AFE?

**Clint Johnson** 09:15
Yes. V_AFE_PRODUCT_COST gives spend and tons by AFE and generic product. Join to WVJOB on AFE_NUMBER for the completion job, OD_AFE_HEADER for the AFE, and WELL_MASTER for LATERAL_LENGTH_FT. Then it's dollars per foot and tons per foot by product. The 100 mesh line is the one that moves with a 10 percent price change.

**Marcus Pena (Completions)** 09:18
Perfect. Use PLAN_VERSION = '2026 Q3 Reforecast' from PLAN_PRODUCTION_CAPEX and the Proppant cost category in AFE_PROPOSED_LINE for the planned side.

## 2026-08-18

**Clint Johnson** 13:27
Caution on the 100 mesh comparison. Monahans MP-100 looks like the cheapest sand on the planet at about 14 percent under benchmark, but that is FOB Monahans. Their last-mile trucking and transload are separate lines classified to Proppant last-mile logistics. Add those back and Monahans is not the cheap option. Kermit FracMax 100 is delivered to pad at benchmark and Redline RL100 is delivered at about 11 percent over, before the overbilling.

**Jessica Whitaker** 13:30
Same trap as the chemical packs. Different basis, not different price.

## 2026-08-21

**Hector Brown** 08:50
One year of taxonomy v3.0 today. Reminder of the rules: Rule and Spec sheet review mappings cite the data sheet or the Exhibit B in SOURCE_DOCUMENT. Steward mappings need a note. ML suggestions wait in Needs review. If you cannot name the spec, it stays Unclassified.

## 2026-08-27

**Jessica Whitaker** 16:12
Drafting the chemicals category review. Headline: savings at best observed price on the water-soluble corrosion inhibitor for 2025 come to well over half a million dollars, from V_SUPPLIER_ALTERNATIVES. Recommendation is consolidate on Corrosion Control Chem totes and bulk and run an RFP in Q4 with both suppliers quoting per gallon on the generic spec, not per pack.

**Hector Brown** 16:15
Add scale inhibitor. BasinScale BS-310 runs about 11 percent over ScaleGuard SG-2200 per gallon. H2S scavenger is basically at parity between the two, so leave that alone.

**Jessica Whitaker** 16:17
Already in. Oil-soluble batch inhibitor is about 10 percent apart too, smaller volume.

## 2026-09-02

**Renee Alvarado (AP)** 10:08
Heads up, Basin Chemical submitted this week's invoices as "BASIN CHEMICAL" in caps and last week as "Basin Chemical LLC". Same vendor?

**Hector Brown** 10:10
Same LIFNR, 0000100040. SUPPLIER_NAME_AS_SUBMITTED is free text. Always group by LIFNR or by OI_SUPPLIER.SUPPLIER_NAME.

## 2026-09-09

**Hector Brown** 09:33
Rental cleanup note. "Frac tank rental, 500 bbl, monthly" and "CREW TRAILER MONTHLY" are quantity in months. Conversion is 30 so the standard quantity is days and the price compares to the daily-rate vendors. Weekly genset and telehandler lines convert at 7.

**Clint Johnson** 09:35
And the fuel surcharge and standby lines stay out of the unit price views, right?

**Hector Brown** 09:36
Right. Fees & surcharges is its own family. They show up in total invoice spend and nowhere else.

## 2026-09-16

**Clint Johnson** 14:44
Redline update. Still above book on every RL100 invoice since February. More than half of their 2026 RL100 lines are Disputed now. Renee, can we short-pay to the book rate instead of holding the whole invoice?

**Renee Alvarado (AP)** 14:49
Policy is Disputed until the supplier issues a credit or Supply Chain approves the price. Short-pay needs your sign-off per line.

**Clint Johnson** 14:52
I'll sign. And I'm escalating to their VP. The contract runs to 2028, they should want to fix this.

## 2026-09-23

**Marcus Pena (Completions)** 11:20
Lateral-foot numbers are in for the Delaware 2025-26 wells. Proppant tons per lateral foot are consistent across the pads, so the plus 10 percent sensitivity is almost entirely price. Thanks for the view, that would have been a two-week spreadsheet exercise last year.

**Clint Johnson** 11:24
Send me the AFE list and I'll check nothing is sitting in Hector's queue for those wells. Unclassified rental lines would understate the per-foot cost.

**Hector Brown** 11:26
Rental is where the backlog is, so yes, check.

## 2026-09-29

**Jessica Whitaker** 09:05
Chemicals category review memo goes to Dale on Friday. Thanks all. The Spend Cube app has the price dispersion and pricebook variance tabs if he wants to click through.

**Hector Brown** 09:08
And the classification queue tab. I would like the 8 percent to be 5 by year end, which means field ticket attachments on the rental invoices.

**Renee Alvarado (AP)** 09:10
I'll add the attachment requirement to the supplier onboarding note.
