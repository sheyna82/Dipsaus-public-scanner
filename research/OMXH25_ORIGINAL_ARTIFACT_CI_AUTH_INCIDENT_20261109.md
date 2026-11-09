# OMXH25 actual issuer artifact CI access incident — 2026-11-09

- Run **42680608657**, offline-gates job **129373802509**: **134 tests OK**, but overall job failed on extra artifact download with **HTTP 401**. The GitHub Actions token could not authenticate cross-run artifact retrieval. This is **not** a failure of the 134 unit tests or of the issuer data.
- Artifact **13700999627**, source run **42679785882**, expected ZIP SHA256 **b0aaeb32563f96f91dcc7372c96a183fb247a0cf3392c4bc94111fd23b8c0465**.
- The previously downloaded artifact was re-inspected outside CI: ZIP digest matched exactly; its `omxh25-history-post-raw-unverified.json` contained 3 issuer rows; raw base64 decoded bytes SHA256 **13a001c9ae5f92b78bfa0dfca421b5f1cb127d737578f983c9efc4ff94edaf2c**, equal to receipt. This checks ZIP/raw integrity, **not yet a recorded execution of the exact repository verifier against the original ZIP**.
- Removed the cross-run download step and reverted `actions: read` permission in commit **9e3a5e169c6241abbeb730511293c992bb6b9f3b**. The standalone offline verifier and its tests remain.
- Next: execute `python research_verify_omxh25_real_history_artifact.py ORIGINAL.zip` in a workspace with both the checked-out research branch and a legitimately downloaded artifact; preserve its JSON receipt, exit code and hashes. Do not weaken auth, make artifacts public or add secrets.
- Preserve `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`. No main/live changes or orders.
