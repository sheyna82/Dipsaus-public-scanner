"""Offline three-session Nasdaq/Yahoo corroboration; never promotes index identity."""
import base64
import hashlib
import json
import math
import zipfile
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from research_validate_omxh25_real_history_post import validate

def verify_yahoo_raw_bars(raw, entry):
    """Reconstruct captured Yahoo bars from immutable raw Chart JSON."""
    try:
        doc = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
        result = doc["chart"]["result"]
        if not isinstance(result, list) or len(result) != 1:
            raise ValueError("invalid result count")
        data = result[0]
        metadata = data["meta"]
        stored_meta = entry["provider_metadata"]
        if any(metadata.get(key) != stored_meta.get(key) for key in
               ("symbol", "currency", "instrumentType", "exchangeName", "timezone", "gmtoffset", "shortName", "longName")):
            raise ValueError("metadata mismatch")
        if metadata.get("symbol") != "^OMXH25":
            raise ValueError("raw symbol mismatch")
        timestamps = data["timestamp"]
        quotes = data["indicators"]["quote"]
        if not isinstance(quotes, list) or len(quotes) != 1:
            raise ValueError("invalid quote count")
        closes = quotes[0]["close"]
        if not isinstance(timestamps, list) or not isinstance(closes, list) or len(timestamps) != len(closes):
            raise ValueError("length mismatch")
        reconstructed = []
        for timestamp, close in zip(timestamps, closes):
            if type(timestamp) is not int:
                raise ValueError("invalid timestamp")
            if close is None or isinstance(close, bool) or not isinstance(close, (int, float)) or not math.isfinite(close) or close <= 0:
                continue  # Capture module explicitly skips unusable closes.
            reconstructed.append({"t": timestamp, "close": close})
        if reconstructed != entry["bars"]:
            raise ValueError("derived bars mismatch")
        if entry.get("count") != len(reconstructed):
            raise ValueError("derived count mismatch")
    except (KeyError, TypeError, IndexError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("YAHOO_RAW_DERIVATION_MISMATCH") from exc

def compare_archive(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        files = ("omxh25-history-post-raw-unverified.json", "europe-benchmarks.json")
        if any(names.count(name) != 1 or archive.getinfo(name).file_size > 2_000_000 for name in files):
            raise ValueError("MISSING_DUPLICATE_OR_OVERSIZED_SOURCE")
        issuer_receipt = json.loads(archive.read(files[0]))
        yahoo = json.loads(archive.read(files[1]))
    issuer = validate(issuer_receipt)
    if any(yahoo.get(k) is not v for k, v in (("research_only", True), ("trade_ready", False), ("benchmark_identity_verified", False))):
        raise ValueError("UNSAFE_YAHOO_GATES")
    entry = yahoo.get("series", {}).get("OMXH25")
    if not isinstance(entry, dict) or entry.get("provider_symbol") != "^OMXH25":
        raise ValueError("INVALID_YAHOO_SYMBOL")
    meta = entry.get("provider_metadata", {})
    if meta.get("currency") != "EUR" or meta.get("instrumentType") != "INDEX":
        raise ValueError("INVALID_YAHOO_METADATA")
    encoded = entry.get("source_raw_base64")
    if not isinstance(encoded, str):
        raise ValueError("MISSING_YAHOO_RAW")
    raw = base64.b64decode(encoded, validate=True)
    if not raw or hashlib.sha256(raw).hexdigest() != entry.get("source_sha256"):
        raise ValueError("YAHOO_RAW_HASH_MISMATCH")
    verify_yahoo_raw_bars(raw, entry)
    bars = {}
    for bar in entry.get("bars", []):
        timestamp, close = bar.get("t"), bar.get("close")
        if type(timestamp) is not int or isinstance(close, bool) or not isinstance(close, (int, float)) or not math.isfinite(close) or close <= 0:
            raise ValueError("INVALID_YAHOO_BAR")
        day = datetime.fromtimestamp(timestamp, timezone.utc).astimezone(ZoneInfo("Europe/Helsinki")).date().isoformat()
        if day in bars:
            raise ValueError("DUPLICATE_YAHOO_SESSION")
        bars[day] = close
    if not issuer["records"]:
        raise ValueError("EMPTY_ISSUER_HISTORY")
    matches = []
    for row in issuer["records"]:
        day, official = row["date"], row["value"]
        if day not in bars:
            raise ValueError("MISSING_YAHOO_SESSION")
        yahoo_close = bars[day]
        if round(official, 2) != round(yahoo_close, 2):
            raise ValueError("CLOSE_MISMATCH")
        matches.append({"date": day, "nasdaq_value": official, "yahoo_close": yahoo_close,
                        "difference": round(yahoo_close - official, 8), "two_decimal_match": True})
    return {"status": "three_session_value_match_unverified_identity",
            "issuer_source_sha256": issuer["source_sha256"], "matched_sessions": len(matches),
            "comparisons": matches, "yahoo_exchange_name": meta.get("exchangeName"),
            "venue_mapping_explained": False, "benchmark_identity_verified": False,
            "independently_audited": False, "research_only": True, "trade_ready": False}

if __name__ == "__main__":
    import sys
    print(json.dumps(compare_archive(sys.argv[1]), sort_keys=True))
