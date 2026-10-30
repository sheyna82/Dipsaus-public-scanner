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
from research.swing_lifecycle.evaluate_warning_risk_archive import evaluate_archive
from research.swing_lifecycle.warning_quarter_robustness import evaluate as quarter_robustness
from research.swing_lifecycle.warning_preentry_regimes import evaluate as preentry_regimes
from research.swing_lifecycle.warning_decision_holdout import evaluate as decision_holdout
from research.swing_lifecycle.warning_duration_placebo import evaluate as duration_placebo

SYMBOLS = (
    ("ASML.AS", "technology"), ("INGA.AS", "financials"),
    ("SAP.DE", "technology"), ("SIE.DE", "industrials"),
    ("SAN.PA", "healthcare"), ("AIR.PA", "industrials"),
    ("NOVN.SW", "healthcare"), ("NESN.SW", "consumer"),
    ("ASM.AS", "technology"), ("BESI.AS", "technology"),
    ("IFX.DE", "technology"), ("ADYEN.AS", "technology"),
    ("BNP.PA", "financials"), ("DBK.DE", "financials"),
    ("ABN.AS", "financials"), ("ISP.MI", "financials"),
    ("BAS.DE", "materials"), ("AKE.PA", "materials"),
    ("MC.PA", "consumer"), ("OR.PA", "consumer"),
    ("TTE.PA", "energy"), ("ENI.MI", "energy"),
    ("RWE.DE", "utilities"), ("IBE.MC", "utilities"),
    ("DHL.DE", "transport"), ("LHA.DE", "transport"),
    ("ALFEN.AS", "industrials"), ("RHM.DE", "industrials"),
    ("PHIA.AS", "healthcare"), ("BAYN.DE", "healthcare"),
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
    euro_records = [record for record in records if record["currency"] == "EUR"]
    euro_archive = output / "historical_eur_only_ohlcv.jsonl.gz"
    with gzip.open(euro_archive, "wt", encoding="utf-8") as stream:
        for record in euro_records:
            stream.write(json.dumps(record) + "\n")
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "requested": len(SYMBOLS),
        "fetched": len(records),
        "eur_only_symbols": [record["symbol"] for record in euro_records],
        "source_audit": source_rows,
        "source": "Yahoo chart via existing europe_ohlcv_pilot.fetch",
        "research_only": True,
        "trade_ready": False,
        "historical_edge_proven": False,
    }
    if records:
        try:
            report["confirmation_sensitivity"] = {
                str(n): evaluate_pilot_artifact(
                    archive, cutoff=cutoff, holding_sessions=10,
                    entry_stride=20, confirmation_sessions=n)
                for n in (1, 2, 3)
            }
            report["diagnostic"] = report["confirmation_sensitivity"]["1"]
            # Predeclared chronological cutoff sensitivity; never select a rule
            # by optimizing on any of these later-period observations.
            report["chronological_cutoff_sensitivity_eur"] = {}
            for rolling_cutoff in (
                date(2026, 1, 1), date(2026, 4, 1),
                date(2026, 7, 1)
            ):
                report["chronological_cutoff_sensitivity_eur"][rolling_cutoff.isoformat()] = {
                    str(n): evaluate_pilot_artifact(
                        euro_archive, cutoff=rolling_cutoff,
                        holding_sessions=10, entry_stride=20,
                        confirmation_sessions=n)
                    for n in (1, 2, 3)
                }

            if euro_records:
                report["eur_warning_risk_diagnostics"] = evaluate_archive(
                    euro_archive, output)
                report["eur_warning_quarter_robustness"] = quarter_robustness(
                    output / "warning_risk_cases.csv")
                (output / "warning_quarter_robustness.json").write_text(
                    json.dumps(report["eur_warning_quarter_robustness"], indent=2),
                    encoding="utf-8")
                report["eur_preentry_regimes"] = preentry_regimes(
                    output / "warning_risk_cases.csv", euro_archive)
                (output / "warning_preentry_regimes.json").write_text(
                    json.dumps(report["eur_preentry_regimes"], indent=2),
                    encoding="utf-8")
                report["eur_warning_decision_holdout"] = decision_holdout(
                    output / "warning_risk_cases.csv", euro_archive)
                (output / "warning_decision_holdout.json").write_text(
                    json.dumps(report["eur_warning_decision_holdout"], indent=2),
                    encoding="utf-8")
                report["eur_duration_placebo"] = duration_placebo(
                    output / "warning_risk_cases.csv", euro_archive)
                (output / "warning_duration_placebo.json").write_text(
                    json.dumps(report["eur_duration_placebo"], indent=2),
                    encoding="utf-8")
                report["eur_only_confirmation_sensitivity"] = {
                    str(n): evaluate_pilot_artifact(
                        euro_archive, cutoff=cutoff, holding_sessions=10,
                        entry_stride=20, confirmation_sessions=n)
                    for n in (1, 2, 3)
                }
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
