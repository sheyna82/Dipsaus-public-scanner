"""Offline CLI: verify and export a reproducible Finnhub artifact collection.

Usage: python research_export_finnhub_collection.py output.json ZIP SHA256 [ZIP SHA256 ...]
Never downloads data or writes to an existing output.
"""
import argparse
import json
import os
from pathlib import Path
from research_finnhub_artifact_collection import build_artifact_collection

def export_collection(output, artifacts):
    report = build_artifact_collection(artifacts)
    destination = Path(output)
    # Exclusive creation prevents silent overwrites of research evidence.
    payload = (json.dumps(report, sort_keys=True, indent=2) + "\n").encode("utf-8")
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("artifact", nargs="+", help="ZIP:SHA256")
    args = parser.parse_args()
    pairs = []
    for item in args.artifact:
        if ":" not in item:
            parser.error("artifact must be ZIP:SHA256")
        archive, digest = item.rsplit(":", 1)
        pairs.append((archive, digest))
    report = export_collection(args.output, pairs)
    print(json.dumps({"count": report["count"], "trade_ready": False}))
