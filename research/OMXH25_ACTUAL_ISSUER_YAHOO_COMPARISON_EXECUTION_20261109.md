# OMXH25 exact repository comparison CLI executed on original combined artifact — 2026-11-09

## Execution evidence

- Original GitHub Actions run: `42679785882`; artifact: `13700999627`.
- Original ZIP path in isolated workspace: `omxh25-history-post-attempt-13700999627.zip`.
- Recomputed ZIP SHA256: `b0aaeb32563f96f91dcc7372c96a183fb247a0cf3392c4bc94111fd23b8c0465` (matched).
- Ran exact `research_compare_omxh25_actual_issuer_yahoo.py` module against original ZIP, using the repository's original `research_validate_omxh25_real_history_post.py` dependency.
- Exit code **0**, actual output status **`three_session_issuer_yahoo_value_match_unverified_identity`**.

## Original CLI result

```json
{"benchmark_identity_verified": false, "comparisons": [{"date": "2026-11-05", "difference": -0.00112374, "nasdaq_value": 6254.30092842816, "two_decimal_match": true, "yahoo_close": 6254.2998046875}, {"date": "2026-11-06", "difference": -0.00252242, "nasdaq_value": 6221.79256147799, "two_decimal_match": true, "yahoo_close": 6221.7900390625}, {"date": "2026-11-09", "difference": 0.00011992, "nasdaq_value": 6278.94714570764, "two_decimal_match": true, "yahoo_close": 6278.947265625}], "independently_audited": false, "issuer_source_sha256": "13a001c9ae5f92b78bfa0dfca421b5f1cb127d737578f983c9efc4ff94edaf2c", "matched_sessions": 3, "research_only": true, "status": "three_session_issuer_yahoo_value_match_unverified_identity", "trade_ready": false, "venue_mapping_explained": false, "yahoo_exchange_name": "STO"}
```

This is an executed CLI comparison, not merely a synthetic test. Only 3 dates were sampled. `STO` venue label remains unexplained; official index variant and long-run mapping remain unproven. **No promotion**: `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`. No main/live modifications or trades.

## Subsequent repository-code consistency review (2026-11-09)

A direct read of `research_compare_omxh25_actual_issuer_yahoo.py` on the research branch found that its current `compare_archive` return literal is `three_session_value_match_unverified_identity`, **not** the longer status string recorded above as the original CLI output. The historical CLI transcript above is retained verbatim as a claimed observation, not silently rewritten. The cause of the discrepancy (different local code revision, transcription, or another factor) has **not** been established. Do not treat the quoted CLI status as reproduced by the currently inspected branch version until the exact executable commit and original artifact are rerun together.

The three reported value matches remain historical evidence, but this discrepancy prevents claiming fully reconciled end-to-end execution provenance. Safety gates remain `venue_mapping_explained=false`, `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`. No benchmark identity promotion is authorized.
