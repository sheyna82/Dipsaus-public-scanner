"""Reproduce exploratory AAPL vs independent SPY benchmark using public examples.

Not a validated backtest: two third-party sample datasets may differ in
split/dividend adjustments; no historical earnings or survivorship controls.
"""
import csv
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen

from research_reproduce_plotly_aapl import download_example_prices
from dipsaus_offline_price_history_eval import evaluate_local_history

SPY_SOURCE = "https://raw.githubusercontent.com/hackingthemarkets/datasets/master/spy.csv"
MAX_BYTES = 500_000


def download_spy_csv():
    request = Request(SPY_SOURCE, headers={"User-Agent": "DipsausOfflineResearch/1.0"})
    with urlopen(request, timeout=20) as response:
        payload = response.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES:
        raise ValueError("spy_dataset_too_large")
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    needed = ("date", "open", "high", "low", "close", "volume")
    if not set(needed).issubset(reader.fieldnames or []):
        raise ValueError("unexpected_spy_columns")
    rows = list(reader)
    if not rows or rows[0]["date"] > "2015-02-17" or rows[-1]["date"] < "2017-02-16":
        raise ValueError("spy_coverage_incomplete")
    return {r["date"]: r for r in rows}


def run_independent_benchmark():
    apple = download_example_prices()
    spy = download_spy_csv()
    apple_lines = apple.strip().splitlines()
    dates = [r.split(",", 1)[0] for r in apple_lines[1:]]
    if len(dates) != 506 or any(day not in spy for day in dates):
        raise ValueError("missing_benchmark_sessions")
    benchmark = ["Date,Open,High,Low,Close,Volume"]
    for day in dates:
        row = spy[day]
        benchmark.append(",".join([day] + [row[k] for k in ("open", "high", "low", "close", "volume")]))
    with TemporaryDirectory() as folder:
        stock_file, benchmark_file = Path(folder) / "apple.csv", Path(folder) / "spy.csv"
        stock_file.write_text(apple, encoding="utf-8")
        benchmark_file.write_text("\n".join(benchmark) + "\n", encoding="utf-8")
        result = evaluate_local_history(stock_file, benchmark_file)
    if result["status"] != "EXPLORATORY_ONLY":
        raise ValueError("evaluation_failed")
    return {"stock_source": "plotly/datasets finance-charts-apple.csv",
            "benchmark_source": SPY_SOURCE, "benchmark": "SPY (independent symbol)",
            "observations": result["observations"],
            "selected_count": result["selected_count"],
            "selected_mean_net_pct": result["selected_mean_net_pct"],
            "all_entry_mean_net_pct": result["always_enter_mean_net_pct"],
            "all_stock_sessions_have_spy": True,
            "adjustment_compatibility_verified": False,
            "historical_earnings_verified": False, "holdout_validated": False,
            "trade_ready": False}


if __name__ == "__main__":
    print(json.dumps(run_independent_benchmark(), indent=2, sort_keys=True))
