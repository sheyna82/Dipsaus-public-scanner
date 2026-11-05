"""Bridge pre-registered historical sector universe to rotation evidence, fail closed.

Historical Yahoo observations are unverified and must never be promoted to
current verified rotation signals. No network access or trading side effects.
"""
from research_swing_diversified_universe import UNIVERSE_V1
from sector_rotation_evidence import SECTORS, assess_sector_rotation


def historical_sector_coverage(status_by_symbol):
    expected = {symbol for symbol, _ in UNIVERSE_V1}
    if not isinstance(status_by_symbol, dict) or set(status_by_symbol) != expected:
        return {"status": "UNKNOWN", "reason": "INCOMPLETE_SYMBOL_COVERAGE",
                "trade_ready": False}
    covered = {sector for symbol, sector in UNIVERSE_V1
               if status_by_symbol[symbol] in ("normalized_unverified", "audited_verified")}
    missing = sorted(set(SECTORS) - covered)
    return {"status": "INCOMPLETE_RESEARCH" if missing else "REVIEW_REQUIRED",
            "covered_sectors": sorted(covered), "missing_sectors": missing,
            "independent_quote_verification": False, "trade_ready": False}


def sector_rotation_from_historical_unverified(relative_returns, observed_utc, now=None):
    """Never relabel historical, unverified data as current PASS/CAUTION."""
    diagnostic = assess_sector_rotation(relative_returns, observed_utc, now)
    return {"status": "UNKNOWN", "reason": "HISTORICAL_UNVERIFIED_NOT_LIVE",
            "historical_diagnostic_status": diagnostic["status"],
            "checked_utc": None, "trade_ready": False, "research_only": True}
