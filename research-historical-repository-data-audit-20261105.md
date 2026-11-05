# DIPSAUS — repository historical dataset audit, 2026-11-05

## Inspected raw repository files

Historical branch `research/offline-technical-risk-20261021` contains:
- `research_event_public_ohlcv_observations_202610.csv`: 12 rows, four symbols TSLA, META, AMZN and COHU, dates 2026-10-21 through 2026-10-23; all source_status `public_page_unverified`.
- `research_event_public_close_observations_202610.csv`: 12 manually extracted close rows over the same four symbols and three dates; provenance `public_historical_page_manual_extract`.

The source URLs are labels, not independent verification. The two files share observations and must not be counted as 24 independent observations. Neither provides a 5-, 10- or 15-session outcome horizon. Neither reconstructs the original 96-entry AMD/COHU/META/SPY comparison.

## CI and historical recovery observations

- Current research-branch commit `b2f5b6252c14bef18acaeee426e1dca1e556487b` passed research CI run 42013408475 and regression run 42013408491.
- The historic 96-entry source workflow run 40316862372 completed successfully but its current artifact list is empty.
- The historical branch contains a separate OOS replay workflow and input snapshot mechanism; its frozen artifact has **not** yet been recovered in this audit.
- The GitHub run listing is large and may be paginated; failure to locate a run in checked pages is not evidence that no matching run ever occurred.

## Decision

`INSUFFICIENT_HISTORICAL_OUTCOME_COVERAGE`: do not compute capital-sizing performance from these 3-day files, treat the duplicated close/ohlcv rows as independent, infer unavailable dates, or relabel a fresh provider fetch as original source data.

Next: locate a preserved frozen OOS input snapshot, or preregister a fresh authorized data acquisition with source hashes, calendar/corporate-action/FX controls, per-candidate ledger and untouched holdout. Existing capacity engine must be audited before reuse.

No live or main changes; research-only.
