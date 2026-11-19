"""Fail-closed classification of DEGIRO execution-route evidence.

A venue listed in public documents, an order-entry selection, and an actual
execution venue are distinct assertions. No self-declared evidence is trusted.
"""
STAGES = ("PUBLIC_VENUE_LISTED", "ORDER_ENTRY_SELECTION", "EXECUTION_CONFIRMATION")

def classify_degiro_route_evidence(isin, public_venue=None, order_entry=None, execution=None):
    out = {"status": "BLOCKED", "isin": isin, "public_venue": None,
           "order_entry_venue": None, "executed_venue": None,
           "evidence_stage": "UNVERIFIED", "broker_route_verified": False,
           "execution_venue_verified": False, "degiro_fee_verified": False,
           "trade_ready": False, "order_placement_enabled": False, "blocks": []}
    if isin not in ("DE0006231004", "DE0007030009"):
        out["blocks"].append("UNKNOWN_PILOT_ISIN")
        return out
    if isinstance(public_venue, dict) and public_venue.get("venue") in ("XETRA", "XETR"):
        out["public_venue"] = "XETRA"
        out["evidence_stage"] = "PUBLIC_VENUE_LISTED"
    if isinstance(order_entry, dict) and order_entry.get("isin") == isin and order_entry.get("venue") in ("XETRA", "XETR"):
        out["order_entry_venue"] = "XETRA"
        out["evidence_stage"] = "ORDER_ENTRY_SELECTION"
    if isinstance(execution, dict) and execution.get("isin") == isin and execution.get("venue") in ("XETRA", "XETR"):
        out["executed_venue"] = "XETRA"
        out["evidence_stage"] = "EXECUTION_CONFIRMATION_UNATTESTED"
    # The inputs are claims, not cryptographically verified broker records.
    # Even a plausible execution confirmation is not independent attestation.
    out["blocks"].extend(("BROKER_RECORD_AUTHENTICITY_NOT_ATTESTED",
                          "ACCOUNT_IDENTITY_NOT_ATTESTED",
                          "EXECUTION_VENUE_NOT_INDEPENDENTLY_VERIFIED",
                          "ACCOUNT_TARIFF_NOT_ATTESTED"))
    return out
