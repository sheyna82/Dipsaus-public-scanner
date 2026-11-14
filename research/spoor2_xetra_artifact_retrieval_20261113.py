"""Fail-closed Xetra artifact retrieval for isolated research only.

No trading permissions, broker connectivity or automatic source attestation.
"""
import hashlib
import json
import socket
import ssl
from urllib.parse import urlsplit
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
        "url": SOURCES.get(kind) if isinstance(kind, str) else None, "retrieved_at_utc": None,
        "byte_count": None, "sha256": None, "bytes": None,
        "blocks": [], "failure_category": None, "http_status": None,
        "redirect_diagnostic": None,
    }
    if not isinstance(kind, str) or kind not in SOURCES:
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
    except urllib.error.HTTPError as exc:
        result["blocks"].append("XETRA_DOWNLOAD_FAILED")
        result["failure_category"] = "HTTP_ERROR"
        if exc.code in (301, 302, 303, 307, 308):
            target = exc.headers.get("Location") if exc.headers is not None else None
            if target:
                try:
                    parts = urlsplit(target)
                    source = urlsplit(SOURCES[kind])
                    target_hostname = parts.hostname
                except ValueError:
                    result["redirect_diagnostic"] = {
                        "location_present": True,
                        "malformed_location": True,
                        "target_not_followed": True,
                    }
                    result["http_status"] = exc.code
                    return result
                # Hash the exact header for later comparison without leaking
                # credentials, query strings, fragments or arbitrary paths.
                result["redirect_diagnostic"] = {
                    "location_present": True,
                    "absolute_https": parts.scheme == "https",
                    "same_hostname": target_hostname == source.hostname,
                    "location_sha256": hashlib.sha256(target.encode("utf-8")).hexdigest(),
                    "has_query": bool(parts.query),
                    "has_fragment": bool(parts.fragment),
                    "target_not_followed": True,
                }
            else:
                result["redirect_diagnostic"] = {
                    "location_present": False, "absolute_https": False,
                    "same_hostname": False, "target_not_followed": True,
                }
        result["http_status"] = exc.code if isinstance(exc.code, int) and 100 <= exc.code <= 599 else None
        return result
    except (TimeoutError, socket.timeout):
        result["blocks"].append("XETRA_DOWNLOAD_FAILED")
        result["failure_category"] = "TIMEOUT"
        return result
    except ssl.SSLError:
        result["blocks"].append("XETRA_DOWNLOAD_FAILED")
        result["failure_category"] = "TLS_ERROR"
        return result
    except urllib.error.URLError as exc:
        result["blocks"].append("XETRA_DOWNLOAD_FAILED")
        reason = exc.reason
        if isinstance(reason, (TimeoutError, socket.timeout)):
            result["failure_category"] = "TIMEOUT"
        elif isinstance(reason, ssl.SSLError):
            result["failure_category"] = "TLS_ERROR"
        elif isinstance(reason, socket.gaierror):
            result["failure_category"] = "DNS_ERROR"
        else:
            result["failure_category"] = "NETWORK_ERROR"
        return result
    except (OSError, ValueError):
        result["blocks"].append("XETRA_DOWNLOAD_FAILED")
        result["failure_category"] = "TRANSPORT_ERROR"
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
