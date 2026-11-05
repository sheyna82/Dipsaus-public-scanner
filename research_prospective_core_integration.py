"""Fail-closed research audit connecting an immutable candidate to source timing and entry.

This is an eligibility audit, not a trade signal or an outcome calculation.
"""
import hashlib
import json
from pathlib import Path

from research_capture_candidate_boundary import audit_capture_candidate_boundary
from research_next_open_reference import assess_next_open_reference


def audit_registered_candidate_entry(candidate_file, manifest, stock_bar, benchmark_bar):
    raw = Path(candidate_file).read_bytes()
    candidate = json.loads(raw)
    if not isinstance(candidate, dict) or candidate.get("trade_ready") is not False:
        raise ValueError("unsafe_candidate")
    if candidate.get("future_outcome") is not None:
        raise ValueError("candidate_contains_future_outcome")
    registered_at = candidate["registered_at_utc"]
    boundary = audit_capture_candidate_boundary(
        manifest, registered_at_utc=registered_at,
        outcome_sessions=(stock_bar["session"], benchmark_bar["session"]))
    if candidate["signal_session"] > manifest["last_common_eligible_session"]:
        raise ValueError("candidate_signal_after_eligible_source")
    if candidate["symbol"] != stock_bar.get("symbol"):
        raise ValueError("candidate_entry_symbol_mismatch")
    reference = assess_next_open_reference(
        registered_at_utc=registered_at, stock_bar=stock_bar,
        benchmark_bar=benchmark_bar)
    return {
        "status": "pending_independent_entry_source_verification",
        "candidate_sha256": hashlib.sha256(raw).hexdigest(),
        "registration_boundary_passed": boundary["capture_precedes_registration"],
        "entry_session": reference["entry_session"],
        "entry_reference_accepted": False,
        "source_authenticated_independently": False,
        "outcome_eligible": False,
        "research_only": True,
        "trade_ready": False,
    }
