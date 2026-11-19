"""Verify preserved Nasdaq HistoryData evidence directly from a GitHub Actions ZIP.

Offline only; does not modify the ZIP or promote index identity/trade readiness.
"""
import json
import sys
import zipfile
from research_validate_omxh25_real_history_post import validate

MEMBER = "omxh25-history-post-raw-unverified.json"

def verify_archive(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if names.count(MEMBER) != 1:
            raise ValueError("MISSING_OR_DUPLICATE_HISTORY_RECEIPT")
        if archive.getinfo(MEMBER).file_size > 2_000_000:
            raise ValueError("OVERSIZED_HISTORY_RECEIPT")
        receipt = json.loads(archive.read(MEMBER))
    result = validate(receipt)
    if result["trade_ready"] is not False or result["benchmark_identity_verified"] is not False:
        raise ValueError("UNSAFE_GATE_PROMOTION")
    return result

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python research_verify_omxh25_real_history_artifact.py ARTIFACT.zip")
    print(json.dumps(verify_archive(sys.argv[1]), sort_keys=True))
