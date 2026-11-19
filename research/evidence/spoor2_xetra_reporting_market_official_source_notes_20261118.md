# Spoor 2 — Xetra reporting-market source notes (18 November 2026)

Research-only documentary leads. **Not** an origin-attested instrument capture, instrument-level segment-MIC proof, broker-route verification, or trading permission.

## Official documentary findings

1. Deutsche Börse, *Cash Market Instrument Reference Data Guide* (T7 Release 10.1): field **Reporting Market** is the ISO 10383 MIC required for supervisory reporting. The guide describes **Market Segment** separately. Source: https://www.cashmarket.deutsche-boerse.com/resource/blob/3044328/e51d9bd541d8692c36d6ff846de3bbdf/data/Cash_Markets_Instrument_Reference_Data_Guide_v.1.0.pdf
2. Deutsche Börse, *Information handbook for audit trail, transaction and other regulatory reporting*: field 36 **Venue** refers to segment MIC for venue-executed transactions; its reference-data examples associate **XETA** with **Xetra Regulated market** and **XETB** with **Xetra Open Market**. Source: https://www.cashmarket.deutsche-boerse.com/resource/blob/185396/b1c4ae910a857a5169cb266a4ab4025a/data/091_17e_Reporting_Handbook.pdf
3. Deutsche Börse, T7 Functional Reference (Release 13.0), section 9.1.8: on-book regulated-market Xetra uses **XETA**, whereas off-book LIS uses **XETU**, and midpoint regulated market uses **XEMA**. Source: https://www.cashmarket.deutsche-boerse.com/resource/blob/4148230/8a90c958128d125ef4bbfa992ec6c10b/data/T7_Release_13.0_-_Functional_Reference_Version_2.pdf
4. ISO 10383 registration authority page: November 2026 MIC publication **2026-11-09**, modifications effective **2026-11-23**. Source: https://www.iso20022.org/market-identifier-codes

## Interpretation and boundaries

The uploaded 2026-11-18 Xetra CSV contains IFX/RHM **Reporting Market=XETA**, **MIC Code=XETR**, **Market Segment=045**. These fields are consistent with the public documentation for regulated-market reporting, but the uploaded bytes are not independently source-attested. **Do not equate Reporting Market with a broker-specific execution report or claim a verified segment MIC for a particular order.**

The documentary references above were consulted as public webpages/search-indexed text; their raw bytes and provenance were not independently captured into the scanner's admission chain. Some references predate current T7 Release 15.0. Current-version mapping remains an explicit follow-up.

Remaining blocks: independent current instrument/source admission, trade-type-specific segment MIC and route, DEGIRO account-specific route and applicable fees.

All flags remain false: source_attested, instrument_segment_verified, segment_mic_verified, broker_route_verified, degiro_fee_verified, trade_ready, order_placement_enabled, notify, automatic_orders.

No network retrieval is performed by this file. No authorization for external Xetra artifact downloads or redirects.
