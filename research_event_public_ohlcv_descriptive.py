"""Descriptive OHLCV audit of public-page observations; never a trade backtest."""
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

def analyze_public_observations(path):
    with Path(path).open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    grouped = {}
    for row in rows:
        symbol = row["symbol"]
        try:
            o,h,l,c,v = [Decimal(row[k]) for k in ("open","high","low","close","volume")]
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError("invalid_observation") from exc
        if not all(x.is_finite() for x in (o,h,l,c,v)) or min(o,h,l,c)<=0 or v<0 or l>min(o,c) or h<max(o,c):
            raise ValueError("invalid_ohlcv")
        grouped.setdefault(symbol, []).append((row["date"], c, l))
    output=[]
    for symbol, bars in sorted(grouped.items()):
        bars.sort()
        if len({day for day,_,_ in bars}) != len(bars):
            raise ValueError("duplicate_session")
        baseline = next((close for day,close,_ in bars if day=="2026-10-21"), None)
        following = next((close for day,close,_ in bars if day=="2026-10-23"), None)
        if baseline is None or following is None:
            continue
        minimum = min(low for day,_,low in bars if "2026-10-21" < day <= "2026-10-23")
        output.append({"symbol":symbol,
                       "close_to_close_pct":str(round((following/baseline-1)*100, 3)),
                       "worst_observed_intraday_vs_baseline_pct":str(round((minimum/baseline-1)*100, 3)),
                       "signal_predictive_edge_proven":False,
                       "execution_price_verified":False,
                       "research_only":True})
    return output
