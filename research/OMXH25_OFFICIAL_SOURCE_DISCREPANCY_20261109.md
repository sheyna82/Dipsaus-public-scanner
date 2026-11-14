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


## Official Nasdaq PDF byte-level audit — 2026-11-09

- Successfully executed independent research job `nasdaq-document-observation` in existing European workflow run **42615494295** at commit `fea5926da70d0f77ecf1fadd2b4d569823d3c302`; artifact **13673030451**.
- Official URL: https://indexes.nasdaqomx.com/docs/Index_Versions_OMXH25.pdf ; retrieval UTC `2026-11-09T12:15:35.625397+00:00`.
- Retained original PDF is **109623 bytes**; SHA256 `52f35d3e0d4500e01d116c135628c3e145de0b3929e3532c37f3a59d79f550ef`. Recalculation from the artifact's decoded base64 bytes matches; byte-for-byte comparison to the downloaded PDF also matches.
- PDF title `OMXH25 Versions`; metadata creation/modification date **2021-04-16**; © 2021 Nasdaq. Page 1 table: **OMX Helsinki 25 / OMXH25 / PRICE RETURN / EUR / base 500 / 1988-03-07**. Distinct variant **OMX Helsinki 25 GI / OMXH25GI / GROSS TOTAL RETURN / EUR / base 2835.17 / 2013-12-30**. Also OMXH25EXP (price return), OMXH25ER (excess return), OMXH25DVP (dividend point).
- This official version-definition PDF **does not contain** a 2026-11-06 EOD close, a timestamped historical-price bulletin, or an independently verified Yahoo `^OMXH25` alias mapping. It **cannot resolve** the historical 6188.75 versus 6221.79 discrepancy or independently authorize benchmark identity. The 2021 document date is not the 2026 retrieval date.
- **Gate stays closed:** `independently_audited=False`, `research_only=True`, `trade_ready=False`. Require independently retained official dated EOD source and provider mapping/field semantics before any promotion. No live scanner or main changes.


## Nasdaq official EOD display reconciliation — 2026-11-09

- Fresh public search retrieval of official Nasdaq index overview https://indexes.nasdaq.com/Index/Overview/OMXH25 shows **DATA AS OF 11/6/2026: 6,221.79**, net change **-32.51 (-0.52%)**. Official Nasdaq beta history page https://beta.indexes.nasdaqomx.com/Index/History/OMXH25 independently displays the same 11/06 value. This agrees with Nasdaq-sourced FRED series NASDAQOMXH25, and FT's historical 2026-11-06 **Close 6,221.79**.
- A previously retrieved Nasdaq domain https://indexes.nasdaqomx.com/index/overview/omxh25 still has a stale-looking **6,188.75** as its 11/6/2026 last observation, while its previous close **6,254.30** matches Nov 5. We have not established its observation timestamp or exact reason for discrepancy; label **snapshot timing hypothesis only**.
- **Research assessment updated:** 6,221.79 is strongly corroborated as Nov 6 EOD close including a first-party Nasdaq page. This resolves the preferred EOD *value* for research comparisons, **not** the old-page display discrepancy's cause and **not** independent proof of Yahoo `^OMXH25` provider alias/field semantics.
- Public web observations above do not include retained first-party HTML response bytes and hashes; separate official Nasdaq PDF artifact 13673030451 only verifies the 2021 version definitions. Do not issue independently audited receipt on this basis alone. `research_only=True`, `independently_audited=False`, `trade_ready=False`.
- CI on preceding commit `9ce4a8d23ad363685eaa8a7768e2c99ba86bb742`: five workflow runs completed successfully, including EU offline gates, evidence integrity, European capture, AMD and SPY.


## 21-session independent historical close cross-check — 2026-11-09

