"""Diagnose rejected OHLCV without silently repairing vendor observations.

Reports counts and first few anomaly dates, not raw prices. A structurally
invalid session must remain excluded from research until independently checked.
"""
import json
import math
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

URL = "https://query1.finance.yahoo.com/v8/finance/chart/DIS?range=5y&interval=1d"


def diagnose_chart(payload, *, symbol="DIS"):
    try:
        result = payload["chart"]["result"][0]
        if result["meta"]["symbol"].upper() != symbol:
            return {"status": "DATA_BLOCKED", "reason": "symbol_mismatch"}
        timestamps = result["timestamp"]
        q = result["indicators"]["quote"][0]
        keys = ("open", "high", "low", "close", "volume")
        if any(len(q[k]) != len(timestamps) for k in keys):
            return {"status": "DATA_BLOCKED", "reason": "length_mismatch"}
        counts = {}
        examples = []
        for i, ts in enumerate(timestamps):
            values = [q[k][i] for k in keys]
            reason = None
            if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
                reason = "missing_or_nonfinite"
            else:
                op, hi, lo, cl, vol = values
                if min(op, hi, lo, cl) <= 0:
                    reason = "nonpositive_price"
                elif vol <= 0:
                    reason = "nonpositive_volume"
                elif not lo <= min(op, cl) <= max(op, cl) <= hi:
                    reason = "inconsistent_ohlc"
            if reason:
                counts[reason] = counts.get(reason, 0) + 1
                if len(examples) < 8:
                    examples.append({"date_utc": datetime.fromtimestamp(ts, timezone.utc).date().isoformat(),
                                     "reason": reason})
        return {"status": "ANOMALY_REVIEW_REQUIRED" if counts else "STRUCTURE_VALID",
                "symbol": symbol, "bars": len(timestamps), "anomaly_counts": counts,
                "examples": examples, "corporate_actions_verified": False,
                "independent_price_validation": False, "trade_ready": False}
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        return {"status": "DATA_BLOCKED", "reason": "invalid_payload"}


if __name__ == "__main__":
    try:
        with urlopen(Request(URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=12) as response:
            raw = response.read(1_500_001)
        result = (diagnose_chart(json.loads(raw)) if len(raw) <= 1_500_000
                  else {"status": "DATA_BLOCKED", "reason": "oversized"})
    except (OSError, HTTPError, URLError, ValueError, TimeoutError):
        result = {"status": "DATA_BLOCKED", "reason": "fetch_failed"}
    print(json.dumps(result, sort_keys=True))
