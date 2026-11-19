"""Spoor 2: deterministic, offline runtime-schema quality summary.

This checks structural completeness only. No historical level is certified
as current or tradeable; no network or ntfy transport.
"""
import math
from collections import Counter

def _finite_positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0

def inspect_report(report, market):
    if market not in ("US", "EU") or not isinstance(report, dict) or not isinstance(report.get("candidates"), list):
        return {"status": "INVALID_REPORT", "market": market, "total": 0,
                "blocked": 0, "issues": {"INVALID_REPORT": 1}, "trade_ready": False}
    issues = Counter()
    blocked = 0
    for candidate in report["candidates"]:
        row_issues = []
        if not isinstance(candidate, dict):
            row_issues.append("CANDIDATE_NOT_OBJECT")
        else:
            if not isinstance(candidate.get("symbol"), str) or not candidate["symbol"].strip():
                row_issues.append("SYMBOL_MISSING")
            if market == "US":
                if not _finite_positive(candidate.get("last_close_usd")):
                    row_issues.append("US_LAST_CLOSE_INVALID")
                rm = candidate.get("recovery_map")
                if not isinstance(rm, dict):
                    row_issues.append("US_RECOVERY_MAP_MISSING")
                else:
                    if not _finite_positive(rm.get("recent_10d_low_invalidation_reference_usd")):
                        row_issues.append("US_INVALIDATION_REFERENCE_INVALID")
                    zones = rm.get("historical_overhead_pivot_zones")
                    if not isinstance(zones, list):
                        row_issues.append("US_PIVOTS_MISSING")
                    elif any(not isinstance(z, dict) or not _finite_positive(z.get("low_usd")) for z in zones):
                        row_issues.append("US_PIVOT_INVALID")
            else:
                if not _finite_positive(candidate.get("historical_close")):
                    row_issues.append("EU_HISTORICAL_CLOSE_INVALID")
                if candidate.get("currency") not in ("EUR", "GBp", "GBP", "NOK", "DKK", "SEK", "CHF"):
                    row_issues.append("EU_CURRENCY_UNRECOGNIZED")
                for name in ("historical_first_friction", "historical_meaningful_resistance"):
                    pivot = candidate.get(name)
                    if not isinstance(pivot, dict) or not _finite_positive(pivot.get("price")):
                        row_issues.append("EU_" + name.upper() + "_INVALID")
        if row_issues:
            blocked += 1
            issues.update(set(row_issues))
    return {"status": "SCHEMA_REVIEW_ONLY", "market": market,
            "total": len(report["candidates"]), "blocked": blocked,
            "structurally_parseable": len(report["candidates"]) - blocked,
            "issues": dict(sorted(issues.items())), "trade_ready": False,
            "order_placement_enabled": False}
