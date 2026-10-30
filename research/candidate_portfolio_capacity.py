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
    rejected_signals=[]
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
                reason="SYMBOL_ALREADY_HELD"
            elif len(positions)>=max_positions:
                reason="CAPACITY_FULL"
            elif cash+1e-9<tranche:
                reason="INSUFFICIENT_CASH"
            else:
                reason=None
            if reason is not None:
                rejected[reason]+=1
                rejected_signals.append({"symbol":row["symbol"],"entry_day":day,
                                         "exit_day":row["exit_day"],"reason":reason})
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
            "rejected_signals":rejected_signals,
            "max_concurrent_positions":max_used,"initial_capital":round(capital,2),
            "ending_cash":round(cash,2),"realized_pnl":round(pnl,2),
            "realized_return_pct":round(100*pnl/capital,4),
            "accepted_signals":[{"symbol":r["symbol"],"entry_day":r["entry_day"],"exit_day":r["exit_day"],"net_return_pct":r["net_return_pct"]} for r in accepted],
            "limitations":["Signals and net returns must be computed independently without lookahead",
                           "Fixed tranche and fixed exit; no intra-trade equity or drawdown curve",
                           "No sector concentration or live fill model; priority must be predeclared",
                           "Historical simulation, not independent prospective validation"]}

def calendar_capital_occupancy(portfolio, tranche=3500.0):
    """Descriptive completed-trade capital-days, not session or MTM exposure."""
    holds=[row["exit_day"]-row["entry_day"]+1
           for row in portfolio["accepted_signals"]]
    units=sum(holds)*tranche
    return {"occupied_tranche_calendar_days":sum(holds),
            "capital_calendar_day_units":round(units,2),
            "longest_calendar_day_hold":max(holds,default=0),
            "realized_pnl_per_1000_capital_calendar_day_units":(
                round(1000*portfolio["realized_pnl"]/units,6) if units else None),
            "calendar_days_not_trading_sessions":True,
            "daily_mark_to_market_drawdown_verified":False}


def verified_session_occupancy(portfolio, trading_session_days, *, tranche=3500.0):
    """Count occupied entry-through-exit sessions on a caller-supplied calendar.

    Calendar provenance is NOT established by this function; callers must
    independently verify the session list and source exchange coverage.
    """
    if not isinstance(trading_session_days, (list, tuple)) or (
            any(type(day) is not int for day in trading_session_days)
            or list(trading_session_days) != sorted(set(trading_session_days))):
        raise ValueError("INVALID_TRADING_SESSION_DAYS")
    sessions=set(trading_session_days)
    counts=[]
    for row in portfolio["accepted_signals"]:
        if row["entry_day"] not in sessions or row["exit_day"] not in sessions:
            raise ValueError("TRADE_ENDPOINT_NOT_IN_TRADING_CALENDAR")
        counts.append(sum(row["entry_day"] <= day <= row["exit_day"]
                          for day in trading_session_days))
    units=sum(counts)*tranche
    return {"occupied_tranche_sessions":sum(counts),
            "capital_session_units":round(units,2),
            "longest_holding_sessions":max(counts,default=0),
            "realized_pnl_per_1000_capital_session_units":(
                round(1000*portfolio["realized_pnl"]/units,6) if units else None),
            "entry_and_exit_included":True,
            "calendar_provenance_independently_verified":False,
            "daily_mtm_drawdown_available":False}


def audited_equity_risk(portfolio, observations):
    """Risk from supplied independent close equity, never invented marks."""
    if observations is None:
        return {"status":"NOT_EVALUATED",
                "reason":"INDEPENDENT_DAILY_MARKS_AND_RECONCILED_FILLS_NOT_PROVIDED",
                "trade_ready":False}
    from pathlib import Path
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from research_swing_equity_risk import summarize_equity_curve
    risk=summarize_equity_curve(observations)
    if abs(float(risk["end_equity"])-portfolio["ending_cash"])>0.005:
        raise ValueError("PAIRED_EQUITY_ENDING_CASH_MISMATCH")
    risk["independent_source_verification"]=False
    risk["ledger_reconciliation_verified"]=False
    risk["limitations"]=["Ending cash checked; full ledger and daily marks not reconciled",
                         "Caller-supplied equity marks; provenance unverified",
                         "Not a trade-ready risk estimate"]
    return risk


