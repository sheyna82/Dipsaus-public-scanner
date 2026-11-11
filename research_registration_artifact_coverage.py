"""Fail-closed reconciliation of a declared, explicitly enumerated artifact run set.

This validates supplied run receipts; it cannot prove that the caller listed
all GitHub runs or that GitHub authenticated the files.
"""
from research_candidate_registration_reconciliation import reconcile_candidate_records


def audit_registration_run_coverage(receipts, expected_run_ids):
    expected = set(expected_run_ids)
    if not expected or len(expected) != len(expected_run_ids):
        raise ValueError("invalid_expected_run_set")
    seen = {}
    paths = []
    for receipt in receipts:
        run_id = receipt["run_id"]
        if run_id not in expected:
            raise ValueError("unexpected_run_id")
        if run_id in seen:
            raise ValueError("duplicate_run_receipt")
        if receipt.get("artifact_verified") is not True:
            raise ValueError("unverified_artifact_receipt")
        if receipt.get("artifact_complete") is not True:
            raise ValueError("incomplete_artifact_receipt")
        files = receipt.get("candidate_paths")
        if not isinstance(files, list):
            raise ValueError("invalid_candidate_paths")
        seen[run_id] = True
        paths.extend(files)
    missing = sorted(expected - set(seen))
    if missing:
        return {"status": "missing_declared_runs", "missing_run_ids": missing,
                "run_set_independently_complete": False, "trade_ready": False,
                "research_only": True}
    report = reconcile_candidate_records(paths)
    return {"status": "declared_run_set_reconciled",
            "expected_run_count": len(expected),
            "candidate_count": report["candidate_count"],
            "candidates": report["candidates"],
            "run_set_independently_complete": False,
            "artifact_authentication_independent": False,
            "trade_ready": False, "research_only": True}
