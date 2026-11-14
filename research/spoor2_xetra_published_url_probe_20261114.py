"""Read-only, no-redirect probe of independently published Xetra URLs.

Never attests source bytes or authorizes trades. Does not follow redirects.
"""
import hashlib
import json
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from research.spoor2_xetra_artifact_retrieval_20261113 import NoRedirect

PUBLISHED = {
    "csv": "https://www.cashmarket.deutsche-boerse.com/resource/blob/1528/b52ea43a2edac92e8283d40645d1c076/data/t7-xetr-allTradableInstruments.csv",
    "zip": "https://www.cashmarket.deutsche-boerse.com/resource/blob/1542/6ddad5f38f99a491ee1ebe750759e833/data/RDF_StaticData_xetr.zip",
}


def probe_published_url(kind, opener=None):
    result = {
        "kind": kind if isinstance(kind, str) else None,
        "status": "BLOCKED", "source_attested": False,
        "trade_ready": False, "order_placement_enabled": False,
        "http_status": None, "location_sha256": None,
        "redirect_target_class": None,
        "redirect_not_followed": True, "failure_category": None,
    }
    if not isinstance(kind, str) or kind not in PUBLISHED:
        result["failure_category"] = "INVALID_KIND"
        return result
    opener = opener or urllib.request.build_opener(NoRedirect())
    request = urllib.request.Request(
        PUBLISHED[kind], method="HEAD",
        headers={"User-Agent": "DIPSAUS-research-source-audit/1.0"},
    )
    try:
        with opener.open(request, timeout=15) as response:
            if response.geturl() != PUBLISHED[kind]:
                result["failure_category"] = "UNEXPECTED_REDIRECT"
                return result
            result["http_status"] = response.status
    except urllib.error.HTTPError as exc:
        result["http_status"] = exc.code if isinstance(exc.code, int) else None
        if exc.code in (301, 302, 303, 307, 308):
            location = exc.headers.get("Location") if exc.headers else None
            if location:
                result["location_sha256"] = hashlib.sha256(location.encode("utf-8")).hexdigest()
                try:
                    target = urlsplit(location)
                    source = urlsplit(PUBLISHED[kind])
                    safe = (target.scheme == "https" and target.netloc == source.netloc
                            and target.username is None and target.password is None
                            and target.port is None and not target.query and not target.fragment
                            and target.path.startswith("/resource/blob/")
                            and "%" not in target.path and chr(92) not in target.path
                            and not any(part in (".", "..") for part in target.path.split("/")))
                    result["redirect_target_class"] = ("SAME_HOST_BLOB_PATH_UNATTESTED" if safe
                                                       else "OTHER_OR_UNSAFE")
                except ValueError:
                    result["redirect_target_class"] = "MALFORMED"
        result["failure_category"] = "HTTP_ERROR"
    except (OSError, ValueError):
        result["failure_category"] = "TRANSPORT_ERROR"
    return result


if __name__ == "__main__":
    for kind in PUBLISHED:
        print(json.dumps(probe_published_url(kind), sort_keys=True))
