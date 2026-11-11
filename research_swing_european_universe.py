"""Research-only preregistered European comparison universe.

Symbols are Yahoo-style research identifiers, not broker order identifiers.
No assertions about availability, adjustment quality or execution.
"""
EUROPE_V1 = (
 ("ASML.AS","technology","XAMS","EUR"),("ASM.AS","technology","XAMS","EUR"),
 ("SHEL.AS","energy","XAMS","EUR"),("TTE.PA","energy","XPAR","EUR"),
 ("INGA.AS","financials","XAMS","EUR"),("SAN.MC","financials","XMAD","EUR"),
 ("SIE.DE","industrials","XETR","EUR"),("AIR.PA","industrials","XPAR","EUR"),
 ("RHM.DE","defense","XETR","EUR"),("HO.PA","defense","XPAR","EUR"),
 ("AD.AS","consumer_staples","XAMS","EUR"),("OR.PA","consumer_staples","XPAR","EUR"),
 ("SAN.PA","healthcare","XPAR","EUR"),("BAYN.DE","healthcare","XETR","EUR"),
 ("ENEL.MI","utilities","XMIL","EUR"),("IBE.MC","utilities","XMAD","EUR"),
 ("BAS.DE","materials","XETR","EUR"),("AI.PA","materials","XPAR","EUR"),
 ("VNA.DE","real_estate","XETR","EUR"),("URW.AS","real_estate","XAMS","EUR"),
)
EU_BENCHMARKS = (("EXSA.DE","europe_equity_proxy","XETR","EUR"),)
def european_manifest():
    from collections import Counter
    symbols=[s for s,_,_,_ in EUROPE_V1]
    sectors=Counter(sector for _,sector,_,_ in EUROPE_V1)
    if len(set(symbols)) != len(symbols) or len(sectors)!=10 or any(v!=2 for v in sectors.values()):
        raise ValueError("invalid_europe_universe")
    return {"research_only":True,"trade_ready":False,"data_verified":False,
            "survivorship_free":False,"symbols":[{"symbol":s,"sector":sector,"exchange":exchange,"currency":currency} for s,sector,exchange,currency in EUROPE_V1],
            "benchmarks":[{"symbol":s,"sector":sector,"exchange":exchange,"currency":currency} for s,sector,exchange,currency in EU_BENCHMARKS]}
def audit_european_coverage(statuses):
    expected=[s for s,_,_,_ in EUROPE_V1]+[s for s,_,_,_ in EU_BENCHMARKS]
    if set(statuses)!=set(expected): raise ValueError("incomplete_europe_coverage")
    return {"available":[s for s in expected if statuses[s]=="normalized_unverified"],
            "unavailable":[s for s in expected if statuses[s]!="normalized_unverified"]}
