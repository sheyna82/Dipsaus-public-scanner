"""Bounded, non-attesting structural inventory of Xetra source artifacts."""
import csv
import io
import re
import zipfile

from research.spoor2_xetra_csv_intake_20261113 import MAX_BYTES, MAX_COLUMNS
from research.spoor2_xetra_zip_intake_20261113 import inspect_xetra_static_zip

DELIMITERS = (",", ";", "\t", "|")


def inventory_csv(data):
    out = {"status": "BLOCKED", "source_attested": False,
           "instrument_segment_verified": False, "broker_route_verified": False,
           "trade_ready": False, "order_placement_enabled": False,
           "delimiter_candidates": [], "first_line_length": None, "blocks": []}
    if not isinstance(data, bytes) or not data or len(data) > MAX_BYTES:
        out["blocks"].append("INVALID_CSV_BYTES")
        return out
    try:
        raw = data.decode("utf-8-sig", "strict")
        if "\x00" in raw:
            raise ValueError("NUL")
        lines = raw.splitlines()
        out["first_line_length"] = len(lines[0]) if lines else 0
        out["line_count"] = len(lines)
        for delimiter in DELIMITERS:
            reader = csv.reader(io.StringIO(raw, newline=""), delimiter=delimiter, strict=True)
            header = next(reader, None)
            if not header or len(header) < 2 or len(header) > MAX_COLUMNS:
                continue
            counts = {}
            seen = 0
            for row in reader:
                counts[len(row)] = counts.get(len(row), 0) + 1
                seen += 1
                if seen > 200_000:
                    break
            out["delimiter_candidates"].append({
                "delimiter": repr(delimiter), "header_columns": len(header),
                "sampled_records": seen,
                "column_count_distribution": sorted(counts.items()),
                "consistent": bool(seen) and counts == {len(header): seen},
            })
    except (UnicodeError, csv.Error, ValueError):
        out["blocks"].append("INVALID_CSV_ENCODING_OR_SYNTAX")
        return out
    out["blocks"].append("STRUCTURAL_INVENTORY_ONLY")
    return out


def inventory_zip(data):
    checked = inspect_xetra_static_zip(data)
    out = {"status": "BLOCKED", "source_attested": False,
           "instrument_segment_verified": False, "broker_route_verified": False,
           "trade_ready": False, "order_placement_enabled": False,
           "members": [], "blocks": []}
    if not checked["zip_container_valid"]:
        out["blocks"].append("ZIP_FAILED_BOUNDED_VALIDATION")
        return out
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        out["members"] = [
            {"name": m.filename, "uncompressed_bytes": m.file_size,
             "compressed_bytes": m.compress_size}
            for m in archive.infolist()
        ]
    out["blocks"].append("STRUCTURAL_INVENTORY_ONLY")
    return out


def inspect_xetra_csv_schema(data):
    """Read bounded header/metadata and ISIN column positions, without asserting provenance."""
    out = {"status": "BLOCKED", "source_attested": False,
           "instrument_segment_verified": False, "broker_route_verified": False,
           "trade_ready": False, "order_placement_enabled": False,
           "metadata": None, "header_count": None, "header_fields": [],
           "isin_columns": [], "pilot_matches": [], "blocks": []}
    if not isinstance(data, bytes) or not data or len(data) > MAX_BYTES:
        out["blocks"].append("INVALID_CSV_BYTES")
        return out
    try:
        raw = data.decode("utf-8-sig", "strict")
        if "\x00" in raw:
            raise ValueError("NUL")
        reader = csv.reader(io.StringIO(raw, newline=""), delimiter=";", strict=True)
        metadata = []
        header = None
        for candidate in reader:
            if len(candidate) == 2 and header is None and len(metadata) < 32:
                metadata.append(candidate)
                continue
            if len(candidate) >= 3 and len(candidate) <= MAX_COLUMNS:
                header = candidate
            break
        if not metadata or not header:
            out["blocks"].append("UNEXPECTED_XETRA_SCHEMA")
            return out
        if any(not h.strip() for h in header) or len(set(header)) != len(header):
            out["blocks"].append("INVALID_XETRA_COLUMN_NAMES")
            return out
        out["metadata"] = metadata
        out["header_count"] = len(header)
        out["header_fields"] = header
        out["isin_columns"] = [i for i, name in enumerate(header) if "isin" in name.casefold()]
        targets = {"DE0006231004", "DE0007030009"}
        for row_number, row in enumerate(reader, start=3):
            if row_number > 200_003:
                out["blocks"].append("EXCESSIVE_XETRA_ROWS")
                return out
            if len(row) != len(header):
                out["blocks"].append("INCONSISTENT_XETRA_ROWS")
                return out
            for i, value in enumerate(row):
                if value.strip() in targets:
                    out["pilot_matches"].append({"row": row_number, "matched_column": header[i],
                        "isin": value.strip(), "fields": {
                            header[j]: row[j] for j, name in enumerate(header)
                            if any(token in name.casefold() for token in ("isin", "mic", "segment", "market", "product"))
                        }})
        out["blocks"].append("SCHEMA_AND_PILOT_INVENTORY_ONLY")
    except (UnicodeError, csv.Error, ValueError):
        out["blocks"].append("INVALID_CSV_ENCODING_OR_SYNTAX")
    return out
