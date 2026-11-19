# Yahoo European benchmark raw-response integrity — CI evidence (2026-11-09)

**Research only. No benchmark identity approval or trading authorization.**

## Verified implementation and results

- Raw-response verifier: `research_verify_europe_benchmark_raw.py`, first committed `376ad0ab286fa4f184efd36ef11aa85ced70142d`.
- Verifier reconstructs all four provider series from the preserved Base64 Yahoo response, recomputes SHA256, validates symbols, currency, instrument type, captured metadata, bar order and values, and OMXH25 Helsinki-session label audit. A mismatch fails closed.
- Negative/positive tests: `test_research_verify_europe_benchmark_raw.py`; tampered raw bytes, altered close, altered exchange label, illicit trade-ready promotion and altered label-audit approval are rejected. Tests use deterministic synthetic responses, without external Yahoo calls.
- Duplicate TestCase discovery corrected at commit `6b023d378cc0aeaa55747c733978a1cfaf6bc3cb`.
- GitHub Actions `EU relative strength offline gate tests`, run **42639444581**, commit **6b023d378cc0aeaa55747c733978a1cfaf6bc3cb**: **103 tests, OK** (confirmed directly in offline-gates job logs).
- Real `benchmark-observation` job also succeeded. The live captured JSON was passed through the production verifier, and its actual log reports `{"benchmark_identity_verified":false,"research_only":true,"series_count":4,"status":"provider_bytes_reconciled","trade_ready":false}`.
- All six GitHub workflows for that commit completed **successfully** (AMD `42639444457`, SPY `42639444468`, OMXH25 original PDF bytes `42639444527`, European capture `42639444863`, evidence integrity `42639444611`, EU tests/capture `42639444581`).

## Scope and remaining blockers

`provider_bytes_reconciled` establishes consistency of **retained provider response bytes** with **the recorded provider observations**. It does not independently certify the external Yahoo feed, a specific official Nasdaq index mapping, provider exchange label `STO`, or any strategy profitability. No benchmark identity approval receipt has been issued.

Original Nasdaq PDF capture artifact `13680073011` expires **2026-11-23**; the retained portable ZIP must still be placed in durable external storage with verified read-back. Research branch remains isolated: no changes to `main`, no live scanner deployment and no orders.
