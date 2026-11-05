"""Validate frozen research-only prospective momentum protocol."""
import json
from datetime import date
from pathlib import Path


def validate_protocol(path="research/prospective_momentum_protocol_v1.json"):
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    if spec["protocol_id"] != "dipsaus-prospective-momentum-v1":
        raise ValueError("unexpected_protocol_id")
    if date.fromisoformat(spec["first_eligible_signal_session"]) <= date.fromisoformat(
            spec["historical_data_inspected_through"]):
        raise ValueError("future_evaluation_overlaps_inspected_data")
    if spec["signal"]["lookback_trading_sessions"] != 3 or spec["signal"][
            "evaluation_horizon_trading_sessions"] != 3:
        raise ValueError("unexpected_signal_definition")
    if spec["symbols"] != ["COHU", "AMD", "META"] or spec["benchmark"] != "SPY":
        raise ValueError("unexpected_universe")
    if not all(spec["safety"][key] is False for key in
               ("trade_ready", "live_alerts_modified", "orders_placed")):
        raise ValueError("unsafe_protocol")
    if not spec["evaluation"]["no_retroactive_parameter_changes"]:
        raise ValueError("mutable_prospective_protocol")
    return {"protocol_id": spec["protocol_id"], "valid": True,
            "research_only": True, "trade_ready": False}


if __name__ == "__main__":
    print(json.dumps(validate_protocol()))
