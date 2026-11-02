"""Read-only comparison of historical portfolio proxies; no trading decisions.

Only compare runs with explicitly matching sample and accounting assumptions.
"""
from math import isfinite


def compare_historical_portfolios(rows, benchmark_return_pct, comparable=False):
    unknown = {"status": "UNKNOWN", "trade_ready": False, "research_only": True}
    if not comparable or not isinstance(rows, list) or not rows:
        return {**unknown, "reason": "COMPARABILITY_NOT_ESTABLISHED"}
    if isinstance(benchmark_return_pct, bool) or not isinstance(benchmark_return_pct, (int, float)) or not isfinite(benchmark_return_pct):
        return {**unknown, "reason": "INVALID_BENCHMARK"}
    ranked = []
    for row in rows:
        if not isinstance(row, dict):
            return {**unknown, "reason": "INVALID_ROW"}
        keys = ("name", "total_net_return_pct", "holdout_max_drawdown_pct", "mean_exposure")
        if any(key not in row for key in keys) or not isinstance(row["name"], str) or not row["name"]:
            return {**unknown, "reason": "MISSING_ROW_FIELDS"}
        values = [row[key] for key in keys[1:]]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v) for v in values):
            return {**unknown, "reason": "INVALID_NUMERIC_VALUE"}
        ret, dd, exposure = values
        if dd > 0 or not 0 < exposure <= 1:
            return {**unknown, "reason": "INVALID_RISK_OR_EXPOSURE"}
        ranked.append({"name": row["name"], "total_net_return_pct": ret,
                       "holdout_max_drawdown_pct": dd, "mean_exposure": exposure,
                       "excess_vs_benchmark_pct_points": round(ret - benchmark_return_pct, 4),
                       "return_per_exposure_proxy": round(ret / exposure, 4),
                       "risk_adjusted_edge_proven": False})
    ranked.sort(key=lambda x: x["excess_vs_benchmark_pct_points"], reverse=True)
    return {"status": "DESCRIPTIVE_ONLY", "rows": ranked, "trade_ready": False,
            "research_only": True, "exposure_proxy_not_risk_adjusted": True,
            "benchmark_comparability_user_attested": True}
