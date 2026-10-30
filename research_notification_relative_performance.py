"""Benchmark-relative research only; no trading decisions or live market feeds."""

def relative_performance(stock_result, benchmark_result):
    """Compare aligned proxy exits; refuse mismatched periods and missing outcomes."""
    if stock_result is None or benchmark_result is None:
        return None
    if (stock_result.get("entry_date") != benchmark_result.get("entry_date")
            or stock_result.get("exit_date") != benchmark_result.get("exit_date")):
        raise ValueError("unaligned_benchmark_window")
    for item in (stock_result, benchmark_result):
        if item.get("execution_verified") is not False:
            raise ValueError("expected_unverified_research_proxy")
        if not isinstance(item.get("gross_return_pct"), (int, float)):
            raise ValueError("missing_gross_return")
    return {
        "excess_gross_pct_points": round(
            stock_result["gross_return_pct"] - benchmark_result["gross_return_pct"], 4
        ),
        "entry_date": stock_result["entry_date"],
        "exit_date": stock_result["exit_date"],
        "research_only": True,
        "execution_verified": False,
    }
