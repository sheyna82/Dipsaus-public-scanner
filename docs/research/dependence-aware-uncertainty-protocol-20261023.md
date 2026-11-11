# Dependence-aware uncertainty: preregistration draft

**Research-only protocol. No interval is currently validated, and no live alert may use it.**

## Unit and estimand
For each predetermined holdout event, compute the *paired* ATR-minus-baseline Brier and log-loss differences. Negative is favorable to ATR. Never bootstrap baseline and ATR independently.

## Dependence sources
Forward 10-session outcomes overlap, events on the same ticker share history, and different tickers can move together in market-wide shocks. Connected outcome-window counts are diagnostics, not an effective sample size.

## Candidate procedure (not yet implemented)
Use a **paired calendar-time moving-block bootstrap**: draw contiguous blocks of calendar sessions, taking *all tickers' paired event records for those dates together*. Preserve ATR/baseline pairing and contemporaneous cross-ticker co-movement. Define a block length before looking at holdout performance, with sensitivity analyses at longer blocks than the 10-session outcome horizon. Recompute mean paired loss differences in each replicate. Handle duplicated dates and variable daily event counts explicitly; report the resampling unit and effective coverage. Use percentile intervals only with clear caveats about finite-sample validity and nonstationarity. Do not treat 95% as a guarantee.

## Minimum checks before using intervals
- Independent chronological holdout, fixed universe, feature availability and outcome maturity verified.
- No event from a training or embargo period appears in holdout scoring.
- Positive and negative control fixtures: identical predictions produce zero differences; correlated synthetic outcomes must not be treated as independent draws.
- Predeclared bootstrap seed, iterations, calendar block length and sensitivity grid.
- Document missing sessions, regime shifts, small samples, ticker concentration, and whether intervals cross zero.
- Do not select a model based on the final untouched holdout; repeated peeking invalidates a naive significance interpretation.

## Decision boundary
A narrow interval excluding zero would not, by itself, prove a tradeable recovery signal. The current task predicts severe *downside* events, not profitable entry points. Any later shadow/live use requires separate recovery research and explicit approval.
