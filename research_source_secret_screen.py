"""Conservative pre-publication secret screening for research evidence.

Heuristic only: passing does not prove that source bytes contain no secrets.
No data is logged in errors. Never publish rejected bytes.
"""
import re

_SECRET_PATTERNS = (
    re.compile(rb'(?i)(?:api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|authorization|password|secret[_-]?key)\s*["\x27]?\s*[:=]\s*["\x27]?\s*[^\s,"\x27}]{4,}'),
    re.compile(rb'(?i)bearer\s+[a-z0-9._~+/-]{8,}'),
    re.compile(rb'gh[pousr]_[A-Za-z0-9_]{20,}'),
)


def reject_obvious_secrets(source_bytes):
    if not isinstance(source_bytes, bytes) or not source_bytes:
        raise ValueError("invalid_source_bytes")
    if any(pattern.search(source_bytes) for pattern in _SECRET_PATTERNS):
        raise ValueError("possible_secret_in_source_bytes")
    return {"secret_screen": "no_known_secret_pattern_detected",
            "secret_free_proven": False, "safe_to_publish_proven": False}
