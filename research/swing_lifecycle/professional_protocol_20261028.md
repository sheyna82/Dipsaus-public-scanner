# DIPSAUS — professional swing lifecycle research protocol (2026-10-28)

Research-only protocol. No changes to production, no automated orders, no stop-loss requirement. Do not merge into main without user approval.

## Objective
Maximize risk-adjusted net realized returns for recovery swings typically 5–15 trading days; avoid months-long involuntary holding. Explicitly track capital tie-up and exit decisions. Longer holds require an independently justified thesis, not hope of returning to cost basis.

## Before entry (mandatory decision record)
- Point-in-time timestamp and source freshness; entry bid/ask and execution costs.
- Sector/market regime, liquidity, FX, portfolio concentration, event/earnings calendar.
- Expected recovery horizon and entry thesis; realistic target and nearby resistance.
- Thesis invalidation conditions: structural, fundamental, event-driven, and time-based. Review manually; no automatic orders.
- Maximum acceptable loss and time/capital budget decided before entry.
- Explicit decision to hold through upcoming earnings or reduce exposure, with documented rationale.

## During position
- Review on trading days 3, 5, 10 and 15 and on material news, earnings or breakdowns.
- Distinguish: hold with thesis intact; reduce; exit; extend only on documented fresh evidence.
- Monitor mark-to-market EUR P&L, FX contribution, maximum adverse excursion (MAE), maximum favorable excursion (MFE), profit giveback, age, and drawdown duration.
- Trigger risk review on post-earnings failed follow-through, negative price/volume confirmation, stale data, concentration and time overrun.
- Use normal limit orders and manual approval. No stop-loss/stop-limit default; no automated execution.

## Research and validation
- Use timestamp-audited historical earnings/events, point-in-time information and tradeable bid/ask assumptions.
- Broad US/EU liquid DEGIRO-eligible universe with survivorship-bias checks.
- Chronological walk-forward and out-of-sample tests; compare 3/5/10/15d, conditional extensions and alternative exit rules.
- Include spreads, fees, FX, liquidity, overnight gaps, overlapping positions, capital constraints and realistic fills.
- Report distribution of net realized return, median, win rate, tail loss, drawdown, time in trade, capital turnover, profit giveback and missed upside. Compare to passive and simple rule baselines.
- Cluster by ticker/date to avoid false independent samples; uncertainty intervals and multiple-testing controls.
- EXE 2026-10-28 case is illustrative, not training target. Position closed: 114 shares sold in two fills (100+14) at $92.10. Do not store personal holdings in public runtime/reports; only anonymized case descriptions or synthetic examples.

## Deployment gate
No live signal until data integrity, backtest robustness, alert false-positive rate, forward paper/shadow monitoring and manual review pass. Never interpret technical signals as calibrated probabilities without validation.
