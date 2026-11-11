"""Isolated EU research dossier with untrusted HTTP envelope review.

Raw bytes are kept separate from the canonical financial candidate receipt.
No network I/O, notifications, orders, or external source attestation.
"""
from research.spoor2_eu_research_chain_20261111 import evaluate_eu_research_chain
from research.spoor2_eu_http_envelope_20261111 import review_http_capture_envelope

def evaluate_eu_http_research_dossier(candidate, *, http_record, raw_bytes, now_utc):
    base={"status":"BLOCKED","trade_ready":False,"order_placement_enabled":False,
          "notification_channel":"NONE"}
    envelope=review_http_capture_envelope(http_record,raw_bytes,now_utc=now_utc)
    if envelope["status"]!="HTTP_ENVELOPE_REVIEW_ONLY":
        return {**base,"blocks":envelope["blocks"],"http_envelope":envelope}
    chain=evaluate_eu_research_chain(candidate,now_utc=now_utc)
    blocks=list(dict.fromkeys(envelope["blocks"]+chain["blocks"]))
    return {**base,"status":"RESEARCH_ONLY" if chain["status"]=="RESEARCH_ONLY" else "BLOCKED",
            "blocks":blocks,"http_envelope":envelope,"research_chain":chain,
            "notification_channel":"RESEARCH_PREVIEW_ONLY" if chain["status"]=="RESEARCH_ONLY" else "NONE",
            "external_source_attested":False}
