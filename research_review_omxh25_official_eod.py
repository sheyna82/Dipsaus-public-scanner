"""Fail-closed provenance review for dated official OMXH25 EOD response bytes.

A matching price is not sufficient: issuer evidence needs preserved raw bytes,
dated field extraction, retrieval timestamp and unambiguous source provenance.
No automatic identity approval is issued by this review.
"""
import base64
import binascii
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urlsplit

ALLOWED_HOSTS = {"indexes.nasdaqomx.com", "beta.indexes.nasdaqomx.com", "www.nasdaq.com"}

def review_official_eod_evidence(record):
    if not isinstance(record, dict):
        raise ValueError("INVALID_RECORD")
    required = ("source_url", "retrieved_utc", "source_sha256", "source_raw_base64",
                "session_date", "official_index", "currency", "return_type",
                "close_field", "close_value", "extraction_method")
    if any(k not in record for k in required):
        raise ValueError("MISSING_PRIMARY_EVIDENCE")
    url = urlsplit(record["source_url"])
    if (url.scheme != "https" or url.hostname not in ALLOWED_HOSTS or url.username
            or url.password or url.fragment or url.port not in (None, 443)):
        raise ValueError("UNAPPROVED_SOURCE_URL")
    try:
        retrieved = datetime.fromisoformat(record["retrieved_utc"])
        session = datetime.strptime(record["session_date"], "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise ValueError("INVALID_DATES") from exc
    if retrieved.tzinfo is None or retrieved.utcoffset() != timezone.utc.utcoffset(retrieved):
        raise ValueError("RETRIEVAL_NOT_UTC")
    if session > retrieved.date():
        raise ValueError("FUTURE_SESSION")
    if (record["official_index"] != "OMXH25" or record["currency"] != "EUR"
            or record["return_type"] != "PRICE_RETURN"):
        raise ValueError("INDEX_VARIANT_NOT_PROVEN")
    if record["extraction_method"] != "reviewed_issuer_dated_eod_field":
        raise ValueError("UNREVIEWED_EXTRACTION")
    if not isinstance(record["close_field"], str) or not record["close_field"].strip():
        raise ValueError("MISSING_CLOSE_FIELD")
    close = record["close_value"]
    if isinstance(close, bool) or not isinstance(close, (int, float)) or not (0 < close < 1000000):
        raise ValueError("INVALID_CLOSE")
    try:
        raw = base64.b64decode(record["source_raw_base64"], validate=True)
    except (TypeError, ValueError, binascii.Error) as exc:
        raise ValueError("INVALID_RAW_BASE64") from exc
    if not raw or len(raw) > 2_000_000 or hashlib.sha256(raw).hexdigest() != record["source_sha256"]:
        raise ValueError("PRIMARY_BYTES_HASH_MISMATCH")
    # A hash alone cannot prove that bytes came from the claimed issuer host.
    return {"status": "official_bytes_self_consistent_requires_independent_source_review",
            "session_date": record["session_date"], "source_sha256": record["source_sha256"],
            "source_authenticity_independently_verified": False,
            "close_extraction_independently_verified": False,
            "benchmark_identity_verified": False, "independently_audited": False,
            "research_only": True, "trade_ready": False}

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: python research_review_omxh25_official_eod.py EVIDENCE_JSON")
    with open(sys.argv[1], encoding="utf-8") as stream:
        print(json.dumps(review_official_eod_evidence(json.load(stream)), sort_keys=True))
