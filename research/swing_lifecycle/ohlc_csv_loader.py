"""Load independently sourced daily OHLC CSV for offline warning-exit research.

Requires an explicit data-source label and chronological session dates.
No downloading, adjusted-price inference, or fill certification is performed.
"""
import csv
from datetime import date
from math import isfinite


def load_daily_ohlc_csv(path, *, source, ticker):
    if not isinstance(source, str) or not source.strip():
        raise ValueError("missing_data_source")
    if not isinstance(ticker, str) or not ticker.strip():
        raise ValueError("missing_ticker")
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not {"date", "open", "high", "low", "close"}.issubset(reader.fieldnames or []):
            raise ValueError("missing_ohlc_columns")
        for raw in reader:
            try:
                day = date.fromisoformat(raw["date"])
                prices = {key: float(raw[key]) for key in ("open", "high", "low", "close")}
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError("invalid_price_or_date") from exc
            if (any(not isfinite(x) or x <= 0 for x in prices.values())
                    or prices["low"] > min(prices["open"], prices["close"])
                    or prices["high"] < max(prices["open"], prices["close"])):
                raise ValueError("inconsistent_ohlc")
            if rows and day <= date.fromisoformat(rows[-1]["date"]):
                raise ValueError("nonchronological_sessions")
            rows.append({"date": day.isoformat(), **prices})
    if len(rows) < 22:
        raise ValueError("insufficient_history")
    return {
        "ticker": ticker,
        "source": source,
        "bars": rows,
        "row_count": len(rows),
        "research_only": True,
        "corporate_actions_verified": False,
        "fill_verified": False,
        "adjustment_policy_verified": False,
    }
