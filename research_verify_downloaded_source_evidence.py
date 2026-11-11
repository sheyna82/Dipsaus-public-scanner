"""Read-only CLI to verify a downloaded synthetic source-byte GitHub artifact.

Metadata must be saved independently from the GitHub Actions API. This tool
does not retrieve market data, modify live scanners, or authorize trading.
"""
import argparse
import json
from pathlib import Path

from research_github_source_evidence_verifier import verify_github_source_evidence


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-zip", required=True, type=Path)
    parser.add_argument("--metadata-json", required=True, type=Path)
    parser.add_argument("--expected-run-id", required=True, type=int)
    parser.add_argument("--expected-head-sha", required=True)
    args = parser.parse_args(argv)
    result = verify_github_source_evidence(
        args.artifact_zip.read_bytes(),
        json.loads(args.metadata_json.read_text(encoding="utf-8")),
        expected_run_id=args.expected_run_id,
        expected_head_sha=args.expected_head_sha)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
