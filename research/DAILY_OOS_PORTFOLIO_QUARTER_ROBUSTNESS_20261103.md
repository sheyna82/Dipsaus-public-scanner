# Daily OOS portfolio quarterly robustness — inspected artifact 13007728223

Source: GitHub Actions run 41121367948, `candidate-feature-oos-historical-report` ZIP, `candidate_feature_oos.json` and `candidate_feature_portfolio_quarters.json`. This is a **daily** OHLCV portfolio experiment, not the intraday episode detector.

Common parameters: 10-session hold, 50 bps modeled cost, US convenience universe, SPY reference. Baseline vs three-feature filtered arms use calendar-matched descriptive comparisons, but **different selected trades and capital occupancy**. No independent prospective validation or daily marked-to-market verification.

| Pattern | Arm | Accepted | Simulated realized PnL (€ nominal model) | Positive / negative quarters | PnL excluding best quarter |
|---|---|---:|---:|---:|---:|
| recovery_from_prior20_low_3to15pct | baseline | 238 | +7141.74 | 5 / 3 | +2000.18 |
| recovery_from_prior20_low_3to15pct | filtered | 78 | +720.58 | 4 / 4 | -587.63 |
| breakout_prior20 | baseline | 183 | +3376.87 | 3 / 5 | -1152.14 |
| breakout_prior20 | filtered | 15 | +955.40 | 3 / 3 | +115.49 |

Interpretation: filters reduce sample size and realized nominal PnL, but these totals are NOT equal-capital exposure-adjusted alpha, cannot establish baseline superiority, and do not include independently verified execution. Quarter signs are descriptive, not confidence intervals. The filtered breakout arm has only 15 accepted trades and six active quarters. The baseline recovery arm has 401 rejected signals versus 7 filtered, so capacity selection materially differs.

**Research gate**: do not promote the three-feature filter or baseline based on these totals. Next compare paired eligible event pools, capital-days/turnover, maximum drawdown and quarter-clustered uncertainty, with point-in-time corporate actions and execution checks. No live scanner or trading changes.
