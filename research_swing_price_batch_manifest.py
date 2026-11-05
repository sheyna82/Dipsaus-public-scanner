"""Offline manifest for historical price research batches.

This records provenance claims without authenticating a data provider.
A manifest is not proof that a market-data license permits redistribution.
"""
import hashlib
import json
from pathlib import Path
from research_swing_ohlcv_csv_ingest import load_verified_ohlcv_csv


def create_price_batch_manifest(files, *, provider_name, retrieved_at):
    if not isinstance(provider_name, str) or not provider_name.strip():
        raise ValueError("missing_provider")
    from datetime import datetime
    try:
        timestamp = datetime.fromisoformat(retrieved_at)
    except (ValueError, TypeError):
        raise ValueError("invalid_retrieval_timestamp") from None
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timezone_required")
    if not isinstance(files, dict) or not files:
        raise ValueError("empty_price_batch")
    entries = []
    for symbol, path in sorted(files.items()):
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("invalid_symbol")
        imported = load_verified_ohlcv_csv(Path(path))
        entries.append({
            "symbol": symbol,
            "sha256": imported["sha256"],
            "sessions": imported["bar_count"],
            "first_session": imported["audit"]["first_session"],
            "last_session": imported["audit"]["last_session"],
        })
    manifest = {
        "research_only": True, "trade_ready": False,
        "provider_claim": provider_name,
        "retrieved_at_claim": timestamp.isoformat(),
        "files": entries,
        "provider_authenticated": False,
        "license_verified": False,
        "corporate_actions_verified": False,
        "opening_auction_volume_verified": False,
    }
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    manifest["manifest_sha256"] = hashlib.sha256(encoded).hexdigest()
    return manifest
