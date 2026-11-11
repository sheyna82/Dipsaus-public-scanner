"""Offline trade-level capital-efficiency diagnostics, not a trading strategy."""
import math


def compare_trade_capital_efficiency(trades, *, tranche_sizes=(3500, 5000, 7500, 10000),
                                     cost_rate=0.005):
    """Identical non-overlap trade samples scaled by tranche; no invented portfolio P&L.

    Each trade: return_pct (gross percentage), holding_days (>0), mae_pct (<=0).
    MAE is an adverse-excursion proxy, not portfolio drawdown. No compounding,
    concurrency, liquidity, funding, opportunity cost or independent validation.
    """
    if not isinstance(trades, list) or not trades:
        raise ValueError("INVALID_TRADE_SAMPLE")
    def number(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
    if not number(cost_rate) or not 0 <= cost_rate < 1:
        raise ValueError("INVALID_COST_RATE")
    if not isinstance(tranche_sizes, (list, tuple)) or not tranche_sizes or any(
            not number(t) or t <= 0 for t in tranche_sizes):
        raise ValueError("INVALID_TRANCHES")
    clean = []
    for trade in trades:
        if not isinstance(trade, dict) or not all(k in trade for k in ("return_pct", "holding_days", "mae_pct")):
            raise ValueError("INVALID_TRADE")
        gross, days, mae = (trade[k] for k in ("return_pct", "holding_days", "mae_pct"))
        if not all(number(x) for x in (gross, days, mae)) or days <= 0 or gross < -100 or mae > 0 or mae < -100:
            raise ValueError("INVALID_TRADE_METRICS")
        clean.append((gross / 100, days, mae / 100))
    total_days = sum(t[1] for t in clean)
    avg_net_return = sum(t[0] - cost_rate for t in clean) / len(clean)
    result = []
    for tranche in tranche_sizes:
        pnl = sum(tranche * (r - cost_rate) for r, _, _ in clean)
        capital_days = tranche * total_days
        result.append({
            "tranche_eur": float(tranche),
            "sample_net_pnl_eur": round(pnl, 2),
            "sample_capital_days_eur": round(capital_days, 2),
            "net_pnl_per_1000_eur_capital_days": round(1000 * pnl / capital_days, 6),
            "worst_single_trade_mae_eur_proxy": round(tranche * min(t[2] for t in clean), 2),
            "annualized_return": None,
            "portfolio_drawdown": None,
            "opportunity_cost_measured": False,
            "risk_adjusted": False,
        })
    return {
        "status": "RESEARCH_ONLY_TRADE_CAPITAL_EFFICIENCY",
        "trade_count": len(clean),
        "total_holding_days": total_days,
        "average_net_trade_return_pct": round(100 * avg_net_return, 6),
        "cost_rate": cost_rate,
        "scenarios": result,
        "independent_validation": False,
        "historical_alpha_established": False,
        "position_sizing_improvement_established": False,
        "trade_ready": False,
        "automatic_orders": False,
    }
