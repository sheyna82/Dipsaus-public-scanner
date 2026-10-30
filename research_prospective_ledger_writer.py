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
    for item in batch["results"]:
        symbol = item["symbol"]
        if item["status"] != "candidate":
            rejected.append({"symbol": symbol, "reason": item["status"]})
            continue
        record = item["record"]
        if record.get("future_outcome") is not None or record.get("trade_ready") is not False:
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
