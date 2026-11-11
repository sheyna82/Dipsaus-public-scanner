"""Read-only schema adapters for actual DIPSAUS research report shapes.

Observed schemas: US migration_runtime.latest_us_reports batch candidates with
recovery_map; EU migration_runtime.latest_eu_report candidates with historical
reference levels. Never maps EU research references into verified trade inputs.
"""
from research.spoor2_historical_report_bridge_20261111 import analyze_candidate
import math


def adapt_us_candidate(candidate):
    if not isinstance(candidate, dict):
        return {"status": "UNKNOWN", "trade_ready": False}
    # US uses last_close_usd and recovery_map. Preserve source bar date.
    result = analyze_candidate(candidate)
    result["source_market"] = "US"
    result["source_bar_date"] = candidate.get("last_bar_date")
    return result


def adapt_eu_candidate(candidate):
    if not isinstance(candidate, dict):
        return {"status": "UNKNOWN", "trade_ready": False}
    symbol = candidate.get("symbol")
    if not isinstance(symbol, str) or not symbol.strip():
        return {"status": "UNKNOWN", "trade_ready": False}
    # EU historical_close and historical_first_friction are *not* executable
    # broker quotes and must not be passed as such into US USD calculations.
    def pivot_reference(key):
        pivot = candidate.get(key)
        if not isinstance(pivot, dict):
            return None
        value = pivot.get("price")
        if (not isinstance(value, (int, float)) or isinstance(value, bool)
                or not math.isfinite(value) or value <= 0):
            return None
        return {"price": value, "pivot_touches": pivot.get("pivot_touches"),
                "historical_dates": pivot.get("historical_dates"),
                "verified": False}

    return {
        "symbol": symbol, "source_market": "EU",
        "status": "HISTORICAL_REFERENCES_ONLY",
        "historical_close": candidate.get("historical_close"),
        "historical_first_friction": pivot_reference("historical_first_friction"),
        "historical_meaningful_resistance": pivot_reference("historical_meaningful_resistance"),
        "currency": candidate.get("currency"),
        "currency_unit_verified": False,
        "notification_channel": "RESEARCH",
        "trade_ready": False, "order_placement_enabled": False,
        "blocks": ["EU_EXECUTABLE_BROKER_EVIDENCE_NOT_CONNECTED",
                   "EU_STRUCTURAL_INVALIDATION_NOT_VERIFIED"],
    }


def adapt_runtime_report(report, market):
    if not isinstance(report, dict) or not isinstance(report.get("candidates"), list):
        return {"status": "UNKNOWN", "rows": [], "trade_ready": False}
    if market == "US":
        adapter = adapt_us_candidate
    elif market == "EU":
        adapter = adapt_eu_candidate
    else:
        return {"status": "UNKNOWN", "rows": [], "trade_ready": False}
    return {"status": "RESEARCH_PREVIEW", "market": market,
            "rows": [adapter(x) for x in report["candidates"]],
            "trade_ready": False}
