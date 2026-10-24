"""Research-only provenance checklist for real event study observations.

A filled source label is not source authentication. This gate accepts a
record only when its URL, observation time, retrieval time, and checksum are
present and internally consistent; independent verification remains separate.
"""
from datetime import datetime, timezone
import re

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def audit_market_observation(record, as_of_timestamp_utc):
    """Check an externally supplied immutable observation envelope."""
    required = ("symbol", "observation_timestamp_utc", "retrieved_at_utc",
                "source_url", "content_sha256", "exchange", "currency")
    missing = [k for k in required if not isinstance(record.get(k), str)
               or not record[k].strip()]
    if missing:
        raise ValueError("missing_provenance_fields:" + ",".join(missing))
    if not record["source_url"].startswith("https://"):
        raise ValueError("source_must_be_https")
    if not _SHA256.fullmatch(record["content_sha256"]):
        raise ValueError("invalid_content_digest")

    def timestamp(value):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValueError("invalid_provenance_timestamp") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("provenance_timezone_required")
        return parsed.astimezone(timezone.utc)

    observed = timestamp(record["observation_timestamp_utc"])
    retrieved = timestamp(record["retrieved_at_utc"])
    cutoff = timestamp(as_of_timestamp_utc)
    if not observed <= retrieved <= cutoff:
        raise ValueError("provenance_temporal_order_invalid")
    return {
        "symbol": record["symbol"],
        "observation_timestamp_utc": observed.isoformat(),
        "retrieved_at_utc": retrieved.isoformat(),
        "source_url": record["source_url"],
        "content_sha256": record["content_sha256"],
        "exchange": record["exchange"],
        "currency": record["currency"],
        "provenance_envelope_valid": True,
        "digest_recomputed_against_source": False,
        "source_authenticity_verified": False,
        "exchange_calendar_verified": False,
        "trade_ready": False,
    }
