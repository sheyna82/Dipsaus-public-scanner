"""Manual research-only intake of a locally supplied market-source snapshot.

Example:
  python research_manual_observation_intake.py --observation observation.json \
    --source source.bin --candidates ./candidates --archive ./evidence.zip \
    --allow-host example.org

This does not download data, infer signals, or establish independent provenance.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from research_offline_observation_archive import archive_offline_observation
from research_alpha_vantage_offline_daily import inspect_alpha_vantage_daily_bytes


def run_manual_intake(observation_path, source_path, candidates, archive, *, allowed_hosts, provider_format=None):
    observation = json.loads(Path(observation_path).read_text(encoding="utf-8"))
    if not isinstance(observation, dict):
        raise ValueError("observation_must_be_object")
    source = Path(source_path)
    if not source.is_file() or source.stat().st_size > 5_000_000:
        raise ValueError("invalid_source_file")
    raw = source.read_bytes()
    if provider_format not in (None, "alpha_vantage_daily"):
        raise ValueError("unsupported_provider_format")
    if provider_format == "alpha_vantage_daily":
        # Parse and validate every daily bar BEFORE creating a candidate.
        # The source URL is caller-supplied, not independent provider proof.
        inspect_alpha_vantage_daily_bytes(
            raw, expected_symbol=observation.get("symbol"),
            as_of_session=observation.get("signal_session"))
    result = archive_offline_observation(
        observation, raw, candidates, archive,
        clock=lambda: datetime.now(timezone.utc),
        allowed_hosts=frozenset(allowed_hosts))
    return {
        "status": "offline_observation_archived_unverified",
        "candidate_sha256": result["registration"]["sha256"],
        "source_sha256": result["source_sha256"],
        "archive_status": result["archive_verification"]["status"],
        "independent_market_data_provenance": False,
        "independent_pre_signal_timestamp_proof": False,
        "trade_ready": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observation", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--allow-host", action="append", required=True)
    parser.add_argument("--provider-format", choices=["alpha_vantage_daily"])
    args = parser.parse_args()
    print(json.dumps(run_manual_intake(
        args.observation, args.source, args.candidates, args.archive,
        allowed_hosts=args.allow_host, provider_format=args.provider_format), sort_keys=True))


if __name__ == "__main__":
    main()
