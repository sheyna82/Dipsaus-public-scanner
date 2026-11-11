"""Offline forward close-to-close drawdown labels for historical research only.

A label is known only after its full future horizon has elapsed.
This is NOT a point-in-time verification or a trading signal.
"""
import csv
import io
from research_daily_price_csv_audit import audit_daily_price_csv


def label_forward_drawdown(payload, *, horizon=10, threshold=0.08):
    """Return dated labels for a >= threshold decline from decision close.

    Decision occurs after the dated close; next horizon daily closes are evaluated.
    Rows lacking a complete horizon are excluded, never marked as safe.
    """
    audit_daily_price_csv(payload)
    if type(horizon) is not int or horizon < 1:
        raise ValueError("invalid_horizon")
    if type(threshold) not in (float, int) or not 0 < threshold < 1:
        raise ValueError("invalid_threshold")
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))
    closes = [float(row["close"]) for row in rows]
    output = []
    for i in range(len(rows) - horizon):
        future_min = min(closes[i + 1:i + horizon + 1])
        output.append({
            "date": rows[i]["date"],
            "label_available_date": rows[i + horizon]["date"],
            "severe": future_min / closes[i] - 1 <= -threshold,
            "horizon_trading_days": horizon,
            "threshold_fraction": threshold,
            "point_in_time_verified": False,
            "trade_ready": False,
        })
    return output
