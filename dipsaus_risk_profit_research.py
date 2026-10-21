"""Offline risk/profit context combination; does not replace live profit watch."""


def combine_research(risk_pressure, profit_context):
    """Keep profit and risk evidence separate; never manufacture an exit order."""
    if (not isinstance(risk_pressure, dict)
            or risk_pressure.get("research_only") is not True
            or risk_pressure.get("trade_ready") is not False
            or risk_pressure.get("notify") is not False
            or risk_pressure.get("sell_recommendation") is not False
            or not isinstance(profit_context, dict)):
        return None
    # Do not accept arbitrary strings as verified live profit-watch output.
    state = profit_context.get("status")
    if state not in ("NO_PROFIT_CONTEXT", "PROFIT_ZONE_OBSERVED", "PROFIT_GIVEBACK_OBSERVED"):
        return None
    risk_state = risk_pressure.get("state")
    if risk_state not in ("ABOVE_REFERENCE_SUPPORT", "BELOW_SUPPORT_REVIEW",
                          "DEEPER_SUPPORT_BREACH_REVIEW"):
        return None
    return {
        "risk_state": risk_state,
        "profit_state": state,
        "joint_review": (risk_state != "ABOVE_REFERENCE_SUPPORT"
                         or state != "NO_PROFIT_CONTEXT"),
        "risk_and_profit_both_need_review": (
            risk_state != "ABOVE_REFERENCE_SUPPORT"
            and state != "NO_PROFIT_CONTEXT"),
        "evidence_verified": False,
        "research_only": True,
        "trade_ready": False,
        "notify": False,
        "automatic_sell": False,
        "stop_order_created": False,
        "stop_advice_enabled": False,
        "note": "Offline labels only; live profit-watch evidence is not connected.",
    }
