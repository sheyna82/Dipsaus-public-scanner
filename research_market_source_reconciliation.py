"""Offline cross-vendor daily-price reconciliation.

No network, live signals or trading. Strict date alignment; adjusted and raw
series must never be compared as though they were interchangeable.
"""
from decimal import Decimal
from research_event_baseline_comparison import compare_event_to_benchmark


def reconcile_daily_sources(sources, *, adjustment_mode, tolerance_pct="0.5"):
    if adjustment_mode not in ("raw", "split_adjusted"):
        raise ValueError("adjustment_mode_required")
    if not isinstance(sources, dict) or len(sources) < 2:
        raise ValueError("two_independent_sources_required")
    if not all(isinstance(name, str) and name.strip() for name in sources):
        raise ValueError("invalid_source_name")
    tolerance = Decimal(str(tolerance_pct))
    if not tolerance.is_finite() or tolerance < 0 or tolerance > 100:
        raise ValueError("invalid_tolerance")
    validated = {}
    for name, rows in sources.items():
        if not isinstance(rows, list) or not rows:
            raise ValueError("missing_daily_prices")
        # Reuse strict date, price and duplicate checks.
        compare_event_to_benchmark(rows, rows, horizons=(1,)) if len(rows) > 1 else None
        from datetime import date
        previous = None
        prices = {}
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"date", "close"}:
                raise ValueError("invalid_session_record")
            try:
                day = date.fromisoformat(row["date"]).isoformat()
                price = Decimal(str(row["close"]))
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError("invalid_session_record") from exc
            if not price.is_finite() or price <= 0:
                raise ValueError("invalid_session_price")
            if previous is not None and day <= previous:
                raise ValueError("unsorted_session_dates")
            previous = day
            prices[day] = price
        validated[name] = prices
    common = set.intersection(*(set(prices) for prices in validated.values()))
    if not common:
        raise ValueError("no_overlapping_sessions")
    report = []
    for day in sorted(common):
        values = [prices[day] for prices in validated.values()]
        low, high = min(values), max(values)
        spread = (high - low) / low * 100
        report.append({"date": day, "spread_pct": str(spread),
                       "within_tolerance": spread <= tolerance})
    return {
        "adjustment_mode": adjustment_mode,
        "sources": sorted(validated),
        "common_sessions": len(common),
        "compared_sessions": report,
        "all_within_tolerance": all(row["within_tolerance"] for row in report),
        "sources_independently_authenticated": False,
        "trade_ready": False,
    }
