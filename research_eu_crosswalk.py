"""Research-only join of independently parsed Xetra and ISO snapshots.

Xetra numeric market-segment identifiers are NOT ISO segment MICs.
This bridge never attests source provenance, broker routing, or execution.
"""
from datetime import date

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False,
           "broker_route_verified": False}

def correlate(xetra, iso, *, as_of):
    base = {**BLOCKED, "status": "EU_CROSSWALK_BLOCKED"}
    if type(as_of) is not date:
        return {**base, "reason": "INVALID_AS_OF"}
    if not isinstance(xetra, dict) or xetra.get("status") != "OFFLINE_XETRA_SNAPSHOT_CONSISTENT":
        return {**base, "reason": "UNVALIDATED_XETRA"}
    if not isinstance(iso, dict) or iso.get("status") != "OFFLINE_ISO_MIC_RECORDS_CONSISTENT":
        return {**base, "reason": "UNVALIDATED_ISO"}
    try:
        effective = date.fromisoformat(iso["effective_date"])
    except (KeyError, TypeError, ValueError):
        return {**base, "reason": "INVALID_EFFECTIVE_DATE"}
    if effective > as_of:
        return {**base, "reason": "ISO_NOT_YET_EFFECTIVE"}
    instruments, selected = xetra.get("instruments"), iso.get("selected")
    if not isinstance(instruments, dict) or not instruments or not isinstance(selected, dict):
        return {**base, "reason": "MISSING_RECORDS"}
    joined = {}
    for isin, instrument in instruments.items():
        if not isinstance(instrument, dict):
            return {**base, "reason": "INVALID_INSTRUMENT"}
        mic = instrument.get("mic")
        record = selected.get(mic)
        if (not isinstance(record, dict) or record.get("kind") != "OPRT"
                or record.get("operating_mic") != mic or record.get("status") != "ACTIVE"):
            return {**base, "reason": "VENUE_MIC_NOT_CORROBORATED", "isin": isin}
        if not instrument.get("research_active"):
            return {**base, "reason": "INACTIVE_INSTRUMENT", "isin": isin}
        if not isinstance(instrument.get("segment"), str) or not isinstance(instrument.get("segment_description"), str) or not instrument.get("segment_description"):
            return {**base, "reason": "UNVERIFIED_XETRA_SEGMENT", "isin": isin}
        joined[isin] = {"venue_mic": mic, "xetra_segment_code": instrument["segment"],
                        "xetra_segment_description": instrument["segment_description"],
                        "iso_segment_mic_verified": False,
                        "listing_independently_verified": False}
    return {**BLOCKED, "status": "OFFLINE_EU_CROSSWALK_CONSISTENT",
            "iso_effective_date": effective.isoformat(), "instruments": joined,
            "iso_segment_mic_verified": False,
            "listing_independently_verified": False}
