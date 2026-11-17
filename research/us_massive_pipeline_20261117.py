"""Offline composition of Massive normalization, integrity and session clock.

Synthetic fixtures only. No market data retrieval or trade authorization.
"""
import hashlib
from research.us_massive_adapter_20261117 import normalize_massive_aggregates
from research.us_ohlcv_integrity_20261117 import attest_ohlcv, canonical_payload
from research.us_session_clock_20261117 import classify_regular_session

def assess_massive_fixture(payload, *, ticker, mic, adjustment_policy,
                           timeframe, fetched_utc, now, expected_sha256):
    norm = normalize_massive_aggregates(payload, ticker=ticker, mic=mic,
                                        adjustment_policy=adjustment_policy)
    blocks = ["NORMALIZATION_" + b for b in norm["blocks"]]
    if norm["status"] != "NORMALIZED_UNVERIFIED":
        return {"status": "UNKNOWN", "blocks": sorted(set(blocks)),
                "provider_independently_verified": False,
                "exchange_calendar_verified": False, "trade_ready": False}
    integrity = attest_ohlcv(norm["bars"], source="massive-offline-fixture",
                             instrument=ticker, timeframe=timeframe,
                             fetched_utc=fetched_utc,
                             expected_sha256=expected_sha256, now=now)
    blocks += ["INTEGRITY_" + b for b in integrity["blocks"]]
    clock = classify_regular_session(norm["bars"], timeframe=timeframe)
    blocks += ["SESSION_" + b for b in clock["blocks"]]
    return {"status": "RESEARCH_SCREENED_UNVERIFIED" if not blocks else "UNKNOWN",
            "blocks": sorted(set(blocks)), "bar_count": len(norm["bars"]),
            "provider_independently_verified": False,
            "exchange_calendar_verified": False, "trade_ready": False}
