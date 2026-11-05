"""Research-only snapshot of explicitly confirmed holdings; no broker cash inference or orders."""
import math


def reconcile_broker_positions(config, broker_positions, *, as_of_utc, now_utc=None, max_age_hours=24, complete_account_snapshot=False):
    """Strict research-only comparison. Broker evidence must be externally verified."""
    from datetime import datetime, timezone
    if not isinstance(as_of_utc, str):
        raise ValueError("INVALID_BROKER_TIMESTAMP")
    try:
        timestamp = datetime.fromisoformat(as_of_utc.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("INVALID_BROKER_TIMESTAMP") from None
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("INVALID_BROKER_TIMESTAMP")
    if now_utc is None:
        now = datetime.now(timezone.utc)
    elif isinstance(now_utc, datetime) and now_utc.tzinfo is not None and now_utc.utcoffset() is not None:
        now = now_utc.astimezone(timezone.utc)
    else:
        raise ValueError("INVALID_NOW")
    if not isinstance(max_age_hours, (int, float)) or isinstance(max_age_hours, bool) or not math.isfinite(max_age_hours) or max_age_hours <= 0:
        raise ValueError("INVALID_MAX_AGE")
    if timestamp > now:
        raise ValueError("FUTURE_BROKER_TIMESTAMP")
    evidence_age_hours = (now - timestamp).total_seconds() / 3600
    evidence_fresh = evidence_age_hours <= max_age_hours
    if not isinstance(complete_account_snapshot, bool):
        raise ValueError("INVALID_COMPLETENESS_CLAIM")
    if not isinstance(broker_positions, dict):
        raise ValueError("INVALID_BROKER_POSITIONS")
    configured = snapshot(config)
    verified = {}
    for symbol, shares in broker_positions.items():
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("INVALID_BROKER_SYMBOL")
        if (not isinstance(shares, (int, float)) or isinstance(shares, bool)
                or not math.isfinite(shares) or shares < 0):
            raise ValueError("INVALID_BROKER_SHARES")
        if shares > 0:
            verified[symbol] = shares
    configured_shares = {symbol: item["shares_configured"]
                         for symbol, item in configured["configured_active_positions"].items()}
    mismatches = {symbol: {"configured": configured_shares.get(symbol, 0),
                           "broker": verified.get(symbol, 0)}
                  for symbol in sorted(set(configured_shares) | set(verified))
                  if configured_shares.get(symbol, 0) != verified.get(symbol, 0)}
    return {"status": "RESEARCH_ONLY_BROKER_RECONCILIATION",
            "trade_ready": False, "automatic_orders": False,
            "broker_as_of_utc": timestamp.isoformat(),
            "broker_evidence_fresh": evidence_fresh,
            "broker_evidence_age_hours": round(evidence_age_hours, 3),
            "broker_evidence_max_age_hours": max_age_hours,
            "broker_verified_claim": False,
            "complete_account_snapshot_claim": complete_account_snapshot,
            "completeness_independently_verified": False,
            "requires_evidence_authentication": True,
            "broker_open_position_count": len(verified),
            "broker_remaining_slots": max(0, configured["max_positions"] - len(verified)),
            "position_mismatches": mismatches,
            "positions_agree": not mismatches if complete_account_snapshot else None,
            "comparison_is_partial": not complete_account_snapshot,
            "portfolio_capacity_usable": False,
            "actual_cash_eur": None,
            "capital_adequacy_verified": False}


def snapshot(config, *, max_positions=6, tranche_eur=3500.0):
    if not isinstance(config, dict) or not isinstance(config.get("positions"), dict):
        raise ValueError("INVALID_POSITIONS")
    if not isinstance(max_positions, int) or isinstance(max_positions, bool) or max_positions < 1:
        raise ValueError("INVALID_CAPACITY")
    if not isinstance(tranche_eur, (int, float)) or isinstance(tranche_eur, bool) or not math.isfinite(tranche_eur) or tranche_eur <= 0:
        raise ValueError("INVALID_TRANCHE")
    active = {}
    closed = []
    unknown = []
    for symbol, item in config["positions"].items():
        if not isinstance(symbol, str) or not symbol or not isinstance(item, dict):
            raise ValueError("INVALID_HOLDING")
        status = item.get("status")
        if status == "CLOSED-SWING":
            closed.append(symbol)
            continue
        shares = item.get("shares")
        if (not isinstance(shares, (int, float)) or isinstance(shares, bool)
                or not math.isfinite(shares) or shares <= 0):
            raise ValueError("INVALID_ACTIVE_SHARES")
        # A watch configuration is not proof that broker positions still exist.
        active[symbol] = {"shares_configured": shares, "status": status,
                          "broker_verified": False}
        unknown.append(symbol)
    return {
        "status": "RESEARCH_ONLY_UNVERIFIED_HOLDINGS",
        "trade_ready": False,
        "automatic_orders": False,
        "max_positions": max_positions,
        "configured_active_count": len(active),
        "configured_remaining_slots": max(0, max_positions-len(active)),
        "configured_over_capacity": len(active) > max_positions,
        "closed_historical_symbols": sorted(closed),
        "configured_active_positions": active,
        "broker_verification_required": sorted(unknown),
        "actual_cash_eur": None,
        "actual_available_capital_eur": None,
        "actual_portfolio_market_value_eur": None,
        "tranche_reference_eur": float(tranche_eur),
        "capital_adequacy_verified": False,
    }
