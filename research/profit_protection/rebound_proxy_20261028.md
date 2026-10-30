# Profit protection: exploratory rebound proxy (2026-10-28)

Local exploratory screen of 17,538 horizon outcomes (5/10/15 trading days) representing 5,967 distinct symbol-entry pairs, from `dipsaus_all_candidates_next_open.csv`. These are NOT independent observations and NOT an earnings or profit-protection validation.

Fixed feature available by day 3: first day <= -2% and days 2–3 >= +2%. Entry assumed at following open. Later period next_open_date >= 2026-08-01.

| Horizon | Cohort | N | <= -5% forward | Median forward |
|---|---|---:|---:|---:|
| 10d | rebound proxy | 358 | 28.8% | -1.025% |
| 10d | other | 2618 | 22.2% | -0.379% |
| 15d | rebound proxy | 347 | 39.2% | -2.393% |
| 15d | other | 2561 | 29.2% | -0.861% |

**Limitations:** May–Oct 2026 only; no verified point-in-time earnings timestamps; selection and survivorship biases; repeated symbol-date horizons; returns measured next-open-to-exit, not intratrade drawdown, realized portfolio P&L, or profit-buffer loss; no validated market/sector matching or uncertainty intervals. Never infer EXE-specific hold/sell probability. No production alert or order behavior change. Next: deduplicate by symbol-date and build position-level path-dependent maximum adverse excursion and earnings calendar with point-in-time audit, walk-forward validation, benchmark, friction and FX.
