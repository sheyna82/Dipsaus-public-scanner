"""Small predeclared *source-availability* probe, not a backtest universe.

The cross-sector list is deliberately explicit and includes a delisted case.
Success for surviving names does not establish survivorship-free coverage.
No data stored, no indicators scored, no trading decisions.
"""
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from research_audit_four_event_ohlcv import audit_chart
from dipsaus_offline_completed_daily_bar_gate import completed_daily_bars

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
        payload = json.loads(raw)
        result = payload['chart']['result'][0]
        timestamps = result['timestamp']
        quote = result['indicators']['quote'][0]
        rows = [{'date': datetime.fromtimestamp(ts, timezone.utc).date().isoformat(),
                 **{field: quote[field][i] for field in ('open', 'high', 'low', 'close', 'volume')}}
                for i, ts in enumerate(timestamps)]
        completed = completed_daily_bars(rows, now_utc=datetime.now(timezone.utc))
        if completed['status'] != 'PRIOR_DATE_ONLY':
            return {'symbol': symbol, 'sector': sector, 'listing_status': listing_status,
                    'status': 'DATA_BLOCKED', 'reason': 'incomplete_session_gate',
                    'trade_ready': False}
        keep = len(completed['rows'])
        result['timestamp'] = timestamps[:keep]
        for field in ('open', 'high', 'low', 'close', 'volume'):
            quote[field] = quote[field][:keep]
        audit = audit_chart(payload, symbol)
        return {"symbol": symbol, "sector": sector, "listing_status": listing_status,
                "status": audit["status"], "bars": audit.get("bars"),
                "discarded_unconfirmed_bars": len(rows) - keep,
                "reason": audit.get("reason"),
                "corporate_actions_verified": False,
                "point_in_time_earnings_verified": False,
                "delisted_coverage_verified": False,
                "trade_ready": False, "delisted_coverage_verified": False}
    except HTTPError as exc:
        return {"symbol": symbol, "sector": sector, "listing_status": listing_status,
                "status": "DATA_BLOCKED", "reason": "http_error",
                "http_status": exc.code, "trade_ready": False}
    except (OSError, URLError, TimeoutError, UnicodeError, ValueError, TypeError, KeyError, IndexError, AttributeError):
        return {"symbol": symbol, "sector": sector, "listing_status": listing_status,
                "status": "DATA_BLOCKED", "reason": "request_or_schema_failure",
                "trade_ready": False}


if __name__ == "__main__":
    for symbol, sector, listing in CANDIDATES:
        print(json.dumps(inspect_candidate(symbol, sector, listing), sort_keys=True))
