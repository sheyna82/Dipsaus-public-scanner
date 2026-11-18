"""Offline Xetra segment taxonomy from Deutsche Boerse T7 functional reference.

This is a venue-level classification, NOT an ISIN-specific segment mapping.
Source: T7 Release 14.1 Functional Reference section 9.1.8.
No requests, broker routing, trading, or independent source attestation.
"""
from research.spoor2_pilot_gap_report_20261118 import PILOT

DOCUMENTATION_URL = ("https://www.cashmarket.deutsche-boerse.com/resource/blob/"
                     "4942826/73b31cf8fa62eeb7d9f0421d5ed07ea9/data/"
                     "T7_Release_14.1_-_Functional_Reference_Version_1.pdf")
SEGMENTS = {
    "on_book": {"regulated": "XETA", "open_market": "XETB", "scale": "XETS"},
    "off_book_lis": {"regulated": "XETU", "open_market": "XETV", "scale": "XETW"},
    "midpoint": {"regulated": "XEMA", "open_market": "XEMB", "scale": "XEMI"},
}


def build_xetra_segment_taxonomy():
    rows = []
    for item in PILOT:
        if item["operating_mic"] != "XETR":
            continue
        rows.append({
            "symbol_claim": item["symbol"],
            "isin_claim": item["isin"],
            "operating_mic_claim": "XETR",
            "possible_segment_codes_by_trade_type": SEGMENTS,
            "actual_segment_mic": None,
            "instrument_market_segment": None,
            "trade_type": None,
            "blocks": [
                "INSTRUMENT_SPECIFIC_SEGMENT_EVIDENCE_MISSING",
                "TRADE_TYPE_NOT_ATTESTED",
                "OFFICIAL_XETRA_REFERENCE_BYTES_NOT_ATTESTED",
            ],
            "instrument_segment_verified": False,
            "segment_mic_verified": False,
        })
    return {
        "status": "BLOCKED",
        "documentation_url": DOCUMENTATION_URL,
        "documentation_status": "PUBLIC_REFERENCE_NOT_INDEPENDENTLY_ATTESTED",
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
    }
