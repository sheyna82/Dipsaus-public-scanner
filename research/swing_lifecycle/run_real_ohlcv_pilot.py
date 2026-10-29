"""Bounded real-provider OHLCV experiment, manually invoked in GitHub Actions.

Uses existing audited European pilot fetcher. No synthetic bars, trade orders,
or strategy optimisation. Provider failures remain explicit.
"""
import argparse
import gzip
import json
from datetime import date, datetime, timezone
from pathlib import Path

from europe_ohlcv_pilot import fetch
from research.swing_lifecycle.evaluate_existing_ohlcv_pilot import evaluate_pilot_artifact

SYMBOLS = (
    ("ASML.AS", "technology"), ("INGA.AS", "financials"),
    ("SAP.DE", "technology"), ("SIE.DE", "industrials"),
    ("SAN.PA", "healthcare"), ("AIR.PA", "industrials"),
    ("NOVN.SW", "healthcare"), ("NESN.SW", "consumer"),
)


def run(output, *, cutoff):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    source_rows, records = [], []
    for symbol, sector in SYMBOLS:
        audit, record = fetch(symbol, sector)
        source_rows.append(audit)
        if record is not None and audit.get("status") == "PASS":
            records.append({
                "symbol": symbol,
                "bars": record["bars"],
                "currency": record["currency"],
                "exchange": record["exchange"],
            })
    archive = output / "historical_provider_ohlcv.jsonl.gz"
    with gzip.open(archive, "wt", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record) + "\n")
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "requested": len(SYMBOLS),
        "fetched": len(records),
        "source_audit": source_rows,
        "source": "Yahoo chart via existing europe_ohlcv_pilot.fetch",
        "research_only": True,
        "trade_ready": False,
        "historical_edge_proven": False,
    }
    if records:
        try:
            report["diagnostic"] = evaluate_pilot_artifact(
                archive, cutoff=cutoff, holding_sessions=10,
                entry_stride=20)
        except (ValueError, KeyError, IndexError) as exc:
            report["diagnostic_error"] = type(exc).__name__ + ": " + str(exc)
    else:
        report["diagnostic_error"] = "DATA-BLOCKED: no usable OHLCV"
    (output / "historical_warning_experiment.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({
        "requested": len(SYMBOLS), "fetched": len(records),
        "diagnostic_status": "available" if "diagnostic" in report else "blocked",
        "report_path": str(output / "historical_warning_experiment.json"),
    }))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="reports/warning-real-pilot")
    parser.add_argument("--cutoff", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    run(args.output, cutoff=args.cutoff)
