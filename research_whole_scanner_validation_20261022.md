# DIPSAUS whole-scanner validation priorities — 22 October 2026

**Scope:** Entire scanner, not any individual ticker. Research branch only. No
changes to production notifications, orders, thresholds, or portfolio state.

## Acceptance criteria before a model is called predictive

1. **Universe and coverage.** Publish eligible US/EU symbols, delisted coverage,
   excluded symbols and reasons, sector/year distributions, and market-hours coverage.
2. **Data provenance.** Verify point-in-time OHLCV, corporate actions, earnings
   dates, timestamps and missing-bar policy. Unknown is never silently accepted.
3. **Recovery selection.** Freeze candidate scoring before untouched chronological
   holdout. Compare selected versus skipped, benchmark and equal-weight baseline
   at identical dates, costs and holding horizons.
4. **Risk and false alerts.** Measure severe downside, drawdowns, alert precision,
   missed moves, signal lead time and repeated-alert rate. Report uncertainty by
   ticker/time block, including adverse regimes.
5. **Profit protection.** Test exit/limit-sale research separately from entry
   quality; never place a stoploss or broker order.
6. **Notification reliability.** Audit generated -> eligible -> attempted ->
   delivered/confirmed states. CI success alone does not prove user delivery.
7. **Operations.** Verify latency, data-source degradation, duplicate suppression,
   API limits and EU/US schedule handling.
8. **Safety.** Research results must not change live trading or alerts until
   independently validated and explicitly approved.

## Current honest status

- Unit-test success proves software checks execute, **not** profitable predictions.
- Existing four-ticker event holdout is small and insufficient for marketwide claims.
- Multi-ticker independent chronological holdout and reliable live notification
  delivery remain unproven.
- The separate EXE minute replay is a data-quality case study, not the roadmap.
- The readiness audit deliberately reports UNKNOWN for evidence not explicitly
  supplied; it is not a pass/fail score inferred from green CI jobs.

## Next research milestones

1. Map current production scanner workflows to the eight validation areas without
   changing them.
2. Build an immutable, representative marketwide evaluation dataset and coverage
   report with provider and exclusion manifests.
3. Pre-register and run cross-sector chronological holdout, then audit false
   alerts and downside alongside returns.
4. Independently verify end-to-end notification delivery and timing.
5. Review findings together before any live changes.