def reconciled_paired_equity(portfolio, inputs):
    """Require a complete independent fill/mark ledger before claiming drawdown."""
    if inputs is None:
        return {"status":"NOT_EVALUATED","trade_ready":False,
                "reason":"RECONCILED_TRADES_DAILY_MARKS_AND_TRADING_DATES_REQUIRED"}
    if not isinstance(inputs,dict) or set(inputs)!={"trades","daily_marks","trading_dates"}:
        raise ValueError("INVALID_PAIRED_RECONCILIATION_INPUTS")
    from pathlib import Path
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from research_swing_portfolio_with_marks import backtest_portfolio_with_marks
    from research_swing_equity_risk import summarize_equity_curve
    from datetime import date, timedelta
    # The accepted-trade ledger alone cannot prove rejected signal population
    # or original priority equivalence. Do not advertise full cohort parity.
    verified=backtest_portfolio_with_marks(**inputs)
    accepted={(row["symbol"],date(1970,1,1)+timedelta(days=row["entry_day"]),
               date(1970,1,1)+timedelta(days=row["exit_day"]))
              for row in portfolio["accepted_signals"]}
    entries={}
    actual=set()
    pnl_by_trade={}
    from decimal import Decimal
    expected_pnl={(row["symbol"],date(1970,1,1)+timedelta(days=row["entry_day"]),
                   date(1970,1,1)+timedelta(days=row["exit_day"])):
                  Decimal("3500")*Decimal(str(row["net_return_pct"]))/100
                  for row in portfolio["accepted_signals"]}

    for event in verified["cash_accounting"]["ledger"]:
        key=event["ticker"]
        day=date.fromisoformat(event["date"])
        if event["action"]=="entry":
            if key in entries:
                raise ValueError("PAIRED_LEDGER_DUPLICATE_OPEN")
            entries[key]=day
        elif event["action"]=="exit":
            if key not in entries:
                raise ValueError("PAIRED_LEDGER_UNMATCHED_EXIT")
            trade_key=(key,entries.pop(key),day)
            actual.add(trade_key)
            pnl_by_trade[trade_key]=Decimal(str(event["net_pnl"]))
    if entries or actual!=accepted:
        raise ValueError("PAIRED_LEDGER_ACCEPTED_POPULATION_MISMATCH")
    if any(abs(pnl_by_trade[key]-expected_pnl[key])>Decimal("0.005")
           for key in expected_pnl):
        raise ValueError("PAIRED_LEDGER_TRADE_PNL_MISMATCH")
    if abs(float(verified["cash_accounting"]["realized_net_pnl"])-
           portfolio["realized_pnl"])>0.005:
        raise ValueError("PAIRED_LEDGER_PNL_MISMATCH")
    observations=[{"date":row["date"],"equity":row["equity"]}
                  for row in verified["equity"]["equity_curve"]]
    risk=summarize_equity_curve(observations)
    return {"status":"ARITHMETIC_RECONCILED_RESEARCH_ONLY","trade_ready":False,
            "risk":risk,"cash_equity_reconciliation":verified["cash_equity_reconciliation"],
            "independent_price_and_calendar_provenance_verified":False,
            "rejected_source_population_verified":False,
            "selection_priority_equivalence_verified":False}


