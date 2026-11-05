"""Offline after-close CSV pilot: real data may be supplied locally, never fetched.

Research score is not a forecast probability. Dates, earnings calendar,
licensing and data adjustments require independent verification.
"""
from dipsaus_offline_ohlcv_csv import load_local_ohlcv_csv
from dipsaus_offline_ohlcv_features import calculate_recovery_features
from dipsaus_offline_recovery_baseline import score_recovery_candidate


def score_local_csv_pair(stock_csv, benchmark_csv, *, days_to_earnings):
    stock = load_local_ohlcv_csv(stock_csv)
    benchmark = load_local_ohlcv_csv(benchmark_csv)
    if stock is None or benchmark is None:
        return {"status": "REJECTED", "reason": "invalid_csv",
                "trade_ready": False, "research_only": True}
    if len(stock) != len(benchmark):
        return {"status": "REJECTED", "reason": "unaligned_sessions",
                "trade_ready": False, "research_only": True}
    features = calculate_recovery_features(stock, benchmark, days_to_earnings)
    if features is None:
        return {"status": "REJECTED", "reason": "invalid_or_unaligned_features",
                "trade_ready": False, "research_only": True}
    score = score_recovery_candidate(features)
    return {"status": "RESEARCH_ONLY", "signal_date": stock[-1]["date"],
            "features": features, "baseline": score,
            "source_verified": False, "historical_performance_validated": False,
            "trade_ready": False, "order_instruction": None,
            "warning": "After-close only; no real-data backtest, verified earnings calendar or verified vendor provenance."}
