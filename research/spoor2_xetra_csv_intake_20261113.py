"""Bounded offline Xetra CSV inspection; syntax is not exchange provenance."""
import csv
import hashlib
import io

MAX_BYTES = 30_000_000
MAX_ROWS = 200_000
MAX_COLUMNS = 200


def inspect_xetra_csv(data):
    out = dict(status="BLOCKED", sha256=None, csv_syntax_valid=False,
               row_count=0, source_attested=False,
               instrument_segment_verified=False, broker_route_verified=False,
               trade_ready=False, order_placement_enabled=False, blocks=[])
    if not isinstance(data, bytes) or not data or len(data) > MAX_BYTES:
        out["blocks"].append("INVALID_OR_OVERSIZED_XETRA_CSV")
        return out
    out["sha256"] = hashlib.sha256(data).hexdigest()
    try:
        raw = data.decode("utf-8-sig", errors="strict")
        if "\x00" in raw:
            out["blocks"].append("NUL_BYTE_IN_XETRA_CSV")
            return out
        reader = csv.reader(io.StringIO(raw, newline=""), strict=True)
        header = next(reader, None)
        if not header or len(header) > MAX_COLUMNS or len(set(header)) != len(header) or any(not x.strip() for x in header):
            out["blocks"].append("INVALID_XETRA_CSV_HEADER")
            return out
        for row in reader:
            if len(row) != len(header):
                out["blocks"].append("INCONSISTENT_XETRA_CSV_COLUMNS")
                return out
            out["row_count"] += 1
            if out["row_count"] > MAX_ROWS:
                out["blocks"].append("EXCESSIVE_XETRA_CSV_ROWS")
                return out
        if not out["row_count"]:
            out["blocks"].append("EMPTY_XETRA_CSV")
            return out
        out["csv_syntax_valid"] = True
    except (UnicodeError, csv.Error, ValueError):
        out["blocks"].append("INVALID_XETRA_CSV_ENCODING_OR_SYNTAX")
        return out
    out["blocks"].extend(("ORIGINAL_XETRA_SOURCE_NOT_ATTESTED",
                          "INSTRUMENT_SEGMENT_NOT_VERIFIED",
                          "DEGIRO_EXECUTION_ROUTE_NOT_VERIFIED"))
    return out
