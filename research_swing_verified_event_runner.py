"""Run real, verified event research against per-symbol historical OHLC JSON.

Offline only. JSON input must contain:
 events: list of audited event records with symbol, event_id, kind, source,
 source_url, published_at, first_observed_at, release_timestamp_verified;
 bars_by_symbol: mapping symbol -> chronological OHLC sessions with UTC
 open_at/close_at and open/high/low/close. No market data is fabricated.
"""
import argparse
import json
from pathlib import Path
from research_swing_historical_event_inputs import (
    validate_historical_event_rows, validate_daily_bars)
from research_swing_event_outcome_study import study_event_outcomes
from research_swing_event_cohort_summary import summarize_event_cohort


def run_verified_event_study(payload, *, as_of_at, horizons=(3, 5, 10, 15),
                             minimum_events=20):
    if not isinstance(payload, dict):
        raise ValueError("invalid_study_payload")
    events = validate_historical_event_rows(payload.get("events"), cutoff_at=as_of_at)
    prices = payload.get("bars_by_symbol")
    if not isinstance(prices, dict):
        raise ValueError("missing_bars_by_symbol")
    from research_swing_event_dataset_audit import _utc
    as_of = _utc(as_of_at)
    for symbol, bars in prices.items():
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("invalid_symbol")
        validate_daily_bars(bars)
    records = []
    skipped = 0
    for event in events:
        symbol = event["symbol"]
        bars = prices.get(symbol)
        if bars is None:
            skipped += 1
            continue
        # Use validated event fields including original publication timestamps.\n        result = study_event_outcomes(event, bars, bars, horizons=horizons)\n        for outcome in result["outcomes"]:
            # Never use prices that were not observable by the study cutoff.
            if _utc(bars[outcome["exit_index"]]["open_at"]) > as_of:
                continue
            records.append({
                "symbol": symbol, "event_id": event["event_id"],
                "kind": event["kind"], **outcome,
            })
    cohorts = {}
    for horizon in horizons:
        selected = [r for r in records if r["horizon"] == horizon]
        # Overlapping same-symbol trades are excluded conservatively, not
        # counted as independent research observations.
        filtered = []
        last_exit = {}
        for row in sorted(selected, key=lambda r: (r["symbol"], r["entry_index"])):
            if row["entry_index"] <= last_exit.get(row["symbol"], -1):
                continue
            last_exit[row["symbol"]] = row["exit_index"]
            filtered.append(row)
        cohorts[str(horizon)] = summarize_event_cohort(
            filtered, horizon=horizon, minimum_events=minimum_events)
        cohorts[str(horizon)]["overlap_excluded"] = len(selected) - len(filtered)
    return {"events_accepted": len(events), "events_missing_prices": skipped,
            "outcome_rows": len(records), "cohorts": cohorts,
            "trade_ready": False, "predictive_edge_proven": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = run_verified_event_study(payload, as_of_at=args.as_of)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Accepted events:", result["events_accepted"],
          "measured outcomes:", result["outcome_rows"])


if __name__ == "__main__":
    main()
