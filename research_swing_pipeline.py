"""Research-only offline bridge between ranked candidates and measured outcomes.

No live data, no order placement, no modification of frozen momentum protocol.
Synthetic candidates include a timestamped score and a completed exit window.
"""
from datetime import date
from decimal import Decimal
from research_swing_portfolio import allocate_and_simulate
from research_swing_rank_validation import evaluate_ranked_outcomes


def evaluate_research_batch(candidates, *, entry_day, outcome_day,
                            capital=10500, tranche=3500, horizon=5,
                            spread_bps=0, slippage_bps=0, commission_bps=0,
                            min_days=10, min_rows=30):
    """Measure both portfolio selection and paired-date ranking evidence.

    Outcomes for all candidates are scored to avoid selection-only bias.
    Only pre-entry recorded scores may participate. Does not imply
    prospective evidence: the caller must independently verify immutable
    provenance and historical price-source timestamps.
    """
    start, end = date.fromisoformat(entry_day), date.fromisoformat(outcome_day)
    if end <= start:
        raise ValueError("outcome_must_follow_entry")
    if not isinstance(candidates, (list, tuple)):
        raise ValueError("invalid_candidates")
    clean = []
    rows = []
    for item in candidates:
        if not isinstance(item, dict):
            raise ValueError("invalid_candidate")
        recorded = date.fromisoformat(item["recorded_day"])
        if recorded > start:
            raise ValueError("score_recorded_after_entry")
        ticker = item["ticker"]
        score = item["score"]
        clean.append({key: item[key] for key in
                      ("ticker", "score", "entry_price", "daily_closes")})
        # Evaluate every candidate with identical per-trade allocation,
        # even if portfolio capacity prevents its selection.
        from research_swing_net_pnl import simulate_swing
        outcome = simulate_swing(
            item["entry_price"], item["daily_closes"], tranche,
            horizon=horizon, spread_bps=spread_bps,
            slippage_bps=slippage_bps, commission_bps=commission_bps)
        rows.append({"ticker": ticker, "entry_day": entry_day,
                     "recorded_day": item["recorded_day"],
                     "outcome_day": outcome_day, "score": score,
                     "net_return_pct": outcome["net_return_on_allocated_capital_pct"],
                     "eligible": item.get("eligible") is True})
    portfolio = allocate_and_simulate(
        clean, capital, tranche=tranche, horizon=horizon,
        spread_bps=spread_bps, slippage_bps=slippage_bps,
        commission_bps=commission_bps)
    ranking = evaluate_ranked_outcomes(rows, min_days=min_days, min_rows=min_rows)
    return {"research_only": True, "trade_ready": False,
            "source_provenance_independently_verified": False,
            "portfolio": portfolio, "ranking": ranking}
