# DIPSAUS — executed historical CSV cross-check (2026-11-05)

## Exact repository inputs
Branch: `research/offline-technical-risk-20261021`.

- `research_event_public_ohlcv_observations_202610.csv`
- `research_event_public_close_observations_202610.csv`

Read both GitHub file contents and compared every close observation by the exact
`(symbol, date)` key to the OHLCV `close` value, using numeric comparison.

| Audit metric | Observed |
|---|---:|
| OHLCV rows | 12 |
| Close-only rows | 12 |
| Unique symbols | 4 (TSLA, META, AMZN, COHU) |
| Unique dates | 3 (2026-10-21, 2026-10-22, 2026-10-23) |
| Matching close values | 12 |
| Unmatched or disagreeing close values | 0 |

**Interpretation:** these files overlap on all 12 symbol/date pairs and must not
be counted as 24 independent market observations. Agreement between files is
internal consistency only, not independent provider verification. OHLCV records
label sources `public_page_unverified`; close-only records label provenance
`public_historical_page_manual_extract`.

## Research gate

**BLOCKED_INSUFFICIENT_HORIZON:** three dates cannot produce validated 5/10/15
trading-session recovery outcomes. These files do not provide a source-bound
historical candidate ledger for tranche-size performance comparisons.

This audit did not fetch new quotes, modify the live scanner, or claim any
trading result. Further work requires a genuinely longer, frozen, licensed and
independently checked source series, or a retained historical OOS snapshot.
