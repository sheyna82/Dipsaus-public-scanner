"""Spoor 2 notification classification — isolated, fail-closed policy.

No ntfy transport, secrets, production hooks, or order execution.
Research phases are never equivalent to a validated trade.
"""

RESEARCH_PHASES = frozenset({
    "BOTTOM-RECOVERY", "BREAKOUT-SEEN", "BREAKOUT-HOLD-RETEST",
    "EXECUTION-NEAR",
})

# An independent, human-verified execution decision is required even if
# numerical checks appear to pass. The scanner cannot authorize orders.
TRADE_EVIDENCE = (
    "broker_quote_verified", "fx_verified", "invalidation_verified",
    "resistance_verified", "entry_zone_verified", "target_verified",
    "company_event_risk_verified", "portfolio_fit_verified",
    "news_events_verified",
)


def classify_notification(row):
    """Classify for distinct future ntfy topics; never authorize a trade.

    Only explicit True values count. Unknown, missing and truthy strings fail.
    """
    if not isinstance(row, dict):
        return {"channel": "NONE", "qualified": False, "reason": "INVALID_INPUT"}
    phase = row.get("phase")
    if phase not in RESEARCH_PHASES:
        return {"channel": "NONE", "qualified": False, "reason": "UNKNOWN_PHASE"}
    if row.get("trade_ready") is True and all(row.get(k) is True for k in TRADE_EVIDENCE):
        # Separate independently calculated financial gates; no trust in phase.
        if (row.get("rr_verified") is True and row.get("net_profit_verified") is True
                and isinstance(row.get("rr"), (int, float))
                and not isinstance(row.get("rr"), bool)
                and isinstance(row.get("net_profit_eur"), (int, float))
                and not isinstance(row.get("net_profit_eur"), bool)):
            import math
            if (math.isfinite(row["rr"]) and row["rr"] >= 2
                    and math.isfinite(row["net_profit_eur"])
                    and row["net_profit_eur"] >= 150):
                return {"channel": "TRADE_QUALIFIED_REVIEW", "qualified": True,
                        "reason": "ALL_EXPLICIT_EVIDENCE_PRESENT",
                        "order_placement_enabled": False}
    return {"channel": "RESEARCH", "qualified": False,
            "reason": "TRADE_EVIDENCE_INCOMPLETE",
            "order_placement_enabled": False}


def notification_subject(symbol, classification):
    """Title labels cannot be confused even when a single topic is displayed."""
    if not isinstance(symbol, str) or not symbol.strip():
        return "DIPSAUS | UNKNOWN"
    if classification.get("channel") == "TRADE_QUALIFIED_REVIEW":
        return "DIPSAUS | GECONTROLEERDE INSTAPCHECK | " + symbol
    if classification.get("channel") == "RESEARCH":
        return "DIPSAUS | ONDERZOEK - GEEN KOOP | " + symbol
    return "DIPSAUS | GEEN MELDING"
