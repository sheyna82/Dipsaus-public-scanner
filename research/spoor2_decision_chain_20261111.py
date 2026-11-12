"""Spoor 2 isolated decision chain: evidence -> costs -> notification preview.

Fail closed: this module never grants trade qualification. Its inputs are
untrusted research data, including any claimed verified/trade_ready booleans.
No network, broker API, ntfy sender, secrets, or order placement.
"""
import math
from research.spoor2_level_evidence_audit_20261111 import audit_levels
from research.spoor2_source_independence_20261111 import audit_source_independence
from research.spoor2_candidate_levels_20261111 import money_scenario, research_entry_zone
from research.spoor2_notification_policy_20261111 import (
    classify_notification, notification_subject, offline_notification_route,
)

def evaluate_research_chain(candidate, *, now_utc):
    if not isinstance(candidate, dict):
        return {"status": "BLOCKED", "blocks": ["INVALID_CANDIDATE"],
                "notification_channel": "NONE", "trade_ready": False,
                "order_placement_enabled": False}
    symbol = candidate.get("symbol")
    if not isinstance(symbol, str) or not symbol.strip():
        return {"status": "BLOCKED", "blocks": ["INVALID_SYMBOL"],
                "notification_channel": "NONE", "trade_ready": False,
                "order_placement_enabled": False}
    # This chain prices USD setups only. EU/GBp quotes must not be silently
    # interpreted as USD or converted without a separately audited adapter.
    market = candidate.get("market")
    quote_currency = candidate.get("quote_currency")
    market_blocks = []
    if market is not None and market != "US":
        market_blocks.append("MARKET_NOT_SUPPORTED_BY_USD_CHAIN")
    if quote_currency is not None and quote_currency != "USD":
        market_blocks.append("QUOTE_CURRENCY_NOT_USD")
    levels = audit_levels(candidate.get("technical_evidence"), now_utc=now_utc)
    provenance = audit_source_independence(candidate.get("technical_evidence"))
    blocks = market_blocks + list(levels.get("blocks", [])) + list(provenance["blocks"])
    scenario = None
    entry_zone = None
    technical = candidate.get("technical_evidence")
    if isinstance(technical, dict):
        entry_zone = research_entry_zone(
            broker_ask_usd=technical.get("broker_ask_usd"),
            invalidation_reference_usd=technical.get("invalidation_usd"),
            resistance_reference_usd=technical.get("resistance_usd"))
        if entry_zone["status"] != "ILLUSTRATIVE_ENTRY_ZONE_ONLY":
            blocks.append("RESEARCH_ENTRY_ZONE_NOT_ESTABLISHED")
    else:
        blocks.append("RESEARCH_ENTRY_ZONE_NOT_ESTABLISHED")
    args = candidate.get("money_inputs")
    if not isinstance(args, dict):
        blocks.append("MONEY_INPUTS_MISSING")
    else:
        # Explicitly whitelist inputs: no hidden overrides of readiness.
        required = ("budget_eur", "ask_usd", "exit_bid_usd",
                    "invalidation_usd", "eur_per_usd", "buy_fee_eur",
                    "sell_fee_eur", "buy_fx_rate", "sell_fx_rate")
        if any(key not in args for key in required):
            blocks.append("MONEY_INPUTS_INCOMPLETE")
        else:
            # Financial inputs must describe exactly the audited technical setup.
            # Otherwise a plausible R/R can be computed against a different
            # invalidation or target than the evidence actually supports.
            tech = candidate.get("technical_evidence")
            if not isinstance(tech, dict):
                blocks.append("TECHNICAL_EVIDENCE_MISSING")
            else:
                pairs = (
                    ("ask_usd", "broker_ask_usd", "ENTRY"),
                    ("invalidation_usd", "invalidation_usd", "INVALIDATION"),
                    ("exit_bid_usd", "resistance_usd", "EXIT_RESISTANCE"),
                )
                for money_key, technical_key, label in pairs:
                    money_value, technical_value = args.get(money_key), tech.get(technical_key)
                    if (not isinstance(money_value, (int, float))
                            or isinstance(money_value, bool)
                            or not isinstance(technical_value, (int, float))
                            or isinstance(technical_value, bool)
                            or not math.isfinite(money_value)
                            or not math.isfinite(technical_value)
                            or abs(money_value - technical_value) > 0.000001):
                        blocks.append(label + "_EVIDENCE_MISMATCH")
            try:
                scenario = money_scenario(**{key: args[key] for key in required},
                    slippage_buy_usd=args.get("slippage_buy_usd", 0),
                    slippage_sell_usd=args.get("slippage_sell_usd", 0))
            except (TypeError, ValueError, OverflowError, ZeroDivisionError):
                blocks.append("MONEY_CALCULATION_INVALID")
            else:
                if scenario.get("status") != "ILLUSTRATIVE_NOT_VERIFIED":
                    blocks.append("MONEY_CALCULATION_BLOCKED")
                elif scenario.get("net_profit_eur", 0) < 150:
                    blocks.append("NET_PROFIT_BELOW_150")
                if scenario.get("reference_rr", 0) < 2:
                    blocks.append("SCENARIO_RR_BELOW_TWO")
                # A gross 2R is not sufficient once execution friction is
                # included. Missing or invalid net R/R fails closed.
                net_rr = scenario.get("net_reference_rr_after_friction")
                if (not isinstance(net_rr, (int, float))
                        or isinstance(net_rr, bool)
                        or not math.isfinite(net_rr) or net_rr < 2):
                    blocks.append("NET_SCENARIO_RR_BELOW_TWO")
    # Never accept claimed trade_ready or claimed independent verification
    # from a historical dossier. Real broker/event/portfolio attestations
    # require a separate trusted source and future integration review.
    blocks.append("INDEPENDENT_TRADE_ATTESTATION_NOT_CONNECTED")
    classification = classify_notification({"phase": "BREAKOUT-SEEN"})
    return {
        "symbol": symbol,
        "status": "RESEARCH_ONLY",
        "technical_audit": levels,
        "source_independence_audit": provenance,
        "money_scenario": scenario,
        "entry_zone_research": entry_zone,
        "blocks": list(dict.fromkeys(blocks)),
        "notification_channel": classification["channel"],
        "offline_notification_route": offline_notification_route(classification),
        "notification_subject": notification_subject(symbol, classification),
        "trade_ready": False,
        "order_placement_enabled": False,
    }
