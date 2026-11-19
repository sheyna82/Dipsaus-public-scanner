# Spoor 2 — T7 Release 15.0 transition audit (2026-11-19)

Research-only; public official webpages reviewed. No Xetra artifact downloads or redirects, no raw Release 15.0 PDF admission, no orders.

## Official findings

- Deutsche Börse T7 Release 15.0 production start 2026-11-09. Functional Reference Part 1, Version 2 dated 2026-10-02 covers market structure, trading states, order and quote handling, matching, trade management and off-book trading. Source: https://www.cashmarket.deutsche-boerse.com/cash-en/Data-Tech/Initiatives-Releases/release15-0/overview-and-functional-documents
- Deutsche Börse circular 047/2026 (2026-10-23) expressly states Release 15.0 has NO BACKWARD COMPATIBILITY with 14.1 interface layouts for ETI, FIX LF, EDCI, public market/reference data interfaces including RDI/RDF, reports and data files. Source: https://cashmarket.deutsche-boerse.com/cash-en/Stay-Informed/circulars-newsletters/deutsche-boerse-circulars/T7-Release-15.0-Important-information-for-production-start-5650620
- Xetra Midpoint Trading Enhancements production activation 2026-11-16. Uploaded 2026-11-18 CSV/ZIP postdate the transition, but dates alone do not authenticate publisher provenance. Source: https://www.cashmarket.deutsche-boerse.com/cash-en/Data-Tech/Initiatives-Releases/release15-0/overview-and-functional-documents

## Interpretation

Release 14.1 and 13.0 documents provide historical taxonomy, not a verified Release 15.0 field-level contract. Never assume RDF schema and field mapping remained unchanged through the non-backward-compatible transition. Uploaded CSV fields Market=XETR, Reporting Market=XETA and Market Segment=045 do not independently prove the actual segment MIC or DEGIRO execution route. Release 15.0 Part 1 Version 2 PDF is listed by Deutsche Börse but its bytes were not downloaded, hashed, parsed or admitted, so no field-level PDF assertions are made.

## DEGIRO public fees

- Official NL fee landing page https://www.degiro.nl/tarieven reviewed 2026-11-19: Euronext Amsterdam equities EUR 2 commission + EUR 1 handling per transaction; US equities EUR 1 + EUR 1; currency handling 0.25%. Potential connectivity, product, spread costs. Connectivity 0.25% portfolio value capped EUR 2.50 per exchange per calendar year, home-market exceptions.
- Landing page does not establish Xetra-specific commission or user-account execution venue. Do not transfer Amsterdam fees to Xetra. Need current full dated tariff and read-only DEGIRO order preview or contract note to verify Xetra route and account-specific costs. A Xetra listing does not prove broker execution there.

## Next evidence needed

1. Inspect Release 15.0 Functional Reference Part 1 Version 2 and Cash Markets Instrument Reference Data Guide for exact MIC and segment fields, only under approved protected-document retrieval policy.
2. Independently attest publisher origin, hash, current ISIN, instrument status and Release 15.0 schema for the Xetra artifact. User-uploaded content remains origin-unattested.
3. Cross-check ISO 10383 effective records; November modifications take effect 2026-11-23, not 2026-11-18 or 2026-11-19.
4. Verify trade-type-specific segment MIC, DEGIRO route, applicable Xetra tariff, spread, currency conversion and connectivity.

Fail closed: source_attested=false; instrument_segment_verified=false; segment_mic_verified=false; broker_route_verified=false; degiro_fee_verified=false; trade_ready=false; order_placement_enabled=false; notify=false; automatic_orders=false.

No changes to main, production or draft PR #65; no external Xetra artifact downloads/redirects.
