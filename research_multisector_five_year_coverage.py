"""Five-year coverage feasibility probe, isolated from the frozen 2y experiment.

This does NOT add symbols to the four-symbol test or claim a new holdout.
It checks availability only; corporate actions and earnings remain unverified.
"""
import json
from urllib.request import Request, urlopen
from research_probe_alternative_daily_source import BASE

SECTORS = {
    "technology": ("AAPL", "MSFT"),
    "healthcare": ("JNJ", "PFE"),
    "industrials": ("CAT", "DE"),
    "energy": ("XOM", "CVX"),
    "financials": ("JPM", "BAC"),
    "consumer": ("WMT", "HD"),
    "materials": ("NEM", "FCX"),
    "utilities": ("NEE", "DUK"),
}
BENCHMARK = "SPY"
SOURCE = BASE.replace("range=3mo", "range=5y")


def inspect_payload(symbol, payload):
    try:
        result = payload["chart"]["result"]
        if not isinstance(result, list) or len(result) != 1:
            raise ValueError("missing_result")
        item = result[0]
        timestamps = item["timestamp"]
        quote = item["indicators"]["quote"][0]
        if not isinstance(timestamps, list) or len(timestamps) < 500:
            raise ValueError("short_history")
        if any(not isinstance(quote.get(k), list) or len(quote[k]) != len(timestamps)
               for k in ("open", "high", "low", "close", "volume")):
            raise ValueError("incomplete_ohlcv")
        if len(set(timestamps)) != len(timestamps) or timestamps != sorted(timestamps):
            raise ValueError("invalid_timestamps")
        return {"symbol": symbol, "status": "STRUCTURAL_HISTORY_OBSERVED",
                "bars": len(timestamps), "verified": False, "trade_ready": False}
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": str(exc),
                "trade_ready": False}


def probe(symbol, fetch=None):
    approved = {BENCHMARK} | {s for group in SECTORS.values() for s in group}
    if symbol not in approved:
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "unapproved_symbol",
                "trade_ready": False}
    try:
        if fetch is None:
            with urlopen(Request(SOURCE.format(symbol=symbol),
                                 headers={"User-Agent": "Mozilla/5.0"}), timeout=12) as response:
                raw = response.read(1_200_001)
        else:
            raw = fetch(SOURCE.format(symbol=symbol))
        if len(raw) > 1_200_000:
            return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "oversized",
                    "trade_ready": False}
        return inspect_payload(symbol, json.loads(raw))
    except (OSError, TimeoutError, UnicodeError, ValueError, TypeError):
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "fetch_failed",
                "trade_ready": False}


if __name__ == "__main__":
    for sector, symbols in [("benchmark", (BENCHMARK,)), *SECTORS.items()]:
        for symbol in symbols:
            print(json.dumps({"sector": sector, **probe(symbol),
                              "corporate_actions_verified": False,
                              "earnings_asof_verified": False,
                              "independent_holdout": False}, sort_keys=True))
