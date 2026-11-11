"""Offline, reproducible Spoor 2 schema audit over supplied runtime snapshots.

Usage:
  python -m research.spoor2_snapshot_audit_20261111 US_STATE.json EU_STATE.json

The caller supplies read-only files; this module never downloads private data.
The report includes SHA256 of the exact source bytes. Structural parsing
does not imply current quotes, independent technical validation, or trade
readiness.
"""
import hashlib
import json
import sys
from pathlib import Path
from research.spoor2_runtime_schema_audit_20261111 import inspect_report


def audit_snapshots(us_bytes, eu_bytes):
    result = {"status": "SCHEMA_AUDIT_ONLY", "trade_ready": False,
              "order_placement_enabled": False, "sources": {}}
    for market, payload in (("US", us_bytes), ("EU", eu_bytes)):
        source = {"sha256": hashlib.sha256(payload).hexdigest(),
                  "size_bytes": len(payload)}
        try:
            data = json.loads(payload)
        except (UnicodeDecodeError, ValueError, TypeError):
            source["status"] = "INVALID_JSON"
            source["reports"] = []
            result["sources"][market] = source
            continue
        if not isinstance(data, dict):
            source["status"] = "INVALID_ROOT"
            source["reports"] = []
        elif market == "US":
            reports = data.get("latest_us_reports")
            if not isinstance(reports, dict):
                source["status"] = "INVALID_REPORT_CONTAINER"
                source["reports"] = []
            else:
                source["status"] = "SCHEMA_AUDIT_ONLY"
                source["reports"] = [
                    {"name": name, **inspect_report(report, "US")}
                    for name, report in sorted(reports.items())
                ]
        else:
            source["status"] = "SCHEMA_AUDIT_ONLY"
            source["reports"] = [
                {"name": "latest_eu_report",
                 **inspect_report(data.get("latest_eu_report"), "EU")}
            ]
        result["sources"][market] = source
    return result


def main(argv):
    if len(argv) != 3:
        raise SystemExit("Usage: python -m research.spoor2_snapshot_audit_20261111 US_STATE.json EU_STATE.json")
    report = audit_snapshots(Path(argv[1]).read_bytes(), Path(argv[2]).read_bytes())
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if all(source["status"] == "SCHEMA_AUDIT_ONLY" and
                    all(row["status"] == "SCHEMA_REVIEW_ONLY"
                        for row in source["reports"])
                    for source in report["sources"].values()) else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
