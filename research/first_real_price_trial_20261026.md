"""Usage notes for the first reproducible historical swing data trial.

Status: no successful real-price retrieval has yet been independently verified.
No profitability conclusions should be drawn from synthetic fixtures.

Prepare provider-authorized CSV files with exact header:
session_date,open,high,low,close,volume
Dates must be ISO 8601, ordered, unique; bars must pass strict OHLCV audit.

Example:
python research_swing_price_batch_cli.py \
  --provider 'provider-name-not-yet-verified' \
  --retrieved-at '2026-10-26T12:00:00+00:00' \
  --file AAPL=./data/aapl.csv \
  --file MSFT=./data/msft.csv \
  --manifest-out ./data/manifest.json

Outputs a manifest with per-file SHA-256, date coverage and counts.
This is provenance *recording*, not source authentication.
Never commit licensed/raw market datasets without explicit rights review.
The daily volume column must NOT be used as opening auction volume.

Next milestones:
1. Verify provider endpoint access and rights.
2. Obtain and audit at least one actual dataset.
3. Verify calendar, splits/dividends, currency and data availability time.
4. Create causal signal histories and next-open executable outcomes.
5. Compare against baselines out of sample with costs and risk.
"""
