"""Local-only OHLCV provenance and benchmark-alignment preflight.

No downloads, provider trust, price repairs, live alerts or trading actions.
Structural PASS never verifies source rights, delistings or corporate actions.
"""
import hashlib
from pathlib import Path
from dipsaus_offline_ohlcv_csv import load_local_ohlcv_csv
from dipsaus_offline_history_quality import audit_price_history

MAX_FILE_BYTES = 10_000_000


def _sha256(path):
    p = Path(path)
    if not p.is_file() or p.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("invalid_file")
    h = hashlib.sha256()
    with p.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect_local_pair(stock_path, spy_path, *, expected_stock_sha256,
                       expected_spy_sha256):
    """Hashes must come from independently recorded source manifests."""
    result = {"status": "DATA_BLOCKED", "trade_ready": False,
              "independent_holdout_verified": False,
              "corporate_actions_verified": False, "provider_rights_verified": False}
    try:
        if (not isinstance(expected_stock_sha256, str)
                or not isinstance(expected_spy_sha256, str)
                or len(expected_stock_sha256) != 64 or len(expected_spy_sha256) != 64
                or any(c not in "0123456789abcdef" for c in expected_stock_sha256 + expected_spy_sha256)):
            raise ValueError("invalid_expected_hashes")
        stock_hash, spy_hash = _sha256(stock_path), _sha256(spy_path)
        if stock_hash != expected_stock_sha256 or spy_hash != expected_spy_sha256:
            raise ValueError("hash_mismatch")
        stock, spy = load_local_ohlcv_csv(stock_path), load_local_ohlcv_csv(spy_path)
        if not stock or not spy:
            raise ValueError("invalid_bars")
        if [x["date"] for x in stock] != [x["date"] for x in spy]:
            raise ValueError("unaligned_sessions")
        stock_findings = audit_price_history(stock)["findings"]
        spy_findings = audit_price_history(spy)["findings"]
        if stock_findings or spy_findings:
            raise ValueError("price_anomaly_review_required")
        result.update({"status": "STRUCTURAL_REVIEW_ONLY",
                       "stock_bars": len(stock), "benchmark_bars": len(spy),
                       "stock_sha256": stock_hash, "benchmark_sha256": spy_hash,
                       "aligned_sessions": True})
    except (OSError, ValueError, TypeError, OverflowError) as exc:
        result["reason"] = str(exc)
    return result
