"""Connect verified historical registration records to offline selection comparison."""
from integrated_historical_priority_provenance import validate
from integrated_ex_ante_selection_comparison import compare_orders

def compare_verified(records, candidates, capital_eur=50000, max_positions=6):
    evidence = validate(records)
    registrations = {r["id"]: r for r in evidence["verified_registrations"]}
    if len(registrations) != len(candidates):
        raise ValueError("CANDIDATE_REGISTRATION_COVERAGE_MISMATCH")
    enriched = []
    seen = set()
    for candidate in candidates:
        ident = candidate["id"]
        if ident in seen:
            raise ValueError("DUPLICATE_CANDIDATE")
        seen.add(ident)
        if ident not in registrations:
            raise ValueError("UNREGISTERED_CANDIDATE")
        if any(k in candidate for k in ("registered_priority", "priority_source_verified",
                                         "priority_registered_before_entry", "future_return",
                                         "realized_pnl_eur")):
            raise ValueError("CANDIDATE_EVIDENCE_OVERRIDE_BLOCKED")
        enriched.append({**candidate, **registrations[ident]})
    result = compare_orders(enriched, capital_eur=capital_eur, max_positions=max_positions)
    return {"status": "RESEARCH_ONLY_VERIFIED_PRIORITY_SELECTION",
            "trade_ready": False, "historical_authenticity_independently_proven": False,
            "selection": result,
            "limitations": ["registration and source booleans require independent external evidence",
                            "source bytes and hash are not verified in this module"]}
