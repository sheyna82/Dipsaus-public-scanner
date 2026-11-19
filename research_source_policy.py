"""Research-only evidence provenance policy; no external authentication.

A source label or an assertion from an upstream process is never proof of
broker execution pricing, fee schedule, or independent technical validation.
"""
from urllib.parse import urlsplit

BROKER_GROUPS = frozenset(("broker_quote", "fees"))
PUBLIC_PROVIDER_HOSTS = frozenset((
    "query1.finance.yahoo.com", "query2.finance.yahoo.com",
    "stooq.com", "www.stooq.com", "api.nasdaq.com",
    "www.nasdaqtrader.com",
))


def classify_source(source):
    """Classify source *claims*, not source authenticity."""
    if not isinstance(source, dict):
        return "UNKNOWN"
    kind = source.get("kind")
    if kind not in ("BROKER", "PUBLIC_PROVIDER", "EXCHANGE",
                    "ISSUER", "MANUAL_RESEARCH"):
        return "UNKNOWN"
    url = source.get("url")
    if url is not None:
        if not isinstance(url, str):
            return "UNKNOWN"
        try:
            parsed = urlsplit(url)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                return "UNKNOWN"
        except ValueError:
            return "UNKNOWN"
        if parsed.hostname.lower() in PUBLIC_PROVIDER_HOSTS:
            return "PUBLIC_PROVIDER"
    return kind


def assess_provenance_claims(attestations, source_registry):
    """Fail closed on source conflicts and missing independent confirmation.

    The registry is untrusted caller metadata. A passing assessment means
    only that the declared provenance is structurally consistent; it cannot
    authenticate a broker or independently corroborate prices.
    """
    blocked = {"status": "PROVENANCE_BLOCKED",
               "source_authenticity_independently_verified": False,
               "trade_ready": False, "order_placement_enabled": False}
    if not isinstance(attestations, dict) or not isinstance(source_registry, dict):
        return {**blocked, "reason": "INVALID_REGISTRY"}
    required = ("broker_quote", "technical_levels", "fees", "fx", "slippage")
    for group in required:
        item = attestations.get(group)
        if not isinstance(item, dict):
            return {**blocked, "reason": "MISSING_ATTESTATION", "group": group}
        source_id = item.get("source_id")
        source = source_registry.get(source_id) if isinstance(source_id, str) else None
        kind = classify_source(source)
        if kind == "UNKNOWN":
            return {**blocked, "reason": "UNKNOWN_SOURCE", "group": group}
        if group in BROKER_GROUPS and kind != "BROKER":
            return {**blocked, "reason": "NOT_BROKER_EVIDENCE", "group": group}
        if group == "technical_levels" and kind == "BROKER":
            # A quote screen alone does not independently verify chart levels.
            return {**blocked, "reason": "TECHNICAL_LEVELS_NOT_INDEPENDENT",
                    "group": group}
    return {"status": "PROVENANCE_CLAIMS_CONSISTENT",
            "source_authenticity_independently_verified": False,
            "trade_ready": False, "order_placement_enabled": False}
