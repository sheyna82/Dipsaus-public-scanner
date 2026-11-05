# External research software comparison — 2026-10-23

Scope: **research only**, no installation, vendoring, imports, runtime dependency or production changes.

| Candidate | Potential reusable idea | Integration boundary | Verification outstanding |
| --- | --- | --- | --- |
| Freqtrade | Lookahead-analysis inspired leakage diagnostics; hyperparameter and strategy comparisons | Design independent tests, do not copy implementation | Confirm exact source license and version, crypto-specific assumptions, dependency security |
| Backtrader | Event-driven backtesting and order execution simulation | Compare methodology with chronological DIPSAUS experiments | Confirm maintained version, license, execution semantics and security |
| vectorbt | Vectorized scenario/parameter sweeps and portfolio diagnostics | Compare outputs on isolated synthetic fixtures | Check edition-specific license and restrictions, dependency security |
| exchange_calendars | Exchange-specific sessions, holidays and exceptional closures | Consume pinned offline exported sessions via existing adapter | Validate release/version, provenance, timezone and exchange mapping |
| pandas_market_calendars | Alternative session calendar for cross-checks | Export only; compare disagreements offline | Validate pinned version, provenance, calendar semantics and dependencies |

## Rules before reuse

1. Record exact repository, immutable commit/tag, license file and SPDX identity; **unknown means not approved**.
2. Check whether copying or linking code creates redistribution/copyleft obligations. Free to use does not mean free to copy into this repository.
3. Review transitive dependencies, vulnerability advisories, repository activity and suspicious install/build scripts. No arbitrary network execution or credentials.
4. Compare on synthetic, deterministic, time-ordered fixtures before real market data; never mistake fixture pass for predictive evidence.
5. For each borrowed idea, measure incremental value against DIPSAUS baseline (Brier/log loss and paired uncertainty), leakage, false alerts, and compute budget.
6. Reject source data without separately verified usage rights, point-in-time provenance, corporate-action policy, delisting coverage and exchange session completeness.
7. Keep experiments on research branch and draft PR #62; never merge or change live alert logic without explicit approval.

**Status:** candidate screening only. No external code security audit, license clearance, installation or predictive benchmark completed. This document does not certify any candidate as safe.
