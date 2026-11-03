"""Research-only immutable candidate ledger writer with deterministic identity.

No live scanner changes. No future outcomes are inserted or modified.
"""
import hashlib
import json
from pathlib import Path


def write_candidate_batch(batch, directory):
    root = Path(directory)
    if not root.is_dir():
        raise ValueError("ledger_directory_must_exist")
    created, duplicates, rejected = [], [], []
    # Validate every candidate before writing any file; prevent partial batches.
    for item in batch["results"]:
        if item["status"] != "candidate":
            continue
        record = item["record"]
        if (record.get("future_outcome") is not None
                or record.get("future_outcome_available") is True
                or record.get("trade_ready") is not False):
            raise ValueError("unsafe_candidate")
        if record["symbol"] != item["symbol"] or record["signal_session"] != batch["signal_session"]:
            raise ValueError("candidate_identity_mismatch")
    # Preflight deterministic identities and existing files before creating any.
    # This does not promise filesystem-level atomicity on unexpected I/O errors.
    seen = set()
    for item in batch["results"]:
        if item["status"] != "candidate":
            continue
        record = item["record"]
        identifier = f'{record["protocol_id"]}-{item["symbol"]}-{record["signal_session"]}'
        if identifier in seen:
            raise ValueError("duplicate_candidate_identity_in_batch")
        seen.add(identifier)
        filename = root / (identifier + ".json")
        payload = (json.dumps(record, sort_keys=True, indent=2) + "\n").encode("utf-8")
        if filename.exists() and filename.read_bytes() != payload:
            raise ValueError("existing_candidate_conflict")
    for item in batch["results"]:
        symbol = item["symbol"]
        if item["status"] != "candidate":
            rejected.append({"symbol": symbol, "reason": item["status"]})
            continue
        record = item["record"]
        if (record.get("future_outcome") is not None
                or record.get("future_outcome_available") is True
                or record.get("trade_ready") is not False):
            raise ValueError("unsafe_candidate")
        if record["symbol"] != symbol or record["signal_session"] != batch["signal_session"]:
            raise ValueError("candidate_identity_mismatch")
        identifier = f'{record["protocol_id"]}-{symbol}-{record["signal_session"]}'
        filename = root / (identifier + ".json")
        payload = (json.dumps(record, sort_keys=True, indent=2) + "\n").encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        try:
            with filename.open("xb") as stream:
                stream.write(payload)
            created.append({"symbol": symbol, "file": str(filename), "sha256": digest})
        except FileExistsError:
            existing = filename.read_bytes()
            if existing != payload:
                raise ValueError("existing_candidate_conflict")
            duplicates.append({"symbol": symbol, "file": str(filename), "sha256": digest})
    return {"research_only": True, "trade_ready": False,
            "created": created, "duplicates": duplicates, "rejected": rejected}


def write_audited_candidate_batch(batch, directory, source_records, *, decision_at):
    """Fail closed on source chronology before using the existing ledger writer.

    Metadata is supplied by the caller, not independently authenticated.
    This route is research-only and does not certify a real-time capture.
    """
    from research_prospective_batch import audit_prospective_batch_availability

    audit = audit_prospective_batch_availability(
        batch, source_records, decision_at=decision_at)
    if not audit["metadata_chronology_accepted"]:
        raise ValueError("prospective_source_chronology_blocked")
    result = write_candidate_batch(batch, directory)
    return {**result, "source_chronology_audit": audit,
            "independent_prospective_proof": False}
