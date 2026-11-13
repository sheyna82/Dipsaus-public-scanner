"""Read-only, fail-closed Xetra market-segment reference inventory."""
import csv
import io
import zipfile

from research.spoor2_xetra_zip_intake_20261113 import inspect_xetra_static_zip

def inspect_market_segment_reference(data):
    out = {"status":"BLOCKED","source_attested":False,"segment_mic_verified":False,
           "broker_route_verified":False,"degiro_fee_verified":False,
           "trade_ready":False,"order_placement_enabled":False,
           "headers":[],"rows_045":[],"blocks":[]}
    if not inspect_xetra_static_zip(data)["zip_container_valid"]:
        out["blocks"].append("ZIP_INVALID")
        return out
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            candidates=[x for x in archive.namelist() if x.endswith("_marketSegment.csv")]
            if len(candidates)!=1:
                out["blocks"].append("MARKET_SEGMENT_FILE_NOT_UNIQUE")
                return out
            raw=archive.read(candidates[0]).decode("utf-8-sig",errors="strict")
            if "\x00" in raw:
                out["blocks"].append("INVALID_MARKET_SEGMENT_ENCODING")
                return out
            for delimiter in (";",",","\t"):
                records=list(csv.reader(io.StringIO(raw,newline=""),delimiter=delimiter,strict=True))
                if not records or len(records[0])<2:
                    continue
                out["delimiter"]=repr(delimiter)
                out["headers"]=records[0]
                out["row_count"]=len(records)-1
                out["rows_045"]=[{"row":i+2,"values":row} for i,row in enumerate(records[1:]) if "045" in row]
                out["consistent"]=all(len(row)==len(records[0]) for row in records[1:])
                out["blocks"].append("REFERENCE_INVENTORY_ONLY")
                return out
            out["blocks"].append("UNKNOWN_MARKET_SEGMENT_SCHEMA")
    except (UnicodeError,ValueError,zipfile.BadZipFile,csv.Error,KeyError):
        out["blocks"].append("MARKET_SEGMENT_PARSE_FAILED")
    return out
