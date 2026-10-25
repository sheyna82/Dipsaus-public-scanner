"""Separate immutable prospective outcome files from frozen signal candidates.

Research-only: outcomes require a matching frozen candidate and three later
benchmark trading sessions. Never edits candidate files or live alerts.
"""
import hashlib
import json
from decimal import Decimal
from pathlib import Path


def write_outcome(candidate_file, stock_rows, spy_rows, output_dir):
    candidate_path = Path(candidate_file)
    candidate_bytes = candidate_path.read_bytes()
    candidate = json.loads(candidate_bytes)
    if candidate.get("future_outcome") is not None or candidate.get("trade_ready") is not False:
        raise ValueError("unsafe_candidate")
    signal_date = candidate["signal_session"]
    def index(rows):
        result = {}
        for row in rows:
            day = row["date"]
            if day in result:
                raise ValueError("duplicate_session")
            value = Decimal(str(row["close"]))
            if not value.is_finite() or value <= 0:
                raise ValueError("invalid_close")
            result[day] = value
        return result
    stock = index(stock_rows)
    spy = index(spy_rows)
    if signal_date not in stock or signal_date not in spy:
        raise ValueError("missing_signal_close")
    future_spy_days = sorted(d for d in spy if d > signal_date)
    if len(future_spy_days) < 3:
        return {"status": "pending_three_future_sessions", "research_only": True}
    future_days = future_spy_days[:3]
    if any(d not in stock for d in future_days):
        return {"status": "missing_stock_future_session", "research_only": True}
    end_day = future_days[-1]
    stock_return = (stock[end_day] / stock[signal_date] - 1) * 100
    spy_return = (spy[end_day] / spy[signal_date] - 1) * 100
    worst = min((stock[d] / stock[signal_date] - 1) * 100 for d in future_days)
    record = {"protocol_id": candidate["protocol_id"],
              "symbol": candidate["symbol"], "signal_session": signal_date,
              "outcome_session": end_day, "future_sessions": future_days,
              "future_excess_return_pp": str(stock_return - spy_return),
              "worst_future_close_return_pct": str(worst),
              "severe_downside_event": worst <= Decimal("-5"),
              "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
              "research_only": True, "trade_ready": False,
              "input_verified_independently": False}
    root = Path(output_dir)
    if not root.is_dir():
        raise ValueError("outcome_directory_must_exist")
    path = root / (candidate_path.stem + "-outcome.json")
    payload = (json.dumps(record, sort_keys=True, indent=2) + "\n").encode("utf-8")
    try:
        with path.open("xb") as f:
            f.write(payload)
        return {"status": "created", "file": str(path), "record": record}
    except FileExistsError:
        if path.read_bytes() != payload:
            raise ValueError("existing_outcome_conflict")
        return {"status": "duplicate", "file": str(path), "record": record}
