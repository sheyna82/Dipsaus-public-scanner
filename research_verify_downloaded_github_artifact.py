"""Read-only CLI for verification of a downloaded synthetic GitHub artifact.

Requires independently obtained GitHub API metadata and an explicit run/head.
Does not fetch data, modify scanners, or grant trading permission.
"""
import argparse
import json
import tempfile
from pathlib import Path

from research_github_synthetic_artifact_verifier import verify_github_synthetic_artifact


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-zip", required=True, type=Path)
    parser.add_argument("--metadata-json", required=True, type=Path)
    parser.add_argument("--expected-run-id", required=True, type=int)
    parser.add_argument("--expected-head-sha", required=True)
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="dipsaus-research-") as directory:
        result = verify_github_synthetic_artifact(
            args.artifact_zip.read_bytes(),
            json.loads(args.metadata_json.read_text(encoding="utf-8")),
            Path(directory) / "verified-inner.zip",
            expected_run_id=args.expected_run_id,
            expected_head_sha=args.expected_head_sha)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
