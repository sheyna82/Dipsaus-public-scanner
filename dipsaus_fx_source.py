"""Conservative FX source adapter for private US gross-EUR research.

USD/EUR is derived from a fresh EURUSD=X close; fail closed on stale data.
No broker conversion spread or executable quote is implied.
"""
import math
from datetime import datetime, timezone

def validated_eur_per_usd(history, now=None, max_age_seconds=120):
    now = now or datetime.now(timezone.utc)
    if history is None or getattr(history, "empty", True):
        return {"status": "FX_UNAVAILABLE"}
    try:
        close = float(history["Close"].iloc[-1])
        idx = history.index[-1]
        if getattr(idx, "tzinfo", None) is None:
            return {"status": "FX_TIMEZONE_UNKNOWN"}
        ts = (idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else idx).astimezone(timezone.utc)
        age = (now-ts).total_seconds()
        if not math.isfinite(close) or close <= 0 or not -30 <= age <= max_age_seconds:
            return {"status": "FX_STALE_OR_INVALID"}
        return {"status": "FX_FRESH", "eur_per_usd": 1.0 / close,
                "fx_checked_utc": ts.isoformat(), "fx_source": "Yahoo EURUSD=X 1m close",
                "fx_broker_executable": False}
    except (ValueError, TypeError, IndexError, KeyError, OverflowError):
        return {"status": "FX_INVALID"}

def fetch_fx(yf, now=None):
    try:
        h = yf.Ticker("EURUSD=X").history(period="1d", interval="1m", prepost=False)
    except Exception:
        return {"status": "FX_UNAVAILABLE"}
    return validated_eur_per_usd(h, now=now)
