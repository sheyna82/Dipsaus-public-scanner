"""Offline shadow decision join; evidence cannot be silently bypassed.

This is a diagnostic gate, not a notification, order or production pathway.
"""
from research.us_candidate_assessment_20261117 import assess_candidate
from research.us_massive_pipeline_20261117 import assess_massive_fixture

def assess_shadow_with_market_evidence(candidate, market_kwargs, *, now=None):
    blocks = []
    if not isinstance(candidate, dict):
        blocks.append("CANDIDATE_INPUT_MISSING")
        candidate_result = None
    else:
        try:
            candidate_result = assess_candidate(candidate, now=now)
            blocks.extend("CANDIDATE_" + b for b in candidate_result["blocks"])
            if candidate_result["status"] != "RESEARCH_CANDIDATE":
                blocks.append("CANDIDATE_NOT_CONFIRMED")
        except (TypeError, ValueError, KeyError, AttributeError, OverflowError, ZeroDivisionError):
            candidate_result = None
            blocks.append("CANDIDATE_EVIDENCE_INVALID")
    if not isinstance(market_kwargs, dict):
        blocks.append("MARKET_EVIDENCE_MISSING")
        market_result = None
    else:
        try:
            market_result = assess_massive_fixture(**market_kwargs)
            blocks.extend("MARKET_" + b for b in market_result["blocks"])
            if market_result["status"] != "RESEARCH_SCREENED_UNVERIFIED":
                blocks.append("MARKET_NOT_SCREENED")
        except (TypeError, ValueError, KeyError):
            market_result = None
            blocks.append("MARKET_EVIDENCE_INVALID")
    # A market fixture must never be joined to a different candidate symbol.
    # Absence of either identifier is also a block, not a wildcard match.
    candidate_symbol = candidate.get("symbol") if isinstance(candidate, dict) else None
    market_symbol = market_kwargs.get("ticker") if isinstance(market_kwargs, dict) else None
    if (not isinstance(candidate_symbol, str) or not candidate_symbol.strip()
            or not isinstance(market_symbol, str) or not market_symbol.strip()):
        blocks.append("INSTRUMENT_JOIN_IDENTITY_MISSING")
    elif candidate_symbol.strip().upper() != market_symbol.strip().upper():
        blocks.append("INSTRUMENT_JOIN_SYMBOL_MISMATCH")
    # Successful offline screening is not source independence, exchange-calendar
    # attestation, license clearance or live broker execution evidence.
    blocks.extend(("SOURCE_INDEPENDENCE_UNVERIFIED", "EXCHANGE_CALENDAR_UNVERIFIED",
                   "DATA_LICENSE_UNVERIFIED"))
    return {"status": "SHADOW_BLOCKED", "blocks": sorted(set(blocks)),
            "candidate": candidate_result, "market": market_result,
            "trade_ready": False, "notify": False, "automatic_orders": False}
