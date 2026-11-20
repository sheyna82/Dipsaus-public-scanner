# DIPSAUS — historical batch digest attestation design (research only)

Status: **design only**. No private repository changes, external service,
GitHub environment/secrets changes, automated execution or public artifacts.

## Threat model

A SHA-256 digest generated alongside a batch is a *checksum*, not a trusted
timestamp or independent proof of original content. A party able to rewrite
both the archive and the digest can make a modified batch appear consistent.
An ordinary Git commit or workflow log is not by itself independent,
tamper-resistant attestation. Hashes of low-entropy private values may
also reveal information through guessing; never publish raw archive digests
or deterministic hashes of ticker/position fields.

## Proposed trust separation

1. **Private event archive**: keep full scanner events, as-of feature snapshots,
   outcome observations, and candidate identifiers in a restricted private
   store, with access logging and retention policy. This requires a separate
   reviewed change; no current production integration is authorized.
2. **Independent attestation boundary**: a separately administered, append-only
   or externally timestamped store receives only a *keyed* commitment to the
   canonical batch digest plus batch sequence and creation time. The signing
   or HMAC key must not reside with the archive writer. Merely using an
   environment secret controlled by the same principal does not qualify.
3. **Verification**: independently fetch the stored commitment and verify
   sequence continuity, timestamps, author/key identity, revocation status,
   archive canonicalization, event coverage, and signatures/commitments.
   Fail closed on absent, altered, duplicated, or reordered batches.
4. **Privacy**: do not publish raw digests, source hashes, private IDs, symbols,
   holdings, quotes, or report contents to public Actions, logs, artifacts,
   commits, notifications or documentation. Even keyed commitments require
   a privacy and access review before deployment.

## Proposed attestation metadata (conceptual; not a deployed schema)

- schema_version, opaque batch identifier, monotonic sequence number
- batch opened/closed UTC, independently recorded attested UTC
- canonicalization version and cryptographic algorithm identifier
- keyed commitment / signature, key identifier, verifier identity
- previous commitment (chain link), verification result and reason

Do not accept self-reported timestamps or a self-reported verified=true flag
as proof. A signed batch can still be incomplete: independent scanner intake
counts and outcome provenance must be verified separately.

## Release gates

- Synthetic adversarial tests: tampering, missing/duplicate/reordered batch,
  wrong key, revoked key, late attestation, replay and missing prior link.
- Privacy review, key ownership separation, secret rotation and recovery.
- Independent point-in-time capture evidence for rejected/deferred candidates.
- Explicit approval before any private-state, workflow or production changes.

Until those conditions are met: archive authenticity unverified,
backtest_validated=false, trade_ready=false, order_placement_enabled=false.
