"""Research-only audit of the Xetra Reporting Market field.

Deutsche Boerse T7 reference data defines Reporting Market as the ISO 10383
MIC required for regulatory reporting. It is NOT evidence of broker execution.
No trading authorization can be issued by this module.
"""
import csv
import io

TARGET_ISINS = ("DE0006231004", "DE0007030009")

def audit_reporting_market(csv_bytes, iso_relationship):
    out = {"status": "BLOCKED", "records": [], "reporting_market_reference_matched": False,
           "instrument_segment_verified": False, "segment_mic_verified": False,
           "broker_route_verified": False, "degiro_fee_verified": False,
           "source_attested": False, "trade_ready": False,
           "order_placement_enabled": False, "blocks": []}
    if not isinstance(csv_bytes, bytes) or not csv_bytes or len(csv_bytes) > 12000000:
        out["blocks"].append("INVALID_XETRA_BYTES")
        return out
    if not isinstance(iso_relationship, dict) or iso_relationship.get("iso_regulated_segment_candidate") != "XETA" or iso_relationship.get("iso_operating_mic_found") is not True:
        out["blocks"].append("ISO_RELATIONSHIP_NOT_CONFIRMED")
        return out
    try:
        text = csv_bytes.decode("utf-8-sig", "strict")
        if "\x00" in text:
            raise ValueError("NUL")
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=";", strict=True)
        if next(reader) != ["Market:", "XETR"]:
            raise ValueError("MARKET")
        metadata = next(reader)
        if len(metadata) != 2 or metadata[0] != "Date Last Update:":
            raise ValueError("DATE")
        header = next(reader)
        required = {"ISIN", "MIC Code", "Market Segment", "Reporting Market"}
        if not required.issubset(header) or len(header) != len(set(header)):
            raise ValueError("HEADER")
        matches = {isin: [] for isin in TARGET_ISINS}
        for values in reader:
            if len(values) != len(header):
                raise ValueError("ROW_WIDTH")
            row = dict(zip(header, values))
            if row["ISIN"] in matches:
                matches[row["ISIN"]].append(row)
        if any(len(matches[isin]) != 1 for isin in TARGET_ISINS):
            raise ValueError("MISSING_OR_DUPLICATE_ISIN")
        for isin in TARGET_ISINS:
            row = matches[isin][0]
            out["records"].append({"isin": isin, "market_mic": row["MIC Code"],
                "market_segment": row["Market Segment"], "reporting_market": row["Reporting Market"]})
        out["reporting_market_reference_matched"] = all(
            row["market_mic"] == "XETR" and row["market_segment"] == "045"
            and row["reporting_market"] == "XETA" for row in out["records"])
        if not out["reporting_market_reference_matched"]:
            out["blocks"].append("INSTRUMENT_REPORTING_MARKET_MISMATCH")
    except (UnicodeError, csv.Error, ValueError, StopIteration, TypeError):
        out["records"] = []
        out["blocks"].append("XETRA_REPORTING_MARKET_PARSE_FAILED")
    out["blocks"].extend(("REPORTING_MIC_IS_NOT_EXECUTION_MIC",
                          "BROKER_ROUTE_NOT_VERIFIED", "TRADE_NOT_AUTHORIZED"))
    return out
