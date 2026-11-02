"""Audit independent historical evidence coverage for exploratory sector universe.

No provider calls; this validates manifests only and cannot authorize trades.
"""
from research_swing_sector_universe_v2 import expanded_universe_manifest
from sector_rotation_evidence import SECTORS

ACCEPTED_RESEARCH_STATUSES = frozenset(("normalized_unverified", "audited_verified"))


def audit_exploratory_sector_coverage(status_by_symbol):
    manifest = expanded_universe_manifest()
    expected = {row["symbol"]: row["sector"] for row in manifest["symbols"]}
    if not isinstance(status_by_symbol, dict) or set(status_by_symbol) != set(expected):
        return {"status": "UNKNOWN", "reason": "INCOMPLETE_UNIVERSE_COVERAGE",
                "research_only": True, "trade_ready": False}
    sector_counts = {sector: 0 for sector in SECTORS}
    for symbol, sector in expected.items():
        if status_by_symbol[symbol] in ACCEPTED_RESEARCH_STATUSES:
            sector_counts[sector] += 1
    missing = sorted(sector for sector, count in sector_counts.items() if count < 2)
    return {"status": "INCOMPLETE_RESEARCH" if missing else "REVIEW_REQUIRED",
            "missing_sectors": missing, "sector_counts": sector_counts,
            "source_data_validated": False,
            "sector_representativeness_verified": False,
            "research_only": True, "trade_ready": False}
