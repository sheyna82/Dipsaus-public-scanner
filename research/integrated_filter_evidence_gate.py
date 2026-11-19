"""Research-only integrity gate for the frozen DIPSAUS filter protocol.

No market orders, scanner imports, notifications, or live configuration.
Usage: python research/integrated_filter_evidence_gate.py PROTOCOL SHA256_FILE
"""
import hashlib
import json
import pathlib
import sys

EXPECTED_SCHEMA = "dipsaus.prospective_filter_evaluation.v1.1"

def verify(protocol_path, digest_path):
    protocol_path = pathlib.Path(protocol_path)
    digest_path = pathlib.Path(digest_path)
    raw = protocol_path.read_bytes()
    data = json.loads(raw)
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    recorded = digest_path.read_text(encoding="utf-8").strip().split()[0].lower()
    if digest != recorded:
        raise ValueError("PROTOCOL_SHA256_MISMATCH")
    data = json.loads(raw)
    if data.get("schema") != EXPECTED_SCHEMA:
        raise ValueError("PROTOCOL_SCHEMA_MISMATCH")
    if data.get("status") != "RESEARCH_ONLY_VERIFIED_NOT_ACTIVATED":
        raise ValueError("UNEXPECTED_PROTOCOL_STATUS")
    if data.get("prospective_earliest_signal_date_utc") != "2026-11-07":
        raise ValueError("PROSPECTIVE_BOUNDARY_MISMATCH")
    return {"status": "RESEARCH_ONLY_INTEGRITY_VERIFIED",
            "sha256": digest, "prospective_activation": False,
            "trade_ready": False}

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: integrated_filter_evidence_gate.py PROTOCOL SHA256_FILE")
    try:
        print(json.dumps(verify(sys.argv[1], sys.argv[2]), sort_keys=True))
    except (OSError, ValueError, KeyError, IndexError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc), "trade_ready": False}))
        raise SystemExit(1)
