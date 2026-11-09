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
