# ISO 10383 MIC official source — verification checkpoint (2026-11-19)

**Source:** https://www.iso20022.org/market-identifier-codes

The ISO 10383 Registration Authority page was inspected on 19 November
2026. It identifies a current downloadable CSV at:

https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv

The page explicitly states:
- Publication: **09 November 2026**.
- Modification implementation: **23 November 2026**.
- Next publication: **14 December 2026**.

**Critical evidence distinction:** the official landing page and its CSV
download link were confirmed, but the CSV **bytes were not retrieved** in
this investigation. The web reader rejected the CSV content type and the
local runtime could not reach the host. Consequently:

- No actual official CSV headers, column mappings, code values or individual
  XETR/XAMS/XHEL records have been inspected or authenticated.
- No official CSV hash has been calculated or pinned.
- `research_iso_mic_parser.py` remains a synthetic-schema parser, not a
  verified importer of the real published ISO register.
- The November file is **not yet effective** as of 2026-11-19.
  Do not infer that a November change was already in force; for a current
  register decision obtain the previously effective publication or
  independently established unchanged-record history.
- ISO MIC records describe market identifiers and operating/segment
  relationships; they are **not** an ISIN-to-listing register.
- The Xetra upload verifies offline instrument-to-venue/segment *claims*
  but does not substitute for the official ISO registry.
- No verified DEGIRO instrument route or execution quote is available.

**All trading and order placement flags remain false.**

## Next required inputs

1. Retrieve the official CSV bytes through an approved download workflow,
   retaining URL, redirect/TLS provenance, timestamp and SHA-256.
2. Inspect actual header names and value encodings before implementing any
   production-like schema mapping.
3. Verify the correct **effective** publication for the decision date.
4. Check operating and segment MIC relationships for XETR/XAMS/XHEL,
   without inventing ISIN fields in the MIC register.
5. Corroborate Xetra listing claims separately and independently verify
   broker route, costs, quote freshness and orderbook depth.

This document records a **source-discovery checkpoint**, not a successful
official ISO register import.
