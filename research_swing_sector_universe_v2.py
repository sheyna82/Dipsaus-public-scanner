"""Separate exploratory additions to the frozen diversified research universe.

Never mutate UNIVERSE_V1 or silently promote source data to verified.
"""
from research_swing_diversified_universe import UNIVERSE_V1
from sector_rotation_evidence import SECTORS

EXPLORATORY_V2_ADDITIONS = (
    ("GOOGL", "communication_services"),
    ("DIS", "communication_services"),
    ("HD", "consumer_discretionary"),
    ("MCD", "consumer_discretionary"),
)


def expanded_universe_manifest():
    existing = tuple(UNIVERSE_V1)
    combined = existing + EXPLORATORY_V2_ADDITIONS
    symbols = [symbol for symbol, _ in combined]
    if len(symbols) != len(set(symbols)):
        raise ValueError("DUPLICATE_SYMBOL")
    coverage = {sector: [symbol for symbol, group in combined if group == sector]
                for sector in SECTORS}
    if any(len(items) != 2 for items in coverage.values()):
        raise ValueError("UNBALANCED_SECTOR_COVERAGE")
    return {"universe_version": "EXPLORATORY_V2",
            "frozen_v1_unchanged": True,
            "symbols": [{"symbol": symbol, "sector": sector} for symbol, sector in combined],
            "sector_count": len(coverage), "symbol_count": len(combined),
            "source_data_validated": False, "survivorship_bias_eliminated": False,
            "trade_ready": False, "research_only": True}
