"""Privacy-preserving requirements for independent DEGIRO execution verification.

This module never ingests account identifiers, names, screenshots, order
documents or transaction details. It describes required evidence fields only.
A declaration that a field exists is not proof of authenticity.
"""
REQUIRED_FIELDS = (
    "broker_issued_document",
    "document_type",
    "execution_timestamp",
    "instrument_isin",
    "executed_quantity",
    "executed_price",
    "execution_currency",
    "execution_venue_mic",
    "commission_amount",
    "handling_amount",
    "total_charged",
    "document_issue_date",
)
SENSITIVE_FIELDS_NOT_FOR_PUBLIC_REPO = (
    "account_number", "account_holder", "client_id", "order_id",
    "transaction_id", "iban", "document_image", "raw_confirmation",
)

def assess_execution_confirmation_requirements(isin, available_fields=None):
    result = {
        "status": "BLOCKED", "isin": isin,
        "required_fields": list(REQUIRED_FIELDS),
        "sensitive_fields_excluded": list(SENSITIVE_FIELDS_NOT_FOR_PUBLIC_REPO),
        "present_field_names": [],
        "missing_fields": list(REQUIRED_FIELDS),
        "metadata_complete": False,
        "document_authenticity_verified": False,
        "account_execution_route_verified": False,
        "account_tariff_verified": False,
        "broker_route_verified": False,
        "degiro_fee_verified": False,
        "trade_ready": False,
        "order_placement_enabled": False,
        "blocks": [],
    }
    if isin not in ("DE0006231004", "DE0007030009"):
        result["blocks"].append("UNKNOWN_PILOT_ISIN")
        return result
    if available_fields is None:
        names = set()
    elif isinstance(available_fields, (list, tuple, set)) and all(isinstance(k, str) for k in available_fields):
        names = set(available_fields)
    else:
        result["blocks"].append("INVALID_FIELD_NAME_INVENTORY")
        return result
    if names.intersection(SENSITIVE_FIELDS_NOT_FOR_PUBLIC_REPO):
        result["blocks"].append("SENSITIVE_FIELD_NAMES_DETECTED")
        return result
    result["present_field_names"] = sorted(names.intersection(REQUIRED_FIELDS))
    result["missing_fields"] = sorted(set(REQUIRED_FIELDS) - names)
    result["metadata_complete"] = not result["missing_fields"]
    result["blocks"].extend((
        "FIELD_NAMES_DO_NOT_AUTHENTICATE_BROKER_DOCUMENT",
        "EXECUTION_MIC_NOT_INDEPENDENTLY_ATTESTED",
        "ACCOUNT_TARIFF_NOT_INDEPENDENTLY_ATTESTED",
    ))
    return result
