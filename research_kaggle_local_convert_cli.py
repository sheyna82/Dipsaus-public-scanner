"""Local-only conversion of a Kaggle-format CSV into audited canonical CSV.

No network calls; never writes source price data into the repository.
"""
import argparse
import json
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
        if output.parent.resolve() == Path.cwd().resolve() or Path.cwd().resolve() in output.parent.resolve().parents:
            raise ValueError("output_inside_repository")
        if output.exists() or output.is_symlink():
            raise ValueError("output_exists")
        converted = convert_kaggle_daily_csv(source.read_bytes())
        with output.open("xb") as handle:
            handle.write(converted)
        output.chmod(0o600)
    except (ValueError, OSError) as exc:
        print(json.dumps({"converted": False, "error_type": type(exc).__name__}))
        return 1
    print(json.dumps({"converted": True, "bytes_written": len(converted),
                      "provenance_verified": False, "trade_ready": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
