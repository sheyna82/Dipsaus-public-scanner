"""Independent broker-route and ISO-MIC evidence gate; fail closed by default.

Xetra reference data identifies instruments, not the account's actual DEGIRO route.
No unverified statement can promote an instrument to trade-ready.
"""

def assess_execution_evidence(pilot, mic_evidence=None, broker_evidence=None, fee_evidence=None):
    out = {"status": "BLOCKED", "source_attested": False,
           "instrument_segment_verified": False, "segment_mic_verified": False,
           "broker_route_verified": False, "degiro_fee_verified": False,
           "trade_ready": False, "order_placement_enabled": False,
           "instruments": [], "blocks": []}
    if not isinstance(pilot, dict) or pilot.get("status") != "BLOCKED":
        out["blocks"].append("INVALID_PILOT_EVIDENCE")
        return out
    records = pilot.get("records")
    if not isinstance(records, list) or len(records) != 2:
        out["blocks"].append("INCOMPLETE_PILOT_INSTRUMENTS")
        return out
    expected = {"DE0006231004", "DE0007030009"}
    if any(not isinstance(r, dict) for r in records) or {r.get("isin") for r in records} != expected:
        out["blocks"].append("INVALID_PILOT_ISIN_SET")
        return out
    for record in records:
        isin = record["isin"]
        item = {"isin": isin, "xetra_operating_mic": record.get("mic_code"),
                "xetra_market_segment": record.get("market_segment_code"),
                "segment_mic": None, "degiro_execution_route": None,
                "degiro_fee": None, "trade_ready": False}
        if record.get("mic_code") != "XETR" or record.get("market_segment_code") != "045":
            out["blocks"].append("UNEXPECTED_XETRA_INSTRUMENT_" + isin)
        # Evidence must be independently sourced, dated and account-specific for broker routes.
        # Until separate source-authenticity and account-route validation exist, never
        # promote external assertions into verified fields.
        out["instruments"].append(item)
    out["blocks"].extend((
        "ISO_10383_SEGMENT_MIC_NOT_INDEPENDENTLY_VERIFIED",
        "DEGIRO_ACCOUNT_EXECUTION_ROUTE_NOT_VERIFIED",
        "DEGIRO_ACCOUNT_TARIFF_NOT_VERIFIED",
        "SOURCE_ATTESTATION_NOT_COMPLETE",
    ))
    return out
