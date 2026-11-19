# Spoor 2 — pinned runtime snapshot Python audit receipt

Date: 2026-11-11 (UTC)

## Verified execution

- Private source repository: `sheyna82/Dipsaus-scanner`
- Isolated private audit branch: `research/spoor2-private-snapshot-audit-20261111`
- Private audit commit: `d185d0816484e23306fa511a67859276b2804c81`
- GitHub Actions run: https://github.com/sheyna82/Dipsaus-scanner/actions/runs/42991047205
- GitHub Actions job: `130423727220`
- Job conclusion: `success`
- Public research audit code commit: `478d278ee84f2347319a2e58d7dc892df29ebe65`
- Executed module: `python -m research.spoor2_snapshot_audit_20261111`
- Original source bytes retrieved from immutable local Git blobs; not from the mutable working tree.
- Source bytes and raw runtime reports were not published in this receipt.

## Source evidence

| Market | Git blob SHA-1 | Size (bytes) | SHA-256 | Reports | Candidates | Structurally blocked |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| US | `deb568fe686a3f258dc304d20003a251bc4999b6` | 2549942 | `4d9b5c36142a80f4f440f4e834ebec2c6e51c7d3625ae135eb1ab40f724a0b8d` | 7 | 416 | 0 |
| EU | `ec042f197a2f192a25c3488cda1fdcfba44b5604` | 133768 | `2707e730cfae9126e62f1d4b2f8d015bd0e46233eb85c4b3eb26293d92698ef2` | 1 | 61 | 0 |

- Canonical JSON audit-result SHA-256: `6c333c3b96be1164ffb6dd1f97a676571a33433be155f4013cd0ae76b467d92d`.
- Python CLI returned success after independent Git blob hash, SHA-256, size, report count, candidate count, blocked count and fail-closed status checks.
- Output status: `SCHEMA_AUDIT_ONLY`; `trade_ready=false`; `order_placement_enabled=false`.

## Scope and limitations

This receipt establishes reproducible **historical snapshot schema integrity only**. It does not validate current quotes, independent technical support/resistance, invalidation, realistic R/R, costs, net profit, broker eligibility, or any live trade decision. Historical US pivot clusters remain unconfirmed pending independent technical verification. The two earlier private runs failed closed before this corrected success. No changes were made to production `main`, live workflows, ntfy, or orders. PR #65 remains draft.

Next research gate: independently verify current market/venue quotes and provenance of technical levels, then apply realistic financial and broker-eligibility gates before any candidate may be marked trade-ready.
