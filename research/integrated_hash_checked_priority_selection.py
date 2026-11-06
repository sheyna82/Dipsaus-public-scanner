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
            "selection": selection["selection"],
            "limitations": ["source publication timestamps require independent validation",
                            "hash matching does not prove immutable historical registration"]}
