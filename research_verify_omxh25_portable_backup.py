"""Fail-closed, fully offline verifier for the portable OMXH25 source-evidence backup.

The portable backup is a container for the ORIGINAL captured GitHub artifact ZIP.
It is not an approval of Yahoo index identity or permission to trade.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from research_rebuild_omxh25_archive import rebuild
from research_recover_omxh25_offline import EXPECTED_CAPTURE_SHA256

EXPECTED_RECEIPT_SHA256 = "d41200941994ab29caeae7fa387fd41207121caaffbf9b1c8e222af5a7b5c67b"
BACKUP_MEMBERS = {"original-capture.zip", "offline-recovery-receipt.json", "manifest.json"}
MAX_MEMBER_BYTES = 600_000


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def verify_portable_backup(path):
    with zipfile.ZipFile(Path(path)) as archive:
        names = archive.namelist()
        if len(names) != 3 or set(names) != BACKUP_MEMBERS:
            raise ValueError("PORTABLE_BACKUP_MEMBERS_INVALID")
        if any(archive.getinfo(name).file_size > MAX_MEMBER_BYTES for name in names):
            raise ValueError("PORTABLE_BACKUP_MEMBER_OVERSIZED")
        manifest = json.loads(archive.read("manifest.json"))
        if (manifest.get("schema") != "dipsaus-omxh25-portable-backup-v1"
                or manifest.get("research_only") is not True
                or manifest.get("trade_ready") is not False
                or manifest.get("benchmark_identity_verified") is not False
                or manifest.get("original_artifact_id") != 13680073011
                or manifest.get("original_artifact_sha256") != EXPECTED_CAPTURE_SHA256):
            raise ValueError("PORTABLE_BACKUP_MANIFEST_INVALID")
        declared = manifest.get("files")
        if not isinstance(declared, dict) or set(declared) != BACKUP_MEMBERS - {"manifest.json"}:
            raise ValueError("PORTABLE_BACKUP_FILE_RECEIPTS_INVALID")
        original = archive.read("original-capture.zip")
        receipt_raw = archive.read("offline-recovery-receipt.json")
        if (sha256(original) != EXPECTED_CAPTURE_SHA256
                or declared["original-capture.zip"] != EXPECTED_CAPTURE_SHA256
                or sha256(receipt_raw) != declared["offline-recovery-receipt.json"]
                or sha256(receipt_raw) != EXPECTED_RECEIPT_SHA256):
            raise ValueError("PORTABLE_BACKUP_HASH_MISMATCH")
        receipt = json.loads(receipt_raw)
        if (receipt.get("source_sha256") != EXPECTED_CAPTURE_SHA256
                or receipt.get("benchmark_identity_verified") is not False
                or receipt.get("independently_audited") is not False
                or receipt.get("research_only") is not True
                or receipt.get("trade_ready") is not False
                or receipt.get("verification", {}).get("status") != "verified_original_bytes"):
            raise ValueError("PORTABLE_BACKUP_RECEIPT_INVALID")
    return {"status": "verified_portable_original_capture", "original_capture_sha256": EXPECTED_CAPTURE_SHA256,
            "research_only": True, "trade_ready": False, "benchmark_identity_verified": False}


def recover_portable_backup(backup_path, capture_path, derived_path, recovery_receipt_path):
    paths = [Path(p) for p in (backup_path, capture_path, derived_path, recovery_receipt_path)]
    if len({p.resolve() for p in paths}) != len(paths):
        raise ValueError("PORTABLE_RECOVERY_PATH_COLLISION")
    verified = verify_portable_backup(paths[0])
    with zipfile.ZipFile(paths[0]) as archive:
        original = archive.read("original-capture.zip")
    paths[1].write_bytes(original)
    from research_recover_omxh25_offline import recover
    receipt = recover(paths[1], paths[2], paths[3])
    return {"portable": verified, "recovery": receipt}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup_zip")
    parser.add_argument("--extract-original")
    parser.add_argument("--derived-zip")
    parser.add_argument("--receipt-json")
    args = parser.parse_args()
    if any((args.extract_original, args.derived_zip, args.receipt_json)):
        if not all((args.extract_original, args.derived_zip, args.receipt_json)):
            parser.error("All three recovery output paths are required together")
        result = recover_portable_backup(args.backup_zip, args.extract_original, args.derived_zip, args.receipt_json)
    else:
        result = verify_portable_backup(args.backup_zip)
    print(json.dumps(result, sort_keys=True))
