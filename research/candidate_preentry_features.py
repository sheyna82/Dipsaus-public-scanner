"""Research-only, predeclared feature definitions for future chronological testing.

These features are calculated at the signal close and never use future bars.
No threshold is fitted here; no trade recommendations are produced.
"""
import statistics

FEATURE_NAMES=("relative_strength_20d_pct","volume_ratio_20d","atr_14_pct")

def pre_entry_features(stock, benchmark, i):
    """Use only stock bars through i, benchmark dates through stock[i] close."""
    if i<21 or i>=len(stock):
        return {"status":"INSUFFICIENT_LOOKBACK","trade_ready":False}
    dates={r["timestamp"]//86400:r for r in benchmark}
    now=stock[i]["timestamp"]//86400
    then=stock[i-20]["timestamp"]//86400
    b_now,b_then=dates.get(now),dates.get(then)
    if not b_now or not b_then or b_then["close"]<=0:
        return {"status":"BENCHMARK_ALIGNMENT_BLOCKED","trade_ready":False}
    if stock[i-20]["close"]<=0 or stock[i]["close"]<=0:
        return {"status":"PRICE_BLOCKED","trade_ready":False}
    volume_base=statistics.mean(r["volume"] for r in stock[i-20:i])
    if volume_base<=0:
        return {"status":"VOLUME_BLOCKED","trade_ready":False}
    tr=[]
    for k in range(i-13,i+1):
        current,prev=stock[k],stock[k-1]
        tr.append(max(current["high"]-current["low"],
                      abs(current["high"]-prev["close"]),
                      abs(current["low"]-prev["close"])))
    stock_ret=stock[i]["close"]/stock[i-20]["close"]-1
    bench_ret=b_now["close"]/b_then["close"]-1
    return {"status":"DESCRIPTIVE_ONLY","trade_ready":False,
            "relative_strength_20d_pct":round(100*(stock_ret-bench_ret),4),
            "volume_ratio_20d":round(stock[i]["volume"]/volume_base,4),
            "atr_14_pct":round(100*statistics.mean(tr)/stock[i]["close"],4)}
