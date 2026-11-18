"""Historical FWB Prime Standard notices: documentary evidence, not current MIC attestation.

Read-only URLs of public official exchange notices. The notices concern
introductions of specific share tranches into existing price determination;
they do not certify today's instrument-level T7 segment MIC or broker route.
No network operations.
"""
NOTICES = {
    "DE0006231004": {
        "symbol_claim": "IFX.DE",
        "issuer": "Infineon Technologies AG",
        "notice_date": "2020-06-02",
        "introduction_date": "2020-06-03",
        "market_label": "Regulierter Markt - Prime Standard",
        "source_url": "https://www.cashmarket.deutsche-boerse.com/resource/blob/2038896/eb6237c1488b41709b63e64f28e1bfe2/data/Introduction_RM.pdf",
    },
    "DE0007030009": {
        "symbol_claim": "RHM.DE",
        "issuer": "Rheinmetall Aktiengesellschaft",
        "notice_date": "2023-05-05",
        "introduction_date": "2023-05-08",
        "market_label": "Regulierter Markt - Prime Standard",
        "source_url": "https://www.cashmarket.deutsche-boerse.com/resource/blob/3526200/ba24ef5ea206d37a4d752199f6260212/data/Introduction_RM.pdf",
    },
}


def build_historical_segment_notice_report():
    rows = []
    for isin, notice in sorted(NOTICES.items()):
        rows.append({
            "isin_claim": isin,
            **notice,
            "documentary_class": "HISTORICAL_OFFICIAL_EXCHANGE_NOTICE",
            "current_instrument_listing_attested": False,
            "current_market_segment_attested": False,
            "actual_segment_mic": None,
            "source_attested": False,
            "instrument_segment_verified": False,
            "segment_mic_verified": False,
            "broker_route_verified": False,
            "degiro_fee_verified": False,
            "trade_ready": False,
            "order_placement_enabled": False,
            "blocks": ["HISTORICAL_NOTICE_NOT_CURRENT_SEGMENT_ATTESTATION",
                       "INSTRUMENT_SPECIFIC_T7_MIC_NOT_ATTESTED",
                       "DEGIRO_ROUTE_NOT_ATTESTED"],
        })
    return {"status": "BLOCKED", "fresh_xetra_artifact_capture": False,
            "source_attested": False, "trade_ready": False,
            "order_placement_enabled": False, "notify": False,
            "automatic_orders": False, "rows": rows}
