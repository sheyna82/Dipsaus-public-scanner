"""Research-only independent benchmark session coverage checks."""
from dipsaus_offline_ohlcv_csv import load_local_ohlcv_csv


def check_benchmark_sessions(stock_csv, benchmark_csv):
    stock = load_local_ohlcv_csv(stock_csv)
    benchmark = load_local_ohlcv_csv(benchmark_csv)
    if stock is None or benchmark is None:
        return {"status": "REJECTED", "reason": "invalid_csv"}
    stock_dates = {bar["date"] for bar in stock}
    benchmark_dates = {bar["date"] for bar in benchmark}
    shared = stock_dates & benchmark_dates
    if len(shared) < 22:
        return {"status": "REJECTED", "reason": "insufficient_overlap"}
    return {"status": "RESEARCH_ONLY", "shared_sessions": len(shared),
            "missing_stock_sessions": len(benchmark_dates - stock_dates),
            "missing_benchmark_sessions": len(stock_dates - benchmark_dates),
            "exact_alignment": stock_dates == benchmark_dates,
            "source_verified": False, "trade_ready": False}
