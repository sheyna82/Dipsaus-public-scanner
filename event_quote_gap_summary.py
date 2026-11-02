"""Offline aggregate diagnostics for already observed provider quote rows.

No network, files, secrets, prices, symbols, or trading instructions in output.
"""
from collections import Counter
from event_quote_gap_diagnostics import diagnose_event_quote_row

def summarize_event_quote_gaps(rows, now, expected_currency="USD"):
    """Count fail-closed evidence gaps without exposing portfolio data."""
    if not isinstance(rows, list):
        return {"status": "INVALID_INPUT", "total": 0, "blocked": 0,
                "validated_research_only": 0, "missing_counts": {},
                "invalid_counts": {}, "execution_ready": False}
    missing, invalid = Counter(), Counter()
    blocked = validated = 0
    for row in rows:
        symbol = row.get("symbol") if isinstance(row, dict) else None
        result = diagnose_event_quote_row(row, symbol, now, expected_currency)
        if result["status"] == "VALIDATED_RESEARCH_QUOTE":
            validated += 1
        else:
            blocked += 1
        missing.update(result["missing_fields"])
        invalid.update(result["invalid_fields"])
    return {"status": "RESEARCH_ONLY", "total": len(rows),
            "blocked": blocked, "validated_research_only": validated,
            "missing_counts": dict(sorted(missing.items())),
            "invalid_counts": dict(sorted(invalid.items())),
            "execution_ready": False}
