# OMXH25 actual Yahoo-to-Nasdaq dated close crosscheck — CI evidence

Date: 2026-11-09. **Research only; benchmark identity not independently approved.**

## Verified real-data execution

- Commit `122adfca2873adb73e510ecfdadc9320b5550a95`; GitHub Actions `EU relative strength offline gate tests` run **42639976030**.
- All **six** workflows associated with the commit completed successfully.
- Offline-gates job log: **109 tests, OK**.
- Benchmark-observation job first captured actual Yahoo responses, then ran `research_verify_europe_benchmark_raw.py` on the captured file. Actual output: `status=provider_bytes_reconciled`, `series_count=4`, `benchmark_identity_verified=false`, `trade_ready=false`.
- The same job then executed `research_compare_omxh25_official_close.py` on the actual captured JSON. For **2026-11-06**, Yahoo `^OMXH25` daily bar close **6221.7900390625** versus documented Nasdaq historical close **6221.79**. Difference **0.0000390625** index points; **two-decimal match=true**.
- Actual comparison output: `status=historical_value_match_unverified_identity`, `compared_days=1`, `venue_metadata=STO`, `venue_mapping_explained=false`, `official_eod_raw_bytes_verified=false`, `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`.
- Published artifact **13685111304**, archive SHA256 **04ae7c0a4a4c934fa93bf6746e9d1351d4f82bf04dbfd5433b299571022ffdab**, expires **2026-11-23 14:58:57 UTC**. Workflow upload includes captured Yahoo response JSON, raw-integrity receipt and OMXH25 comparison JSON. Upload step succeeded; ZIP members were not separately enumerated in this review.

## Evidence boundaries

This demonstrates that the actual preserved Yahoo daily close matches a **previously documented** official Nasdaq closing observation on a **single date**. The Nasdaq EOD response bytes for that observation have **not** been preserved and independently hashed here. The Yahoo `STO` exchange code remains unexplained. The comparison does not independently certify provider-index identity, index variant, session semantics for every date, or profitable trading.

## Next research requirements

1. Preserve official dated Nasdaq EOD observations with raw-response SHA256, acquisition UTC timestamp, and document/field definitions, without assuming the index methodology PDF is itself a dated EOD price record.
2. Compare multiple dates (including differing time zones/market sessions) with explicit issuer/provider provenance, without cherry-picking only matching dates.
3. Independently reconcile the Yahoo `STO` venue label against a reliable publisher/provider identifier, or keep the mapping gate closed.
4. Arrange durable external retention for the original Nasdaq source-document bytes before temporary GitHub artifacts expire.

No merge to `main`, no live scanner changes, no orders. Mandatory flags remain false for independent audit, benchmark identity approval and trade readiness.
