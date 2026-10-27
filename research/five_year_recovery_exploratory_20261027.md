# DIPSAUS five-year exploratory recovery check — 2026-10-27

**Research only. NO-GO for strategy promotion.** Source: GitHub Actions run 40515277880, artifact 12739376023, `dipsaus-diversified-sector-prices-unverified`, commit 8a5949b. This artifact has 18 US equities across nine sectors, plus SPY/IWM; 1,255 daily unverified Yahoo Chart OHLC rows per symbol, approximately 2021-10-27 to 2026-10-27. **Independent source verification and corporate-action adjustment checks not completed.**

Method: trailing 20-close maximum; trigger when latest close <= 90% of that max. Variant requires close > last-five-close mean. Enter at next available open; exit at open after 5/10/15 sessions; subtract 50 basis points total; no overlapping trades within symbol and strategy/horizon. Fixed calendar partition by signal decision date: training before 2025-01-01; holdout 2025-01-01 onward. **Important: this is a retrospective exploratory holdout, not a preregistered truly unseen validation.** Training signals may exit after the split boundary, requiring purge/embargo in a proper study. Per-symbol trade selection and weighting are not portfolio simulation; same-date and cross-symbol signals correlate.

## Mean net returns by cohort

| Horizon | Dip train (n) | Dip holdout (n) | Dip+MA5 train (n) | Dip+MA5 holdout (n) |
|---|---:|---:|---:|---:|
| 5 sessions | -0.226% (390) | +0.207% (186) | -1.115% (162) | -0.028% (83) |
| 10 sessions | +0.319% (266) | +0.759% (121) | -0.469% (131) | +0.583% (61) |
| 15 sessions | +0.503% (215) | +3.214% (96) | +0.299% (109) | +0.279% (54) |

At 15-session holdout, plain dip: median +0.882%, 46.9% negative, worst -14.586%; dip+MA5: median +0.603%, 48.1% negative, worst -15.041%. The plain dip 15-session holdout advantage could be regime or stock concentration and is not validated. Do not infer 15 days is optimal; earlier studies looked at other horizons, making post-hoc selection bias possible.

## Required professional follow-up

1. Verify source prices, split/dividend adjustments, data license and survivorship. Add European and delisted-universe cohorts.
2. Purge/embargo chronological boundaries and pre-register hypotheses before untouched future test periods.
3. Compare against date-matched SPY/IWM and sector baselines; compute cross-sectional and calendar concentration.
4. Model maximum six simultaneous holdings, realistic entry liquidity, currency/FX and stress costs; report drawdown, tails, and annualized net portfolio returns.
5. Do not promote strategies based on average trade return alone; no auto orders or main merge.
