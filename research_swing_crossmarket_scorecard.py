"""Cross-market historical breadth scorecard with explicit sample sufficiency.

Descriptive counts only: no synthetic returns, no implied predictive edge.
"""
from collections import Counter, defaultdict

DIMENSIONS = ("market", "sector", "cap_bucket", "regime", "event_kind", "horizon")
MIN_EVENTS_PER_CELL = 30
MIN_SYMBOLS_PER_CELL = 10


def research_coverage_scorecard(rows, *, min_events=MIN_EVENTS_PER_CELL,
                                min_symbols=MIN_SYMBOLS_PER_CELL):
    if type(min_events) is not int or min_events < 1:
        raise ValueError("invalid_min_events")
    if type(min_symbols) is not int or min_symbols < 1:
        raise ValueError("invalid_min_symbols")
    if not isinstance(rows, (list, tuple)):
        raise ValueError("invalid_rows")
    buckets = {name: defaultdict(lambda: {"events": set(), "symbols": set()})
               for name in DIMENSIONS}
    combinations = defaultdict(lambda: {"events": set(), "symbols": set()})
    missing = Counter()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid_row")
        symbol, event_id = row.get("symbol"), row.get("event_id")
        if not isinstance(symbol, str) or not symbol or not isinstance(event_id, str) or not event_id:
            raise ValueError("invalid_event_identity")
        event_key = (symbol, event_id)
        for name in DIMENSIONS:
            value = row.get(name)
            if value is None or value == "":
                missing[name] += 1
                continue
            if not isinstance(value, (str, int)) or isinstance(value, bool):
                raise ValueError("invalid_dimension")
            bucket = buckets[name][str(value)]
            bucket["events"].add(event_key)
            bucket["symbols"].add(symbol)
        if all(row.get(name) is not None and row.get(name) != "" for name in
               ("market", "regime", "horizon")):
            key = (str(row["market"]), str(row["regime"]), str(row["horizon"]))
            combinations[key]["events"].add(event_key)
            combinations[key]["symbols"].add(symbol)

    def summarize(groups):
        return {key: {
            "event_count": len(value["events"]),
            "symbol_count": len(value["symbols"]),
            "sufficient_for_descriptive_review": (
                len(value["events"]) >= min_events
                and len(value["symbols"]) >= min_symbols),
        } for key, value in sorted(groups.items())}

    return {
        "total_input_rows": len(rows),
        "dimensions": {name: summarize(buckets[name]) for name in DIMENSIONS},
        "market_regime_horizon": summarize(combinations),
        "missing_dimension_counts": dict(missing),
        "thresholds": {"min_events": min_events, "min_symbols": min_symbols},
        "predictive_edge_proven": False,
        "trade_ready": False,
    }
