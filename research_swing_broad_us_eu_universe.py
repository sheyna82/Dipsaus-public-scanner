"""Frozen cross-region research universe, preserving regional benchmarks.

Availability is not assumed. All symbols remain in the denominator when
reporting missing history; no post-hoc removal of delisted/failed symbols.
"""
from collections import Counter
from research_swing_diversified_universe import UNIVERSE_V1, BENCHMARKS
from research_swing_european_universe import EUROPE_V1, EU_BENCHMARKS

US_EXTENSION = (
    ("AAPL","technology"), ("MSFT","technology"), ("GOOGL","communication"),
    ("DIS","communication"), ("WMT","consumer_staples"), ("COST","consumer_staples"),
    ("HD","consumer_discretionary"), ("MCD","consumer_discretionary"),
    ("UNH","healthcare"), ("ABBV","healthcare"), ("DE","industrials"),
    ("GE","industrials"), ("NEE","utilities"), ("D","utilities"),
    ("SLB","energy"), ("COP","energy"), ("GS","financials"), ("MS","financials"),
    ("AMT","real_estate"), ("SPG","real_estate"), ("LIN","materials"), ("APD","materials"),
)
EU_EXTENSION = (
    ("MC.PA","consumer_discretionary","XPAR","EUR"),
    ("RMS.PA","consumer_discretionary","XPAR","EUR"),
    ("VOW3.DE","consumer_discretionary","XETR","EUR"),
    ("MBG.DE","consumer_discretionary","XETR","EUR"),
    ("NOKIA.HE","technology","XHEL","EUR"),
    ("ERIC-B.ST","technology","XSTO","SEK"),
    ("NOVO-B.CO","healthcare","XCSE","DKK"),
    ("AZN.L","healthcare","XLON","GBp"),
    ("BP.L","energy","XLON","GBp"),
    ("EQNR.OL","energy","XOSL","NOK"),
    ("BBVA.MC","financials","XMAD","EUR"),
    ("BNP.PA","financials","XPAR","EUR"),
    ("SU.PA","industrials","XPAR","EUR"),
    ("SAF.PA","industrials","XPAR","EUR"),
    ("RIO.L","materials","XLON","GBp"),
    ("GLEN.L","materials","XLON","GBp"),
    ("NG.L","utilities","XLON","GBp"),
    ("EDP.LS","utilities","XLIS","EUR"),
    ("DTE.DE","telecom","XETR","EUR"),
    ("VOD.L","telecom","XLON","GBp"),
)
REGIONAL_BENCHMARKS = {"US": tuple(BENCHMARKS), "EU": tuple(x[0] for x in EU_BENCHMARKS)}

def broad_universe_manifest():
    us = [dict(symbol=s, sector=sector, region="US", currency="USD")
          for s,sector in (*UNIVERSE_V1,*US_EXTENSION)]
    eu = [dict(symbol=s, sector=sector, region="EU", exchange=exchange, currency=currency)
          for s,sector,exchange,currency in (*EUROPE_V1,*EU_EXTENSION)]
    rows = us + eu
    symbols = [x["symbol"] for x in rows]
    benchmarks = [s for v in REGIONAL_BENCHMARKS.values() for s in v]
    if len(set(symbols + benchmarks)) != len(symbols + benchmarks):
        raise ValueError("duplicate_universe_symbols")
    return {"research_only": True, "trade_ready": False,
            "preregistered": True, "source_verified": False,
            "survivorship_bias_eliminated": False,
            "universe": rows, "benchmarks": REGIONAL_BENCHMARKS,
            "sector_counts": dict(Counter(x["sector"] for x in rows)),
            "region_counts": dict(Counter(x["region"] for x in rows))}

def audit_broad_coverage(statuses):
    manifest = broad_universe_manifest()
    expected = [x["symbol"] for x in manifest["universe"]]
    expected += [s for v in REGIONAL_BENCHMARKS.values() for s in v]
    if not isinstance(statuses,dict) or set(statuses) != set(expected):
        raise ValueError("incomplete_universe_coverage")
    allowed = {"normalized_unverified", "audited_verified"}
    missing = [s for s in expected if statuses[s] not in allowed]
    return {"research_only":True, "total":len(expected),
            "available":len(expected)-len(missing), "unavailable":missing,
            "complete":not missing, "source_verified":False}
