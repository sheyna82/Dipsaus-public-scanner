"""Offline recovery of captured OMXH25 official PDF evidence from a retained local ZIP.

No GitHub API, network calls, live source fallback, or trading operations.
"""
import argparse
import hashlib
import json
from pathlib import Path

from research_rebuild_omxh25_archive import rebuild

EXPECTED_CAPTURE_SHA256 = "6849ebe332ce2be42e51cd9c8537b12e755e739bc4fc4a25ec5bccfcb70fc277"


def recover(retained_zip, derived_zip, receipt_json):
    retained_zip, derived_zip, receipt_json = map(Path, (retained_zip, derived_zip, receipt_json))
    if receipt_json.resolve() in (retained_zip.resolve(), derived_zip.resolve()):
        raise ValueError("RECEIPT_PATH_COLLISION")
    result = rebuild(retained_zip, derived_zip, EXPECTED_CAPTURE_SHA256)
    if result["verification"] != {
        "files": 2, "research_only": True, "status": "verified_original_bytes", "trade_ready": False
    }:
        raise ValueError("RECOVERY_VERIFICATION_INVALID")
    receipt = {
        "schema": "dipsaus-omxh25-offline-recovery-v1",
        "source": "retained_local_original_capture_zip",
        "source_sha256": EXPECTED_CAPTURE_SHA256,
        "derived_zip_sha256": result["derived_zip_sha256"],
        "verification": result["verification"],
        "benchmark_identity_verified": False,
        "independently_audited": False,
        "research_only": True,
        "trade_ready": False,
    }
    receipt_json.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("retained_capture_zip", help="Original captured artifact ZIP saved before expiry")
    parser.add_argument("derived_zip", help="Output archive containing the verified PDF bytes")
    parser.add_argument("receipt_json", help="Output research-only verification receipt")
    args = parser.parse_args()
    print(json.dumps(recover(args.retained_capture_zip, args.derived_zip, args.receipt_json), sort_keys=True))
