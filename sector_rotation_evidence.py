"""Pure, research-only sector rotation evidence. No network or trade actions."""
from datetime import datetime, timezone
from math import isfinite

SECTORS = ("energy", "healthcare", "consumer_staples", "technology",
           "communication_services", "industrials", "financials",
           "utilities", "materials", "real_estate", "consumer_discretionary")


def assess_sector_rotation(relative_returns, observed_utc, now=None):
    """Require independently supplied 5/10/20d sector-relative returns."""
    now = now or datetime.now(timezone.utc)
    unknown = {"status": "UNKNOWN", "reason": "MISSING_OR_STALE_MARKET_EVIDENCE",
               "checked_utc": None, "research_only": True}
    if not isinstance(relative_returns, dict) or not isinstance(observed_utc, str):
        return unknown
    try:
        observed = datetime.fromisoformat(observed_utc.replace("Z", "+00:00"))
        age = (now - observed).total_seconds()
        if observed.tzinfo is None or not 0 <= age <= 900:
            return unknown
    except (ValueError, OverflowError, TypeError):
        return unknown
    if set(relative_returns) != set(SECTORS):
        return unknown
    for sector in SECTORS:
        periods = relative_returns[sector]
        if not isinstance(periods, dict) or set(periods) != {"5d", "10d", "20d"}:
            return unknown
        for value in periods.values():
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value):
                return unknown
    leaders = sorted(SECTORS, key=lambda s: relative_returns[s]["20d"], reverse=True)
    positive = sum(relative_returns[s]["20d"] > 0 for s in SECTORS)
    tech_lags = relative_returns["technology"]["20d"] < 0
    status = "CAUTION" if tech_lags and positive < 6 else "PASS"
    return {"status": status, "reason": "SECTOR_RELATIVE_STRENGTH_RESEARCH",
            "checked_utc": observed_utc, "leaders": leaders[:3],
            "positive_sectors_20d": positive, "technology_lags_20d": tech_lags,
            "research_only": True, "trade_ready": False}
