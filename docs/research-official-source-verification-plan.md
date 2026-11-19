# Official-source verification plan — research only

## Current state (19 November 2026)
The 81 offline tests cover net-EUR arithmetic, explicit slippage, claimed
attestations, provenance categories, privacy-minimized manifests, ISIN
checksum, and cross-source **claim consistency**. They do not fetch or
authenticate official registry entries, DEGIRO route availability, or actual
order-book quotes. All outputs remain non-executable.

## Source-specific evidence required

| Source | Record to capture | Validation before acceptance |
| --- | --- | --- |
| ISO 10383 MIC publication | Official publication/version/date, operating MIC, segment MIC, status, market name | Check original CSV headers and status values against the source publication; confirm active OPRT/SGMT relationship and publication age |
| Exchange instrument register (Xetra / Euronext / Nasdaq etc.) | Source URL, retrieval UTC, file digest, instrument ISIN, exchange MIC, currency, segment, active status | Exact instrument match; verify file format, timestamp, source origin, and segment mapping; reject mismatches |
| DEGIRO broker | Actual instrument/venue route, buy and sell fees, bid and ask, timestamp | Explicit independently supplied broker evidence; no assumed broker API or account access; never publish screenshots/account information |
| Technical structure | Invalidation, first meaningful resistance, target, timeframe, evidence time | Independently review price structure; never infer target solely to satisfy R/R |
| FX | USD/EUR quote, timestamp, spread and conversion fees | Independently verified source and broker conversion policy; provider FX alone is not executable |

## Security and privacy
- No automatic redirect following to unapproved domains for Xetra CSV/ZIP.
- Never accept an HTTP 302 destination as trusted without explicit allowlist
  and a separately recorded approved exact destination.
- Do not publish raw broker screenshots, login/session tokens, account IDs,
  private trade information or personal data in this public repository.
- SHA-256 only establishes content integrity relative to an existing digest.
  A self-reported digest does **not** authenticate the original publisher.
- Store only non-identifying source class, official public instrument IDs,
  timestamps, hashes and rejection reasons in public artifacts.
- Verify instrument-level evidence before any fee/quote-based net scenario.
- A passing offline test or matching source claim must never set
  `trade_ready` or `order_placement_enabled` to True.

## Current blocking conditions
The repository's source audits use Yahoo/Stooq/provider data for research,
not broker execution. The research bridge does not have a verified official
MIC publication parser or a live authenticated exchange instrument adapter.
The DEGIRO account-specific instrument route and costs are not independently
attested. Therefore **no current candidate is promoted to executable status**.

## Next implementation milestones
1. Inspect the original ISO 10383 publication file and exact column schema.
2. Build a pure offline ISO MIC parser with fixture-driven tests; reject
   unexpected headers, duplicate MICs, inactive status and stale publication.
3. Inspect Xetra source CSV/ZIP and approved redirect targets, without
   modifying source integrity or silently following redirects.
4. Build a read-only instrument crosswalk: ISIN ↔ operating MIC ↔ segment MIC.
5. Reconcile the crosswalk against separately attested DEGIRO venue/fee
   evidence; report missing values, never fill with defaults.
6. Extend the non-executable net scenario with separate news, earnings,
   liquidity, risk-cap and portfolio-fit blockers.
