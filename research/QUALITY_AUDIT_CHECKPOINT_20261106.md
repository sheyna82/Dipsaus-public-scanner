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

## Freeze checkpoint — 2026-11-06: ex-ante net return research

**Decision:** user approved the historical cost reconciliation and requested a code freeze. No operational promotion, no merge to main, no live scanner edits, no broker connectivity, and no automatic orders. The private DEGIRO statements, account ledger, normalized transaction data, and locally generated source/test files must **never** be committed to this public repository.

**Local-only research evidence (not uploaded):** `dipsaus_ex_ante_cost_engine.py`, `test_dipsaus_ex_ante_cost_engine.py`, and `DIPSAUS_ex_ante_kosten_onderzoeksresultaten_20261106.md`. These files were developed and tested locally; **they are not part of this branch's tracked code**, and the freeze does not imply they passed GitHub CI.

**Verified local result:** 12/12 unittest cases passed on 2026-11-06, covering ask/bid execution, separate entry/exit FX scenarios, explicit broker fees per side, percentage FX fees, adverse slippage, EUR-only trades, invalid input, double counting prevention, and periodic venue connectivity fees. The bid/ask spread is already included in executable prices and is not subtracted twice. Connectivity fees are portfolio-period obligations, not charged once per trade; the model distinguishes already-paid fees, newly due fees, and analytical allocation.

**Hypothetical 10-share example:** ask 100, target bid 110, EUR/quote 1, EUR 2 broker fee per side, 0.25% FX per side: base **+EUR 90.75**; exit FX 0.95: **+EUR 35.89**; exit FX 0.95, bid 108, adverse slippage 1 per share on both sides: **-EUR 2.57**. These inputs are illustrative, **not verified current DEGIRO tariffs or a forecast**. Newly due EUR 2.50 connectivity fee changes the base portfolio-period outcome to EUR 88.25, not the standalone trade PnL.

**Historical account reconciliation:** the prior private audit reported 40/40 grouped orders matched, 62/62 execution rows reconciled within one cent, and an additional EUR 2.50 Bolsa de Madrid connectivity fee. These figures are recorded as prior local findings; personal transaction-level evidence is intentionally absent from GitHub and cannot be independently reproduced from this public dossier alone. Historical reconciliation is accepted by the user but does not validate prospective price/FX/cost forecasts.

**Open release gates (frozen backlog):** (1) independently verify current DEGIRO transaction, venue connectivity and FX tariffs by instrument, exchange and fee plan, including effective dates; (2) calibrate timestamped FX/spread/slippage scenarios with independently sourced data; (3) preregister scenario forecasts and compare them prospectively with subsequent actual executions without post-hoc adjustment; (4) validate venue-level once-per-period charges and reconcile actual cash movements; (5) develop **synthetic/anonymized** test fixtures that cannot reconstruct personal transaction records and run them in GitHub CI; (6) separately review integration and data provenance before any operational release.

**Freeze status:** research only; **not trade-ready**. Do not edit the cost engine, merge, or change operational configuration until the user reopens the backlog.
