"""Research-only unified SEC document integrity check.

A complete submission must pass both accession binding and acceptance checks.
Passing cannot establish historical public dissemination or document authenticity.
"""
from integrated_sec_accession_binding import verify_sec_accession_binding
from integrated_sec_acceptance_evidence import inspect_sec_acceptance_header


def inspect_sec_complete_submission(raw_bytes, source_url, entry_at):
    binding = verify_sec_accession_binding(raw_bytes, source_url)
    acceptance = inspect_sec_acceptance_header(raw_bytes, source_url, entry_at)
    return {
        "schema": "sec_complete_submission_internal_audit_v1",
        "status": "RESEARCH_ONLY_INTERNAL_CONSISTENCY",
        "accession": binding["accession"],
        "supplied_document_sha256": acceptance["supplied_document_sha256"],
        "acceptance_at_et": acceptance["acceptance_at_et"],
        "acceptance_precedes_entry": acceptance["acceptance_precedes_entry"],
        "internal_accession_consistency": binding["internal_accession_consistency"],
        "source_url_claimed": source_url,
        "source_bytes_authenticity_independently_proven": False,
        "public_dissemination_time_independently_proven": False,
        "historical_authenticity_independently_proven": False,
        "eligible_for_performance_claim": False,
        "trade_ready": False,
        "next_evidence_needed": [
            "independently retrieve and retain exact official SEC bytes",
            "verify externally timestamped public availability before historical entry",
            "bind historical registration and decision to immutable evidence",
        ],
    }
