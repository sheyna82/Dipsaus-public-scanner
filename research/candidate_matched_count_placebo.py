"""Deterministic matched-count placebo controls for descriptive ablation cohorts.

Samples from the SAME eligible baseline events, without replacement per draw.
Not independent validation and not a substitute for calendar/sector matching.
"""
import math
import random
import statistics

def placebo(records, selected, *, draws=1000, seed=20261029):
    if not isinstance(draws, int) or isinstance(draws, bool) or not 1 <= draws <= 10000:
        raise ValueError("INVALID_DRAW_COUNT")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("INVALID_SEED")
    if any(not isinstance(r, dict) or
           not isinstance(r.get("excess_pct"), (int, float)) or
           isinstance(r.get("excess_pct"), bool) or
           not math.isfinite(r["excess_pct"]) for r in records + selected):
        raise ValueError("INVALID_RECORD")
    n = len(selected)
    if not records or n < 2 or n > len(records):
        return {"status": "INSUFFICIENT_MATCHED_SAMPLE", "trade_ready": False,
                "n_selected": n, "n_baseline": len(records)}
    rng = random.Random(seed)
    values = [r["excess_pct"] for r in records]
    observed = statistics.mean(r["excess_pct"] for r in selected)
    null = sorted(statistics.mean(rng.sample(values, n)) for _ in range(draws))
    # An empirical percentile is descriptive, not a calibrated p-value.
    fraction = sum(v <= observed for v in null) / draws
    return {"status": "DESCRIPTIVE_PLACEBO_ONLY", "trade_ready": False,
            "n_selected": n, "n_baseline": len(records), "draws": draws,
            "seed": seed, "observed_mean_excess_pct": round(observed, 4),
            "placebo_median_mean_excess_pct": round(statistics.median(null), 4),
            "placebo_p05_mean_excess_pct": round(null[int(.05*(draws-1))], 4),
            "placebo_p95_mean_excess_pct": round(null[int(.95*(draws-1))], 4),
            "observed_percentile": round(fraction, 4),
            "limitations": ["Not calendar-, sector- or regime-matched",
                            "Same historical test observations reused",
                            "Not independent prospective validation"]}
