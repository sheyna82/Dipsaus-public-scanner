"""Cross-provider OHLCV comparison, offline and research-only.

Comparing two supplied datasets is not proof that providers are independent.
The admission of provider identities and licensing must be performed separately.
"""
from research.us_ohlcv_integrity_20261117 import attest_ohlcv


def compare_sources(left, right, *, now=None, price_tolerance=0.001):
    blocks = []
    if not isinstance(left, dict) or not isinstance(right, dict):
        return {"status": "UNKNOWN", "blocks": ["SOURCE_PAIR_MISSING"],
                "provider_independently_verified": False, "trade_ready": False}
    for label, item in (("LEFT", left), ("RIGHT", right)):
        needed = ("bars", "source", "instrument", "timeframe", "fetched_utc", "expected_sha256")
        if not all(k in item for k in needed):
            blocks.append(label + "_METADATA_MISSING")
            continue
        check = attest_ohlcv(item["bars"], source=item["source"],
                            instrument=item["instrument"], timeframe=item["timeframe"],
                            fetched_utc=item["fetched_utc"],
                            expected_sha256=item["expected_sha256"], now=now)
        if check["status"] != "INTEGRITY_MATCH":
            blocks.extend(label + "_" + b for b in check["blocks"])
    if blocks:
        return {"status": "UNKNOWN", "blocks": sorted(set(blocks)),
                "provider_independently_verified": False, "trade_ready": False}
    if left["source"] == right["source"]:
        blocks.append("SAME_PROVIDER")
    if left["instrument"] != right["instrument"] or left["timeframe"] != right["timeframe"]:
        blocks.append("INSTRUMENT_OR_TIMEFRAME_MISMATCH")
    if left.get("adjustment") not in ("raw", "split") or left.get("adjustment") != right.get("adjustment"):
        blocks.append("ADJUSTMENT_POLICY_MISMATCH")
    a, b = left["bars"], right["bars"]
    if len(a) != len(b):
        blocks.append("BAR_COUNT_MISMATCH")
    else:
        for x, y in zip(a, b):
            if x["time"] != y["time"]:
                blocks.append("SESSION_TIME_MISMATCH")
                break
            for field in ("open", "high", "low", "close"):
                scale = max(abs(x[field]), abs(y[field]))
                if abs(x[field] - y[field]) > price_tolerance * scale:
                    blocks.append("PRICE_DISAGREEMENT")
                    break
            if "PRICE_DISAGREEMENT" in blocks:
                break
    return {"status": "CROSS_SOURCE_CONSISTENT" if not blocks else "UNKNOWN",
            "blocks": sorted(set(blocks)), "provider_independently_verified": False,
            "trade_ready": False, "note": "Source independence and licensing not attested"}
