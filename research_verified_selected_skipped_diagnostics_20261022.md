# Verified selected-versus-skipped real-price diagnostics — 2026-10-22

GitHub Actions: https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/39760746662
Job selected-skipped-cohorts (119764000873): success.

AAPL with independent SPY, 44 non-overlapping observations,
10-session next-open entry to close exit, assumed 10 bps each side.

**Adjusted-OHLC sensitivity scenario (unverified adjustment policy):**

| Metric | Selected (score >= 5) | Skipped |
| --- | ---: | ---: |
| Count | 22 | 22 |
| Mean net return (%) | +0.1539375 | -0.19347463636363632 |
| Loss fraction | 50.0% | 36.36% |
| Positive fraction | 50.0% | 63.64% |
| Worst net return (%) | -6.306751 | -12.471872 |

The raw and adjusted scenarios selected **identical dates**.
Selection's mean is higher but its *loss frequency is also higher*.
The worst recorded value is a fixed-horizon exit return, NOT maximum
intratrade drawdown. This is an important adverse result for an alert
system intended to avoid weak entries.

Do not optimize the score threshold on these same 44 observations and
then call it predictive validation. Next research needs a prespecified
loss/risk metric, chronological holdout and broader symbol universe,
with adjustment provenance resolved. No production changes.
