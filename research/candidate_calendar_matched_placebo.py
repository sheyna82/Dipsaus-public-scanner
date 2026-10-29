"""Strict calendar-stratified placebo: no cross-period substitution.

Requires baseline and selected records with session_day and excess_pct.
Draws from baseline within the same UTC calendar month for each selected entry.
This is descriptive and does not control for sector or shared macro shocks.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import math
import random
import statistics

def _month(row):
    day = row.get("session_day")
    value = row.get("excess_pct")
    if not isinstance(day, int) or isinstance(day, bool) or day < 0:
        raise ValueError("INVALID_SESSION_DAY")
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError("INVALID_EXCESS")
    return datetime.fromtimestamp(day * 86400, tz=timezone.utc).strftime("%Y-%m")

def calendar_placebo(baseline, selected, *, draws=1000, seed=20261029):
    if not isinstance(draws, int) or isinstance(draws, bool) or not 1 <= draws <= 10000:
        raise ValueError("INVALID_DRAWS")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("INVALID_SEED")
    groups = defaultdict(list)
    for row in baseline:
        groups[_month(row)].append(row["excess_pct"])
    counts = Counter(_month(row) for row in selected)
    n = len(selected)
    if n < 2 or any(len(groups[month]) < count for month, count in counts.items()):
        return {"status": "INSUFFICIENT_CALENDAR_MATCHES", "trade_ready": False,
                "n_selected": n, "n_baseline": len(baseline)}
    combinations = math.prod(math.comb(len(groups[month]), count) for month, count in counts.items())
    if combinations < 100:
        return {"status": "INSUFFICIENT_DISTINCT_PLACEBOS", "trade_ready": False,
                "n_selected": n, "n_baseline": len(baseline),
                "distinct_possible_placebos": combinations,
                "required_distinct_placebos": 100}
    rng = random.Random(seed)
    observed = statistics.mean(row["excess_pct"] for row in selected)
    null = []
    for _ in range(draws):
        draw = [value for month, count in sorted(counts.items())
                for value in rng.sample(groups[month], count)]
        null.append(statistics.mean(draw))
    null.sort()
    return {"status": "DESCRIPTIVE_CALENDAR_MATCHED", "trade_ready": False,
            "n_selected": n, "n_baseline": len(baseline), "draws": draws,
            "calendar_months": len(counts),
            "distinct_possible_placebos": combinations,
            "observed_mean_excess_pct": round(observed, 4),
            "placebo_median_mean_excess_pct": round(statistics.median(null), 4),
            "observed_percentile": round(sum(x <= observed for x in null)/draws, 4),
            "limitations": ["Calendar-month matching only; not sector or regime matching",
                            "Shared-date and cross-symbol dependence remains",
                            "Historical reused test data; not independent validation"]}
