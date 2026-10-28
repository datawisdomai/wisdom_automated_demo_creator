"""Pull the reference rows the generator needs from the partner's Snowflake (the one we cannot log in to)
through the Wisdom SQL playground on digitz. Read-only. 100 rows per call, so everything is paged with
LIMIT 100 OFFSET n and cached under inputs/ref/<name>.csv; a file that already exists is skipped, so the
script is resumable. Run:  .venv/bin/python demos/pecos_openinvoice/ref_extract.py [--only NAME ...]
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from wisdomai import Client  # noqa: E402

DOMAIN = "ET_DOMAIN_4804a0b2ffcd484ab6d7cf410dceed55"
REF = Path(__file__).resolve().parent / "inputs" / "ref"
PAGE = 100
CATS = "('Chemicals','Sand/Proppant','Tubulars / OCTG','Rental Equipment','Trucking/Water Hauling')"

# name -> (database, select-list, from/where, order-by key)
EXTRACTS: dict[str, tuple[str, str, str, str]] = {
    "s4_vendor_lfa1": ("PECOS_RIDGE_MAINT_SAP", "LIFNR, NAME1, ORT01, REGIO, KTOKK, VENDOR_CATEGORY, ISN_ID, BLOCKED",
                       "S4_VENDOR_LFA1", "LIFNR"),
    "counterparty_master": ("PECOS_RIDGE_CORP_MDM", "COUNTERPARTY_ID, LEGAL_NAME, COUNTERPARTY_TYPE, DUNS_NUMBER, HQ_STATE, CREDIT_RATING",
                            "COUNTERPARTY_MASTER", "COUNTERPARTY_ID"),
    "well_master": ("PECOS_RIDGE_CORP_MDM",
                    "CORP_WELL_ID, API14, WELL_NAME, PAD_ID, DSU_ID, BASIN, PLAY, COUNTY, STATE_CODE, FIELD_NAME, TARGET_FORMATION, "
                    "WELL_TYPE, TRAJECTORY, IS_OPERATED, OPERATOR_NAME, WORKING_INTEREST_PCT, SPUD_DATE, RIG_RELEASE_DATE, "
                    "FIRST_PRODUCTION_DATE, LATERAL_LENGTH_FT, WELL_STATUS, GATHERING_SYSTEM, CTB_FACILITY_ID",
                    "WELL_MASTER", "CORP_WELL_ID"),
    "pad": ("PECOS_RIDGE_CORP_MDM", "PAD_ID, PAD_NAME, DSU_ID, BASIN, STATE_CODE, COUNTY, GATHERING_SYSTEM, CTB_FACILITY_ID, PAD_CONSTRUCTION_DATE",
            "PAD", "PAD_ID"),
    "od_afe_header": ("PECOS_RIDGE_REV_ACCOUNTING",
                      "AFE_NUMBER, CORP_WELL_ID, PROPERTY_NUMBER, AFE_TYPE, AFE_DATE, GROSS_AFE_AMOUNT, COMPANY_WI_DECIMAL, AFE_STATUS",
                      "OD_AFE_HEADER", "AFE_NUMBER"),
    "xwalk_well": ("PECOS_RIDGE_FIN_SAP",
                   "XWALK_ID, CORP_WELL_ID, QUORUM_PROPERTY_NUMBER, KOSTL, PRCTR, MAPPING_STATUS",
                   "ZFI_SYSTEM_XWALK WHERE XWALK_TYPE = 'WELL'", "XWALK_ID"),
    "clm_contract": ("PECOS_RIDGE_PROCUREMENT_SCM",
                     "CLM_CONTRACT_ID, CONTRACT_TITLE, CONTRACT_TYPE, LIFNR, COUNTERPARTY_ID, EFFECTIVE_DATE, EXPIRY_DATE, AUTO_RENEW, "
                     "ANNUAL_VALUE_USD, TERMINATION_NOTICE_DAYS, CONTRACT_OWNER, CONTRACT_STATUS",
                     "CLM_CONTRACT", "CLM_CONTRACT_ID"),
    "sourcing_event": ("PECOS_RIDGE_PROCUREMENT_SCM",
                       "SOURCING_EVENT_ID, EVENT_TYPE, CATEGORY, LAUNCH_DATE, AWARD_DATE, BIDDERS, AWARDED_LIFNR, AWARDED_VALUE_USD, "
                       "BASELINE_VALUE_USD, SAVINGS_USD, PLATFORM", "SOURCING_EVENT", "SOURCING_EVENT_ID"),
    "wvjob": ("PECOS_RIDGE_DRILLING_WELLVIEW",
              "IDREC_JOB, IDWELL, JOB_TYPE, JOB_START_DATE, JOB_END_DATE, RIG_ID, AFE_NUMBER, AFE_AMOUNT_USD, TARGET_DAYS, ACTUAL_DAYS",
              "WVJOB", "IDREC_JOB"),
    "afe_proposed_header": ("PECOS_RIDGE_DEV_PLANNING",
                            "AFE_NUMBER, CORP_WELL_ID, PAD_ID, DSU_ID, AFE_TYPE, AFE_DATE, GROSS_AFE_AMOUNT, COMPANY_WI_DECIMAL, AFE_STATUS",
                            "AFE_PROPOSED_HEADER", "AFE_NUMBER"),
    "afe_proposed_line": ("PECOS_RIDGE_DEV_PLANNING", "AFE_NUMBER, COST_CATEGORY, ESTIMATE_GROSS",
                          "AFE_PROPOSED_LINE", "AFE_NUMBER, COST_CATEGORY"),
    "plan_production_capex": ("PECOS_RIDGE_DEV_PLANNING",
                              "PLAN_VERSION, VERSION_DATE, BASIN, PLAN_MONTH, IS_ACTUAL_MONTH, GROSS_OIL_BOPD, GROSS_GAS_MMCFD, WELLS_TIL, "
                              "DC_CAPEX_MUSD, FACILITIES_CAPEX_MUSD", "PLAN_PRODUCTION_CAPEX", "PLAN_VERSION, BASIN, PLAN_MONTH"),
    # the exact slice: five supply-chain categories, 2025-01 -> 2026-09
    "spend_invoice_exact": ("PECOS_RIDGE_PROCUREMENT_SCM",
                            "INVOICE_ID, PLATFORM, LIFNR, VENDOR_NAME_AS_INVOICED, BUSINESS_UNIT, SPEND_CATEGORY, INVOICE_DATE, AMOUNT_USD, "
                            "PO_NUMBER, AFE_NUMBER, PROPERTY_NUMBER, GL_ACCOUNT, COST_CATEGORY, SOURCE_LEDGER, APPROVAL_STATUS, PAID_DATE",
                            f"SPEND_INVOICE WHERE SPEND_CATEGORY IN {CATS} AND INVOICE_DATE >= '2025-01-01'", "INVOICE_ID"),
    # calibration aggregates for the earlier years
    "spend_invoice_agg": ("PECOS_RIDGE_PROCUREMENT_SCM",
                          "LIFNR, SPEND_CATEGORY, COST_CATEGORY, BUSINESS_UNIT, SOURCE_LEDGER, DATE_TRUNC('MONTH', INVOICE_DATE) AS INVOICE_MONTH, "
                          "COUNT(*) AS INVOICES, SUM(AMOUNT_USD) AS AMOUNT_USD, SUM(CASE WHEN AFE_NUMBER IS NOT NULL THEN 1 ELSE 0 END) AS AFE_INVOICES",
                          f"SPEND_INVOICE WHERE SPEND_CATEGORY IN {CATS} AND INVOICE_DATE >= '2022-01-01' AND INVOICE_DATE < '2025-01-01' "
                          "GROUP BY LIFNR, SPEND_CATEGORY, COST_CATEGORY, BUSINESS_UNIT, SOURCE_LEDGER, DATE_TRUNC('MONTH', INVOICE_DATE)",
                          "LIFNR, SPEND_CATEGORY, COST_CATEGORY, BUSINESS_UNIT, SOURCE_LEDGER, INVOICE_MONTH"),
}


def fetch(client: Client, name: str) -> Path:
    db, cols, src, order = EXTRACTS[name]
    out = REF / f"{name}.csv"
    if out.exists():
        print(f"[skip] {name}: {out.name} exists")
        return out
    tmp = out.with_suffix(".partial.csv")
    rows_written = 0
    offset = 0
    t0 = time.time()
    with tmp.open("w", newline="") as fh:
        writer = None
        while True:
            sql = f"SELECT {cols} FROM {src} ORDER BY {order} LIMIT {PAGE} OFFSET {offset}"
            for attempt in range(4):
                try:
                    r = client.run_sql(DOMAIN, sql, dialect="snowflake", database_name=db)
                    break
                except Exception as e:  # transient playground errors
                    if attempt == 3:
                        raise
                    print(f"  retry {attempt + 1} on {name} offset {offset}: {str(e)[:120]}")
                    time.sleep(5 * (attempt + 1))
            if writer is None:
                writer = csv.writer(fh)
                writer.writerow(r["columns"])
            for row in r["rows"]:
                writer.writerow(row)
            rows_written += len(r["rows"])
            print(f"  {name}: {rows_written} rows ({time.time() - t0:.0f}s)", flush=True)
            if len(r["rows"]) < PAGE:
                break
            offset += PAGE
    tmp.rename(out)
    print(f"[done] {name}: {rows_written} rows -> {out.name}")
    return out


def main(argv: list[str]) -> int:
    only = argv[argv.index("--only") + 1:] if "--only" in argv else list(EXTRACTS)
    REF.mkdir(parents=True, exist_ok=True)
    client = Client.for_deployment("digitz", timeout=120)
    for name in only:
        fetch(client, name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
