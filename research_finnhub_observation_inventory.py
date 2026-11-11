"""Offline immutable Finnhub observation inventory, no network or trading actions.

Requires verified records and refuses conflicting duplicates. Does not infer
quote accuracy, signal availability, or trading suitability.
"""
import json
from pathlib import Path
from research_verify_finnhub_observation import verify


def build_inventory(paths):
    if not isinstance(paths, (list, tuple)) or not paths:
        raise ValueError("observation_paths_required")
    entries = []
    seen = set()
    for path in paths:
        result = verify(path)
        record = json.loads(Path(path).read_text(encoding="utf-8"))
        identity = (record["symbol_requested"], record["request_started_utc"],
                    record["response_finished_utc"])
        if identity in seen:
            raise ValueError("duplicate_observation_window")
        seen.add(identity)
        entries.append({
            "symbol": result["symbol"],
            "request_started_utc": record["request_started_utc"],
            "response_finished_utc": record["response_finished_utc"],
            "source_sha256": result["source_sha256"],
            "research_only": True,
            "trade_ready": False,
        })
    entries.sort(key=lambda item: (item["request_started_utc"], item["symbol"],
                                   item["response_finished_utc"]))
    return {"schema": "dipsaus_research_observation_inventory_v1",
            "count": len(entries), "observations": entries,
            "quote_accuracy_verified": False,
            "prospective_signal_proven": False, "trade_ready": False}
