"""Isolated AMD-only historical capture. Research data, never a trading signal."""
import hashlib
import json
import math
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://query1.finance.yahoo.com/v8/finance/chart/AMD"
SERIES = (("daily", "6mo", "1d", 100), ("intraday", "5d", "1m", 20))
MAX_BYTES = 2_000_000

class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirect_forbidden")

def collect(destination, fetch=None):
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError("immutable_capture_exists")
    if not destination.parent.is_dir():
        raise ValueError("destination_directory_missing")
    fetch = fetch or urllib.request.build_opener(NoRedirects()).open
    output = {"schema": "dipsaus_amd_history_v1", "symbol": "AMD",
              "captured_utc": datetime.now(timezone.utc).isoformat(),
              "research_only": True, "trade_ready": False, "series": {}}
    for name, period, interval, minimum in SERIES:
        url = BASE + "?" + urllib.parse.urlencode(
            {"range": period, "interval": interval, "includePrePost": "false"})
        request = urllib.request.Request(url, headers={
            "Accept": "application/json", "User-Agent": "DipsausResearchCapture/1.0"})
        with fetch(request, timeout=20) as response:
            if response.status != 200:
                raise ValueError("http_error_" + name)
            raw = response.read(MAX_BYTES + 1)
        if not raw or len(raw) > MAX_BYTES:
            raise ValueError("response_size_invalid_" + name)
        doc = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
        result = doc["chart"]["result"][0]
        meta = result["meta"]
        if meta.get("symbol") != "AMD":
            raise ValueError("symbol_mismatch_" + name)
        timestamps = result["timestamp"]
        quote = result["indicators"]["quote"][0]
        fields = ("open", "high", "low", "close", "volume")
        if any(len(quote[k]) != len(timestamps) for k in fields):
            raise ValueError("bar_length_mismatch_" + name)
        bars = []
        for i, ts in enumerate(timestamps):
            values = [quote[k][i] for k in fields]
            if any(v is None or isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
                continue
            o, h, l, c, volume = values
            if min(o, h, l, c) <= 0 or l > min(o, c) or h < max(o, c) or volume < 0:
                continue
            bars.append({"t": int(ts), **dict(zip(fields, values))})
        if len(bars) < minimum or any(a["t"] >= b["t"] for a, b in zip(bars, bars[1:])):
            raise ValueError("insufficient_or_unsorted_bars_" + name)
        output["series"][name] = {"interval": interval, "source": url,
            "source_sha256": hashlib.sha256(raw).hexdigest(), "count": len(bars),
            "first_timestamp": bars[0]["t"], "last_timestamp": bars[-1]["t"], "bars": bars}
    with destination.open("x", encoding="utf-8") as f:
        json.dump(output, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")
    return {"status": "research_capture_complete", "counts": {k: v["count"] for k, v in output["series"].items()}, "trade_ready": False}

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: python research_capture_amd_history.py OUTPUT")
    print(json.dumps(collect(sys.argv[1]), sort_keys=True))
