# Halcyon Specialty Distribution — POC Design

Fictional company: **Halcyon Specialty Distribution (HSD)**, a US specialty pharmaceutical
distributor. Buys oncology, immunology, GLP-1, rare disease and vaccine products from
manufacturers and delivers them to health systems, oncology practices, infusion centers,
specialty pharmacies and retail chains from six distribution centers.

Built for the McKesson / Tiger Analytics conversation. No prospect names appear anywhere.

- Snowflake database `HALCYON_POC`, schema `SPECIALTY_OPS`
- Demo "today": **2026-09-25** (latest complete week ends 2026-09-20)
- Data span: 2025-01-01 through 2026-09-25
- Seed: 20260925 (fully deterministic)

## Persona

**Director of Customer Supply Operations.** Owns the daily question "which customers and
products need intervention today, and what do we do about it." Measured on line fill rate,
OTIF, backorder aging, cold chain integrity, expiry write-offs, chargeback recovery, and
retention of contracted customers. Works across the DC network, account management, and
manufacturer relations.

Secondary personas: Regional DC operations manager, Contracts and Chargebacks analyst,
Strategic account manager.

## Tables (20)

Dimensions: CALENDAR, DISTRIBUTION_CENTERS, MANUFACTURERS, GPOS, PRODUCTS, CUSTOMERS,
CUSTOMER_SITES, CONTRACT_PRICES

Facts: ORDERS, ORDER_LINES, SHIPMENTS, COLD_CHAIN_EVENTS, BACKORDERS, INVENTORY_SNAPSHOTS,
CUSTOMER_ALLOCATIONS, RETURNS, CHARGEBACKS, SERVICE_CASES

Metadata: DATA_DICTIONARY

Views (9): V_ORDER_LINE_DETAIL, V_FILL_RATE_CUSTOMER_MONTH, V_CUSTOMER_HEALTH,
V_DC_SERVICE_PERFORMANCE, V_INVENTORY_RISK, V_ALLOCATION_UTILIZATION,
V_COLD_CHAIN_EXCURSIONS, V_CHARGEBACK_SUMMARY, V_BACKORDER_AGING

## Engineered control points

1. **GLP-1 allocation squeeze (hero).** Manufacturer *Veltrix Biopharma* cut Halcyon's
   allocation of GLP-1 brand *Vanterra*: held flat through June and July while demand grew,
   then cut in August and again in September (21.8K units in May to 17.3K in August and 14.2K
   in September). Halcyon allocates on historical share, so fast-growing customers are
   squeezed hardest. *Bayview Regional Health* (Strategic, $48.2M ACV, renews 2026-12-15)
   sees overall line fill drop from 92% to 83% and Vanterra line fill to 57%, 35 backorders
   age past 14 days ($1.76M), 14 high severity cases stay open, and its non-allocated order
   value falls ~18% since late July, an early sign it is moving categories to another
   distributor. *Northgate Health Alliance* and *Cascade Oncology Partners* show the same
   pattern at smaller scale.

2. **Cold chain excursion cluster at Memphis.** DC-MEM switched about 60% of refrigerated
   packouts to `GEL_PACK_STD` packaging in June 2026. Its refrigerated excursion rate runs
   4.2% in July and August against 1.3% at the next DC, gel pack packout excursions run
   17.7% against 0.7% for `PHASE_CHANGE_48H`, `TEMP_EXCURSION` returns climb, and $1.41M of
   product is quarantined or destroyed, all of it from gel pack shipments.

3. **Short-dated oncology inventory at Dallas.** DC-DAL holds 835 units ($2.38M WAC) of the
   oncology infusion product *Oncaryl* expiring within 90 days, 313 days of supply, with
   204 more on order, after monthly demand from Dallas-served sites fell from ~750 to ~90
   units in May 2026. Three Houston oncology practices served by DC-DAL still order it, so a
   short-dated sale can avoid the write-off.

4. **Chargeback disputes at Keldon Pharma.** After contract price file 2026-04A loaded on
   2026-04-15, Keldon's chargeback dispute rate runs ~24% versus ~4% before and ~4% across
   other manufacturers, driven by `PRICE_MISMATCH` and `INELIGIBLE_CUSTOMER`. About $1.5M
   sits in disputed or rejected status.

5. **Backorder aging drives severe service cases.** Every HIGH or CRITICAL product
   availability case is attached to a backorder older than 14 days. The customers with the
   oldest open backorders are the ones with the most open cases.

6. **Auto-replenishment outperforms (soft).** Sites on the `AUTO_REPLENISH` channel have
   higher line fill and far fewer STAT orders than portal or phone orderers. Expansion play.

## Demo arc (45 minutes with Tiger)

1. Chat: "which contracted customers renewing in the next 120 days show deteriorating
   service?" surfaces Bayview at the top with reason codes.
2. Drill: Bayview fill rate by therapeutic class, then Vanterra allocation requested vs
   allocated vs consumed, then aging backorders, then the drop in non-GLP-1 volume.
3. Live App "Customer Supply Rescue Workbench": queue of at-risk contracted customers,
   scenario lab (reallocate fair share, expedite from another DC, commercial credit,
   account team hours), implementation plan with action log.
4. Agent: weekly customer risk digest plus daily alerts on critical excursions, backorders
   crossing 14 days, exec escalations, and allocation shortfall.
5. Close: same pattern on the cold chain and chargeback stories in two questions each.
