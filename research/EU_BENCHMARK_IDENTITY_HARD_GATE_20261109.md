# European benchmark provider identity gate — 2026-11-09

Status: **BLOCKED — PROVIDER SYMBOLS NOT INDEPENDENTLY VERIFIED**.

The four requested benchmark variants are:
- AEX price index (Amsterdam)
- DAX **price** index, not DAX performance index (Frankfurt)
- OMX Helsinki 25 price index (Helsinki)
- STOXX Europe 600 EUR price index (SXXP)

The initial capture aliases in `research_capture_europe_benchmarks.py` are unverified hypotheses. In particular, `^GDAXIP` must not be assumed to denote the DAX price index, and `^STOXX` must not be assumed to denote SXXP. A provider symbol match alone is insufficient.

**Required evidence before gate can open:** independent official index variant / ISIN / currency / return type crosswalk, provider chart metadata and daily closes, alignment to market-local dates, and no partial current-session bar. Do not substitute DAX performance or a dividend-inclusive index without explicit disclosure and recalibration.

Offline tests of the relative-strength hard gates succeeded in GitHub Actions run 42599948536. This validates rejection behavior, not index identity or historical relative strength.

European recovery ranking and buy qualification remain **BLOCKED**. No modification to main, live scanner, frozen U.S. thresholds or manual trading workflow.