def compare_ablation_portfolios(report, *, pattern, max_positions=6, trading_session_days=None,
                               paired_equity_observations=None, paired_reconciled_inputs=None):
    """Pool actual held-out dated events across symbols, one filter at a time.

    Never compare the same symbol-pattern twice, and never rank by test returns.
    Each filter gets identical deterministic symbol-priority tie breaking.
    """
    if not isinstance(report,dict) or not isinstance(report.get("candidates"),list):
        raise ValueError("INVALID_ABLATION_REPORT")
    from candidate_feature_ablation import FILTERS
    comparisons={}
    priority_sensitivity={}
    paired_liquidity_portfolios={}
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
        legacy_events=[]
        for candidate in report["candidates"]:
            symbol=candidate.get("symbol")
            detail=candidate.get("patterns",{}).get(pattern,{})
            if detail.get("status")!="DESCRIPTIVE_ONLY":
                continue
            for item in detail.get("legacy_retrospective_portfolio_events_25bps",{}).get(key,[]):
                legacy_events.append({**item,"symbol":symbol})
        legacy=simulate(legacy_events,max_positions=max_positions,priority_mode="symbol_asc")
        current=scenarios["symbol_asc"]
        session_comparison=None
        if trading_session_days is not None:
            session_comparison={
                "point_in_time":verified_session_occupancy(current,trading_session_days),
                "legacy_retrospective":verified_session_occupancy(legacy,trading_session_days),
                "calendar_source_verified":False}
        supplied_marks=(paired_equity_observations or {}).get(key,{})
        if supplied_marks and set(supplied_marks)!={"point_in_time","legacy_retrospective"}:
            raise ValueError("INCOMPLETE_PAIRED_EQUITY_OBSERVATIONS")
        equity_comparison={
            "point_in_time":audited_equity_risk(current,supplied_marks.get("point_in_time")),
            "legacy_retrospective":audited_equity_risk(legacy,supplied_marks.get("legacy_retrospective"))}
        supplied_reconciled=(paired_reconciled_inputs or {}).get(key,{})
        if supplied_reconciled and set(supplied_reconciled)!={"point_in_time","legacy_retrospective"}:
            raise ValueError("INCOMPLETE_PAIRED_RECONCILIATION_INPUTS")
        reconciled_comparison={
            "point_in_time":reconciled_paired_equity(current,supplied_reconciled.get("point_in_time")),
            "legacy_retrospective":reconciled_paired_equity(legacy,supplied_reconciled.get("legacy_retrospective"))}
        paired_liquidity_portfolios[key]={
            "point_in_time_event_n":len(events),
            "legacy_retrospective_event_n":len(legacy_events),
            "point_in_time":current,
            "legacy_retrospective":legacy,
            "point_in_time_capital_occupancy":calendar_capital_occupancy(current),
            "session_occupancy_comparison":session_comparison,
            "legacy_capital_occupancy":calendar_capital_occupancy(legacy),
            "realized_pnl_difference":round(current["realized_pnl"]-legacy["realized_pnl"],2),
            "return_difference_percentage_points":round(
                current["realized_return_pct"]-legacy["realized_return_pct"],4),
            "legacy_not_executable_at_next_open":True,
            "daily_equity_risk":equity_comparison,
            "reconciled_daily_equity_risk":reconciled_comparison,
            "historical_comparison_only":True}
        priority_sensitivity[key]={"scenarios":{mode:{"accepted_n":result["accepted_n"],
                                                "realized_return_pct":result["realized_return_pct"],
                                                "rejected_n":result["rejected_n"]}
                                                for mode,result in scenarios.items()},
                                   "return_range_pct_points":round(max(x["realized_return_pct"] for x in scenarios.values())-
                                                                   min(x["realized_return_pct"] for x in scenarios.values()),4)}
    return {"status":"DESCRIPTIVE_ONLY","trade_ready":False,
            "pattern":pattern,"entry_slippage_bps":25,
            "costs_included_in_trade_returns":True,
            "execution_cost_assumptions":{
                "roundtrip_fixed_cost_bps":50,
                "adverse_entry_slippage_bps":25,
                "entry_price":"next_session_open_adjusted_for_adverse_slippage",
                "exit_price":"horizon_session_close",
                "entry_liquidity_filter":"signal_session_close_times_volume",
                "point_in_time_liquidity_input":True,
                "point_in_time_executable":False,
                "broker_fee_fx_spread_exit_slippage_verified":False,
                "independent_cost_provenance_verified":False,
            },
            "comparison":comparisons,
            "paired_liquidity_portfolios":paired_liquidity_portfolios,
            "priority_sensitivity":priority_sensitivity,
            "limitations":["Held-out sample was previously inspected; not fresh out-of-sample evidence",
                           "One pattern at a time; cross-pattern opportunity competition not modeled",
                           "Fixed exits and no daily drawdown or equity curve",
                           "Three deterministic tie-breakers are sensitivity checks, not randomized inference",
                           "Historical convenience universe and daily open fill assumptions",
                           "Signal-session close-times-volume is observable before next open, but historical fills remain unverified",
                           "50 bps fixed costs and 25 bps entry slippage are model assumptions, not verified broker execution"]}
