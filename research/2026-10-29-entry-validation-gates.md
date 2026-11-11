# Candidate execution gate — 2026-10-29

Follow-up to research/2026-10-29-us-eu-entry-candidate-handoff.md. **This document is a research specification, not an executed backtest or buy recommendation.**

## First research batch
- COHU — post-event: verify actual event release, contemporaneous OHLCV and gap, resistance, volume, spreads, historical post-earnings analogue cohorts.
- BKD — breakout/hold/retest: validate exact phase from persisted scanner row, time-aligned OHLCV, 2026-11-06 event proximity, trend and overhead supply.
- AMD and PLTR — pre-event: issuer-confirmed calendar, exit-before-event test, historical run-up cohort, slippage, event-gap scenarios; no holding through earnings by default.
- AMZN — EVENT_HOLD: no promotion until missing date/quote/implied move/historical gaps/consensus/stress inputs are complete.
- RHM.DE — recovery score 4: do not promote until independent quality gates pass.

## Data contract and pass/fail
For each symbol save as-of timestamp, market/time zone, source, event date/time, adjusted daily and intraday OHLCV (no future bars), bid/ask and DEGIRO tradability, price zones, volume and gap stats, first resistance, structural invalidation (manual reference only), target limit price, FX/fees/spread, expected gross and net EUR at €3500 notional, 5/10/15 trading-day outcomes, max adverse excursion, historical analog sample sizes, chronological out-of-sample validation, placebo/benchmark, confidence intervals, event risk and clear blocker codes.

Gates: R/R >= 2, gross potential >= EUR150 at €3500 notional, realistic net positive after friction, acceptable downside and gap risk, no chase, max 6 positions and portfolio fit. No automated stop-loss/stop-limit orders; no automated trading. No fabricated win rates or implied predictive edge from a notification phase. If no candidate passes, output NO TRADE.

## Implementation safety
Read-only evaluation on research branch; no change to main, private state, secrets, production notifications or live scanner. Research artifact must clearly label *observed data*, *model estimates*, and *unverified hypotheses*. Require tests before any later proposed production changes.
