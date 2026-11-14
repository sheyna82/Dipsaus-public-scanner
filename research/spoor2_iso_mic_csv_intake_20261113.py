"""Offline bounded ISO 10383 CSV intake. A valid CSV does not attest origin."""
import csv
import hashlib
import io

MAX_CSV_BYTES = 20_000_000
MAX_ROWS = 100_000
MAX_COLUMNS = 100


def inspect_iso_mic_csv(data):
    result = {
        "status": "BLOCKED", "sha256": None, "csv_syntax_valid": False,
        "row_count": 0, "source_attested": False, "mic_registered": False,
        "trade_ready": False, "order_placement_enabled": False, "blocks": [],
    }
    if not isinstance(data, bytes) or not data or len(data) > MAX_CSV_BYTES:
        result["blocks"].append("INVALID_OR_OVERSIZED_CSV")
        return result
    result["sha256"] = hashlib.sha256(data).hexdigest()
    try:
        text = data.decode("utf-8-sig", errors="strict")
        if "\x00" in text:
            result["blocks"].append("NUL_BYTE_IN_CSV")
            return result
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        header = next(reader, None)
        if not header or len(header) > MAX_COLUMNS or len(set(header)) != len(header):
            result["blocks"].append("INVALID_CSV_HEADER")
            return result
        if any(not col.strip() for col in header):
            result["blocks"].append("EMPTY_CSV_HEADER_FIELD")
            return result
        for row in reader:
            if len(row) != len(header):
                result["blocks"].append("INCONSISTENT_CSV_COLUMNS")
                return result
            result["row_count"] += 1
            if result["row_count"] > MAX_ROWS:
                result["blocks"].append("EXCESSIVE_CSV_ROWS")
                return result
        if result["row_count"] == 0:
            result["blocks"].append("NO_CSV_DATA_ROWS")
            return result
        result["csv_syntax_valid"] = True
    except (UnicodeError, csv.Error, ValueError):
        result["blocks"].append("INVALID_CSV_ENCODING_OR_SYNTAX")
        return result
    result["blocks"].extend((
        "OFFICIAL_CSV_ORIGIN_NOT_ATTESTED",
        "MIC_RECORDS_NOT_INDEPENDENTLY_VERIFIED",
    ))
    return result
