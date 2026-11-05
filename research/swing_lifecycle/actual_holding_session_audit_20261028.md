# Corrected holding-session audit — 2026-10-28

Research-only. No production scanner changes, no automatic orders.

**Material correction:** prior horizon labels 5/10/15 represent 2/7/12 actual trading sessions from the next-open entry (on 5,710 checked rows per label), not 5/10/15 sessions. Prior comparisons must not be cited as true holding-period evidence.

Rebuilt daily paths from 20 GitHub Actions ZIP archives and replayed **5,707** symbol/signal-entry pairs with enough daily bars for actual 3/5/10/15-session exits (260 other pairs lacked 15 forward bars). Hypothetical next-open entry and day-N close exit; subtract flat 0.2 percentage points for illustrative friction. Not real bid/ask or FX.

Later subset signal entry >= Aug 1, 2026, n=2,288:

| Actual sessions | Median net return | Loss >=5% at exit | Intratrade low <=-5% |
|---|---:|---:|---:|
| 3 | -0.200% | 13.81% | 28.76% |
| 5 | -0.260% | 21.07% | 39.16% |
| 10 | -1.190% | 30.77% | 54.11% |
| 15 | -2.142% | 37.89% | 61.32% |

Full cohort n=5,707: median net return at 3/5/10/15 = -0.340/-0.293/-0.241/-0.924%. Loss>=5% = 16.09/21.36/25.42/31.84%.

**Limitations:** short 2026 window, selected event universe, repeated tickers and correlated entry dates, possible survivorship and timestamp biases, no point-in-time event calendar, hypothetical close execution, no FX, no portfolio capital constraints, no calibrated predictive advantage. Intratrade low is adverse excursion, not a realized loss. This is a fixed-duration benchmark, NOT evidence for any conditional exit engine. No rules deployed.

Next: build leakage-safe dynamic exit simulations with trading-session indexing, point-in-time signals, executable next-open exits, cost stress, walk-forward and clustered confidence intervals; compare against fixed-duration baselines and account for missed upside.
