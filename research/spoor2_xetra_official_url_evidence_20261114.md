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

## GitHub Actions comparison (2026-11-14)

Verified CI run: https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/43600907650
Commit: ebd6605cd8a7092990ee716849533b06198e13eb
Regression: 615/615; three jobs success.

Both independently published URL variants and pre-existing SOURCES return HTTP 302 with identical per-kind Location-header SHA-256 fingerprints in this run:

- CSV: c01ebe5640aecf188585dcee61e0d1fc2e6bfd6553bec970dcfff05fefe23a2c
- ZIP: 18d7f62112f9187bf4f0a529df20f5cd27a97f77b9b0a0326b659aa0d7147cad

Equality is equality of raw Location-header bytes within the recorded run; it is not destination authority, redirect safety, successful artifact retrieval, source attestation, or broker eligibility. No redirect followed; no bytes retrieved. Continue to fail closed.

## Follow-up live CI run (2026-11-14)

Verified run: https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/43601037685
Commit fa995f7e08a5d9cada6f0f0a038a88856e20a2c4; 616/616 tests, three jobs success.

- Published CSV HEAD: HTTP 302, same-host /resource/blob/ technical classification; still NOT ATTESTED.
- Published ZIP HEAD: HTTP 503, no redirect header fingerprint.
- Existing CSV GET: HTTP 503, no artifact bytes.
- Existing ZIP GET: HTTP 503, no artifact bytes.

The same-run HTTP results differ from the preceding 302/302 run. Do not infer a stable redirect chain or a permanent source migration from a single observation. Do not automatically retry in a way that could stress the official service. No source attestation, trading authorization, or broker route verification.

## Follow-up filename and redirect diagnostics (2026-11-14)

Verified run https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/43601237602 for commit 173cbcdf6cad2575871204624b39047ce0c9acda: 618/618 regression tests, all 3 jobs successful.

Published CSV HEAD returned 302 with SAME_HOST_BLOB_PATH_UNATTESTED and expected_filename_matches=true; fingerprint c01ebe5640aecf188585dcee61e0d1fc2e6bfd6553bec970dcfff05fefe23a2c. Published ZIP HEAD and legacy CSV/ZIP GET returned 503. Filename equality is a technical observation, NOT evidence of artifact bytes, provenance, or broker routing. All fail-closed gates remain blocked.

## Follow-up canonical blob shape (2026-11-14)

CI run https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/43601359339 for commit a9612a3e1b6c039ac89bce02280bed1afc0b2c13: 620/620 tests and all three jobs successful.

Published ZIP HEAD: 302; canonical_blob_shape_matches=true; expected_filename_matches=true; redirect_equals_published_url=false; fingerprint 18d7f62112f9187bf4f0a529df20f5cd27a97f77b9b0a0326b659aa0d7147cad. Published CSV HEAD: 503. Legacy CSV and ZIP GET: 302 with no redirects followed. No bytes, provenance attestation, or trading readiness established.

The alternating 302/503 observations show unstable availability across requests, not an approved target. Maintain default-deny redirect policy and prohibit automatic orders.

## Follow-up blob component comparison (2026-11-14)

CI run https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/43602257899 for commit 7a7e233431e7a9322dc951e8584cd9f1d7db8d5c: 621/621 regression tests, all 3 jobs successful.

Published CSV and ZIP HEAD both returned 302. Each redirect had the same official host, canonical blob shape and expected filename, with numeric blob ID unchanged and 32-character blob token changed compared with the published URL. Fingerprints respectively c01ebe5640aecf188585dcee61e0d1fc2e6bfd6553bec970dcfff05fefe23a2c and 18d7f62112f9187bf4f0a529df20f5cd27a97f77b9b0a0326b659aa0d7147cad. Existing CSV/ZIP GET also returned 302. No redirects followed and no bytes retrieved. Exact targets not independently reviewed or approved. All attestation and trade-readiness flags remain false.

## Independent documentary cross-check (2026-11-14)

Official Deutsche Boerse documentation reviewed:
- https://www.cashmarket.deutsche-boerse.com/resource/blob/4764952/ea2c7396b8986d88e37144a1020a5b4f/data/Cash%20Market%20Readiness%20Newsflash_25_11_07_Anhang.pdf
- https://www.cashmarket.deutsche-boerse.com/resource/blob/4765620/fbbc32d0a0c499b447e1d57540ff4153/data/20251120_Info%20URL%20new%20Links%20en.pdf
- https://www.cashmarket.deutsche-boerse.com/resource/blob/4591780/4a5a7f89c8d8b15538a6dc83e3e7c0c5/data/T7_R.14.0_Cash_Markets_Instrument_Reference_Data_Guide_Version_1.pdf

