"""Deterministic, pre-registered diverse-universe research configuration.

No network access, trades, provider assumptions or claims of data availability.
"""
from collections import Counter

UNIVERSE_V1 = (
    ("AMD","technology"),("META","technology"),
    ("KO","consumer_staples"),("PG","consumer_staples"),
    ("JNJ","healthcare"),("PFE","healthcare"),
    ("XOM","energy"),("CVX","energy"),
    ("JPM","financials"),("BAC","financials"),
    ("CAT","industrials"),("RTX","industrials"),
    ("FCX","materials"),("NEM","materials"),
    ("DUK","utilities"),("SO","utilities"),
    ("O","real_estate"),("PLD","real_estate"),
)
BENCHMARKS = ("SPY","IWM")
HORIZONS = (3,5,10,15,20,30,40)


def universe_manifest():
    symbols = [s for s,_ in UNIVERSE_V1]
    if len(set(symbols)) != len(symbols):
        raise ValueError("duplicate_symbols")
    counts = Counter(sector for _,sector in UNIVERSE_V1)
    if len(counts) < 8 or any(v != 2 for v in counts.values()):
        raise ValueError("sector_balance_changed")
    return {"research_only": True, "trade_ready": False,
            "universe_frozen_for_experiment": True,
            "symbols": [{"symbol":s,"sector":sector} for s,sector in UNIVERSE_V1],
            "benchmarks":list(BENCHMARKS), "horizons":list(HORIZONS),
            "source_data_validated":False, "survivorship_bias_eliminated":False}


def audit_coverage(status_by_symbol):
    """Never silently discard unavailable or invalid symbols."""
    expected = [s for s,_ in UNIVERSE_V1] + list(BENCHMARKS)
    if not isinstance(status_by_symbol,dict) or set(status_by_symbol) != set(expected):
        raise ValueError("incomplete_coverage_manifest")
    accepted = {"normalized_unverified","audited_verified"}
    rows = [{"symbol":s,"status":status_by_symbol[s],
             "eligible_for_research":status_by_symbol[s] in accepted}
            for s in expected]
    return {"research_only":True, "complete":True, "rows":rows,
            "available":sum(r["eligible_for_research"] for r in rows),
            "unavailable":[r["symbol"] for r in rows if not r["eligible_for_research"]]}
