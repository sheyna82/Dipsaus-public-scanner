"""Research-only diagnostic for outlier dependence of yearly momentum differences."""
from decimal import Decimal


def summarize_yearly_outlier_dependence(outlier_report):
    results = []
    for stock in outlier_report.get("results", []):
        for year in stock.get("years", []):
            positive, negative = year["positive"], year["negative"]
            fields = ("mean_pp", "median_pp", "mean_without_extremes_pp")
            if any(positive.get(k) is None or negative.get(k) is None for k in fields):
                results.append({"symbol": stock["symbol"], "year": year["year"],
                                "status": "insufficient_data"})
                continue
            differences = {k: Decimal(positive[k]) - Decimal(negative[k]) for k in fields}
            mean, median, trimmed = (differences[k] for k in fields)
            def sign(value):
                return "positive" if value > 0 else "negative" if value < 0 else "zero"
            results.append({
                "symbol": stock["symbol"], "year": year["year"],
                "status": "descriptive_only",
                "positive_count": positive["count"], "negative_count": negative["count"],
                "mean_difference_pp": str(mean),
                "median_difference_pp": str(median),
                "trimmed_difference_pp": str(trimmed),
                "mean_median_sign_disagree": sign(mean) != sign(median),
                "mean_trimmed_sign_disagree": sign(mean) != sign(trimmed),
                "mean_minus_trimmed_difference_pp": str(mean - trimmed),
                "no_statistical_significance_claim": True})
    return {"research_only": True, "not_independent_validation": True,
            "predictive_skill_established": False, "trade_ready": False,
            "results": results}