These official documents independently support the published CSV/ZIP filenames and the 2025 cashmarket hostname migration. They do NOT establish that the different 32-character blob tokens observed in 2026 HTTP 302 Location headers are independently published or authoritative. No exact redirect targets approved, no second-hop fetch permitted, no bytes attested, no broker-route verification. Keep source_attested=false, trade_ready=false, order_placement_enabled=false. Further code changes are not justified by this documentation alone.

## Additional official live instrument inventory evidence (2026-11-14)

Official Deutsche Boerse Cash Market Xetra instrument inventory:
https://www.eurexgroup.com/dbcm-en/instruments-statistics/all-tradable-instruments/xetra
The independently retrieved page reports T7 (XETR) All tradable instruments updated 14 November 2026 01:56 AM and static instrument reference data updated 13 November 2026 11:37 PM, and displays ISIN and XETR market classifications. The inventory is an independent official corroboration channel for *selected* instrument/market assertions, subject to timestamp, instrument-identity and publication consistency checks. The page does NOT disclose or attest the observed HTTP 302 redirect Location blob tokens; it does not prove downloaded CSV/ZIP bytes, a complete inventory snapshot, DEGIRO routing, or trade readiness.

Official migration documentation still publishes the 2025 CSV and ZIP URLs:
https://www.cashmarket.deutsche-boerse.com/resource/blob/4764952/ea2c7396b8986d88e37144a1020a5b4f/data/Cash%20Market%20Readiness%20Newsflash_25_11_07_Anhang.pdf

Keep all fail-closed gates unchanged. Do not automatically follow redirects or promote inventory-page matches to source_attested=true.

## Reproducible official inventory spot-check (2026-11-14)

Source A (English, current page): https://www.eurexgroup.com/dbcm-en/instruments-statistics/all-tradable-instruments/xetra
Source B (official cash market instrument table): https://www.cashmarket.deutsche-boerse.com/cash-en/trading/Tradable-Instruments-Xetra
Source C (German page; indexed snapshot may be stale): https://www.eurexgroup.com/dbcm-de/instrumente-statistiken/alle-handelbaren-instrumente

Observed in A: 5,574 displayed results; CSV update 2026-11-14 01:56; static RDF update 2026-11-13 23:37.
Observed in B: 5,574 displayed results, including:
- DE000A2LQ2D0 — 029 GROUP SE INH O.N. — XETR (source A) — shares, EUR (source B).
- DE0005545503 — 1+1 AG INH O.N. — XETR (source A) — shares, EUR (source B).
- US88025U1097 — 10X GENOMICS DL -,00001 — XETR (source A) — shares, EUR (source B).
Source C indexed an older 5,568-result snapshot dated 2026-11-12. Do NOT treat a differing indexed snapshot as a data conflict without comparing the same publication timestamps and filters.

These three manually observed records are a spot-check of official public web listings, NOT a complete, reproducibly downloaded CSV/ZIP inventory. This cannot independently prove ISIN/MIC mappings for the scanner universe, DEGIRO trading route or tariff, the 302 blob tokens, or source byte integrity. The instrument page and downloaded CSV may share an upstream publication process and are not necessarily independent evidence of data accuracy. Keep all trade gates blocked until a timestamp-matched full evidence join is independently reproduced and reviewed.

## Source-to-scanner reconciliation acceptance criteria (2026-11-14)

Official source documentation:
- https://www.cashmarket.deutsche-boerse.com/resource/blob/4764952/ea2c7396b8986d88e37144a1020a5b4f/data/Cash%20Market%20Readiness%20Newsflash_25_11_07_Anhang.pdf (official November 2025 migration URLs).
- https://www.cashmarket.deutsche-boerse.com/resource/blob/4591780/4a5a7f89c8d8b15538a6dc83e3e7c0c5/data/T7_R.14.0_Cash_Markets_Instrument_Reference_Data_Guide_Version_1.pdf (instrument-reference semantics and publication).
- https://www.cashmarket.deutsche-boerse.com/resource/blob/2609724/9849de7dec92b70a65093dd3817feda6/data/Cash_Markets_Instrument_Reference_Data_Guide_v.1.0.pdf (historical CSV file format: semicolon-delimited; line 1 Market: XETR; line 2 Date Last Update; line 3 headers; records from line 4).
- https://www.cashmarket.deutsche-boerse.com/dynamic/action/cash-en/trading/Tradable-Instruments-Xetra/xetra/4085954/search (official listing; web search snapshots can be stale).

