"""Offline Spoor 2 pilot report using only previously recorded, unverified observations.

Do not infer that source files were freshly downloaded or authenticated.
"""
from research.spoor2_gap_report_bridge_20261118 import build_spoor2_gap_report

PILOT=(
    {"symbol":"ASML.AS","isin":"NL0010273215","operating_mic":"XAMS"},
    {"symbol":"IFX.DE","isin":"DE0006231004","operating_mic":"XETR"},
    {"symbol":"NOKIA.HE","isin":"FI0009000681","operating_mic":"XHEL"},
    {"symbol":"RHM.DE","isin":"DE0007030009","operating_mic":"XETR"},
)

def build_pilot_gap_report():
    audits={}
    for item in PILOT:
        audits[item["isin"]]={
            "instrument":{"status":"BLOCKED","blocks":["INSTRUMENT_LEVEL_EXCHANGE_REFERENCE_UNATTESTED"]},
            "mic":{"status":"BLOCKED","blocks":["EXACT_SEGMENT_MIC_NOT_VERIFIED"]},
            "xetra":{"status":"BLOCKED","blocks":["OFFICIAL_ARTIFACT_BYTES_NOT_CAPTURED"]},
            "degiro":{"status":"BLOCKED","blocks":["ACCOUNT_EXECUTION_ROUTE_NOT_ATTESTED"]},
            "fees":{"status":"BLOCKED","blocks":["ACCOUNT_SPECIFIC_FEES_NOT_ATTESTED"]},
            "manifest":{"status":"BLOCKED","blocks":["INDEPENDENT_PUBLISHER_ATTESTATION_MISSING"]},
        }
    result=build_spoor2_gap_report(list(PILOT),audits)
    result["source_scope"]="PREVIOUSLY_RECORDED_RESEARCH_OBSERVATIONS_ONLY"
    result["fresh_external_capture"]=False
    result["iso_effective_date_warning"]="2026-11-23 changes must not be treated as effective on 2026-11-18"
    return result
