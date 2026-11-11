"""Offline prospective rank validation; no market feed or trading actions.

Evaluate only completed, immutable outcomes. One row per ticker and entry
session; rows must be recorded before their outcome session.
"""
from decimal import Decimal, InvalidOperation
from statistics import mean


def _num(value):
    if isinstance(value, bool):
        raise ValueError("invalid_number")
    try:
        x = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("invalid_number") from None
    if not x.is_finite():
        raise ValueError("invalid_number")
    return x


def evaluate_ranked_outcomes(rows, *, min_days=10, min_rows=30):
    """Compare top and bottom score halves by entry date, net returns.

    This is a descriptive paired-date spread, NOT a significance test or
    evidence of causal/predictive skill. At least two names per date required.
    """
    if not isinstance(rows, (list, tuple)) or isinstance(min_days, bool) or isinstance(min_rows, bool) or min_days < 2 or min_rows < 2:
        raise ValueError("invalid_inputs")
    by_day = {}
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid_row")
        day, ticker = row.get("entry_day"), row.get("ticker")
        recorded, outcome_day = row.get("recorded_day"), row.get("outcome_day")
        if not all(isinstance(v, str) and v for v in (day, ticker, recorded, outcome_day)):
            raise ValueError("missing_provenance")
        # ISO dates compare lexicographically when normalized YYYY-MM-DD.
        from datetime import date
        try:
            d, r, o = (date.fromisoformat(v) for v in (day, recorded, outcome_day))
        except ValueError:
            raise ValueError("invalid_date") from None
        if not (r <= d < o):
            raise ValueError("lookahead_or_unfinished_outcome")
        key = (day, ticker)
        if key in seen:
            raise ValueError("duplicate_signal")
        seen.add(key)
        if row.get("eligible") is not True:
            continue
        score, ret = _num(row.get("score")), _num(row.get("net_return_pct"))
        by_day.setdefault(day, []).append((score, ticker, ret))
    paired = []
    for day, names in sorted(by_day.items()):
        if len(names) < 2:
            continue
        names.sort(key=lambda x: (-x[0], x[1]))
        n = len(names) // 2
        # Discard median on odd counts for equal-size comparison.
        top, bottom = names[:n], names[-n:]
        top_mean = sum((x[2] for x in top), Decimal(0)) / n
        bottom_mean = sum((x[2] for x in bottom), Decimal(0)) / n
        paired.append({"entry_day": day,
                       "top_mean_pct": str(top_mean),
                       "bottom_mean_pct": str(bottom_mean),
                       "spread_pct_points": str(top_mean - bottom_mean)})
    eligible_rows = sum(len(v) for v in by_day.values())
    ready = len(paired) >= min_days and eligible_rows >= min_rows
    average_spread = (sum((Decimal(v["spread_pct_points"]) for v in paired), Decimal(0)) / len(paired)) if paired else None
    return {"research_only": True, "predictive_edge_proven": False,
            "eligible_rows": eligible_rows, "paired_days": len(paired),
            "evidence_sufficient_for_review": ready,
            "mean_top_minus_bottom_pct_points": str(average_spread) if average_spread is not None else None,
            "daily_spreads": paired}
