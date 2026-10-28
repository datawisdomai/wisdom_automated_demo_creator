# Request from Jeff (partner, digitz) — 2026-10-19

Domain to enhance: https://digitz.wisdom.ai/domains/ET_DOMAIN_4804a0b2ffcd484ab6d7cf410dceed55 (the "O&G" / Pecos Ridge domain),
with supply chain data and unstructured data.

What they are trying to accomplish:
- They have several years of invoice data from Enverus OpenInvoice in a database.
- The cost codes, supplier categories, etc. that already label the data are useful for accounting, but are not granular
  enough for supply chain to analyze products, costs, and quantities from alternative suppliers, etc.
- They need to be able to analyze costs categorized by the generic name and/or use of the products and services on the
  line items, not the vendor's marketing product name. (This is context that doesn't exist today.)
- A future step would then be to join that invoice data to operational data from sources like WellView and forecast data
  to see the impact of potential changes in pricing.

Chick's additions: use our Snowflake account (XMSPMYE-PAB51256) through a new connection; keep every new row in sync with
the Pecos Ridge data already in the domain (real vendors, wells, AFEs, properties, contracts); unstructured = supplier
spec sheets and MSA pricing exhibits in S3.
