"""DIPSAUS: deterministic, leak-resistant chronological research split planner.

This module plans splits only; it does not certify market data, run trades, or
claim independent out-of-sample evidence. All timestamps are UTC dates.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Sequence


@dataclass(frozen=True)
class Fold:
    train_start: date
    train_end: date
    validation_start: date
    validation_end: date
    embargo_days: int


def walk_forward_folds(
    trading_dates: Sequence[date],
    *,
    min_train_sessions: int = 504,
    validation_sessions: int = 126,
    embargo_sessions: int = 20,
    step_sessions: int = 126,
) -> list[Fold]:
    """Expanding train, purged boundary, fixed-size validation.

    Embargo is counted in observed sessions (not calendar days). All
    decision dates in training precede the embargo and validation.
    This protects fixed-horizon label overlap only if the caller sets
    embargo_sessions >= maximum holding/label horizon and accounts
    for any other forward-looking label dependencies.
    """
    if any(type(x) is not date for x in trading_dates):
        raise ValueError("trading_dates must contain datetime.date values")
    dates = list(trading_dates)
    if not dates or dates != sorted(set(dates)):
        raise ValueError("trading_dates must be strictly increasing and unique")
    if min_train_sessions < 1 or validation_sessions < 1 or step_sessions < 1:
        raise ValueError("training, validation and step lengths must be positive")
    if embargo_sessions < 0:
        raise ValueError("embargo_sessions must be nonnegative")
    folds = []
    start = min_train_sessions + embargo_sessions
    while start + validation_sessions <= len(dates):
        end_train_index = start - embargo_sessions - 1
        folds.append(Fold(
            train_start=dates[0],
            train_end=dates[end_train_index],
            validation_start=dates[start],
            validation_end=dates[start + validation_sessions - 1],
            embargo_days=embargo_sessions,
        ))
        start += step_sessions
    return folds


def check_disjoint(folds: Sequence[Fold]) -> bool:
    """Check temporal ordering and nonoverlap of validation intervals."""
    for f in folds:
        if not (f.train_start <= f.train_end < f.validation_start <= f.validation_end):
            return False
    return all(a.validation_end < b.validation_start for a, b in zip(folds, folds[1:]))
