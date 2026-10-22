"""Leakage-safe scoring primitives for a future independent ATR risk holdout.

No data fetching, trading actions, tuning, or use of previously inspected labels.
"""
import math


def _validate_event(row):
    if not isinstance(row, dict):
        raise ValueError("invalid_event")
    for name in ("structure_above_20d_mean", "market_20d_positive", "atr_expanding"):
        if type(row.get(name)) is not bool:
            raise ValueError("invalid_flag")
    if type(row.get("severe")) is not bool:
        raise ValueError("invalid_outcome")


def _rate(severe, count):
    # Fixed Laplace smoothing; must not be selected using holdout results.
    return (severe + 1) / (count + 2)


def fit(training):
    """Fit baseline and ATR-augmented cell frequencies using training labels only."""
    if not training:
        raise ValueError("empty_training")
    baseline = {}
    expanded = {}
    for row in training:
        _validate_event(row)
        key = (row["structure_above_20d_mean"], row["market_20d_positive"])
        for table, cell in ((baseline, key), (expanded, key + (row["atr_expanding"],))):
            count, severe = table.get(cell, (0, 0))
            table[cell] = (count + 1, severe + int(row["severe"]))
    pooled = _rate(sum(int(row["severe"]) for row in training), len(training))
    return {"baseline": baseline, "expanded": expanded, "pooled": pooled,
            "training_events": len(training)}



def forecast(model, rows):
    """Produce causal forecasts without requiring future outcome labels."""
    if not isinstance(model, dict) or not all(
            key in model for key in ("baseline", "expanded", "pooled")):
        raise ValueError("invalid_model")
    output = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid_event")
        for name in ("structure_above_20d_mean", "market_20d_positive", "atr_expanding"):
            if type(row.get(name)) is not bool:
                raise ValueError("invalid_flag")
        key = (row["structure_above_20d_mean"], row["market_20d_positive"])
        baseline = model["baseline"].get(key)
        expanded = model["expanded"].get(key + (row["atr_expanding"],))
        output.append({"baseline_probability": _rate(baseline[1], baseline[0])
                       if baseline else model["pooled"],
                       "atr_probability": _rate(expanded[1], expanded[0])
                       if expanded else model["pooled"],
                       "baseline_fallback": baseline is None,
                       "atr_fallback": expanded is None,
                       "trade_ready": False})
    return output

def predict(model, rows):
    """Return paired frozen forecasts; unknown cells fall back to pooled prior."""
    output = []
    for row in rows:
        _validate_event(row)
        key = (row["structure_above_20d_mean"], row["market_20d_positive"])
        baseline = model["baseline"].get(key)
        expanded = model["expanded"].get(key + (row["atr_expanding"],))
        output.append({"severe": row["severe"],
                       "baseline_probability": _rate(baseline[1], baseline[0])
                       if baseline else model["pooled"],
                       "atr_probability": _rate(expanded[1], expanded[0])
                       if expanded else model["pooled"],
                       "baseline_fallback": baseline is None,
                       "atr_fallback": expanded is None})
    return output


def evaluate(predictions):
    if not predictions:
        raise ValueError("empty_holdout")
    result = {"events": len(predictions),
              "severe_events": sum(int(row["severe"]) for row in predictions)}
    for prefix, field in (("baseline", "baseline_probability"), ("atr", "atr_probability")):
        values = [row[field] for row in predictions]
        if any(type(x) not in (float, int) or not math.isfinite(x) or not 0 <= x <= 1
               for x in values):
            raise ValueError("invalid_probability")
        result[prefix + "_brier"] = round(sum(
            (p - int(row["severe"])) ** 2 for p, row in zip(values, predictions))
            / len(predictions), 8)
        result[prefix + "_log_loss"] = round(-sum(
            int(row["severe"]) * math.log(min(.99, max(.01, p)))
            + (1 - int(row["severe"])) * math.log(1 - min(.99, max(.01, p)))
            for p, row in zip(values, predictions)) / len(predictions), 8)
        result[prefix + "_fallback_events"] = sum(
            row[prefix + "_fallback"] for row in predictions)
    result["atr_minus_baseline_brier"] = round(
        result["atr_brier"] - result["baseline_brier"], 8)
    result.update({"independent_holdout_verified": False,
                   "trade_ready": False, "descriptive_only": True})
    return result
