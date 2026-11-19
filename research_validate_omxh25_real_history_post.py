"""Fail-closed review of a preserved REAL Nasdaq OMXH25 HistoryData response.

No network requests. Validates raw-byte integrity and the observed issuer JSON
schema, not independently proven market methodology or trading eligibility.
"""
import base64
import hashlib
import json
import math
from datetime import date

SOURCE = "https://beta.indexes.nasdaqomx.com/Index/HistoryData"
ISIN = "FI0008900212"

def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result

def _reject_constant(value):
    raise ValueError("NONFINITE_JSON_CONSTANT")

def validate(receipt):
    if not isinstance(receipt, dict) or receipt.get("schema") != "dipsaus_omxh25_history_post_candidate_v1":
        raise ValueError("INVALID_CAPTURE_SCHEMA")
    if receipt.get("source_url") != SOURCE or receipt.get("http_method") != "POST" or type(receipt.get("http_status")) is not int or receipt["http_status"] != 200:
        raise ValueError("INVALID_SOURCE")
    if not receipt.get("content_type", "").lower().startswith("application/json"):
        raise ValueError("INVALID_CONTENT_TYPE")
    fields = receipt.get("request_fields")
    if not isinstance(fields, dict) or set(fields) != {"id", "startDate", "endDate", "timeOfDay"} or fields["id"] != "OMXH25" or fields["timeOfDay"] != "EOD":
        raise ValueError("INVALID_REQUEST")
    if not all(isinstance(fields[k], str) and len(fields[k]) == 23 and fields[k][10] == "T" and fields[k][19] == "." for k in ("startDate", "endDate")):
        raise ValueError("INVALID_DATE_FORMAT")
    try:
        start = date.fromisoformat(fields["startDate"][:10])
        end = date.fromisoformat(fields["endDate"][:10])
    except ValueError as exc:
        raise ValueError("INVALID_DATE") from exc
    if start > end:
        raise ValueError("INVALID_DATE_RANGE")
    encoded = receipt.get("source_raw_base64")
    if not isinstance(encoded, str):
        raise ValueError("MISSING_RAW_BYTES")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError("INVALID_BASE64") from exc
    if not raw or hashlib.sha256(raw).hexdigest() != receipt.get("source_sha256"):
        raise ValueError("RAW_HASH_MISMATCH")
    try:
        body = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("INVALID_JSON") from exc
    if not isinstance(body, dict) or set(body) != {"sEcho", "iTotalRecords", "iTotalDisplayRecords", "aaData"}:
        raise ValueError("UNEXPECTED_RESPONSE_SCHEMA")
    rows = body["aaData"]
    if not isinstance(rows, list) or not rows or type(body["iTotalRecords"]) is not int or type(body["iTotalDisplayRecords"]) is not int or body["iTotalRecords"] != len(rows) or body["iTotalDisplayRecords"] != len(rows):
        raise ValueError("INVALID_RECORD_COUNT")
    seen = set()
    checked = []
    for row in rows:
        if not isinstance(row, dict) or row.get("Currency") != "EUR" or row.get("IndexIsin") != ISIN or row.get("Close") is not None:
            raise ValueError("INDEX_IDENTITY_OR_SCHEMA_MISMATCH")
        trade_date = row.get("TradeDate")
        timestamp = row.get("TimeStamp")
        if not isinstance(trade_date, str) or not isinstance(timestamp, str) or trade_date != timestamp or len(trade_date) != 19 or not trade_date.endswith("T00:00:00"):
            raise ValueError("INVALID_SESSION_TIMESTAMP")
        try:
            day = date.fromisoformat(trade_date[:10])
        except ValueError as exc:
            raise ValueError("INVALID_TRADE_DATE") from exc
        if day < start or day > end or day in seen:
            raise ValueError("DUPLICATE_OR_OUT_OF_RANGE_SESSION")
        seen.add(day)
        value = row.get("Value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError("INVALID_INDEX_VALUE")
        checked.append({"date": day.isoformat(), "value": value})
    return {"status": "issuer_history_raw_and_schema_verified_research_only",
            "source_sha256": receipt["source_sha256"], "record_count": len(checked),
            "records": sorted(checked, key=lambda x: x["date"]),
            "official_eod_raw_bytes_verified": True,
            "benchmark_identity_verified": False,
            "independently_audited": False,
            "research_only": True, "trade_ready": False}

if __name__ == "__main__":
    import sys
    with open(sys.argv[1], encoding="utf-8") as stream:
        print(json.dumps(validate(json.load(stream)), sort_keys=True))
