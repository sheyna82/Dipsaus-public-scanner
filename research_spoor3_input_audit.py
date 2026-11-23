"""Read-only Spoor 3 input coverage audit for existing US pilot report JSON.

Never infer broker prices, financial metrics or market/sector context from
historical close, technical prescreen signals or a source label.
"""
import math

SCORE_FIELDS = ("net_profit_eur", "net_rr", "relative_volume",
                "market_context", "sector_context")
RISK_FIELDS = ("bid", "ask", "average_daily_turnover_eur", "relative_volume",
               "sessions_until_earnings", "earnings_calendar_checked")

def audit_us_recovery_report(report):
    blocked = {"trade_ready": False, "order_placement_enabled": False}
    if not isinstance(report, dict) or not isinstance(report.get("candidates"), list):
        return {**blocked, "status": "AUDIT_INPUT_BLOCKED", "reason": "INVALID_REPORT",
                "candidate_count": 0, "candidates": []}
    results = []
    for item in report["candidates"]:
        if not isinstance(item, dict) or not isinstance(item.get("symbol"), str) or not item["symbol"]:
            return {**blocked, "status": "AUDIT_INPUT_BLOCKED", "reason": "INVALID_CANDIDATE",
                    "candidate_count": 0, "candidates": []}
        # No fallback from last_close_usd, signal_count or research_triage.
        score_missing = [k for k in SCORE_FIELDS if k not in item or item[k] is None]
        score_invalid = [k for k in SCORE_FIELDS if k not in score_missing and
                         (type(item[k]) not in (int, float) or
                          not _finite(item[k]))]
        risk = item.get("risk_inputs")
        risk_missing = [k for k in RISK_FIELDS if not isinstance(risk, dict)
                        or k not in risk or risk[k] is None]
        results.append({"symbol": item["symbol"], "missing_score_fields": score_missing,
                        "invalid_score_fields": score_invalid,
                        "missing_risk_fields": risk_missing,
                        "ready_for_research_review": not (score_missing or score_invalid or risk_missing),
                        **blocked})
    return {**blocked, "status": "INPUT_COVERAGE_AUDIT_ONLY",
            "candidate_count": len(results),
            "complete_count": sum(x["ready_for_research_review"] for x in results),
            "candidates": results,
            "note": "Presence audit only. Values and source authenticity are not verified."}

def _finite(value):
    try:
        return math.isfinite(value)
    except (OverflowError, ValueError):
        return False
