"""Offline verification of an archived Finnhub research observation.

This verifies internal integrity and conservative metadata only. It does NOT
authenticate Finnhub, prove a trading signal, or establish quote accuracy.
No network access, credentials, orders or notifications are used.
"""
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

FIELDS = {"c", "d", "dp", "h", "l", "o", "pc", "t"}
SCHEMA = "dipsaus_research_source_observation_v1"


def verify(path):
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(record, dict) or record.get("schema") != SCHEMA:
        raise ValueError("invalid_observation_schema")
    if record.get("provider") != "Finnhub" or record.get("endpoint") != "/api/v1/quote":
        raise ValueError("unexpected_source")
    if record.get("symbol_requested") not in {"AMD", "COHU", "CSGP", "AAPL"}:
        raise ValueError("unexpected_symbol")
    if any(record.get(k) is not False for k in (
        "external_receipt_verified", "provider_identity_independently_verified",
        "prospective_signal_proven", "trade_ready")) or record.get("research_only") is not True:
        raise ValueError("unsafe_evidence_claim")
    try:
        raw = bytes.fromhex(record["raw_response_hex"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid_raw_response") from exc
    if not raw or len(raw) > 4096 or type(record.get("source_bytes")) is not int or len(raw) != record["source_bytes"]:
        raise ValueError("invalid_response_size")
    if hashlib.sha256(raw).hexdigest() != record.get("source_sha256"):
        raise ValueError("source_hash_mismatch")
    try:
        body = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("invalid_quote_json") from exc
    if not isinstance(body, dict) or set(body) - FIELDS or "c" not in body:
        raise ValueError("invalid_quote_fields")
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in body.values()):
        raise ValueError("invalid_quote_values")
    if body["c"] <= 0 or body.get("t") != record.get("source_timestamp_claim_unverified"):
        raise ValueError("invalid_quote_claim")
    try:
        started = datetime.fromisoformat(record["request_started_utc"])
        finished = datetime.fromisoformat(record["response_finished_utc"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid_observation_clock") from exc
    if any(t.tzinfo is None or t.utcoffset().total_seconds() != 0 for t in (started, finished)) or finished < started:
        raise ValueError("invalid_observation_clock")
    return {
        "status": "offline_integrity_verified",
        "symbol": record["symbol_requested"],
        "source_sha256": record["source_sha256"],
        "provider_authenticated": False,
        "quote_accuracy_verified": False,
        "prospective_signal_proven": False,
        "trade_ready": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("observation")
    args = parser.parse_args()
    print(json.dumps(verify(args.observation), sort_keys=True))
