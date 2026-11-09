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
