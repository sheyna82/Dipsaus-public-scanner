"""Audit known price-adjustment incompatibilities in the public AAPL/SPY pilot.

The public Apple example includes AAPL.Adjusted while its OHLC prices are
unadjusted; the SPY sample contains dividends/splits columns. This audit
does not infer a provider's corporate-action policy or repair OHLC bars.
"""
import csv
import io
import json
from urllib.request import Request, urlopen

APPLE_URL = "https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv"
SPY_URL = "https://raw.githubusercontent.com/hackingthemarkets/datasets/master/spy.csv"


def read_public_csv(url, max_bytes=500_000):
    with urlopen(Request(url, headers={"User-Agent": "DipsausOfflineResearch/1.0"}), timeout=20) as response:
        payload = response.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise ValueError("dataset_too_large")
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))


def audit_adjustments():
    apple = read_public_csv(APPLE_URL)
    spy = read_public_csv(SPY_URL)
    if len(apple) != 506:
        raise ValueError("unexpected_apple_sample")
    spy_dates = {r["date"]: r for r in spy}
    dates = [r["Date"] for r in apple]
    if any(day not in spy_dates for day in dates):
        raise ValueError("missing_spy_date")
    # The ratio is informative but does not prove why it differs.
    differences = sum(abs(float(r["AAPL.Close"]) - float(r["AAPL.Adjusted"])) > 0.0001 for r in apple)
    dividend_dates = [day for day in dates if float(spy_dates[day]["dividends"]) != 0]
    split_dates = [day for day in dates if float(spy_dates[day]["splits"]) != 0]
    return {
        "apple_sessions": len(dates),
        "apple_close_differs_from_adjusted_sessions": differences,
        "spy_dividend_event_sessions": len(dividend_dates),
        "spy_split_event_sessions": len(split_dates),
        "spy_dividend_event_dates": dividend_dates,
        "spy_split_event_dates": split_dates,
        "adjustment_compatibility_verified": False,
        "raw_ohlc_cross_provider_comparison_caution": differences > 0 or bool(dividend_dates or split_dates),
        "trade_ready": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit_adjustments(), indent=2, sort_keys=True))
