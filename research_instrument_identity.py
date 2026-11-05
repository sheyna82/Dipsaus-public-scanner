"""Research-only instrument identity contract. Never infer identity from ticker alone."""

def assess_instrument_identity(left, right):
    """Return conservative identity assessment; never authorizes trades or merging."""
    def validate(record):
        if not isinstance(record, dict):
            raise ValueError("INVALID_INSTRUMENT_RECORD")
        allowed = ("isin", "mic", "currency", "instrument_type")
        clean = {}
        for key in allowed:
            value = record.get(key)
            if value is not None:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError("INVALID_INSTRUMENT_FIELD")
                clean[key] = value.strip().upper()
        return clean

    a, b = validate(left), validate(right)
    conflicts = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    if conflicts:
        status = "CONFLICT_REQUIRES_REVIEW"
    elif all(k in a and k in b for k in ("isin", "mic", "currency", "instrument_type")):
        status = "METADATA_MATCH_UNAUTHENTICATED"
    else:
        status = "INSUFFICIENT_IDENTITY_EVIDENCE"
    return {
        "status": status,
        "conflicting_fields": conflicts,
        "metadata_matches": status == "METADATA_MATCH_UNAUTHENTICATED",
        "source_authenticated": False,
        "identity_verified": False,
        "automatic_merge_allowed": False,
        "trade_ready": False,
        "automatic_orders": False,
    }
