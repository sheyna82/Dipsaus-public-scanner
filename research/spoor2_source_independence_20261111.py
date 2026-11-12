"""Offline evidence-source independence gate for Spoor 2.

A source label or verified flag is not independent evidence. Require an
inspectable source record, a distinct provider identity, and a separate
source family for broker quote vs technical levels. No network or trades.
"""
from urllib.parse import urlparse, parse_qsl, urlencode
import re

_UNRESERVED = frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~')

def _canonical_path(path):
    # RFC 3986: decode only unreserved octets; encoded slash remains distinct.
    def normalize(match):
        char = chr(int(match.group(1), 16))
        return char if char in _UNRESERVED else '%' + match.group(1).upper()
    return re.sub(r'%([0-9a-fA-F]{2})', normalize, path).rstrip('/') or '/'


def audit_source_independence(evidence):
    blocks = []
    if not isinstance(evidence, dict):
        return {"status": "BLOCKED", "blocks": ["INVALID_EVIDENCE"], "trade_ready": False}
    records = {}
    record_locations = {}
    for role in ("broker", "invalidation", "resistance"):
        record = evidence.get(role + "_evidence")
        if not isinstance(record, dict):
            blocks.append(role.upper() + "_EVIDENCE_MISSING")
            continue
        provider = record.get("provider_id")
        family = record.get("source_family")
        record_id = record.get("source_record_id")
        url = record.get("source_url")
        if not all(isinstance(v, str) and v.strip() for v in (provider, family, record_id, url)):
            blocks.append(role.upper() + "_PROVENANCE_INCOMPLETE")
            continue
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            blocks.append(role.upper() + "_SOURCE_URL_INVALID")
            continue
        records[role] = (provider.strip().lower(), family.strip().lower(), record_id.strip())
        try:
            port = parsed.port
        except ValueError:
            blocks.append(role.upper() + "_SOURCE_URL_INVALID")
            continue
        # Canonicalize harmless URL variations without collapsing distinct
        # query-addressed exchange records into the same evidence location.
        host = parsed.hostname.lower().rstrip(".")
        authority = host if port in (None, 443) else host + ":" + str(port)
        query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
        record_locations[role] = (
            record_id.strip(),
            authority,
            _canonical_path(parsed.path),
            query,
        )
    if len(records) == 3 and len(record_locations) == 3:
        broker, invalidation, resistance = (records[k] for k in ("broker", "invalidation", "resistance"))
        if broker[0] in (invalidation[0], resistance[0]):
            blocks.append("BROKER_TECHNICAL_PROVIDER_NOT_INDEPENDENT")
        if broker[1] in (invalidation[1], resistance[1]):
            blocks.append("BROKER_TECHNICAL_SOURCE_FAMILY_NOT_INDEPENDENT")
        if (len(set(records.values())) != 3
                or len({item[0] for item in record_locations.values()}) != 3
                or len({item[1:] for item in record_locations.values()}) != 3):
            blocks.append("SOURCE_RECORD_REUSED")
    return {"status": "PROVENANCE_RECORDED_REQUIRES_EXTERNAL_VERIFICATION" if not blocks else "BLOCKED",
            "blocks": blocks, "trade_ready": False, "order_placement_enabled": False}
