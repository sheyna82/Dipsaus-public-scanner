"""Research-only chronological next-open evaluation on local OHLCV.

This is an exploratory price-only ranking comparison, NOT an earnings-aware
strategy validation. No trading instructions, network requests or private data.
"""
from dipsaus_offline_ohlcv_csv import load_local_ohlcv_csv
from dipsaus_offline_ohlcv_features import calculate_recovery_features


def evaluate_local_history(stock_path, benchmark_path, *, horizon=10, fee_bps=10):
    if type(horizon) is not int or not 1 <= horizon <= 30:
        return {"status": "REJECTED", "reason": "invalid_horizon"}
    if type(fee_bps) not in (int, float) or not 0 <= fee_bps <= 200:
        return {"status": "REJECTED", "reason": "invalid_fees"}
    stock = load_local_ohlcv_csv(stock_path)
    benchmark = load_local_ohlcv_csv(benchmark_path)
    if stock is None or benchmark is None:
        return {"status": "REJECTED", "reason": "invalid_csv"}
    if [r["date"] for r in stock] != [r["date"] for r in benchmark]:
        return {"status": "REJECTED", "reason": "unaligned_sessions"}
    if len(stock) < 22 + horizon:
        return {"status": "REJECTED", "reason": "insufficient_history"}
    results = []
    for signal in range(21, len(stock) - horizon - 1, horizon + 1):
        # The next session's open is the entry; no same-close fills.
        features = calculate_recovery_features(stock[:signal + 1],
                                               benchmark[:signal + 1], 4)
        if features is None:
            continue
        # Price-only proxy: earnings calendar UNKNOWN, so this is not a
        # tradable recovery baseline score.
        points = (2 if features["relative_strength_20d"] >= 2 else
                  1 if features["relative_strength_20d"] >= 0 else 0)
        points += (2 if 0 < features["return_5d"] <= 8 else
                   1 if -3 <= features["return_5d"] <= 0 else 0)
        points += int(1.1 <= features["volume_ratio_20d"] <= 3)
        points += int(features["atr_pct"] <= 5)
        points += int(features["market_return_5d"] >= -2)
        entry = stock[signal + 1]["open"]
        exit_price = stock[signal + horizon + 1]["close"]
        net_pct = 100 * (exit_price / entry - 1) - 2 * fee_bps / 100
        results.append({"signal_date": stock[signal]["date"],
                        "exit_date": stock[signal + horizon + 1]["date"],
                        "score": points, "net_return_pct": round(net_pct, 6),
                        "market_return_5d": features["market_return_5d"],
                        "atr_pct": features["atr_pct"]})
    selected = [r["net_return_pct"] for r in results if r["score"] >= 5]
    all_returns = [r["net_return_pct"] for r in results]
    return {"status": "EXPLORATORY_ONLY",
            "observations": len(results), "selected_count": len(selected),
            "selected_mean_net_pct": (sum(selected) / len(selected) if selected else None),
            "always_enter_mean_net_pct": (sum(all_returns) / len(all_returns) if all_returns else None),
            "rows": results, "earnings_calendar_verified": False,
            "source_verified": False, "trade_ready": False,
            "limitations": "Single ticker, non-overlapping samples, no survivorship or regime controls; fixed next-open entry and close exit, fee estimate only, no spread/slippage/limit fills, unknown earnings calendar. No predictive claim."}
