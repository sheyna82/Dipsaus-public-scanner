# Paired exit-horizon exploratory test — 2026-10-28

Source: local historical research file dipsaus_all_candidates_next_open.csv. 5,746 complete symbol-entry pairs, 3,459 tickers. Same pairs compared at horizon labels 5/10/15; these horizon labels come from existing data and do NOT prove exactly 5/10/15 days of holding from next-open entry (inspect date definitions before execution claims). Research-only, no live signals.

Later-entry cohort (entry_date >= 2026-08-01): n=2,326 pairs.

| horizon label | median forward return | share <= -5% | share <= -10% |
|---|---:|---:|---:|
| 5 | -0.209% | 11.99% | 3.22% |
| 10 | -0.801% | 25.84% | 10.88% |
| 15 | -1.172% | 33.02% | 17.45% |

Full cohort medians: -0.323%, -0.299%, -0.299% respectively; extreme outliers drive positive means, so do not infer that longer holding improves typical outcome.

**Critical limitations:** historical outcome labels may differ from actual days held from next-open; no daily price paths, MFE/MAE, FX, bid/ask, event timestamps, sector/market matching or portfolio execution. Same ticker and overlapping dates create correlated observations. Later cohort is not a pre-registered independent holdout. No statistically validated predictive edge or automatic 5-day exit is established.

Next: audit exact exit_date minus next_open_date for each horizon, construct point-in-time daily paths and test manual review/conditional exit policies using chronological walk-forward, costs and realistic fills. Do not modify main or live order behavior.
