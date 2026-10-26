"""Research-only one-shot public daily-price download, disabled by default.

Stooq's CSV endpoint is an exploratory source, not a guaranteed licensed feed.
No secrets, no orders, no background polling. Never substitute daily volume
for opening-auction matched volume. Require explicit opt-in to network access.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from research_swing_ohlcv_csv_ingest import load_verified_ohlcv_csv

ALLOWED_SYMBOLS = frozenset({"aapl.us", "msft.us", "spy.us"})


def download_once(symbol, destination, *, allow_network=False, opener=urlopen):
    if not allow_network:
        raise ValueError("network_access_requires_explicit_opt_in")
    if symbol not in ALLOWED_SYMBOLS:
        raise ValueError("symbol_not_allowlisted")
    destination = Path(destination)
    if destination.exists():
        raise ValueError("destination_already_exists")
    url = "https://stooq.com/q/d/l/?" + urlencode({"s": symbol, "i": "d"})
    request = Request(url, headers={"User-Agent": "DIPSAUS-research/0.1"})
    with opener(request, timeout=15) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000 or not data:
        raise ValueError("empty_or_oversized_response")
    # Stooq uses Date,Open,High,Low,Close,Volume; normalize only the header
    # and retain raw downloaded bytes separately for independent reproduction.
    raw_lines = data.decode("utf-8-sig").splitlines()
    if not raw_lines or raw_lines[0] != "Date,Open,High,Low,Close,Volume":
        raise ValueError("unexpected_provider_header")
    normalized = "\n".join(["session_date,open,high,low,close,volume", *raw_lines[1:]]) + "\n"
    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        scratch = Path(temp) / "normalized.csv"
        scratch.write_text(normalized, encoding="utf-8")
        result = load_verified_ohlcv_csv(scratch)
    destination.write_bytes(data)
    return {
        "research_only": True, "trade_ready": False,
        "provider": "Stooq exploratory CSV endpoint",
        "symbol": symbol, "source_url": url,
        "raw_sha256": hashlib.sha256(data).hexdigest(),
        "normalized_sha256": result["sha256"],
        "bars": result["bar_count"],
        "first_session": result["audit"]["first_session"],
        "last_session": result["audit"]["last_session"],
        "license_verified": False,
        "corporate_actions_verified": False,
        "opening_auction_volume_available": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", choices=sorted(ALLOWED_SYMBOLS), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--allow-network", action="store_true")
    args = parser.parse_args()
    print(json.dumps(download_once(args.symbol, args.output,
                                   allow_network=args.allow_network), indent=2))


if __name__ == "__main__":
    main()
