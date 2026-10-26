"""Offline six-slot cash-account portfolio proxy; not a live trading system.

Ranks a fixed, aligned universe using prior 20-session close momentum. Buys
next open; each slot stays reserved through its scheduled exit. A close-only
warning exits at the next open, with no stop order or same-bar fill.
"""
from math import isfinite
from statistics import mean
from research_swing_failure_warning import failure_warning_at_close

def portfolio_swing_proxy(bars, *, horizon=10, slots=6, round_trip_cost_bps=30,
                          warning_exits=False, starting_cash=21000, max_exposure_fraction=1.0):
    if horizon not in (5,10,15) or type(slots) is not int or not 1<=slots<=6:
        raise ValueError("invalid_parameters")
    if not 0<=round_trip_cost_bps<=1000 or starting_cash<=0 or not 0<max_exposure_fraction<=1:
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
            if bar["low"]>min(bar["open"],bar["close"]) or bar["high"]<max(bar["open"],bar["close"]):
                raise ValueError("inconsistent_ohlc")
    cash=float(starting_cash)
    peak_invested=0
    positions={}
    pending=[]
    trades=[]
    equity=[]
    max_open=0
    worst_daily_equity_move_pct=0.0
    negative_equity_days=0
    prior_equity=None
    worst_breadth_day={"index":None,"declining_positions":0,"open_positions":0,"fraction":0.0}
    days_with_majority_declining=0
    majority_day_equity_changes=[]
    other_day_equity_changes=[]
    worst_trade_pct=0.0
    loss_buckets={"minus_5_to_minus_8":0,"minus_8_to_minus_15":0,"below_minus_15":0}
    severe_loss_by_symbol={}
    severe_loss_by_reason={}
    for t in range(20,n):
        # Execute orders at the open, after decisions made at prior close.
        for order in pending:
            symbol=order["symbol"]
            price=bars[symbol][t]["open"]
            if order["side"]=="sell" and symbol in positions:
                p=positions.pop(symbol)
                proceeds=p["shares"]*price*(1-round_trip_cost_bps/20000)
                cash+=proceeds
                net_pct=100*(proceeds/p["capital"]-1)
                worst_trade_pct=min(worst_trade_pct,net_pct)
                if net_pct<=-8:
                    severe_loss_by_symbol[symbol]=severe_loss_by_symbol.get(symbol,0)+1
                    reason=order["reason"]
                    severe_loss_by_reason[reason]=severe_loss_by_reason.get(reason,0)+1
                if net_pct<=-15:
                    loss_buckets["below_minus_15"]+=1
                elif net_pct<=-8:
                    loss_buckets["minus_8_to_minus_15"]+=1
                elif net_pct<=-5:
                    loss_buckets["minus_5_to_minus_8"]+=1
                trades.append({"symbol":symbol,"entry_index":p["entry_index"],
                               "exit_index":t,"net_pct":round(net_pct,4),
                               "reason":order["reason"]})
            elif order["side"]=="buy" and symbol not in positions and len(positions)<slots:
                # Fixed slots: reserve at most 1/slots of starting capital.
                committed=sum(p["capital"] for p in positions.values())
                budget=min(starting_cash/slots,cash,
                           max(0,starting_cash*max_exposure_fraction-committed))
                if budget>0:
                    shares=budget/(price*(1+round_trip_cost_bps/20000))
                    positions[symbol]={"shares":shares,"capital":budget,"entry_index":t,
                                       "scheduled_exit":min(t+horizon-1,n-1)}
                    cash-=budget
        pending=[]
        max_open=max(max_open,len(positions))
        peak_invested=max(peak_invested,sum(p["capital"] for p in positions.values()))
        marked=cash+sum(p["shares"]*bars[s][t]["close"] for s,p in positions.items())
        equity.append(marked)
        majority_declining=False
        if positions:
            declining=sum(bars[s][t]["close"]<bars[s][t-1]["close"] for s in positions if t>0)
            fraction=declining/len(positions)
            majority_declining=fraction>0.5
            days_with_majority_declining+=majority_declining
            if declining>worst_breadth_day["declining_positions"] or (declining==worst_breadth_day["declining_positions"] and fraction>worst_breadth_day["fraction"]):
                worst_breadth_day={"index":t,"declining_positions":declining,"open_positions":len(positions),"fraction":round(fraction,4)}
        if prior_equity is not None:
            daily_move=100*(marked/prior_equity-1)
            worst_daily_equity_move_pct=min(worst_daily_equity_move_pct,daily_move)
            negative_equity_days+=daily_move<0
            (majority_day_equity_changes if majority_declining else other_day_equity_changes).append(daily_move)
        prior_equity=marked
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
            "worst_daily_equity_move_pct":round(worst_daily_equity_move_pct,4),
            "negative_equity_days":negative_equity_days,
            "days_with_majority_positions_declining":days_with_majority_declining,
            "mean_equity_change_majority_declining_pct":round(mean(majority_day_equity_changes),4) if majority_day_equity_changes else None,
            "worst_equity_change_majority_declining_pct":round(min(majority_day_equity_changes),4) if majority_day_equity_changes else None,
            "mean_equity_change_other_days_pct":round(mean(other_day_equity_changes),4) if other_day_equity_changes else None,
            "worst_declining_position_breadth":worst_breadth_day,
            "completed_trades":len(trades),"open_positions_at_end":len(positions),
            "max_simultaneous_positions":max_open,
            "peak_committed_capital_pct":round(100*peak_invested/starting_cash,4),
            "max_exposure_fraction":max_exposure_fraction,
            "warning_exit_trades":sum(x["reason"]=="warning" for x in trades),
            "severe_completed_losses":sum(x["net_pct"]<=-8 for x in trades),
            "worst_completed_trade_pct":round(worst_trade_pct,4),
            "completed_loss_buckets":loss_buckets,
            "severe_loss_by_symbol":dict(sorted(severe_loss_by_symbol.items())),
            "severe_loss_by_exit_reason":dict(sorted(severe_loss_by_reason.items())),
            "research_only":True,"trade_ready":False,"edge_proven":False,
            "dividends_and_fx_modelled":False,"corporate_actions_verified":False,
            "fractional_shares_assumed":True,"slippage_modelled":False,
            "entry_selection_bias_controlled":False,
            "cash_dividends_modelled":False,
            "risk_adjusted_benchmark_tested":False}
