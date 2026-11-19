"""Read-only primary-source pointers for EU pilot research, reviewed 2026-11-18.

URLs are documentary leads, not downloaded artifacts, signatures, live listings,
ISO 10383 attestations, or DEGIRO account-route evidence. No network access.
"""
from research.spoor2_pilot_gap_report_20261118 import PILOT

PRIMARY_SOURCE_LEADS = {
    "NL0010273215": {
        "issuer_url": "https://www.investor.asml.com/share-information",
        "claim": "Issuer identifies ISIN and Euronext Amsterdam listing",
        "mic_directly_stated": False,
    },
    "DE0006231004": {
        "issuer_url": "https://www.infineon.com/about/investor/infineon-share",
        "claim": "Issuer identifies ISIN and references Xetra trading system",
        "mic_directly_stated": False,
    },
    "FI0009000681": {
        "issuer_url": "https://www.nokia.com/newsroom/nokia-corporation-managers-transactions-ahopelto/",
        "claim": "Issuer transaction notice identifies ISIN and XHEL venue",
        "mic_directly_stated": True,
    },
    "DE0007030009": {
        "issuer_url": "https://ir.rheinmetall.com/news/armin-theodor-papperger/f94331e2-df16-4987-88be-c6f9d27b3116",
        "claim": "Issuer transaction notice identifies ISIN and XETR venue",
        "mic_directly_stated": True,
    },
}


def build_primary_source_lead_report():
    rows = []
    for item in PILOT:
        lead = PRIMARY_SOURCE_LEADS[item["isin"]]
        rows.append({
            "symbol_claim": item["symbol"],
            "isin_claim": item["isin"],
            "operating_mic_claim": item["operating_mic"],
            "issuer_url": lead["issuer_url"],
            "documentary_claim": lead["claim"],
            "mic_directly_stated_in_issuer_document": lead["mic_directly_stated"],
            "evidence_class": "UNATTESTED_PUBLIC_ISSUER_PAGE_POINTER",
            "source_attested": False,
            "instrument_segment_verified": False,
            "segment_mic_verified": False,
            "broker_route_verified": False,
            "degiro_fee_verified": False,
            "trade_ready": False,
            "order_placement_enabled": False,
        })
    return {
        "status": "BLOCKED",
        "fresh_external_artifact_capture": False,
        "independent_source_attestation": False,
        "trade_ready": False,
        "order_placement_enabled": False,
        "rows": rows,
    }
