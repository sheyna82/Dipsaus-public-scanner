"""Research-only closed-trade net-profit diagnostics.

Independent Decimal implementation inspired by standard QuantStats metrics.
Inputs are already NET realized P&L per completed trade, in one currency.
This is not a time-weighted portfolio return or proof of a trading edge.
"""
from decimal import Decimal, InvalidOperation


def _d(value):
    if isinstance(value, bool):
        raise ValueError("invalid_trade_pnl")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("invalid_trade_pnl") from None
    if not result.is_finite():
        raise ValueError("invalid_trade_pnl")
    return result


def analyze_closed_trade_pnl(net_pnls):
    if not isinstance(net_pnls, (list, tuple)) or not net_pnls:
        raise ValueError("empty_trade_sample")
    values = [_d(x) for x in net_pnls]
    wins = [x for x in values if x > 0]
    losses = [x for x in values if x < 0]
    gross_profit = sum(wins, Decimal(0))
    gross_loss = -sum(losses, Decimal(0))
    total = sum(values, Decimal(0))
    count = len(values)
    profit_factor = (
        str((gross_profit / gross_loss).quantize(Decimal("0.0001")))
        if gross_loss else ("undefined_no_losses" if gross_profit else "undefined_no_profit_or_loss"))
    def money(x):
        return str(x.quantize(Decimal("0.01")))
    return {
        "research_only": True, "trade_ready": False,
        "trade_count": count, "winning_trades": len(wins),
        "losing_trades": len(losses),
        "breakeven_trades": count - len(wins) - len(losses),
        "net_profit": money(total),
        "average_net_pnl_per_trade": money(total / count),
        "average_win": money(gross_profit / len(wins)) if wins else None,
        "average_loss": money(-gross_loss / len(losses)) if losses else None,
        "win_rate_pct": str((Decimal(len(wins)) * 100 / count).quantize(Decimal("0.01"))),
        "profit_factor": profit_factor,
        "worst_trade": money(min(values)),
        "best_trade": money(max(values)),
        "portfolio_drawdown_not_computed": True,
        "currency_normalization_verified": False,
        "independent_real_trade_data_verified": False,
    }
