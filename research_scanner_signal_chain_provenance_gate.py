"""Research-only provenance gate for scanner signal -> notification -> trade proxy.

Does not read private state, fetch prices, or infer execution from a notification.
Unknown evidence is rejected rather than filled with assumptions.
"""
from datetime import datetime, timezone


def _utc(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None or dt.utcoffset() is None:
        return None
    return dt.astimezone(timezone.utc)


def audit_signal_chain(records):
    if not isinstance(records, (list, tuple)):
        raise ValueError("invalid_records")
    output = []
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("invalid_record")
        symbol = record.get("symbol")
        family = record.get("family")
        signal_id = record.get("signal_id")
        if not all(isinstance(x, str) and x.strip() for x in (symbol, family, signal_id)):
            raise ValueError("missing_identity")
        if signal_id in seen:
            raise ValueError("duplicate_signal_id")
        seen.add(signal_id)
        decision = _utc(record.get("decision_utc"))
        generated = _utc(record.get("generated_utc"))
        notified = _utc(record.get("provider_accepted_utc"))
        entry = _utc(record.get("entry_utc"))
        reasons = []
        if decision is None:
            reasons.append("unverified_decision_timestamp")
        if generated is None:
            reasons.append("unverified_generation_timestamp")
        if decision is not None and generated is not None and generated < decision:
            reasons.append("generation_before_decision")
        if notified is not None and (generated is None or notified < generated):
            reasons.append("provider_acceptance_before_generation_or_unverified")
        if entry is not None and (decision is None or entry <= decision):
            reasons.append("entry_before_or_at_decision")
        if record.get("decision_source_verified") is not True:
            reasons.append("decision_source_unverified")
        if record.get("signal_rule_version_verified") is not True:
            reasons.append("rule_version_unverified")
        if record.get("point_in_time_inputs_verified") is not True:
            reasons.append("point_in_time_inputs_unverified")
        if record.get("market_data_source_verified") is not True:
            reasons.append("market_data_unverified")
        if record.get("execution_verified") is not True:
            reasons.append("execution_unverified")
        if entry is None:
            reasons.append("entry_timestamp_unverified")
        if record.get("costs_and_currency_verified") is not True:
            reasons.append("costs_currency_unverified")
        # Provider acceptance does not establish receipt by a phone.
        phone_confirmed = record.get("phone_receipt_verified") is True
        provider_accepted = notified is not None
        if not provider_accepted:
            reasons.append("provider_acceptance_unverified")
        if not phone_confirmed:
            reasons.append("phone_receipt_unverified")
        # A historical signal can be studied without notification or execution.
        signal_reconstructable = all(x not in reasons for x in (
            "unverified_decision_timestamp", "unverified_generation_timestamp",
            "generation_before_decision", "decision_source_unverified",
            "rule_version_unverified", "point_in_time_inputs_unverified",
            "market_data_unverified"))
        trade_reconstructable = signal_reconstructable and not any(x in reasons for x in (
            "entry_before_or_at_decision", "execution_unverified",
            "entry_timestamp_unverified", "costs_currency_unverified"))
        output.append({"signal_id": signal_id, "symbol": symbol, "family": family,
                       "signal_reconstructable": signal_reconstructable,
                       "trade_reconstructable": trade_reconstructable,
                       "provider_accepted": provider_accepted,
                       "phone_receipt_verified": phone_confirmed,
                       "reasons": sorted(set(reasons))})
    return {"research_only": True, "trade_ready": False,
            "signal_count": len(output),
            "reconstructable_signals": sum(r["signal_reconstructable"] for r in output),
            "reconstructable_trades": sum(r["trade_reconstructable"] for r in output),
            "records": output}
