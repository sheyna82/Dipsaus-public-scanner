# OMXH25 original Nasdaq HistoryData artifact — actual offline verifier execution

Date: 2026-11-09. Scope: research only. This is a **local execution of the repository's offline verification code**, not a successful GitHub Actions cross-run download (that attempt returned HTTP 401).

## Inputs and command

- Original GitHub Actions run: `42679785882`; artifact ID: `13700999627`.
- Downloaded original artifact ZIP SHA256: `b0aaeb32563f96f91dcc7372c96a183fb247a0cf3392c4bc94111fd23b8c0465`.
- Executed unchanged repository module content from `research_verify_omxh25_real_history_artifact.py` and its import `research_validate_omxh25_real_history_post.py` in an isolated local directory, using the actual original downloaded ZIP.
- Command: `python research_verify_omxh25_real_history_artifact.py ORIGINAL_ARTIFACT.zip`
- Exit status: **0 (success)**.

## Observed machine-readable output

```json
{"benchmark_identity_verified": false, "independently_audited": false, "official_eod_raw_bytes_verified": true, "record_count": 3, "records": [{"date": "2026-11-05", "value": 6254.30092842816}, {"date": "2026-11-06", "value": 6221.79256147799}, {"date": "2026-11-09", "value": 6278.94714570764}], "research_only": true, "source_sha256": "13a001c9ae5f92b78bfa0dfca421b5f1cb127d737578f983c9efc4ff94edaf2c", "status": "issuer_history_raw_and_schema_verified_research_only", "trade_ready": false}
```

## Interpretation and remaining gate

The issuer's raw response is preserved and schema-validated, including its EUR/ISIN, session dates and positive index values. The output flag `official_eod_raw_bytes_verified=true` refers **only to the preserved issuer HistoryData bytes and validated EOD request**; it does not approve benchmark identity, methodology, Yahoo symbol mapping, independent auditing, or trade use. All higher gates remain false. No changes to main or live scanner and no orders.

CI run `42680828759` independently confirmed 134 unit tests passed; all six workflows for the previous commit succeeded.
