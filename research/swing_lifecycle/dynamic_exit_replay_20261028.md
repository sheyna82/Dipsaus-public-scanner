# Dynamic exit replay — exploratory research (2026-10-28)

Research-only. No live scanner changes, no orders, no merge to main.

Using 5,695 historical symbol/signal-entry cases with enough bars, compare seven manually chosen exit rules. Daily close signals are executed at next trading session open; flat 0.2 percentage-point friction deducted. 12 of the previous 5,707 cases lacked a next-session open for the 15-day comparison.

Strategies: fixed exits after 5/10/15 completed sessions; structure break after session 3 (close below previous three closes and return <=-3%); profit protection (peak closing gain >=4% followed by >=2% closing drawdown); time review on day 5/10 when closing gain <2%, else day 15; combined structure/profit/time. Note: rules are hypothetical **automated simulation** for comparison; live workflow would require manual decisions and no automatic orders.

Later cohort signal_entry >=2026-08-01, n=2,276:
| rule | mean net % | median net % | loss >=5% % | mean exposed sessions |
|---|---:|---:|---:|---:|
| fixed_5 | +0.126 | -0.200 | 19.90 | 5.00 |
| fixed_10 | -0.337 | -1.113 | 30.54 | 10.00 |
| fixed_15 | -1.172 | -2.305 | 38.84 | 15.00 |
| structure_5 | +0.073 | -3.298 | 30.40 | 9.55 |
| profit_guard_5 | -0.841 | -0.205 | 30.93 | 11.26 |
| time_review_5_10 | +0.013 | -1.136 | 23.86 | 7.85 |
| combined_5 | -0.110 | -0.687 | 20.56 | 5.16 |

**Interpretation:** no tested dynamic rule consistently outperformed fixed five-session exit on later cohort's mean return and downside. No rule has demonstrated statistically reliable positive alpha. Do not deploy. This is not out-of-sample model validation: rules were conceived after examining the period and may have selection bias. Repeated symbols, overlapping trades, liquidity, stale corporate actions, bid/ask, FX and point-in-time signal/event data remain unaddressed. Mean susceptible to extreme outliers. Same period is not an independent holdout. Need clustered uncertainty, robust trimmed/winsorized results, walk-forward, matched portfolio simulations and explicit missed-upside analysis.

Reproducible local script: dipsaus_dynamic_exit_replay.py; outputs: dipsaus_dynamic_exit_trades.csv and dipsaus_dynamic_exit_summary.csv.
