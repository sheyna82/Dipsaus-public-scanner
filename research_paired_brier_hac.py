"""Research-only paired Brier loss HAC uncertainty, Bartlett/Newey-West reference.

Uses no third-party packages. Input must be chronological, equally spaced
observations; no independent-validation or predictive-edge claims.
"""
import math


def paired_brier_hac(predictions, *, lags):
    if not isinstance(predictions, (list, tuple)) or len(predictions) < 3:
        raise ValueError("insufficient_predictions")
    n = len(predictions)
    if type(lags) is not int or not 0 <= lags < n:
        raise ValueError("invalid_lags")
    differences = []
    for row in predictions:
        if not isinstance(row, dict) or type(row.get("severe")) is not bool:
            raise ValueError("invalid_row")
        a, b = row.get("atr_probability"), row.get("baseline_probability")
        if any(type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1
               for p in (a, b)):
            raise ValueError("invalid_probability")
        y = int(row["severe"])
        differences.append((a - y) ** 2 - (b - y) ** 2)
    mean = sum(differences) / n
    centered = [x - mean for x in differences]
    long_run = sum(x * x for x in centered) / n
    for lag in range(1, lags + 1):
        covariance = sum(centered[t] * centered[t - lag]
                         for t in range(lag, n)) / n
        long_run += 2 * (1 - lag / (lags + 1)) * covariance
    variance = max(0.0, long_run / n)
    se = math.sqrt(variance)
    return {"atr_minus_baseline_brier": mean, "hac_standard_error": se,
            "hac_lags": lags, "observations": n,
            "approximate_95pct_interval": [mean - 1.96 * se, mean + 1.96 * se],
            "assumes_equally_spaced_observations": True,
            "normal_approximation_only": True,
            "independent_holdout_verified": False, "trade_ready": False}
