"""Offline six-slot cash-account portfolio proxy; not a live trading system.

Ranks a fixed, aligned universe using prior 20-session close momentum. Buys
next open; each slot stays reserved through its scheduled exit. A close-only
warning exits at the next open, with no stop order or same-bar fill.
"""
from math import isfinite
from statistics import mean
from research_swing_failure_warning import failure_warning_at_close

def portfolio_swing_proxy(bars, *, horizon=10, slots=6, round_trip_cost_bps=30,
                          warning_exits=False, starting_cash=21000):
    if horizon not in (5,10,15) or type(slots) is not int or not 1<=slots<=6:
        raise ValueError("invalid_parameters")
    if not 0<=round_trip_cost_bps<=1000 or starting_cash<=0:
        raise ValueError("invalid_cost_or_cash")
    if not bars or len({tuple(r["timestamp"] for r in rows) for rows in bars.values()})!=1:
        raise ValueError("unaligned_panel")
    n=len(next(iter(bars.values())))
    if n<60:
        raise ValueError("insufficient_history")
    for rows in bars.values():
        for bar in rows:
            if any(not isinstance(bar[k],(int,float)) or not isfinite(bar[k]) or bar[k]<=0
                   for k in ("open","high","low","close")):
                raise ValueError("invalid_prices")
    cash=float(starting_cash)
    positions={}
    pending=[]
    trades=[]
    equity=[]
    max_open=0
    for t in range(20,n):
        # Execute orders at the open, after decisions made at prior close.
        for order in pending:
            symbol=order["symbol"]
            price=bars[symbol][t]["open"]
            if order["side"]=="sell" and symbol in positions:
                p=positions.pop(symbol)
                proceeds=p["shares"]*price*(1-round_trip_cost_bps/20000)
                cash+=proceeds
                trades.append({"symbol":symbol,"entry_index":p["entry_index"],
                               "exit_index":t,"net_pct":round(100*(proceeds/p["capital"]-1),4),
                               "reason":order["reason"]})
            elif order["side"]=="buy" and symbol not in positions and len(positions)<slots:
                # Fixed slots: reserve at most 1/slots of starting capital.
                budget=min(starting_cash/slots,cash)
                if budget>0:
                    shares=budget/(price*(1+round_trip_cost_bps/20000))
                    positions[symbol]={"shares":shares,"capital":budget,"entry_index":t,
                                       "scheduled_exit":min(t+horizon-1,n-1)}
                    cash-=budget
        pending=[]
        max_open=max(max_open,len(positions))
        marked=cash+sum(p["shares"]*bars[s][t]["close"] for s,p in positions.items())
        equity.append(marked)
        if t==n-1:
            break
        for s,p in list(positions.items()):
            if t>=p["scheduled_exit"]:
                pending.append({"side":"sell","symbol":s,"reason":"time"})
            elif warning_exits and failure_warning_at_close(bars[s],t)["warning"]:
                pending.append({"side":"sell","symbol":s,"reason":"warning"})
        exiting={x["symbol"] for x in pending}
        free_slots=slots-len(positions)
        if free_slots>0:
            ranked=sorted(((bars[s][t]["close"]/bars[s][t-20]["close"]-1,s)
                           for s in bars if s not in positions),reverse=True)
            for _,s in ranked[:free_slots]:
                pending.append({"side":"buy","symbol":s,"reason":"momentum"})
    # Mark remaining positions at final close, with estimated sell cost.
    final_equity=cash+sum(p["shares"]*bars[s][-1]["close"]*(1-round_trip_cost_bps/20000)
                          for s,p in positions.items())
    peak=starting_cash
    worst_drawdown=0
    for value in equity+[final_equity]:
        peak=max(peak,value)
        worst_drawdown=min(worst_drawdown,100*(value/peak-1))
    return {"initial_cash":starting_cash,"final_equity":round(final_equity,2),
            "total_net_return_pct":round(100*(final_equity/starting_cash-1),4),
            "max_mark_to_market_drawdown_pct":round(worst_drawdown,4),
            "completed_trades":len(trades),"open_positions_at_end":len(positions),
            "max_simultaneous_positions":max_open,
            "warning_exit_trades":sum(x["reason"]=="warning" for x in trades),
            "severe_completed_losses":sum(x["net_pct"]<=-8 for x in trades),
            "research_only":True,"trade_ready":False,"edge_proven":False,
            "dividends_and_fx_modelled":False,"corporate_actions_verified":False,
            "fractional_shares_assumed":True,"slippage_modelled":False}
