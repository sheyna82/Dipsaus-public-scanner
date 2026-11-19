# Nasdaq OMXH25 actual History.js endpoint discovery — 2026-11-09

**Research-only. Actual source inspected, endpoint not yet executed.**

GitHub Actions run **42643238270**, artifact **13686292573** (expires 2026-11-23 15:18:04 UTC) captured the Nasdaq-hosted script from:

`https://beta.indexes.nasdaqomx.com/Scripts/History.js?v=2.0.0.0`

The script is **75,710 bytes** and its decoded SHA256 is **`5f679b2c2be40f37750edcb63f41f0e9fe852f7ed0c60ceebd355c1fec456a0c`**. The downloaded artifact was inspected locally; the decoded bytes matched the hash.

## Actual data request found in script

Function `GetHistoryData()` invokes jQuery `$.ajax` with:
- `url: "/Index/HistoryData"`
- `type: "POST"`
- `dataType: "json"`
- form data `id: $("#symbol").text()`, `startDate: (startDate ? startDate.toISONonUtcString() : null)`, `endDate: endDate.toISONonUtcString()`, `timeOfDay: $("#timeOfDay").val()`.

Function `GetChartData()` separately invokes `POST /Index/HistoryChartData` with `id`, `startDate`, `endDate`. `POST /Index/HistoryYTDLastTradeDate` is another separate endpoint. The HistoryData request is the primary candidate for dated table rows.

**No POST request has yet been executed or archived.** Parameters and the exact date serialization need to be derived from the original page and JS; do not invent values. A live request may be blocked by anti-automation or cookies. The capture must preserve HTTP status, raw bytes, timestamp, response content type, SHA256 and explicit failure reasons. A successful HTTP response is not itself proof of correct EOD semantics. Do not promote identity.

`official_eod_raw_bytes_verified=false`, `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`.

No changes to main, live scanner or trading.
