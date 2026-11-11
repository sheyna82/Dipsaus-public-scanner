# DIPSAUS — historical evidence inventory and reuse gate (2026-11-05)

## Verified repository references (not independent market-data verification)

The existing historical branch `research/offline-technical-risk-20261021` contains:

1. `research/first_real_dynamic_exit_comparison_20261026.md` (blob `6c703dade96514a6380b4ba6f75ca2bf1a584205`): summary of 96 hypothetical entries across AMD, COHU, META and SPY; Yahoo five-year OHLC cited, source GitHub Actions run 40316862372 / artifact 12647277768. These are **not** independently verified raw quotes or a live portfolio.
2. `research/candidate_portfolio_capacity.py` (blob `7a7ae22219dc6ba93a7f58ce15a3014345989ba6`): existing chronological fixed-tranche capacity simulator with same-day cash reuse forbidden, symbol collision, max positions and deterministic priority.
3. `research/candidate_capacity_opportunity_audit.py` (blob `cb1a5c839e47b265c6c3079cd9df34cd44ace06e`): historical outcome audit of rejected versus accepted candidates, explicitly descriptive rather than predictive.
4. This branch's `research-capital-efficiency-exit-reassessment-20261103.md` already normalizes the 96-entry comparison to capital-session ratios. The underlying 96 individual trades have **not** been retrieved or reconciled here.

## Important methodological findings

- The 10-session variant had a higher descriptive profit-per-capital-session ratio than the 15-session variant in that specific previously inspected sample. The 40-session variant had the highest aggregate hypothetical P&L. Neither establishes optimal exits.
- Existing historical capacity work is more mature than a fresh date-only simulator; do **not** replace or duplicate it without comparison.
- Historical signal outcomes are post-entry labels. Never allow realized returns, exit dates or subsequent price action to influence as-of entry priority.
- The 96 entries are not confirmed independent DIPSAUS signals, not a six-position realized portfolio, and not a fresh out-of-sample sample.
- New settlement-calendar and cashflow modules on this branch remain **illustrative**; actual broker settlement, currency calendars, funding, daily MTM and fees are not authenticated.
- Account balances, holdings and the user's capital budget are private conversation context; do **not** commit them or public broker screenshots.

## Evidence-first next work (do in this order)

1. Locate exact immutable raw historical candidate/price artifacts and source hashes from the older branch or its CI runs. Distinguish repository text summaries from raw market data and verify time coverage, source, adjustments, currency, timestamps, corporate actions and missing sessions.
2. Retrieve an individual-candidate ledger with **as-of** signal date, entry session, symbol/instrument identity, exit session, exit variant, gross/net return and original data provenance. Fail closed if only aggregate tables exist.
3. Before code changes, compare the existing historical `candidate_portfolio_capacity.py` against the new modules for event ordering, settlement semantics, capital reuse, duplicate symbols, fees and lookahead.
4. Pre-register 5/10/15-session hypotheses, fixed six-position cap, tranche scenarios, benchmark, selection priority, costs and training/holdout boundaries. No optimization on the holdout.
5. Run identical chronological candidate streams across variants. Report rejected opportunity reasons, capital-session utilization, net P&L, drawdown **only if independently marked**, concentration, and quarterly/leave-one-symbol-out robustness.
6. Separate previously inspected historical results from truly unseen OOS or prospective validation; do not recommend operational sizing changes on descriptive results.

## Current decision

**HISTORICAL_DATA_RECONCILIATION_REQUIRED**. No verified individual trade ledger has been imported in this step. No new performance numbers are claimed. Research-only; no changes to main, operational scanner, broker orders or live sizing.
