"""Fail-closed Xetra artifact retrieval for isolated research only.

No trading permissions, broker connectivity or automatic source attestation.
"""
import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone

SOURCES = {
    "csv": "https://www.cashmarket.deutsche-boerse.com/resource/blob/1528/dc073b6568606b91bfcfe8a7328d6c4f/data/t7-xetr-allTradableInstruments.csv",
    "zip": "https://www.cashmarket.deutsche-boerse.com/resource/blob/1542/6c68544124aceb09a250f8cc8411c58c/data/RDF_StaticData_xetr.zip",
}
MAX_BYTES = 30_000_000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def retrieve_xetra_artifact(kind, opener=None):
    """Return bounded original bytes and non-attesting metadata, or a blocked result."""
    result = {
        "status": "BLOCKED", "source_attested": False,
        "instrument_segment_verified": False, "broker_route_verified": False,
        "trade_ready": False, "order_placement_enabled": False,
        "url": SOURCES.get(kind), "retrieved_at_utc": None,
        "byte_count": None, "sha256": None, "bytes": None,
        "blocks": [],
    }
    if kind not in SOURCES:
        result["blocks"].append("UNKNOWN_XETRA_ARTIFACT")
        return result
    opener = opener or urllib.request.build_opener(NoRedirect())
    try:
        request = urllib.request.Request(
            SOURCES[kind], headers={"User-Agent": "DIPSAUS-research-source-audit/1.0"}
        )
        with opener.open(request, timeout=15) as response:
            if response.geturl() != SOURCES[kind] or response.status != 200:
                result["blocks"].append("XETRA_URL_OR_HTTP_STATUS_MISMATCH")
                return result
            declared = response.headers.get("Content-Length")
            if declared is not None and (not declared.isdecimal() or int(declared) > MAX_BYTES):
                result["blocks"].append("XETRA_SIZE_LIMIT")
                return result
            chunks, size = [], 0
            while True:
                chunk = response.read(min(65536, MAX_BYTES + 1 - size))
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_BYTES:
                    result["blocks"].append("XETRA_SIZE_LIMIT")
                    return result
                chunks.append(chunk)
            data = b"".join(chunks)
            if not data:
                result["blocks"].append("EMPTY_XETRA_ARTIFACT")
                return result
            result.update(bytes=data, byte_count=len(data),
                          sha256=hashlib.sha256(data).hexdigest(),
                          retrieved_at_utc=datetime.now(timezone.utc).isoformat())
    except (urllib.error.URLError, OSError, TimeoutError, ValueError) as exc:
        result["blocks"].append("XETRA_DOWNLOAD_FAILED")
        return result
    result["blocks"].append("ORIGINAL_SOURCE_NOT_INDEPENDENTLY_ATTESTED")
    return result


def public_metadata(result):
    """Strip raw bytes from a JSON-safe, permanently blocked research record."""
    return {key: value for key, value in result.items() if key != "bytes"}


if __name__ == "__main__":
    for name in SOURCES:
        result = retrieve_xetra_artifact(name)
        print(json.dumps({"artifact": name, **public_metadata(result)}, sort_keys=True))
