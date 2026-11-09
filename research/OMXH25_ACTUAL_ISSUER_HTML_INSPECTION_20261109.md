# Real Nasdaq OMXH25 history-page capture inspection — 2026-11-09

## Actual immutable CI evidence

GitHub Actions run **42642571048**, artifact **13684634110** (`eu-benchmark-unverified-observations`), ZIP digest `sha256:19a44174a467894dbc728fcad8a6a10c6af809bd070e6144e5aba55dd89dd597`. Artifact expiry **2026-11-23 15:14:10 UTC**.

Captured file `omxh25-issuer-history-candidate.json` records `https://beta.indexes.nasdaqomx.com/Index/History/OMXH25`, retrieval **2026-11-09T15:14:10.360021+00:00**, HTTP 200, `text/html; charset=utf-8`, decoded raw response **69,381 bytes**, SHA256 **`a422861d1050d0035bad58c8f46c28e8c11ed15cbaeebe3d45ba8b8315d2babb`**. Independent local inspection of the downloaded artifact ZIP confirmed the decoded bytes match that digest.

The HTML contains `<title>History for OMXH25</title>`, the symbol **OMXH25**, page label **DATA AS OF 11/09/2026**, and a visible **Previous Close 6,221.79**. This is a useful issuer-hosted page observation supporting the earlier documented Friday November 6 historical close, *subject to the assumption that the immediately previous exchange session was Friday November 6*. The same HTML shows an as-of-day current index value of **6,292.45**, which must **not** be confused with the previous close or an end-of-day historical value.

The HTML table `id="historyTable"` has column headings **Trade Date, Index Value, Net Change, High, Low** but its `<tbody>` is **empty** in the preserved HTTP response. The page loads **`/Scripts/History.js?v=2.0.0.0`**; the historical rows appear to require separate client-side loading. No historical row dated 2026-11-06 with 6,221.79 is directly present in the captured HTML. Do not claim a verified historical EOD feed or use a guessed endpoint. A separate retrieval of the actual JavaScript and its documented history-data endpoint is needed.

## Evidence classification

- **Verified:** actual Nasdaq-hosted HTML response captured with date, HTTP metadata, raw bytes and SHA256; issuer page visibly reports Previous Close 6,221.79.
- **Not verified:** historical dated EOD response bytes, JS endpoint semantics, full multi-day issuer history, independent source authenticity beyond the HTTPS retrieval, Yahoo `^OMXH25` venue metadata `STO` mapping.
- **Mandatory gates:** `official_eod_raw_bytes_verified=false`, `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`.

No change to main, no live scanner modification, no trade authorization.
