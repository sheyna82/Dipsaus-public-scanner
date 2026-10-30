"""Research-only walk-forward split with purge and embargo.

Dates denote completed, timestamp-attested sample outcome windows. No outcome
may cross the training/test boundary. This module partitions metadata only:
it never trains or optimizes a model on test results.
"""
from datetime import date, timedelta


def _date(value):
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise ValueError("invalid_sample_date") from None


def purged_walk_forward_split(samples, *, test_start, test_end,
                              embargo_calendar_days=0):
    if (isinstance(embargo_calendar_days, bool) or
            not isinstance(embargo_calendar_days, int) or
            embargo_calendar_days < 0):
        raise ValueError("invalid_embargo")
    first, last = _date(test_start), _date(test_end)
    if last < first:
        raise ValueError("invalid_test_window")
    if not isinstance(samples, (list, tuple)):
        raise ValueError("invalid_samples")
    seen = set()
    train, test, excluded = [], [], []
    train_cutoff = first - timedelta(days=embargo_calendar_days)
    for item in samples:
        if not isinstance(item, dict):
            raise ValueError("invalid_sample")
        sample_id = item.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id or sample_id in seen:
            raise ValueError("duplicate_or_invalid_sample")
        seen.add(sample_id)
        entry, outcome = _date(item.get("entry_date")), _date(item.get("outcome_date"))
        if outcome <= entry:
            raise ValueError("invalid_outcome_window")
        if first <= entry <= last:
            if outcome <= last:
                test.append(sample_id)
            else:
                excluded.append({"sample_id": sample_id,
                                 "reason": "test_outcome_after_window"})
        elif outcome < train_cutoff:
            train.append(sample_id)
        else:
            excluded.append({"sample_id": sample_id,
                             "reason": "boundary_overlap_or_future"})
    return {
        "research_only": True, "trade_ready": False,
        "training_sample_ids": train, "test_sample_ids": test,
        "excluded_samples": excluded,
        "embargo_calendar_days": embargo_calendar_days,
        "outcome_provenance_verified": False,
        "test_data_used_for_training": False,
    }
