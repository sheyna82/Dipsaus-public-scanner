"""Pure offline technical risk research. No orders, alerts, or network access."""

import math


def _valid(x):
    return type(x) in (int, float) and math.isfinite(x) and x > 0

def assess_risk(bars, entry, target=None, period=14, stoploss_advice=False):
    """Chronological OHLC dictionaries. Outputs research references, never orders."""
    if stoploss_advice is not False or type(period) is not int or period < 2:
        return None
    if not isinstance(bars, (list, tuple)) or len(bars) < period + 1 or not _valid(entry):
        return None
    if target is not None and not _valid(target):
        return None
    for b in bars:
        if not isinstance(b, dict) or any(not _valid(b.get(k)) for k in ("high", "low", "close")):
            return None
        if b["low"] > b["close"] or b["close"] > b["high"]:
            return None
    # Reject malformed chronological sessions rather than silently calculating on them.
    if any("date" in b for b in bars):
        from datetime import date
        try:
            days = [date.fromisoformat(b["date"]) for b in bars]
        except (KeyError, TypeError, ValueError):
            return None
        if any(not isinstance(b["date"], str) or b["date"] != d.isoformat() for b, d in zip(bars, days)):
            return None
        if any(b <= a for a, b in zip(days, days[1:])):
            return None
    trs = []
    for previous, current in zip(bars, bars[1:]):
        trs.append(max(current["high"] - current["low"],
                       abs(current["high"] - previous["close"]),
                       abs(current["low"] - previous["close"])))
    atr = sum(trs[-period:]) / period
    previous_atr = (sum(trs[-2*period:-period]) / period
                    if len(trs) >= 2 * period else None)
    volatility_expansion = (atr / previous_atr >= 1.5
                            if previous_atr is not None and previous_atr > 0 else None)
    # A large overnight gap makes stop references particularly unreliable.
    last_open = bars[-1].get("open")
    if last_open is not None and (not _valid(last_open)
                                 or not bars[-1]["low"] <= last_open <= bars[-1]["high"]):
        return None
    overnight_gap_atr = (abs(last_open - bars[-2]["close"]) / atr
                         if last_open is not None and atr > 0 else None)
    overnight_gap_warning = (overnight_gap_atr >= 1.5
                             if overnight_gap_atr is not None else None)
    previous_low = min(b["low"] for b in bars[-11:-1])
    trend_break = bars[-1]["close"] < previous_low
    invalidation = min(b["low"] for b in bars[-11:-1])
    downside = entry - invalidation
    upside = target - entry if target is not None else None
    rr = upside / downside if upside is not None and upside > 0 and downside > 0 else None
    return {"atr": round(atr, 6), "atr_pct_of_entry": round(100 * atr / entry, 4),
            "technical_invalidation_reference": invalidation,
            "volatility_expansion_1_5x": volatility_expansion,
            "overnight_gap_atr_units": round(overnight_gap_atr, 4) if overnight_gap_atr is not None else None,
            "overnight_gap_warning_1_5x_atr": overnight_gap_warning,
            "trend_break_below_previous_10_bar_low": trend_break,
            "risk_reward": round(rr, 4) if rr is not None else None,
            "risk_reward_unresolved": rr is None,
            "invalidation_below_entry": downside > 0,
            "stoploss_advice_enabled": False, "order_instruction": None,
            "research_only": True, "trade_ready": False,
            "warning": "Invalidation is not a guaranteed exit price or maximum loss."}


def research_optional_stop_reference(bars, entry, atr_multiplier=2.0, period=14):
    """Offline, non-executable stop-reference study; never an order recommendation.

    Compare a structural support reference with an ATR buffer. Both are
    illustrative levels, not guaranteed fills or loss caps. No live wiring.
    """
    if not _valid(atr_multiplier):
        return None
    risk = assess_risk(bars, entry, period=period)
    if risk is None or not risk["invalidation_below_entry"]:
        return None
    atr_reference = entry - atr_multiplier * risk["atr"]
    structural_reference = risk["technical_invalidation_reference"]
    if atr_reference <= 0:
        return None
    return {
        "atr_buffer_reference": round(atr_reference, 6),
        "structural_reference": structural_reference,
        "atr_multiplier": atr_multiplier,
        "reference_only": True,
        "stop_order_proposed": False,
        "order_instruction": None,
        "research_only": True,
        "trade_ready": False,
        "warning": ("A stop order can fill below its trigger after gaps or slippage; "
                    "a stop-limit order may not fill at all. These levels are "
                    "not guaranteed exits or maximum losses."),
    }


