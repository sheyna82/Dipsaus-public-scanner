"""Out-of-sample feature-filter experiment, research-only.

Predeclared median filters are fitted on the first 65% of each stock history;
the last 35% is never used to set thresholds. SPY is used only for US stocks.
"""
import json, statistics, hashlib, argparse
from pathlib import Path
from candidate_entry_snapshot import bars
from candidate_regime_cost_validation import RESEARCH_UNIVERSE, features, nonoverlap, MIN_TRAIN
from candidate_preentry_features import pre_entry_features
from candidate_feature_thresholds import training_median_thresholds, label
from candidate_benchmark_excess import compare, PATTERNS, HORIZON, COST_BPS
from candidate_portfolio_capacity import simulate, calendar_capital_occupancy

def evaluate_filtered(stock, benchmark, pattern):
    cutoff=max(MIN_TRAIN,int(len(stock)*.65))
    training=[]
    for i in range(50,cutoff):
        if features(stock,i)[pattern]:
            training.append((i,pre_entry_features(stock,benchmark,i)))
    fitted=training_median_thresholds(training)
    if fitted["status"]!="TRAINING_ONLY_THRESHOLDS":
        return {"status":fitted["status"],"trade_ready":False,
                "training_pattern_observations":len(training)}
    base=nonoverlap([i for i in range(cutoff,len(stock)-HORIZON)
                     if features(stock,i)[pattern]],HORIZON)
    # Filter AFTER baseline signal non-overlap to prevent changing event selection.
    selected=[]
    for i in base:
        f=pre_entry_features(stock,benchmark,i)
        decision=label(f,fitted)
        if decision["status"]=="RESEARCH_ONLY" and all(decision["passes"].values()):
            selected.append(i)
    dates={r["timestamp"]//86400:r for r in benchmark}
    excess=[]
    adverse=[]
    for i in selected:
        start=dates.get(stock[i+1]["timestamp"]//86400)
        end=dates.get(stock[i+HORIZON]["timestamp"]//86400)
        if not start or not end or start["open"]<=0:
            return {"status":"BLOCKED_BENCHMARK_ALIGNMENT","trade_ready":False}
        entry=stock[i+1]["open"]
        if entry<=0:return {"status":"BLOCKED_STOCK_OPEN","trade_ready":False}
        stock_net=100*(stock[i+HORIZON]["close"]/entry-1)-COST_BPS/100
        bench_ret=100*(end["close"]/start["open"]-1)
        excess.append(stock_net-bench_ret)
        adverse.append(100*(min(r["low"] for r in stock[i+1:i+HORIZON+1])/entry-1))
    return {"status":"DESCRIPTIVE_ONLY" if excess else "NO_FILTERED_SIGNALS",
            "trade_ready":False,"training_pattern_observations":len(training),
            "training_thresholds":fitted["thresholds"],
            "baseline_signal_n":len(base),"filtered_signal_n":len(selected),
            "median_excess_pct":round(statistics.median(excess),3) if excess else None,
            "median_mae_pct":round(statistics.median(adverse),3) if adverse else None,
            "worst_mae_pct":round(min(adverse),3) if adverse else None,
            "inference_valid":False}


def portfolio_oos_pair(stock_by_symbol, benchmark, pattern):
    """Matched per-symbol held-out event pool; no threshold fitting on test dates.

    Dates are Unix epoch days. This is realized closed-trade capacity research,
    not a mark-to-market drawdown or executable trading system.
    """
    baseline, filtered, exclusions = [], [], {}
    candidate_audit = []
    # Common calendar start is determined from eligible stock training cutoffs,
    # never from future returns or observed test performance.
    eligible = {symbol: stock for symbol, stock in stock_by_symbol.items()
                if isinstance(symbol, str) and stock and len(stock) >= 750}
    common_test_start_day = max(
        (stock[max(MIN_TRAIN, int(len(stock) * .65)) + 1]["timestamp"] // 86400
         for stock in eligible.values()
         if max(MIN_TRAIN, int(len(stock) * .65)) + 1 < len(stock)),
        default=None)
    common_test_end_day = min(
        (stock[-1]["timestamp"] // 86400 for stock in eligible.values()),
        default=None)
    comparable_calendar = (common_test_start_day is not None and
                           common_test_end_day is not None and
                           common_test_start_day <= common_test_end_day)
    for symbol, stock in sorted(stock_by_symbol.items()):
        if not isinstance(symbol, str) or not stock or len(stock) < 750:
            exclusions[str(symbol)] = "INSUFFICIENT_HISTORY"
            continue
        if not comparable_calendar:
            exclusions[symbol] = "NO_SHARED_OUT_OF_SAMPLE_CALENDAR"
            continue
        cutoff = max(MIN_TRAIN, int(len(stock) * .65))
        training = [(i, pre_entry_features(stock, benchmark, i))
                    for i in range(50, cutoff) if features(stock, i)[pattern]]
        fitted = training_median_thresholds(training)
        if fitted["status"] != "TRAINING_ONLY_THRESHOLDS":
            exclusions[symbol] = fitted["status"]
            continue
        candidates = nonoverlap(
            [i for i in range(cutoff, len(stock) - HORIZON)
             if features(stock, i)[pattern]], HORIZON)
        for i in candidates:
            entry, end = stock[i + 1], stock[i + HORIZON]
            if (common_test_start_day is not None and
                    entry["timestamp"] // 86400 < common_test_start_day):
                continue
            if (common_test_end_day is not None and
                    end["timestamp"] // 86400 > common_test_end_day):
                continue
            if entry["open"] <= 0:
                exclusions[symbol] = "INVALID_ENTRY_OPEN"
                continue
            trade = {"symbol": symbol, "entry_day": entry["timestamp"] // 86400,
                     "exit_day": end["timestamp"] // 86400,
                     "net_return_pct": 100 * (end["close"] / entry["open"] - 1)
                                       - COST_BPS / 100}
            baseline.append(trade)
            signal_features = pre_entry_features(stock, benchmark, i)
            decision = label(signal_features, fitted)
            selected = (decision["status"] == "RESEARCH_ONLY"
                        and all(decision["passes"].values()))
            candidate_audit.append({
                "symbol": symbol,
                "signal_day": stock[i]["timestamp"] // 86400,
                "entry_day": trade["entry_day"],
                "exit_day": trade["exit_day"],
                "features_at_signal_close": signal_features,
                "training_thresholds": fitted["thresholds"],
                "filter_passes": decision.get("passes"),
                "filter_selected": selected,
                "historical_net_return_pct_outcome_not_selection_input": trade["net_return_pct"]})
            if selected:
                filtered.append(trade.copy())
    base_result = simulate(baseline)
    filtered_result = simulate(filtered)
    comparison_status = (
        "BLOCKED_NO_SHARED_OUT_OF_SAMPLE_CALENDAR" if not comparable_calendar
        else "NO_BASELINE_OUT_OF_SAMPLE_SIGNALS" if not baseline
        else "NO_CAPACITY_ACCEPTED_BASELINE_SIGNALS" if not base_result["accepted_n"]
        else "CALENDAR_MATCHED_DESCRIPTIVE_ONLY")
    return {"research_only": True, "trade_ready": False,
            "independent_prospective_validation": False,
            "daily_mark_to_market_verified": False,
            "same_baseline_event_pool": True,
            "candidate_audit": sorted(candidate_audit, key=lambda row: (row["entry_day"], row["symbol"])),
            "candidate_audit_provenance": {
                "all_eligible_baseline_events_included": True,
                "feature_timestamp": "signal_session_close_before_next_session_entry",
                "training_thresholds": "per_symbol_training_history_only",
                "future_outcome_not_used_for_filter_selection": True,
                "selection_priority_audit_not_yet_evaluated": True,
                "trade_ready": False},
            "cost_bps": COST_BPS, "horizon_sessions": HORIZON,
            "common_test_start_day": common_test_start_day,
            "common_test_end_day": common_test_end_day,
            "comparable_calendar": comparable_calendar,
            "comparison_status": comparison_status,
            "excluded_symbols": exclusions,
            "baseline": base_result, "filtered": filtered_result,
            "capital_occupancy": {
                "baseline": calendar_capital_occupancy(base_result),
                "filtered": calendar_capital_occupancy(filtered_result)},
            "equity_risk": {
                "baseline": {"status": "NOT_EVALUATED",
                             "reason": "INDEPENDENT_DAILY_MARKS_AND_RECONCILED_FILLS_NOT_PROVIDED"},
                "filtered": {"status": "NOT_EVALUATED",
                             "reason": "INDEPENDENT_DAILY_MARKS_AND_RECONCILED_FILLS_NOT_PROVIDED"}},
            "realized_pnl_difference": round(
                filtered_result["realized_pnl"] - base_result["realized_pnl"], 2),
            "accepted_trade_count_difference": (
                filtered_result["accepted_n"] - base_result["accepted_n"]),
            "limitations": ["Convenience universe, correlated securities and survivorship bias",
                            "No daily equity or verified execution fills",
                            "Common calendar start and end enforced; calendar quality unverified",
                            "Filter thresholds fitted separately per stock; no cross-sectional selection calibration"]}

def main(snapshot_input=None):
    if snapshot_input is not None:
        snapshot = json.loads(Path(snapshot_input).read_text(encoding="utf-8"))
        if snapshot.get("format") != "DIPSAUS_OOS_OHLCV_V1":
            raise ValueError("INVALID_SNAPSHOT_FORMAT")
        if snapshot.get("benchmark", {}).get("symbol") != "SPY":
            raise ValueError("INVALID_SNAPSHOT_BENCHMARK")
        frozen_benchmark = snapshot["benchmark"]["bars"]
        frozen_stocks = snapshot["stocks"]
        if not isinstance(frozen_benchmark, list) or not isinstance(frozen_stocks, dict):
            raise ValueError("INVALID_SNAPSHOT_CONTENT")
    else:
        frozen_benchmark, frozen_stocks = None, None
    output={"research_only":True,"trade_ready":False,
            "method":"TRAINING_MEDIAN_ALL_THREE_FEATURES_OUT_OF_SAMPLE",
            "horizon_sessions":HORIZON,"cost_bps":COST_BPS,
            "limitations":["Convenience universe and correlated events",
                           "Median feature filters are hypotheses, not tuned or validated alpha",
                           "Yahoo unadjusted OHLCV and SPY, no corporate-action audit",
                           "No sector or event controls, no broker execution evidence"],
            "candidates":[]}
    portfolio_stocks={}
    try:benchmark=frozen_benchmark if snapshot_input is not None else bars("SPY",history_range="5y")
    except Exception:benchmark=[]
    for symbol in RESEARCH_UNIVERSE:
        if "." in symbol:
            output["candidates"].append({"symbol":symbol,"status":"BLOCKED_CROSS_CURRENCY_BENCHMARK"})
            continue
        try:
            if not benchmark:raise ValueError("BENCHMARK_UNAVAILABLE")
            stock=(frozen_stocks[symbol] if snapshot_input is not None
                   else bars(symbol,history_range="5y"))
            if len(stock)<750:raise ValueError("INSUFFICIENT_HISTORY")
            portfolio_stocks[symbol]=stock
            output["candidates"].append({"symbol":symbol,
                "patterns":{p:{"baseline":compare(stock,benchmark,p),
                                "filtered":evaluate_filtered(stock,benchmark,p)}
                            for p in PATTERNS}})
        except Exception as exc:
            output["candidates"].append({"symbol":symbol,"status":"DATA_BLOCKED",
                                         "error_type":type(exc).__name__})
    def data_digest(rows):
        payload = json.dumps(rows, sort_keys=True, separators=(',', ':'), allow_nan=False)
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()
    snapshot = {"format": "DIPSAUS_OOS_OHLCV_V1",
                "benchmark": {"symbol": "SPY", "bars": benchmark},
                "stocks": {symbol: portfolio_stocks[symbol] for symbol in sorted(portfolio_stocks)}}
    snapshot_path = Path("reports/candidate_feature_oos_input_snapshot.json")
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(snapshot, sort_keys=True, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    output["input_data_provenance"] = {
        "hash_algorithm": "sha256_canonical_json_sorted_keys",
        "benchmark": {"symbol": "SPY", "rows": len(benchmark),
                      "sha256": data_digest(benchmark)},
        "stocks": {symbol: {"rows": len(rows), "sha256": data_digest(rows)}
                   for symbol, rows in sorted(portfolio_stocks.items())},
        "data_frozen": True,
        "snapshot_file": str(snapshot_path),
        "snapshot_format": "DIPSAUS_OOS_OHLCV_V1",
        "replay_from_artifact": snapshot_input is not None,
        "limitations": ["Snapshot retains downloaded raw unadjusted bars but has not been independently verified",
                        "Provider may revise historical unadjusted OHLCV"]}
    output["portfolio_oos"]={
        p:portfolio_oos_pair(portfolio_stocks,benchmark,p)
        for p in PATTERNS}
    output["portfolio_oos_provenance"]={
        "universe":"US-only symbols successfully loaded from RESEARCH_UNIVERSE",
        "loaded_symbols":sorted(portfolio_stocks),
        "benchmark":"SPY",
        "source":"Same five-year OHLCV downloads as candidate-level evaluation",
        "independent_data_validation":False,
        "independent_prospective_validation":False,
        "trade_ready":False}
    dest=Path("reports/candidate_feature_oos.json")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(output,indent=2),encoding="utf-8")
    print(json.dumps({"research_only":True,"candidates":len(output["candidates"])}))

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", help="Replay from archived OHLCV JSON without network")
    args = parser.parse_args()
    main(snapshot_input=args.snapshot)
