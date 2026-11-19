"""Read-only MIC segment crosswalk from a validated offline parser result.

No source authentication, listing verification or broker execution authority.
"""
from research_iso_mic_parser import MIC

BLOCKED = {"trade_ready": False, "order_placement_enabled": False}


def resolve_mic_relationship(parsed, *, operating_mic, segment_mic):
    blocked = {**BLOCKED, "status": "MIC_CROSSWALK_BLOCKED",
               "source_authenticity_independently_verified": False}
    if not isinstance(parsed, dict) or parsed.get("status") != "OFFLINE_MIC_SCHEMA_VALIDATED":
        return {**blocked, "reason": "UNVALIDATED_REGISTER"}
    rows = parsed.get("records")
    if not isinstance(rows, dict) or not isinstance(operating_mic, str) or not isinstance(segment_mic, str):
        return {**blocked, "reason": "INVALID_INPUT"}
    if not MIC.fullmatch(operating_mic) or not MIC.fullmatch(segment_mic):
        return {**blocked, "reason": "INVALID_MIC"}
    parent = rows.get(operating_mic)
    segment = rows.get(segment_mic)
    if not isinstance(parent, dict) or parent.get("kind") != "OPRT" or parent.get("status") != "ACTIVE":
        return {**blocked, "reason": "OPERATING_MIC_NOT_ACTIVE"}
    if not isinstance(segment, dict) or segment.get("kind") != "SGMT" or segment.get("status") != "ACTIVE":
        return {**blocked, "reason": "SEGMENT_MIC_NOT_ACTIVE"}
    if segment.get("operating_mic") != operating_mic:
        return {**blocked, "reason": "SEGMENT_PARENT_MISMATCH"}
    return {**BLOCKED, "status": "OFFLINE_MIC_RELATIONSHIP_CONSISTENT",
            "operating_mic": operating_mic, "segment_mic": segment_mic,
            "source_authenticity_independently_verified": False,
            "broker_route_verified": False,
            "instrument_listing_verified": False}
