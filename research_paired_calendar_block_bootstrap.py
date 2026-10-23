"""Exploratory paired calendar-block bootstrap; synthetic/offline research only."""
from collections import defaultdict
from datetime import date
import math
import random


def paired_calendar_block_bootstrap(rows, *, block_days=14, replicates=500,
                                    seed=20261023, confidence=0.95):
    """Resample contiguous observed calendar dates, retaining all tickers per date.

    The interval is exploratory, not validated for market inference.
    """
    if not isinstance(rows, (list, tuple)) or not rows:
        raise ValueError("empty_holdout")
    if type(block_days) is not int or block_days < 1:
        raise ValueError("invalid_block_days")
    if type(replicates) is not int or replicates < 2 or replicates > 10000:
        raise ValueError("invalid_replicates")
    if (type(seed) is not int or type(confidence) not in (float, int)
            or not math.isfinite(confidence) or not 0 < confidence < 1):
        raise ValueError("invalid_bootstrap_settings")
    grouped = defaultdict(list)
    # Both scoring rules must use the same paired resampling draws.
    grouped_log = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict) or type(row.get("severe")) is not bool:
            raise ValueError("invalid_event")
        try:
            day = date.fromisoformat(row["event_date"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid_event_date") from exc
        probabilities = []
        for field in ("baseline_probability", "atr_probability"):
            p = row.get(field)
            if type(p) not in (float, int) or not math.isfinite(p) or not 0 <= p <= 1:
                raise ValueError("invalid_probability")
            probabilities.append(p)
        y = int(row["severe"])
        grouped[day].append((probabilities[1] - y) ** 2 -
                            (probabilities[0] - y) ** 2)
        def log_loss(p):
            # Explicit clipping avoids infinite loss at probability 0 or 1.
            p = min(.99, max(.01, p))
            return -y * math.log(p) - (1 - y) * math.log(1 - p)
        grouped_log[day].append(log_loss(probabilities[1]) -
                                log_loss(probabilities[0]))
    dates = sorted(grouped)
    if len(dates) < 2 or block_days > len(dates):
        raise ValueError("insufficient_calendar_dates")
    # Dates are observed calendar dates, not verified exchange sessions.
    # The caller must audit calendar gaps before treating this as inference.
    starts = list(range(len(dates) - block_days + 1))
    rng = random.Random(seed)
    estimates = []
    log_estimates = []
    for _ in range(replicates):
        sampled = []
        while len(sampled) < len(dates):
            start = rng.choice(starts)
            sampled.extend(dates[start:start + block_days])
        sampled = sampled[:len(dates)]
        values = [difference for day in sampled for difference in grouped[day]]
        estimates.append(sum(values) / len(values))
        log_values = [difference for day in sampled for difference in grouped_log[day]]
        log_estimates.append(sum(log_values) / len(log_values))
    estimates.sort()
    log_estimates.sort()
    alpha = (1 - confidence) / 2
    lower = estimates[max(0, math.floor(alpha * replicates))]
    upper = estimates[min(replicates - 1, math.ceil((1 - alpha) * replicates) - 1)]
    log_lower = log_estimates[max(0, math.floor(alpha * replicates))]
    log_upper = log_estimates[min(replicates - 1, math.ceil((1 - alpha) * replicates) - 1)]
    observed = [difference for day in dates for difference in grouped[day]]
    observed_log = [difference for day in dates for difference in grouped_log[day]]
    event_counts = [len(grouped[day]) for day in dates]
    return {
        "events": len(observed),
        "observed_calendar_dates": len(dates),
        "minimum_events_per_observed_date": min(event_counts),
        "maximum_events_per_observed_date": max(event_counts),
        "unequal_events_per_date": min(event_counts) != max(event_counts),
        "estimand": "event_weighted_mean_loss_difference",
        "calendar_gaps_present": any((right - left).days > 1
                                     for left, right in zip(dates, dates[1:])),
        "block_observed_dates": block_days,
        "replicates": replicates,
        "seed": seed,
        "confidence": confidence,
        "log_loss_probability_clip": 0.01,
        "interval_method": "empirical_order_statistic_exploratory",
        "resampling_unit": "observed_date_all_events",
        "observed_atr_minus_baseline_brier": sum(observed) / len(observed),
        "exploratory_interval": [lower, upper],
        "observed_atr_minus_baseline_log_loss": sum(observed_log) / len(observed_log),
        "exploratory_log_loss_interval": [log_lower, log_upper],
        "exchange_sessions_verified": False,
        "independent_holdout_verified": False,
        "interval_validated_for_inference": False,
        "trade_ready": False,
    }
