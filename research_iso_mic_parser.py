"""Offline ISO 10383 MIC CSV parser with explicitly supplied schema mapping.

The live official CSV schema MUST be inspected and attested separately.
This module does not fetch sources, infer column names or authenticate origin.
"""
import csv
import io
import re
from datetime import date

BLOCKED = {"trade_ready": False, "order_placement_enabled": False}
FIELDS = frozenset(("mic", "kind", "operating_mic", "status"))
MIC = re.compile(r"[A-Z0-9]{4}")


def parse_mic_csv(csv_text, *, columns, publication_date, effective_date,
                  as_of, expected_sha256=None):
    """Return research-only rows after strict mapping and source metadata checks.

    status values and kind values must use caller-confirmed codes.
    No assumption that publication date equals effective date.
    """
    blocked = {**BLOCKED, "status": "MIC_SOURCE_BLOCKED"}
    if not isinstance(csv_text, str) or not isinstance(columns, dict) or set(columns) != FIELDS:
        return {**blocked, "reason": "SCHEMA_NOT_DECLARED"}
    if any(not isinstance(v, str) or not v.strip() for v in columns.values()) or len(set(columns.values())) != len(columns):
        return {**blocked, "reason": "SCHEMA_INVALID"}
    if not all(isinstance(v, date) and type(v) is date for v in (publication_date, effective_date, as_of)):
        return {**blocked, "reason": "INVALID_DATES"}
    if publication_date > as_of or effective_date < publication_date:
        return {**blocked, "reason": "INVALID_PUBLICATION_TIMELINE"}
    if effective_date > as_of:
        return {**blocked, "reason": "NOT_YET_EFFECTIVE"}
    if expected_sha256 is None:
        return {**blocked, "reason": "UNATTESTED_SOURCE_DIGEST"}
    import hashlib
    if not isinstance(expected_sha256, str) or hashlib.sha256(csv_text.encode("utf-8")).hexdigest() != expected_sha256:
        return {**blocked, "reason": "SOURCE_DIGEST_MISMATCH"}
    try:
        reader = csv.DictReader(io.StringIO(csv_text, newline=""), strict=True)
        headers = reader.fieldnames
        if not headers or len(headers) != len(set(headers)) or not set(columns.values()).issubset(headers):
            return {**blocked, "reason": "HEADER_MISMATCH"}
        rows = {}
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                return {**blocked, "reason": "ROW_SHAPE_MISMATCH"}
            mic = row[columns["mic"]]
            kind = row[columns["kind"]]
            op = row[columns["operating_mic"]]
            status = row[columns["status"]]
            if not MIC.fullmatch(mic) or kind not in ("OPRT", "SGMT") or status not in ("ACTIVE", "INACTIVE"):
                return {**blocked, "reason": "UNRECOGNIZED_SOURCE_VALUE"}
            if op and not MIC.fullmatch(op):
                return {**blocked, "reason": "INVALID_OPERATING_MIC"}
            if mic in rows:
                return {**blocked, "reason": "DUPLICATE_MIC"}
            rows[mic] = {"mic": mic, "kind": kind, "operating_mic": op, "status": status}
        if not rows:
            return {**blocked, "reason": "EMPTY_REGISTER"}
        for item in rows.values():
            if item["kind"] == "SGMT":
                parent = rows.get(item["operating_mic"])
                if parent is None or parent["kind"] != "OPRT" or parent["status"] != "ACTIVE":
                    return {**blocked, "reason": "SEGMENT_PARENT_UNVERIFIED"}
        return {**BLOCKED, "status": "OFFLINE_MIC_SCHEMA_VALIDATED",
                "records": rows, "publication_date": publication_date.isoformat(),
                "effective_date": effective_date.isoformat(),
                "source_authenticity_independently_verified": False}
    except (csv.Error, UnicodeError, TypeError, ValueError):
        return {**blocked, "reason": "CSV_PARSE_ERROR"}
