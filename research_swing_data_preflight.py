"""Fail-closed provenance and calendar preflight for offline OHLC research.

This checks structure, not the authenticity of the source. No downloads,
trading connections or historical edge claims.
"""
from datetime import date
from research_swing_chronological_ledger import _money


def validate_research_bars(series_by_ticker, trading_dates, *, minimum_sessions=3):
    if (not isinstance(trading_dates, (list, tuple)) or
            any(type(d) is not date for d in trading_dates) or
            list(trading_dates) != sorted(set(trading_dates))):
        raise ValueError("invalid_master_calendar")
    if (not isinstance(series_by_ticker, dict) or not series_by_ticker or
            type(minimum_sessions) is not int or minimum_sessions < 2):
        raise ValueError("invalid_dataset")
    calendar = set(trading_dates)
    coverage = {}
    for ticker, bars in sorted(series_by_ticker.items()):
        if not isinstance(ticker, str) or not ticker or not isinstance(bars, list):
            raise ValueError("invalid_symbol_series")
        if len(bars) < minimum_sessions:
            raise ValueError("insufficient_history")
        dates = []
        for bar in bars:
            if not isinstance(bar, dict):
                raise ValueError("invalid_bar")
            day = bar.get("date")
            if type(day) is not date or day not in calendar:
                raise ValueError("bar_outside_calendar")
            dates.append(day)
            for field in ("open", "close"):
                value = _money(bar.get(field))
                if value <= 0:
                    raise ValueError("invalid_price")
            if "volume" in bar:
                if _money(bar["volume"]) < 0:
                    raise ValueError("invalid_volume")
        if dates != sorted(set(dates)):
            raise ValueError("nonchronological_or_duplicate_bars")
        coverage[ticker] = {"sessions": len(dates),
                            "first": dates[0].isoformat(),
                            "last": dates[-1].isoformat()}
    return {"research_only": True, "source_authenticity_verified": False,
            "symbols": len(coverage), "coverage": coverage}
