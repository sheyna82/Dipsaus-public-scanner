"""Offline, ex-ante ordering comparison; no outcome-based candidate ranking."""
import hashlib
import json
from integrated_overlapping_capital_ledger import simulate

def compare_orders(candidates, capital_eur=50000, max_positions=6, same_day_cash_reuse=True):
    if not isinstance(candidates, list):
        raise ValueError("INVALID_CANDIDATES")
    seen = set()
    for c in candidates:
        ident = str(c["id"])
        if ident in seen:
            raise ValueError("DUPLICATE_CANDIDATE")
        seen.add(ident)
        if type(c.get("registered_priority")) not in (int, float) or c.get("priority_source_verified") is not True:
            raise ValueError("MISSING_EX_ANTE_PRIORITY")
        if c.get("priority_registered_before_entry") is not True:
            raise ValueError("LOOKAHEAD_PRIORITY_BLOCKED")
        if c.get("future_return") is not None or c.get("realized_pnl_eur") is not None:
            raise ValueError("FUTURE_OUTCOME_IN_SELECTION")
    by_time = sorted(candidates, key=lambda c: (c["entry_date"], str(c["id"])))
    by_priority = sorted(candidates, key=lambda c: (c["entry_date"], -c["registered_priority"], str(c["id"])))
    fingerprint_payload = {"schema": "ex_ante_selection_input_v1", "candidates": by_time,
                           "capital_eur": str(capital_eur), "max_positions": max_positions,
                           "same_day_cash_reuse": same_day_cash_reuse}
    try:
        canonical = json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("INVALID_FINGERPRINT_INPUT") from exc
    input_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    baseline = simulate(by_time, capital_eur=capital_eur, max_positions=max_positions, same_day_cash_reuse=same_day_cash_reuse)
    prioritized = simulate(by_priority, capital_eur=capital_eur, max_positions=max_positions, same_day_cash_reuse=same_day_cash_reuse)
    return {"status": "RESEARCH_ONLY_EX_ANTE_ORDER_COMPARISON",
            "trade_ready": False, "performance_superiority_proven": False,
            "same_day_cash_reuse": same_day_cash_reuse,
            "input_sha256": input_sha256, "fingerprint_schema": "ex_ante_selection_input_v1",
            "capital_eur": str(capital_eur), "max_positions": max_positions,
            "cash_policy": "exit_before_entry_same_day" if same_day_cash_reuse else "entry_before_exit_same_day",
            "baseline": {"accepted_ids": baseline["accepted_ids"], "rejected": baseline["rejected"]},
            "priority": {"accepted_ids": prioritized["accepted_ids"], "rejected": prioritized["rejected"]},
            "limitations": ["same-day entry ordering is a scenario assumption",
                            "priorities require independently verified historical registration",
                            "no outcome data used to rank entries"]}
