# Nasdaq OMXH25 date serializer — source verification (2026-11-09)

Issuer-hosted `Site.js?v=1.0.0` was captured as raw bytes by GitHub Actions run **42644742467**, artifact **13686578328** (artifact ZIP SHA256 `9ef4a659337ca6b2a2354fdb922c9bc5a62cbb96cf6b814e74ec1b9110fdfce3`, expiration 2026-11-23). This is a research observation, not an index identity approval.

Direct inspection of preserved `omxh25-site-script-candidate.json` raw base64 decoded JavaScript established `Date.prototype.toISONonUtcString` uses local `getFullYear/getMonth/getDate/getHours/getMinutes/getSeconds/getMilliseconds`, zero-pads, and produces `YYYY-MM-DDTHH:MM:SS.mmm` **without UTC suffix**. Example: `2026-11-05T00:00:00.000`.

Issuer-hosted History.js sends this representation in `POST /Index/HistoryData` using form keys `id,startDate,endDate,timeOfDay`. Site HTML offers EOD/SOD; the capture is restricted to EOD. These facts are now reflected in `research_capture_omxh25_history_post.py`.

**Next step**: verify new CI and attempt a single isolated, bounded raw POST to the exact discovered endpoint, with the derived serialization. Record status, raw response, digest and errors without interpreting an HTML response as historical EOD data. Do not promote `official_eod_raw_bytes_verified`, `benchmark_identity_verified`, or `trade_ready` automatically.

No change to main, live scanner or orders.