def research_profit_protection_reference(entry, highest_close, atr, previous_reference=None,
                                         activation_gain_pct=5.0, atr_multiplier=2.0):
    """Offline trailing reference inspired by external stop research; never places orders.

    Uses highest *closing* price, not intraday highs, and activates only after
    a configurable unrealized gain. Previous reference must come from the
    caller's offline research state; the result never lowers that reference.
    """
    if any(not _valid(x) for x in (entry, highest_close, atr,
                                   activation_gain_pct, atr_multiplier)):
        return None
    if highest_close < entry or (previous_reference is not None and not _valid(previous_reference)):
        return None
    gain_pct = 100 * (highest_close / entry - 1)
    if gain_pct < activation_gain_pct:
        return {"active": False, "reference": previous_reference,
                "research_only": True, "trade_ready": False,
                "order_instruction": None}
    candidate = highest_close - atr_multiplier * atr
    if candidate <= 0:
        return None
    reference = max(candidate, previous_reference) if previous_reference is not None else candidate
    return {"active": True, "reference": round(reference, 6),
            "gain_pct": round(gain_pct, 4), "research_only": True,
            "trade_ready": False, "order_instruction": None,
            "warning": "Trailing reference is not a guaranteed exit or loss limit."}


def research_pullback_context(bars, period=14):
    """Classify last-close drawdown relative to ATR; offline context, not a trade signal.

    A close below prior 10-session support is treated as structural damage,
    while smaller declines are described relative to normal daily movement.
    """
    if not isinstance(bars, (list, tuple)) or not bars:
        return None
    entry = bars[-1].get("close") if isinstance(bars[-1], dict) else None
    risk = assess_risk(bars, entry, period=period)
    if risk is None or risk["atr"] <= 0:
        return None
    previous_close = bars[-2]["close"]
    decline = max(0.0, previous_close - entry)
    atr_units = decline / risk["atr"]
    if risk["trend_break_below_previous_10_bar_low"]:
        context = "structural_break"
    elif risk["volatility_expansion_1_5x"] is True:
        context = "volatility_expansion"
    elif atr_units <= 1.0:
        context = "within_one_atr"
    else:
        context = "large_move_without_confirmed_break"
    return {"context": context, "down_move_atr_units": round(atr_units, 4),
            "research_only": True, "trade_ready": False, "order_instruction": None,
            "warning": "Heuristic context only; no validated predictive performance."}


def research_consolidated_risk(bars, period=14):
    """One offline risk assessment from overlapping technical indicators.

    Precedence is intentional: structural break > gap > volatility expansion >
    unusually large pullback > routine movement. This is NOT a notification.
    """
    context = research_pullback_context(bars, period=period)
    if context is None:
        return None
    risk = assess_risk(bars, bars[-1]["close"], period=period)
    if risk is None:
        return None
    reasons = []
    if risk["trend_break_below_previous_10_bar_low"]:
        reasons.append("prior_support_broken")
    if risk["overnight_gap_warning_1_5x_atr"] is True:
        reasons.append("large_overnight_gap")
    if risk["volatility_expansion_1_5x"] is True:
        reasons.append("volatility_expansion")
    if context["down_move_atr_units"] > 1.0:
        reasons.append("large_daily_decline")
    priority = ("structural_break" if "prior_support_broken" in reasons else
                "large_gap" if "large_overnight_gap" in reasons else
                "volatility_expansion" if "volatility_expansion" in reasons else
                "large_pullback" if "large_daily_decline" in reasons else "routine")
    return {"priority": priority, "reasons": reasons, "single_summary": True,
            "notification_sent": False, "research_only": True,
            "trade_ready": False, "order_instruction": None,
            "warning": "Research classification; no live alert or order."}


def research_alert_transition(previous, current):
    """Pure offline comparison of consecutive consolidated risk assessments.

    Only a new issue, a worsening priority, or newly appearing reason merits
    review. This returns a suggestion, never sends a notification.
    """
    ranks = {"routine": 0, "large_pullback": 1, "volatility_expansion": 2,
             "large_gap": 3, "structural_break": 4}
    if not isinstance(current, dict) or current.get("priority") not in ranks:
        return None
    if not isinstance(current.get("reasons"), list) or any(
        not isinstance(reason, str) for reason in current["reasons"]
    ):
        return None
    if previous is not None:
        if not isinstance(previous, dict) or previous.get("priority") not in ranks:
            return None
        if not isinstance(previous.get("reasons"), list) or any(
            not isinstance(reason, str) for reason in previous["reasons"]
        ):
            return None
    old_priority = previous["priority"] if previous is not None else "routine"
    old_reasons = set(previous["reasons"]) if previous is not None else set()
    new_reasons = sorted(set(current["reasons"]) - old_reasons)
    escalated = ranks[current["priority"]] > ranks[old_priority]
    suggest_review = current["priority"] != "routine" and (
        escalated or bool(new_reasons))
    return {"suggest_review": suggest_review,
            "priority_escalated": escalated,
            "new_reasons": new_reasons,
            "duplicate_suppressed": not suggest_review,
            "notification_sent": False,
            "research_only": True, "order_instruction": None}
