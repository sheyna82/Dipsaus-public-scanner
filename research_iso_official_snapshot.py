"""Offline ISO 10383 MIC CSV inspection. Research-only; no source authentication."""
import csv
import hashlib
import io
import re
from datetime import date

REQUIRED = ("MIC", "OPERATING MIC", "OPRT/SGMT", "STATUS", "MARKET NAME-INSTITUTION DESCRIPTION")
BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False}
MIC_PATTERN = re.compile(r"[A-Z0-9]{4}")


def inspect_official_mic_csv(raw, *, expected_sha256, publication_date,
                             effective_date, as_of, requested_mics):
    blocked = {**BLOCKED, "status": "ISO_MIC_BLOCKED"}
    if not isinstance(raw, bytes) or not raw or not isinstance(expected_sha256, str):
        return {**blocked, "reason": "INVALID_INPUT"}
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        return {**blocked, "reason": "DIGEST_MISMATCH"}
    if any(type(d) is not date for d in (publication_date, effective_date, as_of)):
        return {**blocked, "reason": "INVALID_DATES"}
    if publication_date > as_of or effective_date < publication_date:
        return {**blocked, "reason": "INVALID_TIMELINE"}
    if effective_date > as_of:
        return {**blocked, "reason": "NOT_YET_EFFECTIVE"}
    if (not isinstance(requested_mics, (tuple, list)) or not requested_mics
            or any(not isinstance(m, str) or not MIC_PATTERN.fullmatch(m) for m in requested_mics)
            or len(requested_mics) != len(set(requested_mics))):
        return {**blocked, "reason": "INVALID_SELECTION"}
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
        headers = reader.fieldnames
        if not headers or len(headers) != len(set(headers)) or not set(REQUIRED).issubset(headers):
            return {**blocked, "reason": "HEADER_MISMATCH"}
        rows = {}
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                return {**blocked, "reason": "ROW_SHAPE_MISMATCH"}
            mic, op, kind, status = (row["MIC"], row["OPERATING MIC"], row["OPRT/SGMT"], row["STATUS"])
            if not MIC_PATTERN.fullmatch(mic) or not MIC_PATTERN.fullmatch(op) or kind not in ("OPRT", "SGMT") or not status:
                return {**blocked, "reason": "INVALID_REGISTER_VALUE"}
            if mic in rows:
                return {**blocked, "reason": "DUPLICATE_MIC"}
            if kind == "OPRT" and op != mic:
                return {**blocked, "reason": "OPERATING_MIC_SELF_MISMATCH"}
            rows[mic] = row
        selected = {}
        for mic in requested_mics:
            row = rows.get(mic)
            if row is None:
                return {**blocked, "reason": "MISSING_MIC", "mic": mic}
            op = row["OPERATING MIC"]
            if (row["STATUS"] != "ACTIVE" or op not in rows
                    or rows[op]["OPRT/SGMT"] != "OPRT" or rows[op]["STATUS"] != "ACTIVE"):
                return {**blocked, "reason": "INACTIVE_OR_INVALID_PARENT", "mic": mic}
            selected[mic] = {"operating_mic": op, "kind": row["OPRT/SGMT"],
                             "status": row["STATUS"],
                             "description": row["MARKET NAME-INSTITUTION DESCRIPTION"]}
        return {**BLOCKED, "status": "OFFLINE_ISO_MIC_RECORDS_CONSISTENT",
                "record_count": len(rows), "selected": selected,
                "sha256": expected_sha256, "effective_date": effective_date.isoformat()}
    except (UnicodeError, csv.Error, TypeError, ValueError):
        return {**blocked, "reason": "CSV_PARSE_ERROR"}
