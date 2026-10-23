"""Local-only conversion of a Kaggle-format CSV into audited canonical CSV.

No network calls; never writes source price data into the repository.
"""
import argparse
import json
import hashlib
from pathlib import Path

from research_kaggle_daily_converter import convert_kaggle_daily_csv
from research_local_price_audit_cli import MAX_CSV_BYTES


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        source = Path(args.source)
        output = Path(args.output)
        if source.is_symlink() or not source.is_file():
            raise ValueError("invalid_source")
        if source.stat().st_size > MAX_CSV_BYTES:
            raise ValueError("input_too_large")
        # Guard the entire checked-out project tree, not merely the invocation directory.
        repository_root = Path(__file__).resolve().parent
        resolved_parent = output.parent.resolve()
        if resolved_parent == repository_root or repository_root in resolved_parent.parents:
            raise ValueError("output_inside_repository")
        if output.exists() or output.is_symlink():
            raise ValueError("output_exists")
        source_bytes = source.read_bytes()
        source_sha256 = hashlib.sha256(source_bytes).hexdigest()
        converted = convert_kaggle_daily_csv(source_bytes)
        converted_sha256 = hashlib.sha256(converted).hexdigest()
        with output.open("xb") as handle:
            handle.write(converted)
        output.chmod(0o600)
    except (ValueError, OSError) as exc:
        print(json.dumps({"converted": False, "error_type": type(exc).__name__}))
        return 1
    print(json.dumps({"converted": True, "bytes_written": len(converted),
                      "source_sha256": source_sha256,
                      "converted_sha256": converted_sha256,
                      "provenance_verified": False, "trade_ready": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
