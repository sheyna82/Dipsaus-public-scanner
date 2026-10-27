# DIPSAUS — exploratory ranking comparison (2026-10-27)

**NO-GO for promotion.** Unverified historical OHLC from GitHub Actions artifact 12739376023; 18 US stocks; dates 2025-01-02 through 2026-10-27. Same dataset used to compare/rank variants, therefore NOT an untouched holdout. Fixed 21,000 account units, six slots of 3,500, no leverage, next-open entry, fixed exit at next open after 5/10/15 sessions, 0.5% round-trip friction. Trailing 20-close drawdown >=10% signal. Candidate priorities: deepest drawdown, shallowest qualifying drawdown, highest/lowest trailing five-session return, highest/lowest trailing 20-session daily return standard deviation. No sector cap.

| Horizon | Deepest dip | Shallowest dip | Strongest 5d | Weakest 5d | Lowest vol | Highest vol |
|---|---:|---:|---:|---:|---:|---:|
| 5 sessions | +5.54% | -3.92% | -4.78% | +6.43% | -4.04% | +5.21% |
| 10 sessions | +12.08% | +7.25% | +8.43% | +14.23% | +5.96% | +11.12% |
| 15 sessions | +19.54% | +13.29% | +13.18% | +18.33% | +12.36% | +21.84% |

**Critical accounting limitation:** this new simplified ranking engine uses fixed notional profit/loss, approximate cash bookkeeping and fills; does not mark positions to market daily, so max drawdown is **not available**. It is not identical to prior six-slot simulator and **must not be compared as if exact replication**; prior deepest-dip 15-day result was +20.89%, versus +19.54% here. Investigate differences before drawing cross-run conclusions. Results exclude dividends, FX, liquidity, delistings and corporate-action verification. Different symbols/dates can be highly correlated. Risk-adjusted returns, exposure-matched benchmark, and sector concentration are unmeasured.

**Decision:** high-volatility priority had highest 15-day return in this sample, but this is post-hoc winner selection and may increase downside. Do not select live ranking from these results. Next: reconcile engines, reconstruct daily marked-to-market equity and drawdowns, pre-register ranking, purged time split and separate untouched forward test; expand universe and source verification. No auto-orders, no merge to main.
