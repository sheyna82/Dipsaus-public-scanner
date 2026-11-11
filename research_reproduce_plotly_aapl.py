"""Reproducible real-price AAPL pilot from Plotly's public example CSV.

No automatic invocation in production or CI. Uses network only when explicitly
run by researcher. Example source is not a licensed institutional backtest feed.
"""
import csv
import io
import json
from urllib.request import Request, urlopen
from dipsaus_offline_price_history_eval import evaluate_local_history
from tempfile import TemporaryDirectory
from pathlib import Path

SOURCE = "https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv"
EXPECTED_FIRST = "2015-02-17"
EXPECTED_LAST = "2017-02-16"
EXPECTED_COUNT = 506


def download_example_prices():
    request = Request(SOURCE, headers={"User-Agent": "DipsausOfflineResearch/1.0"})
    with urlopen(request, timeout=20) as response:
        content = response.read(250_001)
    if len(content) > 250_000:
        raise ValueError("example_dataset_too_large")
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    expected = ("Date", "AAPL.Open", "AAPL.High", "AAPL.Low", "AAPL.Close", "AAPL.Volume")
    if not set(expected).issubset(reader.fieldnames or []):
        raise ValueError("unexpected_columns")
    rows = list(reader)
    if (len(rows) != EXPECTED_COUNT or rows[0]["Date"] != EXPECTED_FIRST
            or rows[-1]["Date"] != EXPECTED_LAST):
        raise ValueError("unexpected_dataset_version")
    lines = ["Date,Open,High,Low,Close,Volume"]
    for row in rows:
        lines.append(",".join(row[k] for k in expected))
    return "\n".join(lines) + "\n"


def run_example():
    data = download_example_prices()
    with TemporaryDirectory() as folder:
        stock = Path(folder) / "apple.csv"
        stock.write_text(data, encoding="utf-8")
        # The same ticker is NOT a valid independent benchmark. This exercise
        # is strictly a reproducibility check of the price-only pipeline.
        result = evaluate_local_history(stock, stock)
    if result["status"] != "EXPLORATORY_ONLY":
        raise ValueError("evaluation_failed")
    return {"dataset": SOURCE, "observations": result["observations"],
            "selected_count": result["selected_count"],
            "selected_mean_net_pct": result["selected_mean_net_pct"],
            "all_entry_mean_net_pct": result["always_enter_mean_net_pct"],
            "benchmark": "AAPL itself (invalid as independent benchmark)",
            "trade_ready": False, "reproducibility_only": True}


if __name__ == "__main__":
    print(json.dumps(run_example(), indent=2, sort_keys=True))
