"""Research-only cohort eligibility: do not silently mix unverifiable datasets."""


def cohort_eligibility(records):
    """Return a conservative gate; this does not validate provenance independently."""
    if not records:
        return {"eligible": False, "reasons": ["empty_cohort"]}
    reasons = []
    symbols = set()
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            reasons.append(f"record_{i}_invalid")
            continue
        symbol = record.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip():
            reasons.append(f"record_{i}_missing_symbol")
        elif symbol in symbols:
            reasons.append(f"record_{i}_duplicate_symbol")
        else:
            symbols.add(symbol)
        for field in ("source", "adjustment_policy", "asof_cutoff"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                reasons.append(f"record_{i}_missing_{field}")
        for field in ("corporate_actions_verified", "benchmark_compatible_verified",
                      "license_reviewed", "holdout_unseen"):
            if record.get(field) is not True:
                reasons.append(f"record_{i}_{field}_unverified")
    if len(symbols) < 2:
        reasons.append("insufficient_distinct_symbols")
    sources = {r.get("source") for r in records if isinstance(r, dict)}
    policies = {r.get("adjustment_policy") for r in records if isinstance(r, dict)}
    if len(sources) != 1:
        reasons.append("mixed_sources")
    if len(policies) != 1:
        reasons.append("mixed_adjustment_policies")
    return {"eligible": not reasons, "reasons": reasons,
            "distinct_symbols": len(symbols),
            "independent_provenance_verified": False,
            "status": "ATTESTATION_ONLY"}
