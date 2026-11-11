"""Safe read-only coverage gate for an already-hydrated scanner runtime.

Invoke only in trusted main-branch runtime AFTER private hydration and after
the manual report is written. Never run this script in an untrusted PR job
with secrets. Prints counts only; never symbols or private details.
"""
import json
from pathlib import Path
from datetime import datetime, timezone
from manual_candidate_coverage_adapter import audit_manual_candidate_coverage
from private_candidate_registry import public_aggregate

def check_hydrated_runtime(config_dir="config", reports_dir="reports", *, now=None):
    config = Path(config_dir)
    reports = Path(reports_dir)
    primary = json.loads((config / "manual_recovery_triggers.json").read_text())
    supplemental_path = config / "manual_recovery_triggers_supplemental.json"
    supplemental = json.loads(supplemental_path.read_text()) if supplemental_path.exists() else {}
    report = json.loads((reports / "manual_recovery_trigger_report.json").read_text())
    result = audit_manual_candidate_coverage(
        primary, supplemental, report,
        checked_at=report.get("generated_utc"),
        now=now or datetime.now(timezone.utc))
    return public_aggregate(result)

def main():
    try:
        summary = check_hydrated_runtime()
    except Exception:
        # No tracebacks: file paths and private details must stay private.
        print("CANDIDATE_COVERAGE: unavailable")
        raise SystemExit(2)
    print("CANDIDATE_COVERAGE: " + " ".join(
        key + "=" + str(summary[key]) for key in
        ("active", "fresh_checked", "blocked", "deferred", "overdue", "reconciled")))
    if not summary["reconciled"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
