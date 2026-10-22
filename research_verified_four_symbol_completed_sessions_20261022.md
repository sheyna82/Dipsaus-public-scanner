# Four-symbol completed-session verification — 22 October 2026

**Scope:** Historical predictive research, not production notifications.
Verified GitHub Actions run 39826054270 (successful) and original run
39800255450 (9/9 jobs successful). Results from the
`alternative-four-ticker-source-probe` job, executing
`research_four_event_history_results.py`.

| Symbol | Completed bars | Signals | Positive | Selected net mean % | Fixed-calendar mean % | Severe intraperiod | Signal dates |
|---|---:|---:|---:|---:|---:|---:|---|
| AMZN | 65 | 3 | 1 | -1.03689 | 0.22810 | 3 | 2026-09-03; 2026-09-21; 2026-10-07 |
| COHU | 65 | 2 | 1 | -3.43910 | 0.51872 | 2 | 2026-09-04; 2026-10-01 |
| META | 65 | 3 | 2 | 3.73638 | 10.06317 | 1 | 2026-08-24; 2026-09-14; 2026-10-05 |
| TSLA | 65 | 2 | 1 | 0.18010 | 6.13389 | 1 | 2026-09-03; 2026-09-22 |

All four observed payloads originally contained 66 bars; one unconfirmed
current-day bar was excluded. Signal counts, dates, and per-symbol net
means matched the earlier ten-signal observations. The prior run also
reported `discarded_unconfirmed_bars=1` for all four symbols; therefore
the matching signal results alone are **not** proof that the historical
gate caused an outcome change.

## Research interpretation

- All four technical selected means are below the fixed-start calendar
  comparison. These are tiny, nonrandom, nonindependent samples.
- Each chronological test segment contains only **one** signal per symbol,
  far below the configured screening minimum of 30. No predictive edge
  established.
- The phase-shifted calendar comparisons are exploratory sensitivity
  checks, not independent holdout or valid significance tests.
- Corporate actions, independent provenance, earnings dates, complete
  exchange calendar and survivorship bias remain unverified.
- The four names were prompted by observed notifications and cannot serve
  as an untouched representative marketwide universe.

**Next substantive experiment:** use the existing preregistered
multi-ticker protocol to construct a provider-audited cross-sector,
chronologically held-out sample with identical transaction assumptions
and comparators. Do not adjust the signal threshold to fit these names.
No live scanner, notifications, or orders changed.
