"""Strict timestamp-gated, next-open portfolio ranking comparison.

Reject all candidate data if a single trade has invalid chronological metadata.
The benchmark must use next-session-open fills; legacy same-close execution
is intentionally inaccessible through this entrypoint. Research only.
"""
from research_swing_timestamp_gated_pipeline import evaluate_timestamp_gated_batch
from research_swing_entry_open_gate import validate_next_open_entries
from research_swing_portfolio_benchmark import compare_portfolio_rankings


def evaluate_gated_portfolio_benchmark(candidates, capital, *,
                                       evaluation_cutoff, **benchmark_options):
    if not isinstance(candidates, (list, tuple)) or not candidates:
        raise ValueError("empty_gated_batch")
    if benchmark_options.get("execution_model", "next_session_open") != "next_session_open":
        raise ValueError("next_open_execution_required")
    if any(not isinstance(candidate, dict) for candidate in candidates):
        raise ValueError("invalid_candidate")
    if any(candidate.get("eligible") is not True for candidate in candidates):
        raise ValueError("ineligible_candidate_in_gated_cohort")
    # Validate the complete cohort before allowing any portfolio P&L.
    validate_next_open_entries(candidates)
    def evaluate(verified):
        return compare_portfolio_rankings(
            verified, capital, execution_model="next_session_open",
            **{k: v for k, v in benchmark_options.items() if k != "execution_model"})
    result = evaluate_timestamp_gated_batch(
        candidates, evaluation_cutoff=evaluation_cutoff, evaluator=evaluate)
    result["comparison"] = "pre_entry_rankings_identical_next_open_execution"
    result["score_formula_validated"] = False
    result["source_timestamps_independently_attested"] = False
    return result
