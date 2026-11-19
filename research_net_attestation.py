"""Research-only provenance envelope for net EUR evidence.

This checks claimed metadata and timestamps; it does NOT independently
authenticate a broker, issuer, source, fee schedule or market data.
"""
from datetime import datetime, timezone
from research_net_bridge import evaluate_verified_research_evidence

FIELDS = {
    "broker_quote": ("broker_ask", "broker_bid"),
    "technical_levels": ("invalidation", "target"),
    "fees": ("buy_fee_eur", "sell_fee_eur"),
    "fx": ("fx_eur_per_unit", "fx_buy_fee_rate", "fx_sell_fee_rate"),
    "slippage": ("buy_slippage_per_share", "sell_slippage_per_share"),
}
MAX_AGE_SECONDS = {
    "broker_quote": 120,
    "technical_levels": 86400,
    "fees": 30 * 86400,
    "fx": 300,
    "slippage": 86400,
}
BLOCKED = {"trade_ready": False, "order_placement_enabled": False}


def _parse_time(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.utcoffset() is not None else None
    except (ValueError, TypeError, OverflowError):
        return None


def evaluate_attested_scenario(evidence, attestations, *, market, now=None,
                               budget_eur=3500):
    """Fail closed on missing, stale, contradictory or untraceable metadata.

    Attestations have source_id, observed_utc, verified=True, and fields.
    Source IDs are caller claims, not independent authenticity checks.
    """
    if not isinstance(evidence, dict) or not isinstance(attestations, dict):
        return {**BLOCKED, "status": "DATA_BLOCKED", "reason": "INVALID_ENVELOPE"}
    now = datetime.now(timezone.utc) if now is None else now
    if not isinstance(now, datetime) or now.utcoffset() is None:
        return {**BLOCKED, "status": "DATA_BLOCKED", "reason": "INVALID_CLOCK"}
    now = now.astimezone(timezone.utc)
    for group, fields in FIELDS.items():
        item = attestations.get(group)
        if not isinstance(item, dict):
            return {**BLOCKED, "status": "ATTESTATION_BLOCKED",
                    "reason": "MISSING_ATTESTATION", "group": group}
        source = item.get("source_id")
        if not isinstance(source, str) or not source.strip() or len(source) > 256:
            return {**BLOCKED, "status": "ATTESTATION_BLOCKED",
                    "reason": "INVALID_SOURCE_ID", "group": group}
        if item.get("verified") is not True:
            return {**BLOCKED, "status": "ATTESTATION_BLOCKED",
                    "reason": "NOT_VERIFIED", "group": group}
        timestamp = _parse_time(item.get("observed_utc"))
        if timestamp is None:
            return {**BLOCKED, "status": "ATTESTATION_BLOCKED",
                    "reason": "INVALID_TIMESTAMP", "group": group}
        age = (now - timestamp).total_seconds()
        if age < -30 or age > MAX_AGE_SECONDS[group]:
            return {**BLOCKED, "status": "ATTESTATION_BLOCKED",
                    "reason": "STALE_OR_FUTURE", "group": group}
        declared = item.get("fields")
        if not isinstance(declared, dict) or set(declared) != set(fields):
            return {**BLOCKED, "status": "ATTESTATION_BLOCKED",
                    "reason": "FIELD_SET_MISMATCH", "group": group}
        for field in fields:
            if field not in evidence or type(declared[field]) is not type(evidence[field]) or declared[field] != evidence[field]:
                return {**BLOCKED, "status": "ATTESTATION_BLOCKED",
                        "reason": "VALUE_MISMATCH", "group": group, "field": field}
    result = evaluate_verified_research_evidence(evidence, market=market,
                                                 budget_eur=budget_eur)
    return {**result, "attestation_metadata_checked": True,
            "source_authenticity_independently_verified": False,
            "trade_ready": False, "order_placement_enabled": False}
