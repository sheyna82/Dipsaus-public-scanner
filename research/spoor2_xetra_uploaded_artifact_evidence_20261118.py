"""Offline inventory of user-supplied Xetra reference files, inspected 2026-11-18.

The CSV's 'Reporting Market' column is XETA, not a 'Segment MIC'
column. Source-file SHA-256 is content integrity, not origin attestation.
No embedded raw files, network calls, broker actions or trade promotion.
"""
CSV_SHA256 = "c3f9f7e63dd9b551338c29bda00aaade3e48ec71e035d0ce19348423402dc1ee"
ZIP_SHA256 = "1f740e68d775bb3ebc3f79f776860b29034d8a1e47443e56a9730679e0545a24"
CSV_SIZE_BYTES = 4897852
ZIP_SIZE_BYTES = 8590822
CSV_REPORTED_UPDATE = "18.11.2026"
SEGMENT_TABLE_ENTRY = {"identifier": "045", "description": "Regulierter Markt Prime Standard"}
INSTRUMENTS = {
    "DE0006231004": {"mnemonic": "IFX", "mic_code": "XETR", "reporting_market": "XETA"},
    "DE0007030009": {"mnemonic": "RHM", "mic_code": "XETR", "reporting_market": "XETA"},
}


def build_uploaded_xetra_evidence_report():
    rows = []
    for isin, item in sorted(INSTRUMENTS.items()):
        rows.append({
            "isin": isin, **item,
            "product_status": "Active",
            "instrument_status": "Active",
            "trading_model_type": "Continuous",
            "market_segment": "045",
            "market_segment_description": SEGMENT_TABLE_ENTRY["description"],
            "segment_mic": None,
            "reporting_market_is_segment_mic_attested": False,
            "source_origin_independently_attested": False,
            "broker_route_verified": False,
            "degiro_fee_verified": False,
            "trade_ready": False,
        })
    return {
        "status": "BLOCKED",
        "artifact_origin": "USER_UPLOADED",
        "csv_sha256": CSV_SHA256,
        "zip_sha256": ZIP_SHA256,
        "csv_size_bytes": CSV_SIZE_BYTES,
        "zip_size_bytes": ZIP_SIZE_BYTES,
        "csv_reported_update": CSV_REPORTED_UPDATE,
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