- Reused captured Yahoo artifact **13669351476** from workflow run **42608870011**, captured **2026-11-09T11:25:06.541808+00:00**; its `OMXH25` series has 129 bars, provider alias `^OMXH25`, provider metadata currency EUR, longName OMX Helsinki 25, instrumentType INDEX, exchangeName STO, timezone CET, gmtoffset 3600. Original provider response SHA256 in artifact metadata `e6d1d3d12c4c4ad76ff62bddc46952d0979fc6c91bb2179a0dd13470a5b5616d`; **the raw response bytes were not retained in this older artifact**, so that source hash cannot be independently rehashed from this artifact.
- Independently inspected publicly displayed historical **daily close** table https://www.investing.com/indices/omx-helsinki-25-historical-data and https://www.finanzen.net/index/omxh25 for **2026-10-09 through 2026-11-06** (21 trading dates). Compared the actual stored Yahoo bar `close` values to the 21 Investing.com published daily closing values, date by date.
- Result **21/21 matches after rounding Yahoo close to two decimal places; zero mismatches**. Largest unrounded absolute deviation **0.00023437500021827873 index points**, consistent with floating-point representation. Examples: Oct 9 **6378.67**, Oct 19 **6330.06**, Oct 30 **6191.03**, Nov 2 **6213.55**, Nov 5 **6254.30**, Nov 6 **6221.79**. This is a multi-day value check, not only a one-day spot check.
- The Yahoo daily bar timestamps are at **07:00 UTC before the 2026-10-25 European DST transition and 08:00 UTC after**, consistent with a **09:00 CET/CEST** session-date anchor in Helsinki (Helsinki local clock is 10:00); **not evidence that the close occurred at the bar timestamp**. Note Yahoo reports `exchangeName=STO` and `timezone=CET` even though the official index is Nasdaq Helsinki; this provider metadata ambiguity remains unresolved.
- Sources are external published historical tables, not an independently captured official Nasdaq 21-day raw EOD feed; web table bytes have not been preserved as immutable artifacts. Despite perfect 21-day numerical agreement, **formal identity promotion remains blocked** pending provider mapping/field semantics and independent official EOD raw-source capture. `research_only=True`, `independently_audited=False`, `trade_ready=False`.


## Yahoo STO/CET metadata ambiguity — contract audit, 2026-11-09

- Inspected source `research_capture_europe_benchmarks.py` and `research_europe_relative_strength.py` directly on research branch. Yahoo chart `meta.exchangeName`, `meta.timezone` and `meta.gmtoffset` are **recorded verbatim** in `provider_metadata`; they are not mapped to Nasdaq Helsinki or used as independent index identity proof. The relative-strength gate recomputes the provider metadata from the retained raw JSON and rejects any mismatch; it additionally requires `^OMXH25`, EUR, INDEX and a `longName` containing Helsinki 25.
- Yahoo metadata previously observed: `exchangeName=STO`, `timezone=CET`, `gmtoffset=3600`. Neither the string STO nor CET is an official issuer-signed index-identity attestation. In particular, CET is not Helsinki's `Europe/Helsinki` zone. Do not silently rewrite these fields to HEL/EET.
- The daily bar session labels are independently converted with Python `ZoneInfo('Europe/Helsinki')` and checked for **10:00 Helsinki**; this supports session-date alignment but does **not** establish the timestamp as an EOD close time. Provider timestamp metadata and exchange-code semantics remain ambiguous. A documented provider-specific mapping or equivalent official cross-reference is required for formal identity review.
- Numerical 21/21 historical close matches remain valid as a separate observation; neither that comparison nor the Yahoo longName proves the provider's contract semantics. **No gate promotion**: `research_only=True`, `independently_audited=False`, `trade_ready=False`.


## First-party Yahoo/Nasdaq symbol and provider documentation — 2026-11-09

- Yahoo Finance itself publicly labels https://finance.yahoo.com/quote/%5EOMXH25/ **OMX Helsinki 25 (^OMXH25)**, currency **EUR**, but its page header says **Stockholm - Delayed Quote**. This is direct first-party Yahoo evidence for the displayed **symbol-to-index-name mapping**, not a signed provider feed contract or proof that `exchangeName=STO` is Nasdaq Helsinki's actual exchange venue.
- Yahoo's first-party exchange/provider coverage page https://help.yahoo.com/kb/yahoo-finance-plus/partnerships-sln2310.html (and https://uk.help.yahoo.com/kb/exchanges-markets-covered-yahoo-finance-sln2310.html) lists Finland **Nasdaq OMX Helsinki**, ticker suffix **.HE**, and separately states global index historical chart/daily updates supplied by **Commodity Systems, Inc.** Its exchange suffix table pertains to listed instruments and **does not establish that `^OMXH25` is an .HE equity or explain the STO index metadata**.
- Official Nasdaq derivatives information dated 2024-11-04 at https://attachment.news.eu.nasdaq.com/a225e82c14d3dae5bcdf569519db47184 identifies underlying **OMX Helsinki 25**, short name **OMXH25**, ISIN **FI0008900212**, price index, Reuters RIC **.OMXH25**, Bloomberg **HEX25 INDEX**. This strengthens first-party Nasdaq instrument identification but provides **no Yahoo ticker crosswalk**. Nasdaq's official index page https://indexes.nasdaq.com/Index/Overview/OMXH25 reports 2026-11-09 **6,246.13**, previous close **6,221.79** (Nov 6), supporting the previously established dated close.
- **Evidence grading:** Official Nasdaq index identity and Yahoo's public name/symbol display are independently corroborated, alongside 21/21 historical close matches. Yet a first-party technical provider mapping for `exchangeName=STO`, `timezone=CET`, quote-time semantics, and official retained historical EOD feed remains unavailable. These must not be guessed or silently relabeled. Formal audit gate remains **closed** (`research_only=True`, `independently_audited=False`, `trade_ready=False`).


