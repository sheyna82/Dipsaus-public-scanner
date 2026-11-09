# OMXH25 source discrepancy investigation — 2026-11-09

**Research-only. Identity remains NOT independently approved.**

## Verified external observations for Friday 2026-11-06

- Nasdaq official overview https://indexes.nasdaqomx.com/index/overview/omxh25 displays **6,188.75**, change -65.55 / -1.05%, previous close 6,254.30, high 6,225.77, low 6,159.33. Note **the displayed 6,188.75 is within the session range** but is not corroborated as the final historical close.
- FRED series NASDAQOMXH25 (source Nasdaq), https://fred.stlouisfed.org/series/NASDAQOMXH25: **6,221.79**, with Nov 5 **6,254.30**.
- Financial Times historical OMX25:HEX https://markets.ft.markitdigital.com/data/indices/tearsheet/historical?s=OMX25%3AHEX: Nov 6 **6,221.79**, Nov 5 **6,254.30**.
- Het Financieele Dagblad historical https://beurs.fd.nl/noteringen/150176135/omx-helsinki-25/historie: Nov 6 **6,221.79256**.
- Nasdaq official index versions https://indexes.nasdaqomx.com/docs/Index_Versions_OMXH25.pdf: OMXH25 is **PRICE RETURN**, **EUR**; OMXH25GI is separate **GROSS TOTAL RETURN**.
- Nasdaq methodology https://indexes.nasdaqomx.com/docs/methodology_omxh25.pdf: official methodology and index dissemination.

## Assessment

Four sources, including Nasdaq-derived FRED, support the 6,221.79 **historical closing observation**; Nasdaq overview shows conflicting 6,188.75. The difference is **33.04 index points (~0.531% relative to 6,221.79)**. The official overview's high/low and previous close are consistent with the FRED historical close, but this is **not a proven explanation** for the conflicting display. Possible stale or intraday snapshot is only a hypothesis; do not label it a fact.

**Decision: unresolved official source conflict.** Do not issue an identity-verified receipt; keep Nokia / OMXH25 gated until Nasdaq source timestamp and close-definition are independently reconciled and the actual provider `^OMXH25` mapping is checked. No live trade authorization.

Next evidence: Nasdaq historical end-of-day close or dated exchange bulletin, source timestamp/refresh behavior, and provider symbol mapping with captured SHA256 documents. The contract alone is not independent proof.


## Follow-up audit — 2026-11-09 (independent retrieval limitations)

- GitHub Actions for source-document commit `bc0d8c1465c0e568fa03f2e5f2462849d9d9620e`: all five returned PR workflow runs completed successfully (42607754256, 42607753891, 42607754034, 42607753812, 42607753950). The EU offline-gates job ran eight named unittest modules, including benchmark identity receipt tests. This establishes CI execution, **not** independent truth of index values.
- Fresh public-page retrieval returned a **dated 2026-11-04 snapshot** from the official Nasdaq OMXH25 overview (6,289.73), and a **dated 2026-11-05 latest observation** from the FRED page (6,254.30). These retrieved views do not provide a newly independently verified 2026-11-06 close. They must not be used to adjudicate the 6,188.75 versus 6,221.79 conflict.
- Nasdaq's retrieved index description explicitly identifies OMXH25 as a capitalization-weighted stock **price** index with currency EUR. This supports official index identity, but does **not** independently establish the Yahoo `^OMXH25` mapping or historical EOD field semantics.
- Source pages: https://indexes.nasdaqomx.com/index/overview/omxh25 ; https://fred.stlouisfed.org/series/NASDAQOMXH25 . Retrieval date 2026-11-09; the page-visible as-of dates above are distinct from retrieval date. No raw page bytes or source SHA256 captured in this audit, therefore this appendix is **not** a valid benchmark identity evidence receipt.

**Gate remains closed:** `identity_evidence_complete` must not be interpreted as independent audit; `independently_audited=False`, `research_only=True`, `trade_ready=False`. Next evidence required: date-specific Nasdaq end-of-day source plus independently captured Yahoo provider observation, with raw-byte hashes and timestamp/field definitions. No trading use.


## Nasdaq next-session previous-close cross-check — 2026-11-09

Independent public source retrieval (2026-11-09): the official Nasdaq OMXH25 overview now states **DATA AS OF 11/9/2026**, index value **6,279.78**, and **Previous Close 6,221.79**. This is direct issuer-side corroboration of the 2026-11-06 closing observation, assuming the immediately preceding exchange session was Friday 2026-11-06. Source: https://indexes.nasdaqomx.com/index/overview/omxh25 . FRED's Nasdaq-origin daily series explicitly reports **2026-11-06: 6,221.79**, updated **Nov 6 2026 10:44 PM CST**: https://fred.stlouisfed.org/series/NASDAQOMXH25 . FT's historical table and FD's historical table independently show the same Friday close: https://markets.ft.markitdigital.com/data/indices/tearsheet/historical?s=OMX25%3AHEX ; https://beurs.fd.nl/noteringen/150176135/omx-helsinki-25/historie .

