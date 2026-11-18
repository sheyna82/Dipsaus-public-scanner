"""Pure offline provenance chain for prospective US watch observations.

Hash linkage detects subsequent edits *within a supplied chain*. It cannot
prove original observation time, independent source authenticity or storage
immutability. No file, network, broker or production access.
"""
import hashlib
import json
from datetime import datetime, timezone

def _utc(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except (ValueError, OverflowError):
        return None

def _digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False).encode()).hexdigest()

def append_observation(chain, observation):
    if not isinstance(chain, list) or not isinstance(observation, dict):
        return {"status": "BLOCKED", "blocks": ["INVALID_INPUT"]}
    verification = verify_chain(chain)
    if verification["status"] != "VALID":
        return {"status": "BLOCKED", "blocks": ["PRIOR_CHAIN_INVALID"]}
    symbol, source = observation.get("symbol"), observation.get("source_id")
    timestamp = _utc(observation.get("observed_utc"))
    price = observation.get("close_usd")
    if not isinstance(symbol, str) or not symbol.strip() or not isinstance(source, str) or not source.strip():
        return {"status": "BLOCKED", "blocks": ["IDENTITY_OR_SOURCE_MISSING"]}
    if timestamp is None or type(price) not in (int, float) or not 0 < price < float("inf"):
        return {"status": "BLOCKED", "blocks": ["OBSERVATION_INVALID"]}
    if chain and (chain[-1]["symbol"] != symbol or
                  timestamp <= _utc(chain[-1]["observed_utc"])):
        return {"status": "BLOCKED", "blocks": ["IDENTITY_OR_TIME_CONFLICT"]}
    # Only allow known non-secret fields. No raw provider payloads or tokens.
    payload = {"symbol": symbol, "source_id": source,
               "observed_utc": observation["observed_utc"], "close_usd": price,
               "sequence": len(chain), "previous_hash": chain[-1]["hash"] if chain else None}
    item = {**payload, "hash": _digest(payload)}
    return {"status": "VALID", "chain": [*chain, item], "trade_ready": False,
            "notify": False, "automatic_orders": False}

def verify_chain(chain):
    if not isinstance(chain, list):
        return {"status": "BLOCKED", "blocks": ["CHAIN_INVALID"]}
    previous_hash = None
    previous_time = None
    symbol = None
    for i, item in enumerate(chain):
        if not isinstance(item, dict) or set(item) != {"symbol", "source_id", "observed_utc",
                                                       "close_usd", "sequence", "previous_hash", "hash"}:
            return {"status": "BLOCKED", "blocks": ["SCHEMA_INVALID"], "index": i}
        timestamp = _utc(item["observed_utc"])
        if (timestamp is None or (previous_time is not None and timestamp <= previous_time)
                or type(item["close_usd"]) not in (int, float)
                or not 0 < item["close_usd"] < float("inf")
                or not isinstance(item["symbol"], str) or not item["symbol"].strip()
                or not isinstance(item["source_id"], str) or not item["source_id"].strip()
                or (symbol is not None and symbol != item["symbol"])
                or type(item["sequence"]) is not int or item["sequence"] != i
                or item["previous_hash"] != previous_hash):
            return {"status": "BLOCKED", "blocks": ["CHAIN_ORDER_OR_DATA_INVALID"], "index": i}
        payload = {k: v for k, v in item.items() if k != "hash"}
        if not isinstance(item["hash"], str) or item["hash"] != _digest(payload):
            return {"status": "BLOCKED", "blocks": ["HASH_MISMATCH"], "index": i}
        previous_hash, previous_time, symbol = item["hash"], timestamp, item["symbol"]
    return {"status": "VALID", "count": len(chain), "head_hash": previous_hash,
            "trade_ready": False, "notify": False, "automatic_orders": False,
            "limitations": ["Self-consistent chain only; not independently timestamped",
                            "External append-only anchoring and source verification absent"]}
