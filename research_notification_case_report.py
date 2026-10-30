"""Conservative signal case reporting from timestamped historical daily bars.

Never infer an actual fill, signal quote or positive outcome from a phone screenshot.
"""
from datetime import datetime, timezone
from research_notification_pre_signal import pre_signal_context
from research_notification_forward_returns import forward_returns
from research_notification_relative_performance import relative_performance

def case_report(symbol, signal_utc, stock_bars, benchmark_bars=None, cost_bps=30):
    if not isinstance(signal_utc, datetime) or signal_utc.tzinfo is None or signal_utc.utcoffset().total_seconds()!=0:
        raise ValueError("verified_utc_timestamp_required")
    if not symbol:
        raise ValueError("symbol_required")
    # Historical bar timestamps are source UTC, but a daily bar may include
    # trades after the signal. Exclude the entire UTC signal date.
    signal_day=signal_utc.date().isoformat()
    prior=[b for b in stock_bars if datetime.fromtimestamp(b["timestamp"],timezone.utc).date().isoformat()<signal_day]
    before=pre_signal_context(signal_utc,prior)
    def normalize(bars):
        return [{"date":datetime.fromtimestamp(b["timestamp"],timezone.utc).date().isoformat(),
                 "open":b["open"],"close":b["close"]} for b in bars]
    after=forward_returns(signal_utc,normalize(stock_bars),round_trip_cost_bps=cost_bps)
    benchmark=(forward_returns(signal_utc,normalize(benchmark_bars),round_trip_cost_bps=cost_bps)
               if benchmark_bars is not None else None)
    relative={}
    for h, outcome in after.items():
        other=benchmark.get(h) if benchmark else None
        relative[h]=relative_performance(outcome,other) if outcome is not None and other is not None else None
    return {"symbol":symbol,"signal_utc":signal_utc.isoformat(),
            "pre_signal":before,"forward_proxy":after,"benchmark_relative":relative,
            "data_caveats":["daily bars not broker execution quotes",
                            "calendar and corporate actions unverified",
                            "no intraday signal-time reconstruction",
                            "round-trip costs assumed, not observed"],
            "research_only":True,"trade_ready":False}
