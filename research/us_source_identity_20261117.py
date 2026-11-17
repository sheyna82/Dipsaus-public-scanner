"""Offline source identity metadata checks. Never establishes provider independence."""
from urllib.parse import urlsplit
import re

MIC = re.compile(r"^[A-Z0-9]{4}$")
SHA = re.compile(r"^[0-9a-fA-F]{64}$")


def review_source_identity(record):
    blocks = []
    if not isinstance(record, dict):
        return {"status": "UNKNOWN", "blocks": ["RECORD_MISSING"],
                "provider_independently_verified": False, "trade_ready": False}
    for key in ("provider_id", "dataset_id", "instrument_id", "mic",
                "retrieval_url", "retrieval_reference", "license_reference",
                "content_sha256"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            blocks.append("MISSING_" + key.upper())
    if "MISSING_MIC" not in blocks and not MIC.fullmatch(record["mic"]):
        blocks.append("INVALID_MIC_FORMAT")
    if "MISSING_CONTENT_SHA256" not in blocks and not SHA.fullmatch(record["content_sha256"]):
        blocks.append("INVALID_SHA256_FORMAT")
    if "MISSING_RETRIEVAL_URL" not in blocks:
        try:
            url = urlsplit(record["retrieval_url"])
            if url.scheme != "https" or not url.hostname or url.username or url.password or url.fragment:
                blocks.append("RETRIEVAL_URL_NOT_ACCEPTED")
        except ValueError:
            blocks.append("RETRIEVAL_URL_NOT_ACCEPTED")
    # These are only syntactic checks, not a trust registry or network verification.
    return {"status": "METADATA_COMPLETE_UNVERIFIED" if not blocks else "UNKNOWN",
            "blocks": sorted(set(blocks)), "provider_independently_verified": False,
            "license_verified": False, "mic_verified": False, "trade_ready": False}
