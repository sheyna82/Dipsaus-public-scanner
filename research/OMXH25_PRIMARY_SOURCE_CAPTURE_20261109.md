# OMXH25 official issuer candidate capture — 2026-11-09

**Research-only, fail-closed, not index identity approval.**

The EU relative-strength CI `benchmark-observation` job now attempts a separate, immutable raw HTTP response capture from:

`https://beta.indexes.nasdaqomx.com/Index/History/OMXH25`

The research capture stores source URL, UTC retrieval time, HTTP status and content type, exact response bytes encoded as Base64, and SHA256. It blocks redirect URL changes, unexpected hosts, oversized responses and overwrites. It does **not** assert the page contains a machine-readable official daily EOD close. HTML content is not parsed or mapped to the official EOD review contract.

The job uses `continue-on-error: true` specifically because the issuer site may block CI access. A successful workflow does **not** prove the issuer candidate was captured; reviewers must inspect the capture step, the artifact member, and its actual byte hash. Absence of the candidate artifact must remain explicit and must not be silently treated as evidence.

The captured bytes, if present, are **not independently authenticated** by the local SHA256 receipt alone. Official EOD extraction, field semantics, and Yahoo `STO` mapping remain unresolved. `benchmark_identity_verified=false`, `research_only=true`, `trade_ready=false`. No live scanner changes, main merge, or trades.

Next action: inspect the new CI job logs and artifact to determine whether the issuer actually returned a usable dated EOD source, and only then design a reviewed parser for that exact response shape.
