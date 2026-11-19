"""Offline parser for supplied Xetra CSV/ZIP bytes; never downloads or attests origin."""
import csv
import hashlib
import io
import zipfile

EXPECTED_HASHES = {
    "csv": "c3f9f7e63dd9b551338c29bda00aaade3e48ec71e035d0ce19348423402dc1ee",
    "zip": "1f740e68d775bb3ebc3f79f776860b29034d8a1e47443e56a9730679e0545a24",
}
TARGET_ISINS = ("DE0006231004", "DE0007030009")
FIELDS = ("ISIN", "Mnemonic", "Product Status", "Instrument Status",
          "MIC Code", "Trading Model Type", "Market Segment", "Reporting Market")


def inspect_supplied_xetra_artifacts(csv_bytes, zip_bytes):
    """Parse exact bytes offline; all authority/trading gates remain false."""
    hashes = {"csv": hashlib.sha256(csv_bytes).hexdigest(),
              "zip": hashlib.sha256(zip_bytes).hexdigest()}
    if hashes != EXPECTED_HASHES:
        raise ValueError("UPLOADED_ARTIFACT_HASH_MISMATCH")
    lines = io.StringIO(csv_bytes.decode("utf-8-sig"), newline="")
    metadata = [next(lines).rstrip("\r\n"), next(lines).rstrip("\r\n")]
    if metadata[0] != "Market:;XETR":
        raise ValueError("UNEXPECTED_CSV_MARKET")
    reader = csv.DictReader(lines, delimiter=";")
    if not set(FIELDS).issubset(reader.fieldnames or []):
        raise ValueError("REQUIRED_CSV_COLUMNS_MISSING")
    records = {}
    for row in reader:
        isin = row["ISIN"]
        if isin in TARGET_ISINS:
            if isin in records:
                raise ValueError("DUPLICATE_TARGET_ISIN")
            records[isin] = {key: row[key] for key in FIELDS}
    if set(records) != set(TARGET_ISINS):
        raise ValueError("TARGET_INSTRUMENT_MISSING")
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        members = [n for n in archive.namelist() if n.endswith("_marketSegment.csv")]
        if len(members) != 1:
            raise ValueError("AMBIGUOUS_MARKET_SEGMENT_TABLE")
        with archive.open(members[0]) as raw:
            segment_reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"), delimiter=";")
            segments = [row for row in segment_reader if row.get("Identifier") == "045"]
    if len(segments) != 1 or segments[0].get("Description") != "Regulierter Markt Prime Standard":
        raise ValueError("SEGMENT_045_DESCRIPTION_MISMATCH")
    for record in records.values():
        if (record["Product Status"] != "Active" or
            record["Instrument Status"] != "Active" or
            record["MIC Code"] != "XETR" or
            record["Trading Model Type"] != "Continuous" or
            record["Market Segment"] != "045" or
            record["Reporting Market"] != "XETA"):
            raise ValueError("TARGET_INSTRUMENT_FIELD_MISMATCH")
    return {
        "status": "CONTENT_VERIFIED_ORIGIN_UNATTESTED",
        "sha256": hashes,
        "csv_metadata": metadata,
        "segment_045": segments[0]["Description"],
        "instruments": records,
        "reporting_market_is_segment_mic_attested": False,
        "source_attested": False,
        "instrument_segment_verified": False,
        "segment_mic_verified": False,
        "broker_route_verified": False,
        "degiro_fee_verified": False,
        "trade_ready": False,
        "order_placement_enabled": False,
        "notify": False,
        "automatic_orders": False,
    }
