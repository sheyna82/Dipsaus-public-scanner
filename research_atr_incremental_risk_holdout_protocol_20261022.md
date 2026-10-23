# Frozen ATR incremental-risk holdout protocol (research only)

Status: PREREGISTERED DESIGN ONLY. No independent results yet. The existing 364 events, 15 usable symbols and their 196 signal dates have been repeatedly inspected and are development data, never an untouched holdout.

## Fixed question
Does the pre-signal boolean ATR14-percent expanding versus five trading sessions earlier improve the 10-session severe maximum-adverse-excursion risk forecast beyond (a) price above SMA20 and (b) SPY 20-session positive return? Severe risk is maximum adverse excursion <= -3%, not a stoploss instruction.

## Lock before sourcing independent outcomes
- Freeze all indicator definitions, event eligibility, horizon, thresholds, missing-value handling, cost assumptions, and this protocol. Do not tune on the test.
- Obtain a genuinely uninspected, point-in-time dataset with benchmark alignment, documented timestamps, raw/adjusted policy, splits, dividends, delistings, trading calendar, symbol universe, provider rights and hashes. If any cannot be verified, fail closed and report DATA_BLOCKED.
- Prefer a future prospective collection after protocol freeze; historical dates already inspected in any related research are not independent. No cherry-picking sectors or symbols from the 15-stock development set.
- Holdout unit is signal date and symbol, with a >=10 trading-session embargo between training/validation/test, plus sensitivity to shared calendar-day clusters and adjacent 14-calendar-day blocks.
- Freeze the baseline model as four empirical structure x SPY market cells; ATR model adds the ATR boolean within each cell. Fit any smoothed cell risk rates on development/training only. Never estimate rates from test labels. If a training cell is empty, use a prespecified pooled prior and report its use.
- Evaluate paired baseline versus ATR-enhanced forecasts on identical eligible test events. Primary: change in Brier score (lower better); secondary: log loss with probabilities clipped to [0.01,0.99], calibration by predicted-risk bins, severe-event recall at a frozen alert budget, and max drawdown diagnostics. Report all counts and missingness.
- Uncertainty: resample signal-date blocks (and symbols as sensitivity), not independent events. Report confidence intervals, sector/year stability and failure cases. Do not call a small positive difference validated.
- If the independent holdout has fewer than 100 distinct signal dates, or fewer than 30 severe events, mark INSUFFICIENT_POWER; these are reporting gates, not retrospective selection rules. No trading deployment from an underpowered sample.
- No automatic stoploss, no live scanner modification, no calibrated probability claims and no PR merge without separate user approval.

## Known development findings (not validation)
ATR pooled severe-risk delta -7.823 percentage points; 9/15 symbols favorable, 6 unfavorable; 52 same-day matched dates mean -4.167 pp; 14-day offset analyses favorable; conditional structure/market cells 3 favorable and 1 unfavorable, with unstable chronological effect for the unfavorable cell. These were all observed before this protocol and are not independent evidence.
