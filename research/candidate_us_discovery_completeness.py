"""Read-only completeness audit for US recovery discovery reports.

Never promotes candidates, changes screening or emits notifications.
"""
import json
from pathlib import Path


def audit(report):
    if not isinstance(report, dict):
        raise ValueError("REPORT_NOT_OBJECT")
    requested = report.get("sample_symbols")
    if not isinstance(requested, list) or not all(isinstance(s, str) and s for s in requested):
        raise ValueError("INVALID_SAMPLE_SYMBOLS")
    if len(requested) != len(set(requested)):
        raise ValueError("DUPLICATE_SAMPLE_SYMBOLS")
    candidates = report.get("candidates")
    failures = report.get("failures")
    if not isinstance(candidates, list) or not isinstance(failures, dict):
        raise ValueError("INVALID_DISCOVERY_RECORDS")
    accepted = [c.get("symbol") for c in candidates if isinstance(c, dict)]
    if len(accepted) != len(candidates) or any(not isinstance(s, str) for s in accepted):
        raise ValueError("INVALID_CANDIDATES")
    if len(accepted) != len(set(accepted)):
        raise ValueError("DUPLICATE_CANDIDATES")
    if not set(accepted).issubset(requested) or not set(failures).issubset(requested):
        raise ValueError("SYMBOL_OUTSIDE_SAMPLE")
    if set(accepted) & set(failures):
        raise ValueError("CONFLICTING_OUTCOMES")
    unaccounted = sorted(set(requested) - set(accepted) - set(failures))
    screened = report.get("actual_symbols_screened")
    if type(screened) is not int or screened != len(requested) - len(failures):
        raise ValueError("SCREENED_COUNT_MISMATCH")
    return {
        "research_only": True,
        "prospective_validation_ready": False,
        "requested": len(requested),
        "candidate_count": len(accepted),
        "failure_count": len(failures),
        "noncandidate_without_feature_record": len(unaccounted),
        "noncandidate_symbols": unaccounted,
        "assessment": "INCOMPLETE_PREOUTCOME_AUDIT" if unaccounted else "SELECTION_COVERED_ONLY",
        "limitations": "No pre-outcome timestamp proof, rejected feature records, immutable retention, or source provenance."
    }


def main():
    source = Path("reports/us_recovery_pilot.json")
    result = audit(json.loads(source.read_text(encoding="utf-8")))
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
