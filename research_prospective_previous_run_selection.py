"""Research-only planning for restoring an artifact from a previous run.

Produces a fail-closed selection from supplied GitHub API metadata. This does
not fetch artifacts, make API calls, or claim durable storage.
"""
from datetime import datetime, timezone


def select_previous_artifact(artifacts, *, current_run_id, artifact_name,
                             now_iso):
    now = datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
    if now.tzinfo is None:
        raise ValueError("now_must_be_timezone_aware")
    eligible = []
    rejected = []
    for item in artifacts:
        if item.get("name") != artifact_name:
            continue
        artifact_id = item.get("id")
        source_run = (item.get("workflow_run") or {}).get("id")
        if source_run is None or source_run == current_run_id:
            rejected.append({"id": artifact_id, "reason": "not_previous_run"})
            continue
        if item.get("expired") is not False:
            rejected.append({"id": artifact_id, "reason": "expired_or_unknown"})
            continue
        expiry = item.get("expires_at")
        try:
            expiry_time = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            if expiry_time.tzinfo is None or expiry_time <= now:
                raise ValueError("invalid_expiry")
        except (AttributeError, ValueError):
            rejected.append({"id": artifact_id, "reason": "invalid_or_expired_timestamp"})
            continue
        if not isinstance(artifact_id, int) or artifact_id <= 0:
            rejected.append({"id": artifact_id, "reason": "invalid_artifact_id"})
            continue
        eligible.append(item)
    eligible.sort(key=lambda x: (x.get("created_at") or "", x["id"]), reverse=True)
    selected = eligible[0] if eligible else None
    return {"research_only": True, "trade_ready": False,
            "selection_status": "candidate_requires_download_and_checksum_verification"
                                if selected else "no_eligible_prior_artifact",
            "selected_artifact_id": selected["id"] if selected else None,
            "selected_source_run_id": selected["workflow_run"]["id"] if selected else None,
            "rejected": rejected,
            "cross_run_restoration_performed": False}
