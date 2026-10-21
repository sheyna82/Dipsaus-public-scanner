"""Offline chronological holdout split with embargo for overlapping forward horizons.

Input observations must contain signal_time and complete future bars.
This splits research samples; it does not train a model or validate data vendors.
"""
from datetime import date, datetime


def chronological_holdout(observations, *, holdout_fraction=0.25, embargo_sessions=10):
    if (not isinstance(observations, (list, tuple)) or
            type(holdout_fraction) is not float or not 0 < holdout_fraction < 1 or
            type(embargo_sessions) is not int or embargo_sessions < 0):
        return None
    keyed = []
    ids = set()
    for obs in observations:
        if not isinstance(obs, dict):
            return None
        ident = obs.get("id")
        try:
            dt = datetime.fromisoformat(obs["signal_time"])
            if dt.tzinfo is None or dt.utcoffset() is None:
                return None
            bars = obs["bars"]
            if not isinstance(bars, list) or len(bars) < 2:
                return None
            last_date = date.fromisoformat(bars[-1]["date"])
            if last_date < dt.date():
                return None
        except (KeyError, ValueError, TypeError, AttributeError):
            return None
        if not isinstance(ident, str) or not ident or ident in ids:
            return None
        ids.add(ident)
        keyed.append((dt, ident, last_date, obs))
    if len(keyed) < 4:
        return None
    keyed.sort(key=lambda item: (item[0], item[1]))
    count_holdout = max(1, int(len(keyed) * holdout_fraction + 0.999999))
    boundary = len(keyed) - count_holdout
    holdout_start = keyed[boundary][0]
    # All records at the boundary timestamp go to holdout, never both partitions.
    while boundary > 0 and keyed[boundary - 1][0] == holdout_start:
        boundary -= 1
    holdout = keyed[boundary:]
    if not holdout or boundary == 0:
        return None
    # Embargo removes the final N signal sessions before holdout; use distinct
    # signal dates, not calendar days, so weekends do not change its meaning.
    prior_dates = sorted({item[0].date() for item in keyed[:boundary]})
    forbidden = set(prior_dates[-embargo_sessions:]) if embargo_sessions else set()
    train = []
    purged = []
    for item in keyed[:boundary]:
        if item[0].date() in forbidden or item[2] >= holdout_start.date():
            purged.append(item[1])
        else:
            train.append(item[3])
    return {"development": train, "holdout": [item[3] for item in holdout],
            "purged_ids": purged, "holdout_start": holdout_start.isoformat(),
            "embargo_signal_dates": embargo_sessions,
            "research_only": True, "trade_ready": False,
            "warning": "Caller-supplied future bars; no independently verified data or model performance."}
