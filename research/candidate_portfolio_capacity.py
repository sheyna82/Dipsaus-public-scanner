"""Deterministic research-only chronological portfolio capacity simulator.

Input: precomputed signals with known entry/exit session days and *net* returns.
No automatic orders, no stoploss, no signal generation, no same-day capital reuse.
"""
from collections import defaultdict
import math
import hashlib

def simulate(signals, *, max_positions=6, capital=21000.0, tranche=3500.0, priority_mode='symbol_asc'):
    if not isinstance(max_positions, int) or isinstance(max_positions, bool) or max_positions < 1:
        raise ValueError("INVALID_CAPACITY")
    if not all(isinstance(x, (int,float)) and not isinstance(x,bool) and math.isfinite(x) and x>0 for x in (capital,tranche)):
        raise ValueError("INVALID_CAPITAL")
    if priority_mode not in ("symbol_asc","symbol_desc","stable_hash","score_desc"):
        raise ValueError("INVALID_PRIORITY_MODE")
    if not isinstance(signals,list):
        raise ValueError("INVALID_SIGNALS")
    seen=set()
    for row in signals:
        if not isinstance(row,dict):
            raise ValueError("INVALID_SIGNAL")
        symbol=row.get("symbol")
        entry=row.get("entry_day")
        exit_day=row.get("exit_day")
        ret=row.get("net_return_pct")
        if not isinstance(symbol,str) or not symbol.strip() or not isinstance(entry,int) or isinstance(entry,bool) or not isinstance(exit_day,int) or isinstance(exit_day,bool) or exit_day<=entry or not isinstance(ret,(int,float)) or isinstance(ret,bool) or not math.isfinite(ret) or ret < -100:
            raise ValueError("INVALID_SIGNAL")
        if (symbol,entry) in seen:
            raise ValueError("DUPLICATE_SIGNAL")
        seen.add((symbol,entry))
    cash=float(capital)
    positions=[]
    accepted=[]
    rejected=defaultdict(int)
    max_used=0
    # Entry at start of day, exit at end: proceeds cannot fund same-day entries.
    by_day=defaultdict(list)
    for row in signals:
        by_day[row["entry_day"]].append(row)
    for day in sorted(set(by_day)|{x["exit_day"] for x in signals}):
        def priority(row):
            symbol=row["symbol"]
            if priority_mode=="score_desc":
                score=row.get("score")
                if not isinstance(score,(int,float)) or isinstance(score,bool) or not math.isfinite(score):
                    raise ValueError("INVALID_SELECTION_SCORE")
                return (-score,symbol)
            if priority_mode=="symbol_asc":
                return (row.get("priority",0),symbol)
            if priority_mode=="symbol_desc":
                return (row.get("priority",0),tuple(-ord(c) for c in symbol))
            digest=hashlib.sha256((str(day)+":"+symbol).encode()).hexdigest()
            return (row.get("priority",0),digest,symbol)
        for row in sorted(by_day[day],key=priority):
            if any(p["symbol"]==row["symbol"] for p in positions):
                rejected["SYMBOL_ALREADY_HELD"]+=1
            elif len(positions)>=max_positions:
                rejected["CAPACITY_FULL"]+=1
            elif cash+1e-9<tranche:
                rejected["INSUFFICIENT_CASH"]+=1
            else:
                cash-=tranche
                positions.append(row)
                accepted.append(row)
                max_used=max(max_used,len(positions))
        remaining=[]
        for row in positions:
            if row["exit_day"]==day:
                cash+=tranche*(1+row["net_return_pct"]/100)
            else:
                remaining.append(row)
        positions=remaining
    pnl=cash-capital
    return {"status":"DESCRIPTIVE_PORTFOLIO_SIMULATION","trade_ready":False,
            "automatic_orders":False,"priority_mode":priority_mode,"accepted_n":len(accepted),
            "rejected_n":sum(rejected.values()),"rejection_reasons":dict(rejected),
            "max_concurrent_positions":max_used,"initial_capital":round(capital,2),
            "ending_cash":round(cash,2),"realized_pnl":round(pnl,2),
            "realized_return_pct":round(100*pnl/capital,4),
            "accepted_signals":[{"symbol":r["symbol"],"entry_day":r["entry_day"],"exit_day":r["exit_day"]} for r in accepted],
            "limitations":["Signals and net returns must be computed independently without lookahead",
                           "Fixed tranche and fixed exit; no intra-trade equity or drawdown curve",
                           "No sector concentration or live fill model; priority must be predeclared",
                           "Historical simulation, not independent prospective validation"]}

def compare_ablation_portfolios(report, *, pattern, max_positions=6):
    """Pool actual held-out dated events across symbols, one filter at a time.

    Never compare the same symbol-pattern twice, and never rank by test returns.
    Each filter gets identical deterministic symbol-priority tie breaking.
    """
    if not isinstance(report,dict) or not isinstance(report.get("candidates"),list):
        raise ValueError("INVALID_ABLATION_REPORT")
    from candidate_feature_ablation import FILTERS
    comparisons={}
    priority_sensitivity={}
    for key in FILTERS:
        events=[]
        for candidate in report["candidates"]:
            symbol=candidate.get("symbol")
            detail=candidate.get("patterns",{}).get(pattern,{})
            if detail.get("status")!="DESCRIPTIVE_ONLY":
                continue
            for item in detail.get("portfolio_events_25bps",{}).get(key,[]):
                events.append({**item,"symbol":symbol})
        scenarios={mode:simulate(events,max_positions=max_positions,priority_mode=mode)
                   for mode in ("symbol_asc","symbol_desc","stable_hash")}
        comparisons[key]=scenarios["symbol_asc"]
        priority_sensitivity[key]={"scenarios":{mode:{"accepted_n":result["accepted_n"],
                                                "realized_return_pct":result["realized_return_pct"],
                                                "rejected_n":result["rejected_n"]}
                                                for mode,result in scenarios.items()},
                                   "return_range_pct_points":round(max(x["realized_return_pct"] for x in scenarios.values())-
                                                                   min(x["realized_return_pct"] for x in scenarios.values()),4)}
    return {"status":"DESCRIPTIVE_ONLY","trade_ready":False,
            "pattern":pattern,"entry_slippage_bps":25,
            "costs_included_in_trade_returns":True,
            "comparison":comparisons,
            "priority_sensitivity":priority_sensitivity,
            "limitations":["Held-out sample was previously inspected; not fresh out-of-sample evidence",
                           "One pattern at a time; cross-pattern opportunity competition not modeled",
                           "Fixed exits and no daily drawdown or equity curve",
                           "Three deterministic tie-breakers are sensitivity checks, not randomized inference",
                           "Historical convenience universe and daily open fill assumptions"]}