Before any full ISIN/MIC join is accepted:
1. Independently review the exact 302 Location target against official publication; no hash, same-host, basename or blob-shape match alone qualifies. No redirect follow until separately approved.
2. Retrieve only approved, exact, HTTPS URLs with redirect disabled, byte-size/time bounds, deterministic SHA-256 and retained publication timestamp; reject HTTP 503/302 and partial/HTML responses.
3. Parse CSV according to the release-specific official guide; verify XETR market header, update date, schema/column count, instrument status, ISIN syntax and uniqueness rules. Do not assume the historical guide matches the current schema without review.
4. Compare a timestamp-matched complete instrument snapshot to the scanner's explicit ISIN+MIC+currency+segment universe; distinguish absent, ambiguous, inactive and duplicated entries. Public website spot-checks are not a complete snapshot and may share an upstream source.
5. Independently verify DEGIRO product identifier, actual executable exchange/route and applicable fee schedule for each instrument; XETR listing alone cannot establish DEGIRO routing or tariff.
6. Preserve provenance, source version, tests, audit evidence and explicit human sign-off. Until all gates pass, source_attested=false, broker_route_verified=false, trade_ready=false, order_placement_enabled=false.

This is a documented acceptance plan, not a claim that the complete join, file download, or broker verification has been executed.

## Explicit configuration audit and release-blocking decision (2026-11-14)

Cross-checked current research/spoor2_xetra_artifact_retrieval_20261113.py SOURCES against research/spoor2_xetra_published_url_probe_20261114.py PUBLISHED and the official 2025 Deutsche Boerse migration PDF:
https://www.cashmarket.deutsche-boerse.com/resource/blob/4764952/ea2c7396b8986d88e37144a1020a5b4f/data/Cash%20Market%20Readiness%20Newsflash_25_11_07_Anhang.pdf

CSV: research SOURCES token dc073b6568606b91bfcfe8a7328d6c4f versus officially published token b52ea43a2edac92e8283d40645d1c076.
ZIP: research SOURCES token 6c68544124aceb09a250f8cc8411c58c versus officially published token 6ddad5f38f99a491ee1ebe750759e833.

These are distinct exact URLs, even though host, blob ID and filename agree. The observed redirect target token differs from the published one, and exact destination authority remains unverified. Therefore: do not auto-promote legacy SOURCES, published PUBLISHED, or redirect destinations to approved bytes; do not replace SOURCES automatically or follow redirects; no live configuration or broker changes. Require independent publication of exact current targets, reviewed evidence chain and bounded retrieval before approving a source update.

This audit is documentary, not a new CI validation. Last verified regression run remains 621/621 in 43602257899.

## Third-variant redirect evidence (2026-11-14)

Verified GitHub Actions run https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/43615307758 for commit 87c7238a649fa97e3c9e8b9b871a6e11ccae27fb: 622/622 regressions and all three jobs success.

Published CSV and ZIP HEAD both returned HTTP 302. For each: same official hostname, canonical blob path, expected filename, same numeric blob ID as published, changed blob token; redirect_equals_published_url=false AND redirect_equals_legacy_url=false. Their observed Location values are therefore a third exact URL variant, not either of the two documented candidates. Fingerprints remain c01ebe5640aecf188585dcee61e0d1fc2e6bfd6553bec970dcfff05fefe23a2c (CSV) and 18d7f62112f9187bf4f0a529df20f5cd27a97f77b9b0a0326b659aa0d7147cad (ZIP).

Legacy CSV/ZIP GET both returned 302; no redirects followed and no bytes retrieved. A structurally plausible third variant is NOT independent publication authority or content integrity. Keep exact-target approval and all trading gates blocked.

## Verified third-variant redirect finding (2026-11-14, CI)

CI run: https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/43615307758
Code commit: 87c7238a649fa97e3c9e8b9b871a6e11ccae27fb
Jobs: spoor2-xetra-source-capture, integrity-unit-tests and spoor2-regression-auditable all success; 622/622 regression tests passed.

