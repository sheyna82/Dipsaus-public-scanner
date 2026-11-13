"""Bounded, non-attesting structural inventory of Xetra source artifacts."""
import csv
import io
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
