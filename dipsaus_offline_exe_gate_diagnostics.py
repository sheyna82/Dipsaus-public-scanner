"""Explain why the frozen EXE downside rule did not trigger.

Purely descriptive; does not change any trigger or trading behavior.
"""
from portfolio_downside_research import evaluate_intraday_downside


def explain_no_signal(bars):
    counts = {"evaluated_windows": 0, "drawdown_gate": 0,
              "lower_low_gate": 0, "red_candles_gate": 0,
              "all_three_gates": 0}
    for end in range(31, len(bars)+1):
        window = bars[:end]
        result = evaluate_intraday_downside(
            [x["close"] for x in window], [x["high"] for x in window],
            [x["low"] for x in window], [x["open"] for x in window],
            enabled=True)
        if result["status"] != "RESEARCH_ONLY":
            return {"status": "DATA_BLOCKED", "reason": result["status"]}
        counts["evaluated_windows"] += 1
        counts["drawdown_gate"] += int(result["drawdown_pct"] <= -2)
        counts["lower_low_gate"] += int(result["lower_low"])
        counts["red_candles_gate"] += int(result["red_last5"] >= 3)
        counts["all_three_gates"] += int(result["trigger"])
    return {"status": "DESCRIPTIVE_GATE_COUNTS", **counts,
            "thresholds_unchanged": True, "trade_ready": False}
