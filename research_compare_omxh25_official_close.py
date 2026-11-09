"""Research-only dated Nasdaq/Yahoo OMXH25 close comparison.

Pinned official close is a documented observation, not an independently
revalidated raw Nasdaq EOD response. Never promotes benchmark identity.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import math

OFFICIAL_OBSERVATIONS = {
    "2026-11-05": {
        "close": 6254.30,
        "source": "https://fred.stlouisfed.org/series/NASDAQOMXH25",
        "corroboration": "https://markets.ft.markitdigital.com/data/indices/tearsheet/historical?s=OMX25%3AHEX",
        "official_variant": "OMXH25",
        "return_type": "PRICE_RETURN",
        "currency": "EUR",
        "raw_official_eod_bytes_preserved": False,
    },
    "2026-11-06": {
        "close": 6221.79,
        "source": "https://beta.indexes.nasdaqomx.com/Index/History/OMXH25",
        "corroboration": "https://fred.stlouisfed.org/series/NASDAQOMXH25",
        "official_variant": "OMXH25",
        "return_type": "PRICE_RETURN",
        "currency": "EUR",
        "raw_official_eod_bytes_preserved": False,
    }
}

def compare_omxh25_capture(capture):
    if (not isinstance(capture, dict) or capture.get("research_only") is not True
            or capture.get("trade_ready") is not False
            or capture.get("benchmark_identity_verified") is not False):
        raise ValueError("UNSAFE_CAPTURE_GATE")
    entry = capture.get("series", {}).get("OMXH25")
    if not isinstance(entry, dict) or entry.get("provider_symbol") != "^OMXH25":
        raise ValueError("OMXH25_PROVIDER_SYMBOL_MISSING")
    meta = entry.get("provider_metadata")
    if not isinstance(meta, dict) or meta.get("currency") != "EUR" or meta.get("instrumentType") != "INDEX":
        raise ValueError("OMXH25_METADATA_INVALID")
    if not isinstance(entry.get("bars"), list):
        raise ValueError("OMXH25_BARS_INVALID")
    by_date = {}
    for bar in entry["bars"]:
        t, value = bar.get("t"), bar.get("close")
        if (isinstance(t, bool) or not isinstance(t, int) or isinstance(value, bool)
                or not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0):
            raise ValueError("OMXH25_BAR_INVALID")
        local = datetime.fromtimestamp(t, timezone.utc).astimezone(ZoneInfo("Europe/Helsinki"))
        day = local.date().isoformat()
        if day in by_date:
            raise ValueError("OMXH25_DUPLICATE_SESSION")
        by_date[day] = value
    comparisons = []
    for day, observation in OFFICIAL_OBSERVATIONS.items():
        if day not in by_date:
            raise ValueError("OMXH25_PINNED_DATE_MISSING")
        provider_close = by_date[day]
        delta = round(provider_close - observation["close"], 6)
        matches = round(provider_close, 2) == observation["close"]
        comparisons.append({"date": day, "provider_close": provider_close,
                            "official_observed_close": observation["close"],
                            "difference": delta, "two_decimal_match": matches,
                            "official_source": observation["source"],
                            "official_raw_bytes_preserved": False})
        if not matches:
            raise ValueError("OMXH25_OFFICIAL_CLOSE_CONFLICT")
    return {"status": "historical_value_match_unverified_identity",
            "compared_days": len(comparisons), "comparisons": comparisons,
            "venue_metadata": meta.get("exchangeName"),
            "venue_mapping_explained": False,
            "official_eod_raw_bytes_verified": False,
            "benchmark_identity_verified": False, "independently_audited": False,
            "research_only": True, "trade_ready": False}
