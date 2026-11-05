"""Offline matched-cohort score-versus-baseline comparison.

Use only fully completed, externally verified prospective cohorts. All ranking
methods must see the same eligible universe at the same decision timestamp.
This module does not attest provenance or claim predictive significance.
"""
from decimal import Decimal, InvalidOperation


def _number(value):
    if isinstance(value, bool):
        raise ValueError("invalid_numeric_value")
    try:
        n = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("invalid_numeric_value") from None
    if not n.is_finite():
        raise ValueError("invalid_numeric_value")
    return n


def compare_rankings(cohorts, *, slots=6):
    """Compare realized net percentage returns under two preregistered rankings.

    Candidate data: ticker, hypothesis_score, baseline_score, net_return_pct,
    eligible. A same-day cohort is one decision date. Assumes identical fixed
    capital per selected position, and no reallocation during outcome horizon.
    """
    if not isinstance(slots, int) or isinstance(slots, bool) or slots < 1:
        raise ValueError("invalid_slots")
    if not isinstance(cohorts, (list, tuple)) or not cohorts:
        raise ValueError("empty_cohorts")
    results = []
    for cohort in cohorts:
        if not isinstance(cohort, dict) or not isinstance(cohort.get("candidates"), list):
            raise ValueError("invalid_cohort")
        seen = set()
        valid = []
        for candidate in cohort["candidates"]:
            ticker = candidate["ticker"]
            if not isinstance(ticker, str) or not ticker.strip() or ticker in seen:
                raise ValueError("duplicate_or_invalid_ticker")
            seen.add(ticker)
            if candidate.get("eligible") is not True:
                continue
            valid.append({
                "ticker": ticker,
                "hypothesis_score": _number(candidate["hypothesis_score"]),
                "baseline_score": _number(candidate["baseline_score"]),
                "net_return_pct": _number(candidate["net_return_pct"]),
            })
        if len(valid) < 2:
            raise ValueError("insufficient_matched_candidates")
        count = min(slots, len(valid))
        hypothesis = sorted(valid, key=lambda r: (-r["hypothesis_score"], r["ticker"]))[:count]
        baseline = sorted(valid, key=lambda r: (-r["baseline_score"], r["ticker"]))[:count]
        h = sum((x["net_return_pct"] for x in hypothesis), Decimal(0)) / count
        b = sum((x["net_return_pct"] for x in baseline), Decimal(0)) / count
        results.append({"cohort_id": cohort["cohort_id"],
                        "hypothesis_tickers": [x["ticker"] for x in hypothesis],
                        "baseline_tickers": [x["ticker"] for x in baseline],
                        "hypothesis_avg_net_return_pct": str(h),
                        "baseline_avg_net_return_pct": str(b),
                        "difference_percentage_points": str(h - b)})
    mean_diff = sum((Decimal(r["difference_percentage_points"]) for r in results),
                    Decimal(0)) / len(results)
    return {"research_only": True, "predictive_edge_proven": False,
            "capital_and_fill_model_equivalent": False,
            "provenance_independently_verified": False,
            "cohort_count": len(results),
            "mean_difference_percentage_points": str(mean_diff),
            "cohorts": results}
