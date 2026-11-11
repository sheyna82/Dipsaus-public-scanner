"""Explicit outcome classification for the first real historical-price probe.

Never convert provider/network errors into zero prices or empty trading days.
"""
from urllib.error import HTTPError, URLError


def classify_price_probe_error(error):
    if isinstance(error, HTTPError):
        code = error.code
        return {"status": "http_error", "http_status": code,
                "data_verified": False, "retryable": code in (408, 429, 500, 502, 503, 504)}
    if isinstance(error, (URLError, TimeoutError, ConnectionError)):
        return {"status": "network_unavailable", "http_status": None,
                "data_verified": False, "retryable": True}
    if isinstance(error, (UnicodeError, ValueError)):
        return {"status": "invalid_provider_data", "http_status": None,
                "data_verified": False, "retryable": False}
    return {"status": "unexpected_failure", "http_status": None,
            "data_verified": False, "retryable": False}
