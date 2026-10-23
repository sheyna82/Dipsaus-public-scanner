# DIPSAUS: from structural tests to predictive evidence (research only)

Status: protocol proposal; **not** historical validation or permission to trade.

## Question
Does an ATR-augmented downside forecast improve on a predeclared baseline for a severe forward drawdown (at least 8% within 10 subsequent trading sessions)?

## Minimum evidence before making performance claims
1. Record source, redistribution/use rights, immutable file digest, retrieval and **actual as-of availability** of features and benchmarks. Reject or quarantine missing publication times; a plausible timestamp in a self-reported manifest is not verification.
2. Verify exchange sessions, adjusted OHLC consistency, corporate actions, delisted names, benchmark independence and survivorship controls. Include rejected/missing symbols in coverage counts.
3. Freeze the stock universe, outcome definition, 10-session horizon, thresholds, baseline, ATR extension, splits, embargo, scoring and minimum cohort sizes **before** evaluating unseen data.
4. Walk forward chronologically. Train only on labels already available at each decision boundary; use completed bars only. Keep evaluation windows disjoint or account for overlapping events in uncertainty estimates.
5. Report paired Brier and log-loss differences, cohort counts, calibration, missingness, fallback rates, uncertainty intervals, and comparisons across market regimes. Include failures and negative results.
6. Keep a final untouched, genuinely independent holdout. Do not select models or thresholds on that holdout. Require out-of-sample improvement across meaningful samples before proposing live shadow alerts.
7. Run a separate recovery/entry study. A model predicting downside risk is **not** automatically a recovery or entry model.
8. Only after independent evidence: run non-trading shadow forecasts, compare alert lead time, false alarms and coverage, then consider production changes with explicit approval.

## Immediate blocker
Existing GitHub synthetic tests demonstrate structural behavior, not predictive accuracy. The historical data source's rights, point-in-time reconstruction and universe coverage remain unverified. Do not mark `research_data_ready`, `independent_holdout_verified` or `trade_ready` true.

## Software comparison discipline
Freqtrade, Backtrader, vectorbt, exchange_calendars and pandas_market_calendars are research references, **not** approved dependencies. Verify version-specific licenses, security and actual incremental utility before reuse. No external source code copied here.

## Operational boundary
This file is documentation only. No live scanner, alerts, orders, portfolio data, secrets or main branch changes.
