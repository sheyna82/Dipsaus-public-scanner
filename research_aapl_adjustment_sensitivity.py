"""Sensitivity experiment: consistently rescale all Apple OHLC with adjusted-close factor.

This is a *scenario*, not verified total-return pricing. Multiplying the
historical open/high/low/close by AdjClose/Close assumes a common daily
factor; it must not be promoted to live trading or validated backtests.
"""
import csv
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from research_audit_aapl_spy_adjustments import read_public_csv, APPLE_URL
from research_reproduce_aapl_spy import download_spy_csv
from dipsaus_offline_price_history_eval import evaluate_local_history

HEADER = "Date,Open,High,Low,Close,Volume"


def make_adjusted_apple_csv(rows):
    lines = [HEADER]
    for row in rows:
        close = float(row["AAPL.Close"])
        adjusted = float(row["AAPL.Adjusted"])
        if close <= 0 or adjusted <= 0:
            raise ValueError("invalid_apple_adjustment")
        factor = adjusted / close
        prices = [float(row["AAPL." + key]) * factor
                  for key in ("Open", "High", "Low", "Close")]
        lines.append(",".join([row["Date"]] + [str(x) for x in prices] +
                              [row["AAPL.Volume"]]))
    return "\n".join(lines) + "\n"


def run_adjustment_sensitivity():
    apple_rows = read_public_csv(APPLE_URL)
    if len(apple_rows) != 506:
        raise ValueError("unexpected_apple_rows")
    spy = download_spy_csv()
    dates = [r["Date"] for r in apple_rows]
    if any(d not in spy for d in dates):
        raise ValueError("missing_spy_session")
    benchmark = [HEADER] + [
        ",".join([d] + [spy[d][k] for k in
                         ("open", "high", "low", "close", "volume")])
        for d in dates]
    raw_apple = [HEADER] + [
        ",".join([r["Date"]] + [r["AAPL." + k] for k in
                              ("Open", "High", "Low", "Close", "Volume")])
        for r in apple_rows]
    with TemporaryDirectory() as folder:
        folder = Path(folder)
        paths = [folder / name for name in ("raw.csv", "adjusted.csv", "spy.csv")]
        for path, data in zip(paths, ("\n".join(raw_apple) + "\n",
                                      make_adjusted_apple_csv(apple_rows),
                                      "\n".join(benchmark) + "\n")):
            path.write_text(data, encoding="utf-8")
        raw = evaluate_local_history(paths[0], paths[2])
        adjusted = evaluate_local_history(paths[1], paths[2])
    if raw["status"] != "EXPLORATORY_ONLY" or adjusted["status"] != "EXPLORATORY_ONLY":
        raise ValueError("evaluation_rejected")
    def summary(r):
        return {k: r[k] for k in ("observations", "selected_count",
                "selected_mean_net_pct", "always_enter_mean_net_pct")}
    return {"raw": summary(raw), "adjusted_apple_ohlc_scenario": summary(adjusted),
            "method": "AAPL daily AdjClose/Close multiplied into every OHLC field",
            "spy_adjustment_policy_verified": False,
            "apple_adjustment_policy_verified": False,
            "scenario_only": True, "trade_ready": False}


if __name__ == "__main__":
    print(json.dumps(run_adjustment_sensitivity(), indent=2, sort_keys=True))
