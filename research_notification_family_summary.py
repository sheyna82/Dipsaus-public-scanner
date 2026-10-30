"""Compare signal families against observed maturity, without inventing returns."""
from collections import defaultdict

def summarize_families(stages, maturity):
    by_symbol={row["symbol"]:row for row in maturity}
    groups=defaultdict(lambda:{"cases":0,"horizons_ready":{"3":0,"5":0,"10":0,"20":0},"symbols":[]})
    for stage in stages:
        symbol=stage["symbol"]
        if symbol not in by_symbol:
            raise ValueError("missing_maturity_for_"+symbol)
        group=groups[stage["stage"]]
        group["cases"]+=1
        group["symbols"].append(symbol)
        for h in group["horizons_ready"]:
            if by_symbol[symbol]["horizons"][h]["ready"]:
                group["horizons_ready"][h]+=1
    return {"families":dict(groups),"net_returns_computed":False,
            "profitability_ranking_available":False,"research_only":True,
            "warning":"Do not rank strategies on maturity counts or historical pre-signal momentum."}
