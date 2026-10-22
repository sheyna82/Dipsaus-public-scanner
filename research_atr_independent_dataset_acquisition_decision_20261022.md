# ATR independent dataset acquisition decision — 2026-10-22

Research-only. No dataset acquired, no live scanner changes, no performance claim.

## Decision

The current local stock/SPY preflight passes synthetic tests, but the independent holdout remains **DATA_BLOCKED**. Do not mistake 295 passing software tests for predictive validation.

## Source pathways and limitations

| Pathway | Potential utility | Blocking checks |
| --- | --- | --- |
| Frozen NASDAQ Data Link WIKI/PRICES (through March 2018) | Historic US names, including some delisted securities, for offline methodological replication | API registration, rights, point-in-time identity, delisting proceeds, benchmark compatibility, survivorship completeness |
| CRSP/WRDS | Reference-quality security identities, delisting and corporate actions | Institutional access/license; no free access established |
| Public Yahoo chart endpoints | Recent exploratory surviving-ticker OHLCV | Not independently corporate-action verified, missing delisted coverage, no untouched independent universe |
| User-provided licensed local CSV snapshots | Practical zero-network local pilot | User must supply lawful files plus externally recorded SHA-256, adjustment policy, historical identity and benchmark alignment |

No pathway is currently verified to satisfy the full holdout protocol for free. A free historical dataset is not necessarily point-in-time, survivorship-clean or redistributable.

## Exact next acquisition procedure

1. Choose one lawful dataset and separately document provider, license, as-of retrieval timestamp, adjustment conventions and universe membership.
2. Store **raw data locally only**; never commit market-data bulk files, account identifiers, tokens or holdings to this public repository.
3. Independently record SHA-256 for both stock and SPY files before inspection; use `research_atr_local_pair_preflight.inspect_local_pair` to check hashes, structure, date alignment and suspicious jumps.
4. Verify corporate actions, security IDs, delisted coverage, benchmark exchange calendar and knowledge-time for earnings/events against independent documentation.
5. Freeze cohort, model, signal timing, 10-session embargo and evaluation metrics *before* viewing holdout labels.
6. Run `research_atr_holdout_evidence_gate.assess_holdout_readiness` as a metadata preflight. Even `METADATA_REVIEW_REQUIRED` is **not** independent verification or permission to claim performance.
7. Evaluate baseline versus ATR model only after external evidence review and adequate independent signal days/events; report missingness, delistings, calibration, paired Brier and uncertainty.

## Important design caveat

The current stock/SPY pair preflight requires **identical daily session dates**. This is deliberately strict and useful for simple US pilots, but can exclude legitimate mismatches (suspensions, different exchange calendars, missing vendor bars). Do not silently fill or forward-fill absent prices. Instead, log exclusions and build a documented exchange-calendar alignment policy before expanding to European or cross-market assets.

## Status

**DATA_BLOCKED** for independent ATR predictive claims. The existing 364 historical events are development data. Software CI green does not change this status.
