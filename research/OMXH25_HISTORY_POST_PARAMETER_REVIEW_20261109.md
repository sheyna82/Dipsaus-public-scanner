# OMXH25 HistoryData POST parameter review — 2026-11-09

**Status: endpoint and EOD selector evidenced; exact date serialization still under review. No live POST yet.**

Primary source script: Nasdaq `/Scripts/History.js?v=2.0.0.0` raw bytes captured in GitHub run **42643238270**, SHA256 `5f679b2c2be40f37750edcb63f41f0e9fe852f7ed0c60ceebd355c1fec456a0c`.

The script's `GetHistoryData()` sends `POST /Index/HistoryData` with `id`, `startDate`, `endDate`, and `timeOfDay`. The actual HTML page offers `EOD` and `SOD`; the research capture now **requires EOD**. This is a contract constraint, not evidence that any POST has returned historical values.

**Unresolved before executing:** exact implementation of `toISONonUtcString()` in Nasdaq's included JavaScript dependencies; exact date range semantics and timezone handling; any CSRF/session requirements. The capture currently accepts `YYYY-MM-DDTHH:MM:SS` as a candidate format, not yet proven to be the site's actual wire format. Do not run or report an issuer POST as official until this is reviewed.

GitHub run **42643947853** reported 125 tests, one ERROR because the second call in the immutability test still passed `timeOfDay="0"` after the EOD restriction. Fixed in commit `ff4f4c63cc00750859b4333349fde692d2971ddb`; CI result for this fix must be inspected separately.

Fail-closed: `official_eod_raw_bytes_verified=false`, `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`. No main/live changes or trades.
