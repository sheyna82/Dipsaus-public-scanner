"""Offline end-to-end prospective research ledger smoke test.

Synthetic prices only: proves candidate -> immutable file -> delayed outcome ->
integrity audit without contacting markets or changing the live scanner.
"""
import json
import tempfile
from pathlib import Path

from research_prospective_batch import generate_prospective_batch
from research_prospective_ledger_writer import write_candidate_batch
from research_prospective_outcome_writer import write_outcome
from research_prospective_ledger_audit import audit_prospective_ledger


def run_smoke_test():
    dates = ["2026-10-20", "2026-10-21", "2026-10-22", "2026-10-26",
             "2026-10-27", "2026-10-28", "2026-10-29"]
    spy = [{"date": day, "close": 100 + i} for i, day in enumerate(dates)]
    stocks = {
        symbol: [{"date": day, "close": 100 + i * (j + 2)}
                 for i, day in enumerate(dates)]
        for j, symbol in enumerate(("COHU", "AMD", "META"))
    }
    batch = generate_prospective_batch(
        {symbol: rows[:4] for symbol, rows in stocks.items()},
        spy[:4], signal_session="2026-10-26")
    with tempfile.TemporaryDirectory() as tmp:
        candidates = Path(tmp) / "candidates"
        outcomes = Path(tmp) / "outcomes"
        candidates.mkdir()
        outcomes.mkdir()
        first = write_candidate_batch(batch, candidates)
        if len(first["created"]) != 3:
            raise AssertionError("expected_three_candidates")
        repeat = write_candidate_batch(batch, candidates)
        if len(repeat["duplicates"]) != 3:
            raise AssertionError("expected_three_duplicate_replays")
        for symbol in ("COHU", "AMD", "META"):
            candidate = candidates / (
                f"dipsaus-prospective-momentum-v1-{symbol}-2026-10-26.json")
            pending = write_outcome(candidate, stocks[symbol][:6], spy[:6], outcomes)
            if pending["status"] != "pending_three_future_sessions":
                raise AssertionError("future_outcome_available_too_early")
            complete = write_outcome(candidate, stocks[symbol], spy, outcomes)
            if complete["status"] != "created":
                raise AssertionError("outcome_not_created")
        audit = audit_prospective_ledger(candidates, outcomes)
        if not audit["integrity_pass"] or audit["pending_outcome_count"] != 0:
            raise AssertionError("ledger_integrity_failure")
        return {"research_only": True, "synthetic_data_only": True,
                "candidate_count": audit["candidate_count"],
                "outcome_count": audit["outcome_count"],
                "integrity_pass": True, "trade_ready": False}


if __name__ == "__main__":
    print(json.dumps(run_smoke_test()))
