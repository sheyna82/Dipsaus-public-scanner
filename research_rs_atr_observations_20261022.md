# RS/ATR four-symbol observations — 2026-10-22

Source: GitHub Actions run 39837506410, job observed-four-rs-atr-cohorts.
Data: public Yahoo two-year daily OHLCV, unverified; historical frozen event rule; sample-derived per-symbol medians, **post-hoc**, not independent holdout.

| Symbol | Events | RS lower mean net % | RS upper mean net % | ATR lower mean net % | ATR upper mean net % | ATR lower mean adverse % | ATR upper mean adverse % |
|---|---:|---:|---:|---:|---:|---:|---:|
| AMZN | 30 | -0.38465 | +0.20128 | -0.40083 | +0.21746 | -4.10581 | -5.38779 |
| COHU | 33 | +1.55859 | -0.89040 | +0.16126 | +0.59425 | -5.74826 | -11.18203 |
| META | 31 | +0.34313 | +0.52924 | -0.80832 | +1.75745 | -4.80900 | -5.64697 |
| TSLA | 28 | +0.22190 | +4.33857 | +0.63665 | +3.92382 | -7.17780 | -6.52190 |

**Interpretation:** Higher ATR coincided with higher average net terminal return in all four *post-hoc* within-symbol splits, but the average adverse excursion worsened for AMZN, COHU and META. Higher RS did not uniformly improve returns (COHU reversed). This does NOT establish causal value or future predictability. Median cutoffs were selected from the observed full sample, and each group contains only 14–17 signals.

**Decision:** Do not turn RS/ATR into live entry thresholds. Retain RS and ATR as candidate contextual indicators in research only.

**Next preregistered evaluation plan:**
1. Freeze factor direction and thresholds **before** evaluation. Avoid choosing the best cutoffs using holdout.
2. Construct multi-sector, survivorship-aware historical universe and independently verify OHLCV adjustments, earnings as-of timestamps, calendar and source licensing.
3. Evaluate paired same-date/same-symbol baseline vs factor-gated signals on a separate chronological holdout, with a purge/embargo and no parameter retuning.
4. Report signal coverage, rejected winners, mean net excess vs SPY, median and tail returns, maximum adverse excursion and severe adverse rate, separately by symbol and market regime.
5. Require enough independent events per cohort and include uncertainty intervals and multiple-testing caution. Never call the factor predictive until a genuine independent holdout passes.
6. Audit end-to-end live alert delivery independently. Green CI alone is not evidence of received alerts.

Safety: no live changes, no orders, no automatic stop-losses, no private portfolio or credentials, trade_ready=false.
