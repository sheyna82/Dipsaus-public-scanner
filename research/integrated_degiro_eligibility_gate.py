"""Research-only DEGIRO eligibility gate; unknown instrument availability fails closed."""
import json
from pathlib import Path

CONFIG = Path(__file__).with_name("degiro_eligibility_research_20261106.json")
SUPPORTED = "EXCHANGE_SUPPORTED_INSTRUMENT_UNVERIFIED"
UNSUPPORTED = "EXCHANGE_NOT_LISTED_BY_DEGIRO_UNVERIFIED"

def evaluate(config, verified_instruments=None):
    if config.get("schema") != "dipsaus.research_broker_eligibility.v1":
        raise ValueError("INVALID_ELIGIBILITY_SCHEMA")
    if config.get("research_only") is not True or config.get("trade_ready") is not False:
        raise ValueError("UNSAFE_ELIGIBILITY_CONFIG")
    if config.get("live_scanner_changed") is not False:
        raise ValueError("LIVE_SCANNER_CHANGE_NOT_ALLOWED")
    if config.get("broker") != "DEGIRO NL":
        raise ValueError("WRONG_BROKER")
    rules = config["rules"]
    for key in ("supported_exchange_required", "exact_instrument_in_account_required",
                "isin_and_listing_required", "liquidity_spread_costs_fx_required",
                "unverified_is_not_eligible"):
        if rules.get(key) is not True:
            raise ValueError("UNSAFE_ELIGIBILITY_RULE:" + key)
    if config.get("portfolio_constraints", {}).get("orders") != "MANUAL_ONLY":
        raise ValueError("AUTOMATED_ORDERS_NOT_ALLOWED")
    if config["portfolio_constraints"].get("stoploss_or_stoplimit") is not False:
        raise ValueError("UNSAFE_ORDER_TYPE")
    verified_instruments = verified_instruments or {}
    results = []
    seen = set()
    for candidate in config["candidates"]:
        symbol = candidate["symbol"]
        if symbol in seen:
            raise ValueError("DUPLICATE_SYMBOL:" + symbol)
        seen.add(symbol)
        if candidate["status"] not in (SUPPORTED, UNSUPPORTED):
            raise ValueError("UNKNOWN_EXCHANGE_STATUS:" + symbol)
        evidence = verified_instruments.get(symbol, {})
        if not isinstance(evidence, dict):
            raise ValueError("INVALID_INSTRUMENT_EVIDENCE:" + symbol)
        # A positive account listing alone is insufficient: require identity, fees, liquidity.
        eligible = (
            candidate["status"] == SUPPORTED
            and evidence.get("account_verified") is True
            and isinstance(evidence.get("isin"), str) and len(evidence["isin"]) == 12
            and evidence.get("market") == candidate["market"]
            and evidence.get("liquidity_spread_costs_fx_verified") is True
        )
        results.append({"symbol": symbol, "eligible_for_recovery_screen": eligible,
                        "trade_ready": False,
                        "status": "BROKER_SCREEN_ELIGIBLE_RESEARCH_ONLY" if eligible else "BLOCKED_UNVERIFIED_OR_UNSUPPORTED"})
    return {"status": "RESEARCH_ONLY_BROKER_GATE", "trade_ready": False, "candidates": results}

if __name__ == "__main__":
    result = evaluate(json.loads(CONFIG.read_text(encoding="utf-8")))
    assert all(not row["eligible_for_recovery_screen"] for row in result["candidates"])
    print(result["status"], "candidates", len(result["candidates"]), "eligible", 0)
