"""Audit operating and segment MIC relationships in the official ISO register.

Research-only: a segment classification does not establish the execution
venue of an individual security or a DEGIRO account.
"""
from datetime import date

def audit_xetra_iso_relationship(inventory, as_of="2026-11-13"):
    out = {"status": "BLOCKED", "iso_operating_mic_found": False,
           "iso_regulated_segment_candidate": None,
           "instrument_segment_verified": False, "segment_mic_verified": False,
           "broker_route_verified": False, "degiro_fee_verified": False,
           "trade_ready": False, "order_placement_enabled": False, "blocks": []}
    try:
        cutoff = date.fromisoformat(as_of)
    except (ValueError, TypeError):
        out["blocks"].append("INVALID_AS_OF_DATE")
        return out
    if not isinstance(inventory, dict) or not isinstance(inventory.get("target_rows"), list):
        out["blocks"].append("INVALID_ISO_INVENTORY")
        return out
    rows = inventory["target_rows"]
    if any(not isinstance(r, dict) for r in rows):
        out["blocks"].append("INVALID_ISO_ROW")
        return out
    def valid(r, mic, kind):
        if (r.get("MIC") != mic or r.get("OPERATING MIC") != "XETR"
                or r.get("OPRT/SGMT") != kind or r.get("STATUS") != "ACTIVE"
                or r.get("ISO COUNTRY CODE (ISO 3166)") != "DE"):
            return False
        try:
            created = date.fromisoformat(r["CREATION DATE"][:4] + "-" + r["CREATION DATE"][4:6] + "-" + r["CREATION DATE"][6:8])
            expired = r.get("EXPIRY DATE", "")
            return created <= cutoff and not expired
        except (ValueError, TypeError, KeyError):
            return False
    operating = [r for r in rows if valid(r, "XETR", "OPRT")]
    regulated = [r for r in rows if valid(r, "XETA", "SGMT")
                 and r.get("MARKET CATEGORY CODE") == "RMKT"
                 and "REGULIERTER MARKT" in r.get("MARKET NAME-INSTITUTION DESCRIPTION", "").upper()]
    if len(operating) == 1:
        out["iso_operating_mic_found"] = True
    else:
        out["blocks"].append("XETR_OPERATING_MIC_NOT_UNIQUELY_CONFIRMED")
    if len(regulated) == 1:
        out["iso_regulated_segment_candidate"] = "XETA"
    else:
        out["blocks"].append("XETA_REGULATED_SEGMENT_NOT_UNIQUELY_CONFIRMED")
    out["blocks"] += ["XETRA_MARKET_SEGMENT_045_TO_ISO_MIC_NOT_ATTESTED",
                      "DEGIRO_ACCOUNT_ROUTE_NOT_ATTESTED",
                      "DEGIRO_ACCOUNT_TARIFF_NOT_ATTESTED"]
    return out
