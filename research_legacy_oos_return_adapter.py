"""Explicitly adapt old OOS net-return records to new gross-return contract.

Old candidate_feature_oos portfolio_oos_pair produces entry_day/exit_day
as Unix epoch days and net_return_pct with COST_BPS already deducted.
The new cash simulator expects gross realized_return_pct and subtracts
round_trip_cost_rate itself. Never silently double-count fees.
"""
from datetime import date, timedelta
import math


def adapt_legacy_oos_net_candidates(rows, *, legacy_cost_bps, simulator_round_trip_cost_rate):
    if not isinstance(rows, list):
        raise ValueError("INVALID_LEGACY_CANDIDATES")
    for value in (legacy_cost_bps, simulator_round_trip_cost_rate):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError("INVALID_COST_ASSUMPTION")
    if simulator_round_trip_cost_rate >= 1:
        raise ValueError("INVALID_COST_ASSUMPTION")
    # Only mathematically equivalent additive percentage-point fee models
    # can be converted this way. Does not model fill/FX differences.
    original_fee_pct = legacy_cost_bps / 100.0
    result = []
    ids = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("INVALID_LEGACY_CANDIDATE")
        symbol = row.get("symbol")
        entry, exit_ = row.get("entry_day"), row.get("exit_day")
        ret = row.get("net_return_pct")
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("MISSING_CANDIDATE_SYMBOL")
        if any(not isinstance(x, int) or isinstance(x, bool) for x in (entry, exit_)) or exit_ <= entry:
            raise ValueError("INVALID_LEGACY_DATES")
        if isinstance(ret, bool) or not isinstance(ret, (int, float)) or not math.isfinite(ret):
            raise ValueError("INVALID_LEGACY_RETURN")
        gross = ret + original_fee_pct
        if gross < -100:
            raise ValueError("INVALID_LEGACY_RETURN")
        try:
            start = date(1970, 1, 1) + timedelta(days=entry)
            end = date(1970, 1, 1) + timedelta(days=exit_)
        except (OverflowError, ValueError):
            raise ValueError("INVALID_LEGACY_DATES") from None
        identifier = f"{symbol.strip().upper()}:{entry}"
        if identifier in ids:
            raise ValueError("DUPLICATE_LEGACY_CANDIDATE")
        ids.add(identifier)
        result.append({"id": identifier, "symbol": symbol.strip().upper(),
                       "entry_date": start.isoformat(), "exit_date": end.isoformat(),
                       "realized_return_pct": gross})
    # The older OOS generator emits symbol-grouped candidates, not a global
    # chronology. Stable date sorting retains original order on same-day ties.
    result.sort(key=lambda row: row["entry_date"])
    return {"status": "RESEARCH_ONLY_LEGACY_NET_TO_GROSS_ADAPTER",
            "candidates": result,
            "legacy_cost_bps": legacy_cost_bps,
            "simulator_round_trip_cost_rate": simulator_round_trip_cost_rate,
            "effective_net_return_pct_formula": "gross_pct - 100 * simulator_round_trip_cost_rate",
            "legacy_fee_model_equivalent_to_simulator": abs(original_fee_pct - 100 * simulator_round_trip_cost_rate) < 1e-10,
            "same_day_priority_preserved_from_input_order": True,
            "chronological_order_normalized": True,
            "source_independently_verified": False,
            "trade_ready": False}
