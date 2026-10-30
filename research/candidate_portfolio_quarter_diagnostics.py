"""Read-only quarterly diagnostics for existing candidate feature portfolio artifact.

No strategy fitting, portfolio replay, orders, or inference of daily drawdown.
"""
import json
from collections import defaultdict, Counter
from datetime import date, timedelta
from pathlib import Path

REPORT = Path("reports/candidate_feature_oos.json")
OUT = Path("reports/candidate_feature_portfolio_quarters.json")


def summarize(report):
    results = {}
    for pattern, paired in report["portfolio_oos"].items():
        arms = {}
        for arm in ("baseline", "filtered"):
            by_quarter = defaultdict(list)
            trades = paired[arm]["accepted_signals"]
            for trade in trades:
                entry = date(1970, 1, 1) + timedelta(days=trade["entry_day"])
                quarter = f"{entry.year}Q{(entry.month - 1) // 3 + 1}"
                by_quarter[quarter].append(trade)
            tranche = paired[arm]["tranche"]
            quarters = {}
            for quarter, rows in sorted(by_quarter.items()):
                pnl = sum(tranche * r["net_return_pct"] / 100 for r in rows)
                quarters[quarter] = {
                    "accepted_n": len(rows),
                    "realized_pnl_approx": round(pnl, 2),
                    "positive_trades": sum(r["net_return_pct"] > 0 for r in rows),
                }
            arms[arm] = {
                "accepted_n": len(trades),
                "positive_quarters": sum(q["realized_pnl_approx"] > 0 for q in quarters.values()),
                "negative_quarters": sum(q["realized_pnl_approx"] < 0 for q in quarters.values()),
                "flat_quarters": sum(q["realized_pnl_approx"] == 0 for q in quarters.values()),
                "quarters": quarters,
                "top_symbols_by_accepted_count": Counter(
                    t["symbol"] for t in trades).most_common(5),
            }
        results[pattern] = arms
    return {
        "research_only": True,
        "trade_ready": False,
        "source": str(REPORT),
        "allocation": "Trades attributed to quarter of entry; no intra-quarter equity marks",
        "limitations": [
            "Rounded per-quarter PnL is approximate and based on accepted trade returns",
            "Quarter sign is descriptive, not a significance or walk-forward test",
            "Different arms can select different trades under capacity constraints",
            "Unadjusted prices, survivorship, and currency provenance unverified",
        ],
        "patterns": results,
    }


def main():
    result = summarize(json.loads(REPORT.read_text(encoding="utf-8")))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"research_only": True, "patterns": list(result["patterns"])}))


if __name__ == "__main__":
    main()
