"""Read-only bounded download and inventory of official ISO 10383 MIC CSV.

The published November 2026 register may include changes effective 23 November;
do not interpret future-effective changes as active on 13 November.
"""
import csv
import hashlib
import io
import urllib.request

URL = "https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv"
MAX_BYTES = 15_000_000
TARGETS = frozenset(("XETR", "XETA", "XETB", "XETS", "XETU", "XETV", "XETW"))

def inspect_iso_mic_csv(data):
    out = {"status": "BLOCKED", "source_attested": False,
           "mic_registered": False, "segment_mic_verified": False,
           "broker_route_verified": False, "trade_ready": False,
           "order_placement_enabled": False, "headers": [],
           "target_rows": [], "blocks": []}
    if not isinstance(data, bytes) or not data or len(data) > MAX_BYTES:
        out["blocks"].append("INVALID_ISO_CSV_BYTES")
        return out
    out["sha256"] = hashlib.sha256(data).hexdigest()
    out["bytes"] = len(data)
    try:
        raw = data.decode("utf-8-sig", "strict")
        if "\x00" in raw:
            raise ValueError("NUL")
        for delimiter in (",", ";"):
            reader = csv.reader(io.StringIO(raw, newline=""), delimiter=delimiter, strict=True)
            header = next(reader, None)
            if not header or not (3 <= len(header) <= 80):
                continue
            out["delimiter"] = repr(delimiter)
            out["headers"] = header
            out["row_count"] = 0
            for row in reader:
                if len(row) != len(header):
                    out["blocks"].append("INCONSISTENT_ISO_CSV_COLUMNS")
                    return out
                out["row_count"] += 1
                if out["row_count"] > 100_000:
                    out["blocks"].append("EXCESSIVE_ISO_ROWS")
                    return out
                if any(v.strip().upper() in TARGETS for v in row):
                    out["target_rows"].append(dict(zip(header, row)))
            out["blocks"].append("ISO_REGISTER_ROWS_REQUIRE_EFFECTIVE_DATE_AND_TYPE_AUDIT")
            return out
        out["blocks"].append("UNRECOGNIZED_ISO_CSV_SCHEMA")
    except (UnicodeError, ValueError, csv.Error):
        out["blocks"].append("INVALID_ISO_CSV")
    return out

def retrieve_iso_mic_csv(opener=None):
    out = {"status": "BLOCKED", "source_attested": False, "url": URL,
           "blocks": [], "bytes": None}
    try:
        request = urllib.request.Request(URL, headers={"User-Agent": "DIPSAUS-research-evidence/1.0"})
        if opener is None:
            opener = urllib.request.urlopen
        with opener(request, timeout=15) as response:
            if response.status != 200 or response.geturl() != URL:
                out["blocks"].append("ISO_HTTP_STATUS_OR_REDIRECT")
                return out
            payload = response.read(MAX_BYTES + 1)
        if not payload or len(payload) > MAX_BYTES:
            out["blocks"].append("ISO_EMPTY_OR_OVERSIZED")
            return out
        out["bytes"] = payload
        out["blocks"].append("SOURCE_BYTES_RETRIEVED_NOT_INDEPENDENTLY_ATTESTED")
    except (OSError, ValueError, TimeoutError) as exc:
        out["blocks"].append("ISO_FETCH_FAILED_" + type(exc).__name__)
    return out
