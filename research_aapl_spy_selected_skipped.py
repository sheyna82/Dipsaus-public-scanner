"""Research-only diagnostics for selected vs skipped price-history signals.

Never use in live alerts. Reports loss frequency and observed drawdown
proxy (worst 10-session exit return), not intraperiod maximum drawdown.
"""
import json
from research_aapl_adjustment_sensitivity import (
    make_adjusted_apple_csv,
)
from research_audit_aapl_spy_adjustments import read_public_csv, APPLE_URL
from research_reproduce_aapl_spy import download_spy_csv
from dipsaus_offline_price_history_eval import evaluate_local_history
from dipsaus_offline_downside_metrics import downside_metrics
from pathlib import Path
from tempfile import TemporaryDirectory

HEADER = "Date,Open,High,Low,Close,Volume"


def cohort_summary(rows):
    if not rows:
        return {"count": 0, "mean_net_pct": None, "loss_fraction": None,
                "worst_net_pct": None, "positive_fraction": None}
    returns = [r["net_return_pct"] for r in rows]
    return {"count": len(rows), "mean_net_pct": sum(returns) / len(returns),
            "loss_fraction": sum(x < 0 for x in returns) / len(returns),
            "positive_fraction": sum(x > 0 for x in returns) / len(returns),
            "worst_net_pct": min(returns)}


def evaluate_cohorts():
    apple = read_public_csv(APPLE_URL)
    spy = download_spy_csv()
    if len(apple) != 506 or any(r["Date"] not in spy for r in apple):
        raise ValueError("invalid_source_alignment")
    dates = [r["Date"] for r in apple]
    raw = [HEADER] + [",".join([r["Date"]] + [r["AAPL." + k] for k in
                             ("Open", "High", "Low", "Close", "Volume")]) for r in apple]
    benchmark = [HEADER] + [",".join([d] + [spy[d][k] for k in
                                      ("open", "high", "low", "close", "volume")])
                            for d in dates]
    with TemporaryDirectory() as folder:
        paths = [Path(folder) / x for x in ("raw.csv", "adjusted.csv", "spy.csv")]
        for path, payload in zip(paths, ("\n".join(raw) + "\n",
                                         make_adjusted_apple_csv(apple),
                                         "\n".join(benchmark) + "\n")):
            path.write_text(payload, encoding="utf-8")
        outputs = [evaluate_local_history(paths[i], paths[2]) for i in (0, 1)]
    report = {}
    for label, result in zip(("raw", "adjusted_scenario"), outputs):
        if result["status"] != "EXPLORATORY_ONLY":
            raise ValueError("evaluation_rejected")
        selected = [r for r in result["rows"] if r["score"] >= 5]
        skipped = [r for r in result["rows"] if r["score"] < 5]
        # Prespecified calendar split, not a truly untouched holdout: earlier
        # exploratory work already inspected the full Apple history.
        split_date = "2016-02-17"
        chronological = {}
        for period, predicate in (("early", lambda d: d < split_date),
                                  ("late", lambda d: d >= split_date)):
            period_rows = [r for r in result["rows"] if predicate(r["signal_date"])]
            period_selected = [r for r in period_rows if r["score"] >= 5]
            period_skipped = [r for r in period_rows if r["score"] < 5]
            chronological[period] = {
                "selected": cohort_summary(period_selected),
                "skipped": cohort_summary(period_skipped),
                "selected_downside": downside_metrics(period_selected),
                "skipped_downside": downside_metrics(period_skipped)}
        # Fixed descriptive regimes: benchmark 5-day return, known at signal close.
        # Never tune thresholds on these observed outcomes.
        market_regimes = {}
        for name, predicate in (("market_down_5d", lambda x: x < -2),\n                                ("market_flat_5d", lambda x: -2 <= x <= 2),\n                                ("market_up_5d", lambda x: x > 2)):
            group = [r for r in result["rows"] if predicate(r["market_return_5d"])]
            yes = [r for r in group if r["score"] >= 5]
            no = [r for r in group if r["score"] < 5]
            market_regimes[name] = {"selected": cohort_summary(yes),
                                    "skipped": cohort_summary(no),
                                    "selected_downside": downside_metrics(yes),
                                    "skipped_downside": downside_metrics(no)}
        report[label] = {"market_regime_diagnostic": market_regimes,
                         "chronological_diagnostic": chronological,
                         "selected": cohort_summary(selected),
                         "skipped": cohort_summary(skipped),
                         "selected_downside": downside_metrics(selected),
                         "skipped_downside": downside_metrics(skipped),
                         "selected_dates": [r["signal_date"] for r in selected]}
    report["selection_dates_identical"] = (
        report["raw"]["selected_dates"] == report["adjusted_scenario"]["selected_dates"])
    report["adjustment_policy_verified"] = False
    report["holdout_validated"] = False
    report["chronological_split_is_independent_holdout"] = False
    report["trade_ready"] = False
    return report


if __name__ == "__main__":
    print(json.dumps(evaluate_cohorts(), indent=2, sort_keys=True))
