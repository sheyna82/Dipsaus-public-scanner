# Xetra user-supplied snapshot — offline evidence audit

**Audit date:** 2026-11-19. **Scope:** read-only, research only.

These are user-supplied files inspected in the local working environment.
Their hashes pin the exact uploaded bytes but **do not independently prove**
that the original downloads came from Deutsche Börse.

| File | SHA-256 |
| --- | --- |
| `t7-xetr-allTradableInstruments.csv` | `c3f9f7e63dd9b551338c29bda00aaade3e48ec71e035d0ce19348423402dc1ee` |
| `RDF_StaticData_xetr.zip` | `1f740e68d775bb3ebc3f79f776860b29034d8a1e47443e56a9730679e0545a24` |

## Observed data

- CSV preamble: `Market:;XETR`; `Date Last Update:;18.11.2026`.
- 153 CSV columns and 5,544 instrument records; no malformed record shapes.
- ZIP contains 10 members, including `20261118_marketSegment.csv`.
- Segment file has 148 distinct identifiers. All 5,544 instrument
  records have a segment identifier found in that file.
- Each selected ISIN below has exactly one XETR row in this snapshot:

| ISIN | Xetra mnemonic | Segment | Segment description | Product / instrument |
| --- | --- | --- | --- | --- |
| DE0006231004 | IFX | 045 | Regulierter Markt Prime Standard | Active / Active |
| DE0007030009 | RHM | 045 | Regulierter Markt Prime Standard | Active / Active |
| NL0010273215 | ASME | 003 | Freiverkehr | Active / Active |
| FI0009000681 | NOA3 | 003 | Freiverkehr | Active / Active |

## Evidence boundaries

1. Local file inspection is not the same as running the GitHub module
   against the uploaded bytes inside GitHub Actions. The existing CI tests
   use synthetic fixtures. An actual fixture replay remains pending.
2. The MIC code `XETR` in a Xetra instrument row is not itself proof
   of official ISO 10383 operating/segment MIC registration.
3. The Xetra mnemonic is not a primary-exchange ticker. ASML and Nokia
   have different Xetra mnemonics than their primary venue symbols.
4. An active exchange listing is not evidence of DEGIRO account-level
   execution access, executable bid/ask, current order-book liquidity or fees.
5. No private broker/account records or full raw vendor files are
   published to this public research repository.

**All trading permission flags remain false.** Do not promote any candidate
on the strength of this snapshot alone.

## Follow-up

Replay the pinned files against `research_xetra_snapshot.py` in a trusted
local environment; check the exact parser output and error paths. Independently
attest the official source origin and the ISO MIC register separately, then
seek explicit broker-route evidence.
