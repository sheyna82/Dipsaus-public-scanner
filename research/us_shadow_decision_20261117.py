"""Offline shadow decision join; evidence cannot be silently bypassed.

This is a diagnostic gate, not a notification, order or production pathway.
"""
from research.us_candidate_assessment_20261117 import assess_candidate
from research.us_massive_pipeline_20261117 import assess_massive_fixture
from research.us_source_identity_20261117 import review_source_identity
from research.us_exchange_calendar_evidence_20261117 import review_exchange_calendar
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def assess_shadow_with_market_evidence(candidate, market_kwargs, *, now=None, source_identity=None,
                                       calendar_evidence=None, session_date=None):
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
    # Source identity metadata is independently inspected, but never self-attests.
    source_result = review_source_identity(source_identity)
    blocks.extend("SOURCE_" + b for b in source_result["blocks"])
    if source_result["status"] != "METADATA_COMPLETE_UNVERIFIED":
        blocks.append("SOURCE_METADATA_INCOMPLETE")
    if (isinstance(market_kwargs, dict) and
            isinstance(source_identity, dict) and
            isinstance(market_kwargs.get("mic"), str) and
            isinstance(source_identity.get("mic"), str) and
            market_kwargs["mic"] != source_identity["mic"]):
        blocks.append("SOURCE_MARKET_MIC_MISMATCH")
    # The source record must refer to the exact market payload digest.
    # Matching self-declared hashes are consistency evidence, not authenticity.
    if isinstance(source_identity, dict) and isinstance(market_kwargs, dict):
        source_hash = source_identity.get("content_sha256")
        market_hash = market_kwargs.get("expected_sha256")
        if (not isinstance(source_hash, str) or not isinstance(market_hash, str)
                or not source_hash.strip() or not market_hash.strip()):
            blocks.append("SOURCE_MARKET_DIGEST_MISSING")
        elif source_hash.lower() != market_hash.lower():
            blocks.append("SOURCE_MARKET_DIGEST_MISMATCH")
    # Calendar metadata is reviewed separately; never grant official-session trust.
    try:
        calendar_result = review_exchange_calendar(
            calendar_evidence, session_date=session_date, now=now)
        blocks.extend("CALENDAR_" + b for b in calendar_result["blocks"])
        if calendar_result["status"] != "METADATA_COMPLETE_UNVERIFIED":
            blocks.append("CALENDAR_METADATA_INCOMPLETE")
    except (TypeError, ValueError, AttributeError, OverflowError):
        calendar_result = None
        blocks.append("CALENDAR_EVIDENCE_INVALID")
    # Bind hourly fixture bars to the declared NY calendar date. Daily
    # aggregate timestamps may denote session labels, not local clock times.
    if (isinstance(market_kwargs, dict) and
            market_kwargs.get("timeframe") == "hourly" and
            isinstance(session_date, str)):
        payload = market_kwargs.get("payload")
        raw_bars = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(raw_bars, list) or not raw_bars:
            blocks.append("CALENDAR_BAR_DATE_UNRESOLVED")
        else:
            try:
                dates = {
                    datetime.fromtimestamp(bar["t"] / 1000, tz=timezone.utc)
                    .astimezone(ZoneInfo("America/New_York")).date().isoformat()
                    for bar in raw_bars
                }
                if dates != {session_date}:
                    blocks.append("CALENDAR_BAR_DATE_MISMATCH")
            except (TypeError, ValueError, KeyError, OverflowError, OSError, AttributeError):
                blocks.append("CALENDAR_BAR_DATE_UNRESOLVED")
    # A declared closed or shortened session cannot be treated as a regular
    # session by the offline pipeline, even if the clock-only screen passes.
    if isinstance(calendar_evidence, dict):
        if calendar_evidence.get("session_kind") == "closed":
            blocks.append("CALENDAR_SESSION_CLOSED")
        elif calendar_evidence.get("session_kind") == "early_close":
            blocks.append("CALENDAR_EARLY_CLOSE_UNRESOLVED")
    if (isinstance(calendar_evidence, dict) and
            isinstance(market_kwargs, dict) and
            isinstance(calendar_evidence.get("exchange"), str) and
            isinstance(market_kwargs.get("mic"), str) and
            calendar_evidence["exchange"] != market_kwargs["mic"]):
        blocks.append("CALENDAR_MARKET_MIC_MISMATCH")
    # A matching ticker and MIC still do not prove that source metadata refers
    # to the same instrument. Reject contradictory instrument identifiers.
    if (isinstance(source_identity, dict) and
            isinstance(candidate_symbol, str) and candidate_symbol.strip()):
        source_instrument = source_identity.get("instrument_id")
        if not isinstance(source_instrument, str) or not source_instrument.strip():
            blocks.append("SOURCE_INSTRUMENT_IDENTITY_MISSING")
        elif source_instrument.strip().upper() != candidate_symbol.strip().upper():
            blocks.append("SOURCE_INSTRUMENT_IDENTITY_UNRESOLVED")
    # Successful offline screening is not source independence, exchange-calendar
    # attestation, license clearance or live broker execution evidence.
    blocks.extend(("SOURCE_INDEPENDENCE_UNVERIFIED", "EXCHANGE_CALENDAR_UNVERIFIED",
                   "DATA_LICENSE_UNVERIFIED"))
    return {"status": "SHADOW_BLOCKED", "blocks": sorted(set(blocks)),
            "candidate": candidate_result, "market": market_result,
            "source_identity": source_result, "calendar": calendar_result,
            "trade_ready": False, "notify": False, "automatic_orders": False}
