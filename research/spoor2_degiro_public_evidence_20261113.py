"""Official DEGIRO public-document evidence inventory; no account-specific claims.

Public URLs establish documentation availability, not an account's execution
route, applicable tariff, or a particular trade's realized fees.
"""
SOURCES = {
    "execution_process": "https://www.degiro.nl/helpdesk/handelsmogelijkheden/wat-gebeurt-er-wanneer-een-order-uitgevoerd",
    "trading_venue": "https://www.degiro.nl/helpdesk/handelsmogelijkheden/wat-een-trading-venue-handelsplaats",
    "fees": "https://www.degiro.nl/tarieven",
    "connectivity": "https://www.degiro.nl/helpdesk/tarieven/transactiekosten/wat-zijn-de-degiro-aansluitingskosten-connectivity-fees",
    "fx": "https://www.degiro.nl/helpdesk/geld-overboeken/valuta-afhandeling/kan-ik-een-vreemde-valuta-beleggen",
    "venues_reports": "https://www.degiro.nl/helpdesk/andere-documenten/handel-en-beurzen",
}

def assess_public_degiro_evidence(instrument_ledger):
    out = {"status": "BLOCKED", "sources": dict(SOURCES),
           "public_documentation_identified": True,
           "public_documentation_independently_attested": False,
           "account_execution_route_verified": False,
           "account_tariff_verified": False,
           "broker_route_verified": False, "degiro_fee_verified": False,
           "trade_ready": False, "order_placement_enabled": False,
           "instruments": [], "blocks": []}
    if not isinstance(instrument_ledger, dict) or not isinstance(instrument_ledger.get("instruments"), list):
        out["blocks"].append("INVALID_INSTRUMENT_LEDGER")
        return out
    records = instrument_ledger["instruments"]
    expected = {"DE0006231004", "DE0007030009"}
    if len(records) != 2 or any(not isinstance(r, dict) for r in records) or {r.get("isin") for r in records} != expected:
        out["blocks"].append("INCOMPLETE_OR_INVALID_INSTRUMENT_SET")
        return out
    for r in records:
        out["instruments"].append({
            "isin": r["isin"],
            "public_execution_venue_context": "IDENTIFIED_NOT_ACCOUNT_ATTESTED",
            "public_fee_context": "IDENTIFIED_NOT_ACCOUNT_ATTESTED",
            "degiro_execution_route": None,
            "account_specific_fee": None,
            "fx_fee_applicability": "UNDETERMINED",
            "connectivity_fee_applicability": "UNDETERMINED",
            "trade_ready": False,
        })
    out["blocks"].extend((
        "PUBLIC_DOCUMENTATION_NOT_ACCOUNT_EXECUTION_PROOF",
        "XETRA_COMMISSION_NOT_ACCOUNT_ATTESTED",
        "HANDLING_FEE_NOT_ACCOUNT_ATTESTED",
        "FX_APPLICABILITY_NOT_ATTESTED",
        "CONNECTIVITY_FEE_APPLICABILITY_NOT_ATTESTED",
    ))
    return out
