# Spoor 2 — onafhankelijke Xetra URL-broncontrole (2026-11-14)

Status: RESEARCH ONLY / NOT ATTESTED / NOT TRADE READY. No production changes, no automatic orders.

## Official Deutsche Börse publication

Primary official publication: https://www.cashmarket.deutsche-boerse.com/resource/blob/4764952/ea2c7396b8986d88e37144a1020a5b4f/data/Cash%20Market%20Readiness%20Newsflash_25_11_07_Anhang.pdf

Cross-check official publication: https://www.cashmarket.deutsche-boerse.com/resource/blob/4764932/ea2c7396b8986d88e37144a1020a5b4f/data/Cash%20Market%20Readiness%20Newsflash_251107_Attach.pdf

Additional official reference: https://www.cashmarket.deutsche-boerse.com/resource/blob/4765620/fbbc32d0a0c499b447e1d57540ff4153/data/20251120_Info%20URL%20new%20Links%20en.pdf

The Deutsche Börse document identifies new Xetra Production URLs effective 2025-11-10:

CSV: https://www.cashmarket.deutsche-boerse.com/resource/blob/1528/b52ea43a2edac92e8283d40645d1c076/data/t7-xetr-allTradableInstruments.csv

ZIP: https://www.cashmarket.deutsche-boerse.com/resource/blob/1542/6ddad5f38f99a491ee1ebe750759e833/data/RDF_StaticData_xetr.zip

## Discrepancy requiring investigation

Current research SOURCES use different blob tokens:

CSV: https://www.cashmarket.deutsche-boerse.com/resource/blob/1528/dc073b6568606b91bfcfe8a7328d6c4f/data/t7-xetr-allTradableInstruments.csv

ZIP: https://www.cashmarket.deutsche-boerse.com/resource/blob/1542/6c68544124aceb09a250f8cc8411c58c/data/RDF_StaticData_xetr.zip

The current URLs return HTTP 302 in GitHub Actions. The original Location values have NOT been disclosed or verified. Their SHA256 fingerprints do NOT establish that they point to the official published URLs. The published URLs may also have changed since 2025.

## Next verification gates

1. Independently inspect current HTTP status and exact Location header for both published URLs with redirects disabled; avoid logging sensitive Location values or credentials.
2. Compare any observed Location to independently reviewed exact URL and current Deutsche Börse publication; do not infer authority from hostname alone.
3. Only after independent review consider an explicit exact-URL allowlist for bounded, no-redirect, read-only retrieval; do not follow redirects automatically.
4. Validate bounded artifact bytes, checksum, format and instrument fields; independently verify ISO MIC, venue, instrument and DEGIRO tariff/route.
5. Keep source_attested=false, trade_ready=false, order_placement_enabled=false until all required independent gates pass.

This note records documentary evidence only. It is NOT a source-attestation or broker-route authorization.

## Web retrieval check (2026-11-14)

The official November 2025 Deutsche Börse PDF was accessible through a web document reader. A request for the published CSV URL returned a tool error indicating unsupported text/csv content type, rather than readable CSV bytes. This does not establish the response status, checksum, completeness, authenticity of downloaded bytes, or any current redirect target. ZIP retrieval was not established by this check. No URL allowlist or research SOURCES entries were changed.

