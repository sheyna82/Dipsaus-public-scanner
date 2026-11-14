# Spoor 2 — DNS trust-boundary audit (2026-11-11)

Scope: offline research modules only. This is a source-code review, not a live security assessment or proof of independent DNS provenance. Baseline: CI run 43009158272, 258 tests passed.

## Verified from implementation

1. `verify_signed_dns_observation` verifies an Ed25519 signature over the canonical record, including `challenge_nonce`, after comparing exact record fields and claimed time. This proves possession of the signing private key, **not** DNS authenticity, DNSSEC, resolver identity, or source independence.
2. `APPROVED_DNS_SIGNER_KEY_SHA256=frozenset()` is empty. Production-like verification cannot establish `key_trusted=True` under the checked-in policy. Tests that patch this outcome are isolated simulations, not enrolled keys.
3. `issue_dns_challenge` stores caller-provided `issuer_id`. `review_dns_challenge_issuance` always returns `issuer_attested=False`. No actual issuer attestation exists.
4. `review_dns_challenge_admission` checks signature, key trust, issuance and issuer attestation before calling `consume_dns_challenge_once`. Under checked-in defaults the consumption path is unreachable; the mocked positive-path test is not evidence of operational readiness.
5. `consume_dns_challenge_once` relies on a local SQLite PRIMARY KEY for replay prevention. It does not provide cross-host coordination or authorization.

## Open risks, prioritized

**P0 — Trust evidence unavailable.** No independently verified DNS evidence producer, enrolled signer, authenticated issuer, or DNSSEC validation. Do not label evidence independently verified, admit DNS, enable network capture or trading from these modules. Do not invent an Ed25519 signer for a public DNS-over-HTTPS service.

**P1 — Caller-controlled clock.** `verification_time_utc` is provided by the caller, so the age-window check is only a comparison of claims. Bind verification to a trusted clock at the service boundary, with controlled clock-skew policy and tests for replay across time.

**P1 — Separate databases and check/use gap.** Issuance lookup and consumption occur in separate calls/databases; there is no atomic transaction binding issued, unexpired, unrevoked and unused status. In a future authenticated-issuer implementation, use one transactional authority for issuance and consumption or a separately proven distributed coordination mechanism.

**P1 — Filesystem authority.** Database paths are caller-provided; symlinks, permission controls, ownership, durability, and tampering are not established. Restrict to an application-owned path and protect file permissions and backups before deployment.

**P1 — Challenge issuance authenticity.** Current issuance accepts caller-chosen nonce and self-asserted issuer ID. A real challenge service should generate unpredictable nonces using a CSPRNG, authenticate the issuer, bind hostname/request/expiry and maintain revocation status. Do not confuse an issuance row with an authenticated issuance receipt.

**P2 — Positive-path tests use patched trust decisions.** Keep these tests clearly named as simulations. Add real-source integration tests only after an independent evidence source and its documented trust model are selected.

## Next research decision

Stop expanding self-asserted admission gates. First identify a real DNS verification architecture (e.g. DNSSEC-validating resolver with independently pinned trust roots, plus documented DoH transport verification where appropriate). Independently capture raw source evidence and verify its provenance, freshness and identity. Only then design an authenticated issuance/consumption authority and an integration protocol. Continue fail-closed; keep PR #65 draft and production unchanged.