**Revised assessment:** historical Friday close **6,221.79 is strongly corroborated, including by the issuer's next-session Previous Close field**. The earlier **6,188.75** overview value was **not** the final Friday close; the hypothesis that it was a prior intraday/stale snapshot remains unproven without its timestamp. Do not erase that discrepancy. The separate Yahoo provider symbol `^OMXH25` mapping, field semantics, and raw-byte evidence SHA256 remain **unverified**. Consequently **no independent benchmark identity approval receipt**, no trade-ready status, no live deployment. Research-only gate remains closed.


## Yahoo provider crosswalk — independent public metadata check, 2026-11-09

- Yahoo Finance public quote https://finance.yahoo.com/quote/%5EOMXH25/ explicitly labels `^OMXH25` **OMX Helsinki 25**, **EUR**, and **Stockholm - Delayed Quote**. The publicly retrievable result is **stale (at close 2026-10-16, 6,385.89)**, so it **cannot** confirm the 2026-11-06 close or actual Yahoo OHLC fields. Its venue label 'Stockholm' also needs explanation against Nasdaq Helsinki's official index identity.
- Official Nasdaq index versions https://indexes.nasdaqomx.com/docs/Index_Versions_OMXH25.pdf explicitly lists `OMXH25` as **PRICE RETURN, EUR** and `OMXH25GI` as **GROSS TOTAL RETURN, EUR**. Official methodology https://indexes.nasdaqomx.com/docs/methodology_OMXH25.pdf states dissemination **once per second from 10:00:10 to 18:35:00 Helsinki local time** on trading days; thus an overview intraday value can differ from the eventual official close, although the specific 6,188.75 snapshot timestamp is not established.
- Official Nasdaq history page https://beta.indexes.nasdaqomx.com/Index/History/OMXH25 publicly displays **DATA AS OF 11/06/2026 6,221.79**, corroborating the Friday close. FRED https://fred.stlouisfed.org/series/NASDAQOMXH25 likewise gives **2026-11-06 6,221.79**. A separate Nasdaq overview retrieval may show **6,188.75**; record field, timestamp and endpoint for each observation rather than treating dynamic pages as immutable.

**Crosswalk verdict: PARTIAL / NOT APPROVED.** Yahoo's name, symbol and EUR metadata agree at a superficial level with the official price index, but Yahoo's stale quote, 'Stockholm' label, missing independently captured November 6 Yahoo daily OHLC, and absent raw-byte hashes prevent a verified provider-to-index mapping. Do not issue an independent identity receipt; `research_only=True`, `trade_ready=False`, `orders_placed=False`. Next: capture date-specific Yahoo raw historical bars (including timezone, currency and provider exchange metadata) and compare to Nasdaq official dated history, preserving hashes and acquisition timestamps.


## Artifact provenance correction — 2026-11-09

The GitHub Actions artifact **13668877675**, run **42608640148** (`European recovery research capture`), was downloaded and its ZIP contents inspected. It contains **`europe-history.json`**, an **equity** history dataset with `ASML.AS` (131 bars), `IFX.DE` (131), `NOKIA.HE` (129), and `RHM.DE` (131). **It does not contain OMXH25 or other benchmark series.** Artifact archive digest reported by GitHub: `sha256:931ef283fe770653d43365d72b80ac3fb1630a5e9de707f1f1bd03b345fae7e0` (archive digest, not a Nasdaq/Yahoo raw-response digest).

The separate `.github/workflows/research-europe-benchmarks-isolated.yml` is **workflow_dispatch only**, runs `research_capture_europe_benchmarks.py`, and uploads `dipsaus-europe-benchmarks-research` containing `europe-benchmarks.json`. Do **not** infer benchmark capture from the five successful PR workflows; no matching benchmark artifact was inspected in this step.

**Evidence gate unchanged:** historical Nasdaq Friday close 6,221.79 is issuer-corroborated, but Yahoo `^OMXH25` Friday bar has **not** been verified. No independent benchmark identity receipt, no trade authorization, no changes to main or live scanner. Next obtain an actual benchmark-capture run artifact, verify run commit, ZIP digest, embedded `source_sha256`, provider metadata and UTC timestamp-to-Helsinki trading-day mapping before comparing Yahoo close to official Nasdaq history.


## Actual Yahoo benchmark artifact verification — 2026-11-09

**Directly inspected artifact:** GitHub Actions run **42608870011** (`EU relative strength offline gate tests`), artifact **13669351476** (`eu-benchmark-unverified-observations`), head commit **cc123a6a4e2437c5c95c5339a9247a2a52cb6442**. Downloaded ZIP and parsed `europe-benchmarks.json`. Independently recomputed ZIP SHA256 **e1aa70e78c2b42eb3e4ef62adf9855d9fbce02331f18f91a0d8742f829a29b43**, exactly matching GitHub's artifact digest. Embedded capture timestamp **2026-11-09T11:25:06.541808+00:00**. Dataset has four series: AEX 131, DAX_PRICE 131, OMXH25 129, STOXX600_PRICE 129 bars.

