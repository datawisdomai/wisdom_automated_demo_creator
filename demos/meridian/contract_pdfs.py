"""Render signed-contract PDFs from the generated data (stretch goal of the Meridian demo).

`demo docs meridian` calls `render(spec, out_dir)` through the `generated_documents` hook in
demo.yaml. The Halvorsen Therapeutics chain (MSA + three amendments) plus about twenty other
agreements are rendered so every value on a PDF equals the CONTRACTS / CONTRACT_LINE_ITEMS /
CONTRACT_BILLING_SCHEDULE rows it came from. File names equal CONTRACTS.PDF_FILE_NAME.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from demo_creator.documents import render_pdf

HERO_NUMBER = "MCN-2025-0142"
OTHER_CHAINS = 20
COMPANY = "Meridian Clinician Network, Inc."
ADDRESS = "400 Montgomery Street, Suite 1200, San Francisco, CA 94104"


def _money(x: float) -> str:
    return f"${x:,.2f}"


def _date(d) -> str:
    return pd.Timestamp(d).strftime("%B %-d, %Y")


def _doc_markdown(doc: pd.Series, cust: pd.Series, lines: pd.DataFrame, sched: pd.DataFrame, original: pd.Series | None, prev: pd.Series | None) -> str:
    is_amend = int(doc.AMENDMENT_NUMBER) > 0
    title = (f"Amendment No. {int(doc.AMENDMENT_NUMBER)} to Master Services Agreement {original.CONTRACT_NUMBER}" if is_amend
             else f"Master Services Agreement {doc.CONTRACT_NUMBER}")
    out = [f"# {title}",
           f"Letterhead: {COMPANY}, {ADDRESS}",
           f"Agreement Number: {doc.CONTRACT_NUMBER}",
           f"DocuSign Envelope: {doc.DOCUSIGN_ENVELOPE_ID}",
           f"Executed: {_date(doc.SIGNED_DATE)}",
           ""]
    if is_amend:
        out += ["## Recitals",
                f"This Amendment No. {int(doc.AMENDMENT_NUMBER)} (the \"Amendment\") is entered into as of {_date(doc.SIGNED_DATE)} between {COMPANY} (\"Meridian\") and {cust.CUSTOMER_NAME} (\"Customer\") and amends the Master Services Agreement numbered {original.CONTRACT_NUMBER} executed on {_date(original.SIGNED_DATE)}"
                + (f", as previously amended through Amendment No. {int(prev.AMENDMENT_NUMBER)}" if prev is not None and int(prev.AMENDMENT_NUMBER) > 0 else "")
                + " (the \"Agreement\"). Capitalised terms have the meaning given in the Agreement. Except as expressly amended below, the Agreement remains in full force and effect.",
                "",
                "## 1. Amended Terms"]
        changes = []
        if prev is not None:
            if float(doc.TOTAL_CONTRACT_VALUE) != float(prev.TOTAL_CONTRACT_VALUE):
                changes.append(f"Section 4 (Fees) is amended so that the Total Contract Value is restated from {_money(float(prev.TOTAL_CONTRACT_VALUE))} to **{_money(float(doc.TOTAL_CONTRACT_VALUE))}**.")
            if pd.Timestamp(doc.END_DATE) != pd.Timestamp(prev.END_DATE):
                changes.append(f"Section 3 (Term) is amended so that the Term ends on **{_date(doc.END_DATE)}** instead of {_date(prev.END_DATE)} ({int(doc.TERM_MONTHS)} months from the Effective Date).")
            if doc.PAYMENT_TERMS != prev.PAYMENT_TERMS:
                changes.append(f"Section 5 (Payment) is amended so that invoices are payable **{doc.PAYMENT_TERMS}** instead of {prev.PAYMENT_TERMS}.")
            if doc.BILLING_FREQUENCY != prev.BILLING_FREQUENCY:
                changes.append(f"Section 5 (Payment) is amended so that fees are invoiced on a **{doc.BILLING_FREQUENCY}** basis instead of {prev.BILLING_FREQUENCY}; Exhibit B is replaced in its entirety.")
        changes.append("Exhibit A (Services and Fees) and Exhibit B (Billing Schedule) are replaced in their entirety by the Exhibits attached to this Amendment.")
        if isinstance(doc.SPECIAL_TERMS, str) and doc.SPECIAL_TERMS:
            changes.append(doc.SPECIAL_TERMS)
        out += [f"- {c}" for c in changes] + [""]
    else:
        out += ["## 1. Parties and Services",
                f"This Master Services Agreement (the \"Agreement\") is entered into as of {_date(doc.SIGNED_DATE)} between {COMPANY} (\"Meridian\") and {cust.CUSTOMER_NAME} (\"Customer\"). Meridian will provide the services described in Exhibit A on the Meridian clinician network in accordance with this Agreement.",
                "",
                "## 2. Effective Date and Term",
                f"The Effective Date is {_date(doc.EFFECTIVE_DATE)}. The Term runs {int(doc.TERM_MONTHS)} months from the Effective Date and ends on {_date(doc.END_DATE)}."
                + (" This Agreement renews automatically for successive twelve-month periods unless either party gives written notice of non-renewal" if bool(doc.AUTO_RENEW) else " This Agreement does not renew automatically")
                + f" at least {int(doc.CANCELLATION_NOTICE_DAYS)} days before the end of the then-current Term.",
                "",
                "## 3. Fees",
                f"The Total Contract Value for the Term is **{_money(float(doc.TOTAL_CONTRACT_VALUE))}** ({doc.CURRENCY}), as itemised in Exhibit A.",
                "",
                "## 4. Invoicing and Payment",
                f"Fees are invoiced on a **{doc.BILLING_FREQUENCY}** basis per the schedule in Exhibit B. Invoices are payable **{doc.PAYMENT_TERMS}** from the invoice date. Late amounts accrue interest at 1.0% per month.",
                ""]
        if isinstance(doc.SPECIAL_TERMS, str) and doc.SPECIAL_TERMS:
            out += ["## 5. Special Terms", doc.SPECIAL_TERMS, ""]
    # exhibits
    out += [f"## Exhibit A — Services and Fees (Total Contract Value {_money(float(doc.TOTAL_CONTRACT_VALUE))})",
            "| # | Service | Specialty | Quantity | Unit price | Amount | Service period |",
            "|---|---|---|---|---|---|---|"]
    for _, l in lines.sort_values("LINE_NUMBER").iterrows():
        out.append(f"| {int(l.LINE_NUMBER)} | {l.PRODUCT_NAME} | {l.SPECIALTY_TARGETED if isinstance(l.SPECIALTY_TARGETED, str) else '-'} | {int(l.QUANTITY)} | {_money(float(l.UNIT_PRICE))} | {_money(float(l.LINE_AMOUNT))} | {_date(l.START_DATE)} to {_date(l.END_DATE)} |")
    out += ["", "## Exhibit B — Billing Schedule",
            "| Milestone | Description | Invoice date | Amount |",
            "|---|---|---|---|"]
    for _, m in sched.sort_values("MILESTONE_NUMBER").iterrows():
        out.append(f"| {int(m.MILESTONE_NUMBER)} | {m.MILESTONE_DESCRIPTION} | {_date(m.SCHEDULED_DATE)} | {_money(float(m.SCHEDULED_AMOUNT))} |")
    out += ["", "## Signatures",
            f"Signed electronically via DocuSign (envelope {doc.DOCUSIGN_ENVELOPE_ID}) on {_date(doc.SIGNED_DATE)}.",
            "",
            "| For Meridian Clinician Network, Inc. | For the Customer |",
            "|---|---|",
            f"| Elena Marsh, Chief Revenue Officer | {doc.SIGNATORY_NAME} |",
            f"| {_date(doc.SIGNED_DATE)} | {_date(doc.SIGNED_DATE)} |"]
    return "\n".join(out)


def render(spec, out_dir: Path, *, echo: bool = True) -> list[dict]:
    cache = spec.paths
    contracts = pd.read_parquet(cache.parquet("CONTRACTS"))
    customers = pd.read_parquet(cache.parquet("CUSTOMERS")).set_index("CUSTOMER_ID")
    lines = pd.read_parquet(cache.parquet("CONTRACT_LINE_ITEMS"))
    sched = pd.read_parquet(cache.parquet("CONTRACT_BILLING_SCHEDULE"))
    contracts["CHAIN"] = contracts.PARENT_CONTRACT_ID.fillna(contracts.CONTRACT_ID)
    hero_chain = contracts[contracts.CONTRACT_NUMBER == HERO_NUMBER].CONTRACT_ID.iloc[0]
    # other chains: amended ones first (they tell the story), deterministic order
    amended = contracts.groupby("CHAIN").AMENDMENT_NUMBER.max()
    others = [c for c in amended.sort_values(ascending=False).index if c != hero_chain][:OTHER_CHAINS]
    chains = [hero_chain] + others
    docs = contracts[contracts.CHAIN.isin(chains)].sort_values(["CHAIN", "AMENDMENT_NUMBER"])
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / "_md"
    tmp.mkdir(exist_ok=True)
    results = []
    for chain_id, group in docs.groupby("CHAIN", sort=False):
        original = group[group.AMENDMENT_NUMBER == 0].iloc[0]
        prev = None
        for _, d in group.sort_values("AMENDMENT_NUMBER").iterrows():
            md = _doc_markdown(d, customers.loc[d.CUSTOMER_ID], lines[lines.CONTRACT_ID == d.CONTRACT_ID], sched[sched.CONTRACT_ID == d.CONTRACT_ID],
                               original if d.AMENDMENT_NUMBER > 0 else None, prev)
            md_path = tmp / (Path(d.PDF_FILE_NAME).stem + ".md")
            md_path.write_text(md)
            pdf = out_dir / d.PDF_FILE_NAME
            render_pdf(md_path, pdf, title=Path(d.PDF_FILE_NAME).stem)
            results.append({"file": pdf.name, "contract_number": d.CONTRACT_NUMBER, "customer": customers.loc[d.CUSTOMER_ID].CUSTOMER_NAME, "ok": True})
            prev = d
    if echo:
        print(f"  rendered {len(results)} contract PDFs for {len(chains)} agreements -> {out_dir}")
    return results
