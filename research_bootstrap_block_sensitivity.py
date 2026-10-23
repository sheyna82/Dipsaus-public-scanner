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
    return {
        "block_lengths": list(block_lengths),
        "results": results,
        "all_intervals_exclude_zero": all(
            low > 0 or high < 0 for low, high in
            (result["exploratory_interval"] for result in results)),
        "intervals_validated_for_inference": False,
        "independent_holdout_verified": False,
        "trade_ready": False,
    }
