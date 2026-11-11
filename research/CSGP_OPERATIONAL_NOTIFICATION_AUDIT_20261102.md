# CSGP operational notification-chain audit — 2026-11-02

Status: VERIFIED CODE INSPECTION; NOT an active watch configuration or trade approval.

## Verified production topology
- Public default-branch workflow `.github/workflows/shadow-prealert.yml` schedules five-minute checks.
- `prealert_cadence.py` invokes `safe_runner.py prealert`; `safe_runner.py` uses private hydrated runtime state and `private_notifications.notify`.
- Public repository had successful scheduled runs on 2026-11-02; private repository's last listed run was 2026-10-09.
- ntfy sends are reserved and deduplicated; network uncertainty is not treated as successful delivery.
- `private_notifications.notify` sends research-phase upgrades (BREAKOUT-SEEN, BREAKOUT-HOLD-RETEST, EXECUTION-NEAR), not verified buy alerts.
- `ENTRY|US|CSGP|PHASE` persists the highest phase; a later independent setup in the same phase is not necessarily announced.
- Runtime watchlist configuration is hydrated from private secrets/state; presence of CSGP in actual private runtime data has NOT been verified. Existing ntfy screenshot proves a signal, not continuous dedicated monitoring.

## Safe requirements before activating a dedicated CSGP follow-up
1. Inspect runtime candidate source and its freshness/coverage; avoid adding a duplicate scanner.
2. Define a per-setup identity and reset criteria, plus a strict daily alert cap.
3. Block buy-ready claims without verified broker bid/ask/spread, event clearance, current-leg invalidation, R/R>=2, net EUR profit after FX/fees, and portfolio fit.
4. Add deterministic fake-sender tests: initial research signal, same-phase duplicate, material new setup, stale quote, missing structure, earnings block, failed delivery.
5. Run tests in research branch; require explicit production-change authorization before editing main/private runtime secrets.
6. Test notification transport without a real market-alert push, then verify scheduled run and delivery evidence.

No trading orders, no stoploss, no live notification sent.
