"""Aggregate sector replication cautiously without treating symbols as independent.

Reads newline-delimited JSON output from the existing historical replication
runner. Descriptive only; rejects invalid, duplicate or incomplete coverage.
"""
import json
import sys
from research_multisector_five_year_coverage import SECTORS

EXPECTED = {symbol: sector for sector, symbols in SECTORS.items() for symbol in symbols}


def summarize(records):
    by_symbol = {}
    for row in records:
        symbol = row.get("symbol")
        if symbol not in EXPECTED or symbol in by_symbol or row.get("sector") != EXPECTED[symbol]:
            return {"status": "DATA_BLOCKED", "reason": "invalid_or_duplicate_universe", "trade_ready": False}
        by_symbol[symbol] = row
    if set(by_symbol) != set(EXPECTED):
        return {"status": "DATA_BLOCKED", "reason": "incomplete_universe", "trade_ready": False}
    valid = [row for row in by_symbol.values() if row.get("status") == "EXPLORATORY_JOINT_FACTOR_DIAGNOSTIC"]
    blocked = [s for s, row in by_symbol.items() if row.get("status") != "EXPLORATORY_JOINT_FACTOR_DIAGNOSTIC"]
    if not valid:
        return {"status": "DATA_BLOCKED", "reason": "no_valid_symbols", "trade_ready": False}
    comparisons = {}
    for key in ("atr_and_structure", "atr_and_market", "atr_structure_market"):
        better, worse, equal, empty, missed, evaluated = 0, 0, 0, 0, 0, 0
        for row in valid:
            base = row["baseline_test"]["mean_net_return_pct"]
            factor = row["factors"][key]
            selected = factor["selected"]
            missed += factor["missed_winning_events"]
            evaluated += row["baseline_test"]["events"]
            if selected is None:
                empty += 1
                continue
            diff = selected["mean_net_return_pct"] - base
            better += diff > 0
            worse += diff < 0
            equal += diff == 0
        comparisons[key] = {"symbols_better": better, "symbols_worse": worse,
                            "symbols_equal": equal, "symbols_without_selected": empty,
                            "missed_winning_events_sum": missed,
                            "test_events_sum": evaluated}
    return {"status": "EXPLORATORY_SECTOR_REPLICATION_SUMMARY",
            "symbols_evaluated": len(valid), "symbols_blocked": sorted(blocked),
            "comparisons": comparisons, "symbol_dependence_unadjusted": True,
            "survivorship_free": False, "independent_holdout": False,
            "corporate_actions_verified": False, "trade_ready": False}


if __name__ == "__main__":
    rows = [json.loads(line) for line in sys.stdin if line.strip()]
    print(json.dumps(summarize(rows), sort_keys=True))
