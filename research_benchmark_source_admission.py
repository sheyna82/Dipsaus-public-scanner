"""Fail-closed research benchmark source admission; no network or trading actions."""

REQUIRED = ("official_identity_verified", "provider_series_mapping_verified",
            "historical_values_verified", "data_use_rights_verified")

def assess_source(record):
    """Return auditable eligibility without inferring permission from data agreement."""
    if not isinstance(record, dict):
        raise ValueError("INVALID_SOURCE_RECORD")
    if not isinstance(record.get("source_id"), str) or not record["source_id"].strip():
        raise ValueError("INVALID_SOURCE_ID")
    if any(key not in record or type(record[key]) is not bool for key in REQUIRED):
        raise ValueError("MISSING_OR_INVALID_SOURCE_GATE")
    if record.get("research_only") is not True or record.get("trade_ready") is not False:
        raise ValueError("UNSAFE_SOURCE_STATE")
    missing = [key for key in REQUIRED if not record[key]]
    return {"source_id": record["source_id"],
            "research_calculation_eligible": not missing,
            "unmet_requirements": missing,
            "research_only": True, "trade_ready": False}

def omxh25_yahoo_candidate():
    """Known evidence only; never assume a licence or venue mapping."""
    return assess_source({
        "source_id": "yahoo:^OMXH25",
        "official_identity_verified": True,  # Nasdaq's OMXH25 definition/ISIN only
        "provider_series_mapping_verified": False,  # Yahoo STO unresolved
        "historical_values_verified": False,  # three dates != long-run history
        "data_use_rights_verified": False,  # systematic reuse not cleared
        "research_only": True, "trade_ready": False,
    })
