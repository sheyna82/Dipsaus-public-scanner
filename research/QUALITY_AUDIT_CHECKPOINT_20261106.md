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

## CI and source audit extension — 6 November 2026

- CI workflow `research-integrated-evidence.yml` now includes the isolated €50k ledger, net-cost / signal-freshness / pivot tests and independent source-capture tests.
- GitHub CI run **#205** for commit `dd8a5976baeaab40aafdbc2ec63a9d1752f97e16` completed successfully; this covers the isolated ledger and cost/signal/pivot test suites.
- Independent source-capture module `isolated_source_capture_audit.py` verifies source SHA256 against actual bytes and checks claimed source availability, capture time and decision time. Tests reject tampering, late capture, late publication and timezone-naive timestamps.
- **Hash match is not publication authenticity:** independent publisher timestamp and source origin remain unverified; the module never marks evidence trade-ready.
- The newer workflow run #209 includes the source-capture tests; its result must be checked separately.
- **DEGIRO reconciliation remains blocked pending actual transaction statements** with fees, exchange-rate conversion, trade dates and quantities. No tariff has been guessed. No operational scanner modifications.

### Confirmed source-gate CI result
GitHub CI **#209**, run ID **42265054773**, completed **SUCCESS** for commit `d2fec12c1b2e9652c6239a183a2798ec2a164f32`. Logs explicitly show 8 isolated ledger tests, 10 cost/freshness/pivot tests and 5 source capture tests passing. This does not establish independently authenticated external source timestamps or DEGIRO statement reconciliation. **Operational release remains blocked.**
