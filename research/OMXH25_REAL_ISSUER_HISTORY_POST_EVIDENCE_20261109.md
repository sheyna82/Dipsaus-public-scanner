# OMXH25 actual issuer HistoryData POST — first raw EOD observation (2026-11-09)

**Real issuer response captured; research only, NOT independently approved for trading.**

- GitHub Actions run: **42679785882**, artifact **13700999627**, expires **2026-11-23T19:04:28Z**; ZIP SHA256 **b0aaeb32563f96f91dcc7372c96a183fb247a0cf3392c4bc94111fd23b8c0465**.
- Source endpoint: `https://beta.indexes.nasdaqomx.com/Index/HistoryData`, method POST, status 200, content type `application/json; charset=utf-8`, capture time `2026-11-09T19:04:28.102987+00:00`.
- Form fields: `id=OMXH25`, `startDate=2026-11-05T00:00:00.000`, `endDate=2026-11-09T00:00:00.000`, `timeOfDay=EOD`.
- Raw body: **3361 bytes**, SHA256 **13a001c9ae5f92b78bfa0dfca421b5f1cb127d737578f983c9efc4ff94edaf2c**, verified against preserved base64.
- Response object contains `sEcho=1`, `iTotalRecords=3`, `iTotalDisplayRecords=3`, `aaData` array of three records. Historical EOD index value appears in **`Value`**, not `Close` (`Close` is null).
- Records:
  - 2026-11-05 `Value=6254.30092842816`
  - 2026-11-06 `Value=6221.79256147799`
  - 2026-11-09 `Value=6278.94714570764`
- Each record includes `Currency=EUR`, `IndexIsin=FI0008900212`, `Constituents=26`. November 5 and 6 values round to previously documented Nasdaq-origin observations `6254.30` and `6221.79`.
- The capture's stored gates remain `official_eod_raw_bytes_verified=false`, `benchmark_identity_verified=false`, `research_only=true`, `trade_ready=false`. Raw official issuer response is now present; any gate promotion requires a separate strict schema, identity and source-verification review. Do not use synthetic `/session/close` fixture for this actual payload.

**Safety:** The one-time POST step was removed from the regular European research workflow in commit `4ef61eac09c81be33225e3f35f2b53e4af6aaa8e` to prevent repeated issuer requests. The separate manual-dispatch workflow exists on the research branch but is not discoverable from default-branch Actions UI. No main/live scanner changes or trades.
