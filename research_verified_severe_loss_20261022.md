# Observed fixed-threshold downside evaluation — 2026-10-22

Run https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/39762571928
Job selected-skipped-cohorts 119770095885: success.

AAPL/SPY adjusted-OHLC sensitivity scenario, 44 nonoverlapping
observations, 22 selected and 22 skipped, 10-session net exit returns.

| Metric | Selected | Skipped |
| --- | ---: | ---: |
| Net return <= -3% | 5/22 (22.73%) | 7/22 (31.82%) |
| Any loss | 11/22 (50%) | 8/22 (36.36%) |
| Mean among losses | -2.81615% | -6.65356% |
| Worst exit return | -6.306751% | -12.471872% |

Raw OHLC scenario likewise had 5/22 versus 7/22 severe losses.
This is descriptive only: tiny sample, unverified provider adjustment
compatibility, no prespecified external holdout, no event-time earnings
availability and no intratrade drawdown or slippage stress test.

Interpretation: fewer severe losses among selected dates, but MORE
negative exits overall. Never report this as validated predictive
accuracy or a trade-ready strategy. No live modifications.
