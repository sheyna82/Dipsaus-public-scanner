"""Fail-closed integration readiness for frozen research evidence.

No operational scanner imports. No trading or alert actions.
"""
import hashlib
import json
from pathlib import Path
from integrated_filter_evidence_gate import verify

MANIFEST_PATH = Path(__file__).with_name("integrated_evidence_manifest.json")
PROTOCOL_PATH = Path(__file__).with_name("prospective_filter_protocol_v1_1.json")
DIGEST_PATH = Path(__file__).with_name("prospective_filter_protocol_v1_1.sha256")

def readiness(manifest_path=MANIFEST_PATH, protocol_path=PROTOCOL_PATH, digest_path=DIGEST_PATH):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("schema") != "dipsaus.research_evidence_manifest.v1":
        raise ValueError("INVALID_MANIFEST_SCHEMA")
    if manifest.get("trade_ready") is not False or manifest.get("research_only") is not True:
        raise ValueError("UNSAFE_MANIFEST_STATUS")
    if manifest.get("protocol_embedded") is not True:
        return {"status": "BLOCKED_PROTOCOL_NOT_IMPORTED", "trade_ready": False}
    if not Path(protocol_path).is_file() or not Path(digest_path).is_file():
        return {"status": "BLOCKED_PROTOCOL_FILES_MISSING", "trade_ready": False}
    checked = verify(protocol_path, digest_path)
    if checked["sha256"] != manifest.get("protocol_sha256_canonical_json"):
        raise ValueError("MANIFEST_PROTOCOL_HASH_MISMATCH")
    return {"status": "RESEARCH_EVIDENCE_INTEGRITY_VERIFIED",
            "protocol_sha256": checked["sha256"],
            "prospective_activation": False, "trade_ready": False}

if __name__ == "__main__":
    print(json.dumps(readiness(), sort_keys=True))
