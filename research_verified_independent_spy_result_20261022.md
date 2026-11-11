# Verified independent SPY benchmark pilot — 2026-10-22

GitHub Actions: https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/39753003894
Independent SPY job 119737932041: **success**. Both other jobs succeeded.

Actual Python evaluation of publicly hosted historical AAPL and SPY
daily OHLCV samples, AAPL dates 2015-02-17 through 2017-02-16:

| Quantity | AAPL as own proxy | AAPL with independent SPY |
| --- | ---: | ---: |
| Observations | 44 | 44 |
| Selected | 26 | 22 |
| Selected mean net return (%) | +0.16822446153846157 | +0.0916068181818182 |
| All-entry mean net return (%) | -0.10875622727272728 | -0.10875622727272728 |

The two data feeds' split/dividend adjustment compatibility remains
**unverified**. No historical earnings calendar, independent universe,
confidence intervals, chronological holdout, or transaction execution
validation. Selection and average returns do not establish a positive
strategy edge. Do not promote to production or use for trade decisions.

Next: check price adjustment conventions and evaluate on multiple stocks
and disjoint holdout periods, including losing and flat market regimes.
