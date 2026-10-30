"""Deterministic *hypothesis* scores for offline swing research only.

Not trained, calibrated, or validated on actual market outcomes. Inputs must
be pre-entry observed factors from an independently verified source.
Separate score recipes avoid falsely treating event and recovery as identical.
"""
from decimal import Decimal, InvalidOperation

# These are deliberately transparent research hypotheses, not optimized weights.
RECOVERY_WEIGHTS = {
    "relative_strength_5d": Decimal("0.30"),
    "rebound_from_20d_low": Decimal("0.25"),
    "volume_confirmation": Decimal("0.20"),
    "trend_stability": Decimal("0.15"),
    "downside_resilience": Decimal("0.10"),
}
EVENT_WEIGHTS = {
    "catalyst_materiality": Decimal("0.30"),
    "source_reliability": Decimal("0.25"),
    "volume_confirmation": Decimal("0.20"),
    "price_confirmation": Decimal("0.15"),
    "downside_resilience": Decimal("0.10"),
}
RECIPES = {"technical_recovery": RECOVERY_WEIGHTS, "event_catalyst": EVENT_WEIGHTS}


def score_candidate(lane, factors):
    """Score 0..100 from preregisterable 0..1 factor measurements.

    Never silently clamp: out-of-range or missing measurements are rejected.
    Scores across lanes are not comparable until empirically calibrated.
    """
    if lane not in RECIPES:
        raise ValueError("unknown_research_lane")
    if not isinstance(factors, dict) or set(factors) != set(RECIPES[lane]):
        raise ValueError("missing_or_unexpected_factors")
    values = {}
    for name, raw in factors.items():
        if isinstance(raw, bool):
            raise ValueError("invalid_factor")
        try:
            value = Decimal(str(raw))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError("invalid_factor") from None
        if not value.is_finite() or not 0 <= value <= 1:
            raise ValueError("factor_out_of_range")
        values[name] = value
    total = sum((values[k] * weight for k, weight in RECIPES[lane].items()), Decimal(0))
    return {"research_only": True, "trade_ready": False,
            "score_recipe": "swing_hypothesis_v0_unvalidated",
            "lane": lane, "score": str(total * 100),
            "score_calibrated": False, "predictive_edge_proven": False}
