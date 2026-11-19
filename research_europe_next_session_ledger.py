"""Isolated next-session execution research ledger. Never places orders."""
from datetime import date
import math

def simulate(bars_by_symbol, signals, *, initial_cash=50000, tranche=3500,
             max_positions=6, fee_per_side=4.90, roundtrip_slippage_fraction=0.0015,
             hold_sessions=5):
    if not (isinstance(max_positions,int) and 1<=max_positions<=6):
        raise ValueError("INVALID_POSITION_CAP")
    if not (isinstance(hold_sessions,int) and hold_sessions>=1):
        raise ValueError("INVALID_HOLD")
    for v in (initial_cash,tranche,fee_per_side,roundtrip_slippage_fraction):
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0:
            raise ValueError("INVALID_PARAMETER")
    if initial_cash<=0 or tranche<=0 or roundtrip_slippage_fraction>=1:
        raise ValueError("INVALID_PARAMETER")
    if not isinstance(bars_by_symbol,dict) or not isinstance(signals,list):
        raise ValueError("INVALID_INPUT")
    histories={}
    for symbol,bars in bars_by_symbol.items():
        if not isinstance(bars,list):raise ValueError("INVALID_BARS")
        dates=set()
        for bar in bars:
            day=bar["day"]
            if date.fromisoformat(day).isoformat()!=day or day in dates:
                raise ValueError("INVALID_OR_DUPLICATE_DAY")
            dates.add(day)
            for key in ("open","close"):
                price=bar[key]
                if isinstance(price,bool) or not isinstance(price,(int,float)) or not math.isfinite(price) or price<=0:
                    raise ValueError("INVALID_PRICE")
        histories[symbol]=sorted(bars,key=lambda x:x["day"])
    candidates=[]
    for s in signals:
        symbol=s["symbol"];day=s["day"]
        if symbol not in histories:raise ValueError("UNKNOWN_SYMBOL")
        bars=histories[symbol]
        indices=[i for i,b in enumerate(bars) if b["day"]==day]
        if len(indices)!=1:raise ValueError("UNKNOWN_SIGNAL_DAY")
        i=indices[0]
        if i+1+hold_sessions>=len(bars):
            continue  # no completed future exit; no invented trade
        entry=bars[i+1];exit_bar=bars[i+1+hold_sessions]
        if entry["day"]<=day:raise ValueError("LOOKAHEAD")
        candidates.append((entry["day"],symbol,day,entry,exit_bar))
    candidates.sort(key=lambda x:(x[0],x[1],x[2]))
    cash=float(initial_cash);positions=[];ledger=[];rejected=[]
    for entry_day,symbol,signal_day,entry,exit_bar in candidates:
        still=[]
        for p in positions:
            if p["exit_day"]<entry_day:
                cash+=p["exit_proceeds"]
            else:still.append(p)
        positions=still
        if len(positions)>=max_positions or any(p["symbol"]==symbol for p in positions):
            rejected.append({"symbol":symbol,"signal_day":signal_day,"reason":"CAP_OR_SYMBOL_BUSY"})
            continue
        # one-way slippage applied to entry and exit, no fractional shares
        buy_price=entry["open"]*(1+roundtrip_slippage_fraction/2)
        shares=min(int(tranche//buy_price),int(max(0,cash-fee_per_side)//buy_price))
        if shares<1:
            rejected.append({"symbol":symbol,"signal_day":signal_day,"reason":"NO_CASH_OR_SHARE"})
            continue
        cost=shares*buy_price+fee_per_side
        sell_price=exit_bar["close"]*(1-roundtrip_slippage_fraction/2)
        proceeds=shares*sell_price-fee_per_side
        cash-=cost
        p={"symbol":symbol,"signal_day":signal_day,"entry_day":entry_day,
           "exit_day":exit_bar["day"],"shares":shares,"entry_cost":cost,
           "exit_proceeds":proceeds,"net_pnl":proceeds-cost}
        positions.append(p);ledger.append(p)
    total_pnl=sum(p["net_pnl"] for p in ledger)
    return {"research_only":True,"trade_ready":False,"orders_placed":False,
            "assumptions":{"next_session_open":True,"whole_shares":True,
                "same_day_exit_cash_reuse":False,"fee_per_side":fee_per_side,
                "roundtrip_slippage_fraction":roundtrip_slippage_fraction,
                "fees_verified":False},
            "trade_count":len(ledger),"net_realized_and_scheduled_pnl":total_pnl,
            "trades":ledger,"rejected":rejected}
