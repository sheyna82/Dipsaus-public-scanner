# Spoor 2 — Real-world DoH/DNSSEC architecture decision (2026-11-11)

Status: research decision only; no network access, production changes, or admission granted.

## Authoritative vendor documentation

- Google Public DNS secure transports: https://developers.google.com/speed/public-dns/docs/secure-transports
- Google Public DNS DoH JSON API: https://developers.google.com/speed/public-dns/docs/doh/json
- Google DNSSEC FAQ: https://developers.google.com/speed/public-dns/faq
- Cloudflare DoH requests: https://developers.cloudflare.com/1.1.1.1/encryption/dns-over-https/make-api-requests/
- Cloudflare JSON caveats: https://developers.cloudflare.com/1.1.1.1/encryption/dns-over-https/make-api-requests/dns-json/
- IANA DNS flags: https://www.iana.org/assignments/dns-parameters

## Decision

Prefer standards-based DNS-over-HTTPS using `application/dns-message` wireformat (RFC 8484) and an explicitly configured validating resolver. Cloudflare recommends wireformat for critical use; JSON formats are not standardized across providers. Google and Cloudflare offer validating public DNS services. This is an architecture candidate, not a validated implementation.

The current custom Ed25519 signed-observation chain is **not a protocol implemented by these public resolvers**. It must not be treated as a prerequisite that a provider can satisfy without a separate independently audited signing gateway. Do not enroll invented resolver signing keys.

## Required verification gates before any future live capture

1. Resolver endpoint hostname allowlist and HTTPS certificate/hostname verification, with a reviewed bootstrap/resolution strategy. TLS authenticates the HTTPS endpoint under the selected PKI model; it does not prove DNSSEC itself.
2. Explicit DNS question (QNAME, QTYPE, QCLASS), `CD=0`, bounded response size, binary response decoding and exact question/answer matching; reject malformed, truncated, mismatched, unexpected, or redirecting responses.
3. DNSSEC-aware validation: `AD=1` from an authenticated validating resolver is an assertion of resolver validation, not local independent DNSSEC proof. Stronger independence requires local RRSIG/DS/DNSKEY validation against a separately established root trust anchor and verified time. Unsigned domains cannot yield positive DNSSEC authentication.
4. Trusted wall-clock timestamps captured by the client, raw request/response hashes, HTTP/TLS transport metadata and provenance receipts; no caller-supplied time as sole freshness evidence.
5. Multiple providers can support discrepancy detection but do not alone prove independence or correctness; compare normalized answers and document cache, CDN, geographic and TTL differences.
6. Fail closed on DNSSEC bogus/SERVFAIL, unknown status, transport failure, or unsupported security claims. Never silently fall back to insecure resolution.
7. Keep DNS verification separate from market-data authenticity, financial evidence, DEGIRO eligibility, signal confidence and trading authorization.

## Validation plan

- Offline parser and negative test corpus first (DNS compression loops, duplicate questions, RCODE, AD/CD flags, DNSSEC unsigned, malformed lengths).
- A separately approved, isolated network capture with exact endpoint, verified TLS, raw response archive and reproducible hash; do not silently enable network.
- Independent comparison and source-integrity audit; only after reproducible evidence, consider bounded integration.

## Current state

No actual DoH request was performed in this research step. No real DNSSEC chain was validated. The checked-in DNS signer trust registry remains empty and issuer attestation remains unavailable. All DNS admission and trading gates remain closed. PR #65 stays draft.
