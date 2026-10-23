"""Predeclared block-length sensitivity diagnostics for exploratory paired bootstrap."""
from research_paired_calendar_block_bootstrap import paired_calendar_block_bootstrap


def bootstrap_block_sensitivity(rows, *, block_lengths=(10, 14, 20),
                                replicates=500, seed=20261023):
    """Compare intervals across fixed block lengths; never optimize on holdout."""
    if not isinstance(block_lengths, (list, tuple)) or not block_lengths:
        raise ValueError("invalid_block_lengths")
    if any(type(length) is not int or length < 1 for length in block_lengths):
        raise ValueError("invalid_block_lengths")
    if len(set(block_lengths)) != len(block_lengths):
        raise ValueError("duplicate_block_lengths")
    results = [
        paired_calendar_block_bootstrap(
            rows, block_days=length, replicates=replicates, seed=seed)
        for length in block_lengths
    ]
    def excludes_zero(interval):
        low, high = interval
        return low > 0 or high < 0

    def sign(interval):
        low, high = interval
        return "positive" if low > 0 else ("negative" if high < 0 else "crosses_zero")

    weight_sensitivity = [
        {
            "block_observed_dates": result["block_observed_dates"],
            "event_weighted_brier_sign": sign(result["exploratory_interval"]),
            "equal_date_brier_sign": sign(result["equal_date_weighted_brier_interval"]),
            "event_weighted_log_loss_sign": sign(result["exploratory_log_loss_interval"]),
            "equal_date_log_loss_sign": sign(result["equal_date_weighted_log_loss_interval"]),
            "brier_weighting_agrees": sign(result["exploratory_interval"]) ==
                                      sign(result["equal_date_weighted_brier_interval"]),
            "log_loss_weighting_agrees": sign(result["exploratory_log_loss_interval"]) ==
                                         sign(result["equal_date_weighted_log_loss_interval"]),
        }
        for result in results
    ]
    opposite_brier = any(
        {item["event_weighted_brier_sign"], item["equal_date_brier_sign"]} ==
        {"positive", "negative"} for item in weight_sensitivity)
    opposite_log_loss = any(
        {item["event_weighted_log_loss_sign"], item["equal_date_log_loss_sign"]} ==
        {"positive", "negative"} for item in weight_sensitivity)
    return {
        "opposite_brier_weighting_conclusions": opposite_brier,
        "opposite_log_loss_weighting_conclusions": opposite_log_loss,
        "weighting_sensitivity": weight_sensitivity,
        "all_brier_weighting_agrees": all(
            item["brier_weighting_agrees"] for item in weight_sensitivity),
        "all_log_loss_weighting_agrees": all(
            item["log_loss_weighting_agrees"] for item in weight_sensitivity),
        "block_lengths": list(block_lengths),
        "results": results,
        "all_intervals_exclude_zero": all(
            low > 0 or high < 0 for low, high in
            (result["exploratory_interval"] for result in results)),
        "intervals_validated_for_inference": False,
        "independent_holdout_verified": False,
        "trade_ready": False,
    }
