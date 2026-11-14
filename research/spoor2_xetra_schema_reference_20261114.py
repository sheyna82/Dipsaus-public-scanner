"""Explicit, non-attesting CSV schema comparison for isolated Xetra research.

Expected headers must be supplied from independently reviewed evidence;
this module never guesses official field names or approves an instrument.
"""
import csv
import io
from research.spoor2_xetra_offline_structure_20261114 import inspect_xetra_bytes


def compare_xetra_csv_schema(data, expected_header=None, expected_sha256=None):
    result = {
        "status": "BLOCKED", "schema_matches_reviewed_reference": False,
        "source_attested": False, "instrument_segment_verified": False,
        "broker_route_verified": False, "trade_ready": False,
        "order_placement_enabled": False, "blocks": [],
    }
    structural = inspect_xetra_bytes("csv", data)
    if not structural["format_plausible"]:
        result["blocks"].extend(structural["blocks"])
        return result
    if (not isinstance(expected_header, tuple) or len(expected_header) < 2
            or any(not isinstance(x, str) or not x.strip() for x in expected_header)
            or len(set(expected_header)) != len(expected_header)):
        result["blocks"].append("REVIEWED_SCHEMA_REQUIRED")
        return result
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
        result["blocks"].append("REVIEWED_REFERENCE_HASH_REQUIRED")
        return result
    try:
        int(expected_sha256, 16)
        reader = csv.reader(io.StringIO(data.decode("utf-8-sig"), newline=""), strict=True)
        header = tuple(next(reader))
        if header != expected_header:
            result["blocks"].append("CSV_SCHEMA_MISMATCH")
            return result
        rows = 0
        for row in reader:
            if len(row) != len(header):
                result["blocks"].append("CSV_ROW_WIDTH_MISMATCH")
                return result
            rows += 1
        if not rows:
            result["blocks"].append("CSV_NO_DATA_ROWS")
            return result
    except (UnicodeError, csv.Error, ValueError, StopIteration):
        result["blocks"].append("CSV_PARSE_ERROR")
        return result
    # The reference hash is an explicit provenance marker, not an attestation
    # of this payload. It is deliberately not used to auto-approve bytes.
    result["schema_matches_reviewed_reference"] = True
    result["column_count"] = len(header)
    result["row_count"] = rows
    result["blocks"].append("SCHEMA_MATCH_DOES_NOT_ATTEST_SOURCE_OR_INSTRUMENT")
    return result
