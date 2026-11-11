"""Research-only setup episode evaluation, using independently labeled episodes.

Inputs must be timestamped and labels must not be derived from this detector.
No orders, live market calls, notification promotion or optimized thresholds.
"""
from datetime import datetime, timezone
from research.us_independent_setup_replay import replay


def _ts(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("NAIVE_TIMESTAMP")
    return dt.astimezone(timezone.utc)


def optimal_episode_matches(observed_times, reference_times, tolerance_seconds):
    """Maximize chronological one-to-one matches, then minimize total delay."""
    n, m = len(observed_times), len(reference_times)
    if n > 5000 or m > 5000 or n * m > 1_000_000:
        raise ValueError("MATCHING_INPUT_TOO_LARGE")
    # Store scalar scores and one backpointer per cell, not an ever-growing
    # tuple of prior matches in every cell (which scales poorly).
    scores = [[(0, 0.0) for _ in range(m + 1)] for _ in range(n + 1)]
    direction = [[0 for _ in range(m + 1)] for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            best = scores[i - 1][j]
            step = 1  # skip detection
            if scores[i][j - 1] > best:
                best, step = scores[i][j - 1], 2  # skip reference
            delay = abs((observed_times[i - 1] - reference_times[j - 1]).total_seconds())
            if delay <= tolerance_seconds:
                count, neg_delay = scores[i - 1][j - 1]
                candidate = (count + 1, neg_delay - delay)
                if candidate > best:
                    best, step = candidate, 3
            scores[i][j], direction[i][j] = best, step
    pairs = []
    i, j = n, m
    while i and j:
        step = direction[i][j]
        if step == 3:
            delay = abs((observed_times[i - 1] - reference_times[j - 1]).total_seconds())
            pairs.append((i - 1, j - 1, delay))
            i -= 1
            j -= 1
        elif step == 1:
            i -= 1
        else:
            j -= 1
    return tuple(reversed(pairs))

def evaluate(symbol, bars, reference_episodes, *, tolerance_minutes=30):
    """Optimal chronological one-to-one match to external episode-confirmation timestamps.

    Reference episodes: {confirmed_utc: ISO timestamp, source: nonempty string}.
    This is a diagnostic matching contract, not proof labels are independent.
    """
    if tolerance_minutes < 0 or tolerance_minutes > 1440:
        raise ValueError("INVALID_TOLERANCE")
    references = []
    for row in reference_episodes:
        if not isinstance(row, dict) or not row.get("source"):
            raise ValueError("MISSING_INDEPENDENT_REFERENCE_SOURCE")
        references.append(_ts(row["confirmed_utc"]))
    if references != sorted(set(references)):
        raise ValueError("UNSORTED_OR_DUPLICATE_REFERENCES")
    detections = replay(symbol, bars)
    pairs = optimal_episode_matches(
        [_ts(detection["confirmed_utc"]) for detection in detections],
        references, tolerance_minutes * 60)
    matches = [
        {"candidate_setup_id": detections[i]["candidate_setup_id"],
         "reference_index": j, "absolute_delay_minutes": round(delta / 60, 3)}
        for i, j, delta in pairs
    ]
    tp = len(matches)
    fp = len(detections) - tp
    fn = len(references) - tp
    return {"research_only": True, "independent_labels_not_audited": True,
            "candidate_count": len(detections), "reference_count": len(references),
            "true_positive": tp, "false_positive": fp, "false_negative": fn,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "matches": matches,
            "notifications_allowed": False, "trade_ready": False}