## Official session clock versus Yahoo daily label — 2026-11-09

- Nasdaq's **2025 OMXH25 methodology** https://indexes.nasdaqomx.com/docs/methodology_OMXH25.pdf specifies index calculation/dissemination from **10:00:10 to 18:35:00 Helsinki local time (EET/EEST)**, Monday–Friday except Nasdaq Helsinki holidays. This is an official exchange-side clock reference; note first dissemination at 10:00:10, not necessarily a first-trade/open value at exactly 10:00:00.
- Yahoo daily chart timestamps previously observed at **07:00 UTC before European winter DST change and 08:00 UTC after** translate to **10:00 Helsinki** and simultaneously **09:00 Central European local clock**. Thus Yahoo's displayed `CET` timezone and the daily timestamp *can be consistent with a vendor-local session-date anchor* while the actual index is calculated in Helsinki EET/EEST. This is a **clock-consistency explanation, not proof of Yahoo's metadata semantics**. Yahoo `exchangeName=STO` still lacks a documented technical crosswalk.
- Yahoo's public source https://help.yahoo.com/kb/SLN2310.html states **US equities and global index historical data/daily updates** are supplied by **Commodity Systems, Inc.**, and explicitly says the data are informational and **not intended for trading or investing purposes**. The coverage table's Helsinki `.HE` suffix describes securities, not the `^OMXH25` index alias; do not conflate them.
- Official Nasdaq 2024-11-04 derivatives document https://attachment.news.eu.nasdaq.com/a225e82c14d3dae5bcdf569519db47184 is issued by **NASDAQ DERIVATIVES MARKETS**, secondary name Nasdaq Stockholm AB, despite identifying underlying index OMX Helsinki 25 / OMXH25 / ISIN FI0008900212. This shows that Stockholm-labeled administrative contexts can coexist with Helsinki index identity; **it does not demonstrate Yahoo's STO field meaning**.
- **Decision:** session-clock observation corroborated, vendor metadata interpretation still unverified. Do not hardcode a semantic conversion STO→Helsinki or promote research to trading. `research_only=True`, `independently_audited=False`, `trade_ready=False`.


## Reproducible official-PDF capture receipts — GitHub Actions 2026-11-09

- Isolated research branch commit: `94a4117348b6b6c00ff2fb4b716b99028dc348f9`.
- Workflow run: https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/42630114290 ; `nasdaq-document-observation` job `129203931384`: **success**. Other EU history job also succeeded; all five commit workflows passed.
- Archived artifact ID `13680073011`, name `nasdaq-official-document-unverified-observation`, GitHub artifact ZIP digest `sha256:6849ebe332ce2be42e51cd9c8537b12e755e739bc4fc4a25ec5bccfcb70fc277`, created `2026-11-09T13:58:09Z`, expires `2026-11-23T13:58:07Z`. This digest identifies the **artifact archive**, not either source PDF.
- GitHub job output records **official index-variants PDF SHA256** `52f35d3e0d4500e01d116c135628c3e145de0b3929e3532c37f3a59d79f550ef` and **official methodology PDF SHA256** `41c43c502b6862606aef255a55cef41ccc8ff606b21f8b32975edb48fe6b12a2`. Both captures report `identity approved: False`.
- Source capture JSON files include original PDF bytes as base64 and timestamps; **artifact storage is temporary**. Permanent independent reproducibility requires retention outside the expiring GitHub artifact, preferably content-addressed immutable storage with a verified read-back and separate manifest. This dossier records identifiers and hashes only; **it is not itself a permanent copy of PDF bytes**.
- Do not equate successful retrieval with an independent review of content or provider semantics. `research_only=True`, `independently_audited=False`, `trade_ready=False` remain mandatory.


## Reconstructed official-source archive and CI regression closure — 2026-11-09

