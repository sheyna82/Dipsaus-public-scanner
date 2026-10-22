"""Small predeclared *source-availability* probe, not a backtest universe.

The cross-sector list is deliberately explicit and includes a delisted case.
Success for surviving names does not establish survivorship-free coverage.
No data stored, no indicators scored, no trading decisions.
"""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from research_audit_four_event_ohlcv import audit_chart

CANDIDATES = (
    ("XOM", "Energy", "active"),
    ("JPM", "Financials", "active"),
    ("JNJ", "Health Care", "active"),
    ("CAT", "Industrials", "active"),
    ("PG", "Consumer Staples", "active"),
    ("NEE", "Utilities", "active"),
    ("AMT", "Real Estate", "active"),
    ("LIN", "Materials", "active"),
    ("DIS", "Communication Services", "active"),
    ("HD", "Consumer Discretionary", "active"),
    ("MSFT", "Information Technology", "active"),
    ("LEH", "Financials", "delisted"),
)
BASE = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5y&interval=1d"


def inspect_candidate(symbol, sector, listing_status, fetch=None):
    try:
        url = BASE.format(symbol=symbol)
        if fetch is None:
            with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}),
                         timeout=10) as response:
                raw = response.read(1_500_001)
        else:
            raw = fetch(url)
        if len(raw) > 1_500_000:
            return {"symbol": symbol, "sector": sector, "listing_status": listing_status,
                    "status": "DATA_BLOCKED", "reason": "oversized"}
        audit = audit_chart(json.loads(raw), symbol)
        return {"symbol": symbol, "sector": sector, "listing_status": listing_status,
                "status": audit["status"], "bars": audit.get("bars"),
                "reason": audit.get("reason"),
                "corporate_actions_verified": False,
                "point_in_time_earnings_verified": False,
                "delisted_coverage_verified": False,
                "trade_ready": False}
    except HTTPError as exc:
        return {"symbol": symbol, "sector": sector, "listing_status": listing_status,
                "status": "DATA_BLOCKED", "reason": "http_error",
                "http_status": exc.code, "trade_ready": False}
    except (OSError, URLError, TimeoutError, UnicodeError, ValueError, TypeError):
        return {"symbol": symbol, "sector": sector, "listing_status": listing_status,
                "status": "DATA_BLOCKED", "reason": "request_or_schema_failure",
                "trade_ready": False}


if __name__ == "__main__":
    for symbol, sector, listing in CANDIDATES:
        print(json.dumps(inspect_candidate(symbol, sector, listing), sort_keys=True))
