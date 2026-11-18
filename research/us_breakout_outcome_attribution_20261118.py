"""Offline, privacy-minimal US breakout/retest outcome attribution.

Counts only *observed* evidence. Does not infer later prices from the
historical snapshot. Never emits symbols, timestamps, source IDs or raw bars.
"""
from research.us_breakout_retest_shadow_20261118 import audit_breakout_retest

def aggregate_watch_outcomes(records):
    base = {"status": "BLOCKED", "trade_ready": False, "notify": False,
            "automatic_orders": False, "order_placement_enabled": False,
            "research_only": True}
    if not isinstance(records, list):
        return {**base, "blocks": ["INVALID_RECORDS"]}
    counts = {s: 0 for s in ("WATCH_UNVERIFIED", "BREAKOUT_OBSERVED",
                              "RETEST_OBSERVED", "RESEARCH_REVIEW", "BLOCKED")}
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            return {**base, "blocks": ["INVALID_RECORD"]}
        symbol = record.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip() or symbol in seen:
            return {**base, "blocks": ["DUPLICATE_OR_MISSING_SYMBOL"]}
        seen.add(symbol)
        result = audit_breakout_retest(record)
        counts[result["status"]] += 1
    return {**base, "status": "AGGREGATED_RESEARCH_ONLY",
            "total": len(records), "counts": counts,
            "breakout_observed_total": counts["BREAKOUT_OBSERVED"] +
                                       counts["RETEST_OBSERVED"] +
                                       counts["RESEARCH_REVIEW"],
            "retest_and_reclaim_observed_total": counts["RESEARCH_REVIEW"],
            "verified_trade_opportunities": 0,
            "limitations": ["Observed pattern stages only, not a win-rate or backtest",
                            "No verified independent source or executable broker evidence",
                            "Counts must not be interpreted as profitability"]}
