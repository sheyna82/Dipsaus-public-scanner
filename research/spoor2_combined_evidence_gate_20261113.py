"""Research-only composition of existing instrument audit and MIC documentary audit."""
from research.spoor2_instrument_venue_fee_audit_20261113 import audit_instrument_venue_fee
from research.spoor2_mic_evidence_gate_20261113 import audit_mic_dossier

def audit_combined_evidence(candidate, mic_dossier, *, isin_record=None,
                            mic_record=None, listing_record=None, degiro_record=None):
    candidate = candidate if isinstance(candidate, dict) else {}
    identity = audit_instrument_venue_fee(
        candidate, isin_record=isin_record, mic_record=mic_record,
        listing_record=listing_record, degiro_record=degiro_record)
    mic = audit_mic_dossier(mic_dossier)
    matching = [x for x in mic["instruments"]
                if x.get("provider_symbol") == candidate.get("symbol")
                and x.get("isin") == candidate.get("isin")
                and x.get("venue_mic_candidate") == candidate.get("venue_mic")
                and x.get("currency") == candidate.get("trading_currency")]
    blocks = list(dict.fromkeys(identity["blocks"] + mic["blocks"] +
                  ([] if len(matching)==1 else ["MIC_DOSSIER_INSTRUMENT_MISMATCH"])))
    if matching:
        blocks = list(dict.fromkeys(blocks + matching[0]["blocks"]))
    return {"status":"BLOCKED", "identity_documentary":identity,
            "mic_documentary":mic, "matching_mic_record_count":len(matching),
            "source_attested":False, "mic_registered":False,
            "broker_route_verified":False, "segment_mic_verified":False,
            "degiro_fee_verified":False,
            "trade_ready":False, "order_placement_enabled":False, "blocks":blocks}
