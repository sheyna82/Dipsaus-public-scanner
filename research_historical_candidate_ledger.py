"""Fail-closed offline input gate for a historical DIPSAUS candidate ledger.

Does not download data or attest that input is independently verified.
"""
from datetime import date
from hashlib import sha256
import json
import math


def validate_historical_candidate_ledger(payload):
    if not isinstance(payload, dict) or payload.get("format") != "DIPSAUS_HISTORICAL_CANDIDATES_V1":
        raise ValueError("INVALID_LEDGER_FORMAT")
    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("MISSING_PROVENANCE")
    for field in ("source", "retrieved_at_utc", "source_snapshot_sha256"):
        if not isinstance(provenance.get(field), str) or not provenance[field].strip():
            raise ValueError("INCOMPLETE_PROVENANCE")
    digest = provenance["source_snapshot_sha256"]
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise ValueError("INVALID_SOURCE_DIGEST")
    rows = payload.get("candidates")
    if not isinstance(rows, list):
        raise ValueError("INVALID_CANDIDATES")
    ids = set()
    validated = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("INVALID_CANDIDATE")
        identifier, symbol = row.get("id"), row.get("symbol")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in ids:
            raise ValueError("INVALID_CANDIDATE_ID")
        ids.add(identifier)
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("MISSING_CANDIDATE_SYMBOL")
        try:
            entry, exit_ = date.fromisoformat(row["entry_date"]), date.fromisoformat(row["exit_date"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("INVALID_CANDIDATE_DATES") from None
        if entry >= exit_:
            raise ValueError("INVALID_CANDIDATE_DATES")
        ret = row.get("realized_return_pct")
        if isinstance(ret, bool) or not isinstance(ret, (int, float)) or not math.isfinite(ret) or ret < -100:
            raise ValueError("INVALID_CANDIDATE_OUTCOME")
        validated.append({"id": identifier, "symbol": symbol.strip().upper(),
                          "entry_date": entry.isoformat(), "exit_date": exit_.isoformat(),
                          "realized_return_pct": ret})
    canonical = json.dumps(validated, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {"status": "RESEARCH_ONLY_LEDGER_STRUCTURALLY_VALID",
            "candidates": validated, "candidate_count": len(validated),
            "candidate_sha256": sha256(canonical.encode("utf-8")).hexdigest(),
            "source_snapshot_sha256": digest,
            "source_independently_verified": False,
            "outcomes_independently_verified": False,
            "source_snapshot_bytes_verified": False,
            "trade_ready": False}


def verify_historical_source_snapshot(payload, source_bytes):
    """Validate ledger and compare SHA-256 against exact frozen source bytes.

    Byte match proves only identity with a declared digest, not independent
    market data quality, provider identity, or historical trading performance.
    """
    validated = validate_historical_candidate_ledger(payload)
    if not isinstance(source_bytes, bytes):
        raise ValueError("INVALID_SOURCE_BYTES")
    if not source_bytes:
        raise ValueError("EMPTY_SOURCE_SNAPSHOT")
    actual = sha256(source_bytes).hexdigest()
    if actual != validated["source_snapshot_sha256"]:
        raise ValueError("SOURCE_SNAPSHOT_DIGEST_MISMATCH")
    return {**validated, "source_snapshot_bytes_verified": True,
            "source_snapshot_byte_length": len(source_bytes),
            "source_independently_verified": False,
            "outcomes_independently_verified": False,
            "trade_ready": False}
