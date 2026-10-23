"""Descriptive paired comparison of frozen holdout forecasts; not a significance claim."""
import math


def paired_holdout_diagnostics(predictions):
    """Return event-level paired loss differences and fallback coverage.

    Negative differences favor ATR. Overlapping horizons and shared tickers
    make events dependent; do not interpret standard errors as independent.
    """
    if not isinstance(predictions, (list, tuple)) or not predictions:
        raise ValueError("empty_holdout")
    brier_diffs = []
    log_diffs = []
    for row in predictions:
        if not isinstance(row, dict) or type(row.get("severe")) is not bool:
            raise ValueError("invalid_outcome")
        probs = []
        for field in ("baseline_probability", "atr_probability"):
            p = row.get(field)
            if type(p) not in (float, int) or not math.isfinite(p) or not 0 <= p <= 1:
                raise ValueError("invalid_probability")
            probs.append(p)
        y = int(row["severe"])
        brier_diffs.append((probs[1] - y) ** 2 - (probs[0] - y) ** 2)
        losses = [-y * math.log(min(.99, max(.01, p))) -
                  (1 - y) * math.log(1 - min(.99, max(.01, p))) for p in probs]
        log_diffs.append(losses[1] - losses[0])
    n = len(predictions)
    # Direction counts are descriptive; dependent events invalidate a naive binomial test.
    improved = sum(d < 0 for d in brier_diffs)
    worsened = sum(d > 0 for d in brier_diffs)
    ties = n - improved - worsened
    return {
        "events": n,
        "atr_minus_baseline_brier_unrounded": sum(brier_diffs) / n,
        "atr_minus_baseline_log_loss_unrounded": sum(log_diffs) / n,
        "atr_brier_better_events": improved,
        "atr_brier_worse_events": worsened,
        "equal_brier_events": ties,
        "atr_brier_better_fraction": improved / n,
        "atr_brier_worse_fraction": worsened / n,
        "atr_brier_tie_fraction": ties / n,
        "non_tied_events": improved + worsened,
        "event_level_brier_differences": brier_diffs,
        "event_level_log_loss_differences": log_diffs,
        "independent_events_assumed": False,
        "uncertainty_interval_verified": False,
        "descriptive_only": True,
        "trade_ready": False,
    }
