# OOS portfolio → integrated risk: source-contract audit (2026-11-02)

**Status:** HISTORICAL RESEARCH / CODE INSPECTION. No execution or live trade validation.

## Reuse confirmed
- `research/candidate_feature_oos.py::portfolio_oos_pair` already generates a common held-out calendar, baseline and filtered historical event pools, runs `candidate_portfolio_capacity.simulate`, and reports accepted/rejected decisions and calendar capital occupancy.
- `portfolio_oos.candidate_audit` records symbol, signal day, entry/exit days, filter selection, and *realized outcome*. The outcome must **never** become a ranking or selection feature.
- `portfolio_oos.baseline` and `portfolio_oos.filtered` are already capacity-simulated. Re-running them in a second adapter is unnecessary and may change priority tie-breaking.
- `research/candidate_integrated_readonly_report.py::build` accepts candidate-snapshot-bound `dated_signals`, `sector_by_symbol`, `equity_observations`, and `reconciled_portfolio_inputs`. It rejects symbols absent from the provided candidate snapshot.

## Critical boundary: not directly joinable
The OOS report's *historical* symbol universe and signal dates are not equivalent to the *current candidate* snapshot/evidence pair consumed by the integrated report. Feeding OOS historical signals into `build` with an unrelated current snapshot would either raise `SIGNAL_NOT_IN_CANDIDATE_SNAPSHOT` or misrepresent the provenance. Do not bypass this guard.

## Still missing for full daily risk reconciliation
1. Point-in-time historical candidate/evidence snapshots **matching each OOS signal** (or a separate historical integration entrypoint that explicitly preserves historical provenance).
2. Reconciled `trades`, `daily_marks`, and `trading_dates` for the same calendar, with currency, fees, fills, corporate actions, and cash checks.
3. Daily portfolio equity observations derived from those same reconciled records; closed-trade P&L is **not** a substitute.
4. Audited sector labels at the same historical date; V2 exploratory universe labels are not independently validated sector evidence.

## Decision
Do not create another portfolio simulator, another benchmark comparator, or synthetic daily marks. Preserve existing OOS capacity results. Only integrate when a single historical provenance and accounting contract can be verified end-to-end. Until then, `equity_risk` remains `NOT_EVALUATED`, `trade_ready=False`.

Next empirical research: compare existing OOS baseline vs filtered **on the same common calendar and priority mode**, using already reported accepted counts, realized P&L, capital occupancy, and uncertainty across quarters; do not claim risk-adjusted alpha without reconciled daily equity.
