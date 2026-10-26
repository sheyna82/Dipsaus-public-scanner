"""Research-only download probe that never commits market data.

Explicit workflow dispatch only. Outputs metadata and SHA256 as job logs,
never raw downloaded prices. Provider access and licensing are NOT verified.
"""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from research_swing_public_price_one_shot import download_once
from research_swing_price_probe_status import classify_price_probe_error


def probe(symbol):
    with TemporaryDirectory() as tmp:
        try:
            result = download_once(symbol, Path(tmp) / "raw.csv", allow_network=True)
        except Exception as exc:
            result = classify_price_probe_error(exc)
            result["status"] = "failed"
            result["error_type"] = type(exc).__name__
            result["source_data_saved"] = False
            return result
        return {"status": "validated_download", "symbol": result["symbol"],
                "bars": result["bars"],
                "first_session": result["first_session"],
                "last_session": result["last_session"],
                "raw_sha256": result["raw_sha256"],
                "source_data_saved": False,
                "license_verified": False,
                "corporate_actions_verified": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", choices=("aapl.us", "msft.us", "spy.us"),
                        default="aapl.us")
    args = parser.parse_args()
    print(json.dumps(probe(args.symbol), sort_keys=True))


if __name__ == "__main__":
    main()
