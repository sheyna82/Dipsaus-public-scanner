"""Dated public DEGIRO Xetra fee schedule; never account-specific evidence.

Dutch DEGIRO tariff PDF effective 2026-01-01, stock XETRA commission
EUR 3.90, handling EUR 1.00. This does not attest the broker route,
account category, fee exemptions, or realized order costs.
"""
from decimal import Decimal
from datetime import date

SCHEDULE = {
    "effective_from": "2026-01-01",
    "market": "XETRA",
    "instrument_class": "STOCK",
    "currency": "EUR",
    "commission_eur": "3.90",
    "handling_eur": "1.00",
    "source_url": "https://www.degiro.nl/data/pdf/Tarievenoverzicht.pdf",
    "source_kind": "OFFICIAL_PUBLIC_TARIFF_DOCUMENT",
    "account_specific": False,
}

def assess_public_xetra_tariff(as_of="2026-11-13", execution_venue=None, account_tariff_evidence=None):
    out = {"status": "BLOCKED", "public_tariff": dict(SCHEDULE),
           "public_schedule_applicable_by_date": False,
           "public_per_side_eur": None, "public_round_trip_eur": None,
           "account_tariff_verified": False, "broker_route_verified": False,
           "degiro_fee_verified": False, "trade_ready": False,
           "order_placement_enabled": False, "blocks": []}
    try:
        current = date.fromisoformat(as_of)
        effective = date.fromisoformat(SCHEDULE["effective_from"])
    except (TypeError, ValueError):
        out["blocks"].append("INVALID_TARIFF_DATE")
        return out
    if current < effective:
        out["blocks"].append("TARIFF_NOT_YET_EFFECTIVE")
        return out
    out["public_schedule_applicable_by_date"] = True
    per_side = Decimal(SCHEDULE["commission_eur"]) + Decimal(SCHEDULE["handling_eur"])
    out["public_per_side_eur"] = str(per_side)
    out["public_round_trip_eur"] = str(per_side * 2)
    if execution_venue != "XETRA":
        out["blocks"].append("XETRA_EXECUTION_VENUE_NOT_ACCOUNT_ATTESTED")
    out["blocks"].extend(("ACCOUNT_TARIFF_NOT_ATTESTED",
                          "PUBLIC_TARIFF_DOES_NOT_PROVE_ACTUAL_COSTS",
                          "SPREAD_SLIPPAGE_AND_OTHER_COSTS_EXCLUDED"))
    return out
