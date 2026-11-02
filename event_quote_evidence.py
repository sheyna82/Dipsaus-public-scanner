"""Offline, fail-closed validation of observed event quote evidence.

This module never fetches prices or creates trading instructions.
"""
from datetime import datetime, timezone
from math import isfinite


def validated_event_quote(price, observed_at, source, now, max_age_seconds=120):
    """Return auditable quote evidence or None, with no implicit data filling."""
    if isinstance(price, bool) or not isinstance(price, (int, float)):
        return None
    if not isfinite(price) or price <= 0:
        return None
    if not isinstance(source, str) or not source.strip():
        return None
    if not isinstance(observed_at, str) or not isinstance(now, datetime):
        return None
    if now.tzinfo is None or now.utcoffset() is None:
        return None
    if isinstance(max_age_seconds, bool) or not isinstance(max_age_seconds, (int, float)):
        return None
    if not isfinite(max_age_seconds) or max_age_seconds <= 0:
        return None
    try:
        observed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    if observed.tzinfo is None or observed.utcoffset() is None:
        return None
    age = (now.astimezone(timezone.utc) - observed.astimezone(timezone.utc)).total_seconds()
    if not 0 <= age <= max_age_seconds:
        return None
    return {"price": float(price), "observed_at": observed.isoformat(),
            "source": source.strip(), "age_seconds": age}


def event_quote_metrics(price, observed_at, source, now, max_age_seconds=120):
    """Only a validated quote can satisfy the event research fresh_quote field.

    Returns a research metrics fragment; never supplies other missing evidence.
    """
    evidence = validated_event_quote(price, observed_at, source, now, max_age_seconds)
    return {"fresh_quote": evidence} if evidence is not None else {}
