"""Run matched returns and downside on identical offline historical events.

The caller supplies predeclared signal indices; this module does not select
or optimize signals, download data, or imply predictive validity.
"""
from dipsaus_offline_matched_benchmark import matched_event_comparison
from dipsaus_offline_matched_downside import matched_downside
from dipsaus_offline_return_risk_pairing import pair_return_and_downside


def evaluate_matched_return_risk(stock, benchmark, signal_indices, *,
                                 horizon=10, fee_bps_each_side=10):
    returns = matched_event_comparison(stock, benchmark, signal_indices,
                                       horizon=horizon,
                                       fee_bps_each_side=fee_bps_each_side)
    if returns.get("status") != "EXPLORATORY_MATCHED_DATES":
        return {"status": "DATA_BLOCKED", "reason": "return_" + returns.get("reason", "unknown"),
                "trade_ready": False}
    downside = matched_downside(stock, benchmark, signal_indices, horizon=horizon)
    if downside.get("status") != "EXPLORATORY_MATCHED_DOWNSIDE":
        return {"status": "DATA_BLOCKED", "reason": "downside_" + downside.get("reason", "unknown"),
                "trade_ready": False}
    paired = pair_return_and_downside(returns, downside)
    if paired.get("status") != "EXPLORATORY_RETURN_RISK_PAIRING":
        return {"status": "DATA_BLOCKED", "reason": "pairing_" + paired.get("reason", "unknown"),
                "trade_ready": False}
    return {"status": "EXPLORATORY_COMBINED_RETURN_RISK",
            "events": paired["events"],
            "mean_excess_pct_points": returns["mean_excess_pct_points"],
            "mean_extra_adverse_pct_points": downside["mean_extra_adverse_pct_points"],
            "beat_market_count": paired["beat_market_count"],
            "beat_market_with_deeper_drawdown_count": paired["beat_market_with_deeper_drawdown_count"],
            "rows": paired["rows"],
            "independent_holdout": False, "source_verified": False,
            "predictive_edge_proven": False, "trade_ready": False}
