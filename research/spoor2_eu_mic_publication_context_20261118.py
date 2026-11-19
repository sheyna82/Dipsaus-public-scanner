"""Offline ISO 10383 publication context for the four EU pilot research claims.

The November 2026 MIC edition was published 2026-11-09; modifications are
effective 2026-11-23, not 2026-11-18. Venue names are documentary context,
not a captured/attested ISO registry record or instrument-level segment proof.
No external access, trading, or account-specific broker assertions.
"""
from datetime import date
from research.spoor2_pilot_gap_report_20261118 import PILOT

PUBLICATION_DATE = date(2026, 11, 9)
IMPLEMENTATION_DATE = date(2026, 11, 23)
OFFICIAL_REGISTRY_PAGE = "https://www.iso20022.org/market-identifier-codes"
VENUE_CONTEXT = {
    "XAMS": "Euronext Amsterdam",
    "XETR": "Deutsche Boerse Xetra",
    "XHEL": "Nasdaq Helsinki",
}


def build_mic_publication_context(as_of="2026-11-18"):
    blocked = {
        "status": "BLOCKED",
        "source_attested": False,
        "instrument_segment_verified": False,
        "segment_mic_verified": False,
        "broker_route_verified": False,
        "degiro_fee_verified": False,
        "trade_ready": False,
        "order_placement_enabled": False,
        "automatic_orders": False,
        "notify": False,
    }
    try:
        observation_date = date.fromisoformat(as_of)
    except (TypeError, ValueError):
        return {**blocked, "blocks": ["INVALID_OBSERVATION_DATE"], "rows": []}
    if observation_date < PUBLICATION_DATE:
        return {**blocked, "blocks": ["MIC_EDITION_NOT_YET_PUBLISHED"], "rows": []}
    rows = []
    for item in PILOT:
        mic = item["operating_mic"]
        rows.append({
            "symbol_claim": item["symbol"],
            "isin_claim": item["isin"],
            "operating_mic_claim": mic,
            "venue_context": VENUE_CONTEXT[mic],
            "mic_registry_record_attested": False,
            "instrument_listing_attested": False,
            "segment_mic_attested": False,
            "november_changes_effective_as_of_date": observation_date >= IMPLEMENTATION_DATE,
            "blocks": [
                "MIC_REGISTRY_RECORD_NOT_INDEPENDENTLY_CAPTURED",
                "INSTRUMENT_LEVEL_SEGMENT_NOT_ATTESTED",
                "BROKER_EXECUTION_ROUTE_NOT_ATTESTED",
            ],
        })
    return {
        **blocked,
        "blocks": ["INDEPENDENT_MIC_AND_INSTRUMENT_EVIDENCE_MISSING"],
        "iso_publication_date": PUBLICATION_DATE.isoformat(),
        "iso_modifications_effective_date": IMPLEMENTATION_DATE.isoformat(),
        "as_of_date": observation_date.isoformat(),
        "registry_documentation_url": OFFICIAL_REGISTRY_PAGE,
        "rows": rows,
    }
