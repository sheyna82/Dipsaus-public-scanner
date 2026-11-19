# Spoor 2 — instrument identity and canonical signing contract (research only)

Status: **provisional research contract; no admission authority**. This document does not change the scanner, grant source authority, or enable trading.

## Boundaries

1. **Exact signed bytes.** Current offline Ed25519 verifiers serialize a record using Python `json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")`. A valid signature proves possession of the supplied signing key for those exact bytes only. The format is an implementation-specific serialization contract, **not** an assertion of general cross-language canonical JSON compliance.
2. **Unicode.** Reject isolated surrogate code points U+D800–U+DFFF in instrument identity fields. Do **not** silently normalize NFC/NFD, case-fold, strip whitespace, transliterate, or replace confusable characters in the signed payload. Distinct Unicode sequences remain distinct signed records. Any future normalization policy requires a versioned schema, independent source agreement, and explicit regression tests.
3. **Identity fields.** `symbol`, `market`, `venue_mic`, and `isin` are string claims. Type, length, Unicode scalar validity and candidate equality do **not** prove exchange assignment, ISIN checksum, MIC registration, or issuer identity. A valid checksum alone would not establish authoritative instrument mapping.
4. **Source authority.** Caller-provided keys and signatures do not establish independent provenance. Approved signer fingerprint set remains empty. Do not infer `source_attested=True` from signature success.
5. **Freshness and replay.** An `observed_utc` timestamp and a syntactically valid `challenge_nonce` are claims, not trusted issuance or single-use enforcement. No trusted clock, issuer or persistent replay store is connected.
6. **Fail-closed trading boundary.** `trade_ready=False` and `order_placement_enabled=False` remain mandatory for all paths, including cryptographically valid but unattested observations.

## Proposed negative-test matrix (not yet an assertion of test coverage)

- Isolated high/low surrogate in each identity field: reject before signature verification.
- NFC vs NFD visually similar values: exact-byte signature binding must not silently normalize or equate them.
- Noncanonical Base64 key and signature encodings: reject even if decoded bytes match.
- Invalid/mismatched identity field type and excessive length: block.
- Valid-looking but unverified ISIN/MIC/symbol mapping: never confer source authority.
- Reused nonce, untrusted timestamp, and caller-selected public key: never confer replay protection or trading readiness.
- Cross-language serialization mismatch: block unless an explicitly versioned and verified canonicalization contract is established.

## Change control

Before implementing normalization or external instrument validation: write failing offline tests, document the source-of-truth and versioned byte contract, preserve research/production separation, and verify the isolated Spoor 2 regression plus PR workflows. PR #65 remains draft and must not be merged as part of this work.
