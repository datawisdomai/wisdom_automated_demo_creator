# Chemicals Category Review — Q3 2026

Letterhead: Pecos Ridge Energy LLC — Supply Chain Management
To: Dale Rutherford, VP Supply Chain
From: Jessica Whitaker, Category Manager — Production and Completion Chemicals, Water Logistics
Copy: Clint Johnson (Category Manager, Proppant and OCTG); Hector Brown (Supply Chain Data Steward)
Date: 2026-10-02
Reference: SCM-CR-2026Q3-CHEM
Classification: Internal

## 1. Summary

This is the first chemicals category review built on the generic product taxonomy (v3.0) applied to OpenInvoice line items rather than on the accounting cost code. The LOE-CHEM cost code and the "Chemicals" supplier category showed a flat category total for 2025 and told us nothing else. The line-level view shows that our single largest production chemical, water-soluble filming-amine corrosion inhibitor (taxonomy node SCM-01-01-001), is bought from two suppliers at a per-gallon gap of more than 20 percent, with a further premium on small packs that nobody had authorised. Savings at the best observed price for that one product in 2025 come to well over half a million dollars. Smaller but real dispersion exists on scale inhibitor and oil-soluble batch inhibitor; H2S scavenger is at parity between the two suppliers. I recommend consolidating corrosion inhibitor on the lower-priced supplier in totes and bulk, converting pail and drum demand to tote-and-pump setups, and running a Q4 RFP in which both suppliers quote per gallon against the generic specification.

## 2. What the taxonomy revealed on corrosion inhibitor

Both suppliers hold a Chemical Supply Agreement and a loaded price book in OpenInvoice.

| Supplier | LIFNR | Contract | Price book | Supplier item | Pack | 2025 standard unit price (per gal) | Versus 2025 benchmark ($16.40) |
|---|---|---|---|---|---|---|---|
| Corrosion Control Chem LLC | 0000100039 | CLM-00040 | CCC-PB-2025A | CorroShield CS-7000 bulk delivery (gal) | Bulk | about $15.91 | about 3% below |
| Corrosion Control Chem LLC | 0000100039 | CLM-00040 | CCC-PB-2025A | CorroShield CS-7000 Corrosion Inhibitor 330 gal tote | Tote (330 gal) | about $16.40 | at benchmark |
| Corrosion Control Chem LLC | 0000100039 | CLM-00040 | CCC-PB-2025A | CorroShield CS-7000 Corrosion Inhibitor 55 gal drum | Drum (55 gal) | about $17.55 | about 7% above |
| Basin Chemical LLC | 0000100040 | CLM-00041 | BSN-PB-2025 | CorroGuard BC-220 CI 330 GAL TOTE | Tote (330 gal) | about $19.84 | about 21% above |
| Basin Chemical LLC | 0000100040 | CLM-00041 | BSN-PB-2025 | CorroGuard BC-220 CI 55 GAL DRUM | Drum (55 gal) | about $21.16 | about 29% above |
| Basin Chemical LLC | 0000100040 | CLM-00041 | BSN-PB-2025 | CORROGUARD BC-220 5 GAL PAIL | Pail (5 gal) | about $23.29 | about 42% above |

Observations:

- Tote to tote, Basin Chemical is about 21 percent more expensive than Corrosion Control Chem for the same generic product. Both technical data sheets describe a water-soluble imidazoline/quaternary amine filming inhibitor for continuous or batch treatment; the field has used them interchangeably on the same wells for years.
- Both suppliers are invoicing at their contracted price book rates. This is not a compliance problem; it is a sourcing decision that was never made because the two items were invisible inside one cost code.
- The dispersion is entirely a function of which supplier the field pumper calls and which pack is on the truck. There is no basin or well-type pattern behind it.
- Savings at the best observed price (V_SUPPLIER_ALTERNATIVES, 2025, SCM-01-01-001) are well over half a million dollars: the volume bought from Basin Chemical, and the drum and pail volume from both suppliers, repriced at the lowest supplier standard unit price observed in the year.

## 3. The pack premium

Small packs carry a premium on top of the supplier gap. Corrosion Control Chem charges about 7 percent more per gallon for a drum than for a tote; Basin Chemical charges about 7 percent more for a drum and about 17 percent more for a pail than for its own tote. The pail is the worst case: at about $23.29 per gallon it is roughly 46 percent above Corrosion Control Chem's bulk price for the same product.

Pails and drums are bought for convenience. Pumpers keep them on the truck for batch treating wells that are not on continuous injection, mostly in the Delaware Basin. A 330 gallon tote on a skid with a transfer pump at the tank battery removes the need for pails on almost every lease. Completions and production operations have agreed to trial tote-and-pump setups on the Delaware batch-treated wells in Q4.

## 4. Scale inhibitor, H2S scavenger and other products

