# Spoor 2 — DNSSEC chain validation requirements (research only)

Status: **NOT IMPLEMENTED / NOT VERIFIED / NOT ADMITTED**. This document does not enable network access, change production, or enroll a trust anchor.

## Trust boundary

Parsing DNS wireformat and DS/DNSKEY/RRSIG structure is not DNSSEC verification. A resolver's AD bit is an assertion by that resolver, not locally verified proof. Signed observations and self-declared resolver identity likewise cannot replace DNSSEC chain validation.

## Requirements before a DNSSEC verification claim

1. Obtain raw, complete, bounded DNS response evidence, including the relevant RRsets, RRSIG, DNSKEY and DS records, with source metadata and SHA-256 receipts. Explicitly classify missing data, truncation, unsupported types and CNAME/delegation paths; fail closed.
2. Pin a genuine independently provisioned DNSSEC root trust anchor with provenance, update/revocation policy and documented rollover procedure. Never infer trust from a supplied key or a signed observation.
3. Canonicalize each signed RRset per RFC 4034 (owner names, label counts, wildcard expansion, canonical ordering, TTL and wire encodings); reject ambiguous or malformed canonicalization.
4. Verify each RRSIG cryptographically against the correct DNSKEY, using algorithm-specific verification, key tag and signer name, inception/expiration and an independently justified verification clock. Explicitly reject unsupported algorithms and invalid key material.
5. Verify DS digest(s) against child DNSKEY, validate parent DS RRset signatures and recursively authenticate the chain to the independently pinned root anchor. Handle unsigned delegations separately from bogus proofs.
6. Validate authenticated denial of existence (NSEC/NSEC3) when needed, including opt-out semantics; do not equate NXDOMAIN or empty answers with validated absence.
7. Keep resolver TLS authentication, DNSSEC cryptographic validation, source independence, freshness and nonce replay protection as separate gates. None alone authorizes connections, quotes or trades.
8. Use vetted DNSSEC implementation or a dedicated audited verifier, RFC test vectors, known bogus and unsigned domains, mutation/fuzz tests, and independent security review before any admission decision.

## Current limitations

The checked-in wire inspector only rejects certain malformed DNS messages and minimally checks DS/DNSKEY/RRSIG RDATA. It does **not** parse full DNSSEC signer/algorithm semantics, verify signatures, canonicalize RRsets, validate a trust chain, prove resolver identity or validate a DNSSEC trust anchor. Existing signer allowlist is intentionally empty and local nonce issuance is self-asserted. Therefore all DNSSEC, connection and trading admission flags remain false.

## Safe next implementation milestone

Build an **offline evidence inventory** that lists observed RRset types and evidence hashes, preserving raw records without making trust claims. Keep the result strictly informational, and test malformed/duplicate/truncated/unsupported evidence. Separately evaluate a vetted DNSSEC library and published test vectors before implementing cryptographic verification.
