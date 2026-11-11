"""Pre-registered short-swing market regime gate; research-only, no orders.

A conservative proxy based on index closes and realized volatility. Thresholds
are hypotheses, not calibrated probabilities or guaranteed crash protection.
"""
from math import log, sqrt, isfinite
from statistics import pstdev

def assess_short_swing_regime(index_closes, *, lookback=20):
    if type(lookback) is not int or lookback < 10:
        raise ValueError("invalid_lookback")
    if not isinstance(index_closes, (list, tuple)) or len(index_closes) < max(60, lookback + 1):
        raise ValueError("insufficient_index_history")
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or
           not isfinite(x) or x <= 0 for x in index_closes):
        raise ValueError("invalid_index_close")
    prices = index_closes
    returns = [log(prices[i] / prices[i-1]) for i in range(len(prices)-lookback, len(prices))]
    vol = pstdev(returns) * sqrt(252)
    drawdown20 = prices[-1] / max(prices[-20:]) - 1
    below_ma50 = prices[-1] < sum(prices[-50:]) / 50
    if drawdown20 <= -.10 or (below_ma50 and vol >= .35):
        state, new_entries = "risk_off", False
    elif drawdown20 <= -.05 or vol >= .25 or below_ma50:
        state, new_entries = "caution", True
    else:
        state, new_entries = "normal", True
    return {"research_only": True, "trade_ready": False,
            "state": state, "new_entries_permitted_for_research": new_entries,
            "suggested_max_positions": {"normal": 6, "caution": 3, "risk_off": 0}[state],
            "preferred_horizons": [5, 10, 15],
            "realized_volatility_annualized": round(vol, 5),
            "recent_drawdown": round(drawdown20, 5),
            "below_50_session_average": below_ma50,
            "thresholds_validated_out_of_sample": False,
            "crash_protection_guaranteed": False}
