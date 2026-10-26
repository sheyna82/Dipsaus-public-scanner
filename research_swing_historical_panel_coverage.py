"""Offline coverage gate for diversified historical price experiments.

Never silently treat missing tickers or benchmark histories as usable.
No downloads, no licensing claims, no backtest profitability assertions.
"""
from datetime import date

def audit_historical_panel(universe, benchmark_symbols, histories, *, min_sessions=252):
    if type(min_sessions) is not int or min_sessions < 2:
        raise ValueError("invalid_min_sessions")
    if not isinstance(universe, (list, tuple)) or not isinstance(benchmark_symbols, (list, tuple)) or not isinstance(histories, dict):
        raise ValueError("invalid_panel")
    required = list(universe) + list(benchmark_symbols)
    if not required or len(set(required)) != len(required) or any(not isinstance(s, str) or not s for s in required):
        raise ValueError("invalid_symbols")
    if set(histories) - set(required):
        raise ValueError("unexpected_symbols")
    rows = []
    for symbol in required:
        bars = histories.get(symbol)
        if bars is None:
            rows.append({"symbol": symbol, "status": "missing", "sessions": 0})
            continue
        if not isinstance(bars, list):
            raise ValueError("invalid_bars")
        dates = []
        for bar in bars:
            if not isinstance(bar, dict):
                raise ValueError("invalid_bar")
            try:
                session = date.fromisoformat(bar["date"])
            except (KeyError, TypeError, ValueError):
                raise ValueError("invalid_session_date") from None
            dates.append(session)
        if dates != sorted(set(dates)):
            raise ValueError("duplicate_or_unsorted_sessions")
        rows.append({"symbol": symbol, "status": "sufficient_length_unverified" if len(dates) >= min_sessions else "insufficient_history",
                     "sessions": len(dates)})
    complete = all(row["status"] == "sufficient_length_unverified" for row in rows)
    return {"research_only": True, "trade_ready": False,
            "all_symbols_present": all(row["status"] != "missing" for row in rows),
            "length_coverage_complete": complete, "source_provenance_verified": False,
            "survivorship_bias_eliminated": False, "historical_profitability_established": False,
            "rows": rows}
