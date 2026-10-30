"""Append-only-style prospective signal ledger generator (research only).

This script emits a candidate JSON record; it never updates a live scanner,
places orders, or silently overwrites a previously saved record.
"""
import argparse
import json
from datetime import date
from pathlib import Path

from research_validate_prospective_protocol import validate_protocol


def build_candidate(symbol, signal_session, stock_close, spy_close, *,
                    protocol_path="research/prospective_momentum_protocol_v1.json"):
    validate_protocol(protocol_path)
    spec = json.loads(Path(protocol_path).read_text(encoding="utf-8"))
    session = date.fromisoformat(signal_session)
    if session < date.fromisoformat(spec["first_eligible_signal_session"]):
        raise ValueError("signal_before_prospective_start")
    if symbol not in spec["symbols"]:
        raise ValueError("symbol_not_preregistered")
    if len(stock_close) != 4 or len(spy_close) != 4:
        raise ValueError("requires_four_consecutive_closes")
    from decimal import Decimal
    stock = [Decimal(str(v)) for v in stock_close]
    spy = [Decimal(str(v)) for v in spy_close]
    if any(v <= 0 or not v.is_finite() for v in stock + spy):
        raise ValueError("invalid_close")
    past_stock = stock[-1] / stock[0] - 1
    past_spy = spy[-1] / spy[0] - 1
    return {"protocol_id": spec["protocol_id"], "symbol": symbol,
            "signal_session": signal_session,
            "signal_positive_past_excess": past_stock > past_spy,
            "past_stock_return": str(past_stock),
            "past_spy_return": str(past_spy),
            "future_outcome": None, "future_outcome_available": False,
            "research_only": True, "trade_ready": False,
            "input_verified_independently": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--stock-closes", required=True,
                        help="Four consecutive daily closes, comma-separated")
    parser.add_argument("--spy-closes", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    record = build_candidate(args.symbol, args.session,
                             args.stock_closes.split(","), args.spy_closes.split(","))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
        f.write("\n")
    print(json.dumps({"created": str(output), "trade_ready": False}))


if __name__ == "__main__":
    main()
