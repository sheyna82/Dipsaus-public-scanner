# Chronological stability diagnostic — observed results (2026-10-22)

GitHub Actions run: https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/39767284155
Job selected-skipped-cohorts 119785779960: success.

AAPL versus independent SPY; adjusted AAPL OHLC **scenario**, unverified
corporate-action adjustment parity. Split at 2016-02-17. This is NOT
an untouched out-of-sample holdout: the full series was previously
inspected.

| Metric | Early selected | Early skipped | Late selected | Late skipped |
| --- | ---: | ---: | ---: | ---: |
| Count | 9 | 12 | 13 | 10 |
| Mean net exit return (%) | -0.37762022 | -2.53566650 | +0.52193900 | +2.61715560 |
| Severe exit loss <= -3% | 1/9 | 6/12 | 4/13 | 1/10 |
| Any negative exit | 5/9 | 7/12 | 6/13 | 1/10 |

Interpretation: the full-sample selected mean and severe-loss edge
**do not remain stable across the two subperiods**. Late skipped
opportunities outperformed selected opportunities and were positive
in 9 of 10 cases, with one -12.47% exception.

No causal proof that market regime explains this. A regime-based filter
must be prespecified and evaluated on independent data, not fitted
to these already-observed outcomes. Do not activate live trading
signals or imply strategy validation.
