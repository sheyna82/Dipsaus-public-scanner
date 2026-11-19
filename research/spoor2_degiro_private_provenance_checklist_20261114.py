"""Fail-closed, privacy-preserving provenance checklist for broker confirmations.

No document contents, account IDs, order IDs, hashes of sensitive documents,
or actual transactions are accepted. This is a requirements inventory, not
authentication or authorization of a brokerage record.
"""
from datetime import date

ALLOWED_DOCUMENT_TYPES = frozenset(("BROKER_EXECUTION_CONFIRMATION", "BROKER_TRANSACTION_STATEMENT"))
REQUIRED_CHECKS = frozenset((
    "broker_origin_checked_outside_public_repository",
    "document_integrity_checked_outside_public_repository",
    "account_ownership_checked_outside_public_repository",
    "execution_venue_mic_checked_against_broker_record",
    "fee_breakdown_checked_against_broker_record",
    "instrument_isin_checked_against_broker_record",
))
SENSITIVE_KEYS = frozenset((
    "account_number", "account_holder", "client_id", "order_id", "transaction_id",
    "iban", "raw_confirmation", "document_image", "document_hash",
    "executed_price", "executed_quantity", "execution_timestamp",
))

def assess_provenance_checklist(isin, document_type=None, checked_names=None, review_date=None):
    out = {
        "status": "BLOCKED", "isin": isin,
        "required_checks": sorted(REQUIRED_CHECKS),
        "declared_checks": [], "missing_checks": sorted(REQUIRED_CHECKS),
        "review_date_valid": False, "document_type_recognized": False,
        "checklist_complete": False, "independently_authenticated": False,
        "broker_route_verified": False, "degiro_fee_verified": False,
        "trade_ready": False, "order_placement_enabled": False, "blocks": [],
    }
    if isin not in ("DE0006231004", "DE0007030009"):
        out["blocks"].append("UNKNOWN_PILOT_ISIN")
        return out
    if document_type not in ALLOWED_DOCUMENT_TYPES:
        out["blocks"].append("DOCUMENT_TYPE_NOT_RECOGNIZED")
    else:
        out["document_type_recognized"] = True
    if review_date is None:
        out["blocks"].append("REVIEW_DATE_MISSING")
    else:
        try:
            date.fromisoformat(review_date)
            out["review_date_valid"] = True
        except (TypeError, ValueError):
            out["blocks"].append("INVALID_REVIEW_DATE")
    if checked_names is None:
        names = set()
    elif isinstance(checked_names, (list, tuple, set)) and all(isinstance(x, str) for x in checked_names):
        names = set(checked_names)
    else:
        out["blocks"].append("INVALID_CHECKLIST_INPUT")
        return out
    if names.intersection(SENSITIVE_KEYS) or names.difference(REQUIRED_CHECKS):
        out["blocks"].append("UNEXPECTED_OR_SENSITIVE_CHECKLIST_KEYS")
        return out
    out["declared_checks"] = sorted(names)
    out["missing_checks"] = sorted(REQUIRED_CHECKS - names)
    out["checklist_complete"] = bool(out["document_type_recognized"] and out["review_date_valid"] and not out["missing_checks"])
    out["blocks"].extend(("DECLARED_CHECKS_ARE_NOT_INDEPENDENT_ATTESTATION",
                          "PRIVATE_BROKER_EVIDENCE_NOT_AVAILABLE_TO_RESEARCH_CI"))
    return out
