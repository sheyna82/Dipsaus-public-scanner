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


def evaluate(symbol, bars, reference_episodes, *, tolerance_minutes=30):
    """Greedy one-to-one match to external episode-confirmation timestamps.

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
    available = set(range(len(references)))
    matches = []
    for detection in detections:
        observed = _ts(detection["confirmed_utc"])
        choices = [(abs((observed - references[i]).total_seconds()), i)
                   for i in available
                   if abs((observed - references[i]).total_seconds()) <= tolerance_minutes * 60]
        if not choices:
            continue
        delta, index = min(choices)
        available.remove(index)
        matches.append({"candidate_setup_id": detection["candidate_setup_id"],
                        "reference_index": index, "absolute_delay_minutes": round(delta / 60, 3)})
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
