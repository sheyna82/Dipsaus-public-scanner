# DIPSAUS independent research QA checkpoint — 2026-11-06

Scope: inspected PR #65 research modules and the read-only public main copies of `shadow-prealert.yml`, `prealert_cadence.py`, `safe_runner.py`, `private_notifications.py`. This is **not** a full audit of the private scanner or all repository files.

## Confirmed and corrected
- Historical priority registration previously checked a caller-supplied `entry_at` without binding it to the candidate `entry_date`. Fixed in `integrated_verified_priority_selection.py` with regression tests; research CI #197 passed.
- A pre-existing hash-checked cash-policy fixture reused a registration for another entry date. Fixture corrected rather than weakening the guard.

## New isolated research component
- `isolated_50000_portfolio_ledger.py` models a €50,000 initial EUR cash balance, max six positions, date-granular entry/exit events, realized net PnL on exit only, and conservative no-same-day-reuse default.
- No DEGIRO connection, orders, live imports, strategy promotion, or automatic execution.
- The older `integrated_overlapping_capital_ledger.py` does **not** reinvest realized PnL; its documentation acknowledges that limitation. Do not treat it as an executable portfolio accounting engine.

## Open / not cleared
1. **Point-in-time:** candidate entry date binding is a partial guard. Historical source authenticity and public availability remain independently unproven; a self-declared verification boolean is not enough.
2. **Execution:** new ledger accepts realized PnL as offline input; it does not compute fills, bid/ask, FX, fees, partial fills, or settlement. It is not a broker simulation.
3. **Live signal inspection:** `private_notifications.phase` accepts several textual statuses and boolean fields as evidence of a phase. Need trace from provider quote timestamp, calculation, and data availability to the final alert, including stale/delayed feeds and deduplication; no claim of exploit or bug until reproduced.
4. **Operational completeness:** read-only inspection of four public files does not cover the private repository, provider adapters, all signal computations, or secrets/config. No declaration of '100% clean'.
5. **Data freshness:** point-in-time historical OHLCV, corporate actions, symbol changes, survivorship, and provider freshness require separate verification.

## Required next gates
- Run the new isolated ledger regression suite in CI and inspect failure logs.
- Reconstruct fee/FX/slippage calculations from broker statements and independent quotations; test currency conversion direction and double counting.
- Trace actual live alert inputs from quote timestamp through feature construction, stage classification, notification gate and state persistence. Add negative tests for stale timestamps, missing fields, NaN, and duplicate independent setups.
- Keep research separate from main and the private live scanner; require separate user authorization for operational integration.
