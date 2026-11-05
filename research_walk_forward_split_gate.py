"""Research-only walk-forward holdout protocol; no market data or trading actions.

The caller must supply independently sourced, chronological observations.
A passing structural check is not evidence that the source is independent.
"""

from datetime import datetime


def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError("invalid_timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("invalid_timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone_required")
    return parsed


def validate_walk_forward_split(training, holdout, *, embargo_seconds=0):
    """Reject overlap, unordered records and labels unavailable at forecast time.

    Each row requires event_at (feature cutoff) and label_available_at.
    The embargo is measured from the last training label's availability
    to the first holdout event. This is a structural, not provenance, audit.
    """
    if not isinstance(embargo_seconds, int) or isinstance(embargo_seconds, bool) or embargo_seconds < 0:
        raise ValueError("invalid_embargo")
    if not isinstance(training, (list, tuple)) or not isinstance(holdout, (list, tuple)):
        raise ValueError("invalid_split")
    if not training or not holdout:
        raise ValueError("empty_split")

    def inspect(rows):
        previous = None
        output = []
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("invalid_row")
            event = _timestamp(row.get("event_at"))
            available = _timestamp(row.get("label_available_at"))
            feature_available_raw = row.get("feature_available_at")
            if feature_available_raw is not None:
                feature_available = _timestamp(feature_available_raw)
                if feature_available > event:
                    raise ValueError("feature_not_available_at_event")
            if available < event:
                raise ValueError("label_before_event")
            if previous is not None and event <= previous:
                raise ValueError("unordered_or_duplicate_events")
            previous = event
            output.append((event, available))
        return output

    train = inspect(training)
    test = inspect(holdout)
    if train[-1][0] >= test[0][0]:
        raise ValueError("train_holdout_overlap")
    from datetime import timedelta

    if max(available for _, available in train) + timedelta(seconds=embargo_seconds) > test[0][0]:
        raise ValueError("training_labels_not_available_before_holdout")
    return {
        "accepted": True,
        "training_events": len(train),
        "holdout_events": len(test),
        "independent_source_verified": False,
        "trade_ready": False,
    }
