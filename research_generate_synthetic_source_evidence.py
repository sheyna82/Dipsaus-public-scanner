"""Produce a clearly synthetic source-byte evidence ZIP for GitHub transport tests.

No market network requests, credentials, live candidates, or trade signals.
"""
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from research_source_bound_registration import register_observation_with_source_snapshot
from research_source_evidence_archive import archive_source_evidence


def generate(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    source = b'{"synthetic_data_only":true,"symbol":"AMD","price":123.45}\n'
    observation = {
        "symbol": "AMD", "protocol_id": "synthetic-source-transport-v1",
        "signal_session": "2026-11-03",
        "source_name": "synthetic-fixture-not-market-data",
        "source_url": "https://example.org/synthetic-fixture",
        "source_observed_at_utc": "2026-11-03T15:00:00Z",
        "independent_source_authentication": False,
        "independent_timestamp_proof": False,
        "synthetic_data_only": True,
        "research_only": True, "trade_ready": False, "future_outcome": None,
    }
    with tempfile.TemporaryDirectory() as tmp:
        candidates = Path(tmp) / "candidates"
        candidates.mkdir()
        result = register_observation_with_source_snapshot(
            observation, source, candidates,
            clock=lambda: datetime(2026, 11, 3, 16, tzinfo=timezone.utc))
        archive = destination / "source-evidence-synthetic.zip"
        verified = archive_source_evidence(result["path"], source, archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (destination / "sha256.txt").write_text(digest + "  source-evidence-synthetic.zip\n", encoding="utf-8")
    return {"synthetic_data_only": True, "trade_ready": False,
            "sha256": digest, "verification": verified}


if __name__ == "__main__":
    print(json.dumps(generate("synthetic-source-evidence"), sort_keys=True))
