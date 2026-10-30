"""Descriptive five-year, eight-sector chronological joint-factor replication.

Exploratory extension of a previously inspected hypothesis, NOT an untouched
holdout or evidence of a trading edge. Fail closed on source/session defects.
"""
import json
from urllib.request import Request, urlopen
from research_multisector_five_year_coverage import SECTORS, SOURCE
from research_observed_four_event_spy_risk import bars_from_payload
from dipsaus_offline_structure_intersection_gate import evaluate_structure_intersections


def fetch_payload(symbol):
    with urlopen(Request(SOURCE.format(symbol=symbol),
                         headers={"User-Agent": "Mozilla/5.0"}), timeout=12) as response:
        raw = response.read(1_200_001)
    if len(raw) > 1_200_000:
        raise ValueError("oversized")
    return json.loads(raw)


def evaluate_sector_symbol(symbol, sector, payload, benchmark_payload, *, now_utc=None):
    if symbol not in SECTORS.get(sector, ()):
        return {"symbol": symbol, "sector": sector, "status": "DATA_BLOCKED",
                "reason": "unapproved_sector_symbol", "trade_ready": False}
    stock = bars_from_payload(symbol, payload, now_utc=now_utc)
    spy = bars_from_payload("SPY", benchmark_payload, now_utc=now_utc)
    if stock is None or spy is None:
        return {"symbol": symbol, "sector": sector, "status": "DATA_BLOCKED",
                "reason": "source_quality", "trade_ready": False}
    if [r["date"] for r in stock] != [r["date"] for r in spy]:
        return {"symbol": symbol, "sector": sector, "status": "DATA_BLOCKED",
                "reason": "unaligned_sessions", "stock_bars": len(stock),
                "benchmark_bars": len(spy), "trade_ready": False}
    result = evaluate_structure_intersections(stock, spy)
    return {"symbol": symbol, "sector": sector, **result,
            "observed_source": "unverified_yahoo_daily",
            "corporate_actions_verified": False, "earnings_asof_verified": False,
            "survivorship_free": False, "independent_untouched_holdout": False,
            "trade_ready": False}


if __name__ == "__main__":
    try:
        spy = fetch_payload("SPY")
    except (OSError, ValueError, TimeoutError, UnicodeError, TypeError, KeyError):
        spy = None
    for sector, symbols in SECTORS.items():
        for symbol in symbols:
            try:
                if spy is None:
                    raise ValueError("benchmark_unavailable")
                result = evaluate_sector_symbol(symbol, sector, fetch_payload(symbol), spy)
            except (OSError, ValueError, TimeoutError, UnicodeError, TypeError, KeyError):
                result = {"symbol": symbol, "sector": sector, "status": "DATA_BLOCKED",
                          "reason": "fetch_failed", "trade_ready": False}
            print(json.dumps(result, sort_keys=True))
