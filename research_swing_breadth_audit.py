"""Offline breadth specification for point-in-time swing research.

Targets are research ambitions, not claims about acquired data.
"""
from collections import Counter

TARGET_MARKETS = ("US", "NL", "DE", "FR", "BE", "IT", "ES", "GB", "SE", "NO", "DK", "FI", "CH")
TARGET_CAP_BUCKETS = ("small", "mid", "large")
TARGET_REGIMES = ("bull", "bear", "correction", "sideways", "high_volatility")
TARGET_HORIZONS = (3, 5, 10, 15, 20)
REQUIRED_FIELDS = (
    "symbol", "market", "sector", "cap_bucket", "regime", "event_kind",
    "event_id", "available_at_utc", "source_url", "delisted_included",
)


def audit_research_breadth(rows):
    """Count coverage without pretending missing dimensions are measured."""
    counts = {field: Counter() for field in
              ("market", "sector", "cap_bucket", "regime", "event_kind")}
    identities = set()
    missing = Counter()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid_row")
        for field in REQUIRED_FIELDS:
            if field not in row or row[field] is None or row[field] == "":
                missing[field] += 1
        if any(field not in row or row[field] is None or row[field] == ""
               for field in REQUIRED_FIELDS):
            continue
        key = (row["symbol"], row["event_id"])
        if key in identities:
            raise ValueError("duplicate_event_identity")
        identities.add(key)
        for field in counts:
            counts[field][row[field]] += 1
    return {
        "total_rows": len(rows),
        "complete_rows": len(identities),
        "missing_field_counts": dict(missing),
        "coverage": {field: dict(counter) for field, counter in counts.items()},
        "delisted_included_count": sum(
            row.get("delisted_included") is True for row in rows if isinstance(row, dict)),
        "target_markets": TARGET_MARKETS,
        "target_cap_buckets": TARGET_CAP_BUCKETS,
        "target_regimes": TARGET_REGIMES,
        "target_horizons": TARGET_HORIZONS,
        "trade_ready": False,
    }
