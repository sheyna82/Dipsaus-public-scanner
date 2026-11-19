# ISO 10383 real-file evidence audit — 19 November 2026

## Exact locally uploaded file

- Filename: `ISO10383_MIC.csv`
- SHA-256: `74cc23bb951c6cc0c2f2f8af60e97e63e36093d5f599975ad1b90311d9daea2b`
- 2,893 data rows, 17 columns, UTF-8-SIG compatible.
- Status distribution: ACTIVE 2,304; EXPIRED 580; UPDATED 9.
- Record types: OPRT 1,599; SGMT 1,294.

The full file is **not committed**. This is an offline inspection of
user-supplied bytes; official server/TLS provenance is not independently
authenticated. Its checksum is an integrity fingerprint, not an
authentication certificate.

## Selected exact register fields

| MIC | Operating MIC | Kind | Status | Creation YYYYMMDD | Last update YYYYMMDD |
|---|---|---|---|---|---|
| XETR | XETR | OPRT | ACTIVE | 20050627 | 20161128 |
| XETA | XETR | SGMT | ACTIVE | 20080324 | 20161128 |
| XETB | XETR | SGMT | ACTIVE | 20080324 | 20251222 |
| XAMS | XAMS | OPRT | ACTIVE | 20050627 | 20150427 |
| XHEL | XHEL | OPRT | ACTIVE | 20110124 | 20230925 |

All selected records have blank expiry dates in this upload.

**Interpretation:** The last-update fields predate the 23 November 2026
implementation date, which is evidence consistent with unchanged records,
but does **not** prove that the previous effective publication had identical
values. The complete November publication remains blocked by the offline
parser as of 19 November 2026; this is intentionally conservative.

## Remaining security and market blockers

1. Authenticate official download origin, redirect chain and pinned digest.
2. Obtain or verify prior effective register for 19 November as-of decisions.
3. Distinguish ISO `UPDATED` status from `ACTIVE`; never treat UPDATED as
   active without explicit source-specific semantics and effective-date proof.
4. Verify DEGIRO instrument route, live executable bid/ask, venue and fees.
5. Keep `trade_ready=False` and `order_placement_enabled=False` always
   in research modules; no automatic orders.
