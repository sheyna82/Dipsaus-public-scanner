# OMXH25 official-source retention and recovery plan — 2026-11-09

**Research only — no provider identity or trading approval.**

## Immutable evidence currently available

- Original GitHub Actions capture: run `42630114290`, artifact `13680073011` (`nasdaq-official-document-unverified-observation`), artifact ZIP SHA256 `6849ebe332ce2be42e51cd9c8537b12e755e739bc4fc4a25ec5bccfcb70fc277`. GitHub artifact expiration: **2026-11-23 13:58:07 UTC**.
- Nasdaq index-versions PDF SHA256: `52f35d3e0d4500e01d116c135628c3e145de0b3929e3532c37f3a59d79f550ef` (109623 bytes).
- Nasdaq methodology PDF SHA256: `41c43c502b6862606aef255a55cef41ccc8ff606b21f8b32975edb48fe6b12a2` (193988 bytes).
- First successful real-artifact CI verification: run `42634125556`, job `129217680433`, receipt artifact `13682690727`, ZIP SHA256 `6ee015cbf6e1e8bbbe5d734e0afe1f239585d3dcabeca3932939b0c75d094eb6`, expires **2026-11-23 14:23:07 UTC**.
- Repeated successful verification: run `42634535402` at commit `819a5fb7ae961301948141d08a27785ed0b98226`. All six associated PR workflows succeeded.
- Offline verifier: `research_verify_omxh25_archive.py`; reconstruction: `research_rebuild_omxh25_archive.py`; CI: `.github/workflows/research-omxh25-original-artifact.yml`.

## Retention risk

The CI job fetches a **fixed historical artifact ID**. After that artifact expires, the download should fail and the workflow should **fail closed**. A successful run before expiration does not guarantee reproducibility after expiration. A published JSON receipt proves what the job observed but **cannot recreate missing original PDF bytes**.

## Recovery requirements

1. Before expiry, retain the **original capture ZIP bytes** in a durable, access-controlled evidence store, with its original ZIP SHA256, acquisition time, run/commit IDs and provenance. Preserve the PDF bytes, not only the derived JSON receipt. Do not commit large/binary evidence to the source repository without explicit retention and licensing review.
2. Independently rehash the retained original ZIP and both decoded PDFs. Store a second verification receipt containing the verifier commit SHA, source hashes, verification timestamp and storage locator; avoid publishing short-lived signed download URLs or credentials.
3. Add an explicit, separately authorized retention source to the workflow only **after** the durable store exists and access/permissions are reviewed. Do not silently fall back to live Nasdaq downloads: a newly fetched PDF may have different bytes and is a new observation.
4. Run a disaster-recovery drill **without** relying on artifact `13680073011`: reconstruct and verify solely from the retained copy, then compare document SHA256 and record any ZIP-container differences.
5. Keep a distinct research record for the Yahoo `^OMXH25` mapping, `STO`/`CET` metadata ambiguity, date-specific official EOD observations and independent reviewer sign-off. Source-byte integrity is **not** benchmark identity approval.

## Status / limitations

As of this record, **no durable external storage location has been verified or provisioned** by this workflow. The recovery plan is documented, not executed. Do not claim that artifact retention has been extended. The fixed-ID workflow will not remain reproducible indefinitely without preservation.

Mandatory gates: `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`. No merge to `main`, live scanner changes, or orders.


## Local positive offline recovery drill — 2026-11-09

A positive recovery drill was completed against the **locally retained original capture artifact ZIP**, without downloading fresh Nasdaq documents or fetching the source from GitHub during the drill. This was a local reproduction of the repository's reconstruction and verifier checks, **not an execution of the checked-in recovery entrypoint within GitHub CI**.

- Source: original capture artifact `13680073011` saved locally as `github-actions-artifact-13680073011.zip`, independently rehashed SHA256 `6849ebe332ce2be42e51cd9c8537b12e755e739bc4fc4a25ec5bccfcb70fc277`.
- Two decoded original PDFs rehashed against pinned official-source SHA256 values; each matched.
- Reconstructed local archive `OMXH25_offline_recovery_verified_20261109.zip` SHA256 `f47b5c34b167963466eaca5feaec103a43e994d592ea6600b824633b4c7ba115`. ZIP member set, manifest, document lengths and hashes checked.
- Local receipt `OMXH25_offline_recovery_receipt_20261109.json` records `status=verified_original_bytes`, `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`.
- CI at code commit `6e67bce14c8e88546818003e1df73e75347e4794`: **93 tests, OK**, including four new negative offline-recovery tests; all six associated workflows successful.

**Limit:** this demonstrates recovery from a locally retained copy during this session. It does **not** establish durable offsite storage, indefinite artifact availability, formal benchmark identity verification or trading authorization. Next: execute the exact checked-in recovery entrypoint in a dedicated CI recovery drill using an explicitly provisioned durable source, and document storage ownership, access and retention.
