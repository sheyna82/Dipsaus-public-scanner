"""Chronological training eligibility: outcomes must be known strictly before cutoff.

Research only. No orders, no model selection, no test-set tuning.
"""
from .dipsaus_point_in_time_audit import parse_time


def partition_training_rows(rows, cutoff):
    """Return (eligible, purged, future, invalid), preserving input order.

    A training candidate is selected by decision_at < cutoff.
    Its outcome must be available strictly before cutoff; equality is purged.
    Rows with malformed or timezone-naive timestamps are quarantined.
    """
    boundary = parse_time(cutoff)
    eligible, purged, future, invalid = [], [], [], []
    for row in rows:
        try:
            decision = parse_time(row["decision_at"])
            outcome = parse_time(row["outcome_available_at"])
            if outcome < decision:
                invalid.append(row)
            elif decision >= boundary:
                future.append(row)
            elif outcome >= boundary:
                purged.append(row)
            else:
                eligible.append(row)
        except (KeyError, TypeError, ValueError, AttributeError):
            invalid.append(row)
    return eligible, purged, future, invalid
