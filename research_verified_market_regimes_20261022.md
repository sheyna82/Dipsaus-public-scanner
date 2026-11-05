# Observed market-regime diagnostic — 2026-10-22

Source: https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/39768441829
selected-skipped-cohorts job 119789645308 passed.

AAPL vs independent SPY 2015-2017; adjusted OHLC *sensitivity scenario*
(not independently verified corporate-action policy), nonoverlapping
10-session fixed-exit returns with estimated fees. Market regime is
as-of signal close SPY 5-session return: down < -2%, flat -2% to +2%,
up > +2%. All numbers descriptive and research-only.

| Regime | Selected n | Selected mean net | Selected severe loss <=-3% | Skipped n | Skipped mean net | Skipped severe loss |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Down | 1 | -3.910064% | 1/1 | 2 | -2.1652555% | 1/2 |
| Flat | 18 | +0.3124391% | 4/18 | 15 | -0.2051267% | 5/15 |
| Up | 3 | +0.557595% | 0/3 | 5 | +0.6301938% | 1/5 |

Critical: **do not** infer an effective market regime filter.
The down/up sample sizes are extremely small; the benchmark market
return also contributes to the score, creating structural selection
imbalance. No untouched holdout, no verified earnings calendar, no
verified corporate-action parity, and no slippage/limit fill simulation.

Next appropriate test: independent tickers and longer historical
windows with consistent data-provider adjustment policies; fix the
model/thresholds in advance. No live changes.
