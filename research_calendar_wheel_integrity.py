"""Fail-closed verification of a locally supplied calendar wheel and its SHA256.

Offline only. This does not install packages or certify transitive dependencies.
"""
import hashlib
from pathlib import Path


def verify_wheel(path, expected_sha256, *, expected_version="4.13.2"):
    if not isinstance(path, (str, Path)):
        raise ValueError("invalid_wheel_path")
    wheel = Path(path)
    if not wheel.is_file() or wheel.suffix != ".whl":
        raise ValueError("invalid_wheel_path")
    if not wheel.name.startswith("exchange_calendars-" + expected_version + "-"):
        raise ValueError("unexpected_wheel_version")
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64 or any(
            char not in "0123456789abcdef" for char in expected_sha256):
        raise ValueError("invalid_expected_hash")
    digest = hashlib.sha256()
    with wheel.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected_sha256:
        raise ValueError("wheel_hash_mismatch")
    return {"wheel_name": wheel.name, "sha256_verified": True,
            "dependency_audit_complete": False,
            "vulnerability_scan_complete": False,
            "production_approved": False}
