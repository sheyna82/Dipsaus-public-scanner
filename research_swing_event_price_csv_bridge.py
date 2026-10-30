"""Offline historical OHLC CSV bridge for multi-market event studies.

Requires explicit timezone-aware session opens/closes and original price fields.
No guessing local exchange calendars or downloading price data.
"""
import csv
import json
from pathlib import Path
from research_swing_historical_event_inputs import validate_daily_bars

REQUIRED_COLUMNS = ("open_at", "close_at", "open", "high", "low", "close")


def load_verified_price_csv(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or any(name not in reader.fieldnames for name in REQUIRED_COLUMNS):
            raise ValueError("missing_price_columns")
        bars = []
        for row in reader:
            if not any(row.values()):
                continue
            try:
                bar = {"open_at": row["open_at"], "close_at": row["close_at"],
                       **{field: float(row[field]) for field in
                          ("open", "high", "low", "close")}}
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError("invalid_price_csv_row") from exc
            bars.append(bar)
    validate_daily_bars(bars)
    return bars


def prepare_event_study_input(events_json_path, price_csv_by_symbol):
    events = json.loads(Path(events_json_path).read_text(encoding="utf-8"))
    if not isinstance(events, list):
        raise ValueError("events_must_be_list")
    if not isinstance(price_csv_by_symbol, dict) or not price_csv_by_symbol:
        raise ValueError("missing_price_mapping")
    prices = {}
    for symbol, path in price_csv_by_symbol.items():
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("invalid_symbol")
        prices[symbol] = load_verified_price_csv(path)
    return {"events": events, "bars_by_symbol": prices}
