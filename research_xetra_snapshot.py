"""Offline Xetra instrument and market segment crosswalk, research-only.

Accepts exact CSV/ZIP bytes and externally pinned SHA-256 hashes. The
hashes identify the user-provided files, not independent publisher trust.
"""
import csv
import hashlib
import io
import zipfile

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False}
REQUIRED = {"Product Status", "Instrument Status", "Instrument", "ISIN",
            "Mnemonic", "MIC Code", "Market Segment", "Currency"}
SEGMENT_REQUIRED = {"Content type", "Identifier", "Description"}


def _rows(raw, *, skip=0):
    text = raw.decode("utf-8-sig")
    lines = text.splitlines()
    reader = csv.DictReader(io.StringIO("\n".join(lines[skip:])), delimiter=";", strict=True)
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("duplicate or missing headers")
    records = list(reader)
    if not records or any(None in r or any(v is None for v in r.values()) for r in records):
        raise ValueError("empty or malformed rows")
    return set(reader.fieldnames), records


def inspect_xetra_snapshot(instrument_bytes, zip_bytes, *, instrument_sha256,
                           zip_sha256, expected_update="18.11.2026",
                           requested_isins=()):
    blocked = {**BLOCKED, "status": "XETRA_SNAPSHOT_BLOCKED"}
    if not all(isinstance(x, bytes) and x for x in (instrument_bytes, zip_bytes)):
        return {**blocked, "reason": "MISSING_BYTES"}
    if not all(isinstance(x, str) and len(x) == 64 for x in (instrument_sha256, zip_sha256)):
        return {**blocked, "reason": "MISSING_PINNED_DIGEST"}
    if hashlib.sha256(instrument_bytes).hexdigest() != instrument_sha256 or hashlib.sha256(zip_bytes).hexdigest() != zip_sha256:
        return {**blocked, "reason": "DIGEST_MISMATCH"}
    try:
        header = instrument_bytes.decode("utf-8-sig").splitlines()
        if len(header) < 4 or header[0] != "Market:;XETR" or header[1] != "Date Last Update:;" + expected_update:
            return {**blocked, "reason": "UNEXPECTED_MARKET_OR_DATE"}
        columns, instruments = _rows(instrument_bytes, skip=2)
        if not REQUIRED.issubset(columns):
            return {**blocked, "reason": "MISSING_INSTRUMENT_COLUMNS"}
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            matches = [n for n in z.namelist() if n.endswith("_marketSegment.csv") and "/" not in n]
            if len(matches) != 1:
                return {**blocked, "reason": "MISSING_SEGMENT_TABLE"}
            segcols, segrows = _rows(z.read(matches[0]))
        if not SEGMENT_REQUIRED.issubset(segcols):
            return {**blocked, "reason": "MISSING_SEGMENT_COLUMNS"}
        segments = {}
        for row in segrows:
            if row["Content type"] not in {"Market Segment", "Market Segment Supplement"} or not row["Identifier"] or row["Identifier"] in segments:
                return {**blocked, "reason": "INVALID_SEGMENT_TABLE"}
            segments[row["Identifier"]] = row["Description"]
        if any(r["Market Segment"] not in segments for r in instruments):
            return {**blocked, "reason": "UNMAPPED_SEGMENT"}
        selected = {}
        for isin in requested_isins:
            if not isinstance(isin, str) or isin in selected:
                return {**blocked, "reason": "INVALID_ISIN_SELECTION"}
            matches = [r for r in instruments if r["ISIN"] == isin and r["MIC Code"] == "XETR"]
            if len(matches) != 1:
                return {**blocked, "reason": "MISSING_OR_DUPLICATE_INSTRUMENT", "isin": isin}
            r = matches[0]
            selected[isin] = {
                "instrument": r["Instrument"], "mnemonic": r["Mnemonic"],
                "mic": r["MIC Code"], "segment": r["Market Segment"],
                "segment_description": segments[r["Market Segment"]],
                "currency": r["Currency"], "product_status": r["Product Status"],
                "instrument_status": r["Instrument Status"],
                "research_active": r["Product Status"] == r["Instrument Status"] == "Active"}
        return {**BLOCKED, "status": "OFFLINE_XETRA_SNAPSHOT_CONSISTENT",
                "instrument_count": len(instruments), "column_count": len(columns),
                "active_instrument_count": sum(r["Product Status"] == r["Instrument Status"] == "Active" for r in instruments),
                "instruments": selected, "instrument_sha256": instrument_sha256,
                "zip_sha256": zip_sha256, "broker_route_verified": False}
    except (UnicodeError, ValueError, KeyError, csv.Error, zipfile.BadZipFile, RuntimeError, OSError):
        return {**blocked, "reason": "INVALID_SOURCE_FORMAT"}
