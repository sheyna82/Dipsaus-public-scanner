"""Deterministic, research-only ranking directions for DIPSAUS.

Scores are computed by callers from point-in-time observations. No orders.
"""
from math import isfinite

RANKING_DIRECTIONS = {
    "deepest_dip": "descending",
    "shallowest_dip": "ascending",
    "strongest_1d_return": "descending",
    "weakest_1d_return": "ascending",
    "strongest_5d_return": "descending",
    "weakest_5d_return": "ascending",
    "strongest_10d_return": "descending",
    "weakest_10d_return": "ascending",
    "highest_20d_volatility": "descending",
    "lowest_20d_volatility": "ascending",
    "highest_relative_volume": "descending",
    "lowest_relative_volume": "ascending",
    "highest_close_location": "descending",
    "lowest_close_location": "ascending",
    "highest_short_long_vol_ratio": "descending",
    "lowest_short_long_vol_ratio": "ascending",
    "closest_to_ma20": "ascending",
    "farthest_from_ma20": "descending",
}


def rank_candidates(scores, method):
    """Rank (ticker, score) pairs with deterministic ticker tie-breaks.

    Dip scores must be positive *depths*; MA20 scores must be absolute
    distances. Caller is responsible for point-in-time feature validity.
    """
    if method not in RANKING_DIRECTIONS:
        raise ValueError("unknown_ranking_method")
    seen = set()
    normalized = []
    for ticker, score in scores:
        if not isinstance(ticker, str) or not ticker or ticker in seen:
            raise ValueError("invalid_or_duplicate_ticker")
        if type(score) not in (int, float) or not isfinite(score):
            raise ValueError("invalid_score")
        seen.add(ticker)
        normalized.append((ticker, score))
    descending = RANKING_DIRECTIONS[method] == "descending"
    return sorted(normalized, key=lambda item: ((-item[1] if descending else item[1]), item[0]))
