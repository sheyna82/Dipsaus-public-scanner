# Official European benchmark identity crosswalk — 2026-11-09

Status: **PARTIALLY VERIFIED, PROVIDER CAPTURE BLOCKED**.

## Independently verified official variants

| Benchmark | Official symbol | ISIN | Currency | Return type | Official Reuters identifier | Official source |
|---|---|---|---|---|---|---|
| DAX price | DAXK | DE0008467440 | EUR | Price | .GDAXIP | https://stoxx.com/index/dax/?factsheet=true |
| STOXX Europe 600 | SXXP | EU0009658202 | EUR | Price | .STOXX | https://stoxx.com/index/SXXP/?factsheet=true |

The DAX gross-return variant is **DAX**, ISIN **DE0008469008**, Reuters **.GDAXI**, and is **not** a price-only substitute.

## Provider-symbol verification still required

The experimental Yahoo Finance aliases `^GDAXIP` and `^STOXX` are **not validated** by the official Reuters crosswalk. Similar-looking identifiers from different providers must not be equated without metadata and historical price cross-checks. The existing capture module deliberately sets `benchmark_identity_verified=false`.

AEX and OMX Helsinki 25 official variant/ISIN and provider mapping remain pending. No EU relative-strength output is approved. No frozen US threshold is reused.

## Next verification

Capture each provider series; verify exact provider symbol, index name, price-return type, currency, ISIN where available, and independently compare date-aligned closes with official reference observations. Only after this should the benchmark identity gate be opened. Research only; no orders or changes to main/live scanner.
