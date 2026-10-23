"""Offline point-in-time provenance audit for historical research features.

The caller supplies feature observation and publication timestamps. This is a
necessary consistency check, NOT proof that the underlying vendor data was
historically available or free of revisions.
"""
from datetime import datetime, timezone


def audit_asof_features(signal_time, features):
    def parse(value):
        if not isinstance(value, str):
            return None
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return None
        if dt.tzinfo is None or dt.utcoffset() is None:
            return None
        return dt.astimezone(timezone.utc)

    signal = parse(signal_time)
    if signal is None or not isinstance(features, dict) or not features:
        return None
    rejected, accepted = [], []
    for name, record in features.items():
        if not isinstance(name, str) or not name or not isinstance(record, dict):
            return None
        observed = parse(record.get("observed_at"))
        published = parse(record.get("published_at"))
        if observed is None or published is None or published < observed:
            rejected.append({"feature": name, "reason": "invalid_provenance"})
        elif published > signal:
            rejected.append({"feature": name, "reason": "future_publication"})
        else:
            accepted.append(name)
    return {"asof_pass": not rejected, "accepted_features": sorted(accepted),
            "rejected_features": rejected, "signal_time": signal.isoformat(),
            "research_only": True, "trade_ready": False,
            "order_instruction": None,
            "warning": "Caller-attested timestamps; no independent point-in-time vendor verification."}
