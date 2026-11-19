"""Reconcile historical missing-evidence report with later user-uploaded artifacts.

This is a reporting bridge, not source admission or trading authorization.
"""
from research.spoor2_xetra_current_evidence_gap_report_20261118 import (
    build_current_xetra_evidence_gap_report,
)
from research.spoor2_xetra_uploaded_artifact_evidence_20261118 import (
    build_uploaded_xetra_evidence_report,
)

BLOCKED = (
    "source_attested", "instrument_segment_verified", "segment_mic_verified",
    "broker_route_verified", "degiro_fee_verified", "trade_ready",
    "order_placement_enabled", "notify", "automatic_orders",
)


def build_xetra_reconciled_evidence_report():
    historical = build_current_xetra_evidence_gap_report()
    uploaded = build_uploaded_xetra_evidence_report()
    old = {row["isin_claim"]: row for row in historical["rows"]}
    new = {row["isin"]: row for row in uploaded["rows"]}
    if set(old) != set(new):
        raise ValueError("XETRA_EVIDENCE_INSTRUMENT_SET_MISMATCH")
    if any(historical[key] or uploaded[key] for key in BLOCKED):
        raise ValueError("XETRA_EVIDENCE_UNEXPECTED_RELEASE_FLAG")
    rows = []
    for isin in sorted(old):
        prior, current = old[isin], new[isin]
        # Historical notices use broker-style IFX.DE/RHM.DE; Xetra CSV uses IFX/RHM.
        # Only the explicitly expected .DE suffix may be normalized here.
        historical_symbol = prior["symbol_claim"]
        if not isinstance(historical_symbol, str) or not historical_symbol.endswith(".DE") or historical_symbol[:-3] != current["mnemonic"]:
            raise ValueError("XETRA_EVIDENCE_SYMBOL_MISMATCH")
        rows.append({
            "isin": isin,
            "symbol": current["mnemonic"],
            "historical_report_record_available": prior["current_record_available"],
            "uploaded_record_available": True,
            "uploaded_record_origin": "USER_UPLOADED_UNATTESTED",
            "csv_sha256": uploaded["csv_sha256"],
            "zip_sha256": uploaded["zip_sha256"],
            "market_segment": current["market_segment"],
            "market_segment_description": current["market_segment_description"],
            "mic_code": current["mic_code"],
            "reporting_market": current["reporting_market"],
            "segment_mic": None,
            "remaining_evidence_required": [
                "INDEPENDENT_SOURCE_ORIGIN_AND_ARTIFACT_INTEGRITY",
                "INDEPENDENT_CURRENT_INSTRUMENT_AND_SEGMENT_ATTESTATION",
                "TRADE_TYPE_SPECIFIC_SEGMENT_MIC",
                "DEGIRO_ACCOUNT_ROUTE_AND_APPLICABLE_FEES",
            ],
            "trade_ready": False,
        })
    return {
        "status": "BLOCKED_WITH_UPLOADED_RECORDS",
        "historical_gap_report_preserved": True,
        "external_download_performed": False,
        "rows": rows,
        **{key: False for key in BLOCKED},
    }
