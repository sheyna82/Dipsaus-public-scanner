"""Research-only selection from independently hash-checked registration source bytes."""
from integrated_historical_source_bytes_gate import verify_sources
from integrated_verified_priority_selection import compare_verified

def compare_hash_checked(registrations, source_bytes_by_hash, candidates,
                         capital_eur=50000, max_positions=6, same_day_cash_reuse=True):
    evidence = verify_sources(registrations, source_bytes_by_hash)
    selection = compare_verified(registrations, candidates, capital_eur=capital_eur,
                                 max_positions=max_positions, same_day_cash_reuse=same_day_cash_reuse)
    if len(evidence["source_bytes_verified"]) != len(candidates):
        raise ValueError("HASH_CHECKED_COVERAGE_MISMATCH")
    return {"status": "RESEARCH_ONLY_HASH_CHECKED_PRIORITY_SELECTION",
            "trade_ready": False, "historical_authenticity_independently_proven": False,
            "hash_checked_count": len(evidence["source_bytes_verified"]),
            "research_manifest": {
                "schema": "hash_checked_selection_manifest_v1",
                "input_sha256": selection["selection"]["input_sha256"],
                "fingerprint_schema": selection["selection"]["fingerprint_schema"],
                "capital_eur": selection["selection"]["capital_eur"],
                "max_positions": selection["selection"]["max_positions"],
                "cash_policy": selection["selection"]["cash_policy"],
                "source_sha256": sorted(set(row["source_sha256"] for row in registrations)),
                "registration_evidence": sorted(({
                    "id": row["id"], "source_sha256": row["source_sha256"],
                    "source_available_at_claimed": row["source_available_at"],
                    "registered_at_claimed": row["registered_at"],
                    "entry_at": row["entry_at"]} for row in registrations),
                    key=lambda row: str(row["id"])),
                "external_publication_time_independently_proven": False,
                "source_bytes_hash_checked": True,
                "historical_authenticity_independently_proven": False,
                "trade_ready": False},
            "selection": selection["selection"],
            "limitations": ["source publication timestamps require independent validation",
                            "hash matching does not prove immutable historical registration"]}