Both official published URL HEAD probes returned HTTP 302, redirect_equals_published_url=false and redirect_equals_legacy_url=false. For both, blob_id_matches_published=true, blob_token_matches_published=false, expected_filename_matches=true, canonical_blob_shape_matches=true. CSV Location SHA-256: c01ebe5640aecf188585dcee61e0d1fc2e6bfd6553bec970dcfff05fefe23a2c. ZIP Location SHA-256: 18d7f62112f9187bf4f0a529df20f5cd27a97f77b9b0a0326b659aa0d7147cad.

This establishes that the observed exact redirect targets are a third variant relative to both known source URL sets, not that the targets are authoritative, safe to retrieve, or stable. The legacy GET probes also returned HTTP 302, with no bytes. All redirect requests remained un-followed; all attestation and trading flags false.


## Live official download-link observation (2026-11-14; publication URL only)

Independently opened Deutsche Boerse's official Xetra instruments page:
https://www.cashmarket.deutsche-boerse.com/cash-en/trading/Tradable-Instruments-Xetra

The page's own "T7 (Xetra) All tradable instruments" download link (link 139 in the observed page response) resolved to this exact CSV URL:
https://www.cashmarket.deutsche-boerse.com/resource/blob/1528/a4b7965b87cf1ef4621a28b85f145ae9/data/t7-xetr-allTradableInstruments.csv

The retrieval interface returned an unsupported text/csv content-type error. This is a URL-link observation ONLY: no successful byte download, no checksum of file contents, no independently verified CSV schema or publication timestamp, and no comparison against the actual full raw HTTP Location strings. The link token differs from the 2025 migration-document token (b52ea43a2edac92e8283d40645d1c076), the configured legacy token (dc073b6568606b91bfcfe8a7328d6c4f), and the previously observed page-link token (2ecdd46ed6dca90fbfc8575d5a21fb4b). These variations demonstrate that page-published resource URLs may change; they do not establish the exact authority or integrity of any redirect target.

Do NOT automatically add this URL to any allowlist, follow redirects, change SOURCES/PUBLISHED, mark source_attested, or enable trading. A controlled, reviewed exact-target comparison and bounded no-follow byte retrieval remain separate prerequisites.

## Exact SHA-256 reconciliation: official page CSV link versus observed HTTP Location (2026-11-14)

Independent source: https://www.cashmarket.deutsche-boerse.com/cash-en/trading/Tradable-Instruments-Xetra (the official page's link labelled "T7 (Xetra) All tradable instruments"). The observed literal link destination is:
https://www.cashmarket.deutsche-boerse.com/resource/blob/1528/a4b7965b87cf1ef4621a28b85f145ae9/data/t7-xetr-allTradableInstruments.csv

Computed SHA-256 of the UTF-8 bytes of the COMPLETE literal URL string, without newline:
c01ebe5640aecf188585dcee61e0d1fc2e6bfd6553bec970dcfff05fefe23a2c

This EXACTLY matches the SHA-256 of the full HTTP 302 Location string recorded independently by the no-follow published-URL HEAD probe in GitHub Actions run 43623830133. The matching fingerprint establishes a reproducible exact-string linkage between that recorded Location and the official page's observed CSV download URL (subject to the usual cryptographic SHA-256 collision assumption). This supersedes the earlier statement that the CSV Location could not be matched to an official publication link. The link still differs from the 2025 migration PDF and the legacy configured source URL.

CRITICAL SCOPE: The observation does NOT verify CSV response bytes, byte SHA-256, content-type acceptance, schema, publication timestamp, completeness, or instrument identity; opening the CSV link through the independent page reader returned unsupported text/csv. It does not establish ZIP Location authority, DEGIRO routing or tariff, or trade readiness. The GitHub job continued to report HTTP 302 and zero accepted Xetra CSV/ZIP bytes. No redirect was followed in the research capture. Do not silently approve this URL for fetching: bounded no-follow retrieval and explicit review remain separate steps. Keep source_attested=false, instrument_segment_verified=false, broker_route_verified=false, trade_ready=false, order_placement_enabled=false.

Reproduce the URL fingerprint locally: Python hashlib.sha256(url.encode('utf-8')).hexdigest(), where url is the literal complete CSV URL above and contains no trailing newline.
