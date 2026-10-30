# Observed execution-cost stress — 22 October 2026

Source: GitHub Actions run 39828884171, job alternative-four-ticker-source-probe; Yahoo chart daily OHLCV; completed sessions only (65 per symbol).

Frozen descriptive rule: existing three-rising-closes and five-close average recovery event with risk exclusion, next-open to tenth-session close, nonoverlapping entries. **This is not the preregistered score >=5 multi-ticker strategy**, and these four names were not independently sampled.

| Symbol | Events | Net mean at 10 bps/side | Net mean at 25 bps/side | Net mean at 50 bps/side |
|---|---:|---:|---:|---:|
| AMZN | 3 | -1.03689% | -1.33689% | -1.83689% |
| COHU | 2 | -3.43910% | -3.73910% | -4.23910% |
| META | 3 | +3.73638% | +3.43638% | +2.93638% |
| TSLA | 2 | +0.18010% | -0.11990% | -0.61990% |

Higher cost levels are scenario stress tests, not observed spreads or verified execution costs. The fixed selection produces 10 events total; no independent holdout or statistically defensible inference. These are not proof of prediction or a live trading recommendation.

**Critical next experiment:** follow `research_preregister_multiticker_holdout_20261022.md`, including the *different* frozen recovery score >=5, unbiased multi-sector universe with delisted coverage, real historical earnings availability, same-date skipped/benchmark comparators, 10-session embargo, source and adjustment verification, and an untouched chronological test. Do not substitute the four-event rule or its historical results for the preregistered score experiment. No live integration or PR merge.
