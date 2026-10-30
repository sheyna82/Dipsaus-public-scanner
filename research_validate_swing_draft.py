"""Fail-closed validator for the prospective swing *draft*, not activation."""
import json
from pathlib import Path

DRAFT = "DRAFT_NOT_FROZEN_NOT_ACTIVE"
REQUIRED_LANES = {"technical_recovery", "event_catalyst"}
REQUIRED_HORIZONS = [3, 5, 10]


def validate_swing_draft(path="research/prospective_swing_protocol_v0_draft.json"):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("status") != DRAFT:
        raise ValueError("swing_draft_must_remain_inactive")
    if data.get("research_only") is not True or data.get("trade_ready") is not False:
        raise ValueError("unsafe_swing_protocol")
    if set(data.get("research_lanes", [])) != REQUIRED_LANES:
        raise ValueError("invalid_research_lanes")
    if data.get("evaluation", {}).get("completed_trading_session_horizons") != REQUIRED_HORIZONS:
        raise ValueError("invalid_swing_horizons")
    if data.get("entry_decision", {}).get("maximum_concurrent_positions") != 6:
        raise ValueError("invalid_position_cap")
    if data.get("entry_decision", {}).get("orders") != "RESEARCH_ONLY_NO_AUTOMATED_EXECUTION":
        raise ValueError("orders_must_be_disabled")
    if data.get("do_not_modify") != "research/prospective_momentum_protocol_v1.json":
        raise ValueError("frozen_protocol_protection_missing")
    if not data.get("must_resolve_before_freeze"):
        raise ValueError("unresolved_design_questions_missing")
    return {"valid_draft": True, "active": False, "research_only": True,
            "unresolved_count": len(data["must_resolve_before_freeze"])}
