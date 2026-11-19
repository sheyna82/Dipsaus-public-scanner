# Spoor 2 — Release 15.0 reference-data source selection (2026-11-19)

Research-only addendum to `spoor2_t7_release15_transition_audit_20261119.md`. Official HTML pages inspected, no linked PDF/ZIP/CSV downloaded or redirects followed. No production or trade actions.

## New directly verified official evidence

1. Deutsche Börse circular 047/2026 (23 October 2026) states the T7 15.0 production start is 9 November 2026 and that market/reference data interfaces RDI/RDF, reports and data files do not provide backwards compatibility with T7 14.1.
2. The same circular, section 3.D, says initial reference data for business day 9 November were made available during the 7 November conversion support window.
3. Crucially, section 3.F says the initial reference data for 9 November would be **regenerated after the Sunday-evening system restart**, and explicitly requires participants to use that later initial reference data because the 7 November pre-support-window version might have changed.
4. Deutsche Börse's Release 15.0 official documentation index identifies the more targeted source contracts:
   - *T7 Release 15.0 Market and Reference Data Interfaces Manual, Version 2* (26 August 2026): covers EMDI, MDI, RDI and RDF concepts/messages.
   - *T7 Release 15.0 Market + Reference Data Interfaces XML FAST Templates - FIXML schema files, Version 2* (26 August 2026).
   - *T7 Release 15.0 Cash Markets Instrument Reference Data Guide, Version 1* (17 August 2026): overview of reference-data services via Common Report Engine, RDI, member section and Deutsche Börse Xetra website.
   - *T7 Release 15.0 Functional Reference Part 1, Version 2* (2 October 2026) covers functional concepts, **not** a substitute for the RDF/CSV field-level contract.

Official HTML sources:
- https://cashmarket.deutsche-boerse.com/cash-en/Stay-Informed/circulars-newsletters/deutsche-boerse-circulars/T7-Release-15.0-Important-information-for-production-start-5650620
- https://www.cashmarket.deutsche-boerse.com/cash-en/Data-Tech/Initiatives-Releases/release15-0/overview-and-functional-documents

## Consequences for DIPSAUS verification

- Require business-date, file-generation/version and publisher-origin evidence, not only a local upload timestamp. In particular, do not accept the 7 November pre-restart reference-data snapshot as equivalent to the regenerated production snapshot for 9 November.
- For later-day files (including user-provided 18 November files), verify their **own** provenance and schema; the 9 November regeneration instruction is a historical transition requirement, not proof that any later upload is authentic or invalid.
- Distinguish (a) market/operating MIC, (b) reporting-market field, (c) segment code, (d) externally attested segment MIC, (e) DEGIRO order execution venue. None is automatically interchangeable.
- Do not infer exact RDF field mappings from the official HTML index. The named manuals/schema packages have not been downloaded, hashed, parsed or admitted under the protected-document policy.
- Future approved validation should record document version, publisher URL, download approval, redirect decision, content hash, relevant exact field definition, extraction provenance and cross-source match per ISIN.

## Open blockers and safe state

No independent current publisher-origin attestation of the uploaded CSV/ZIP; no admitted Release 15.0 field-level reference contract; no independently verified segment MIC, DEGIRO execution route or account-specific Xetra fee.

`source_attested=false`; `instrument_segment_verified=false`; `segment_mic_verified=false`; `broker_route_verified=false`; `degiro_fee_verified=false`; `trade_ready=false`; `order_placement_enabled=false`.

No Xetra artifact downloads/redirects, no orders, no main/production changes, no changes to draft PR #65.