**Research-only evidence; no benchmark identity promotion.** GitHub Actions source capture run `42630114290`, artifact `13680073011` (`nasdaq-official-document-unverified-observation`), recorded archive digest `sha256:6849ebe332ce2be42e51cd9c8537b12e755e739bc4fc4a25ec5bccfcb70fc277`; the artifact was available for download on 2026-11-09, with GitHub retention expiry 2026-11-23. The original source-document PDF bytes were decoded from its captured JSON records into a separate, **derived** three-member ZIP, `DIPSAUS_OMXH25_official_sources_verified_20261109.zip` (local output, **not committed to this repository**).

- Derived ZIP SHA256 (recomputed from local file): `f23f77eff5660664f1f6523946b4694b9d908fff0182a5018b82ec8ff01f80fd`. Do **not** confuse this with the GitHub artifact's original ZIP digest.
- `nasdaq-index-versions.pdf`: 109623 bytes, SHA256 `52f35d3e0d4500e01d116c135628c3e145de0b3929e3532c37f3a59d79f550ef`.
- `nasdaq-methodology.pdf`: 193988 bytes, SHA256 `41c43c502b6862606aef255a55cef41ccc8ff606b21f8b32975edb48fe6b12a2`.
- `manifest.json`: 762 bytes, SHA256 `df5f20e244f4c107948b39884f0f69ec34be6924a279c16b5b1c6d5d153ce056`; schema `dipsaus-official-source-archive-v1`, `research_only=true`, `trade_ready=false`. The archive has precisely these three members. The hashes and lengths above were recomputed by reading the derived ZIP entries independently on 2026-11-09.
- Regression fix commit `cace03321d1350d7002b5490b79a6196fe891bd8` changes only `test_research_verify_omxh25_archive.py`: tests now write synthetic ZIP bytes to temporary filesystem paths before calling the path-based verifier. The preceding commit had 3 `TypeError` failures caused by passing `BytesIO` to `Path()`.
- GitHub Actions `EU relative strength offline gate tests` run `42632827821`, job `129213207828`: **84 tests run, OK**, including rejection of synthetic PDFs, `trade_ready` promotion, and unexpected ZIP members. All five workflows on the correction commit succeeded (European capture `42632827198`, integrity gate `42632827512`, EU offline tests `42632827821`, AMD checks `42632827197`, SPY history `42632827267`).

**Evidence distinction:** successful negative/offline tests plus independently rehashed original PDF bytes support source-integrity handling; they do **not** certify the Yahoo `^OMXH25` mapping or exchange/timezone semantics. The derived ZIP was checked for entries and hashes locally; this paragraph does not claim a new CI run directly executing the production verifier on the derived ZIP. **Formal gate remains closed:** `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`. No live orders, main merge, or scanner deployment.


## First successful end-to-end CI verification of original Nasdaq artifact — 2026-11-09

- Dedicated research-only workflow `.github/workflows/research-omxh25-original-artifact.yml` at commit `94d90d63a55cf559838a73a96bd82c6645f60d71`, run **42634125556**, job **129217680433**: **SUCCESS**. The workflow downloaded original capture artifact **13680073011** directly from GitHub's Actions API, checked its archive SHA256, rebuilt the two original PDF members, checked their issuer-document hashes, and executed the repository's production offline ZIP verifier.
- Actual CI stdout: `{"artifact_sha256":"6849ebe332ce2be42e51cd9c8537b12e755e739bc4fc4a25ec5bccfcb70fc277","derived_zip_sha256":"6809a4f1b49c88d2e38ea1ee544ed9b772dbac82d3f177dc72a48d7abdf5a807","verification":{"files":2,"research_only":true,"status":"verified_original_bytes","trade_ready":false}}`.
- Published machine-readable receipt: artifact **13682690727**, name `omxh25-official-bytes-research-receipt`, GitHub archive digest `sha256:6ee015cbf6e1e8bbbe5d734e0afe1f239585d3dcabeca3932939b0c75d094eb6`, expires **2026-11-23 14:23:07 UTC**. Receipt contains verification JSON only, not the PDFs.
- The CI-generated derived ZIP digest `6809a4f1...` is **not** the original capture artifact digest `6849ebe3...` and need not match earlier locally packaged derived archives (ZIP metadata/serialization may differ). The verifier checks the original PDF bytes against fixed expected hashes.
- All **six** workflows for this commit succeeded (five existing workflows plus the new original-artifact verifier). The preceding code commit's European offline gate ran **89 tests, OK**, including five new negative reconstruction tests.

**Scope:** This is a genuinely successful end-to-end GitHub CI source-byte integrity verification, not independent proof of the Yahoo `^OMXH25` provider mapping, venue metadata or all historical close semantics. Source artifact and receipt currently have limited GitHub retention. Continue `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`. No main merge, deployment, or orders.
