"""Point-in-time chronological research partitions; offline, no order signals.

The embargo excludes training events whose outcome windows cross a later split.
"""
from datetime import timedelta
from research_swing_event_dataset_audit import _utc


def partition_event_windows(records, *, validation_start, test_start, embargo_days=20):
    """Split on event availability, not hindsight outcome.

    Rows require available_at_utc and outcome_end_at_utc. Test is never used
    for fitting or model selection. Calendar-day embargo is conservative for
    3/5/10/15/20 trading-session outcomes, but not a substitute for session audit.
    """
    validation = _utc(validation_start)
    test = _utc(test_start)
    if validation >= test:
        raise ValueError("invalid_split_boundaries")
    if type(embargo_days) is not int or embargo_days < 0:
        raise ValueError("invalid_embargo")
    embargo = timedelta(days=embargo_days)
    groups = {"train": [], "validation": [], "test": [], "excluded": []}
    identities = set()
    for row in records:
        if not isinstance(row, dict):
            raise ValueError("invalid_record")
        available = _utc(row.get("available_at_utc"))
        end = _utc(row.get("outcome_end_at_utc"))
        if end <= available:
            raise ValueError("invalid_outcome_window")
        key = (row.get("symbol"), row.get("event_id"))
        if not all(isinstance(v, str) and v for v in key):
            raise ValueError("invalid_identity")
        if key in identities:
            raise ValueError("duplicate_event")
        identities.add(key)
        if available >= test:
            group = "test"
        elif available >= validation:
            group = "validation" if end + embargo < test else "excluded"
        else:
            group = "train" if end + embargo < validation else "excluded"
        groups[group].append(row)
    return {
        "counts": {name: len(items) for name, items in groups.items()},
        "groups": groups, "trade_ready": False,
    }
