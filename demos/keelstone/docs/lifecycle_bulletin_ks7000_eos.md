# Product Lifecycle Bulletin PLB-2026-014: KS-7000 Family End of Support

Letterhead: Keelstone Data Systems — Product Management
Bulletin: PLB-2026-014
Issued: 2026-06-15
Applies to: KS-7200, KS-7400 and KS-7600 all-flash arrays (product family KS-7000)
Audience: Customers, channel partners, Keelstone sales and support
Owner: Aisha Haddad, Director of Product Lifecycle Management

## Announcement

Keelstone Data Systems announces the end of support for the KS-7000 all-flash array family. The KS-7200, KS-7400 and KS-7600 reached end of sale on 31 October 2025. End of support is 31 January 2027. After that date Keelstone will no longer provide hardware replacement, engineering support or KeelOS releases for these systems under standard support contracts.

## Milestones

| Milestone | Date | Meaning |
|---|---|---|
| End of sale | 2025-10-31 | Last date the KS-7000 family could be ordered. Capacity expansions remain orderable until end of support. |
| End of support announcement | 2026-06-15 | This bulletin. |
| Last KeelOS release line | 9.14.x | 9.14.3 (released 2026-09-15) is the recommended and final supported release for the family. |
| End of support | 2027-01-31 | Standard, Premium and Mission Critical support contracts cannot extend beyond this date. |
| Extended support available until | 2028-01-31 | KS-7000 Extended Support (SUP-EXT7K): parts on a best-effort basis, no new firmware, priority 1 and 2 cases only. |

## What this means for customers

- Support contracts on KS-7000 systems will be co-termed to end no later than 31 January 2027. Renewal quotes issued after this bulletin reflect that date.
- KeelOS Core subscriptions on KS-7000 systems remain valid until the system is decommissioned or migrated; the subscription transfers to the replacement array at no charge when the migration is through Keelstone or an authorised partner.
- Customers running KeelOS 9.14.2 should upgrade to 9.14.3 at the earliest maintenance window. Refer to knowledge base article KB-2026-0917 for the controller takeover and giveback defect that 9.14.3 resolves.

## Migration paths

| Current system | Recommended replacement | Notes |
|---|---|---|
| KS-7200 | KS-9300 | Same rack footprint; non-disruptive volume move with KeelOS 9.14.3 on both systems |
| KS-7400 | KS-9300 or KS-9500 | KS-9500 recommended above 600 TB raw |
| KS-7600 | KS-9500 or KS-9700 | KS-9700 for database and AI pipeline workloads |

- Migration incentives: trade-in credit of up to 12 percent of the replacement list price for KS-7000 systems returned within 90 days of the new system's install, available until 2027-04-30.
- KS-7000 Extended Support is intended as a bridge of at most twelve months for customers with a signed migration plan. It is not a long-term alternative to migration.

## Partner guidance

- Partners should contact every account with a KS-7000 system and a support contract ending before 2027-01-31 to present the migration path and the Extended Support bridge together.
- Deal registration for KS-9000 replacement systems linked to a KS-7000 serial number receives the standard migration incentive plus the partner migration bonus described in the FY27 partner programme guide.

## Support and contacts

- Lifecycle questions: lifecycle@keelstone.example (fictional).
- Technical questions on 9.14.3 and KB-2026-0917: Keelstone Support via the customer portal, priority as appropriate.
- Commercial questions: your Keelstone account executive or partner of record.