**Actual Yahoo provider observation** for `OMXH25`: `provider_symbol=^OMXH25`, `currency=EUR`, `instrumentType=INDEX`, `longName=OMX Helsinki 25`, `exchangeName=STO`, `timezone=CET`, `gmtoffset=3600`; source response SHA256 **e6d1d3d12c4c4ad76ff62bddc46952d0979fc6c91bb2179a0dd13470a5b5616d** (hash stored by collector; original response bytes not retained in artifact, so cannot independently recompute this embedded raw-response hash). Yahoo daily bars: **2026-11-04 08:00 UTC = 6289.72998046875**, **2026-11-05 08:00 UTC = 6254.2998046875**, **2026-11-06 08:00 UTC = 6221.7900390625**, **2026-11-09 08:00 UTC = 6272.388671875**. The 2026-11-06 daily close rounds to **6221.79**, matching the official Nasdaq issuer history **6221.79** to two decimal places. Yahoo's daily timestamp is **08:00 UTC / 09:00 CET**, which is a **daily bar label, not the EOD execution timestamp**; do not infer a close at 09:00 CET.

**Assessment upgraded from missing Yahoo data to verified historical value match**, not to independent benchmark identity approval. The Yahoo `STO` venue label versus official Helsinki index, timestamp semantics, and issuer/provider identity mapping still need explanation; no independently preserved Yahoo response bytes and no official raw-source hashes. Existing flags remain `benchmark_identity_verified=false`, `research_only=true`, `trade_ready=false`. This historical matching observation is not evidence of profitable strategy performance or trading authorization.


## Timezone and venue-label interpretation — 2026-11-09

Official Nasdaq methodology https://indexes.nasdaqomx.com/docs/methodology_OMXH25.pdf says OMXH25 is calculated on Nasdaq Helsinki trading days and disseminated from **10:00:10 to 18:35:00 Helsinki local time (EET/EEST)**. On Friday 2026-11-06, Finland used EET (UTC+2), so **10:00 EET = 08:00 UTC**. The Yahoo daily bar timestamp for that date, **08:00 UTC**, therefore aligns with the **session start** to the minute; it is **not an end-of-day execution timestamp**. The captured Yahoo `timezone=CET`, `gmtoffset=3600`, and `exchangeName=STO` refer to provider display/venue metadata, and do not independently prove the index calculation venue or a provider-specific mapping guarantee. Yahoo's own public quote labels `^OMXH25` 'Stockholm - Delayed Quote' while its help page lists Nasdaq OMX Helsinki as a distinct Finnish exchange. The reason for Yahoo's STO code remains unconfirmed; do not silently normalize it to HEL.

The 2026-11-06 Yahoo `close=6221.7900390625` is a **daily-bar closing value**, even though its **bar label** is 08:00 UTC. A two-decimal match with Nasdaq's official 6221.79 close is strong historical cross-validation, not proof that all future bars or index variants map identically. Continue requiring independent provider mapping and field semantics before changing `benchmark_identity_verified=false`. No orders, no main/live changes.


## Captured official Nasdaq index-version PDF — 2026-11-09

Official issuer URL: https://indexes.nasdaqomx.com/docs/Index_Versions_OMXH25.pdf

GitHub Actions run **42615494295**, job **nasdaq-document-observation**, research branch commit **fea5926da70d0f77ecf1fadd2b4d569823d3c302**; artifact **13673030451**, ZIP SHA256 **5d4475449813e7444ef491fe1348f83ec3a3b0146cef404ceb6e1191fca51f7a**, captured at **2026-11-09T12:15:35Z**. Official PDF raw byte length **109623**, SHA256 **52f35d3e0d4500e01d116c135628c3e145de0b3929e3532c37f3a59d79f550ef**. Independently recomputed SHA256 from downloaded PDF matches the capture receipt; PDF header is %PDF-1.7. Original bytes are preserved base64-encoded inside the downloadable research artifact (artifact retention through 2026-11-23).

Page 1 of Nasdaq's *Index Versions — OMXH25* (copyright 2021) identifies:
- **OMX Helsinki 25**, symbol **OMXH25**, **PRICE RETURN**, **EUR**, base value **500**, base date **3/7/1988**.
- **OMX Helsinki 25 GI**, symbol **OMXH25GI**, **GROSS TOTAL RETURN**, **EUR**, base value **2835.17**, base date **12/30/2013**.
- **OMX Helsinki 25 Expiration**, symbol **OMXH25EXP**, **PRICE RETURN**, **EUR**; this is a distinct variant and must not be silently equated to OMXH25.

**What this independently establishes:** issuer-authored index naming, official ticker, price-vs-gross-total-return identity and EUR denomination; provenance of a specific retrievable PDF byte sequence. **What it does not establish:** Yahoo's provider alias `^OMXH25` mapping contract, Yahoo's `STO` venue-label meaning, daily-close field semantics across all dates, current-day official closing prices, or profitability of any trading strategy. The issuer document is ©2021, so treat its index-versions table as a captured historical issuer specification rather than a guarantee of unchanged 2026 index rules.

**Fail-closed decision:** `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`. Independent reviewer approval and provider-mapping evidence remain outstanding; no promotion on the basis of a value match alone. No main, live scanner, or orders changed.
