"""Read-only per-instrument evidence ledger. No broker execution authority.

Reporting MIC is a regulatory reporting attribute, not proof of execution MIC.
Statuses describe exactly what is evidenced; no status is a trading permission.
"""
from datetime import date

ISINS = ("DE0006231004", "DE0007030009")
STAGES = ("UNVERIFIED", "SOURCE_RETRIEVED", "STRUCTURE_VALIDATED",
          "OFFICIAL_REFERENCE_MATCHED", "INDEPENDENTLY_CORROBORATED",
          "ACCOUNT_SPECIFICALLY_VERIFIED")

def build_instrument_evidence_ledger(reporting_audit, iso_relationship, as_of="2026-11-13"):
    ledger = {"status": "BLOCKED", "as_of": as_of, "instruments": [],
              "trade_ready": False, "order_placement_enabled": False,
              "broker_route_verified": False, "degiro_fee_verified": False,
              "segment_mic_verified": False, "blocks": []}
    try:
        date.fromisoformat(as_of)
    except (TypeError, ValueError):
        ledger["blocks"].append("INVALID_AS_OF_DATE")
        return ledger
    if not isinstance(reporting_audit, dict) or not isinstance(iso_relationship, dict):
        ledger["blocks"].append("INVALID_EVIDENCE_INPUT")
        return ledger
    records = reporting_audit.get("records")
    if not isinstance(records, list) or len(records) != len(ISINS) or any(not isinstance(r, dict) for r in records):
        ledger["blocks"].append("INCOMPLETE_REPORTING_MIC_RECORDS")
        return ledger
    by_isin = {r.get("isin"): r for r in records}
    if len(by_isin) != len(ISINS) or set(by_isin) != set(ISINS):
        ledger["blocks"].append("DUPLICATE_OR_UNEXPECTED_ISIN")
        return ledger
    relationship_ok = (iso_relationship.get("iso_operating_mic_found") is True
                       and iso_relationship.get("iso_regulated_segment_candidate") == "XETA")
    audit_ok = reporting_audit.get("reporting_market_reference_matched") is True
    for isin in ISINS:
        record = by_isin[isin]
        matched = (audit_ok and relationship_ok and record.get("market_mic") == "XETR"
                   and record.get("market_segment") == "045"
                   and record.get("reporting_market") == "XETA")
        ledger["instruments"].append({
            "isin": isin,
            "market_mic": record.get("market_mic"),
            "market_segment_code": record.get("market_segment"),
            "reporting_mic": record.get("reporting_market"),
            "reporting_mic_evidence": {
                "stage": "OFFICIAL_REFERENCE_MATCHED" if matched else "UNVERIFIED",
                "sources": ["XETRA_INSTRUMENT_CSV", "ISO_10383_MIC_REGISTRY"] if matched else [],
                "scope": "INSTRUMENT_REGULATORY_REPORTING",
                "account_specific": False,
                "limitations": ["SOURCE_AUTHENTICITY_NOT_INDEPENDENTLY_ATTESTED",
                                "REPORTING_MIC_DOES_NOT_PROVE_EXECUTION_VENUE"]},
            "execution_mic_evidence": {"stage": "UNVERIFIED", "sources": [], "scope": "ACCOUNT_EXECUTION"},
            "degiro_route_evidence": {"stage": "UNVERIFIED", "sources": [], "scope": "ACCOUNT_EXECUTION"},
            "degiro_tariff_evidence": {"stage": "UNVERIFIED", "sources": [], "scope": "ACCOUNT_TARIFF"},
            "trade_ready": False})
        if not matched:
            ledger["blocks"].append("REPORTING_MIC_NOT_MATCHED_" + isin)
    ledger["blocks"].extend(("EXECUTION_MIC_NOT_ATTESTED",
                             "ACCOUNT_ROUTE_NOT_ATTESTED",
                             "ACCOUNT_TARIFF_NOT_ATTESTED"))
    return ledger
