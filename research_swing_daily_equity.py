"""Research-only daily equity and drawdown from audited close marks.

The ledger supplies accepted entry/exit events and realized cash amounts.
Marks are close prices expressed as a value per fixed invested tranche,
including no exit proceeds until the documented exit date. No FX, dividends
or intraday drawdown; missing marks fail closed.
"""
from datetime import date
from decimal import Decimal
from research_swing_chronological_ledger import _money


def daily_equity_from_ledger(ledger, daily_marks, trading_dates, *, initial_capital=21000,
                             tranche=3500):
    """Marks: {(date, ticker): close_value_of_invested_tranche}.

    Each mark must be the total value of the original tranche at that day's
    close, in the same currency as cash. Marks must be net of any known
    entry costs; exit cash already includes all realized costs.
    """
    capital, ticket = _money(initial_capital), _money(tranche)
    if capital <= 0 or ticket <= 0 or not isinstance(ledger, list):
        raise ValueError("invalid_equity_inputs")
    events = {}
    for event in ledger:
        day = date.fromisoformat(event["date"])
        events.setdefault(day, []).append(event)
    if not events:
        return {"research_only": True, "trade_ready": False,
                "equity_curve": [], "max_drawdown_pct": "0",
                "ending_equity": str(capital)}
    if (not isinstance(trading_dates, (tuple, list)) or
            any(type(day) is not date for day in trading_dates) or
            list(trading_dates) != sorted(set(trading_dates)) or
            not set(events).issubset(trading_dates)):
        raise ValueError('invalid_trading_dates')
    if not isinstance(daily_marks, dict):
        raise ValueError("invalid_marks")
    cash = capital
    positions = set()
    peak = capital
    worst = Decimal(0)
    curve = []
    for today in trading_dates:
        for event in events.get(today, []):
            ticker = event["ticker"]
            if event["action"] == "entry":
                if ticker in positions or cash < ticket:
                    raise ValueError("inconsistent_entry")
                cash -= ticket
                positions.add(ticker)
            elif event["action"] == "exit":
                if ticker not in positions:
                    raise ValueError("inconsistent_exit")
                positions.remove(ticker)
                cash = _money(event["cash"])
            else:
                raise ValueError("unknown_action")
        marked = Decimal(0)
        for ticker in sorted(positions):
            key = (today, ticker)
            if key not in daily_marks:
                raise ValueError("missing_daily_mark")
            value = _money(daily_marks[key])
            if value < 0:
                raise ValueError("negative_mark")
            marked += value
        equity = cash + marked
        peak = max(peak, equity)
        drawdown = (equity / peak - 1) * 100
        worst = min(worst, drawdown)
        curve.append({"date": today.isoformat(), "cash": str(cash),
                      "marked_positions": str(marked), "equity": str(equity),
                      "drawdown_pct": str(drawdown)})
    if positions:
        raise ValueError("unclosed_positions")
    return {"research_only": True, "trade_ready": False,
            "valuation": "trading_session_close_no_intraday",
            "equity_curve": curve, "max_drawdown_pct": str(worst),
            "ending_equity": str(cash)}
