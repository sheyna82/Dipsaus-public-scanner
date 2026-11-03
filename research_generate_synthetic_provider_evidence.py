"""Generate synthetic provider-validated candidate evidence; never real market data."""
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from research_manual_observation_intake import run_manual_intake
from research_source_evidence_archive import verify_source_evidence_archive


def generate(destination):
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        candidates = root / "candidates"
        candidates.mkdir()
        observation = root / "observation.json"
        source = root / "source.bin"
        observation.write_text(json.dumps({
            "symbol": "AMD", "protocol_id": "synthetic-provider-transport-v1",
            "signal_session": "2026-11-03",
            "source_name": "SYNTHETIC_FIXTURE_NOT_REAL_ALPHA_VANTAGE",
            "source_url": "https://example.org/synthetic-fixture",
            "source_observed_at_utc": "2026-11-03T15:00:00Z",
            "independent_source_authentication": False,
            "independent_timestamp_proof": False,
            "synthetic_data_only": True,
            "research_only": True, "trade_ready": False, "future_outcome": None,
        }), encoding="utf-8")
        source.write_text(json.dumps({
            "Meta Data": {"2. Symbol": "AMD"},
            "Time Series (Daily)": {"2026-11-03": {
                "1. open": "100", "2. high": "104", "3. low": "99",
                "4. close": "102", "5. volume": "12345"}}
        }), encoding="utf-8")
        archive = out / "synthetic-provider-evidence.zip"
        with patch("research_manual_observation_intake.datetime") as dt:
            dt.now.return_value = datetime(2026, 11, 3, 16, tzinfo=timezone.utc)
            result = run_manual_intake(
                observation, source, candidates, archive,
                allowed_hosts=["example.org"], provider_format="alpha_vantage_daily")
    verified = verify_source_evidence_archive(archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (out / "sha256.txt").write_text(
        digest + "  synthetic-provider-evidence.zip\n", encoding="utf-8")
    return {"synthetic_data_only": True, "trade_ready": False,
            "source_sha256": result["source_sha256"],
            "archive_sha256": digest, "verification": verified}


if __name__ == "__main__":
    print(json.dumps(generate("synthetic-provider-evidence"), sort_keys=True))
