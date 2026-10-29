"""Deterministic research-only chronological portfolio capacity simulator.

Input: precomputed signals with known entry/exit session days and *net* returns.
No automatic orders, no stoploss, no signal generation, no same-day capital reuse.
"""
from collections import defaultdict
import math

def simulate(signals, *, max_positions=6, capital=21000.0, tranche=3500.0):
    if not isinstance(max_positions, int) or isinstance(max_positions, bool) or max_positions < 1:
        raise ValueError("INVALID_CAPACITY")
    if not all(isinstance(x, (int,float)) and not isinstance(x,bool) and math.isfinite(x) and x>0 for x in (capital,tranche)):
        raise ValueError("INVALID_CAPITAL")
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
        for row in sorted(by_day[day],key=lambda r:(r.get("priority",0),r["symbol"])):
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
            "automatic_orders":False,"accepted_n":len(accepted),
            "rejected_n":sum(rejected.values()),"rejection_reasons":dict(rejected),
            "max_concurrent_positions":max_used,"initial_capital":round(capital,2),
            "ending_cash":round(cash,2),"realized_pnl":round(pnl,2),
            "realized_return_pct":round(100*pnl/capital,4),
            "accepted_signals":[{"symbol":r["symbol"],"entry_day":r["entry_day"],"exit_day":r["exit_day"]} for r in accepted],
            "limitations":["Signals and net returns must be computed independently without lookahead",
                           "Fixed tranche and fixed exit; no intra-trade equity or drawdown curve",
                           "No sector concentration or live fill model; priority must be predeclared",
                           "Historical simulation, not independent prospective validation"]}