The same comparison across the chemicals family, using the 2025 standard unit prices:

| Generic product | Node | Corrosion Control Chem item | Basin Chemical item | Observation |
|---|---|---|---|---|
| Scale inhibitor, phosphonate, continuous injection | SCM-01-02-001 | ScaleGuard SG-2200 Phosphonate Scale Inhibitor tote (about 2% below benchmark) | BasinScale BS-310 Inhibitor TOTE (about 9% above benchmark) | About 11 percent apart per gallon; same continuous-injection phosphonate specification; consolidation candidate |
| Corrosion inhibitor, oil-soluble, batch | SCM-01-01-002 | CorroShield CS-7100 Oil-Soluble Batch Inhibitor 55 gal drum (about 2% above benchmark) | CorroGuard BC-240 OS Batch 55 GAL DRUM (about 12% above benchmark) | About 10 percent apart; drums only from both suppliers; smaller volume |
| H2S scavenger, triazine | SCM-01-04-001 | SulfiStop HS-9000 Triazine Scavenger 330 gal tote (about 3% above benchmark) | Basin H2S-Trap BH-700 TOTE (about 6% above benchmark) | Effectively at parity; no action beyond the RFP |
| Paraffin solvent, aromatic | SCM-01-03-001 | ParaClear PX-500 Aromatic Solvent 55 gal drum (at benchmark) | Basin ParaSolv BP-150 55 GAL DRUM (about 8% above benchmark) | About 8 percent apart; both in drums; convert to tote where volume justifies |
| Completion fluids (friction reducer, acid, clay stabilizer, breaker) | SCM-01-08-xxx | Bulk delivery at or just below benchmark | Bulk delivery at benchmark | No dispersion; bulk pricing by the gallon already |

Products sold by only one of the two suppliers (biocide THPS, water clarifier, oxygen scavenger, demulsifier, foamer, methanol) show no supplier dispersion and are priced within a few percent of benchmark. They are in scope for the RFP only to establish a second qualified source.

## 5. Recommendations

- Consolidate water-soluble corrosion inhibitor on Corrosion Control Chem LLC (CorroShield CS-7000) in totes and bulk delivery for 2027, subject to the RFP result. Basin Chemical remains qualified as the second source.
- Convert pail and drum demand to tote-and-pump: no 5 gal pails of corrosion inhibitor from January 2027 except by category manager exception; drums only where a tote cannot be sited.
- Run a Q4 2026 RFP for the chemicals family with both suppliers (and one additional qualified bidder) quoting per gallon against the generic product specification and standard UOM, not per pack. Award by generic product, not by supplier relationship.
- Enforce price books in OpenInvoice for both chemical suppliers so that any pack or price not in the exhibit is rejected at submission rather than approved in the field.
- Keep the benchmark column on the taxonomy current: the 2025 benchmarks are the reference for this review; the RFP outcome becomes the 2027 benchmark.

## 6. Next steps

| Action | Owner | Due |
|---|---|---|
| Issue chemicals RFP (per-gallon pricing on generic specification) | Jessica Whitaker | 2026-11-15 |
| Tote-and-pump trial on Delaware batch-treated wells | Marcus Pena (Completions) with Production Operations | 2026-12-31 |
| Price book enforcement switched on for CCC-PB-2025A and BSN-PB-2025 in OpenInvoice | Hector Brown with AP | 2026-11-01 |
| Steward backlog: rental and distributor items from about 8 percent to 5 percent of 2026 line spend; field ticket attachment required on rental invoices | Hector Brown | 2026-12-31 |
| Extend the review to proppant (Redline Sand RL100 invoiced above the RLS-2026 book rate since February; FOB versus delivered basis across the three mines) and OCTG (per-joint versus per-foot billing on 5-1/2 in 20 lb/ft P-110 casing) | Clint Johnson | Q4 2026 category reviews |
| Cost per lateral foot by generic product for the 2025-26 wells, feeding the plus 10 percent proppant sensitivity against the 2026 Q3 Reforecast | Clint Johnson with Marcus Pena | 2026-10-31 |

## 7. Data notes

All figures come from PECOS_RIDGE_SCM_OPENINVOICE.OPENINVOICE: standard unit prices from V_INVOICE_LINE_CLASSIFIED (STD_UNIT_PRICE_USD, volume weighted by year), supplier comparison and savings from V_SUPPLIER_ALTERNATIVES, contract rates from V_PRICEBOOK_VARIANCE. Only lines with an approved classification are included; fees and surcharges are excluded from every unit price. Prices are 2025 invoice prices; 2026 prices are about 3 percent higher under the escalation clauses in both price books. The classification evidence (technical data sheets and MSA Exhibit B pricing schedules) is in the supplier document archive.

Prepared by Supply Chain Management. Questions to #supply-chain-category.
