"""Read-only Xetra instrument-to-market-segment evidence; no trading authorization."""
import csv
import io
import zipfile
from research.spoor2_xetra_csv_intake_20261113 import MAX_BYTES
from research.spoor2_xetra_zip_intake_20261113 import inspect_xetra_static_zip

PILOT_ISINS = ("DE0006231004", "DE0007030009")
EXPECTED_MARKET = "XETR"
REQUIRED = ("ISIN", "MIC Code", "Market Segment", "Product Status", "Instrument", "Product ID")

def build_pilot_evidence(csv_bytes, zip_bytes):
    result = {"status": "BLOCKED", "source_attested": False,
              "instrument_segment_verified": False, "segment_mic_verified": False,
              "broker_route_verified": False, "degiro_fee_verified": False,
              "trade_ready": False, "order_placement_enabled": False,
              "records": [], "blocks": []}
    if not isinstance(csv_bytes, bytes) or not csv_bytes or len(csv_bytes) > MAX_BYTES:
        result["blocks"].append("INVALID_INSTRUMENT_CSV")
        return result
    if not inspect_xetra_static_zip(zip_bytes)["zip_container_valid"]:
        result["blocks"].append("INVALID_REFERENCE_ZIP")
        return result
    try:
        raw = csv_bytes.decode("utf-8-sig", "strict")
        if "\x00" in raw:
            raise ValueError("NUL")
        reader = csv.reader(io.StringIO(raw, newline=""), delimiter=";", strict=True)
        preamble = []
        header = None
        for row in reader:
            if len(row) == 2 and len(preamble) < 32:
                preamble.append(row)
            else:
                header = row
                break
        if not header or not set(REQUIRED).issubset(header) or len(header) != len(set(header)):
            result["blocks"].append("INVALID_INSTRUMENT_HEADER")
            return result
        if ["Market:", EXPECTED_MARKET] not in preamble:
            result["blocks"].append("UNEXPECTED_MARKET")
            return result
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
            names = [n for n in archive.namelist() if n.endswith("_marketSegment.csv")]
            if len(names) != 1:
                result["blocks"].append("INVALID_REFERENCE_MEMBER")
                return result
            reference = list(csv.DictReader(io.StringIO(archive.read(names[0]).decode("utf-8-sig")), delimiter=";", strict=True))
            segments = {}
            for entry in reference:
                if entry.get("Content type") != "Market Segment":
                    continue
                identifier, description = entry["Identifier"], entry["Description"]
                if not identifier or not description or identifier in segments:
                    result["blocks"].append("AMBIGUOUS_MARKET_SEGMENT_REFERENCE")
                    return result
                segments[identifier] = description
        found = {isin: [] for isin in PILOT_ISINS}
        for row in csv.DictReader(io.StringIO(raw, newline=""), fieldnames=header, delimiter=";", strict=True):
            # Skip metadata and header; reject malformed instrument rows.
            if None in row or row.get(None) is not None:
                result["blocks"].append("INCONSISTENT_INSTRUMENT_ROW")
                return result
            if row["ISIN"] in found:
                found[row["ISIN"]].append(row)
        for isin in PILOT_ISINS:
            matches = found[isin]
            if len(matches) != 1:
                result["blocks"].append("MISSING_OR_AMBIGUOUS_ISIN_" + isin)
                continue
            record = matches[0]
            segment = record["Market Segment"]
            if record["MIC Code"] != EXPECTED_MARKET or segment not in segments:
                result["blocks"].append("UNMATCHED_MARKET_OR_SEGMENT_" + isin)
                continue
            result["records"].append({"isin": isin, "instrument": record["Instrument"],
                "mic_code": record["MIC Code"], "market_segment_code": segment,
                "market_segment_description": segments[segment],
                "product_id": record["Product ID"], "product_status": record["Product Status"]})
        result["blocks"].extend(("ORIGINAL_SOURCE_NOT_INDEPENDENTLY_ATTESTED",
                                 "SEGMENT_MIC_NOT_VERIFIED",
                                 "DEGIRO_EXECUTION_ROUTE_NOT_VERIFIED",
                                 "DEGIRO_FEE_NOT_VERIFIED"))
    except (UnicodeError, csv.Error, ValueError, KeyError, zipfile.BadZipFile, TypeError):
        result["blocks"].append("EVIDENCE_PARSE_FAILED")
    return result
