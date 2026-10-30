"""Exploratory warning-exit comparison on existing DIPSAUS OHLCV pilot artifacts.

Calendar-spaced entries are deliberately NOT scanner signals. This measures
warning behaviour on actual provider bars, not profitable strategy selection.
No download, no orders, no cross-currency return aggregation certification.
"""
import argparse
import gzip
import json
from datetime import date
from math import isfinite
from pathlib import Path
from research.swing_lifecycle.warning_exit_holdout import evaluate_warning_exit_holdout


def evaluate_pilot_artifact(path, *, cutoff, holding_sessions=10,
                            entry_stride=20, embargo_days=15,
                            confirmation_sessions=1):
    if type(holding_sessions) is not int or not 5 <= holding_sessions <= 15:
        raise ValueError("invalid_holding_sessions")
    if type(entry_stride) is not int or entry_stride < holding_sessions:
        raise ValueError("invalid_entry_stride")
    cases, skipped = [], []
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            symbol = record.get("symbol")
            raw_bars = record.get("bars", [])
            bars = []
            for row in raw_bars:
                if not isinstance(row, list) or len(row) < 5:
                    raise ValueError("invalid_pilot_bar")
                day, op, high, low, close = row[:5]
                bars.append({"date": day, "open": op, "high": high,
                             "low": low, "close": close})
            if not isinstance(symbol, str) or not symbol:
                raise ValueError("missing_symbol")
            # Reject corrupt or nonchronological provider bars before scoring.
            previous_day = None
            for bar in bars:
                day = date.fromisoformat(bar["date"])
                prices = [bar[key] for key in ("open", "high", "low", "close")]
                if (previous_day is not None and day <= previous_day):
                    raise ValueError("nonchronological_pilot_bars")
                if (any(isinstance(x, bool) or not isinstance(x, (int, float))
                        or not isfinite(x) or x <= 0 for x in prices)
                        or bar["low"] > min(bar["open"], bar["close"])
                        or bar["high"] < max(bar["open"], bar["close"])):
                    raise ValueError("invalid_pilot_ohlc")
                previous_day = day
            if len(bars) < 21 + holding_sessions:
                skipped.append({"symbol": symbol, "reason": "short_history"})
                continue
            for i in range(21, len(bars) - holding_sessions, entry_stride):
                cases.append({"ticker": symbol, "bars": bars,
                              "entry_index": i,
                              "baseline_exit_index": i + holding_sessions,
                              "score": 0})
    if not cases:
        raise ValueError("no_eligible_cases")
    # This is a per-symbol trade-candidate comparison, not a calibrated
    # scanner portfolio backtest. Ledger cash accounting is an illustration.
    result = evaluate_warning_exit_holdout(
        cases, cutoff=cutoff, embargo_days=embargo_days,
        confirmation_sessions=confirmation_sessions)
    return {
        "input": str(path),
        "candidate_method": "calendar_spaced_fixed_hold_not_scanner_entries",
        "candidate_count": len(cases),
        "confirmation_sessions": confirmation_sessions,
        "unique_symbols": len({x["ticker"] for x in cases}),
        "skipped": skipped,
        "result": result,
        "research_only": True,
        "historical_edge_proven": False,
        "provider_data_quality_independently_verified": False,
        "survivorship_bias_controlled": False,
        "fx_comparability_verified": False,
        "note": "Diagnostic only: no claim of scanner alpha, representative universe, actual fills or validated portfolio P&L.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot_gzip", type=Path)
    parser.add_argument("--cutoff", type=date.fromisoformat, required=True)
    parser.add_argument("--holding-sessions", type=int, default=10)
    parser.add_argument("--entry-stride", type=int, default=20)
    args = parser.parse_args()
    print(json.dumps(evaluate_pilot_artifact(
        args.pilot_gzip, cutoff=args.cutoff,
        holding_sessions=args.holding_sessions,
        entry_stride=args.entry_stride), indent=2, default=str))


if __name__ == "__main__":
    main()
