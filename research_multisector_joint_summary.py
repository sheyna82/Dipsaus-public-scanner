"""Aggregate sector replication cautiously without treating symbols as independent.

Reads newline-delimited JSON output from the existing historical replication
runner. Descriptive only; rejects invalid, duplicate or incomplete coverage.
"""
import json
import sys
from research_multisector_five_year_coverage import SECTORS

EXPECTED = {symbol: sector for sector, symbols in SECTORS.items() for symbol in symbols}


def summarize(records):
    by_symbol = {}
    for row in records:
        symbol = row.get("symbol")
        if symbol not in EXPECTED or symbol in by_symbol or row.get("sector") != EXPECTED[symbol]:
            return {"status": "DATA_BLOCKED", "reason": "invalid_or_duplicate_universe", "trade_ready": False}
        by_symbol[symbol] = row
    if set(by_symbol) != set(EXPECTED):
        return {"status": "DATA_BLOCKED", "reason": "incomplete_universe", "trade_ready": False}
    valid = [row for row in by_symbol.values() if row.get("status") == "EXPLORATORY_JOINT_FACTOR_DIAGNOSTIC"]
    blocked = [s for s, row in by_symbol.items() if row.get("status") != "EXPLORATORY_JOINT_FACTOR_DIAGNOSTIC"]
    if not valid:
        return {"status": "DATA_BLOCKED", "reason": "no_valid_symbols", "trade_ready": False}
    # Cross-symbol same-day clusters are not independent observations.
    from collections import Counter
    day_counts = Counter()
    all_signal_days = []
    all_event_outcomes = []
    for row in valid:
        dependency = row.get("dependence_diagnostic")
        if not isinstance(dependency, dict):
            return {"status": "DATA_BLOCKED", "reason": "missing_dependence_diagnostic", "trade_ready": False}
        dates = dependency.get("test_signal_dates")
        if (not isinstance(dates, list) or len(dates) != row["baseline_test"]["events"]
                or len(set(dates)) != len(dates)
                or any(not isinstance(day, str) or len(day) != 10 for day in dates)):
            return {"status": "DATA_BLOCKED", "reason": "invalid_signal_dates", "trade_ready": False}
        outcomes = dependency.get("test_event_outcomes")
        if (not isinstance(outcomes, list) or len(outcomes) != len(dates)
                or [o.get("date") for o in outcomes if isinstance(o, dict)] != dates
                or any(type(o.get("atr_structure_selected")) is not bool
                       or type(o.get("net_return_pct")) not in (int, float)
                       for o in outcomes if isinstance(o, dict))
                or any(not isinstance(o, dict) for o in outcomes)):
            return {"status": "DATA_BLOCKED", "reason": "invalid_event_outcomes", "trade_ready": False}
        all_event_outcomes.extend(outcomes)
        day_counts.update(dates)
        all_signal_days.extend(dates)
    from datetime import date
    try:
        ordered_days = sorted(date.fromisoformat(day) for day in day_counts)
    except ValueError:
        return {"status": "DATA_BLOCKED", "reason": "invalid_signal_date_format", "trade_ready": False}
    # Calendar-window clustering is only a sensitivity proxy, not trading-session independence.
    rolling_pairs_14_calendar_days = sum(
        day_counts[ordered_days[i].isoformat()] * day_counts[ordered_days[j].isoformat()]
        for i in range(len(ordered_days)) for j in range(i + 1, len(ordered_days))
        if (ordered_days[j] - ordered_days[i]).days < 14
    )
    # Predeclared calendar offsets: test sensitivity to arbitrary block boundaries.
    # Descriptive only: the offset analyses reuse the same observations.
    anchor = ordered_days[0]
    offset_sensitivity = []
    for offset in (0, 3, 7, 10):
        blocks = {}
        for event in all_event_outcomes:
            block = ((date.fromisoformat(event["date"]) - anchor).days + offset) // 14
            blocks.setdefault(block, []).append(event)
        deltas = []
        for group in blocks.values():
            selected = [e["net_return_pct"] for e in group if e["atr_structure_selected"]]
            rejected = [e["net_return_pct"] for e in group if not e["atr_structure_selected"]]
            if selected and rejected:
                deltas.append(sum(selected)/len(selected) - sum(rejected)/len(rejected))
        offset_sensitivity.append({
            "offset_calendar_days": offset, "total_blocks": len(blocks),
            "paired_blocks": len(deltas),
            "selected_better_blocks": sum(d > 0 for d in deltas),
            "selected_worse_blocks": sum(d < 0 for d in deltas),
            "selected_equal_blocks": sum(d == 0 for d in deltas),
            "mean_paired_block_delta_pct": round(sum(deltas)/len(deltas), 5) if deltas else None})
    observed_deltas = [x["mean_paired_block_delta_pct"] for x in offset_sensitivity]
    time_block = {"calendar_days_per_block": 14,
                  "all_offsets_positive": all(x is not None and x > 0 for x in observed_deltas),
                  "min_offset_delta_pct": min(x for x in observed_deltas if x is not None) if any(x is not None for x in observed_deltas) else None,
                  "max_offset_delta_pct": max(x for x in observed_deltas if x is not None) if any(x is not None for x in observed_deltas) else None,
                  **{k: v for k, v in offset_sensitivity[0].items() if k != "offset_calendar_days"},
                  "offset_sensitivity": offset_sensitivity,
                  "formal_significance_test": False}
    # Predeclared chronological thirds: a descriptive stability check across eras.
    # Calendar thirds use the observed holdout span; no future outcomes inform selection.
    first_day, final_day = ordered_days[0], ordered_days[-1]
    span = (final_day - first_day).days + 1
    era_sensitivity = []
    for era in range(3):
        group = [e for e in all_event_outcomes
                 if min(2, 3 * (date.fromisoformat(e["date"]) - first_day).days // span) == era]
        selected = [e["net_return_pct"] for e in group if e["atr_structure_selected"]]
        rejected = [e["net_return_pct"] for e in group if not e["atr_structure_selected"]]
        era_sensitivity.append({
            "chronological_third": era + 1,
            "events": len(group), "selected_events": len(selected),
            "rejected_events": len(rejected),
            "selected_minus_rejected_mean_pct":
                round(sum(selected)/len(selected) - sum(rejected)/len(rejected), 5)
                if selected and rejected else None})
    # Regime composition by chronological third, based on information available at signal.
    era_market_regimes = []
    for era in range(3):
        group = [e for e in all_event_outcomes
                 if min(2, 3 * (date.fromisoformat(e["date"]) - first_day).days // span) == era]
        regimes = []
        for market_up in (True, False):
            subset = [e for e in group if e["market_20d_positive"] is market_up]
            selected = [e["net_return_pct"] for e in subset if e["atr_structure_selected"]]
            rejected = [e["net_return_pct"] for e in subset if not e["atr_structure_selected"]]
            regimes.append({"market_20d_positive": market_up, "events": len(subset),
                "selected_events": len(selected), "rejected_events": len(rejected),
                "selected_minus_rejected_mean_pct":
                    round(sum(selected)/len(selected) - sum(rejected)/len(rejected), 5)
                    if selected and rejected else None})
        era_market_regimes.append({"chronological_third": era + 1, "regimes": regimes})
    # Diagnose whether era differences are driven by changing symbol composition.
    # Within-symbol contrasts are descriptive and deliberately unweighted.
    symbol_era = []
    for row in valid:
        outcomes = row["dependence_diagnostic"]["test_event_outcomes"]
        for era in range(3):
            group = [e for e in outcomes
                     if min(2, 3 * (date.fromisoformat(e["date"]) - first_day).days // span) == era]
            selected = [e["net_return_pct"] for e in group if e["atr_structure_selected"]]
            rejected = [e["net_return_pct"] for e in group if not e["atr_structure_selected"]]
            symbol_era.append({"symbol": row["symbol"], "chronological_third": era + 1,
                "events": len(group), "selected_events": len(selected), "rejected_events": len(rejected),
                "selected_minus_rejected_mean_pct":
                    round(sum(selected)/len(selected) - sum(rejected)/len(rejected), 5)
                    if selected and rejected else None})
    era_symbol_coverage = []
    for era in range(1, 4):
        groups = [x for x in symbol_era if x["chronological_third"] == era]
        comparable = [x for x in groups if x["selected_minus_rejected_mean_pct"] is not None]
        era_symbol_coverage.append({"chronological_third": era,
            "symbols_with_events": sum(x["events"] > 0 for x in groups),
            "symbols_with_both_groups": len(comparable),
            "symbols_selected_better": sum(x["selected_minus_rejected_mean_pct"] > 0 for x in comparable),
            "symbols_rejected_better": sum(x["selected_minus_rejected_mean_pct"] < 0 for x in comparable)})
    era_breadth = [{"chronological_third": e["chronological_third"],
                    "comparable_symbols": e["symbols_with_both_groups"],
                    "filter_better_share_pct": round(100 * e["symbols_selected_better"] / e["symbols_with_both_groups"], 2)
                        if e["symbols_with_both_groups"] else None,
                    "majority_better": e["symbols_selected_better"] > e["symbols_with_both_groups"] / 2
                        if e["symbols_with_both_groups"] else None}
                   for e in era_symbol_coverage]
    era_deltas = [e["selected_minus_rejected_mean_pct"] for e in era_sensitivity]
    era_stability = {"all_eras_positive": all(x is not None and x > 0 for x in era_deltas),
                     "eras_positive": sum(x is not None and x > 0 for x in era_deltas),
                     "eras_negative": sum(x is not None and x < 0 for x in era_deltas),
                     "era_range_pct_points": round(max(era_deltas) - min(era_deltas), 5)
                         if all(x is not None for x in era_deltas) else None,
                     "stable_across_eras_claimed": False}
    cross_symbol = {"distinct_signal_days": len(day_counts),
                    "cross_day_pairs_within_14_calendar_days": rolling_pairs_14_calendar_days,
                    "days_with_multiple_symbols": sum(n > 1 for n in day_counts.values()),
                    "signals_on_shared_days": sum(n for n in day_counts.values() if n > 1),
                    "same_day_cross_symbol_pairs": sum(n * (n - 1) // 2 for n in day_counts.values()),
                    "largest_same_day_cluster": max(day_counts.values(), default=0),
                    "effective_days_kish_descriptive": round(sum(day_counts.values()) ** 2 / sum(n*n for n in day_counts.values()), 3) if day_counts else None,
                    "cross_day_market_dependence_unmeasured": True}
    comparisons = {}
    for key in ("atr_and_structure", "atr_and_market", "atr_structure_market"):
        better, worse, equal, empty, missed, evaluated = 0, 0, 0, 0, 0, 0
        for row in valid:
            base = row["baseline_test"]["mean_net_return_pct"]
            factor = row["factors"][key]
            selected = factor["selected"]
            missed += factor["missed_winning_events"]
            evaluated += row["baseline_test"]["events"]
            if selected is None:
                empty += 1
                continue
            diff = selected["mean_net_return_pct"] - base
            better += diff > 0
            worse += diff < 0
            equal += diff == 0
        comparisons[key] = {"symbols_better": better, "symbols_worse": worse,
                            "symbols_equal": equal, "symbols_without_selected": empty,
                            "missed_winning_events_sum": missed,
                            "test_events_sum": evaluated}
    regime_summary = {}
    for label in ("market_20d_positive", "market_20d_nonpositive"):
        totals = {"events": 0, "selected_events": 0, "rejected_events": 0,
                  "missed_winning_events": 0, "selected_winning_events": 0,
                  "selected_severe_adverse_events_estimate": None}
        baseline_return_weighted = 0.0
        baseline_adverse_weighted = 0.0
        baseline_severe_weighted = 0.0
        rejected_return_weighted = 0.0
        rejected_adverse_weighted = 0.0
        rejected_severe_weighted = 0.0
        selected_return_weighted = 0.0
        selected_adverse_weighted = 0.0
        selected_severe_weighted = 0.0
        for row in valid:
            regime = row.get("market_regime_diagnostics", {}).get(label)
            if not isinstance(regime, dict):
                return {"status": "DATA_BLOCKED", "reason": "missing_regime_diagnostic",
                        "trade_ready": False}
            base = regime.get("baseline")
            selected = regime.get("atr_structure_selected")
            rejected = regime.get("atr_structure_rejected")
            n = (base or {}).get("events", 0)
            ns = (selected or {}).get("events", 0)
            nr = (rejected or {}).get("events", 0)
            missed = regime.get("missed_winning_events")
            if ns + nr != n or type(missed) is not int or not 0 <= missed <= nr:
                return {"status": "DATA_BLOCKED", "reason": "regime_count_inconsistent",
                        "trade_ready": False}
            if base:
                baseline_return_weighted += n * base["mean_net_return_pct"]
                baseline_adverse_weighted += n * base["mean_adverse_excursion_pct"]
                baseline_severe_weighted += n * base["severe_adverse_rate_pct"]
            totals["events"] += n
            totals["selected_events"] += ns
            totals["rejected_events"] += nr
            totals["missed_winning_events"] += missed
            if rejected:
                rejected_return_weighted += nr * rejected["mean_net_return_pct"]
                rejected_adverse_weighted += nr * rejected["mean_adverse_excursion_pct"]
                rejected_severe_weighted += nr * rejected["severe_adverse_rate_pct"]
            if selected:
                totals["selected_winning_events"] += selected["winning_events"]
                selected_return_weighted += ns * selected["mean_net_return_pct"]
                selected_adverse_weighted += ns * selected["mean_adverse_excursion_pct"]
                selected_severe_weighted += ns * selected["severe_adverse_rate_pct"]
        n = totals["events"]
        totals["baseline_mean_net_return_pct"] = round(baseline_return_weighted / n, 5) if n else None
        totals["baseline_mean_adverse_excursion_pct"] = round(baseline_adverse_weighted / n, 5) if n else None
        totals["baseline_severe_adverse_rate_pct"] = round(baseline_severe_weighted / n, 3) if n else None
        nr = totals["rejected_events"]
        totals["rejected_mean_net_return_pct"] = round(rejected_return_weighted / nr, 5) if nr else None
        totals["rejected_mean_adverse_excursion_pct"] = round(rejected_adverse_weighted / nr, 5) if nr else None
        totals["rejected_severe_adverse_rate_pct"] = round(rejected_severe_weighted / nr, 3) if nr else None
        ns = totals["selected_events"]
        totals["selected_mean_net_return_pct"] = round(selected_return_weighted / ns, 5) if ns else None
        totals["selected_mean_adverse_excursion_pct"] = round(selected_adverse_weighted / ns, 5) if ns else None
        totals["selected_severe_adverse_rate_pct"] = round(selected_severe_weighted / ns, 3) if ns else None
        totals.pop("selected_severe_adverse_events_estimate")
        regime_summary[label] = totals
    if sum(x["events"] for x in regime_summary.values()) != sum(
            row["baseline_test"]["events"] for row in valid):
        return {"status": "DATA_BLOCKED", "reason": "regime_total_mismatch",
                "trade_ready": False}
    return {"status": "EXPLORATORY_SECTOR_REPLICATION_SUMMARY",
            "symbols_evaluated": len(valid), "symbols_blocked": sorted(blocked),
            "comparisons": comparisons, "cross_symbol_dependence": cross_symbol,
            "time_block_sensitivity": time_block,
            "chronological_era_sensitivity": era_sensitivity,
            "chronological_era_stability": era_stability,
            "chronological_era_symbol_coverage": era_symbol_coverage,
            "chronological_era_breadth": era_breadth,
            "chronological_era_market_regimes": era_market_regimes,
            "market_regime_summary": regime_summary, "symbol_dependence_unadjusted": True,
            "survivorship_free": False, "independent_holdout": False,
            "corporate_actions_verified": False, "trade_ready": False}


if __name__ == "__main__":
    rows = [json.loads(line) for line in sys.stdin if line.strip()]
    print(json.dumps(summarize(rows), sort_keys=True))
