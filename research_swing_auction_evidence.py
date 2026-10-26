"""Research-only classification of auction-volume evidence.

Do not substitute daily consolidated volume or generic intraday volume for
opening-auction matched shares. No network calls, no provider authentication.
"""
ALLOWED_SOURCE_KINDS = frozenset({
    "official_exchange_opening_auction",
    "licensed_vendor_opening_auction",
})
REJECTED_SOURCE_KINDS = frozenset({
    "daily_consolidated_volume",
    "exchange_daily_volume",
    "intraday_bar_volume",
    "preopen_imbalance",
    "unknown",
})


def validate_auction_volume_evidence(candidates):
    if not isinstance(candidates, (list, tuple)) or not candidates:
        raise ValueError("empty_evidence_cohort")
    seen = set()
    for item in candidates:
        if not isinstance(item, dict):
            raise ValueError("invalid_evidence_candidate")
        ticker = item.get("ticker")
        if not isinstance(ticker, str) or not ticker.strip() or ticker in seen:
            raise ValueError("duplicate_or_invalid_ticker")
        seen.add(ticker)
        kind = item.get("auction_volume_source_kind")
        if kind not in ALLOWED_SOURCE_KINDS:
            raise ValueError("opening_auction_volume_source_required")
        uri = item.get("auction_volume_source_uri")
        if not isinstance(uri, str) or not uri.startswith("https://") or len(uri) <= 8:
            raise ValueError("invalid_source_uri")
        observed_date = item.get("auction_volume_session_date")
        entry_date = item.get("entry_session_date")
        if not isinstance(observed_date, str) or not isinstance(entry_date, str):
            raise ValueError("missing_session_date")
        # Explicit equality prevents matching an auction volume from another
        # session; exchange calendar validity remains separately unverified.
        if observed_date != entry_date:
            raise ValueError("auction_volume_session_mismatch")
    return {"research_only": True, "trade_ready": False,
            "opening_auction_source_type_checked": True,
            "source_authenticity_verified": False,
            "source_license_verified": False,
            "exchange_calendar_verified": False,
            "validated_count": len(candidates)}
