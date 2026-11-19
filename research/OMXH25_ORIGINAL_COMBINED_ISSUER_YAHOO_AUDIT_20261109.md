# OMXH25 issuer/Yahoo combined original artifact audit — 2026-11-09

## Original evidence

- GitHub Actions run `42679785882`, artifact `13700999627`, original ZIP SHA256 `b0aaeb32563f96f91dcc7372c96a183fb247a0cf3392c4bc94111fd23b8c0465` (recomputed locally).
- Original ZIP includes both `europe-benchmarks.json` (129 Yahoo OMXH25 bars) and `omxh25-history-post-raw-unverified.json` (3 Nasdaq issuer EOD records).
- Yahoo `source_raw_base64` recomputed SHA256 matches its stored `source_sha256`.
- Yahoo metadata: `longName=OMX Helsinki 25`, `currency=EUR`, `instrumentType=INDEX`, `exchangeName=STO`, `timezone=CET`.
- Nasdaq response: `id=OMXH25`, `timeOfDay=EOD`, `Currency=EUR`, `IndexIsin=FI0008900212`; issuer raw digest `13a001c9ae5f92b78bfa0dfca421b5f1cb127d737578f983c9efc4ff94edaf2c`.

## Cross-source dated values

| Date | Nasdaq issuer Value | Yahoo close | Yahoo minus issuer |
| --- | ---: | ---: | ---: |
| 2026-11-05 | 6254.30092842816 | 6254.2998046875 | -0.00112374 |
| 2026-11-06 | 6221.79256147799 | 6221.7900390625 | -0.00252242 |
| 2026-11-09 | 6278.94714570764 | 6278.947265625 | +0.00011992 |

All 3 match when rounded to 2 decimals. This is a **direct local cross-check of the original ZIP contents**, separate from the 137 CI unit tests. The newly added `research_compare_omxh25_actual_issuer_yahoo.py` still requires a separately recorded end-to-end execution on the original ZIP before its exact CLI result can be claimed.

## Limits

Three matched dates do not prove the full 129-session mapping, price-versus-total-return methodology, Yahoo's `STO` venue label, or independently audited index identity. Keep `venue_mapping_explained=false`, `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`. No main/live changes or trades.

CI run `42681352637`: **137 tests OK**; all six workflows for commit `a7f683c1561d646dd9e71e7f10acdcc0c95587fe` passed.
