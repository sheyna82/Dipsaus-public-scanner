"""Offline contract for externally captured EU source bytes.

The caller supplies raw response bytes and capture metadata. This records
their hash but does not retrieve, authenticate or attest an external source.
"""
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlsplit

def audit_external_capture(record, raw_bytes, *, now_utc, max_age_seconds=900):
    base={"status":"BLOCKED","source_attested":False,"trade_ready":False,
          "order_placement_enabled":False}
    if not isinstance(record,dict) or type(raw_bytes) is not bytes or not isinstance(now_utc,datetime) or now_utc.tzinfo is None:
        return {**base,"blocks":["INVALID_CAPTURE_INPUT"]}
    if type(max_age_seconds) is not int or not 0<=max_age_seconds<=86400:
        return {**base,"blocks":["INVALID_MAX_AGE"]}
    if now_utc.utcoffset() is None:
        return {**base,"blocks":["INVALID_CAPTURE_INPUT"]}
    fields=("provider_id","source_record_id","source_url","captured_utc","content_sha256")
    if any(not isinstance(record.get(k),str) or not record[k].strip() for k in fields):
        return {**base,"blocks":["CAPTURE_METADATA_INCOMPLETE"]}
    try:
        url=record["source_url"]
        parts=urlsplit(url)
        if (parts.scheme!="https" or not parts.hostname or parts.username or parts.password
            or parts.fragment or parts.port not in (None,443) or any(c.isspace() for c in url)):
            raise ValueError
        captured=datetime.fromisoformat(record["captured_utc"].replace("Z","+00:00"))
        if captured.tzinfo is None:
            raise ValueError
        age=(now_utc.astimezone(timezone.utc)-captured.astimezone(timezone.utc)).total_seconds()
        if not 0<=age<=max_age_seconds:
            return {**base,"blocks":["CAPTURE_STALE_OR_FUTURE"]}
    except (ValueError,TypeError,AttributeError,OverflowError):
        return {**base,"blocks":["CAPTURE_URL_OR_TIME_INVALID"]}
    if not raw_bytes:
        return {**base,"blocks":["CAPTURE_EMPTY"]}
    digest=hashlib.sha256(raw_bytes).hexdigest()
    if record["content_sha256"]!=digest:
        return {**base,"blocks":["CAPTURE_CONTENT_HASH_MISMATCH"]}
    if type(record.get("content_bytes")) is not int or record["content_bytes"]!=len(raw_bytes):
        return {**base,"blocks":["CAPTURE_CONTENT_LENGTH_MISMATCH"]}
    return {**base,"status":"CAPTURE_BYTES_MATCH_UNATTESTED",
            "content_sha256":digest,"content_bytes":len(raw_bytes),
            "blocks":["EXTERNAL_RETRIEVAL_AND_PROVIDER_AUTHENTICITY_NOT_VERIFIED"],
            "scope":"caller-supplied bytes and metadata only; no trusted HTTP capture"}
