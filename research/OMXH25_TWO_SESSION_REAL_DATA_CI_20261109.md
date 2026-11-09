# OMXH25 two-session real-data reconciliation — 2026-11-09

**Evidence status: verified CI execution; NOT independently verified index identity.**

Commit `b31081d57b66af754ba019797e9bbc1e66fa6b13`; EU relative strength offline gate run **42640384288**.

- `offline-gates` log: **109 tests; OK**.
- `benchmark-observation` captured actual Yahoo data and validated four series: `provider_bytes_reconciled`, `research_only=true`, `benchmark_identity_verified=false`, `trade_ready=false`.
- Same job performed the real-data two-day comparison, `compared_days=2` and `historical_value_match_unverified_identity`:
  - **2026-11-05**: Yahoo **6254.2998046875**, documented FRED Nasdaq-origin close **6254.30**; difference **-0.0001953125** index points, two-decimal match.
  - **2026-11-06**: Yahoo **6221.7900390625**, documented Nasdaq history close **6221.79**; difference **+0.0000390625** index points, two-decimal match.
- Venue metadata **STO** remains unexplained; `venue_mapping_explained=false`.
- Official historical EOD raw-response bytes were **not** preserved for either reference close; `official_eod_raw_bytes_verified=false`.
- `independently_audited=false`, `benchmark_identity_verified=false`, `trade_ready=false` remain mandatory.
- Other workflow results at time of inspection: SPY, research evidence, OMXH25 source-document offline verification, European recovery capture completed success; AMD workflow was still in progress and should not be reported as complete until checked.

**Interpretation:** this is a reproducible two-session comparison of actual Yahoo captured values against documented published Nasdaq-origin historical closes. It is not a primary-source byte-level validation of the issuer's EOD historical feed, nor proof of Yahoo's exchange code mapping or price-index identity. The discrepancy log for Nasdaq's earlier displayed intraday-looking 6188.75 remains preserved.

**Next evidence:** issuer-side dated historical raw response with timestamp and hash, and a reliable independent Yahoo provider-to-index symbol/venue mapping. No change to main, live scanner, or orders.
