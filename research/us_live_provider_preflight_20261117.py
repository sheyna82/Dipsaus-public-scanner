"""Offline, fail-closed preflight for a future private US market-data probe.

Never reads environment variables, credentials, network, or licensed market data.
Self-declared metadata is a checklist, not a license or access attestation.
"""
from urllib.parse import urlsplit

def review_live_provider_preflight(record):
    blocks = []
    if not isinstance(record, dict):
        record = {}
    for field in ("provider", "account_plan_reference", "entitlement_reference",
                  "license_scope_reference", "private_execution_boundary",
                  "credential_storage_reference", "data_retention_policy_reference"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            blocks.append("MISSING_" + field.upper())
    endpoint = record.get("endpoint")
    if not isinstance(endpoint, str) or not endpoint:
        blocks.append("ENDPOINT_MISSING")
    else:
        try:
            url = urlsplit(endpoint)
            if (url.scheme != "https" or not url.hostname or
                    url.username is not None or url.password is not None or
                    url.query or url.fragment or any(ch.isspace() for ch in endpoint)):
                blocks.append("ENDPOINT_UNSAFE")
        except ValueError:
            blocks.append("ENDPOINT_UNSAFE")
    if record.get("public_ci_live_data") is not False:
        blocks.append("PUBLIC_CI_LIVE_DATA_NOT_DISABLED")
    if record.get("public_logs_contain_market_data") is not False:
        blocks.append("PUBLIC_LOG_MARKET_DATA_NOT_DISABLED")
    if record.get("credential_in_source") is not False:
        blocks.append("CREDENTIAL_IN_SOURCE_NOT_DISABLED")
    # A complete form still cannot independently verify contractual rights.
    blocks.extend(("ACCOUNT_ENTITLEMENT_NOT_INDEPENDENTLY_VERIFIED",
                   "DATA_LICENSE_NOT_INDEPENDENTLY_VERIFIED",
                   "PRIVATE_RUNTIME_NOT_ATTESTED"))
    return {"status": "LIVE_PROBE_BLOCKED", "blocks": sorted(set(blocks)),
            "network_access": False, "credential_access": False,
            "trade_ready": False, "notify": False, "automatic_orders": False}
