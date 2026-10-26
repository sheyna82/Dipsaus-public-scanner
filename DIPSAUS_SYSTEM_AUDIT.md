# DIPSAUS — full-lifecycle audit and rollout checklist (research only)

## Existing implementation (observed in main, 2026-10-19)
- Discovery and early-phase alerts: private_notifications.py, recovery_prescreen.py, US and EU research.
- EU indicative recovery invalidation: europe_swing_research.py (explicitly NOT an executable stop).
- US execution gate: us_execution_gate.py (requires independent verified inputs).
- Profit zones, fast-crash override and structure review: profit_exit_watch.py.
- Ratcheting confirmed 1h higher-low reference, 2 hourly closes and corroboration: dynamic_profit_watch.py.
- Private notification deduplication: private_notifications.py.
- Safe read-only tests: validate-migration.yml (manual dispatch).

## New modules in this branch
- risk_budget_plan.py: EUR whole-share sizing at 50/75/100 EUR risk budgets; 3500 EUR maximum nominal tranche, R/R and gross profit gates. No execution.
- trade_lifecycle.py: portfolio and sector planned-risk aggregation, peak-profit giveback escalation, pretrade verification gate.
- Both are **standalone**: not wired into live runner, ntfy, broker, or private configuration.

## Required before production
1. Validate unit tests in CI; inspect exact workflow permissions and public/private data boundaries.
2. Verify entry, structural stop and target on completed bars, plus fresh bid/ask/spread and fees.
3. Convert provider prices and costs into **the same verified EUR basis**. Never mix USD provider quote with EUR DEGIRO listing.
4. Confirm stop-order support, trading venue, gaps/slippage, order expiry and interaction with outstanding take-profit orders; do not assume OCO.
5. Load actual holdings, filled quantities, cost basis, sector, FX, open orders, and stop coverage from private broker-verified configuration; never publish private holdings.
6. Determine whether current profit is truly positive net of costs. Peak-profit giveback alerts are informational; never infer guaranteed stop execution.
7. Add explicit alert priority and escalation with anti-spam that cannot suppress a newly urgent protective alert.
8. Preserve early discovery alerts even when execution validation is incomplete. Execution readiness is a separate decision.
9. Backtest point-in-time early signals, FER loss, RHM and GEHC missed entries; account for spreads, gaps, FX, events, look-ahead bias and rejected signals.
10. Shadow-run at least several sessions; review false positives, missed alerts and delivered notification evidence.
11. Define stale-feed/outage notifications, health heartbeat and manual fallback. GitHub Actions scheduling is not guaranteed to start on time.
12. Monitor open risk across correlated positions, event concentration, liquidity and max six positions.
13. Maintain a trade journal: candidate, rejected reason, fill, stop, risk in EUR, profit giveback, exit and R-multiple.
14. Require explicit user review before enabling live notifications; never place automatic trades.

## Decision vocabulary
- DISCOVERY: research candidate, not a buy.
- CONDITIONAL_ENTRY: price-triggered setup awaiting independent verification.
- ENTRY_REVIEW: all checks passed, human broker review required.
- HOLD_REVIEW: structure intact; no automatic sale.
- PROTECT_PROFIT_REVIEW: material giveback; inspect price action and broker orders.
- URGENT_EXIT_REVIEW: confirmed structure failure, severe giveback or rapid crash; verify and act promptly.
- DATA_BLOCKED: no confident trade decision on stale/unverified data.

The 35% and 60% peak-profit giveback fractions in trade_lifecycle.py are **initial research parameters**, not calibrated or live trading thresholds.
