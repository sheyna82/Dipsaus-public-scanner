"""Offline comparison of untrusted Xetra instrument records to pilot claims.

The official Xetra instrument reference guide distinguishes Market Segment
Status, Instrument Status, ISIN and venue metadata. Caller-supplied records
are NEVER attested evidence, even if they match all expected values.
No fetching, no redirect following, no broker actions.
"""
from research.spoor2_xetra_historical_segment_notices_20261118 import NOTICES

REQUIRED = ("isin", "market_mic", "market_segment_status",
            "instrument_status", "market_segment", "segment_mic")


def compare_xetra_instrument_record(isin, record=None):
    blocks = []
    expected = NOTICES.get(isin)
    if expected is None:
        blocks.append("PILOT_ISIN_NOT_SUPPORTED")
    if not isinstance(record, dict):
        blocks.append("CURRENT_INSTRUMENT_RECORD_MISSING")
        record = {}
    for field in REQUIRED:
        if not isinstance(record.get(field), str) or not record[field].strip():
            blocks.append("FIELD_MISSING:" + field)
    if expected is not None:
        if record.get("isin") != isin:
            blocks.append("ISIN_CONFLICT")
        if record.get("market_mic") != "XETR":
            blocks.append("OPERATING_MIC_CONFLICT")
        if record.get("market_segment") != "Regulierter Markt - Prime Standard":
            blocks.append("HISTORICAL_SEGMENT_MISMATCH_OR_UNCONFIRMED")
    if record.get("market_segment_status") != "Active":
        blocks.append("MARKET_SEGMENT_NOT_REPORTED_ACTIVE")
    if record.get("instrument_status") != "Active":
        blocks.append("INSTRUMENT_NOT_REPORTED_ACTIVE")
    # The code is only a claim. Do not infer XETA from Prime Standard.
    if record.get("segment_mic") not in ("XETA", "XETB", "XETS", "XETU",
                                         "XETV", "XETW", "XEMA", "XEMB", "XEMI"):
        blocks.append("SEGMENT_MIC_NOT_IN_DOCUMENTED_TAXONOMY")
    blocks.append("UNTRUSTED_RECORD_NOT_INDEPENDENTLY_ATTESTED")
    blocks.append("BROKER_ROUTE_AND_FEES_NOT_VERIFIED")
    return {
        "status": "BLOCKED",
        "isin_claim": isin,
        "reported_record_fields": {k: record.get(k) for k in REQUIRED},
        "blocks": sorted(set(blocks)),
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
