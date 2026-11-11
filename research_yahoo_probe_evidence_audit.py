"""Audit stored Yahoo evidence; metadata is not independent market authentication."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from research_yahoo_chart_daily import parse_yahoo_chart_daily


def audit_yahoo_probe(root, symbol):
    root = Path(root)
    if not isinstance(symbol, str) or not symbol.isalnum():
        raise ValueError("invalid_symbol")
    meta = json.loads((root / f"yahoo-{symbol}-validation.json").read_text())
    if meta.get("provider") != "yahoo_chart" or meta.get("symbol") != symbol:
        raise ValueError("probe_identity_mismatch")
    if meta.get("status") != "normalized_unverified":
        return {"symbol": symbol, "accepted": False, "trade_ready": False}
    raw = (root / f"yahoo-{symbol}-raw.json").read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != meta.get("raw_sha256"):
        raise ValueError("raw_payload_hash_mismatch")
    parsed = parse_yahoo_chart_daily(json.loads(raw), expected_symbol=symbol)
    normalized = json.loads((root / f"yahoo-{symbol}-normalized.json").read_text())
    if normalized != parsed:
        raise ValueError("normalized_price_mismatch")
    stamp = datetime.fromisoformat(meta["retrieved_at_utc"])
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("retrieval_timezone_required")
    retrieval_day = stamp.astimezone(ZoneInfo("America/New_York")).date().isoformat()
    if any(r["date"] > retrieval_day for r in parsed):
        raise ValueError("future_market_session_in_probe")
    prior = [r for r in parsed if r["date"] < retrieval_day]
    if not prior:
        raise ValueError("no_prior_session_available")
    return {"symbol": symbol, "accepted": True, "raw_sha256": digest,
            "retrieved_at_utc": stamp.isoformat(),
            "last_conservatively_eligible_session": prior[-1]["date"],
            "same_day_rows_excluded": len(parsed) - len(prior),
            "source_authenticated_independently": False,
            "publication_time_verified": False,
            "prospective_candidate_registered": False, "trade_ready": False}
