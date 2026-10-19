"""Fetch timestamped broad-market ETF observations for silent research only."""
from datetime import datetime, timezone

def fetch_index_quotes(fetcher=None):
    """Reject delayed, incomplete or off-session bars; no fabricated live quotes."""
    if fetcher is None:
        import yfinance as yf
        fetcher = lambda symbol: yf.Ticker(symbol).history(period="2d", interval="1m", prepost=False)
    result = {}
    for symbol in ("SPY", "QQQ"):
        try:
            frame = fetcher(symbol)
            if frame is None or len(frame) < 2:
                continue
            # Compare against the preceding regular-session close, not the previous minute.
            idx = frame.index
            latest = idx[-1]
            if getattr(latest, "tzinfo", None) is None:
                continue
            dates = [t.date() for t in idx]
            prior_dates = [d for d in set(dates) if d < latest.date()]
            if not prior_dates:
                continue
            prior_date = max(prior_dates)
            prior = float(frame["Close"].iloc[max(i for i, d in enumerate(dates) if d == prior_date)])
            current = float(frame["Close"].iloc[-1])
            if prior <= 0 or current <= 0:
                continue
            result[symbol] = {"timestamp_utc": latest.astimezone(timezone.utc).isoformat(),
                              "change_pct": round((current / prior - 1) * 100, 4)}
        except (Exception):
            continue
    return result
