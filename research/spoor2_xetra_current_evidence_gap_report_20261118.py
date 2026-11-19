"""Current missing-evidence inventory for Xetra pilot instruments, offline only.

No current Xetra reference artifact has been independently admitted.
The report intentionally compares absent current records, rather than
manufacturing positive records from historical notices or venue taxonomy.
"""
from research.spoor2_xetra_historical_segment_notices_20261118 import NOTICES
from research.spoor2_xetra_instrument_record_comparison_20261118 import (
    compare_xetra_instrument_record,
)


def build_current_xetra_evidence_gap_report():
    rows = []
    for isin in sorted(NOTICES):
        comparison = compare_xetra_instrument_record(isin)
        rows.append({
            "isin_claim": isin,
            "symbol_claim": NOTICES[isin]["symbol_claim"],
            "historical_notice_date": NOTICES[isin]["notice_date"],
            "historical_segment_claim": NOTICES[isin]["market_label"],
            "current_record_available": False,
            "current_record_comparison": comparison,
            "next_evidence_required": [
                "CURRENT_OFFICIAL_XETRA_INSTRUMENT_RECORD_WITH_ISIN",
                "INDEPENDENT_SOURCE_ORIGIN_AND_ARTIFACT_INTEGRITY",
                "CURRENT_INSTRUMENT_AND_SEGMENT_STATUS",
                "TRADE_TYPE_SPECIFIC_SEGMENT_MIC",
                "DEGIRO_ACCOUNT_ROUTE_AND_APPLICABLE_FEES",
            ],
            "trade_ready": False,
        })
    return {
        "status": "BLOCKED",
        "rows": rows,
        "source_attested": False,
        "instrument_segment_verified": False,
        "segment_mic_verified": False,
        "broker_route_verified": False,
        "degiro_fee_verified": False,
        "trade_ready": False,
        "order_placement_enabled": False,
        "notify": False,
        "automatic_orders": False,
        "external_download_performed": False,
    }
