"""Research-only MIC documentary checks. No source attestation or order authority."""
import re

MIC = re.compile(r"^[A-Z0-9]{4}$", re.ASCII)
REQUIRED = ("provider_symbol", "isin", "venue_mic_candidate", "currency")

def audit_mic_dossier(dossier):
    out = dict(status="BLOCKED", source_attested=False, mic_registered=False,
               broker_route_verified=False, broker_execution_quote_verified=False,
               segment_mic_verified=False,
               trade_ready=False, order_placement_enabled=False,
               instruments=[], blocks=[])
    if not isinstance(dossier, dict) or not isinstance(dossier.get("instruments"), list):
        out["blocks"].append("INVALID_DOSSIER")
        return out
    sources = dossier.get("evidence")
    if not isinstance(sources, list) or not sources:
        out["blocks"].append("NO_DOCUMENTARY_SOURCES")
    elif any(not isinstance(s, dict) or not isinstance(s.get("url"), str)
             or not s["url"].startswith("https://") or not s.get("role") for s in sources):
        out["blocks"].append("INVALID_DOCUMENTARY_SOURCE")
    seen = set()
    for item in dossier["instruments"]:
        if not isinstance(item, dict) or any(not isinstance(item.get(k), str)
               or not item[k] for k in REQUIRED):
            out["instruments"].append(dict(status="BLOCKED", blocks=["INVALID_INSTRUMENT_RECORD"]))
            continue
        key = tuple(item[k] for k in REQUIRED)
        blocks = []
        if key in seen:
            blocks.append("DUPLICATE_INSTRUMENT")
        seen.add(key)
        if not MIC.fullmatch(item["venue_mic_candidate"]):
            blocks.append("INVALID_MIC_FORMAT")
        if item["currency"] not in ("EUR", "USD", "GBP", "CHF", "DKK", "SEK", "NOK"):
            blocks.append("UNRECOGNIZED_CURRENCY")
        blocks.extend(("ISO_REGISTER_RECORD_NOT_ATTESTED", "BROKER_ROUTE_NOT_ATTESTED",
                       "SEGMENT_MIC_NOT_VERIFIED"))
        out["instruments"].append({**{k:item[k] for k in REQUIRED},
             "status":"BLOCKED", "blocks":blocks, "mic_registered":False,
             "broker_route_verified":False, "segment_mic_verified":False,
             "trade_ready":False})
    if not dossier["instruments"]:
        out["blocks"].append("EMPTY_INSTRUMENT_LIST")
    out["blocks"].extend(("ISO_REGISTER_RECORD_NOT_ATTESTED",
                          "BROKER_ROUTE_NOT_ATTESTED", "DEGIRO_EXECUTION_QUOTE_NOT_VERIFIED",
                          "SEGMENT_MIC_NOT_VERIFIED"))
    return out
