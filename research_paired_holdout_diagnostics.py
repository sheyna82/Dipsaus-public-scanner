"""Descriptive paired comparison of frozen holdout forecasts; not a significance claim."""
import math
from datetime import date


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
    # Optional observation windows permit overlap auditing. Missing dates
    # cannot be interpreted as evidence of independence.
    windows = []
    for row in predictions:
        start, end = row.get("event_date"), row.get("label_available_date")
        if start is None and end is None:
            continue
        if not isinstance(start, str) or not isinstance(end, str):
            raise ValueError("incomplete_outcome_window")
        try:
            start_day, end_day = date.fromisoformat(start), date.fromisoformat(end)
        except ValueError as exc:
            raise ValueError("invalid_outcome_window") from exc
        if end_day < start_day:
            raise ValueError("invalid_outcome_window")
        windows.append((start_day, end_day))
    windows.sort()
    # Connected components of overlapping outcome windows. This is a
    # descriptive dependence warning, NOT an effective sample-size estimate.
    clusters = 0
    active_end = None
    for start_day, end_day in windows:
        if active_end is None or start_day > active_end:
            clusters += 1
            active_end = end_day
        else:
            active_end = max(active_end, end_day)
    overlapping_pairs = sum(
        windows[i][0] <= windows[j][1] and windows[j][0] <= windows[i][1]
        for i in range(len(windows)) for j in range(i + 1, len(windows)))
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
        "outcome_windows_supplied": len(windows),
        "overlapping_outcome_window_pairs": overlapping_pairs,
        "overlap_connected_groups": clusters,
        "overlap_group_count_is_effective_sample_size": False,
        "outcome_window_coverage_complete": len(windows) == n,
        "independent_events_assumed": False,
        "uncertainty_interval_verified": False,
        "descriptive_only": True,
        "trade_ready": False,
    }
